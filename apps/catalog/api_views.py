"""DRF API Views — Catalog"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q

from .models import Category, Product, PricingTier
from .serializers import (
    CategorySerializer, ProductListSerializer,
    ProductDetailSerializer, ProductWriteSerializer, PricingTierSerializer,
)


class CategoryListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cats = Category.objects.filter(is_active=True)
        return Response(CategorySerializer(cats, many=True).data)


class ProductListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        products = Product.objects.filter(is_active=True).select_related("category").prefetch_related("pricing_tiers")
        category = request.GET.get("category")
        brand = request.GET.get("brand")
        q = request.GET.get("q")
        if category:
            products = products.filter(category__slug=category)
        if brand:
            products = products.filter(brand__icontains=brand)
        if q:
            products = products.filter(Q(name__icontains=q) | Q(brand__icontains=q))
        return Response(ProductListSerializer(products, many=True, context={"request": request}).data)

    def post(self, request):
        if not (request.user.is_authenticated and (request.user.is_admin or request.user.is_staff)):
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
        if not (request.user.is_authenticated and (request.user.is_admin or request.user.is_staff)):
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
        if not (request.user.is_authenticated and (request.user.is_admin or request.user.is_staff)):
            return Response({"error": "Admin only."}, status=403)
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"error": "Not found."}, status=404)
        product.is_active = False
        product.save()
        return Response({"message": "Product deactivated."})
