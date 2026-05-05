"""DRF Serializers — Catalog"""
from rest_framework import serializers
from .models import Category, Product, PricingTier


class PricingTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingTier
        fields = ["id", "min_qty", "max_qty", "unit_price", "label"]


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "description", "product_count"]

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    base_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "brand", "category", "category_name", "base_price", "moq", "unit", "stock", "image"]

    def get_base_price(self, obj):
        return float(obj.base_price) if obj.base_price else None


class ProductDetailSerializer(serializers.ModelSerializer):
    pricing_tiers = PricingTierSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "brand", "category", "category_name",
            "description", "moq", "unit", "stock", "image",
            "pricing_tiers", "is_active", "created_at",
        ]


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["name", "brand", "category", "description", "stock", "moq", "unit", "is_active", "image"]
