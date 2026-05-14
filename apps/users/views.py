"""Users app — Template Views (Login, Register, Logout)"""
import logging
from urllib.parse import urlencode

from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.views import View

from .models import User

logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _safe_next(raw):
    """Allow same-site relative paths only (may include query string)."""
    if not raw:
        return None
    raw = raw.strip()
    path_only = raw.split("?")[0]
    if not path_only.startswith("/") or path_only.startswith("//"):
        return None
    return raw


def _redirect_login_failed(request):
    """After failed login — send to sign-in page with optional next preserved."""
    n = _safe_next(request.POST.get("next", ""))
    if not n:
        ref = request.META.get("HTTP_REFERER", "")
        if ref:
            from urllib.parse import urlparse

            p = urlparse(ref)
            if p.path.startswith("/") and not p.path.startswith("//"):
                n = p.path + (("?" + p.query) if p.query else "")
    q = {}
    if n:
        q["next"] = n
    url = reverse("login")
    if q:
        url = f"{url}?{urlencode(q)}"
    return redirect(url)


def _get_user_by_normalized_phone(norm_digits):
    """Resolve user by 10-digit Indian mobile (stored value may be legacy formatted)."""
    if len(norm_digits) != 10:
        return None
    u = User.objects.filter(phone=norm_digits).first()
    if u:
        return u
    for candidate in User.objects.exclude(phone__isnull=True).exclude(phone="").only("id", "phone"):
        if _normalize_phone_digits(candidate.phone) == norm_digits:
            return User.objects.get(pk=candidate.pk)
    return None


def _normalize_phone_digits(phone_raw):
    digits = "".join(c for c in (phone_raw or "") if c.isdigit())
    if len(digits) >= 10:
        return digits[-10:]
    return digits


# ── Auth Views ────────────────────────────────────────────────────────────────

class LoginView(View):
    """Customer phone login: admins go to admin panel; delivery staff go to Delivery ops; shoppers go home."""

    template_name = "auth/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            nxt = _safe_next(request.GET.get("next"))
            if nxt:
                return redirect(nxt)
            if getattr(request.user, "can_access_admin_panel", False):
                return redirect("admin_dashboard")
            if getattr(request.user, "can_use_delivery_ops", False):
                return redirect("staff_delivery_panel")
            return redirect("home")
        ctx = {"next": _safe_next(request.GET.get("next")) or ""}
        return render(request, self.template_name, ctx)

    def post(self, request):
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")

        if not phone:
            messages.error(request, "Please enter your phone number.")
            return _redirect_login_failed(request)
        if not password:
            messages.error(request, "Please enter your password.")
            return _redirect_login_failed(request)

        norm_phone = _normalize_phone_digits(phone)
        if len(norm_phone) != 10:
            messages.error(request, "Enter a valid 10-digit Indian mobile number.")
            return _redirect_login_failed(request)

        user = _get_user_by_normalized_phone(norm_phone)
        if not user:
            messages.error(request, "No account found for this phone number.")
            return _redirect_login_failed(request)
        if not user.check_password(password):
            messages.error(request, "Invalid password.")
            return _redirect_login_failed(request)

        if getattr(user, "is_delivery_only_staff", False):
            messages.error(
                request,
                "This number is for delivery staff only. Use Staff login or Admin login from the sign-in page.",
            )
            return redirect(reverse("staff_login"))

        display_name = user.full_name or user.phone or user.email or "there"
        next_ok = _safe_next(request.POST.get("next", ""))
        # Treat "/" as no deep link so staff still land on admin when signing in from the home page.
        follow_next = bool(next_ok and next_ok != "/")

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        if follow_next:
            messages.success(request, f"Welcome back, {display_name}!")
            return redirect(next_ok)

        if getattr(user, "can_access_admin_panel", False):
            messages.success(request, f"Welcome, {display_name}.")
            return redirect("admin_dashboard")
        if getattr(user, "can_use_delivery_ops", False):
            messages.success(request, f"Welcome, {display_name}.")
            return redirect("staff_delivery_panel")

        messages.success(request, f"Welcome back, {display_name}!")
        return redirect("home")


