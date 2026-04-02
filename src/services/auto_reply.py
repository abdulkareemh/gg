"""Smart auto-reply for common customer questions.

Handles FAQ-type questions without routing to Claude,
providing instant responses for common queries.
"""

from src.nlp.syrian_arabic import normalize_arabic


# FAQ patterns and their responses
FAQ_PATTERNS: list[tuple[list[str], str]] = [
    # Business hours
    (
        ["ساعات العمل", "ساعات الدوام", "وقت الفتح", "امتى بتفتحو", "متى بتسكرو",
         "مفتوح", "مسكر", "opening hours", "when open"],
        "ساعات العمل: {opening_time} - {closing_time}\nأيام الإغلاق: {closed_days}",
    ),
    # Location / address
    (
        ["العنوان", "الموقع", "وين محلكم", "وين موقعكم", "كيف بوصلكم",
         "address", "location", "where"],
        "📍 موقعنا: {city}, {address}",
    ),
    # Delivery
    (
        ["بتوصلو", "في توصيل", "تكلفة التوصيل", "رسوم التوصيل", "كم التوصيل",
         "delivery", "do you deliver"],
        "🚚 نعم منوصّل! ابعت 'مناطق التوصيل' لتشوف المناطق والأسعار.",
    ),
    # Payment methods
    (
        ["طرق الدفع", "كيف بدفع", "بتقبلو", "سيرياتيل", "mtn",
         "payment", "how to pay"],
        "💳 طرق الدفع المتاحة:\n• كاش عند الاستلام\n• سيرياتيل كاش\n• MTN كاش",
    ),
    # Menu / products
    (
        ["المنيو", "القائمة", "الأصناف", "شو عندكم", "menu", "what do you have"],
        "📋 ابعت 'القائمة' وبعرضلك كل المنتجات المتوفرة!",
    ),
    # Order status
    (
        ["وين طلبيتي", "شو صار", "وصلت", "order status"],
        "📦 ابعت رقم الطلبية وبخبرك شو صار فيها!",
    ),
    # Contact
    (
        ["رقم الهاتف", "تلفون", "بدي احكي مع حدا", "phone", "contact"],
        "📞 تقدر تتواصل معنا على: {phone}",
    ),
    # Return / refund
    (
        ["إرجاع", "استرداد", "رجّعو", "مش صح", "غلط", "return", "refund"],
        "تواصل معنا مباشرة وبنحل المشكلة فوراً! 🙏",
    ),
]


def get_auto_reply(message: str, merchant_context: dict) -> str | None:
    """Try to match an FAQ pattern and return an auto-reply.

    Returns None if no FAQ pattern matches.
    """
    normalized = normalize_arabic(message.lower())

    for keywords, template in FAQ_PATTERNS:
        for keyword in keywords:
            if keyword in normalized:
                try:
                    return template.format(**merchant_context)
                except KeyError:
                    return template

    return None


def get_faq_list() -> str:
    """Generate a list of available FAQ topics."""
    topics = [
        "🕐 ساعات العمل",
        "📍 العنوان والموقع",
        "🚚 التوصيل ومناطقه",
        "💳 طرق الدفع",
        "📋 القائمة والمنتجات",
        "📦 حالة الطلبية",
        "📞 التواصل معنا",
    ]
    return "❓ الأسئلة الشائعة:\n" + "\n".join(f"  {t}" for t in topics)
