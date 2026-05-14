# Generated manually — line-level variant for packet products

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0017_productvariant_mrp"),
        ("orders", "0005_order_cancellation_reason"),
    ]

    operations = [
        migrations.AddField(
            model_name="cartitem",
            name="product_variant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cart_items",
                to="catalog.productvariant",
            ),
        ),
    ]
