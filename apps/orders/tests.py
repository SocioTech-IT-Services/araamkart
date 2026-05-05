from django.test import TestCase
from apps.users.models import User
from apps.catalog.models import Category, Product, PricingTier
from .models import Cart, CartItem

class CartTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="123", full_name="Buyer")
        self.cat = Category.objects.create(name="Grocery")
        self.prod = Product.objects.create(
            category=self.cat, name="Salt", brand="S", moq=2, unit="pkt", stock=50
        )
        # 2-4 pkt @ 20, 5+ pkt @ 15
        PricingTier.objects.create(product=self.prod, min_qty=2, unit_price=20)
        PricingTier.objects.create(product=self.prod, min_qty=5, unit_price=15)
        
        self.cart = Cart.objects.create(user=self.user)

    def test_cart_totals(self):
        item = CartItem.objects.create(cart=self.cart, product=self.prod, quantity=3)
        self.assertEqual(float(item.unit_price()), 20.0)
        self.assertEqual(float(item.line_total()), 60.0)
        self.assertEqual(float(self.cart.get_total()), 60.0)

        # Update quantity to hit next tier
        item.quantity = 6
        item.save()
        self.assertEqual(float(item.unit_price()), 15.0)
        self.assertEqual(float(item.line_total()), 90.0)
        self.assertEqual(float(self.cart.get_total()), 90.0)
