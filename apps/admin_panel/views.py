import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib import messages

from apps.accounts.models import User, ActivityLog
from apps.services.models import Service, ServiceCategory, UserService
from apps.webhooks.models import WebhookLog


def staff_required(view_func):
    """Decorator: requires login + is_staff. Returns 403 (not redirect loop) for non-staff."""
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    wrapped.__name__ = view_func.__name__
    return wrapped


@staff_required
def dashboard(request):
    total_users = User.objects.exclude(is_staff=True).count()
    active_users = User.objects.filter(status=User.STATUS_ACTIVE).count()
    pro_users = User.objects.filter(plan=User.PLAN_PRO).count()
    total_services = Service.objects.count()
    active_services = Service.objects.filter(status=Service.STATUS_ACTIVE).count()
    recent_users = User.objects.exclude(is_staff=True).order_by('-created_at')[:10]
    recent_webhooks = WebhookLog.objects.order_by('-received_at')[:10]

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'pro_users': pro_users,
        'total_services': total_services,
        'active_services': active_services,
        'recent_users': recent_users,
        'recent_webhooks': recent_webhooks,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@staff_required
def users_list(request):
    query = request.GET.get('q', '')
    plan_filter = request.GET.get('plan', '')
    status_filter = request.GET.get('status', '')

    users = User.objects.exclude(is_staff=True).order_by('-created_at')
    if query:
        users = users.filter(Q(email__icontains=query) | Q(username__icontains=query))
    if plan_filter:
        users = users.filter(plan=plan_filter)
    if status_filter:
        users = users.filter(status=status_filter)

    context = {
        'users': users,
        'query': query,
        'plan_filter': plan_filter,
        'status_filter': status_filter,
        'plan_choices': User.PLAN_CHOICES,
        'status_choices': User.STATUS_CHOICES,
    }
    return render(request, 'admin_panel/users.html', context)


@staff_required
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    activities = ActivityLog.objects.filter(user=user)[:20]
    user_services = UserService.objects.filter(user=user).select_related('service')
    all_services = Service.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_plan':
            user.plan = request.POST.get('plan', user.plan)
            user.status = request.POST.get('status', user.status)
            user.save()
            messages.success(request, 'User updated.')
        elif action == 'toggle_service':
            svc_id = request.POST.get('service_id')
            svc = get_object_or_404(Service, id=svc_id)
            us, created = UserService.objects.get_or_create(user=user, service=svc)
            if not created:
                us.is_active = not us.is_active
                us.save()
            messages.success(request, f'Service {svc.name} updated.')
        return redirect('admin_panel:user_detail', user_id=user_id)

    context = {
        'target_user': user,
        'activities': activities,
        'user_services': user_services,
        'all_services': all_services,
        'plan_choices': User.PLAN_CHOICES,
        'status_choices': User.STATUS_CHOICES,
    }
    return render(request, 'admin_panel/user_detail.html', context)


@staff_required
def services_list(request):
    services = Service.objects.annotate(
        active_users=Count('userservice', filter=Q(userservice__is_active=True))
    ).order_by('order', 'name')
    categories = ServiceCategory.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            cat_id = request.POST.get('category')
            cat = ServiceCategory.objects.filter(id=cat_id).first() if cat_id else None
            try:
                order = int(request.POST.get('order', 0))
            except (ValueError, TypeError):
                order = 0
            Service.objects.create(
                name=request.POST['name'],
                description=request.POST.get('description', ''),
                icon=request.POST.get('icon', '⚡'),
                category=cat,
                status=request.POST.get('status', Service.STATUS_ACTIVE),
                url=request.POST.get('url', ''),
                tool_slug=request.POST.get('tool_slug', ''),
                order=order,
            )
            messages.success(request, 'Service created.')
        elif action == 'edit':
            svc = get_object_or_404(Service, id=request.POST['service_id'])
            cat_id = request.POST.get('category')
            cat = ServiceCategory.objects.filter(id=cat_id).first() if cat_id else None
            try:
                order = int(request.POST.get('order', svc.order))
            except (ValueError, TypeError):
                order = svc.order
            svc.name = request.POST.get('name', svc.name)
            svc.description = request.POST.get('description', svc.description)
            svc.icon = request.POST.get('icon', svc.icon)
            svc.category = cat
            svc.status = request.POST.get('status', svc.status)
            svc.url = request.POST.get('url', svc.url)
            svc.tool_slug = request.POST.get('tool_slug', svc.tool_slug)
            svc.order = order
            svc.save()
            messages.success(request, f'{svc.name} updated.')
        elif action == 'toggle':
            svc = get_object_or_404(Service, id=request.POST['service_id'])
            svc.status = Service.STATUS_PAUSED if svc.status == Service.STATUS_ACTIVE else Service.STATUS_ACTIVE
            svc.save()
            messages.success(request, f'{svc.name} toggled.')
        elif action == 'delete':
            get_object_or_404(Service, id=request.POST['service_id']).delete()
            messages.success(request, 'Service deleted.')
        return redirect('admin_panel:services')

    context = {'services': services, 'categories': categories}
    return render(request, 'admin_panel/services.html', context)


@staff_required
def webhook_logs(request):
    logs = WebhookLog.objects.order_by('-received_at')[:100]
    return render(request, 'admin_panel/webhooks.html', {'logs': logs})
