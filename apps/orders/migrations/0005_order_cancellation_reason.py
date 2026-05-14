from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0004_order_last_status_updated_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="cancellation_reason",
            field=models.CharField(
                blank=True,
                help_text="Filled when staff cancels from delivery ops (e.g. didn't pick up).",
                max_length=255,
            ),
        ),
    ]
