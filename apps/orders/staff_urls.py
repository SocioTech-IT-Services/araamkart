"""Staff-only routes (not under /orders/ prefix)."""
from django.urls import path

from .staff_views import staff_dashboard, staff_delivery_panel

urlpatterns = [
    path("dashboard/", staff_dashboard, name="staff_dashboard"),
    path("delivery-panel/", staff_delivery_panel, name="staff_delivery_panel"),
]
