from django.db import migrations


def forwards(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    Category.objects.get_or_create(
        slug="daily-essentials",
        defaults={
            "name": "Daily essentials",
            "icon": "✨",
            "description": "Everyday must-haves for your store",
            "is_active": True,
            "order": 7,
        },
    )


def backwards(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    Category.objects.filter(slug="daily-essentials").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
