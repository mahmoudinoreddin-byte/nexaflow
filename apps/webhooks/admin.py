from django.contrib import admin
from .models import WebhookLog


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'email', 'gumroad_sale_id', 'status', 'received_at']
    list_filter = ['event_type', 'status']
    search_fields = ['email', 'gumroad_sale_id']
    readonly_fields = ['received_at', 'payload']
