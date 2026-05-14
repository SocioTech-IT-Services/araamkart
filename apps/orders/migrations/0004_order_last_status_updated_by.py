from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("orders", "0003_packet_size_snapshots"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="last_status_updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="orders_delivery_updates",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
