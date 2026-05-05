"""Catalog app — Template Views"""
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Category, Product


def home(request):
    categories = Category.objects.filter(is_active=True).order_by("order")
    return render(request, "home.html", {"categories": categories})


def contact(request):
    return render(request, "pages/contact.html")


def best_offers(request):
    categories = Category.objects.filter(is_active=True).order_by("order", "name")
    return render(request, "pages/offers.html", {"categories": categories})


def policies(request):
    return render(request, "pages/policies.html")


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True).prefetch_related("pricing_tiers")

    # Filters
    brand = request.GET.get("brand", "").strip()
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    search = request.GET.get("q", "").strip()

    if brand:
        products = products.filter(brand__icontains=brand)
    if search:
        products = products.filter(Q(name__icontains=search) | Q(brand__icontains=search))

    # Brand list for filter sidebar
    all_brands = (
        Product.objects.filter(category=category, is_active=True)
        .values_list("brand", flat=True)
        .distinct()
        .order_by("brand")
    )

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
        "min_price": min_price,
        "max_price": max_price,
        "search": search,
    })


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.prefetch_related("gallery_images"),
        pk=pk,
        is_active=True,
    )
    tiers = product.pricing_tiers.all().order_by("min_qty")
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=pk)[:4]
    return render(request, "catalog/product.html", {
        "product": product,
        "tiers": tiers,
        "related": related,
        "gallery_images": product.gallery_images.all(),
    })


def search_results(request):
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    products = Product.objects.filter(is_active=True).prefetch_related("pricing_tiers")
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(brand__icontains=query) | Q(description__icontains=query)
        )
    
    if category_id:
        products = products.filter(category__slug=category_id)

    return render(request, "catalog/search.html", {"products": products, "query": query})
