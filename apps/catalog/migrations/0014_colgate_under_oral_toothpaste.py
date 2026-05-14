"""Attach Colgate products to Oral → Toothpaste (leaf) under Personal care and hygiene."""

from django.db import migrations
from django.db.models import Q


def forwards(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    SubCategory = apps.get_model("catalog", "SubCategory")
    Product = apps.get_model("catalog", "Product")
    ProductPlacement = apps.get_model("catalog", "ProductPlacement")

    cat = (
        Category.objects.filter(name="Personal care and hygiene").first()
        or Category.objects.filter(name="Personal Care & Hygiene").first()
    )
    if not cat:
        return

    oral = SubCategory.objects.filter(
        category_id=cat.pk,
        parent_id__isnull=True,
        name__iexact="Oral",
    ).first()
    if not oral:
        return

    # Browse filters use leaf subcategories; Oral is a parent — use Toothpaste under Oral.
    leaf = (
        SubCategory.objects.filter(parent_id=oral.pk, name__iexact="Toothpaste").first()
        or SubCategory.objects.filter(parent_id=oral.pk).order_by("order", "pk").first()
    )
    if not leaf:
        return

    qs = Product.objects.filter(
        Q(name__icontains="colgate") | Q(brand__icontains="colgate")
    )
    for p in qs.iterator():
        Product.objects.filter(pk=p.pk).update(
            category_id=cat.pk,
            subcategory_id=leaf.pk,
        )
        ProductPlacement.objects.filter(product_id=p.pk).update(
            category_id=cat.pk,
            subcategory_id=leaf.pk,
        )


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0013_games_top_level_remove_household_games_group"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
