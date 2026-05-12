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
        return (
            Product.objects.filter(placements__category=obj, is_active=True)
            .distinct()
            .count()
        )


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    base_price = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "brand", "category", "category_name", "base_price", "moq", "unit", "stock", "image"]

    def get_base_price(self, obj):
        return float(obj.base_price) if obj.base_price else None

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        if request:
            return request.build_absolute_uri(url)
        return url


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
