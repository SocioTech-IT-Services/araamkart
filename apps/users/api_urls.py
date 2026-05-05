"""Users — DRF API URL patterns"""
from django.urls import path
from .api_views import (
    RegisterAPIView, LoginPhoneAPIView, LoginEmailAPIView,
    MeAPIView, LogoutAPIView,
)

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="api_register"),
    path("login/phone/", LoginPhoneAPIView.as_view(), name="api_login_phone"),
    path("login/email/", LoginEmailAPIView.as_view(), name="api_login_email"),
    path("me/", MeAPIView.as_view(), name="api_me"),
    path("logout/", LogoutAPIView.as_view(), name="api_logout"),
]
