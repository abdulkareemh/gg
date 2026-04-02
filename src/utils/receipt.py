"""Order receipt generator.

Generates formatted text receipts that can be sent via WhatsApp/Telegram.
"""

from datetime import datetime


def generate_receipt(
    merchant_name: str,
    order_id: int,
    items: list[dict],
    subtotal: float,
    delivery_fee: float = 0,
    discount: float = 0,
    payment_method: str | None = None,
    customer_name: str | None = None,
    order_date: datetime | None = None,
) -> str:
    """Generate a formatted text receipt."""
    date_str = (order_date or datetime.utcnow()).strftime("%Y-%m-%d %H:%M")
    total = subtotal + delivery_fee - discount

    lines = [
        "═══════════════════════════",
        f"         {merchant_name}",
        "═══════════════════════════",
        f"  فاتورة #{order_id}",
        f"  التاريخ: {date_str}",
    ]

    if customer_name:
        lines.append(f"  الزبون: {customer_name}")

    lines.extend([
        "───────────────────────────",
        "  الصنف            الكمية    السعر",
        "───────────────────────────",
    ])

    for item in items:
        name = item.get("name_ar", item.get("name", "?"))
        qty = item.get("quantity", 1)
        price = item.get("total", item.get("price", 0) * qty)
        # Pad for alignment
        lines.append(f"  {name[:16]:<16} {qty:>3}   {price:>10,.0f}")

    lines.append("───────────────────────────")
    lines.append(f"  المجموع الفرعي:      {subtotal:>10,.0f} ل.س")

    if delivery_fee > 0:
        lines.append(f"  رسوم التوصيل:        {delivery_fee:>10,.0f} ل.س")

    if discount > 0:
        lines.append(f"  الخصم:              -{discount:>10,.0f} ل.س")

    lines.extend([
        "═══════════════════════════",
        f"  المجموع:             {total:>10,.0f} ل.س",
        "═══════════════════════════",
    ])

    if payment_method:
        method_labels = {
            "syriatel_cash": "سيرياتيل كاش",
            "mtn_cash": "MTN كاش",
            "cash": "كاش",
        }
        lines.append(f"  طريقة الدفع: {method_labels.get(payment_method, payment_method)}")

    lines.extend([
        "",
        "  شكراً لتعاملكم معنا! 🙏",
        "  مدعوم من نور AI 🌟",
        "═══════════════════════════",
    ])

    return "\n".join(lines)


def generate_simple_receipt(order_id: int, items: list[dict], total: float) -> str:
    """Generate a minimal receipt for quick orders."""
    lines = [f"🧾 فاتورة #{order_id}"]

    for item in items:
        name = item.get("name_ar", "?")
        qty = item.get("quantity", 1)
        price = qty * item.get("price", 0)
        lines.append(f"  {name} × {qty} = {price:,.0f}")

    lines.append(f"💰 المجموع: {total:,.0f} ل.س")
    return "\n".join(lines)
