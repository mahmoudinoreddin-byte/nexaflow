from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Browse catalogue
    path('', views.service_list, name='list'),
    # My active services + tokens
    path('my/', views.my_services, name='my'),
    # Add / remove
    path('<int:service_id>/add/', views.add_service, name='add'),
    path('<int:service_id>/remove/', views.remove_service, name='remove'),
    path('<int:service_id>/rotate-token/', views.rotate_token, name='rotate_token'),
    # Secure access (token in URL)
    path('access/<uuid:token>/', views.service_access, name='access'),
    # Verify endpoint for internal apps
    path('verify/<uuid:token>/', views.verify_token, name='verify'),
]
