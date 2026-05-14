"""DRF API Views — Catalog"""
import json
from pathlib import Path

from django.db.models import Q, Sum, Count, Prefetch
from django.urls import reverse
from urllib.parse import urlencode
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Category, Product, PricingTier, SubCategory, ProductVariant
from .serializers import (
    CategorySerializer, ProductListSerializer,
    ProductDetailSerializer, ProductWriteSerializer, PricingTierSerializer,
)
from apps.orders.models import OrderItem


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


class CategoryListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cats = Category.objects.filter(is_active=True)
        return Response(CategorySerializer(cats, many=True).data)


class SearchTaxonomySuggestAPIView(APIView):
    """
    Suggest category > subcategory paths from active products matching the query
    (e.g. brand/name/subcategory text), for smart search navigation.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        q = request.GET.get("q", "").strip()
        if len(q) < 2:
            return Response([])
        try:
            limit = int(request.GET.get("limit", "5"))
        except ValueError:
            limit = 5
        limit = max(1, min(limit, 10))

        name_q = (
            Q(name__icontains=q)
            | Q(brand__icontains=q)
            | Q(brand_obj__name__icontains=q)
            | Q(subcategory__name__icontains=q)
            | Q(subcategory__parent__name__icontains=q)
            | Q(category__name__icontains=q)
            | Q(placements__subcategory__name__icontains=q)
            | Q(placements__subcategory__parent__name__icontains=q)
            | Q(placements__category__name__icontains=q)
        )
        base = Product.objects.filter(is_active=True).filter(name_q)

        out = []
        seen_urls = set()

        sub_rows = (
            base.filter(placements__subcategory__isnull=False)
            .values("placements__subcategory_id")
            .annotate(matches=Count("id", distinct=True))
            .order_by("-matches")[: limit * 2]
        )
        ids = [r["placements__subcategory_id"] for r in sub_rows if r.get("placements__subcategory_id")]
        subs_by_id = {
            s.id: s
            for s in SubCategory.objects.filter(pk__in=ids).select_related(
                "category", "parent"
            )
        }

        for row in sub_rows:
            sid = row.get("placements__subcategory_id")
            sub = subs_by_id.get(sid)
            if not sub:
                continue
            cat_name = sub.category.name
            chain_names = [n.name for n in sub.ancestor_chain()]
            path = " > ".join([cat_name] + chain_names)
            rel = (
                reverse("category_detail", kwargs={"slug": sub.category.slug})
                + "?"
                + urlencode({"subcategory": sub.slug})
            )
            if rel in seen_urls:
                continue
            seen_urls.add(rel)
            out.append(
                {
                    "path": path,
                    "url": rel,
                    "matches": row["matches"],
                    "kind": "subcategory",
                }
            )
            if len(out) >= limit:
                break

        remaining = limit - len(out)
        if remaining > 0:
            cat_rows = (
                base.filter(placements__subcategory__isnull=True)
                .values("placements__category__name", "placements__category__slug")
                .annotate(matches=Count("id", distinct=True))
                .order_by("-matches", "placements__category__name")[:remaining]
            )
            for row in cat_rows:
                path = f"{row['placements__category__name']} > Browse category"
                rel = reverse("category_detail", kwargs={"slug": row["placements__category__slug"]})
                if rel in seen_urls:
                    continue
                seen_urls.add(rel)
                out.append(
                    {
                        "path": path,
                        "url": rel,
                        "matches": row["matches"],
                        "kind": "category",
                    }
                )

        return Response(out[:limit])


class ProductListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        products = (
            Product.objects.filter(is_active=True)
            .select_related("category", "brand_obj", "subcategory")
            .prefetch_related("pricing_tiers", "placements")
        )
        category = request.GET.get("category")
        brand = request.GET.get("brand")
        q = request.GET.get("q", "").strip()
        if category:
            products = products.filter(
                Q(category__slug=category) | Q(placements__category__slug=category)
            ).distinct()
        if brand:
            products = products.filter(brand__icontains=brand)
        if q:
            products = products.filter(
                Q(name__icontains=q)
                | Q(brand__icontains=q)
                | Q(brand_obj__name__icontains=q)
                | Q(subcategory__name__icontains=q)
                | Q(subcategory__parent__name__icontains=q)
                | Q(category__name__icontains=q)
                | Q(placements__subcategory__name__icontains=q)
                | Q(placements__subcategory__parent__name__icontains=q)
                | Q(placements__category__name__icontains=q)
            ).distinct()
        try:
            lim = int(request.GET.get("limit", "0"))
            if lim > 0:
                products = products[:lim]
        except ValueError:
            pass
        return Response(ProductListSerializer(products, many=True, context={"request": request}).data)

    def post(self, request):
        if not (request.user.is_authenticated and getattr(request.user, "can_access_admin_panel", False)):
            return Response({"error": "Admin only."}, status=403)
        s = ProductWriteSerializer(data=request.data)
        if s.is_valid():
            product = s.save()
            return Response(ProductDetailSerializer(product, context={"request": request}).data, status=201)
        return Response(s.errors, status=400)


class ProductDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk, is_active=True)
        except Product.DoesNotExist:
            return Response({"error": "Not found."}, status=404)
        return Response(ProductDetailSerializer(product, context={"request": request}).data)

    def put(self, request, pk):
        if not (request.user.is_authenticated and getattr(request.user, "can_access_admin_panel", False)):
            return Response({"error": "Admin only."}, status=403)
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"error": "Not found."}, status=404)
        s = ProductWriteSerializer(product, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(ProductDetailSerializer(product, context={"request": request}).data)
        return Response(s.errors, status=400)

    def delete(self, request, pk):
        if not (request.user.is_authenticated and getattr(request.user, "can_access_admin_panel", False)):
            return Response({"error": "Admin only."}, status=403)
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"error": "Not found."}, status=404)
        product.is_active = False
        product.save()
        return Response({"message": "Product deactivated."})


class MostSellingProductsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        valid_statuses = ["confirmed", "processing", "shipped", "delivered"]
        aggregated_rows = list(
            OrderItem.objects.filter(
                order__status__in=valid_statuses,
                product__isnull=False,
                product__is_active=True,
            )
            .values(
                "product_id",
                "product__name",
                "product__stock",
                "product__subcategory__name",
                "product__category__name",
                "product__category__slug",
                "product__subcategory__slug",
            )
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold", "product__name")
        )

        try:
            limit = int(request.GET.get("limit", "10"))
        except ValueError:
            limit = 10
        limit = max(1, min(limit, 30))

        product_ids = [row["product_id"] for row in aggregated_rows[:limit]]
        product_map = {
            p.id: p
            for p in Product.objects.filter(pk__in=product_ids)
            .prefetch_related(
                "pricing_tiers",
                Prefetch(
                    "variants",
                    queryset=ProductVariant.objects.filter(is_active=True).order_by("id"),
                ),
            )
            .select_related("category", "subcategory")
        }

        def _default_variant_id_for_quick_add(product: Product):
            """When multiple variants exist, cart add needs a variant_id; pick first in-stock or first row."""
            variants = list(product.variants.all())
            if len(variants) <= 1:
                return None
            pick = next((v for v in variants if int(v.stock or 0) > 0), None) or variants[0]
            return pick.pk

        manifest = _catalog_image_manifest()
        payload = []
        for row in aggregated_rows[:limit]:
            product = product_map.get(row["product_id"])
            if not product:
                continue
            category_name = row.get("product__category__name")
            subcategory_name = row.get("product__subcategory__name")
            category_assets = manifest.get(category_name, {})
            image = None
            if subcategory_name:
                image = category_assets.get("subcategories", {}).get(subcategory_name)
            if not image:
                image = category_assets.get("category_image")
            if not image and product.image:
                image_url = request.build_absolute_uri(product.image.url)
            else:
                image_url = request.build_absolute_uri(f"/static/{image}") if image else ""

            stock = int(row.get("product__stock") or 0)
            stock_status = "In Stock" if stock > 10 else ("Low Stock" if stock > 0 else "Out of Stock")

            payload.append(
                {
                    "product_id": row["product_id"],
                    "default_variant_id": _default_variant_id_for_quick_add(product),
                    "product_name": row["product__name"],
                    "quantity_sold": int(row["total_sold"] or 0),
                    "wholesale_price": float(product.base_price) if product.base_price else 0,
                    "packet_price": float(product.packet_price) if product.packet_price else None,
                    "single_product_price": float(product.single_product_price) if product.single_product_price else None,
                    "pack_quantity": int(product.pack_quantity) if product.pack_quantity else None,
                    "discount_percentage": float(product.discount_percentage) if product.discount_percentage is not None else 0,
                    "moq": int(product.moq or 1),
                    "unit": product.unit,
                    "stock": stock,
                    "stock_status": stock_status,
                    "category": category_name,
                    "subcategory": subcategory_name,
                    "image": image_url,
                }
            )

        return Response(payload)
