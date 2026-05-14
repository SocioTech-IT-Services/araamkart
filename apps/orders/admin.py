"""Orders app — Django Admin"""
from django.contrib import admin
from django.contrib.auth import login as auth_login
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
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
    list_display = ("user", "item_count", "get_total", "updated_at", "login_as_user_link")
    search_fields = ("user__email", "user__phone", "user__full_name", "user__business_name")
    list_filter = ("updated_at",)
    inlines = [CartItemInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(items__isnull=False).distinct()

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:cart_id>/login-as-user/",
                self.admin_site.admin_view(self.login_as_user),
                name="orders_cart_login_as_user",
            ),
        ]
        return custom + urls

    def item_count(self, obj):
        return obj.item_count()

    def get_total(self, obj):
        return f"₹{obj.get_total()}"
    get_total.short_description = "Total"

    def login_as_user_link(self, obj):
        url = reverse("admin:orders_cart_login_as_user", args=[obj.pk])
        return format_html('<a class="button" href="{}">Login as user</a>', url)
    login_as_user_link.short_description = "Support"

    def login_as_user(self, request, cart_id):
        cart = self.get_object(request, cart_id)
        if not cart:
            return HttpResponseRedirect(reverse("admin:orders_cart_changelist"))
        # Support helper: switch session to customer for troubleshooting cart issues.
        auth_login(request, cart.user, backend="django.contrib.auth.backends.ModelBackend")
        return HttpResponseRedirect(reverse("cart"))


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
