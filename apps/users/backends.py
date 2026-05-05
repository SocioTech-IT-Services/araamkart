"""Allow Django admin (and session auth) with email OR 10-digit Indian mobile."""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


def _normalize_phone_digits(phone_raw):
    digits = "".join(c for c in (phone_raw or "") if c.isdigit())
    if len(digits) >= 10:
        return digits[-10:]
    return digits


class EmailOrPhoneBackend(ModelBackend):
    """
    USERNAME_FIELD is email, but the admin login field can accept:
    - full email (same as default), or
    - 10-digit mobile (matches stored phone or legacy formatted phone).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if not username or password is None:
            return None

        username = username.strip()
        user = None

        if "@" in username:
            email = UserModel.objects.normalize_email(username)
            user = UserModel.objects.filter(email__iexact=email).first()
        else:
            norm = _normalize_phone_digits(username)
            if len(norm) != 10:
                return None
            user = UserModel.objects.filter(phone=norm).first()
            if user is None:
                qs = UserModel.objects.exclude(phone__isnull=True).exclude(phone="").only("id", "phone")
                for candidate in qs:
                    if _normalize_phone_digits(candidate.phone) == norm:
                        user = UserModel.objects.get(pk=candidate.pk)
                        break

        if user is None:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
