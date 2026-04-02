from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ActivityLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'plan', 'status', 'created_at']
    list_filter = ['plan', 'status', 'is_staff']
    search_fields = ['email', 'username', 'gumroad_sale_id']
    ordering = ['-created_at']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Subscription', {'fields': ('plan', 'status', 'subscription_start', 'subscription_end')}),
        ('Gumroad', {'fields': ('gumroad_sale_id', 'gumroad_subscription_id', 'gumroad_product_id')}),
        ('Setup', {'fields': ('setup_token', 'setup_token_expires', 'password_set')}),
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'created_at']
    list_filter = ['action']
    search_fields = ['user__email', 'action']
    readonly_fields = ['created_at']
