"""
URL Configuration for Billing App
"""
from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('expired/', views.subscription_expired_view, name='expired'),
]
