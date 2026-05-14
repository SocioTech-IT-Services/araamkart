"""Move Candles from Household essentials to Utilities."""

from django.db import migrations
from django.db.models import Q
from django.utils.text import slugify


def _unique_slug(SubCategory, category_id, parent_id, name, exclude_pk=None):
    base = slugify(name)[:95] or "item"
    slug = base
    n = 2
    qs = SubCategory.objects.filter(category_id=category_id, parent_id=parent_id, slug=slug)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    while qs.exists():
        slug = f"{base}-{n}"
        n += 1
        qs = SubCategory.objects.filter(category_id=category_id, parent_id=parent_id, slug=slug)
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
    return slug


def _ensure_placement(ProductPlacement, product_id, category_id, subcategory_id):
    ProductPlacement.objects.get_or_create(
        product_id=product_id,
        category_id=category_id,
        subcategory_id=subcategory_id,
    )


def forwards(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    SubCategory = apps.get_model("catalog", "SubCategory")
    Product = apps.get_model("catalog", "Product")
    ProductPlacement = apps.get_model("catalog", "ProductPlacement")

    utilities = Category.objects.filter(name__iexact="Utilities").first()
    if not utilities:
        return

    sources = list(SubCategory.objects.filter(name__iexact="Candles").order_by("pk"))
    destination = SubCategory.objects.filter(
        category_id=utilities.pk,
        parent_id__isnull=True,
        name__iexact="Candles",
    ).first()

    if not destination:
        if sources:
            destination = sources[0]
            destination.category_id = utilities.pk
            destination.parent_id = None
            destination.slug = _unique_slug(
                SubCategory,
                utilities.pk,
                None,
                "Candles",
                exclude_pk=destination.pk,
            )
            destination.is_active = True
            destination.save()
        else:
            destination = SubCategory.objects.create(
                category_id=utilities.pk,
                parent_id=None,
                name="Candles",
                slug=_unique_slug(SubCategory, utilities.pk, None, "Candles"),
                is_active=True,
            )

    for source in sources:
        if source.pk == destination.pk:
            continue

        Product.objects.filter(subcategory_id=source.pk).update(
            category_id=utilities.pk,
            subcategory_id=destination.pk,
        )
        for placement in ProductPlacement.objects.filter(subcategory_id=source.pk).iterator():
            _ensure_placement(
                ProductPlacement,
                placement.product_id,
                utilities.pk,
                destination.pk,
            )
            placement.delete()
        source.delete()

    Product.objects.filter(
        Q(subcategory_id=destination.pk) | Q(name__icontains="candle") | Q(brand__icontains="candle")
    ).update(category_id=utilities.pk, subcategory_id=destination.pk)

    for product in Product.objects.filter(subcategory_id=destination.pk).iterator():
        _ensure_placement(ProductPlacement, product.pk, utilities.pk, destination.pk)

    for placement in ProductPlacement.objects.filter(subcategory_id=destination.pk).iterator():
        _ensure_placement(
            ProductPlacement,
            placement.product_id,
            utilities.pk,
            destination.pk,
        )
        if placement.category_id != utilities.pk:
            placement.delete()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0015_sync_tapes_cellotapes_placements"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
