"""Create or upgrade a superuser from .env (never commit real passwords)."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from decouple import config

from apps.users.backends import _normalize_phone_digits


class Command(BaseCommand):
    help = (
        "Create or update a superuser using ADMIN_PHONE + ADMIN_EMAIL from settings "
        "and BOOTSTRAP_ADMIN_PASSWORD from .env. Set the password only for this one run, then remove it from .env."
    )

    def handle(self, *args, **options):
        password = config("BOOTSTRAP_ADMIN_PASSWORD", default="").strip()
        if not password:
            self.stderr.write(
                self.style.ERROR(
                    "Set BOOTSTRAP_ADMIN_PASSWORD in your local .env, then run:\n"
                    "  python manage.py bootstrap_admin\n"
                    "Then delete BOOTSTRAP_ADMIN_PASSWORD from .env so it is not left on disk."
                )
            )
            return

        phone_raw = (getattr(settings, "ADMIN_PHONE", None) or "").strip()
        digits = _normalize_phone_digits(phone_raw)
        if len(digits) != 10:
            self.stderr.write(
                self.style.ERROR(
                    "Set ADMIN_PHONE in .env to a valid Indian mobile (+91 optional). "
                    f"Current value normalizes to {digits!r} (need 10 digits)."
                )
            )
            return

        email = (getattr(settings, "ADMIN_EMAIL", None) or "").strip()
        if not email:
            email = f"admin+{digits}@localhost.local"

        full_name = config("BOOTSTRAP_ADMIN_FULL_NAME", default="Admin").strip() or "Admin"

        try:
            validate_password(password)
        except ValidationError as exc:
            for msg in exc.messages:
                self.stderr.write(self.style.ERROR(msg))
            return

        User = get_user_model()
        user = User.objects.filter(phone=digits).first()
        if user is None:
            user = User.objects.filter(email__iexact=email).first()

        if user:
            conflict = (
                User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists()
            )
            if conflict:
                self.stderr.write(
                    self.style.ERROR(
                        f"Email {email} is already used by another account. "
                        "Change ADMIN_EMAIL in .env or free that email first."
                    )
                )
                return
            user.email = email
            user.phone = digits
            user.full_name = full_name
            user.set_password(password)
            user.is_active = True
            user.is_staff = True
            user.is_admin = True
            user.is_superuser = True
            user.is_verified = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Updated superuser pk={user.pk} — sign in with phone {digits} or email {user.email}"
                )
            )
            return

        if User.objects.filter(email__iexact=email).exists():
            self.stderr.write(
                self.style.ERROR(
                    f"No user with phone {digits}, but email {email} is taken. "
                    "Use a different ADMIN_EMAIL or attach this phone in Django admin."
                )
            )
            return

        User.objects.create_user(
            email=email,
            phone=digits,
            password=password,
            full_name=full_name,
            is_staff=True,
            is_admin=True,
            is_superuser=True,
            is_verified=True,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Created superuser — sign in with phone {digits} or email {email}"
            )
        )
