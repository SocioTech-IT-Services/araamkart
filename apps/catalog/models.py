"""Catalog app models — Category, Product, PricingTier"""
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=10, default="📦")   # emoji icon
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["order", "name"]


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    moq = models.PositiveIntegerField(default=1, help_text="Minimum Order Quantity")
    unit = models.CharField(max_length=30, default="pcs", help_text="e.g. pcs, kg, box, carton")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.brand} — {self.name}"

    @property
    def base_price(self):
        """Return lowest tier price (MOQ tier)."""
        tier = self.pricing_tiers.order_by("min_qty").first()
        return tier.unit_price if tier else None

    def get_price_for_qty(self, qty):
        """Return unit price for a given quantity."""
        applicable = (
            self.pricing_tiers.filter(min_qty__lte=qty)
            .order_by("-min_qty")
            .first()
        )
        if applicable:
            return applicable.unit_price
        return self.base_price

    class Meta:
        ordering = ["name"]


class ProductImage(models.Model):
    """Extra photos for a product (primary hero remains Product.image)."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gallery_images")
    image = models.ImageField(upload_to="products/gallery/")
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "pk"]

    def __str__(self):
        return f"{self.product.name} — image #{self.pk}"


class PricingTier(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="pricing_tiers")
    min_qty = models.PositiveIntegerField(help_text="Minimum quantity for this tier")
    max_qty = models.PositiveIntegerField(null=True, blank=True, help_text="Max qty (leave blank = unlimited)")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    label = models.CharField(max_length=50, blank=True, help_text='e.g. "Bulk Price", "Wholesale"')

    def __str__(self):
        return f"{self.product.name} | {self.min_qty}+ {self.product.unit} @ ₹{self.unit_price}"

    class Meta:
        ordering = ["min_qty"]
