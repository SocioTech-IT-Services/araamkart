"""AaramKart URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("django-admin/", admin.site.urls),
    # Frontend views
    path("", include("apps.catalog.urls")),
    path("auth/", include("apps.users.urls")),
    path("orders/", include("apps.orders.urls")),
    # REST API
    path("api/auth/", include("apps.users.api_urls")),
    path("api/", include("apps.catalog.api_urls")),
    path("api/", include("apps.orders.api_urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
