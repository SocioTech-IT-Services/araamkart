"""Users app — Django Admin"""
from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPRecord


class EmailOrPhoneAdminAuthenticationForm(AdminAuthenticationForm):
    """Login field accepts email (USERNAME_FIELD) or 10-digit mobile — see EmailOrPhoneBackend."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email or phone number"
        self.fields["username"].widget.attrs.setdefault(
            "placeholder",
            "you@example.com or 9876543210",
        )


admin.site.login_form = EmailOrPhoneAdminAuthenticationForm


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "phone", "full_name", "business_name", "is_verified", "is_admin", "date_joined")
    list_filter = ("is_admin", "is_verified", "is_active")
    search_fields = ("email", "phone", "full_name", "business_name")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("email", "phone", "password")}),
        ("Personal Info", {"fields": ("full_name", "business_name", "address")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_admin", "is_verified", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("date_joined", "last_login")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "phone", "full_name", "business_name", "password1", "password2"),
        }),
    )
    readonly_fields = ("date_joined", "last_login")


@admin.register(OTPRecord)
class OTPRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "otp_code", "purpose", "is_used", "created_at", "expires_at")
    list_filter = ("purpose", "is_used")
    search_fields = ("user__email", "user__phone", "otp_code")
    readonly_fields = ("created_at",)
