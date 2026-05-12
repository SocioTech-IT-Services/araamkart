"""
Full category → subcategory → leaf taxonomy for seeding SubCategory rows.

Used by migration and optionally `manage.py` commands. Structure:
  Category name → list of (group_name, list_of_leaf_names).
  If list_of_leaf_names is empty, `group_name` is a single browse leaf (no children).
"""
from __future__ import annotations

from django.utils.text import slugify


def _make_slug(SubCategory, category_id: int, parent_id: int | None, name: str) -> str:
    base = slugify(name)[:95] or "item"
    slug = base
    n = 2
    while SubCategory.objects.filter(
        category_id=category_id, parent_id=parent_id, slug=slug
    ).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


def seed_subcategories(apps, schema_editor) -> None:
    Category = apps.get_model("catalog", "Category")
    SubCategory = apps.get_model("catalog", "SubCategory")
    Product = apps.get_model("catalog", "Product")

    Product.objects.all().update(subcategory_id=None)
    SubCategory.objects.all().delete()

    # Plan keys are canonical (post–0011 names). Also match legacy names from 0005 for
    # migrations that run seed before category rename (e.g. 0008).
    category_lookup_names: dict[str, list[str]] = {
        "Personal care and hygiene": ["Personal Care & Hygiene", "Personal care and hygiene"],
        "Household essentials": ["Household Essentials", "Household essentials"],
        "Utilities": ["Utilities"],
        "Baby care": ["Baby Care", "Baby care"],
        "Stationery": ["Stationery"],
        "Female hygiene": ["Female Hygiene", "Female hygiene"],
        "Games": ["Games"],
    }

    personal_care = [
        (
            "Hair Care",
            [
                "Shampoo",
                "Conditioner",
                "Hair oil",
                "Hair serum",
                "Hair cream",
                "Hair styling gel",
                "Hair wax",
                "Hair color",
                "Henna",
                "Shampoo hair color",
            ],
        ),
        ("Oral", ["Toothpaste", "Toothbrush", "Mouth wash"]),
        (
            "Creams and lotion",
            [
                "Antiseptic cream",
                "Fairness cream",
                "Nourishing and moisturising cream",
                "Sunscreen",
                "Face serum",
                "Mens cream",
                "Mens face wash",
                "Face wash",
                "Anti-aging cream",
                "BB cream",
                "CC cream",
                "Foundation",
                "Compact",
                "Glycerin",
                "Cold cream",
                "Face pack",
                "Face scrub",
                "Bathing soap and body wash",
                "Hand wash",
                "Hand santizer",
                "Anteseptic cream and liquid",
                "Ears bud",
                "Adult diapers",
                "Body oil",
            ],
        ),
        ("Vaseline and lip balms", ["Vaseline petroleum jelly", "Pomle"]),
        (
            "Perfume Fragrance",
            ["Perfume", "Deodorant", "Pocket deodorant", "Roll on in perfume"],
        ),
        (
            "Razor and blades",
            [
                "Blades",
                "Razor",
                "Women razor",
                "Shaving lotion",
                "Shaving foam",
                "Shaving brush",
            ],
        ),
        ("Bleach and hair remover", []),
        ("Vix and Balm", []),
    ]

    household = [
        (
            "Toilet cleaner",
            [
                "Toilet cleaner",
                "Glass cleaner",
                "Lyzol",
                "Bathroom cleaner",
                "Feniyle",
                "Bleaching powder",
                "Toilet brush",
                "Bathroom air freshener",
            ],
        ),
        ("Insects repellent", []),
        (
            "Cleaning essential",
            [
                "Utensils Scrub",
                "Cloth washing brush",
                "Floor brush",
                "Dishwasher bar",
                "Dishwasher gel",
                "Clothes detergent",
                "Naphthalin balls",
                "Insence sticks",
            ],
        ),
        ("Shoes brush and polish", []),
    ]

    utilities_flat = [
        "Batteries",
        "Torch light",
        "Glue and gums",
        "Tapes",
        "Scissors",
        "Nail cutter",
        "Needles and threads",
        "Nail remover",
        "Cotton",
        "Combs",
        "Hankerchief",
        "Rope",
        "Lock and keys",
        "Mirrors",
        "Saftty pin",
        "Lighters",
        "Candles",
        "Clothe clips",
        "Bandages",
        "Toilet paper",
        "Bulb",
        "Drawing pin",
    ]

    baby_flat = [
        "Baby soap",
        "Baby cream",
        "Baby powder",
        "Baby oil",
        "Baby shampoo",
        "Baby lotion",
        "Baby hair oil",
        "Baby body wash",
        "Baby diapers",
        "Baby vipes",
        "Anti rashes cream",
        "Baby nipple and soother",
        "Teether",
        "Baby bottles",
        "Baby gripe water and mixtures",
        "Baby gift set",
    ]

    stationery_flat = [
        "Plain notebook",
        "Ruled notebook",
        "Gell Pen",
        "Ball pen",
        "Pencil",
        "Rubber",
        "Sharpner",
        "Lid pencils",
        "Lid",
        "Marker pen",
        "Highlighter",
        "Scale",
        "Correction pen",
        "Scissors",
        "Cellotapes",
        "Staplers and pin",
        "Pocket dairies and notebooks",
        "Color pencils",
        "Sceth pen",
        "Wax crayons",
        "Plastic crayons",
        "Water color",
        "Geometry box",
        "Book cover",
        "Chalk",
        "Slid",
        "Exam board",
        "Glue stics and gum",
    ]

    female_flat = [
        "Sanitary pads",
        "Panty liner",
        "Veet",
        "Hair remover",
        "Razor",
    ]

    games_flat = ["Playing Cards", "Housie Books", "Tennis Balls", "Balloons"]

    # Category names must match `0011_categories_six_only` / home page exactly.
    plan: list[tuple[str, list[tuple[str, list[str]]] | list[str]]] = [
        ("Personal care and hygiene", personal_care),
        ("Household essentials", household),
        ("Utilities", utilities_flat),
        ("Games", games_flat),
        ("Baby care", baby_flat),
        ("Stationery", stationery_flat),
        ("Female hygiene", female_flat),
    ]

    for cat_name, spec in plan:
        cat = None
        for try_name in category_lookup_names.get(cat_name, [cat_name]):
            cat = Category.objects.filter(name=try_name).first()
            if cat:
                break
        if not cat:
            cat = Category.objects.create(
                name=cat_name,
                slug=slugify(cat_name)[:100],
                is_active=True,
                order=0,
            )

        order = 0

        if isinstance(spec, list) and spec and isinstance(spec[0], str):
            # Flat category (Utilities, Baby, Stationery, Female)
            for leaf_name in spec:
                order += 1
                SubCategory.objects.create(
                    category=cat,
                    parent=None,
                    name=leaf_name,
                    slug=_make_slug(SubCategory, cat.pk, None, leaf_name),
                    is_active=True,
                    order=order,
                )
            continue

        # Nested: list of (group_name, leaves)
        for group_name, leaves in spec:
            order += 1
            parent = SubCategory.objects.create(
                category=cat,
                parent=None,
                name=group_name,
                slug=_make_slug(SubCategory, cat.pk, None, group_name),
                is_active=True,
                order=order,
            )
            if not leaves:
                continue
            child_order = 0
            for leaf_name in leaves:
                child_order += 1
                SubCategory.objects.create(
                    category=cat,
                    parent=parent,
                    name=leaf_name,
                    slug=_make_slug(SubCategory, cat.pk, parent.pk, leaf_name),
                    is_active=True,
                    order=child_order,
                )


def noop_reverse(apps, schema_editor) -> None:
    pass
