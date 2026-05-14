"""Keep only six store categories; merge all former categories into them and drop subcategories."""

from django.db import migrations
from django.utils.text import slugify


# Exact display names (order = homepage / nav order).
FINAL_CATEGORIES = [
    ("Personal care and hygiene", 1),
    ("Household essentials", 2),
    ("Utilities", 3),
    ("Baby care", 4),
    ("Stationery", 5),
    ("Female hygiene", 6),
]

# Map legacy Category.name → final category name.
OLD_TO_NEW = {
    "Personal Care & Hygiene": "Personal care and hygiene",
    "Oral Care": "Personal care and hygiene",
    "Skin Care / Creams & Lotion": "Personal care and hygiene",
    "Vaseline & Lip Care": "Personal care and hygiene",
    "Perfume & Fragrance": "Personal care and hygiene",
    "Razor & Grooming": "Personal care and hygiene",
    "Household Essentials": "Household essentials",
    "Utilities": "Utilities",
    "Games": "Household essentials",
    "Baby Care": "Baby care",
    "Stationery": "Stationery",
    "Female Hygiene": "Female hygiene",
    "Daily Essentials": "Household essentials",
}


def forwards(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    SubCategory = apps.get_model("catalog", "SubCategory")
    Product = apps.get_model("catalog", "Product")
    ProductPlacement = apps.get_model("catalog", "ProductPlacement")

    Product.objects.all().update(subcategory_id=None)
    ProductPlacement.objects.all().update(subcategory_id=None)
    SubCategory.objects.all().delete()

    survivors = {}

    for final_name, order in FINAL_CATEGORIES:
        sources = [old for old, new in OLD_TO_NEW.items() if new == final_name]
        sources.append(final_name)
        cat = Category.objects.filter(name__in=sources).order_by("pk").first()
        if cat:
            cat.name = final_name
            cat.slug = slugify(final_name)
            cat.order = order
            cat.is_active = True
            cat.save()
            survivors[final_name] = cat
        else:
            survivors[final_name] = Category.objects.create(
                name=final_name,
                slug=slugify(final_name),
                order=order,
                is_active=True,
            )

    survivor_ids = {c.pk for c in survivors.values()}

    for c in list(Category.objects.exclude(pk__in=survivor_ids)):
        tgt_name = OLD_TO_NEW.get(c.name)
        if tgt_name is None:
            tgt_name = "Household essentials"
        tgt = survivors[tgt_name]
        Product.objects.filter(category_id=c.pk).update(category_id=tgt.pk)
        ProductPlacement.objects.filter(category_id=c.pk).update(category_id=tgt.pk)
        c.delete()


def backwards(apps, schema_editor):
    # Irreversible data migration.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0010_product_placement"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
