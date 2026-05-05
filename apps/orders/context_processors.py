"""Expose cart totals safely (anonymous users have no cart; user may have no Cart row yet)."""
from apps.orders.models import Cart


def cart_summary(request):
    """Never raise — a broken cart must not blank the whole site."""
    empty = {"cart_item_count": 0, "cart_total_display": "0.00"}
    try:
        if not request.user.is_authenticated:
            return empty
        try:
            cart = request.user.cart
        except Cart.DoesNotExist:
            return empty
        total = cart.get_total()
        try:
            total_str = f"{float(total):.2f}"
        except (TypeError, ValueError):
            total_str = "0.00"
        return {
            "cart_item_count": cart.item_count(),
            "cart_total_display": total_str,
        }
    except Exception:
        return empty
