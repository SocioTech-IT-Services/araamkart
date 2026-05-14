# Generated manually — MRP per packet for variant PDP / inventory

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0016_move_candles_to_utilities"),
    ]

    operations = [
        migrations.AddField(
            model_name="productvariant",
            name="mrp",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="List/MRP for one packet (bundle MRP).",
                max_digits=12,
                null=True,
            ),
        ),
    ]
