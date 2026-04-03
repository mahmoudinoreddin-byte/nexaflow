from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Extended user with subscription and Gumroad integration."""

    PLAN_FREE = 'free'
    PLAN_PRO = 'pro'
    PLAN_ENTERPRISE = 'enterprise'
    PLAN_CHOICES = [
        (PLAN_FREE, 'Free'),
        (PLAN_PRO, 'Pro'),
        (PLAN_ENTERPRISE, 'Enterprise'),
    ]

    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_SUSPENDED = 'suspended'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_SUSPENDED, 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_FREE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INACTIVE)

    # Gumroad integration
    gumroad_sale_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    gumroad_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    gumroad_product_id = models.CharField(max_length=255, blank=True, null=True)

    # Subscription dates
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)
    subscription_renewed_at = models.DateTimeField(null=True, blank=True)

    # Password setup
    setup_token = models.UUIDField(null=True, blank=True)
    setup_token_expires = models.DateTimeField(null=True, blank=True)
    password_set = models.BooleanField(default=False)

    # Profile
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    language = models.CharField(max_length=5, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.email} ({self.plan})'

    @property
    def is_subscribed(self):
        return self.status == self.STATUS_ACTIVE and self.plan != self.PLAN_FREE

    @property
    def subscription_days_remaining(self):
        if self.subscription_end and self.subscription_end > timezone.now():
            delta = self.subscription_end - timezone.now()
            return delta.days
        return 0

    def generate_setup_token(self):
        self.setup_token = uuid.uuid4()
        self.setup_token_expires = timezone.now() + timezone.timedelta(hours=48)
        self.save(update_fields=['setup_token', 'setup_token_expires'])
        return self.setup_token

    def is_setup_token_valid(self, token):
        return (
            self.setup_token is not None
            and str(self.setup_token) == str(token)
            and self.setup_token_expires
            and self.setup_token_expires > timezone.now()
        )


class ActivityLog(models.Model):
    """Tracks user activity for the dashboard."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, default='📋')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.action}'
