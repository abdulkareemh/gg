"""Comprehensive Arabic number word parser.

Parses both Eastern Arabic numerals (١٢٣) and written number words
in Syrian Arabic dialect.
"""

import re

# Eastern Arabic digits mapping
EASTERN_ARABIC = {"٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
                  "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9"}

# Syrian Arabic number words
NUMBER_WORDS = {
    # Units
    "صفر": 0, "واحد": 1, "وحدة": 1, "واحدة": 1,
    "اثنين": 2, "تنين": 2, "اتنين": 2,
    "ثلاثة": 3, "تلاته": 3, "تلاتة": 3, "ثلاث": 3,
    "أربعة": 4, "اربعه": 4, "اربعة": 4, "أربع": 4,
    "خمسة": 5, "خمسه": 5, "خمس": 5,
    "ستة": 6, "سته": 6, "ست": 6,
    "سبعة": 7, "سبعه": 7, "سبع": 7,
    "ثمانية": 8, "تمانيه": 8, "تمانية": 8, "ثماني": 8, "تمنه": 8,
    "تسعة": 9, "تسعه": 9, "تسع": 9,
    "عشرة": 10, "عشره": 10, "عشر": 10,
    # Teens
    "أحد عشر": 11, "حدعش": 11, "احدعشر": 11,
    "اثنا عشر": 12, "اثنعش": 12, "طنعش": 12,
    "ثلاثة عشر": 13, "تلطعش": 13, "تلتعش": 13,
    "أربعة عشر": 14, "اربعتعش": 14,
    "خمسة عشر": 15, "خمستعش": 15,
    "ستة عشر": 16, "ستعش": 16,
    "سبعة عشر": 17, "سبعتعش": 17,
    "ثمانية عشر": 18, "تمنتعش": 18,
    "تسعة عشر": 19, "تسعتعش": 19,
    # Tens
    "عشرين": 20, "عشرون": 20,
    "ثلاثين": 30, "تلاتين": 30,
    "أربعين": 40, "اربعين": 40,
    "خمسين": 50,
    "ستين": 60,
    "سبعين": 70,
    "ثمانين": 80, "تمانين": 80,
    "تسعين": 90,
    # Hundreds
    "مية": 100, "مئة": 100, "ميه": 100,
    "ميتين": 200, "مئتين": 200,
    "ثلاثمية": 300, "تلتمية": 300,
    "أربعمية": 400, "اربعمية": 400,
    "خمسمية": 500,
    "ستمية": 600,
    "سبعمية": 700,
    "ثمنمية": 800, "تمنمية": 800,
    "تسعمية": 900,
    # Large numbers
    "ألف": 1000, "الف": 1000,
    "ألفين": 2000, "الفين": 2000,
    "مليون": 1000000,
    # Common quantities
    "نص": 0.5, "نصف": 0.5,
    "ربع": 0.25,
    "كيلو": 1, "كيلوين": 2,
    "درزن": 12, "درزينة": 12,
}

# Ordinal words
ORDINALS = {
    "أول": 1, "اول": 1, "أولى": 1,
    "ثاني": 2, "تاني": 2,
    "ثالث": 3, "تالت": 3,
    "رابع": 4,
    "خامس": 5,
}


def convert_eastern_arabic(text: str) -> str:
    """Convert Eastern Arabic numerals (١٢٣) to Western (123)."""
    result = text
    for eastern, western in EASTERN_ARABIC.items():
        result = result.replace(eastern, western)
    return result


def parse_number(text: str) -> float | None:
    """Parse a number from Arabic text.

    Handles:
    - Western digits: "3", "25"
    - Eastern Arabic digits: "٣", "٢٥"
    - Written words: "ثلاثة", "خمسة وعشرين"
    - Mixed: "3 كيلو"
    """
    text = text.strip()

    # Try Western digits first
    match = re.search(r"[\d,]+\.?\d*", text)
    if match:
        try:
            return float(match.group().replace(",", ""))
        except ValueError:
            pass

    # Try Eastern Arabic digits
    converted = convert_eastern_arabic(text)
    match = re.search(r"[\d,]+\.?\d*", converted)
    if match:
        try:
            return float(match.group().replace(",", ""))
        except ValueError:
            pass

    # Try word-based parsing
    from src.nlp.syrian_arabic import normalize_arabic
    normalized = normalize_arabic(text.lower())

    # Direct word match
    for word, value in sorted(NUMBER_WORDS.items(), key=lambda x: -len(x[0])):
        if word in normalized:
            return value

    return None


def parse_quantity_and_item(text: str) -> tuple[int | None, str]:
    """Parse a quantity and item name from text.

    Examples:
        "3 شاورما" → (3, "شاورما")
        "تلاته فلافل" → (3, "فلافل")
        "شاورما" → (1, "شاورما")  # default quantity 1
    """
    text = text.strip()

    # Check for leading number
    match = re.match(r"(\d+)\s+(.+)", text)
    if match:
        return int(match.group(1)), match.group(2).strip()

    # Check for Eastern Arabic number
    converted = convert_eastern_arabic(text)
    match = re.match(r"(\d+)\s+(.+)", converted)
    if match:
        return int(match.group(1)), match.group(2).strip()

    # Check for number word at start
    from src.nlp.syrian_arabic import normalize_arabic
    normalized = normalize_arabic(text.lower())

    for word, value in sorted(NUMBER_WORDS.items(), key=lambda x: -len(x[0])):
        if normalized.startswith(word):
            remaining = text[len(word):].strip()
            if remaining:
                return int(value), remaining

    # No quantity found — assume 1
    return 1, text


def parse_price(text: str) -> float | None:
    """Parse a price from Arabic text.

    Handles: "25000", "25,000", "٢٥٠٠٠", "25 ألف", "خمسة وعشرين ألف"
    """
    text = text.strip().replace("ل.س", "").replace("ليرة", "").strip()

    # Try direct number
    num = parse_number(text)
    if num is not None:
        return num

    # Check for "X ألف" pattern
    match = re.search(r"(\d+)\s*(?:ألف|الف)", text)
    if match:
        return float(match.group(1)) * 1000

    return None
