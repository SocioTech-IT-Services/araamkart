"""Catalog app — Template Views"""
import json
import math
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q, Prefetch
from .models import Category, Product, SubCategory, Brand


SUBCATEGORY_IMAGE_OVERRIDES = {
    "baby cream": "product-images/New folder/New folder/babycream.jpg",
    "baby oil": "product-images/New folder/New folder/bboil.jpg",
    "baby powder": "product-images/New folder/New folder/bbpowder.jpg",
    "baby shampoo": "product-images/New folder/New folder/bbshampoo.jpg",
    "balloons": "product-images/New folder/New folder/balloons.jpg",
    "bandages": "product-images/New folder/New folder/BANDAGE.jpg",
    "batteries": "product-images/New folder/New folder/BATTERIES.jpg",
    "bleach and hair remover": "product-images/BLEACH.jpg",
    "bulb": "product-images/New folder/New folder/BULB.jpg",
    "candles": "product-images/New folder/New folder/candles.jpg",
    "cleaning essential": "product-images/New folder/CLEANING.jpg",
    "clothe clips": "product-images/New folder/New folder/CLOTHESCLIP.jpg",
    "combs": "product-images/New folder/New folder/COMB.jpg",
    "cotton": "product-images/New folder/New folder/COTTON.jpg",
    "creams and lotion": "product-images/CREAM.jpg",
    "drawing pin": "product-images/New folder/New folder/DRAWINGPIN.jpg",
    "glue and gums": "product-images/New folder/New folder/GUM.jpg",
    "hair care": "product-images/HAIR.jpg",
    "handkerchief": "product-images/New folder/New folder/HANKERCHEIF.jpg",
    "hankerchief": "product-images/New folder/New folder/HANKERCHEIF.jpg",
    "housie books": "product-images/New folder/New folder/housie.jpg",
    "insects repellent": "product-images/New folder/INSECTS.jpg",
    "lighters": "product-images/New folder/New folder/LIGHTER.jpg",
    "lock and keys": "product-images/New folder/New folder/LOCK.jpg",
    "mirrors": "product-images/New folder/New folder/MIRROR.jpg",
    "nail cutter": "product-images/New folder/New folder/NAILCUTTER.jpg",
    "nail remover": "product-images/New folder/New folder/NAILREMOVER.jpg",
    "needles and threads": "product-images/New folder/New folder/NEEDLE.jpg",
    "oral": "product-images/ORAL.jpg",
    "panty liner": "product-images/New folder/New folder/pantyliners.jpg",
    "panty liners": "product-images/New folder/New folder/pantyliners.jpg",
    "perfume fragrance": "product-images/PERFUME.jpg",
    "playing cards": "product-images/New folder/New folder/cards.jpg",
    "razor and blades": "product-images/RAZOR.jpg",
    "rope": "product-images/New folder/New folder/ROPE.jpg",
    "saftty pin": "product-images/New folder/New folder/SAFTEYPIN.jpg",
    "safety pin": "product-images/New folder/New folder/SAFTEYPIN.jpg",
    "shampoo": "product-images/SHAMPOO.jpg",
    "shoes brush and polish": "product-images/New folder/SHOE.jpg",
    "scissors": "product-images/New folder/New folder/SCISSORS.jpg",
    "tapes": "product-images/New folder/New folder/TAPES.jpg",
    "tennis balls": "product-images/New folder/New folder/tenis.jpg",
    "toilet cleaner": "product-images/New folder/TOILET.jpg",
    "toilet paper": "product-images/New folder/New folder/TOILETPAPER.jpg",
    "torch light": "product-images/New folder/New folder/TORCH.jpg",
    "sanitary pads": "product-images/New folder/New folder/sanitary.jpg",
    "vaseline and lip balms": "product-images/VASELINE.jpg",
    "veet": "product-images/New folder/New folder/veet.jpg",
    "vix and balm": "product-images/BALM.jpg",
}


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
        "Personal care and hygiene",
        "Household essentials",
        "Utilities",
        "Games",
        "Baby care",
        "Stationery",
        "Female hygiene",
    ]
    category_qs = Category.objects.filter(is_active=True, name__in=wanted_home_categories)
    category_map = {c.name: c for c in category_qs}
    featured_categories = [category_map[name] for name in wanted_home_categories if name in category_map]
    home_category_images = {
        "Personal care and hygiene": "product-images/personalcare.jpg",
        "Household essentials": "product-images/household.jpg",
        "Utilities": "product-images/utilites.jpg",
        "Games": "product-images/games.jpg",
        "Baby care": "product-images/babycare.jpg",
        "Stationery": "product-images/stationaries.jpg",
        "Female hygiene": "product-images/female.jpg",
    }
    image_manifest = _catalog_image_manifest()
    for category in featured_categories:
        category.generated_image = (
            home_category_images.get(category.name)
            or image_manifest.get(category.name, {}).get("category_image")
        )

    return render(request, "home.html", {"categories": featured_categories})


