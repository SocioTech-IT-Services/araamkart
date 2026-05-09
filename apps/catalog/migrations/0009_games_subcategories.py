"""Add Games category leaves after nested taxonomy seed (Games was omitted from 0008)."""

from django.db import migrations
from django.utils.text import slugify


def forwards(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    SubCategory = apps.get_model("catalog", "SubCategory")
    try:
        cat = Category.objects.get(name="Games")
    except Category.DoesNotExist:
        return
    if SubCategory.objects.filter(category=cat).exists():
        return
    names = ["Playing Cards", "Housie Books", "Tennis Balls", "Balloons"]
    for order, name in enumerate(names, start=1):
        base = slugify(name)[:95] or "item"
        slug = base
        n = 2
        while SubCategory.objects.filter(category=cat, parent_id=None, slug=slug).exists():
            slug = f"{base}-{n}"
            n += 1
        SubCategory.objects.create(
            category=cat,
            parent=None,
            name=name,
            slug=slug,
            is_active=True,
            order=order,
        )


def backwards(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    SubCategory = apps.get_model("catalog", "SubCategory")
    try:
        cat = Category.objects.get(name="Games")
    except Category.DoesNotExist:
        return
    SubCategory.objects.filter(category=cat).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0008_subcategory_parent_tree"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
