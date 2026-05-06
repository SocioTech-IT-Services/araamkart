"""Orders app — Template Views (Cart, Checkout, Order History)"""
import json
from decimal import Decimal, InvalidOperation
from django.db.models import Sum
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from openpyxl import load_workbook

from apps.catalog.forms import AdminProductForm
from apps.catalog.models import Product, ProductImage, Category, SubCategory, Brand, ProductVariant
from .models import Cart, CartItem, Order, OrderItem
from apps.notifications.services import send_order_confirmation


# ── Cart ──────────────────────────────────────────────────────────────────────

@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related("product").prefetch_related("product__pricing_tiers")
    return render(request, "orders/cart.html", {
        "cart": cart,
        "items": items,
        "total": cart.get_total(),
    })


@login_required
@require_POST
def add_to_cart(request):
    data = json.loads(request.body)
    product_id = data.get("product_id")
    quantity = int(data.get("quantity", 1))

    product = get_object_or_404(Product, pk=product_id, is_active=True)

    if quantity < product.moq:
        return JsonResponse({"success": False, "error": f"Minimum order quantity is {product.moq} {product.unit}."})

    if quantity > product.stock:
        return JsonResponse({"success": False, "error": "Not enough stock available."})

    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity

    if item.quantity > product.stock:
        item.quantity = product.stock
    item.save()

    return JsonResponse({
        "success": True,
        "message": f"Added {quantity} {product.unit} of {product.name} to cart.",
        "cart_count": cart.item_count(),
    })


@login_required
@require_POST
def update_cart(request):
    data = json.loads(request.body)
    item_id = data.get("item_id")
    quantity = int(data.get("quantity", 1))

    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    product = item.product

    if quantity < product.moq:
        return JsonResponse({"success": False, "error": f"Minimum order quantity is {product.moq} {product.unit}."})

    if quantity > product.stock:
        return JsonResponse({"success": False, "error": "Not enough stock available."})

    item.quantity = quantity
    item.save()

    cart = item.cart
    return JsonResponse({
        "success": True,
        "line_total": float(item.line_total()),
        "cart_total": float(cart.get_total()),
        "unit_price": float(item.unit_price()),
    })


@login_required
@require_POST
def remove_from_cart(request):
    data = json.loads(request.body)
    item_id = data.get("item_id")
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    item.delete()
    cart = Cart.objects.get(user=request.user)
    return JsonResponse({
        "success": True,
        "cart_total": float(cart.get_total()),
        "cart_count": cart.item_count(),
    })


# ── Checkout ──────────────────────────────────────────────────────────────────

@login_required
def checkout_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related("product").prefetch_related("product__pricing_tiers")

    if not items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    if request.method == "POST":
        customer_name = request.POST.get("customer_name", "").strip()
        business_name = request.POST.get("business_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        pincode = request.POST.get("pincode", "").strip()
        notes = request.POST.get("notes", "").strip()

        if not all([customer_name, phone, address]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, "orders/checkout.html", {"cart": cart, "items": items})

        # Create order
        total = cart.get_total()
        order = Order.objects.create(
            user=request.user,
            customer_name=customer_name,
            business_name=business_name,
            phone=phone,
            email=email,
            address=address,
            city=city,
            pincode=pincode,
            notes=notes,
            payment_method="cod",
            total_amount=total,
            status="pending",
        )

        # Create order items + reduce stock
        for item in items:
            price = item.unit_price()
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                brand=item.product.brand,
                quantity=item.quantity,
                unit_price=price,
            )
            # Reduce stock
            product = item.product
            product.stock = max(0, product.stock - item.quantity)
            product.save()

        # Clear cart
        items.delete()

        # Send notifications
        try:
            send_order_confirmation(order)
        except Exception:
            pass  # don't block checkout on notification failure

        messages.success(request, f"Order #{order.order_number} placed successfully!")
        return redirect("order_success", order_number=order.order_number)

    return render(request, "orders/checkout.html", {
        "cart": cart,
        "items": items,
        "total": cart.get_total(),
        "user": request.user,
    })


def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, "orders/order_success.html", {"order": order})


# ── Order History ─────────────────────────────────────────────────────────────

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items").order_by("-created_at")
    return render(request, "orders/order_history.html", {"orders": orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})


# ── Admin Panel ───────────────────────────────────────────────────────────────