def contact(request):
    return render(request, "pages/contact.html")


def best_offers(request):
    categories = Category.objects.filter(is_active=True).order_by("order", "name")
    return render(request, "pages/offers.html", {"categories": categories})


def policies(request):
    return render(request, "pages/policies.html")


def _leaf_subcategory_ids(subcat):
    """Return leaf SubCategory PKs under `subcat` (includes `subcat` if it has no children)."""
    children = SubCategory.objects.filter(
        parent=subcat, category=subcat.category, is_active=True
    )
    if not children.exists():
        return [subcat.pk]
    ids = []
    for ch in children.order_by("order", "name"):
        ids.extend(_leaf_subcategory_ids(ch))
    return ids


def _category_products(category, selected_subcategory_obj=None, brand="", search="", min_price="", max_price=""):
    products = (
        Product.objects.filter(is_active=True)
        .filter(Q(placements__category=category) | Q(category=category))
        .select_related("subcategory", "subcategory__parent", "brand_obj")
        .prefetch_related("pricing_tiers", "placements")
        .distinct()
    )
    if selected_subcategory_obj:
        leaf_ids = _leaf_subcategory_ids(selected_subcategory_obj)
        products = products.filter(
            Q(placements__subcategory_id__in=leaf_ids) | Q(subcategory_id__in=leaf_ids)
        ).distinct()
    if brand:
        products = products.filter(Q(brand__icontains=brand) | Q(brand_obj__name__icontains=brand))
    if search:
        products = products.filter(
            Q(name__icontains=search)
            | Q(brand__icontains=search)
            | Q(brand_obj__name__icontains=search)
            | Q(placements__subcategory__name__icontains=search)
            | Q(placements__subcategory__parent__name__icontains=search)
        ).distinct()

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
    return filtered_products


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)

    brand = request.GET.get("brand", "").strip()
    subcategory_slug = request.GET.get("subcategory", "").strip()
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    search = request.GET.get("q", "").strip()

    top_subcategories = list(
        category.subcategories.filter(parent__isnull=True, is_active=True)
        .prefetch_related(
            Prefetch(
                "children",
                queryset=SubCategory.objects.filter(is_active=True).order_by("order", "name"),
            )
        )
        .order_by("order", "name")
    )

    selected_subcategory_obj = None
    if subcategory_slug:
        selected_subcategory_obj = SubCategory.objects.filter(
            category=category, slug=subcategory_slug, is_active=True
        ).first()
        if selected_subcategory_obj is None:
            subcategory_slug = ""
        elif not selected_subcategory_obj.children.filter(is_active=True).exists():
            return redirect(
                "category_product_view",
                slug=category.slug,
                subcategory_slug=selected_subcategory_obj.slug,
            )

    secondary_subcategories = []
    if selected_subcategory_obj:
        if selected_subcategory_obj.parent_id:
            secondary_subcategories = list(
                SubCategory.objects.filter(
                    parent_id=selected_subcategory_obj.parent_id,
                    category=category,
                    is_active=True,
                ).order_by("order", "name")
            )
        else:
            secondary_subcategories = list(
                selected_subcategory_obj.children.filter(is_active=True).order_by("order", "name")
            )

    breadcrumb_chain = []
    selected_root = None
    if selected_subcategory_obj:
        breadcrumb_chain = selected_subcategory_obj.ancestor_chain()
        selected_root = breadcrumb_chain[0] if breadcrumb_chain else None

    all_brands = (
        Product.objects.filter(is_active=True)
        .filter(Q(placements__category=category) | Q(category=category))
        .values_list("brand", flat=True)
        .distinct()
        .order_by("brand")
    )
    all_brand_objs = Brand.objects.filter(
        Q(products__placements__category=category) | Q(products__category=category),
        is_active=True,
    ).distinct().order_by("name")
    category_manifest = _catalog_image_manifest().get(category.name, {})
    subcategory_images = category_manifest.get("subcategories", {})

    for sc in top_subcategories:
        sc.generated_image = SUBCATEGORY_IMAGE_OVERRIDES.get(sc.name.lower(), subcategory_images.get(sc.name))
        sc.has_children = bool(sc.children.all())
    for sc in secondary_subcategories:
        sc.generated_image = SUBCATEGORY_IMAGE_OVERRIDES.get(sc.name.lower(), subcategory_images.get(sc.name))

    return render(request, "catalog/category.html", {
        "category": category,
        "products": [],
        "all_brands": all_brands,
        "selected_brand": brand,
        "top_subcategories": top_subcategories,
        "secondary_subcategories": secondary_subcategories,
        "selected_subcategory": subcategory_slug,
        "selected_subcategory_obj": selected_subcategory_obj,
        "breadcrumb_chain": breadcrumb_chain,
        "selected_root": selected_root,
        "all_brand_objs": all_brand_objs,
        "min_price": min_price,
        "max_price": max_price,
        "search": search,
    })


