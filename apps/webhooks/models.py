from django.db import models


class WebhookLog(models.Model):
    EVENT_SALE = 'sale'
    EVENT_REFUND = 'refund'
    EVENT_DISPUTE = 'dispute'
    EVENT_SUBSCRIPTION_ENDED = 'subscription_ended'
    EVENT_SUBSCRIPTION_RESTARTED = 'subscription_restarted'
    EVENT_CANCELLATION = 'cancellation'
    EVENT_UNKNOWN = 'unknown'

    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_DUPLICATE = 'duplicate'

    event_type = models.CharField(max_length=50, default=EVENT_UNKNOWN)
    gumroad_sale_id = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, default=STATUS_SUCCESS)
    error_message = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-received_at']

    def __str__(self):
        return f'{self.event_type} — {self.email} ({self.status})'
