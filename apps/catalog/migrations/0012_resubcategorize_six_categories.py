"""Re-create subcategories under the six top-level categories (0011 removed them)."""

from django.db import migrations

from apps.catalog.category_tree_data import noop_reverse, seed_subcategories


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0011_categories_six_only"),
    ]

    operations = [
        migrations.RunPython(seed_subcategories, noop_reverse),
    ]
