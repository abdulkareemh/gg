"""Tests for conversation context builder."""

from src.nlp.conversation import (
    build_conversation_prompt,
    format_order_summary,
    format_product_menu,
)


class TestBuildConversationPrompt:
    def test_returns_messages_list(self):
        messages = build_conversation_prompt(
            merchant_name="مطعم الشام",
            products=[],
            history=[],
        )
        assert isinstance(messages, list)
        assert len(messages) >= 2

    def test_includes_merchant_name(self):
        messages = build_conversation_prompt(
            merchant_name="مطعم الشام",
            products=[],
            history=[],
        )
        context = messages[0]["content"]
        assert "مطعم الشام" in context

    def test_includes_products(self):
        products = [{"name_ar": "شاورما", "price": 25000, "stock": 10}]
        messages = build_conversation_prompt(
            merchant_name="test",
            products=products,
            history=[],
        )
        context = messages[0]["content"]
        assert "شاورما" in context

    def test_includes_history(self):
        history = [
            {"role": "user", "text": "مرحبا"},
            {"role": "bot", "text": "أهلا وسهلا!"},
        ]
        messages = build_conversation_prompt(
            merchant_name="test",
            products=[],
            history=history,
        )
        # 2 system messages + 2 history
        assert len(messages) == 4

    def test_limits_history_to_8(self):
        history = [{"role": "user", "text": f"msg {i}"} for i in range(20)]
        messages = build_conversation_prompt(
            merchant_name="test",
            products=[],
            history=history,
        )
        # 2 system + 8 history
        assert len(messages) == 10


class TestFormatOrderSummary:
    def test_empty_cart(self):
        result = format_order_summary([])
        assert "فاضية" in result

    def test_single_item(self):
        items = [{"name_ar": "شاورما", "quantity": 2, "price": 25000}]
        result = format_order_summary(items)
        assert "شاورما" in result
        assert "50,000" in result

    def test_multiple_items_total(self):
        items = [
            {"name_ar": "شاورما", "quantity": 1, "price": 25000},
            {"name_ar": "عصير", "quantity": 2, "price": 5000},
        ]
        result = format_order_summary(items)
        assert "35,000" in result


class TestFormatProductMenu:
    def test_empty_products(self):
        result = format_product_menu([])
        assert "ما في" in result

    def test_with_products(self):
        products = [
            {"name_ar": "شاورما", "price": 25000, "stock": 10, "category": "ساندويشات"},
            {"name_ar": "فلافل", "price": 15000, "stock": 0, "category": "ساندويشات"},
        ]
        result = format_product_menu(products)
        assert "شاورما" in result
        assert "فلافل" in result
        assert "✅" in result  # in stock
        assert "❌" in result  # out of stock
