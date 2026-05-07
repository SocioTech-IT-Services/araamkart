"""Expose active categories to all templates (nav strip, search, footer)."""
from django.conf import settings
import time

from .models import Category


def nav_categories(request):
    return {
        "nav_categories": Category.objects.filter(is_active=True)
        .prefetch_related("subcategories")
        .order_by("order", "name"),
    }


def static_assets_version(request):
    """Query-string cache bust for {% static %} CSS/JS so laptop browsers pick up updates."""
    if getattr(settings, "DEBUG", False):
        # In local dev, always bust cache so CSS/JS changes appear instantly.
        return {"STATIC_CACHE_BUSTER": str(int(time.time()))}
    return {"STATIC_CACHE_BUSTER": getattr(settings, "STATIC_CACHE_BUSTER", "1")}
