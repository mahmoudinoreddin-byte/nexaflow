from django.db import models
import uuid
import secrets


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Service(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_PAUSED = 'paused'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_PAUSED, 'Paused'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, default='⚡')
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    url = models.URLField(blank=True, help_text='Internal path or external URL for this service')
    tool_slug = models.SlugField(
        blank=True,
        help_text='If set, opens a built-in tool page (e.g. cad-editor). Overrides url.'
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @property
    def user_count(self):
        return self.userservice_set.filter(is_active=True).count()


class UserService(models.Model):
    """Links a user to a service with a unique secure access token."""

    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='user_services'
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    access_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    activated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'service')

    def __str__(self):
        return f'{self.user.email} → {self.service.name}'

    def get_access_url(self, request=None):
        """Return the full secure access URL for this user-service link."""
        from django.urls import reverse
        path = reverse('services:access', kwargs={'token': str(self.access_token)})
        if request:
            return request.build_absolute_uri(path)
        from django.conf import settings
        return f"{settings.SITE_URL.rstrip('/')}{path}"

    def rotate_token(self):
        """Generate a new access token (invalidates old links)."""
        self.access_token = uuid.uuid4()
        self.save(update_fields=['access_token'])
        return self.access_token
