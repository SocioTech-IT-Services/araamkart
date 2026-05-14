# Generated manually — delivery-only staff (phone allowlist in settings)

from django.db import migrations


def _digits10(phone):
    if not phone:
        return ""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) >= 10:
        return digits[-10:]
    return digits


def apply_delivery_only_flags(apps, schema_editor):
    """9485317830: delivery ops via settings list — not Django-admin / inventory staff."""
    User = apps.get_model("users", "User")
    target = "9485317830"
    for u in User.objects.exclude(phone__isnull=True).exclude(phone="").iterator():
        if _digits10(u.phone) == target:
            User.objects.filter(pk=u.pk).update(is_staff=False, is_admin=False)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(apply_delivery_only_flags, noop_reverse),
    ]
