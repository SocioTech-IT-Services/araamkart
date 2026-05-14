"""DRF API Views — Orders & Cart"""
import math

from django.db.models import Sum
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.catalog.models import Product
from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartSerializer, OrderSerializer, PlaceOrderSerializer
from apps.notifications.services import send_order_confirmation


def _packet_rules(product):
    if not (product.packet_price and product.pack_quantity):
        return None
    pack_qty = int(product.pack_quantity or 0)
    if pack_qty <= 0:
        return None
    min_packets = 1
    return {"pack_qty": pack_qty, "min_packets": min_packets}


def _money(value):
    return Decimal(value or 0).quantize(Decimal("0.01"))


class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return Response(CartSerializer(cart).data)

    def post(self, request):
        """Add item to cart."""
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))
        try:
            product = Product.objects.get(pk=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=404)
        packet_rules = _packet_rules(product)
        if not packet_rules and quantity < product.moq:
            return Response({"error": f"Minimum order quantity is {product.moq} {product.unit}."}, status=400)
        if packet_rules:
            min_packets = packet_rules["min_packets"]
            if quantity < min_packets:
                return Response(
                    {"error": f"Minimum packet order is {min_packets} packet(s)."},
                    status=400,
                )
        if quantity > product.stock:
            return Response({"error": "Not enough stock."}, status=400)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if packet_rules:
            item.packet_size = packet_rules["pack_qty"]
        item.quantity = quantity if created else item.quantity + quantity
        if item.quantity > product.stock:
            return Response({"error": "Not enough stock."}, status=400)
        item.save()
        return Response(CartSerializer(cart).data)

    def patch(self, request):
        """Update item quantity."""
        item_id = request.data.get("item_id")
        quantity = int(request.data.get("quantity", 1))
        try:
            item = CartItem.objects.get(pk=item_id, cart__user=request.user)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found."}, status=404)
        packet_rules = _packet_rules(item.product)
        if not packet_rules and quantity < item.product.moq:
            return Response({"error": f"Minimum is {item.product.moq}."}, status=400)
        if packet_rules:
            min_packets = packet_rules["min_packets"]
            if quantity < min_packets:
                return Response(
                    {"error": f"Minimum packet order is {min_packets} packet(s)."},
                    status=400,
                )
        if quantity > item.product.stock:
            return Response({"error": "Not enough stock."}, status=400)
        if packet_rules:
            item.packet_size = packet_rules["pack_qty"]
        item.quantity = quantity
        item.save()
        return Response(CartSerializer(item.cart).data)

    def delete(self, request):
        """Remove item from cart."""
        item_id = request.data.get("item_id")
        try:
            item = CartItem.objects.get(pk=item_id, cart__user=request.user)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found."}, status=404)
        item.delete()
        cart = Cart.objects.get(user=request.user)
        return Response(CartSerializer(cart).data)


class PlaceOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = PlaceOrderSerializer(data=request.data)
        if not s.is_valid():
            return Response(s.errors, status=400)
        d = s.validated_data
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.select_related("product")
        if not items.exists():
            return Response({"error": "Cart is empty."}, status=400)
        total = cart.get_total()
        original_total = cart.get_original_total()
        total_savings = cart.get_total_savings()
        order = Order.objects.create(
            user=request.user,
            customer_name=d["customer_name"],
            business_name=d.get("business_name", ""),
            phone=d["phone"],
            email=d.get("email", ""),
            address=d["address"],
            city=d.get("city", ""),
            pincode=d.get("pincode", ""),
            notes=d.get("notes", ""),
            payment_method="cod",
            subtotal_amount=_money(original_total),
            total_savings=_money(total_savings),
            total_amount=total,
        )
        for item in items:
            original_unit_price = item.original_unit_price()
            line_savings = item.line_savings()
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                brand=item.product.brand,
                quantity=item.quantity,
                packet_size=item.effective_packet_size,
                original_unit_price=_money(original_unit_price),
                unit_price=item.unit_price(),
                line_savings=_money(line_savings),
            )
            p.decrease_inventory_for_sale(item.quantity)
        items.delete()
        try:
            send_order_confirmation(order)
        except Exception:
            pass
        return Response(OrderSerializer(order).data, status=201)


class OrderHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).prefetch_related("items").order_by("-created_at")
        return Response(OrderSerializer(orders, many=True).data)


class AdminDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not getattr(request.user, "can_access_admin_panel", False):
            return Response({"error": "Admin only."}, status=403)
        non_cancelled = Order.objects.exclude(status="cancelled")
        total_sales = non_cancelled.aggregate(s=Sum("total_amount"))["s"] or 0
        units = OrderItem.objects.filter(order__in=non_cancelled).aggregate(s=Sum("quantity"))["s"] or 0
        return Response({
            "total_orders": Order.objects.count(),
            "pending_orders": Order.objects.filter(status="pending").count(),
            "total_products": Product.objects.filter(is_active=True).count(),
            "total_sales": float(total_sales),
            "units_sold": units,
        })
