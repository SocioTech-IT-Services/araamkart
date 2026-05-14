"""Staff-only delivery management UI (B2B ops dashboard)."""
from datetime import datetime, time

from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from .models import Order


def staff_admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        u = request.user
        if not u.is_authenticated or not getattr(u, "can_use_delivery_ops", False):
            messages.error(request, "Staff access required.")
            return redirect_to_login(request.get_full_path())
        return view_func(request, *args, **kwargs)

    return wrapper


@staff_admin_required
def staff_delivery_panel(request):
    """Premium glassmorphism delivery dashboard — staff only."""
    # Stats = active queue only (excludes cancelled). Table lists recent orders including cancelled
    # so staff can move them back into the pipeline later.
    active_base = Order.objects.exclude(status="cancelled")
    today = timezone.localdate()
    start_today = timezone.make_aware(datetime.combine(today, time.min))

    status_counts = {
        "confirmed": active_base.filter(Q(status="pending") | Q(status="confirmed")).count(),
        "processing": active_base.filter(status="processing").count(),
        "shipped": active_base.filter(status="shipped").count(),
        "delivered": active_base.filter(status="delivered").count(),
    }

    staff = request.user
    handled_today = active_base.filter(last_status_updated_by=staff, updated_at__gte=start_today).count()

    delivered_by_staff = list(
        active_base.filter(status="delivered", last_status_updated_by=staff).order_by("-updated_at")[:80]
    )
    if delivered_by_staff:
        deltas = [(o.updated_at - o.created_at).total_seconds() / 3600 for o in delivered_by_staff]
        avg_delivery_hours = sum(deltas) / len(deltas)
    else:
        avg_delivery_hours = None

    orders = (
        Order.objects.select_related("last_status_updated_by")
        .prefetch_related("items")
        .order_by("-created_at")[:120]
    )

    # Progress ring percentages (heuristic display)
    orders_today = active_base.filter(created_at__gte=start_today).count()
    ring_handled = min(100, int(round(100 * handled_today / max(orders_today, 1))))
    ring_speed = 72 if avg_delivery_hours is None else max(15, min(100, int(120 / max(avg_delivery_hours, 0.25))))

    context = {
        "status_counts": status_counts,
        "orders": orders,
        "staff_name": staff.full_name or staff.email or staff.phone or "Staff",
        "staff_email": staff.email or "",
        "handled_today": handled_today,
        "avg_delivery_hours": round(avg_delivery_hours, 1) if avg_delivery_hours is not None else None,
        "ring_handled_pct": ring_handled,
        "ring_speed_pct": ring_speed,
        "pipeline_labels": [
            ("confirmed", "Confirm"),
            ("processing", "Process"),
            ("shipped", "Ship"),
            ("delivered", "DELIVERED"),
            ("cancelled", "Cancel"),
        ],
    }
    return render(request, "staff/delivery_panel.html", context)


@staff_admin_required
def staff_dashboard(request):
    """Landing hub after staff login — links to delivery ops and admin tools."""
    if getattr(request.user, "can_use_delivery_ops", False) and not getattr(
        request.user, "can_access_admin_panel", False
    ):
        return redirect("staff_delivery_panel")
    return render(request, "staff/staff_hub.html", {})