def category_product_view(request, slug, subcategory_slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    selected_subcategory_obj = get_object_or_404(
        SubCategory,
        category=category,
        slug=subcategory_slug,
        is_active=True,
    )
    brand = request.GET.get("brand", "").strip()
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    search = request.GET.get("q", "").strip()

    breadcrumb_chain = selected_subcategory_obj.ancestor_chain()
    selected_root = breadcrumb_chain[0] if breadcrumb_chain else None
    products = _category_products(
        category,
        selected_subcategory_obj=selected_subcategory_obj,
        brand=brand,
        search=search,
        min_price=min_price,
        max_price=max_price,
    )
    return render(request, "catalog/category_products.html", {
        "category": category,
        "products": products,
        "selected_brand": brand,
        "selected_subcategory": subcategory_slug,
        "selected_subcategory_obj": selected_subcategory_obj,
        "breadcrumb_chain": breadcrumb_chain,
        "selected_root": selected_root,
        "min_price": min_price,
        "max_price": max_price,
        "search": search,
    })


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related(
            "category", "brand_obj", "subcategory", "subcategory__parent"
        )
        .prefetch_related("gallery_images"),
        pk=pk,
        is_active=True,
    )
    tiers = product.pricing_tiers.all().order_by("min_qty")
    cat_ids = list(product.placements.values_list("category_id", flat=True).distinct())
    if not cat_ids and product.category_id:
        cat_ids = [product.category_id]
    related = (
        Product.objects.filter(placements__category_id__in=cat_ids, is_active=True)
        .exclude(pk=pk)
        .distinct()[:4]
    )

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
        products = products.filter(
            Q(category__slug=category_id) | Q(placements__category__slug=category_id)
        ).distinct()
    if subcategory_id:
        sc = SubCategory.objects.filter(slug=subcategory_id).first()
        if sc:
            leaf_ids = _leaf_subcategory_ids(sc)
            products = products.filter(
                Q(subcategory_id__in=leaf_ids) | Q(placements__subcategory_id__in=leaf_ids)
            ).distinct()
        else:
            products = products.filter(
                Q(subcategory__slug=subcategory_id) | Q(placements__subcategory__slug=subcategory_id)
            ).distinct()
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
    subcats = SubCategory.objects.filter(**filters)
    parent_id = request.GET.get("parent_id")
    roots_only = request.GET.get("roots_only") == "1"
    if parent_id:
        try:
            subcats = subcats.filter(parent_id=int(parent_id))
        except (TypeError, ValueError):
            subcats = subcats.none()
    elif roots_only:
        subcats = subcats.filter(parent__isnull=True)
    subcats = subcats.order_by("order", "name").values("id", "name")
    return JsonResponse({"subcategories": list(subcats)})
