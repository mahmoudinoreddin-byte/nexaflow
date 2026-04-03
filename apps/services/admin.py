from django.contrib import admin
from .models import Service, ServiceCategory, UserService


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'status', 'order', 'user_count']
    list_filter = ['status', 'category']
    list_editable = ['status', 'order']
    search_fields = ['name']


@admin.register(UserService)
class UserServiceAdmin(admin.ModelAdmin):
    list_display = ['user', 'service', 'is_active', 'activated_at']
    list_filter = ['is_active', 'service']
    search_fields = ['user__email']