def _save_gallery_uploads(product, request):
    """Attach multiple extra images from the inventory form (`gallery_images` files)."""
    files = request.FILES.getlist("gallery_images")
    if not files:
        return
    start = product.gallery_images.count()
    for i, f in enumerate(files):
        ProductImage.objects.create(product=product, image=f, sort_order=start + i)


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_admin or request.user.is_staff):
            messages.error(request, "Admin access required.")
            return redirect_to_login(request.get_full_path())
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_dashboard(request):
    non_cancelled = Order.objects.exclude(status="cancelled")
    sales_agg = non_cancelled.aggregate(total=Sum("total_amount"))
    total_sales_rs = sales_agg["total"] or 0

    unit_agg = OrderItem.objects.filter(order__in=non_cancelled).aggregate(u=Sum("quantity"))
    units_sold = unit_agg["u"] or 0

    context = {
        "total_orders": Order.objects.count(),
        "pending_orders": Order.objects.filter(status="pending").count(),
        "total_products": Product.objects.filter(is_active=True).count(),
        "low_stock": Product.objects.filter(stock__lte=10, is_active=True).count(),
        "recent_orders": Order.objects.order_by("-created_at")[:10],
        "total_sales_rs": total_sales_rs,
        "units_sold": units_sold,
    }
    return render(request, "admin_panel/dashboard.html", context)


@admin_required
def admin_products(request):
    products = (
        Product.objects.select_related("category", "subcategory", "brand_obj")
        .prefetch_related("pricing_tiers", "variants")
        .order_by("-updated_at")
    )
    categories = Category.objects.filter(is_active=True)
    return render(
        request,
        "admin_panel/products.html",
        {"products": products, "categories": categories, "brands": Brand.objects.filter(is_active=True)},
    )


@admin_required
@require_POST
def admin_bulk_import_products(request):
    file = request.FILES.get("import_file")
    if not file:
        messages.error(request, "Please upload an Excel (.xlsx) file.")
        return redirect("admin_products")
    if not file.name.lower().endswith(".xlsx"):
        messages.error(request, "Only .xlsx files are supported.")
        return redirect("admin_products")

    wb = load_workbook(file, data_only=True)
    ws = wb.active
    headers = [str(c.value).strip().lower() if c.value is not None else "" for c in ws[1]]
    required = [
        "category",
        "subcategory",
        "brand",
        "product_name",
        "variant_name",
        "price",
        "stock",
        "unit",
        "moq",
    ]
    missing = [h for h in required if h not in headers]
    if missing:
        messages.error(request, f"Missing required columns: {', '.join(missing)}")
        return redirect("admin_products")

    idx = {h: headers.index(h) for h in headers}
    created_products = 0
    created_variants = 0
    updated_variants = 0
    errors = 0

    for row_num, row in enumerate(ws.iter_rows(min_row=2), start=2):
        try:
            def val(key):
                cell = row[idx[key]]
                return "" if cell.value is None else str(cell.value).strip()

            category_name = val("category")
            subcategory_name = val("subcategory")
            brand_name = val("brand")
            product_name = val("product_name")
            variant_name = val("variant_name") or "Default"
            unit = val("unit") or "pcs"
            sku = val("sku") if "sku" in idx else ""
            variant_sku = val("variant_sku") if "variant_sku" in idx else ""
            moq_raw = val("moq") or "1"
            price_raw = val("price")
            stock_raw = val("stock") or "0"

            if not (category_name and subcategory_name and brand_name and product_name and price_raw):
                errors += 1
                continue

            category, _ = Category.objects.get_or_create(name=category_name, defaults={"is_active": True})
            subcategory, _ = SubCategory.objects.get_or_create(
                category=category, name=subcategory_name, defaults={"is_active": True}
            )
            brand_obj, _ = Brand.objects.get_or_create(name=brand_name, defaults={"is_active": True})

            moq = max(1, int(float(moq_raw)))
            price = Decimal(str(price_raw))
            stock = max(0, int(float(stock_raw)))

            product, created = Product.objects.get_or_create(
                category=category,
                subcategory=subcategory,
                name=product_name,
                defaults={
                    "brand": brand_name,
                    "brand_obj": brand_obj,
                    "unit": unit,
                    "moq": moq,
                    "stock": stock,
                    "sku": sku or None,
                    "is_active": True,
                },
            )
            if created:
                created_products += 1
            else:
                product.brand_obj = brand_obj
                product.brand = brand_name
                product.unit = unit or product.unit
                product.moq = moq
                if sku:
                    product.sku = sku
                product.subcategory = subcategory
                product.save()

            variant_defaults = {
                "price": price,
                "stock": stock,
                "is_active": True,
            }
            variant, v_created = ProductVariant.objects.get_or_create(
                product=product,
                name=variant_name,
                defaults={
                    **variant_defaults,
                    "sku": variant_sku or None,
                },
            )
            if v_created:
                created_variants += 1
            else:
                variant.price = price
                variant.stock = stock
                if variant_sku:
                    variant.sku = variant_sku
                variant.is_active = True
                variant.save()
                updated_variants += 1

            # Keep legacy product fields in sync.
            product.stock = stock
            product.save(update_fields=["stock", "updated_at"])

            tier = product.pricing_tiers.order_by("min_qty").first()
            if tier:
                tier.min_qty = 1
                tier.unit_price = price
                tier.max_qty = None
                tier.save()
            else:
                product.pricing_tiers.create(min_qty=1, max_qty=None, unit_price=price, label="")

        except (ValueError, TypeError, InvalidOperation):
            errors += 1
            continue

    messages.success(
        request,
        f"Import complete: {created_products} products created, "
        f"{created_variants} variants created, {updated_variants} variants updated, {errors} rows skipped.",
    )
    return redirect("admin_products")


