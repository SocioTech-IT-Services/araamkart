"""Catalog — Template URL patterns"""
from django.urls import path
from .views import (
    home,
    category_detail,
    product_detail,
    search_results,
    contact,
    best_offers,
    policies,
)

urlpatterns = [
    path("", home, name="home"),
    path("contact/", contact, name="contact"),
    path("offers/", best_offers, name="best_offers"),
    path("policies/", policies, name="policies"),
    path("category/<slug:slug>/", category_detail, name="category_detail"),
    path("product/<int:pk>/", product_detail, name="product_detail"),
    path("search/", search_results, name="search"),
]
