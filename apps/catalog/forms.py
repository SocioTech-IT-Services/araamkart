"""Catalog forms — staff product management"""
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from .models import Product, PricingTier, SubCategory, Brand, ProductPlacement


EQUIVALENT_PRODUCT_PATHS = (
    (("Utilities", "Tapes"), ("Stationery", "Cellotapes")),
)


def find_existing_product_for_merge(cleaned_data):
    """
    Same SKU, or same normalized name + brand (FK or text) → one inventory row.
    """
    sku = (cleaned_data.get("sku") or "").strip()
    if sku:
        found = Product.objects.filter(sku__iexact=sku).first()
        if found:
            return found
    name = (cleaned_data.get("name") or "").strip()
    if not name:
        return None
    brand_obj = cleaned_data.get("brand_obj")
    brand_txt = (cleaned_data.get("brand") or "").strip()
    if brand_obj:
        return Product.objects.filter(brand_obj=brand_obj, name__iexact=name).first()
    if brand_txt:
        return Product.objects.filter(brand__iexact=brand_txt, name__iexact=name).first()
    return None


def _create_product_placement(product, category_id, subcategory_id):
    qs = ProductPlacement.objects.filter(product_id=product.pk, category_id=category_id)
    if subcategory_id is None:
        qs = qs.filter(subcategory_id__isnull=True)
    else:
        qs = qs.filter(subcategory_id=subcategory_id)
    if qs.exists():
        return qs.first()
    return ProductPlacement.objects.create(
        product_id=product.pk,
        category_id=category_id,
        subcategory_id=subcategory_id,
    )


def _find_subcategory_path(category_name, subcategory_name):
    return SubCategory.objects.filter(
        category__name__iexact=category_name,
        parent__isnull=True,
        name__iexact=subcategory_name,
    ).select_related("category").first()


def _ensure_equivalent_product_placements(product, category_id, subcategory_id):
    if not subcategory_id:
        return
    current = (
        SubCategory.objects.filter(pk=subcategory_id, category_id=category_id)
        .select_related("category")
        .first()
    )
    if not current:
        return

    current_key = (current.category.name.lower(), current.name.lower())
    for left, right in EQUIVALENT_PRODUCT_PATHS:
        left_key = (left[0].lower(), left[1].lower())
        right_key = (right[0].lower(), right[1].lower())
        if current_key == left_key:
            target = _find_subcategory_path(*right)
        elif current_key == right_key:
            target = _find_subcategory_path(*left)
        else:
            continue
        if target:
            _create_product_placement(product, target.category_id, target.pk)


def ensure_product_placement(product, category_id=None, subcategory_id=None):
    """Create placement row if missing, including known equivalent category paths."""
    cid = category_id if category_id is not None else product.category_id
    sid = subcategory_id if subcategory_id is not None else product.subcategory_id
    placement = _create_product_placement(product, cid, sid)
    _ensure_equivalent_product_placements(product, cid, sid)
    return placement


def build_auto_product_description(product, category=None, subcategory=None):
    """Generate a concise default description from the product's catalog/pricing fields."""
    name = (product.name or "").strip()
    brand = (product.brand_obj.name if product.brand_obj else product.brand or "").strip()
    category_name = (category.name if category else getattr(product.category, "name", "") or "").strip()
    subcategory_name = (subcategory.name if subcategory else getattr(product.subcategory, "name", "") or "").strip()

    title = " ".join(part for part in [brand, name] if part).strip() or name or "This product"
    parts = [f"{title} is available"]
    if subcategory_name and category_name:
        parts.append(f"under {category_name} > {subcategory_name}")
    elif category_name:
        parts.append(f"under {category_name}")
    parts[-1] = parts[-1] + "."

    details = []
    if product.net_quantity_value and product.net_quantity_unit:
        details.append(f"Net quantity: {product.net_quantity_value} {product.net_quantity_unit}")
    if product.pack_quantity:
        details.append(f"Items per packet: {product.pack_quantity}")
    if product.single_product_price:
        details.append(f"Single MRP: ₹{product.single_product_price}")
    if product.packet_price:
        details.append(f"Packet price: ₹{product.packet_price}")
    if product.moq:
        details.append(f"MOQ: {product.moq} {product.unit or 'pcs'}")
    if details:
        parts.append(" ".join(details) + ".")
    return " ".join(parts)


