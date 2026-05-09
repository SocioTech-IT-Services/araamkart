# Generated manually — nested subcategories + full taxonomy seed

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


def forwards(apps, schema_editor):
    from apps.catalog.category_tree_data import seed_subcategories

    seed_subcategories(apps, schema_editor)


def backwards(apps, schema_editor):
    from apps.catalog.category_tree_data import noop_reverse

    noop_reverse(apps, schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0007_product_net_quantity_unit_product_net_quantity_value"),
    ]

    operations = [
        migrations.AddField(
            model_name="subcategory",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="children",
                to="catalog.subcategory",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="subcategory",
            unique_together=set(),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.AddConstraint(
            model_name="subcategory",
            constraint=models.UniqueConstraint(
                condition=Q(parent__isnull=True),
                fields=("category", "slug"),
                name="catalog_subcat_root_slug",
            ),
        ),
        migrations.AddConstraint(
            model_name="subcategory",
            constraint=models.UniqueConstraint(
                condition=Q(parent__isnull=False),
                fields=("category", "parent", "slug"),
                name="catalog_subcat_nested_slug",
            ),
        ),
    ]
