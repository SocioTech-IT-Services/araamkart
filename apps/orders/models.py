"""Orders app models — Cart, CartItem, Order, OrderItem"""
from decimal import Decimal

from django.db import models
from django.conf import settings
from apps.catalog.models import Product, ProductVariant


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user}"

    def get_total(self):
        return sum(item.line_total() for item in self.items.all())

    def get_original_total(self):
        return sum(item.original_line_total() for item in self.items.all())

    def get_total_savings(self):
        return sum(item.line_savings() for item in self.items.all())

    def item_count(self):
        return self.items.count()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_variant = models.ForeignKey(
        ProductVariant,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    packet_size = models.PositiveIntegerField(default=1)

    @property
    def effective_packet_size(self):
        if self.packet_size and self.packet_size > 0:
            return self.packet_size
        if self.product_variant_id and self.product_variant.pack_size:
            return int(self.product_variant.pack_size)
        if self.product.pack_quantity:
            return int(self.product.pack_quantity)
        return 1

    @property
    def total_pieces(self):
        return self.quantity * self.effective_packet_size

    def unit_price(self):
        product = self.product
        v = self.product_variant
        if v and product.packet_price and product.pack_quantity:
            return v.packet_selling_price
        return product.get_price_for_qty(self.quantity)

    def original_unit_price(self):
        product = self.product
        v = self.product_variant
        unit_price = self.unit_price() or Decimal("0")
        if v and product.packet_price and product.pack_quantity:
            pkt = v.packet_mrp_total
            if pkt is not None:
                return pkt
            if product.single_product_price:
                pk = max(1, int(v.pack_size or 1))
                return Decimal(product.single_product_price) * Decimal(pk)
        if product.packet_price and product.pack_quantity and product.single_product_price:
            return Decimal(product.single_product_price) * Decimal(self.effective_packet_size)
        if product.single_product_price:
            return max(Decimal(product.single_product_price), Decimal(unit_price))
        return Decimal(unit_price)

    def line_total(self):
        price = self.unit_price()
        return price * self.quantity if price else 0

    def original_line_total(self):
        return self.original_unit_price() * self.quantity

    def line_savings(self):
        return max(Decimal("0"), self.original_line_total() - Decimal(self.line_total() or 0))

    def unit_savings(self):
        return max(Decimal("0"), self.original_unit_price() - Decimal(self.unit_price() or 0))

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="orders"
    )
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    business_name = models.CharField(max_length=200)
    customer_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    payment_method = models.CharField(max_length=20, default="cod")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_savings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    last_status_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders_delivery_updates",
    )
    cancellation_reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Filled when staff cancels from delivery ops (e.g. didn't pick up).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            import random, string
            self.order_number = "AK" + "".join(
                random.choices(string.digits, k=8)
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.order_number} — {self.business_name}"

    class Meta:
        ordering = ["-created_at"]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)  # snapshot
    brand = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    packet_size = models.PositiveIntegerField(default=1)
    original_unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_savings = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def total_pieces(self):
        return self.quantity * max(1, int(self.packet_size or 1))

    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"
