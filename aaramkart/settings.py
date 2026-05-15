"""
AaramKart Django Settings
"""
import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# Railway sets these; used for hosts / CSRF / CORS without manual copy-paste.
_railway_public = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
_is_railway = bool(
    os.environ.get("RAILWAY_ENVIRONMENT")
    or os.environ.get("RAILWAY_PROJECT_ID")
    or os.environ.get("RAILWAY_SERVICE_ID")
)

SECRET_KEY = config("SECRET_KEY", default="django-insecure-aaramkart-dev-key-change-in-production")
DEBUG = config("DEBUG", default=True, cast=bool)
# Strip whitespace so "localhost, 127.0.0.1" matches correctly.
_hosts_from_env = [h.strip() for h in config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",") if h.strip()]
# While DEBUG is on, accept any Host header so phone/LAN (192.168.x) and runserver test client work.
if DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    _prod_hosts = list(_hosts_from_env) or ["localhost", "127.0.0.1"]
    if _railway_public and _railway_public not in _prod_hosts:
        _prod_hosts.append(_railway_public)
    ALLOWED_HOSTS = _prod_hosts

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Local apps
    "apps.users",
    "apps.catalog",
    "apps.orders",
    "apps.notifications",
]

MIDDLEWARE = [
    "aaramkart.middleware.HealthCheckMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "aaramkart.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.orders.context_processors.cart_summary",
                "apps.catalog.context_processors.nav_categories",
                "apps.catalog.context_processors.static_assets_version",
            ],
        },
    },
]

WSGI_APPLICATION = "aaramkart.wsgi.application"

# Database: PostgreSQL only (no SQLite in this project).
# Prefer OS env first so Railway linked DATABASE_URL wins over an empty DATABASE_URL= line in .env.
# Tables live wherever DATABASE_URL points if set; otherwise POSTGRES_* (default localhost:5432).
# Supabase: paste the Postgres URI into DATABASE_URL or SUPABASE_DATABASE_URL (same value).
DATABASE_URL = (
    os.environ.get("DATABASE_URL", "").strip()
    or os.environ.get("SUPABASE_DATABASE_URL", "").strip()
    or os.environ.get("SUPABASE_DB_URL", "").strip()
    or config("DATABASE_URL", default="").strip()
    or config("SUPABASE_DATABASE_URL", default="").strip()
    or config("SUPABASE_DB_URL", default="").strip()
)

if DATABASE_URL:
    parsed_db = urlparse(DATABASE_URL)
    db_options = {}
    query = parse_qs(parsed_db.query)
    if query.get("sslmode"):
        db_options["sslmode"] = query["sslmode"][0]

    db_host = parsed_db.hostname or ""
    db_port = str(parsed_db.port or "")
    if not db_port:
        db_port = "5432"

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed_db.path.lstrip("/") or "postgres",
            "USER": unquote(parsed_db.username or ""),
            "PASSWORD": unquote(parsed_db.password or ""),
            "HOST": db_host,
            "PORT": db_port,
            "OPTIONS": db_options,
            "CONN_MAX_AGE": config("DB_CONN_MAX_AGE", default=60, cast=int),
        }
    }

    # Supabase / Railway public proxy: TLS required unless URI already sets sslmode.
    _host_lc = db_host.lower()
    if "supabase" in _host_lc or "rlwy.net" in _host_lc:
        DATABASES["default"].setdefault("OPTIONS", {}).setdefault("sslmode", "require")
    if db_port == "6543":
        DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("POSTGRES_DB", default="aaramkart"),
            "USER": config("POSTGRES_USER", default="postgres"),
            "PASSWORD": config("POSTGRES_PASSWORD", default=""),
            "HOST": config("POSTGRES_HOST", default="localhost"),
            "PORT": config("POSTGRES_PORT", default="5432"),
            "CONN_MAX_AGE": config("DB_CONN_MAX_AGE", default=60, cast=int),
        }
    }
    _postg_host = (DATABASES["default"].get("HOST") or "").lower()
    if "supabase" in _postg_host:
        DATABASES["default"].setdefault("OPTIONS", {})["sslmode"] = "require"

AUTH_USER_MODEL = "users.User"
AUTHENTICATION_BACKENDS = [
    "apps.users.backends.EmailOrPhoneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
    ("product-images", BASE_DIR / "product image"),
]
STATIC_ROOT = BASE_DIR / "staticfiles"
# Bump this (or set STATIC_CACHE_BUSTER in .env) when CSS/JS changes don’t show — browsers cache /static/ aggressively.
STATIC_CACHE_BUSTER = config("STATIC_CACHE_BUSTER", default="20260618")

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Email ──────────────────────────────────────────────────────────────────
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="AaramKart <noreply@aaramkart.com>")

# ── App-specific ────────────────────────────────────────────────────────────
ADMIN_EMAIL = config("ADMIN_EMAIL", default="admin@aaramkart.com")
ADMIN_PHONE = config("ADMIN_PHONE", default="")


def _delivery_only_staff_phones_set():
    """10-digit mobiles that may use delivery ops only (no inventory / custom admin). Comma-separated in env."""
    raw = config("DELIVERY_ONLY_STAFF_PHONES", default="9485317830")
    out = set()
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        digits = "".join(c for c in chunk if c.isdigit())
        if len(digits) >= 10:
            out.add(digits[-10:])
    return frozenset(out)


DELIVERY_ONLY_STAFF_PHONES_SET = _delivery_only_staff_phones_set()
FAST2SMS_API_KEY = config("FAST2SMS_API_KEY", default="")
CALLMEBOT_API_KEY = config("CALLMEBOT_API_KEY", default="")
CALLMEBOT_PHONE = config("CALLMEBOT_PHONE", default="")

# ── DRF ────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
if _railway_public:
    _rh = f"https://{_railway_public}"
    if _rh not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS = [*CORS_ALLOWED_ORIGINS, _rh]

# Production (Railway + HTTPS): CSRF_TRUSTED_ORIGINS or auto from RAILWAY_PUBLIC_DOMAIN when DEBUG=False.
_csrf_origins = config("CSRF_TRUSTED_ORIGINS", default="").strip()
_csrf_list = [o.strip() for o in _csrf_origins.split(",") if o.strip()] if _csrf_origins else []
if not DEBUG and _railway_public:
    _auto_csrf = f"https://{_railway_public}"
    if _auto_csrf not in _csrf_list:
        _csrf_list.append(_auto_csrf)
if _csrf_list:
    CSRF_TRUSTED_ORIGINS = _csrf_list

# Behind Railway's HTTPS edge: trust X-Forwarded-Proto so Django sees secure requests.
if not DEBUG and _is_railway:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

SESSION_COOKIE_AGE = 86400 * 7  # 7 days
LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/"
