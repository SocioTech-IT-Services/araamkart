"""Treat Utilities > Tapes and Stationery > Cellotapes as the same product path."""

from django.db import migrations
from django.db.models import Q


def _root_subcategory(SubCategory, category_name, subcategory_name):
    return SubCategory.objects.filter(
        category__name__iexact=category_name,
        parent_id__isnull=True,
        name__iexact=subcategory_name,
    ).select_related("category").first()


def _ensure_placement(ProductPlacement, product_id, category_id, subcategory_id):
    ProductPlacement.objects.get_or_create(
        product_id=product_id,
        category_id=category_id,
        subcategory_id=subcategory_id,
    )


def forwards(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    SubCategory = apps.get_model("catalog", "SubCategory")
    ProductPlacement = apps.get_model("catalog", "ProductPlacement")

    tapes = _root_subcategory(SubCategory, "Utilities", "Tapes")
    cellotapes = _root_subcategory(SubCategory, "Stationery", "Cellotapes")
    if not (tapes and cellotapes):
        return

    products = Product.objects.filter(
        Q(category_id=tapes.category_id, subcategory_id=tapes.pk)
        | Q(category_id=cellotapes.category_id, subcategory_id=cellotapes.pk)
        | Q(placements__category_id=tapes.category_id, placements__subcategory_id=tapes.pk)
        | Q(placements__category_id=cellotapes.category_id, placements__subcategory_id=cellotapes.pk)
    ).distinct()

    for product in products.iterator():
        _ensure_placement(ProductPlacement, product.pk, tapes.category_id, tapes.pk)
        _ensure_placement(ProductPlacement, product.pk, cellotapes.category_id, cellotapes.pk)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0014_colgate_under_oral_toothpaste"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
