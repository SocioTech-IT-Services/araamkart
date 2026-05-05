from django.test import TestCase
from .models import Category, Product, PricingTier

class CatalogTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Grocery", slug="grocery")
        self.prod = Product.objects.create(
            category=self.cat,
            name="Rice",
            brand="BrandX",
            moq=5,
            unit="kg",
            stock=100
        )
        # Tiers: 5-9 kg @ 100, 10+ kg @ 80
        self.tier1 = PricingTier.objects.create(product=self.prod, min_qty=5, max_qty=9, unit_price=100)
        self.tier2 = PricingTier.objects.create(product=self.prod, min_qty=10, max_qty=None, unit_price=80)

    def test_pricing_tiers(self):
        # Quantity < MOQ (should still return base_price or first tier price if logic allows)
        # Note: MOQ is enforced at view level, model just returns what fits
        self.assertEqual(float(self.prod.get_price_for_qty(5)), 100.0)
        self.assertEqual(float(self.prod.get_price_for_qty(8)), 100.0)
        self.assertEqual(float(self.prod.get_price_for_qty(10)), 80.0)
        self.assertEqual(float(self.prod.get_price_for_qty(50)), 80.0)

    def test_base_price(self):
        self.assertEqual(float(self.prod.base_price), 100.0)
