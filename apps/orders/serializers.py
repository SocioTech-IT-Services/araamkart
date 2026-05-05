"""DRF Serializers — Orders"""
from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem
from apps.catalog.serializers import ProductListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    unit_price = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "unit_price", "line_total"]

    def get_unit_price(self, obj):
        return float(obj.unit_price()) if obj.unit_price() else 0

    def get_line_total(self, obj):
        return float(obj.line_total())


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "items", "total", "updated_at"]

    def get_total(self, obj):
        return float(obj.get_total())


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "product_name", "brand", "quantity", "unit_price", "line_total"]

    def get_line_total(self, obj):
        return float(obj.line_total())


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "business_name", "customer_name",
            "phone", "email", "address", "city", "pincode",
            "payment_method", "status", "total_amount", "notes",
            "items", "created_at",
        ]
        read_only_fields = ["order_number", "status", "created_at"]


class PlaceOrderSerializer(serializers.Serializer):
    customer_name = serializers.CharField()
    business_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True)
    address = serializers.CharField()
    city = serializers.CharField(required=False, allow_blank=True)
    pincode = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
