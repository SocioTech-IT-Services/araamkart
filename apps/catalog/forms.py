"""Catalog forms — staff product management"""
from decimal import Decimal

from django import forms

from .models import Product, PricingTier, SubCategory, Brand


class AdminProductForm(forms.ModelForm):
    """Single list price = first MOQ tier (min_qty=1). For extra tiers, use Django Admin."""

    unit_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        label="Unit price (₹)",
        help_text="Base price per unit for the minimum order quantity. Additional volume tiers can be set in Django Admin.",
    )

    class Meta:
        model = Product
        fields = [
            "category",
            "subcategory",
            "name",
            "sku",
            "brand",
            "brand_obj",
            "description",
            "image",
            "stock",
            "moq",
            "unit",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "sku": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional unique SKU"}),
            "brand": forms.TextInput(attrs={"class": "form-control"}),
            "brand_obj": forms.Select(attrs={"class": "form-control"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "moq": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "unit": forms.TextInput(attrs={"class": "form-control", "placeholder": "pcs, kg, box…"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "subcategory": forms.Select(attrs={"class": "form-control"}),
            "image": forms.FileInput(
                attrs={
                    "class": "form-control file-input admin-primary-image-input",
                    "accept": "image/jpeg,image/png,image/webp,image/gif",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "image": "Primary image (catalog & product page hero)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Category

        self.fields["category"].queryset = Category.objects.all().order_by("order", "name")
        self.fields["subcategory"].queryset = SubCategory.objects.none()
        self.fields["brand_obj"].queryset = Brand.objects.filter(is_active=True).order_by("name")
        self.fields["subcategory"].required = False
        self.fields["brand_obj"].required = False

        if self.instance.pk and self.instance.category_id:
            self.fields["subcategory"].queryset = SubCategory.objects.filter(
                category_id=self.instance.category_id, is_active=True
            ).order_by("order", "name")

        category_id = self.data.get("category")
        if category_id:
            try:
                self.fields["subcategory"].queryset = SubCategory.objects.filter(
                    category_id=int(category_id), is_active=True
                ).order_by("order", "name")
            except (TypeError, ValueError):
                pass

        if self.instance.pk:
            tier = self.instance.pricing_tiers.order_by("min_qty").first()
            if tier:
                self.fields["unit_price"].initial = tier.unit_price

    def save(self, commit=True):
        product = super().save(commit=False)
        price = self.cleaned_data["unit_price"]
        if product.brand_obj and not product.brand:
            product.brand = product.brand_obj.name
        if commit:
            product.save()
            self._sync_base_tier(product, price)
        return product

    def _sync_base_tier(self, product, price):
        tier = product.pricing_tiers.order_by("min_qty").first()
        if tier:
            tier.min_qty = 1
            tier.unit_price = price
            tier.max_qty = None
            tier.save()
        else:
            PricingTier.objects.create(
                product=product,
                min_qty=1,
                max_qty=None,
                unit_price=price,
                label="",
            )