@admin_required
def admin_product_add(request):
    if request.method == "POST":
        form = AdminProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            _save_gallery_uploads(product, request)
            messages.success(request, f"Product “{product.name}” added.")
            return redirect("admin_products")
    else:
        form = AdminProductForm()
    return render(
        request,
        "admin_panel/product_form.html",
        {"form": form, "title": "Add product", "product": None, "gallery_images": []},
    )


@admin_required
@require_POST
def admin_gallery_image_delete(request, pk):
    img = get_object_or_404(ProductImage, pk=pk)
    product_pk = img.product_id
    if img.image:
        img.image.delete(save=False)
    img.delete()
    messages.success(request, "Extra image removed.")
    return redirect("admin_product_edit", pk=product_pk)


@admin_required
@require_POST
def admin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    label = str(product)
    product.delete()
    messages.success(request, f"Removed product “{label}”.")
    return redirect("admin_products")


@admin_required
def admin_product_edit(request, pk):
    product = get_object_or_404(
        Product.objects.prefetch_related("pricing_tiers"),
        pk=pk,
    )
    if request.method == "POST":
        form = AdminProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            _save_gallery_uploads(product, request)
            messages.success(request, "Product updated.")
            return redirect("admin_products")
    else:
        form = AdminProductForm(instance=product)
    gallery_images = product.gallery_images.all()
    return render(
        request,
        "admin_panel/product_form.html",
        {"form": form, "title": "Edit product", "product": product, "gallery_images": gallery_images},
    )


@admin_required
def admin_order_detail(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related("items"), order_number=order_number)
    return render(
        request,
        "admin_panel/order_detail.html",
        {"order": order, "status_choices": Order.STATUS_CHOICES},
    )


@admin_required
def admin_orders(request):
    status_filter = request.GET.get("status", "")
    orders = Order.objects.prefetch_related("items").order_by("-created_at")
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, "admin_panel/orders.html", {
        "orders": orders,
        "status_filter": status_filter,
        "status_choices": Order.STATUS_CHOICES,
    })


@admin_required
@require_POST
def admin_update_order_status(request):
    data = json.loads(request.body)
    order_id = data.get("order_id")
    new_status = data.get("status")
    order = get_object_or_404(Order, pk=order_id)
    if new_status in dict(Order.STATUS_CHOICES):
        order.status = new_status
        order.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid status."})


@admin_required
@require_POST
def admin_update_stock(request):
    """Set absolute stock or apply a delta (+/-) from the inventory dashboard."""
    data = json.loads(request.body)
    product_id = data.get("product_id")
    product = get_object_or_404(Product, pk=product_id)
    if "delta" in data:
        delta = int(data["delta"])
        product.stock = max(0, int(product.stock) + delta)
    else:
        product.stock = max(0, int(data.get("stock", 0)))
    product.save(update_fields=["stock", "updated_at"])
    return JsonResponse({"success": True, "stock": product.stock})


@admin_required
@require_POST
def admin_toggle_product_active(request):
    data = json.loads(request.body)
    product = get_object_or_404(Product, pk=data.get("product_id"))
    product.is_active = bool(data.get("is_active", True))
    product.save()
    return JsonResponse({"success": True, "is_active": product.is_active})
