"""Orders app — Django Admin"""
from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("unit_price", "line_total")

    def unit_price(self, obj):
        return f"₹{obj.unit_price()}"
    unit_price.short_description = "Unit Price"

    def line_total(self, obj):
        return f"₹{obj.line_total()}"
    line_total.short_description = "Line Total"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("line_total",)

    def line_total(self, obj):
        return f"₹{obj.line_total()}"
    line_total.short_description = "Line Total"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "item_count", "get_total", "updated_at")
    inlines = [CartItemInline]

    def item_count(self, obj):
        return obj.item_count()

    def get_total(self, obj):
        return f"₹{obj.get_total()}"
    get_total.short_description = "Total"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "business_name", "customer_name", "phone", "status", "total_amount", "created_at")
    list_filter = ("status", "payment_method")
    list_editable = ("status",)
    search_fields = ("order_number", "business_name", "customer_name", "phone")
    readonly_fields = ("order_number", "created_at", "updated_at")
    inlines = [OrderItemInline]
    fieldsets = (
        ("Order Info", {"fields": ("order_number", "user", "status", "payment_method", "total_amount", "notes")}),
        ("Customer Details", {"fields": ("customer_name", "business_name", "phone", "email", "address", "city", "pincode")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
