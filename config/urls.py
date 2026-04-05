from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.dashboard.views import landing_page
from tools_app import sketch_fabric


urlpatterns = [
    path('', landing_page, name='landing'),
    path('django-admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('admin-panel/', include('apps.admin_panel.urls')),
    path('webhooks/', include('apps.webhooks.urls')),
    path('services/', include('apps.services.urls')),


    path('tools/sketch-fabric/save/', sketch_fabric.save_drawing, name='sketch_fabric_save'),
    path('tools/sketch-fabric/load/', sketch_fabric.load_drawing, name='sketch_fabric_load'),
    path('tools/sketch-fabric/list/', sketch_fabric.list_drawings, name='sketch_fabric_list'),
    path('tools/sketch-fabric/delete/<str:filename>/', sketch_fabric.delete_drawing, name='sketch_fabric_delete'),
    path('tools/sketch-fabric/info/', sketch_fabric.get_upload_folder_info, name='sketch_fabric_info'),

    path('tools/sketch-fabric/', sketch_fabric.sketch_fabric_view, name='sketch_fabric'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
