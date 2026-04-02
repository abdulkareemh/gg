"""Tests for diaspora service and currency conversion."""

from src.services.diaspora_service import (
    convert_to_syp,
    convert_from_syp,
    format_price_multi_currency,
    format_diaspora_order_message,
    EXCHANGE_RATES,
)


class TestCurrencyConversion:
    def test_usd_to_syp(self):
        result = convert_to_syp(10, "USD")
        assert result == 10 * EXCHANGE_RATES["USD"]

    def test_eur_to_syp(self):
        result = convert_to_syp(10, "EUR")
        assert result == 10 * EXCHANGE_RATES["EUR"]

    def test_syp_to_usd(self):
        result = convert_from_syp(145000, "USD")
        assert result == 10.0

    def test_unknown_currency(self):
        assert convert_to_syp(10, "XYZ") is None
        assert convert_from_syp(10000, "XYZ") is None

    def test_format_multi_currency(self):
        result = format_price_multi_currency(145000, "USD")
        assert "145,000" in result
        assert "USD" in result
        assert "10.00" in result


class TestDiasporaOrderMessage:
    def test_format_order(self):
        order = {
            "sender": {"name": "أحمد", "country": "DE"},
            "recipient": {"name": "فاطمة", "city": "دمشق"},
            "items": [
                {"name_ar": "شاورما", "quantity": 2},
                {"name_ar": "عصير", "quantity": 1},
            ],
            "total_syp": 55000,
            "foreign_currency": "EUR",
            "delivery_fee_syp": 15000,
            "message": "كل عام وانتي بخير يا ماما",
        }

        result = format_diaspora_order_message(order)
        assert "أحمد" in result
        assert "فاطمة" in result
        assert "دمشق" in result
        assert "شاورما" in result
        assert "ألمانيا" in result
        assert "كل عام" in result

    def test_format_without_message(self):
        order = {
            "sender": {"name": "خالد", "country": "TR"},
            "recipient": {"name": "سارة", "city": "حلب"},
            "items": [{"name_ar": "هدية", "quantity": 1}],
            "total_syp": 100000,
            "foreign_currency": "TRY",
            "delivery_fee_syp": 15000,
            "message": "",
        }
        result = format_diaspora_order_message(order)
        assert "💌" not in result  # No message section
