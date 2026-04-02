"""Fuzzy search for Arabic product names.

Handles common issues with Arabic text matching:
- Spelling variations (شاورما vs شاورمة vs شاورما)
- Missing/extra letters
- Transliteration from English (shawarma -> شاورما)
- Partial matches
"""

from src.nlp.syrian_arabic import normalize_arabic


# Common product name aliases (Syrian dialect)
PRODUCT_ALIASES = {
    "شاورما": ["شاورمة", "شاورمه", "شورما", "shawarma"],
    "فلافل": ["فلافل", "فلاقل", "falafel"],
    "حمص": ["حمص", "حموص", "hummus"],
    "فتوش": ["فتوش", "فطوش", "fattoush"],
    "تبولة": ["تبوله", "تبولي", "tabbouleh"],
    "كبة": ["كبه", "كبب", "kibbeh"],
    "متبل": ["متبل", "بابا غنوج", "baba ghanoush"],
    "منقوشة": ["منقوشه", "منئوشة", "manouche", "manakish"],
    "عصير": ["عصير", "جوس", "juice"],
    "قهوة": ["قهوه", "قهوة عربية", "coffee"],
    "شاي": ["شاي", "تي", "tea"],
    "بيتزا": ["بيتزا", "بيتسا", "pizza"],
    "برغر": ["برغر", "همبرغر", "برجر", "burger", "hamburger"],
    "سندويش": ["سندويش", "سندويشة", "ساندويتش", "sandwich"],
    "سلطة": ["سلطه", "سلطات", "salad"],
}


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


def _similarity(s1: str, s2: str) -> float:
    """Calculate similarity ratio between two strings (0.0 to 1.0)."""
    if not s1 or not s2:
        return 0.0
    max_len = max(len(s1), len(s2))
    distance = _levenshtein_distance(s1, s2)
    return 1.0 - (distance / max_len)


def fuzzy_match_product(query: str, products: list[dict], threshold: float = 0.5) -> list[dict]:
    """Find products matching a fuzzy search query.

    Args:
        query: Search text (Arabic or English)
        products: List of product dicts with 'name_ar' and 'name' keys
        threshold: Minimum similarity score (0.0-1.0)

    Returns:
        List of (product, score) sorted by relevance
    """
    normalized_query = normalize_arabic(query.lower().strip())
    results = []

    for product in products:
        best_score = 0.0

        # Check exact substring match first
        name_ar = normalize_arabic(product.get("name_ar", "").lower())
        name_en = product.get("name", "").lower()

        if normalized_query in name_ar or normalized_query in name_en:
            best_score = 1.0
        else:
            # Fuzzy match against Arabic name
            score = _similarity(normalized_query, name_ar)
            best_score = max(best_score, score)

            # Fuzzy match against English name
            score = _similarity(query.lower(), name_en)
            best_score = max(best_score, score)

            # Check word-level matches
            query_words = normalized_query.split()
            name_words = name_ar.split()
            for qw in query_words:
                for nw in name_words:
                    word_score = _similarity(qw, nw)
                    best_score = max(best_score, word_score)

            # Check aliases
            for canonical, aliases in PRODUCT_ALIASES.items():
                canonical_norm = normalize_arabic(canonical)
                if _similarity(normalized_query, canonical_norm) > 0.7:
                    for alias in aliases:
                        alias_norm = normalize_arabic(alias.lower())
                        if alias_norm in name_ar or _similarity(alias_norm, name_ar) > 0.7:
                            best_score = max(best_score, 0.85)
                            break

        if best_score >= threshold:
            results.append({**product, "_score": best_score})

    # Sort by score descending
    results.sort(key=lambda x: x["_score"], reverse=True)
    return results


def suggest_products(query: str, products: list[dict], limit: int = 5) -> list[dict]:
    """Get top product suggestions for a search query."""
    matches = fuzzy_match_product(query, products, threshold=0.4)
    return matches[:limit]
