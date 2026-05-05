"""Catalog — DRF API URL patterns"""
from django.urls import path
from .api_views import CategoryListAPIView, ProductListAPIView, ProductDetailAPIView

urlpatterns = [
    path("categories/", CategoryListAPIView.as_view(), name="api_categories"),
    path("products/", ProductListAPIView.as_view(), name="api_products"),
    path("products/<int:pk>/", ProductDetailAPIView.as_view(), name="api_product_detail"),
]
