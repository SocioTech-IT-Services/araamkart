"""Move Naphthalin balls from Household essentials to Utilities (flat)."""

from django.db import migrations
from django.db.models import Max
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

    label = "Naphthalin balls"
    candidates = list(SubCategory.objects.filter(name__iexact=label).order_by("pk"))
    util_flat = [s for s in candidates if s.category_id == utilities.pk and s.parent_id is None]

    if util_flat:
        destination = util_flat[0]
        sources = [s for s in candidates if s.pk != destination.pk]
    else:
        sources = list(candidates)
        destination = None

    next_order = SubCategory.objects.filter(
        category_id=utilities.pk,
        parent_id__isnull=True,
    ).aggregate(m=Max("order"))["m"]
    next_order = (next_order or 0) + 1

    if destination is None:
        if sources:
            destination = sources.pop(0)
            destination.category_id = utilities.pk
            destination.parent_id = None
            destination.order = next_order
            destination.slug = _unique_slug(
                SubCategory,
                utilities.pk,
                None,
                label,
                exclude_pk=destination.pk,
            )
            destination.is_active = True
            destination.save()
        else:
            destination = SubCategory.objects.create(
                category_id=utilities.pk,
                parent_id=None,
                name=label,
                slug=_unique_slug(SubCategory, utilities.pk, None, label),
                is_active=True,
                order=next_order,
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

    Product.objects.filter(subcategory_id=destination.pk).update(
        category_id=utilities.pk,
        subcategory_id=destination.pk,
    )
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
        ("catalog", "0017_productvariant_mrp"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
