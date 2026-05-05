"""Orders — DRF API URL patterns"""
from django.urls import path
from .api_views import CartAPIView, PlaceOrderAPIView, OrderHistoryAPIView, AdminDashboardAPIView

urlpatterns = [
    path("cart/", CartAPIView.as_view(), name="api_cart"),
    path("orders/place/", PlaceOrderAPIView.as_view(), name="api_place_order"),
    path("orders/", OrderHistoryAPIView.as_view(), name="api_orders"),
    path("admin/dashboard/", AdminDashboardAPIView.as_view(), name="api_admin_dashboard"),
]
