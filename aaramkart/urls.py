"""AaramKart URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

from apps.users.views import StaffLoginView

admin.site.site_header = "AaramKart administration"
admin.site.site_title = "AaramKart Admin"
admin.site.index_title = "Store administration"

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("staff-login/", StaffLoginView.as_view(), name="staff_login"),
    path(
        "admin/dashboard/",
        RedirectView.as_view(pattern_name="admin_dashboard", query_string=False),
        name="admin_dashboard_public",
    ),
    path("staff/", include("apps.orders.staff_urls")),
    # Frontend views
    path("", include("apps.catalog.urls")),
    path("auth/", include("apps.users.urls")),
    path("orders/", include("apps.orders.urls")),
    # REST API
    path("api/auth/", include("apps.users.api_urls")),
    path("api/", include("apps.catalog.api_urls")),
    path("api/", include("apps.orders.api_urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
