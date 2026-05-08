"""Users app — Template Views (Login, Register, Logout)"""
import logging
from urllib.parse import urlencode

from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
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
    """Single sign-in page and POST handler: redirect staff to admin dashboard, others to storefront (or next)."""

    template_name = "auth/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            nxt = _safe_next(request.GET.get("next"))
            if nxt:
                return redirect(nxt)
            if request.user.is_staff or request.user.is_admin:
                return redirect("admin_dashboard")
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

        display_name = user.full_name or user.phone or user.email or "there"
        next_ok = _safe_next(request.POST.get("next", ""))
        # Treat "/" as no deep link so staff still land on admin when signing in from the home page.
        follow_next = bool(next_ok and next_ok != "/")

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        if follow_next:
            messages.success(request, f"Welcome back, {display_name}!")
            return redirect(next_ok)

        if user.is_staff or user.is_admin:
            messages.success(request, f"Welcome, {display_name}.")
            return redirect("admin_dashboard")

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
        return render(request, self.template_name, {"user": request.user})
