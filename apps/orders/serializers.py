"""DRF Serializers — Orders"""
from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem
from apps.catalog.serializers import ProductListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    unit_price = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()
    original_line_total = serializers.SerializerMethodField()
    line_savings = serializers.SerializerMethodField()
    total_pieces = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "packet_size", "total_pieces", "unit_price", "line_total", "original_line_total", "line_savings"]

    def get_unit_price(self, obj):
        return float(obj.unit_price()) if obj.unit_price() else 0

    def get_line_total(self, obj):
        return float(obj.line_total())

    def get_original_line_total(self, obj):
        return float(obj.original_line_total())

    def get_line_savings(self, obj):
        return float(obj.line_savings())

    def get_total_pieces(self, obj):
        return obj.total_pieces


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    original_total = serializers.SerializerMethodField()
    total_savings = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "items", "total", "original_total", "total_savings", "updated_at"]

    def get_total(self, obj):
        return float(obj.get_total())

    def get_original_total(self, obj):
        return float(obj.get_original_total())

    def get_total_savings(self, obj):
        return float(obj.get_total_savings())


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.SerializerMethodField()
    total_pieces = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "product_name", "brand", "quantity", "packet_size", "total_pieces", "original_unit_price", "unit_price", "line_savings", "line_total"]

    def get_line_total(self, obj):
        return float(obj.line_total())

    def get_total_pieces(self, obj):
        return obj.total_pieces


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "business_name", "customer_name",
            "phone", "email", "address", "city", "pincode",
            "payment_method", "status", "subtotal_amount", "total_savings", "total_amount", "notes",
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
