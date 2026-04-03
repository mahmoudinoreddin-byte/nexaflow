from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Service


@login_required
def service_list(request):
    services = Service.objects.filter(status=Service.STATUS_ACTIVE)
    return render(request, 'dashboard/services.html', {'services': services})
