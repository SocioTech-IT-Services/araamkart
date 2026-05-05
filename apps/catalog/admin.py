"""Catalog app — Django Admin"""
from django.contrib import admin
from .models import Category, Product, PricingTier, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image", "sort_order")


class PricingTierInline(admin.TabularInline):
    model = PricingTier
    extra = 2
    fields = ("min_qty", "max_qty", "unit_price", "label")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "slug", "is_active", "order")
    list_editable = ("is_active", "order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "category", "stock", "moq", "unit", "is_active", "updated_at")
    list_filter = ("category", "is_active", "brand")
    list_editable = ("stock", "is_active")
    search_fields = ("name", "brand")
    inlines = [PricingTierInline, ProductImageInline]
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Product Info", {"fields": ("name", "brand", "category", "description", "image")}),
        ("Inventory", {"fields": ("stock", "moq", "unit", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(PricingTier)
class PricingTierAdmin(admin.ModelAdmin):
    list_display = ("product", "min_qty", "max_qty", "unit_price", "label")
    list_filter = ("product__category",)
    search_fields = ("product__name", "product__brand")