class RegisterView(View):
    template_name = "auth/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("home")
        return render(request, self.template_name)

    def post(self, request):
        full_name = request.POST.get("full_name", "").strip()
        business_name = request.POST.get("business_name", "").strip()
        phone_raw = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not full_name:
            messages.error(request, "Full name is required.")
            return render(request, self.template_name)

        norm_phone = _normalize_phone_digits(phone_raw)
        if len(norm_phone) != 10:
            messages.error(
                request,
                "Enter a valid 10-digit mobile number (same one you will use to sign in).",
            )
            return render(request, self.template_name)

        if norm_phone in getattr(settings, "DELIVERY_ONLY_STAFF_PHONES_SET", frozenset()):
            messages.error(
                request,
                "This mobile number is reserved for delivery staff. If that is you, use Staff login or Admin login from the sign-in page.",
            )
            return render(request, self.template_name)

        if not email:
            messages.error(
                request,
                "Email is required — sign-in uses both your phone and email.",
            )
            return render(request, self.template_name)

        if not password:
            messages.error(
                request,
                "Please create a password — you need it to sign in from the header.",
            )
            return render(request, self.template_name)

        try:
            validate_password(password)
        except ValidationError as e:
            for msg in e.messages:
                messages.error(request, msg)
            return render(request, self.template_name)

        # Match login modal: same email + phone + password
        if User.objects.filter(phone=norm_phone).exists():
            messages.error(request, "An account with this phone already exists. Please sign in.")
            return redirect(reverse("login"))
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "An account with this email already exists. Please sign in.")
            return redirect(reverse("login"))

        try:
            user = User.objects.create_user(
                email=email,
                phone=norm_phone,
                password=password,
                full_name=full_name,
                business_name=business_name,
            )
        except IntegrityError:
            logger.exception("Register integrity error")
            messages.error(
                request,
                "This phone or email is already registered. Try signing in instead.",
            )
            return render(request, self.template_name)
        user.is_verified = True
        user.save()

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, f"Welcome, {user.full_name or user.phone or user.email}!")
        return redirect("home")


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("home")


class ProfileView(View):
    template_name = "auth/profile.html"

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect(
                reverse("login") + "?" + urlencode({"next": request.get_full_path()})
            )
        from apps.orders.models import Order

        qs = Order.objects.filter(user=request.user).order_by("-created_at")
        recent_orders = list(qs[:8])
        order_count = qs.count()
        return render(
            request,
            self.template_name,
            {
                "user": request.user,
                "recent_orders": recent_orders,
                "order_count": order_count,
            },
        )


def _resolve_user_from_identifier(raw_ident):
    """Return User from email or 10-digit Indian phone, or None."""
    ident = (raw_ident or "").strip()
    if not ident:
        return None
    if "@" in ident:
        return User.objects.filter(email__iexact=ident).first()
    norm = _normalize_phone_digits(ident)
    if len(norm) == 10:
        return _get_user_by_normalized_phone(norm)
    return None


class StaffLoginView(View):
    """
    Dedicated staff/admin sign-in at /staff-login/ (separate from customer phone login).
    POST: identifier (work email or phone), password, portal_role=staff|admin
    """

    template_name = "auth/staff_login.html"

    def get(self, request):
        if request.user.is_authenticated and getattr(request.user, "can_use_delivery_ops", False):
            if getattr(request.user, "can_access_admin_panel", False):
                return redirect("staff_dashboard")
            return redirect("staff_delivery_panel")
        raw_role = (request.GET.get("portal_role") or "").strip().lower()
        portal_role = raw_role if raw_role in {"staff", "admin"} else "staff"
        return render(request, self.template_name, {"portal_role": portal_role})

    def post(self, request):
        identifier = (request.POST.get("identifier") or "").strip()
        password = request.POST.get("password") or ""
        portal_role = (request.POST.get("portal_role") or "staff").strip().lower()
        if portal_role not in {"staff", "admin"}:
            portal_role = "staff"

        ctx = {"portal_role": portal_role, "identifier": identifier}

        if not identifier:
            messages.error(request, "Enter your work email or phone.")
            return render(request, self.template_name, ctx, status=400)
        if not password:
            messages.error(request, "Enter your password.")
            return render(request, self.template_name, ctx, status=400)

        user = _resolve_user_from_identifier(identifier)
        if not user or not user.check_password(password):
            messages.error(request, "Invalid email/phone or password.")
            return render(request, self.template_name, ctx, status=401)

        if not user.is_active:
            messages.error(request, "This account is disabled.")
            return render(request, self.template_name, ctx, status=403)

        if not getattr(user, "can_use_delivery_ops", False):
            messages.error(
                request,
                "This account does not have staff access. Use customer sign-in (phone) from the shop.",
            )
            return render(request, self.template_name, ctx, status=403)

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        display = user.full_name or user.email or user.phone or "there"

        if portal_role == "admin" and not getattr(user, "can_access_admin_panel", False):
            messages.warning(
                request,
                "This account only has delivery team access — opening Delivery ops.",
            )
            return redirect("staff_delivery_panel")

        messages.success(request, f"Welcome, {display}.")

        if portal_role == "admin":
            return redirect("admin_dashboard_public")

        if getattr(user, "can_use_delivery_ops", False) and not getattr(user, "can_access_admin_panel", False):
            return redirect("staff_delivery_panel")

        return redirect("staff_dashboard")
