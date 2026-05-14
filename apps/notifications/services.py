"""Notification services — Email (SMTP) + OTP console fallback"""
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_otp_console(user, otp_code):
    """Print OTP to console (dev) and optionally send via email."""
    identifier = user.email or user.phone or str(user.pk)
    print(f"\n{'='*50}")
    print(f"  AaramKart OTP for {identifier}: {otp_code}")
    print(f"  (valid for 10 minutes)")
    print(f"{'='*50}\n")
    logger.info(f"OTP generated for {identifier}: {otp_code}")

    # Also send via email if available
    if user.email and settings.EMAIL_HOST_USER:
        try:
            send_mail(
                subject="Your AaramKart Login OTP",
                message=f"Your OTP is: {otp_code}\n\nValid for 10 minutes.\n\n— AaramKart Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.warning(f"OTP email failed: {e}")


def send_order_confirmation(order):
    """Send order confirmation email to customer and admin."""
    # Customer email
    if order.email:
        try:
            subject = f"Order Confirmed — #{order.order_number} | AaramKart"
            body = _build_order_email(order)
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.email],
                fail_silently=True,
            )
            logger.info(f"Order confirmation sent to {order.email}")
        except Exception as e:
            logger.warning(f"Customer order email failed: {e}")

    # Admin notification
    admin_email = getattr(settings, "ADMIN_EMAIL", "")
    if admin_email:
        try:
            subject = f"New Order #{order.order_number} — {order.business_name}"
            body = f"""New order received on AaramKart!

Order Number : {order.order_number}
Business     : {order.business_name}
Customer     : {order.customer_name}
Phone        : {order.phone}
Address      : {order.address}, {order.city} - {order.pincode}
Total        : ₹{order.total_amount}
Payment      : Cash on Delivery

Items:
"""
            for item in order.items.all():
                body += f"  - {item.product_name} (x{item.quantity}) @ ₹{item.unit_price} = ₹{item.line_total()}\n"

            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
                fail_silently=True,
            )
            logger.info(f"Admin notification sent for order {order.order_number}")
        except Exception as e:
            logger.warning(f"Admin order email failed: {e}")

    # Console log always
    print(f"\n{'='*60}")
    print(f"  NEW ORDER: #{order.order_number}")
    print(f"  Business : {order.business_name}")
    print(f"  Total    : ₹{order.total_amount}")
    print(f"  Status   : {order.status}")
    print(f"{'='*60}\n")


def _build_order_email(order):
    lines = [
        f"Dear {order.customer_name},",
        f"",
        f"Thank you for your order on AaramKart!",
        f"",
        f"Order Number : {order.order_number}",
        f"Business     : {order.business_name}",
        f"Total Amount : ₹{order.total_amount}",
        f"Payment      : Cash on Delivery",
        f"Status       : {order.get_status_display()}",
        f"",
        f"Delivery Address:",
        f"  {order.address}",
        f"  {order.city} — {order.pincode}",
        f"",
        f"Items Ordered:",
    ]
    for item in order.items.all():
        lines.append(f"  • {item.product_name} (x{item.quantity}) — ₹{item.line_total()}")
    lines += [
        f"",
        f"We will contact you on {order.phone} to confirm your order.",
        f"",
        f"— Team AaramKart",
        f"  Aapka Aaram, Hamara Kaam",
    ]
    return "\n".join(lines)


def _normalize_in_mobile_10(phone_raw):
    digits = "".join(c for c in (phone_raw or "") if c.isdigit())
    if len(digits) >= 10:
        return digits[-10:]
    return ""


def notify_customer_order_status_change(order, previous_status, new_status):
    """
    Notify customer when staff advances order status (SMS via Fast2SMS,
    WhatsApp via CallMeBot to 91XXXXXXXXXX, optional email).
    No-ops when API keys are missing; always logs to console.
    """
    if previous_status == new_status:
        return
    if new_status not in {"confirmed", "processing", "shipped", "delivered"}:
        return

    customer = order.customer_name or "Customer"
    num = order.order_number
    msgs = {
        "confirmed": (
            f"Hi {customer}, AaramKart order #{num} is confirmed. "
            f"We will prepare your wholesale delivery from Shillong."
        ),
        "processing": f"Hi {customer}, order #{num} is being processed at AaramKart.",
        "shipped": (
            f"Hi {customer}, order #{num} is SHIPPED and on the way. "
            f"Questions? Reply to this SMS. — AaramKart"
        ),
        "delivered": f"Hi {customer}, order #{num} has been delivered. Thank you! — AaramKart",
    }
    text = msgs.get(new_status)
    if not text:
        return

    mobile = _normalize_in_mobile_10(order.phone)
    logger.info("Order %s status %s → %s (customer notify)", num, previous_status, new_status)

    print(f"\n[STATUS NOTIFY] #{num} {previous_status} → {new_status}\n  {text}\n")

    if order.email and settings.EMAIL_HOST_USER:
        try:
            send_mail(
                subject=f"AaramKart — Order #{num} update ({new_status.replace('_', ' ').title()})",
                message=text + "\n\n— Team AaramKart\nShillong",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.warning("Status email failed: %s", e)

    api_key = getattr(settings, "FAST2SMS_API_KEY", "") or ""
    if api_key and mobile and new_status in {"shipped", "delivered"}:
        try:
            import requests

            r = requests.post(
                "https://www.fast2sms.com/dev/bulkV2",
                json={
                    "route": "q",
                    "message": text,
                    "language": "english",
                    "numbers": mobile,
                },
                headers={"authorization": api_key},
                timeout=12,
            )
            if r.status_code != 200:
                logger.warning("Fast2SMS HTTP %s: %s", r.status_code, (r.text or "")[:200])
        except Exception as e:
            logger.warning("Fast2SMS failed: %s", e)

    wkey = (getattr(settings, "CALLMEBOT_API_KEY", "") or "").strip()
    if wkey and mobile and new_status in {"shipped", "delivered"}:
        try:
            import urllib.parse

            import requests

            msg_q = urllib.parse.quote_plus(text)
            phone_intl = "91" + mobile
            url = (
                "https://api.callmebot.com/whatsapp.php?"
                f"phone={phone_intl}&text={msg_q}&apikey={urllib.parse.quote_plus(wkey)}"
            )
            r = requests.get(url, timeout=15)
            body = (r.text or "").strip()
            if r.status_code != 200 or body.upper().startswith("ERROR"):
                logger.warning("CallMeBot WhatsApp: %s %s", r.status_code, body[:200])
        except Exception as e:
            logger.warning("WhatsApp notify failed: %s", e)
