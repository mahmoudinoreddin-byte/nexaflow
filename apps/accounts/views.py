from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from .models import User, ActivityLog
from .forms import LoginForm, SetPasswordForm, ProfileForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(request, username=email, password=password)
        if user:
            if user.status == User.STATUS_SUSPENDED:
                messages.error(request, 'Your account has been suspended. Contact support.')
                return render(request, 'accounts/login.html', {'form': form})
            login(request, user)
            ActivityLog.objects.create(
                user=user, action='Login', description='User logged in', icon='🔐'
            )
            next_url = request.GET.get('next', 'dashboard:home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        ActivityLog.objects.create(
            user=request.user, action='Logout', description='User logged out', icon='👋'
        )
    logout(request)
    return redirect('landing')


def setup_password(request, token):
    """Token-based password setup sent via email after Gumroad purchase."""
    user = get_object_or_404(User, setup_token=token)
    
    if not user.is_setup_token_valid(token):
        return render(request, 'accounts/setup_expired.html')
    
    if user.password_set:
        messages.info(request, 'Your password is already set. Please log in.')
        return redirect('accounts:login')
    
    form = SetPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user.set_password(form.cleaned_data['password1'])
        user.password_set = True
        user.setup_token = None
        user.setup_token_expires = None
        user.status = User.STATUS_ACTIVE
        user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        ActivityLog.objects.create(
            user=user, action='Account Setup', description='Password created, account activated', icon='✅'
        )
        messages.success(request, f'Welcome to NexaFlow, {user.username}! Your account is ready.')
        return redirect('dashboard:home')
    
    return render(request, 'accounts/setup_password.html', {'form': form, 'user_email': user.email})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'form': form})
