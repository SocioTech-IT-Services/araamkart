"""Users app models — Custom User + OTP"""
import random
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        if not email and not phone:
            raise ValueError("Either email or phone is required.")
        if email:
            email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_verified", True)
        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=120)
    business_name = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return self.email or self.phone or self.full_name

    def normalized_phone_digits(self):
        """Last 10 digits for Indian mobile, or empty if not enough digits."""
        if not self.phone:
            return ""
        digits = "".join(c for c in self.phone if c.isdigit())
        if len(digits) >= 10:
            return digits[-10:]
        return digits

    @property
    def is_delivery_only_staff(self):
        """True when this account is limited to delivery ops (see settings.DELIVERY_ONLY_STAFF_PHONES_SET)."""
        from django.conf import settings

        n = self.normalized_phone_digits()
        if len(n) != 10:
            return False
        return n in getattr(settings, "DELIVERY_ONLY_STAFF_PHONES_SET", frozenset())

    @property
    def can_use_delivery_ops(self):
        """Delivery board + order status API: staff/admin/superuser, or delivery-only phones from settings."""
        if not self.is_active:
            return False
        if self.is_superuser or self.is_admin or self.is_staff:
            return True
        return self.is_delivery_only_staff

    @property
    def can_access_admin_panel(self):
        """
        Custom admin (/orders/admin-panel/), inventory, product APIs.
        Only superusers and users with is_admin. Plain is_staff (no is_admin) = delivery ops only.
        Delivery-only phones (settings) never get this flag.
        """
        if not self.is_active:
            return False
        if self.is_superuser:
            return True
        if self.is_delivery_only_staff:
            return False
        if self.is_admin:
            return True
        return False

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class OTPRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(
        max_length=20,
        choices=[("login", "Login"), ("register", "Register"), ("reset", "Password Reset")],
        default="login",
    )
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    @classmethod
    def generate_otp(cls, user, purpose="login"):
        # Invalidate previous unused OTPs for same user+purpose
        cls.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)
        otp = str(random.randint(100000, 999999))
        return cls.objects.create(
            user=user,
            otp_code=otp,
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP {self.otp_code} for {self.user} [{self.purpose}]"

    class Meta:
        ordering = ["-created_at"]
