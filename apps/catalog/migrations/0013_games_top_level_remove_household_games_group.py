"""Add top-level Games category; move leaves out of Household's 'Games' subcategory group."""

from django.db import migrations
from django.utils.text import slugify


GAMES_LEAVES = ["Playing Cards", "Housie Books", "Tennis Balls", "Balloons"]


def _unique_root_slug(SubCategory, category_id, base_slug):
    slug = base_slug[:95] or "item"
    n = 2
    while SubCategory.objects.filter(
        category_id=category_id, parent_id__isnull=True, slug=slug
    ).exists():
        slug = f"{base_slug[:90]}-{n}"
        n += 1
    return slug


def forwards(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    SubCategory = apps.get_model("catalog", "SubCategory")

    games_cat, created = Category.objects.get_or_create(
        name="Games",
        defaults={
            "slug": "games",
            "is_active": True,
            "order": 4,
        },
    )
    if not created:
        games_cat.slug = "games"
        games_cat.is_active = True
        games_cat.save()

    household = (
        Category.objects.filter(name="Household essentials").first()
        or Category.objects.filter(name="Household Essentials").first()
    )
    if household:
        games_parent = (
            SubCategory.objects.filter(
                category_id=household.pk,
                parent_id__isnull=True,
            )
            .filter(name__iexact="Games")
            .first()
        )
        if games_parent:
            for child in list(SubCategory.objects.filter(parent_id=games_parent.pk)):
                child.category_id = games_cat.pk
                child.parent_id = None
                base = slugify(child.name)[:95] or "item"
                child.slug = _unique_root_slug(SubCategory, games_cat.pk, base)
                child.save()
            games_parent.delete()

    # Ensure browse leaves exist under Games (covers partial / empty states).
    for i, leaf in enumerate(GAMES_LEAVES, start=1):
        if SubCategory.objects.filter(
            category_id=games_cat.pk, parent_id__isnull=True, name=leaf
        ).exists():
            continue
        base = slugify(leaf)[:95] or "item"
        slug = _unique_root_slug(SubCategory, games_cat.pk, base)
        SubCategory.objects.create(
            category_id=games_cat.pk,
            parent_id=None,
            name=leaf,
            slug=slug,
            is_active=True,
            order=i,
        )

    order_spec = [
        ("Personal care and hygiene", 1),
        ("Household essentials", 2),
        ("Utilities", 3),
        ("Games", 4),
        ("Baby care", 5),
        ("Stationery", 6),
        ("Female hygiene", 7),
    ]
    for name, ord in order_spec:
        Category.objects.filter(name=name).update(order=ord)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0012_resubcategorize_six_categories"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
