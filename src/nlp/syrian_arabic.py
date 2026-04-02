"""Syrian Arabic dialect NLP processor.

Handles text normalization, intent detection, and entity extraction
specifically tuned for Syrian Arabic (اللهجة السورية).
"""

import re


# Syrian dialect keyword mappings for intent detection
INTENT_KEYWORDS = {
    "new_order": [
        "بدي اطلب", "بدي طلب", "اطلب", "طلبية", "طلبية جديدة",
        "طلبيه", "طلبيه جديده",
        "بدي اشتري", "شو عندكم", "القائمة", "المنيو", "order",
    ],
    "check_order": [
        "وين طلبيتي", "شو صار بالطلب", "وصلت", "جاهز", "تتبع",
        "وين صارت", "كم بقي", "order status",
    ],
    "cancel_order": [
        "الغي", "بدي الغي", "ما بدي", "كنسل", "cancel",
    ],
    "view_products": [
        "شو عندكم", "القائمة", "المنيو", "الأصناف", "المنتجات",
        "اعرض", "وريني", "menu", "products",
    ],
    "help": [
        "مساعدة", "مساعده", "كيف", "شلون", "شو بتقدرو", "help",
    ],
    "greeting": [
        "مرحبا", "هلا", "أهلا", "السلام عليكم", "صباح الخير",
        "مساء الخير", "هاي", "hi", "hello",
    ],
    "inventory_check": [
        "كم باقي", "المخزون", "الكمية", "متوفر", "stock",
    ],
    "payment": [
        "دفع", "بدي ادفع", "كاش", "سيرياتيل كاش", "تحويل", "pay",
    ],
    "report": [
        "تقرير", "احصائيات", "مبيعات", "كم بعنا", "report", "stats",
    ],
}

# Common Syrian Arabic normalizations
NORMALIZATIONS = {
    "أ": "ا",
    "إ": "ا",
    "آ": "ا",
    "ة": "ه",
    "ى": "ي",
    "ؤ": "و",
    "ئ": "ي",
}


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for consistent matching."""
    # Remove diacritics (tashkeel)
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    # Apply character normalizations
    for original, replacement in NORMALIZATIONS.items():
        text = text.replace(original, replacement)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def detect_intent(text: str) -> tuple[str, float]:
    """Detect the user's intent from Syrian Arabic text.

    Returns (intent_name, confidence_score).
    """
    normalized = normalize_arabic(text.lower())

    best_intent = "unknown"
    best_score = 0.0

    for intent, keywords in INTENT_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in normalized)
        if matches > 0:
            score = matches / len(keywords)
            if score > best_score:
                best_score = score
                best_intent = intent

    return best_intent, min(best_score * 3, 1.0)  # Scale up confidence


def extract_quantity(text: str) -> int | None:
    """Extract a quantity number from text."""
    # Arabic numerals
    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))

    # Written Arabic numbers
    arabic_numbers = {
        "واحد": 1, "اثنين": 2, "تلاته": 3, "اربعه": 4, "خمسه": 5,
        "سته": 6, "سبعه": 7, "تمانيه": 8, "تسعه": 9, "عشره": 10,
        "تنين": 2, "تلاتة": 3, "اربعة": 4, "خمسة": 5,
    }
    normalized = normalize_arabic(text)
    for word, num in arabic_numbers.items():
        if word in normalized:
            return num
    return None


def extract_phone(text: str) -> str | None:
    """Extract a Syrian phone number from text."""
    # Syrian phone: +963 9XX XXX XXX or 09XX XXX XXX
    match = re.search(r"(?:\+?963|0)9\d{8}", text.replace(" ", "").replace("-", ""))
    if match:
        return match.group(0)
    return None


def is_arabic(text: str) -> bool:
    """Check if text contains Arabic characters."""
    return bool(re.search(r"[\u0600-\u06FF]", text))
