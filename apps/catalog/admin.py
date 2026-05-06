"""Catalog app — Django Admin"""
from django.contrib import admin
from .models import Category, SubCategory, Brand, Product, PricingTier, ProductImage, ProductVariant


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image", "sort_order")


class PricingTierInline(admin.TabularInline):
    model = PricingTier
    extra = 2
    fields = ("min_qty", "max_qty", "unit_price", "label")


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("name", "size_value", "size_unit", "pack_size", "sku", "price", "stock", "is_active")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "slug", "is_active", "order")
    list_editable = ("is_active", "order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active", "order")
    list_filter = ("category", "is_active")
    list_editable = ("is_active", "order")
    search_fields = ("name", "category__name")


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_editable = ("is_active",)
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "brand",
        "brand_obj",
        "category",
        "subcategory",
        "stock",
        "moq",
        "unit",
        "is_active",
        "updated_at",
    )
    list_filter = ("category", "subcategory", "brand_obj", "is_active", "brand")
    list_editable = ("stock", "is_active", "subcategory")
    search_fields = ("name", "brand", "sku")
    inlines = [PricingTierInline, ProductImageInline, ProductVariantInline]
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Product Info",
            {"fields": ("name", "sku", "brand", "brand_obj", "category", "subcategory", "description", "image")},
        ),
        ("Inventory", {"fields": ("stock", "moq", "unit", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(PricingTier)
class PricingTierAdmin(admin.ModelAdmin):
    list_display = ("product", "min_qty", "max_qty", "unit_price", "label")
    list_filter = ("product__category",)
    search_fields = ("product__name", "product__brand")
