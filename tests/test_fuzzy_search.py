"""Tests for Arabic fuzzy product search."""

from src.nlp.fuzzy_search import fuzzy_match_product, suggest_products


SAMPLE_PRODUCTS = [
    {"name": "Shawarma", "name_ar": "شاورما دجاج", "price": 25000},
    {"name": "Falafel", "name_ar": "فلافل", "price": 15000},
    {"name": "Hummus", "name_ar": "حمص", "price": 10000},
    {"name": "Fattoush", "name_ar": "فتوش", "price": 12000},
    {"name": "Tabbouleh", "name_ar": "تبولة", "price": 12000},
    {"name": "Kibbeh", "name_ar": "كبة", "price": 20000},
    {"name": "Orange Juice", "name_ar": "عصير برتقال", "price": 5000},
    {"name": "Pizza Margherita", "name_ar": "بيتزا مارغريتا", "price": 30000},
]


class TestFuzzyMatchProduct:
    def test_exact_match(self):
        results = fuzzy_match_product("فلافل", SAMPLE_PRODUCTS)
        assert len(results) >= 1
        assert results[0]["name"] == "Falafel"

    def test_partial_match(self):
        results = fuzzy_match_product("شاورما", SAMPLE_PRODUCTS)
        assert len(results) >= 1
        assert results[0]["name"] == "Shawarma"

    def test_english_match(self):
        results = fuzzy_match_product("pizza", SAMPLE_PRODUCTS)
        assert len(results) >= 1
        assert results[0]["name"] == "Pizza Margherita"

    def test_no_match(self):
        results = fuzzy_match_product("سوشي", SAMPLE_PRODUCTS, threshold=0.8)
        assert len(results) == 0

    def test_substring_match(self):
        results = fuzzy_match_product("عصير", SAMPLE_PRODUCTS)
        assert len(results) >= 1
        assert "عصير" in results[0]["name_ar"]


class TestSuggestProducts:
    def test_limit(self):
        results = suggest_products("ش", SAMPLE_PRODUCTS, limit=3)
        assert len(results) <= 3

    def test_returns_top_matches(self):
        results = suggest_products("شاورما", SAMPLE_PRODUCTS, limit=5)
        assert len(results) >= 1
        # Shawarma should be the top result
        assert results[0]["name"] == "Shawarma"


class TestEdgeCases:
    def test_empty_query(self):
        results = fuzzy_match_product("", SAMPLE_PRODUCTS)
        assert len(results) == 0

    def test_empty_products(self):
        results = fuzzy_match_product("شاورما", [])
        assert len(results) == 0

    def test_misspelled_arabic(self):
        # "شورما" instead of "شاورما" — should still match
        results = fuzzy_match_product("شورما", SAMPLE_PRODUCTS, threshold=0.4)
        assert len(results) >= 1
