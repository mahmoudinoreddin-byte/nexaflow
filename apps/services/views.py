from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from apps.accounts.models import ActivityLog
from .models import Service, UserService


# ─── Public service catalogue (search + add) ────────────────────────────────

@login_required
def service_list(request):
    """Browse all active services; user can search and add to their list."""
    query = request.GET.get('q', '').strip()
    category = request.GET.get('cat', '')

    services = Service.objects.filter(status=Service.STATUS_ACTIVE).select_related('category')
    if query:
        services = services.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    if category:
        services = services.filter(category__slug=category)

    # IDs the user already has (active or not)
    user_service_map = {
        us.service_id: us
        for us in UserService.objects.filter(user=request.user).select_related('service')
    }

    from .models import ServiceCategory
    categories = ServiceCategory.objects.all()

    context = {
        'services': services,
        'user_service_map': user_service_map,
        'query': query,
        'selected_cat': category,
        'categories': categories,
    }
    return render(request, 'dashboard/services.html', context)


# ─── Add a service to user's list ───────────────────────────────────────────

@login_required
@require_POST
def add_service(request, service_id):
    service = get_object_or_404(Service, id=service_id, status=Service.STATUS_ACTIVE)
    us, created = UserService.objects.get_or_create(
        user=request.user,
        service=service,
    )
    if not created and not us.is_active:
        us.is_active = True
        us.save(update_fields=['is_active'])
        created = True  # treat reactivation as new

    if created:
        ActivityLog.objects.create(
            user=request.user,
            action='Service Added',
            description=f'Added service: {service.name}',
            icon='➕',
        )
        messages.success(request, f'✅ {service.name} added to your services.')
    else:
        messages.info(request, f'{service.name} is already in your list.')

    return redirect('services:list')


# ─── Remove a service ────────────────────────────────────────────────────────

@login_required
@require_POST
def remove_service(request, service_id):
    us = get_object_or_404(UserService, user=request.user, service_id=service_id)
    service_name = us.service.name
    us.is_active = False
    us.save(update_fields=['is_active'])
    ActivityLog.objects.create(
        user=request.user,
        action='Service Removed',
        description=f'Removed service: {service_name}',
        icon='➖',
    )
    messages.success(request, f'{service_name} removed from your services.')
    return redirect('services:my')


# ─── My Services (with tokens) ───────────────────────────────────────────────

@login_required
def my_services(request):
    """Show only the user's own active services with their secure access links."""
    user_services = (
        UserService.objects
        .filter(user=request.user, is_active=True)
        .select_related('service', 'service__category')
        .order_by('service__order', 'service__name')
    )
    return render(request, 'dashboard/my_services.html', {
        'user_services': user_services,
    })


# ─── Rotate token ────────────────────────────────────────────────────────────

@login_required
@require_POST
def rotate_token(request, service_id):
    us = get_object_or_404(UserService, user=request.user, service_id=service_id, is_active=True)
    us.rotate_token()
    ActivityLog.objects.create(
        user=request.user,
        action='Token Rotated',
        description=f'Regenerated access token for: {us.service.name}',
        icon='🔄',
    )
    messages.success(request, f'New access link generated for {us.service.name}.')
    return redirect('services:my')


# ─── Secure access endpoint ──────────────────────────────────────────────────

def service_access(request, token):
    """
    Token-gated entry point for a service.
    The token identifies both the user AND the service — no login required via URL.
    If the service has a URL, redirects there (with token as query param for your
    internal apps to verify).  Otherwise shows a service landing page.
    """
    us = get_object_or_404(
        UserService.objects.select_related('service', 'user'),
        access_token=token,
        is_active=True,
    )

    if not us.user.is_active or us.user.status not in ('active',):
        raise Http404('Account not active')

    if us.service.status != Service.STATUS_ACTIVE:
        raise Http404('Service not available')

    # Log the access
    ActivityLog.objects.create(
        user=us.user,
        action='Service Accessed',
        description=f'Accessed via token: {us.service.name}',
        icon='🔑',
    )

    # If service has a built-in tool slug → render it embedded
    if us.service.tool_slug:
        tool_template = f'tools/{us.service.tool_slug}.html'
        return render(request, tool_template, {
            'us': us,
            'service': us.service,
            'user': us.user,
            'token': str(token),
        })

    # If service has an external/internal URL → redirect with token
    if us.service.url:
        separator = '&' if '?' in us.service.url else '?'
        redirect_url = f"{us.service.url}{separator}nexatoken={token}"
        from django.shortcuts import redirect as dj_redirect
        return dj_redirect(redirect_url)

    # No URL or slug → show generic landing page
    return render(request, 'dashboard/service_access.html', {
        'us': us,
        'service': us.service,
        'user': us.user,
    })


# ─── Verify endpoint (called by your internal apps) ──────────────────────────

def verify_token(request, token):
    """
    JSON endpoint your internal services call to verify a nexatoken.
    Returns user info if valid, 403 if not.
    Used by internal apps: GET /services/verify/<token>/
    """
    try:
        us = UserService.objects.select_related('service', 'user').get(
            access_token=token,
            is_active=True,
        )
    except UserService.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Invalid or expired token'}, status=403)

    if us.user.status != 'active':
        return JsonResponse({'valid': False, 'error': 'Account suspended'}, status=403)

    if us.service.status != Service.STATUS_ACTIVE:
        return JsonResponse({'valid': False, 'error': 'Service unavailable'}, status=403)

    return JsonResponse({
        'valid': True,
        'user': {
            'id': str(us.user.id),
            'email': us.user.email,
            'username': us.user.username,
            'plan': us.user.plan,
        },
        'service': {
            'id': us.service.id,
            'name': us.service.name,
            'slug': us.service.url,
        },
        'token': str(token),
        'activated_at': us.activated_at.isoformat(),
    })
