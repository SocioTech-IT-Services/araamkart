"""Catalog — DRF API URL patterns"""
from django.urls import path
from .api_views import (
    CategoryListAPIView,
    SearchTaxonomySuggestAPIView,
    ProductListAPIView,
    ProductDetailAPIView,
    MostSellingProductsAPIView,
)

urlpatterns = [
    path("categories/", CategoryListAPIView.as_view(), name="api_categories"),
    path("search/suggest/", SearchTaxonomySuggestAPIView.as_view(), name="api_search_suggest"),
    path("products/", ProductListAPIView.as_view(), name="api_products"),
    path("products/<int:pk>/", ProductDetailAPIView.as_view(), name="api_product_detail"),
    path("products/most-selling/", MostSellingProductsAPIView.as_view(), name="api_products_most_selling"),
]