class AdminProductForm(forms.ModelForm):
    """Single list price = first MOQ tier (min_qty=1). For extra tiers, use Django Admin."""

    unit_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        label="Single S.P (₹)",
        help_text="Single selling price. Additional volume tiers can be set in Django Admin.",
    )
    pack_quantity = forms.IntegerField(
        required=False,
        min_value=1,
        label="Items qty P.Packet",
        help_text="How many single items are included in one packet.",
    )
    single_product_price = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        label="Single MRP (₹)",
        help_text="MRP of one single item.",
    )
    packet_price = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        label="Packet Price (₹)",
        help_text="Actual selling price for the full packet/bundle.",
    )
    discount_percentage = forms.DecimalField(
        required=False,
        max_digits=6,
        decimal_places=2,
        label="Discount (%)",
        help_text="Auto-calculated from pack quantity, single price, and packet price.",
        widget=forms.NumberInput(attrs={"readonly": "readonly"}),
    )
    subcategory_root = forms.ModelChoiceField(
        queryset=SubCategory.objects.none(),
        required=False,
        label="Subcategory",
        empty_label="---------",
    )
    subcategory_child = forms.ModelChoiceField(
        queryset=SubCategory.objects.none(),
        required=False,
        label="Sub-subcategory (optional)",
        empty_label="---------",
    )

    class Meta:
        model = Product
        fields = [
            "category",
            "name",
            "sku",
            "brand",
            "brand_obj",
            "description",
            "image",
            "stock",
            "moq",
            "unit",
            "pack_quantity",
            "single_product_price",
            "packet_price",
            "net_quantity_value",
            "net_quantity_unit",
            "discount_percentage",
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
            "net_quantity_value": forms.NumberInput(attrs={"class": "form-control", "min": "0.01", "step": "0.01"}),
            "net_quantity_unit": forms.Select(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-control"}),
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

        if not self.instance.pk:
            self.fields["image"].required = False

        self.fields["pack_quantity"].widget.attrs.update({"class": "form-control", "min": 1})
        self.fields["single_product_price"].widget.attrs.update(
            {"class": "form-control", "min": "0.01", "step": "0.01"}
        )
        self.fields["packet_price"].widget.attrs.update(
            {"class": "form-control", "min": "0.01", "step": "0.01"}
        )
        self.fields["net_quantity_value"].widget.attrs.update(
            {"class": "form-control", "min": "0.01", "step": "0.01", "placeholder": "e.g. 500"}
        )
        self.fields["net_quantity_unit"].widget.attrs.update({"class": "form-control"})
        self.fields["discount_percentage"].widget.attrs.update(
            {"class": "form-control", "step": "0.01", "placeholder": "Auto-calculated"}
        )
        self.fields["net_quantity_unit"].choices = [("", "Select unit"), ("ml", "ml"), ("g", "g"), ("pieces", "pieces")]

        self.fields["category"].queryset = Category.objects.all().order_by("order", "name")
        self.fields["brand_obj"].queryset = Brand.objects.filter(is_active=True).order_by("name")
        self.fields["subcategory_root"].widget.attrs.update({"class": "form-control"})
        self.fields["subcategory_child"].widget.attrs.update({"class": "form-control"})
        self.fields["brand_obj"].required = False
        self.fields["description"].required = False
        self.fields["stock"].required = False
        self.fields["moq"].required = False
        self.fields["unit"].required = False
        self.fields["net_quantity_value"].required = False
        self.fields["net_quantity_unit"].required = False
        self.fields["is_active"].required = False
        self.fields["unit_price"].required = False
        self.did_merge_existing = False

        def roots_qs(cat_id):
            return SubCategory.objects.filter(
                category_id=cat_id, parent__isnull=True, is_active=True
            ).order_by("order", "name")

        def children_qs(cat_id, root_pk):
            return SubCategory.objects.filter(
                category_id=cat_id, parent_id=root_pk, is_active=True
            ).order_by("order", "name")

        if self.instance.pk and self.instance.category_id:
            cid = self.instance.category_id
            self.fields["subcategory_root"].queryset = roots_qs(cid)
            sc = self.instance.subcategory
            if sc:
                chain = sc.ancestor_chain()
                root = chain[0]
                self.fields["subcategory_root"].initial = root
                self.fields["subcategory_child"].queryset = children_qs(cid, root.pk)
                if sc.parent_id == root.pk:
                    self.fields["subcategory_child"].initial = sc
                elif sc.pk == root.pk:
                    self.fields["subcategory_child"].initial = None
                else:
                    self.fields["subcategory_child"].initial = None
            else:
                self.fields["subcategory_child"].queryset = SubCategory.objects.none()

        category_id = self.data.get("category")
        root_pk = self.data.get("subcategory_root")
        if category_id:
            try:
                cid = int(category_id)
                self.fields["subcategory_root"].queryset = roots_qs(cid)
                if root_pk:
                    try:
                        self.fields["subcategory_child"].queryset = children_qs(cid, int(root_pk))
                    except (TypeError, ValueError):
                        pass
            except (TypeError, ValueError):
                pass

        if self.instance.pk:
            tier = self.instance.pricing_tiers.order_by("min_qty").first()
            if tier:
                self.fields["unit_price"].initial = tier.unit_price
        elif not self.fields["pack_quantity"].initial:
            self.fields["pack_quantity"].initial = 1

    def clean(self):
        cleaned = super().clean()
        root = cleaned.get("subcategory_root")
        child = cleaned.get("subcategory_child")
        if child and not root:
            raise ValidationError(
                {"subcategory_child": "Choose a subcategory before selecting a sub-subcategory."}
            )
        if root and child and child.parent_id != root.pk:
            raise ValidationError({"subcategory_child": "That sub-subcategory does not belong to the selected subcategory."})
        cat = cleaned.get("category")
        if root and cat and root.category_id != cat.pk:
            raise ValidationError({"subcategory_root": "Subcategory must belong to the selected category."})
        if child and cat and child.category_id != cat.pk:
            raise ValidationError({"subcategory_child": "Sub-subcategory must belong to the selected category."})
        return cleaned

    def save(self, commit=True):
        root = self.cleaned_data.get("subcategory_root")
        child = self.cleaned_data.get("subcategory_child")
        resolved_sub = child if child else root if root else None
        cat = self.cleaned_data.get("category")

        if commit and not self.instance.pk:
            existing = find_existing_product_for_merge(self.cleaned_data)
            if existing:
                ensure_product_placement(
                    existing,
                    category_id=cat.pk if cat else None,
                    subcategory_id=resolved_sub.pk if resolved_sub else None,
                )
                self.did_merge_existing = True
                return existing

        product = super().save(commit=False)
        product.subcategory = resolved_sub if resolved_sub else None
        price = (
            self.cleaned_data.get("unit_price")
            or self.cleaned_data.get("packet_price")
            or self.cleaned_data.get("single_product_price")
            or Decimal("1.00")
        )
        if not product.moq:
            product.moq = 1
        if product.stock is None:
            product.stock = 0
        if not product.unit:
            product.unit = "packet"
        if product.brand_obj and not product.brand:
            product.brand = product.brand_obj.name
        if not (product.description or "").strip():
            product.description = build_auto_product_description(product, cat, resolved_sub)
        product.sync_discount_from_pack_pricing()
        if commit:
            product.save()
            self._sync_base_tier(product, price)
            ensure_product_placement(product)
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
