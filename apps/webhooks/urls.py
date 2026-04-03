from django.urls import path
from . import views

app_name = 'webhooks'

urlpatterns = [
    path('gumroad/', views.gumroad_webhook, name='gumroad'),
]
