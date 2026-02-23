"""
JWT Authentication URLs
POST /api/v1/auth/token/    — obtain access + refresh tokens
POST /api/v1/auth/refresh/  — refresh access token
POST /api/v1/auth/logout/   — blacklist refresh token
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .auth_views import LogoutView

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='jwt_token_obtain'),
    path('refresh/', TokenRefreshView.as_view(), name='jwt_token_refresh'),
    path('logout/', LogoutView.as_view(), name='jwt_logout'),
]
