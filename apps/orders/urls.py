"""Orders — Template URL patterns"""
from django.urls import path
from .views import (
    cart_view, add_to_cart, update_cart, remove_from_cart,
    checkout_view, order_success, order_quotation, order_history, order_detail,
    admin_dashboard, admin_products, admin_orders,
    admin_product_add, admin_product_edit, admin_product_delete,
    admin_bulk_import_products,
    admin_gallery_image_delete,
    admin_order_detail,
    admin_update_order_status, admin_update_stock,
    admin_toggle_product_active,
)

urlpatterns = [
    # Cart
    path("cart/", cart_view, name="cart"),
    path("cart/add/", add_to_cart, name="add_to_cart"),
    path("cart/update/", update_cart, name="update_cart"),
    path("cart/remove/", remove_from_cart, name="remove_from_cart"),
    # Checkout & Orders
    path("checkout/", checkout_view, name="checkout"),
    path("success/<str:order_number>/", order_success, name="order_success"),
    path("success/<str:order_number>/quotation/", order_quotation, name="order_quotation"),
    path("history/", order_history, name="order_history"),
    path("detail/<str:order_number>/", order_detail, name="order_detail"),
    # Admin Panel
    path("admin-panel/", admin_dashboard, name="admin_dashboard"),
    path("admin-panel/products/", admin_products, name="admin_products"),
    path("admin-panel/products/add/", admin_product_add, name="admin_product_add"),
    path("admin-panel/products/import/", admin_bulk_import_products, name="admin_bulk_import_products"),
    path("admin-panel/products/<int:pk>/edit/", admin_product_edit, name="admin_product_edit"),
    path("admin-panel/products/<int:pk>/delete/", admin_product_delete, name="admin_product_delete"),
    path(
        "admin-panel/products/gallery-image/<int:pk>/delete/",
        admin_gallery_image_delete,
        name="admin_gallery_image_delete",
    ),
    path("admin-panel/products/update-stock/", admin_update_stock, name="admin_update_stock"),
    path("admin-panel/products/toggle-active/", admin_toggle_product_active, name="admin_toggle_product_active"),
    path("admin-panel/orders/", admin_orders, name="admin_orders"),
    path("admin-panel/orders/update-status/", admin_update_order_status, name="admin_update_order_status"),
    path("admin-panel/orders/<str:order_number>/", admin_order_detail, name="admin_order_detail"),
]
