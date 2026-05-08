"""Catalog app — Template Views"""
import json
import math
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from .models import Category, Product, SubCategory, Brand


@lru_cache(maxsize=1)
def _catalog_image_manifest():
    manifest_path = (
        Path(__file__).resolve().parent.parent.parent
        / "static"
        / "img"
        / "generated"
        / "manifest.json"
    )
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def home(request):
    wanted_home_categories = [
        "Personal Care & Hygiene",
        "Household Essentials",
        "Utilities",
        "Games",
        "Baby Care",
        "Stationery",
        "Female Hygiene",
    ]
    category_qs = Category.objects.filter(is_active=True, name__in=wanted_home_categories)
    category_map = {c.name: c for c in category_qs}
    featured_categories = [category_map[name] for name in wanted_home_categories if name in category_map]
    image_manifest = _catalog_image_manifest()
    for category in featured_categories:
        category.generated_image = image_manifest.get(category.name, {}).get("category_image")

    return render(request, "home.html", {"categories": featured_categories})


def contact(request):
    return render(request, "pages/contact.html")


def best_offers(request):
    categories = Category.objects.filter(is_active=True).order_by("order", "name")
    return render(request, "pages/offers.html", {"categories": categories})


def policies(request):
    return render(request, "pages/policies.html")


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = (
        Product.objects.filter(category=category, is_active=True)
        .select_related("subcategory", "brand_obj")
        .prefetch_related("pricing_tiers")
    )

    # Filters
    brand = request.GET.get("brand", "").strip()
    subcategory_slug = request.GET.get("subcategory", "").strip()
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    search = request.GET.get("q", "").strip()

    if subcategory_slug:
        products = products.filter(subcategory__slug=subcategory_slug)
    if brand:
        products = products.filter(Q(brand__icontains=brand) | Q(brand_obj__name__icontains=brand))
    if search:
        products = products.filter(
            Q(name__icontains=search)
            | Q(brand__icontains=search)
            | Q(brand_obj__name__icontains=search)
            | Q(subcategory__name__icontains=search)
        )

    # Brand list for filter sidebar
    all_brands = (
        Product.objects.filter(category=category, is_active=True)
        .values_list("brand", flat=True)
        .distinct()
        .order_by("brand")
    )
    all_brand_objs = Brand.objects.filter(products__category=category, is_active=True).distinct().order_by("name")
    subcategories = list(category.subcategories.filter(is_active=True).order_by("order", "name"))
    category_manifest = _catalog_image_manifest().get(category.name, {})
    subcategory_images = category_manifest.get("subcategories", {})
    for subcategory in subcategories:
        subcategory.generated_image = subcategory_images.get(subcategory.name)

    # Price filter (approximate via base_price)
    filtered_products = []
    for p in products:
        bp = p.base_price
        if bp is None:
            filtered_products.append(p)
            continue
        if min_price:
            try:
                if float(bp) < float(min_price):
                    continue
            except ValueError:
                pass
        if max_price:
            try:
                if float(bp) > float(max_price):
                    continue
            except ValueError:
                pass
        filtered_products.append(p)

    return render(request, "catalog/category.html", {
        "category": category,
        "products": filtered_products,
        "all_brands": all_brands,
        "selected_brand": brand,
        "subcategories": subcategories,
        "selected_subcategory": subcategory_slug,
        "all_brand_objs": all_brand_objs,
        "min_price": min_price,
        "max_price": max_price,
        "search": search,
    })


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related("category", "brand_obj", "subcategory")
        .prefetch_related("gallery_images"),
        pk=pk,
        is_active=True,
    )
    tiers = product.pricing_tiers.all().order_by("min_qty")
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=pk)[:4]

    pack_qty = product.pack_quantity
    packet_price = product.packet_price
    use_packet_pricing = bool(pack_qty and packet_price)
    list_price_total = None
    packet_savings_amount = None
    effective_price_per_unit = None
    if use_packet_pricing and product.single_product_price is not None:
        list_price_total = product.single_product_price * pack_qty
    if use_packet_pricing and list_price_total is not None and packet_price is not None:
        packet_savings_amount = list_price_total - packet_price
    if use_packet_pricing and pack_qty and packet_price is not None:
        effective_price_per_unit = (Decimal(packet_price) / Decimal(pack_qty)).quantize(Decimal("0.01"))

    packets_available = None
    min_packets = None
    can_order_packets = True
    if use_packet_pricing and pack_qty:
        packets_available = product.stock // pack_qty
        if packets_available > 0:
            min_packets = max(1, math.ceil(product.moq / pack_qty))
            min_packets = min(min_packets, packets_available)
            can_order_packets = product.moq <= packets_available * pack_qty

    return render(request, "catalog/product.html", {
        "product": product,
        "tiers": tiers if not use_packet_pricing else [],
        "related": related,
        "gallery_images": product.gallery_images.all(),
        "use_packet_pricing": use_packet_pricing,
        "list_price_total": list_price_total,
        "packet_savings_amount": packet_savings_amount,
        "effective_price_per_unit": effective_price_per_unit,
        "packets_available": packets_available,
        "min_packets": min_packets,
        "can_order_packets": can_order_packets,
    })


def search_results(request):
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    subcategory_id = request.GET.get("subcategory", "")
    brand = request.GET.get("brand", "").strip()
    products = Product.objects.filter(is_active=True).prefetch_related("pricing_tiers")
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(brand__icontains=query) | Q(description__icontains=query)
        )
    
    if category_id:
        products = products.filter(category__slug=category_id)
    if subcategory_id:
        products = products.filter(subcategory__slug=subcategory_id)
    if brand:
        products = products.filter(Q(brand__icontains=brand) | Q(brand_obj__name__icontains=brand))

    return render(
        request,
        "catalog/search.html",
        {"products": products, "query": query, "selected_subcategory": subcategory_id, "selected_brand": brand},
    )


def subcategories_api(request):
    category_slug = request.GET.get("category")
    category_id = request.GET.get("category_id")
    if not category_slug and not category_id:
        return JsonResponse({"subcategories": []})
    filters = {"is_active": True}
    if category_id:
        filters["category_id"] = category_id
    else:
        filters["category__slug"] = category_slug
    subcats = SubCategory.objects.filter(**filters).order_by("order", "name").values("id", "name")
    return JsonResponse({"subcategories": list(subcats)})
