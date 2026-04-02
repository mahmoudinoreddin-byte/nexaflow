from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('users/', views.users_list, name='users'),
    path('users/<uuid:user_id>/', views.user_detail, name='user_detail'),
    path('services/', views.services_list, name='services'),
    path('webhooks/', views.webhook_logs, name='webhooks'),
]
