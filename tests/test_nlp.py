"""Tests for Syrian Arabic NLP pipeline."""

from src.nlp.syrian_arabic import (
    normalize_arabic,
    detect_intent,
    extract_quantity,
    extract_phone,
    is_arabic,
)


class TestNormalizeArabic:
    def test_removes_diacritics(self):
        assert normalize_arabic("مَرْحَبًا") == "مرحبا"

    def test_normalizes_alef(self):
        assert normalize_arabic("أهلا") == "اهلا"
        assert normalize_arabic("إسلام") == "اسلام"

    def test_normalizes_taa_marbuta(self):
        assert normalize_arabic("طلبية") == "طلبيه"

    def test_normalizes_whitespace(self):
        assert normalize_arabic("  مرحبا   كيفك  ") == "مرحبا كيفك"


class TestDetectIntent:
    def test_greeting(self):
        intent, _ = detect_intent("مرحبا")
        assert intent == "greeting"

    def test_new_order(self):
        intent, _ = detect_intent("بدي اطلب")
        assert intent == "new_order"

    def test_check_order(self):
        intent, _ = detect_intent("وين طلبيتي")
        assert intent == "check_order"

    def test_cancel_order(self):
        intent, _ = detect_intent("بدي الغي الطلب")
        assert intent == "cancel_order"

    def test_help(self):
        intent, _ = detect_intent("مساعدة")
        assert intent == "help"

    def test_inventory(self):
        intent, _ = detect_intent("كم باقي بالمخزون")
        assert intent == "inventory_check"

    def test_english_fallback(self):
        intent, _ = detect_intent("hello")
        assert intent == "greeting"

    def test_unknown(self):
        intent, _ = detect_intent("xyz123")
        assert intent == "unknown"


class TestExtractQuantity:
    def test_arabic_numeral(self):
        assert extract_quantity("بدي 3 حبات") == 3

    def test_written_number(self):
        assert extract_quantity("بدي تلاته") == 3

    def test_no_quantity(self):
        assert extract_quantity("بدي اطلب") is None


class TestExtractPhone:
    def test_syrian_mobile(self):
        assert extract_phone("رقمي 0944123456") == "0944123456"

    def test_international_format(self):
        assert extract_phone("+963944123456") == "+963944123456"

    def test_no_phone(self):
        assert extract_phone("مرحبا كيفك") is None


class TestIsArabic:
    def test_arabic(self):
        assert is_arabic("مرحبا") is True

    def test_english(self):
        assert is_arabic("hello") is False

    def test_mixed(self):
        assert is_arabic("hello مرحبا") is True
