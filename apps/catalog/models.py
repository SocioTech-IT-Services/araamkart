"""Catalog app models — Category, SubCategory, Brand, Product, Variants, Pricing"""
from django.db import models
from django.utils.text import slugify
from decimal import Decimal


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


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    def _unique_slug_base(self):
        base = slugify(self.name)[:95] or "item"
        slug = base
        n = 2
        qs = SubCategory.objects.filter(category=self.category, parent=self.parent, slug=slug)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        while qs.exists():
            slug = f"{base}-{n}"
            n += 1
            qs = SubCategory.objects.filter(category=self.category, parent=self.parent, slug=slug)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug_base()
        super().save(*args, **kwargs)

    def ancestor_chain(self):
        """Root → … → self (for breadcrumbs)."""
        chain = []
        node = self
        while node:
            chain.append(node)
            node = node.parent
        return list(reversed(chain))

    def __str__(self):
        return f"{self.category.name} / {self.name}"

    class Meta:
        ordering = ["category__order", "order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "slug"],
                condition=models.Q(parent__isnull=True),
                name="catalog_subcat_root_slug",
            ),
            models.UniqueConstraint(
                fields=["category", "parent", "slug"],
                condition=models.Q(parent__isnull=False),
                name="catalog_subcat_nested_slug",
            ),
        ]
        verbose_name = "Subcategory"
        verbose_name_plural = "Subcategories"


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Product(models.Model):
    NET_QUANTITY_UNIT_CHOICES = [
        ("ml", "ml"),
        ("g", "g"),
        ("pieces", "pieces"),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    subcategory = models.ForeignKey(
        SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    brand_obj = models.ForeignKey(
        Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    sku = models.CharField(max_length=60, blank=True, unique=True, null=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    moq = models.PositiveIntegerField(default=1, help_text="Minimum Order Quantity")
    unit = models.CharField(max_length=30, default="pcs", help_text="e.g. pcs, kg, box, carton")
    pack_quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of single items in one packet/bundle",
    )
    single_product_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price of one item if bought separately",
    )
    packet_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual packet/bundle selling price",
    )
    net_quantity_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Numeric net quantity for one packet/unit",
    )
    net_quantity_unit = models.CharField(
        max_length=20,
        blank=True,
        choices=NET_QUANTITY_UNIT_CHOICES,
        help_text="Unit for net quantity",
    )
    discount_percentage = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Computed bundle savings percentage",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.brand} — {self.name}"

    @property
    def base_price(self):
        """Return lowest tier price (MOQ tier)."""
        # Packet pricing takes precedence across the storefront.
        if self.packet_price and self.pack_quantity:
            try:
                return Decimal(self.packet_price) / Decimal(self.pack_quantity)
            except Exception:
                pass
        tier = self.pricing_tiers.order_by("min_qty").first()
        return tier.unit_price if tier else None

    def get_price_for_qty(self, qty):
        """Return unit price for a given quantity."""
        # If packet pricing is configured, always treat it as the final price.
        # Cart quantities are stored as single units (pcs), so we return an effective per-piece rate.
        if self.packet_price and self.pack_quantity:
            try:
                return Decimal(self.packet_price) / Decimal(self.pack_quantity)
            except Exception:
                pass
        applicable = (
            self.pricing_tiers.filter(min_qty__lte=qty)
            .order_by("-min_qty")
            .first()
        )
        if applicable:
            return applicable.unit_price
        return self.base_price

    def sync_discount_from_pack_pricing(self):
        if not (self.pack_quantity and self.single_product_price and self.packet_price):
            self.discount_percentage = None
            return
        total_single = Decimal(self.single_product_price) * Decimal(self.pack_quantity)
        if total_single <= 0:
            self.discount_percentage = None
            return
        self.discount_percentage = (Decimal("1") - (Decimal(self.packet_price) / total_single)) * Decimal("100")

    class Meta:
        ordering = ["name"]


class ProductPlacement(models.Model):
    """
    Extra category/subcategory paths where the same Product appears (one SKU / one inventory row).
    Product.category / Product.subcategory remain the canonical storefront defaults;
    placements list every browse path including additional categories.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="placements",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="product_placements",
    )
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="product_placements",
    )

    class Meta:
        verbose_name = "product placement"
        verbose_name_plural = "product placements"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "category", "subcategory"],
                name="catalog_productplacement_unique_cat_sub",
            ),
        ]

    def __str__(self):
        sub = f" / {self.subcategory.name}" if self.subcategory_id else ""
        return f"{self.product_id} → {self.category.name}{sub}"


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


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=120, blank=True, help_text="e.g. 200ml, 1kg pack, Twin pack")
    size_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    size_unit = models.CharField(max_length=20, blank=True, help_text="e.g. ml, g, kg, l")
    pack_size = models.PositiveIntegerField(default=1)
    sku = models.CharField(max_length=80, blank=True, unique=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        label = self.name or "Default"
        return f"{self.product.name} — {label}"

    class Meta:
        ordering = ["product__name", "id"]
