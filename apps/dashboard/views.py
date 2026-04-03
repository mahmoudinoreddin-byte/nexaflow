from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from apps.accounts.models import User, ActivityLog
from apps.services.models import Service, UserService


def landing_page(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_panel:dashboard')
        return redirect('dashboard:home')
    return render(request, 'landing_page.html')


@login_required
def home(request):
    user = request.user
    user_services = UserService.objects.filter(user=user, is_active=True).select_related('service')
    activities = ActivityLog.objects.filter(user=user)[:8]
    days_remaining = user.subscription_days_remaining

    context = {
        'user_services': user_services,
        'activities': activities,
        'days_remaining': days_remaining,
        'services_count': user_services.count(),
    }
    return render(request, 'dashboard/home.html', context)
