from django.db import migrations, models


def populate_packet_sizes(apps, schema_editor):
    CartItem = apps.get_model("orders", "CartItem")
    OrderItem = apps.get_model("orders", "OrderItem")

    for item in CartItem.objects.select_related("product").iterator():
        product = item.product
        packet_size = int(getattr(product, "pack_quantity", None) or 1)
        if packet_size < 1:
            packet_size = 1
        CartItem.objects.filter(pk=item.pk).update(packet_size=packet_size)

    for item in OrderItem.objects.select_related("product").iterator():
        product = item.product
        packet_size = int(getattr(product, "pack_quantity", None) or 1) if product else 1
        if packet_size < 1:
            packet_size = 1
        OrderItem.objects.filter(pk=item.pk).update(packet_size=packet_size)


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_order_savings_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="cartitem",
            name="packet_size",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="packet_size",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.RunPython(populate_packet_sizes, migrations.RunPython.noop),
    ]
