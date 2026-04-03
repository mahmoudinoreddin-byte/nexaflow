from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.dashboard.views import landing_page

urlpatterns = [
    path('', landing_page, name='landing'),
    path('django-admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('admin-panel/', include('apps.admin_panel.urls')),
    path('webhooks/', include('apps.webhooks.urls')),
    path('services/', include('apps.services.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
