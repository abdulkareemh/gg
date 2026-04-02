"""Tests for Sprint 8 — feedback, Arabic numbers, business hours, repeat orders, auth."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.feedback_agent import FeedbackAgent
from src.nlp.arabic_numbers import (
    parse_number, parse_quantity_and_item, parse_price,
    convert_eastern_arabic, NUMBER_WORDS,
)
from src.services.business_hours import (
    is_within_hours, get_away_message, get_syria_time,
)
from src.services.repeat_order_service import RepeatOrderService, format_repeat_order
from src.services.onboarding_guide import OnboardingGuide
from src.services.merchant_service import MerchantService
from src.services.customer_service import CustomerService
from src.services.product_service import ProductService
from src.services.order_service import OrderService
from src.api.auth import generate_api_key, hash_api_key


# --- Arabic Number Parser ---

class TestArabicNumbers:
    def test_western_digits(self):
        assert parse_number("25") == 25
        assert parse_number("3") == 3

    def test_eastern_arabic_digits(self):
        assert convert_eastern_arabic("١٢٣") == "123"
        assert parse_number("٢٥") == 25

    def test_number_words(self):
        assert parse_number("ثلاثة") == 3
        assert parse_number("تلاته") == 3
        assert parse_number("خمسة") == 5
        assert parse_number("عشرة") == 10

    def test_quantity_and_item(self):
        qty, item = parse_quantity_and_item("3 شاورما")
        assert qty == 3
        assert item == "شاورما"

    def test_word_quantity_and_item(self):
        qty, item = parse_quantity_and_item("تلاته فلافل")
        assert qty == 3
        assert item == "فلافل"

    def test_default_quantity(self):
        qty, item = parse_quantity_and_item("شاورما")
        assert qty == 1
        assert item == "شاورما"

    def test_parse_price(self):
        assert parse_price("25000") == 25000
        assert parse_price("25,000") == 25000

    def test_parse_price_with_suffix(self):
        assert parse_price("25000 ل.س") == 25000

    def test_unknown_returns_none(self):
        assert parse_number("hello world") is None


# --- Feedback Agent ---

class TestFeedbackAgent:
    def setup_method(self):
        self.agent = FeedbackAgent()

    @pytest.mark.asyncio
    async def test_initial_ask_rating(self):
        response = await self.agent.handle(1, "", {"feedback_step": None})
        assert response.action == "ask_rating"
        assert "1" in response.text_ar
        assert "5" in response.text_ar

    @pytest.mark.asyncio
    async def test_process_rating_number(self):
        response = await self.agent.handle(1, "5", {"feedback_step": "rating"})
        assert response.action == "rating_received"
        assert response.data["rating"] == 5

    @pytest.mark.asyncio
    async def test_process_rating_word(self):
        response = await self.agent.handle(1, "ممتاز", {"feedback_step": "rating"})
        assert response.action == "rating_received"
        assert response.data["rating"] == 5

    @pytest.mark.asyncio
    async def test_process_comment_skip(self):
        response = await self.agent.handle(1, "لا", {"feedback_step": "comment"})
        assert response.action == "feedback_done"

    @pytest.mark.asyncio
    async def test_process_comment(self):
        response = await self.agent.handle(1, "الأكل كان ممتاز", {"feedback_step": "comment"})
        assert response.action == "feedback_complete"
        assert response.data["sentiment"] == "positive"


# --- Business Hours ---

class TestBusinessHours:
    def test_within_hours(self):
        # This depends on current time, but we test the function works
        result = is_within_hours("00:00", "23:59")
        assert result is True

    def test_outside_hours(self):
        result = is_within_hours("25:00", "25:01")  # Impossible range
        assert result is False

    def test_away_message(self):
        msg = get_away_message("مطعم الشام", "09:00", "23:00", "")
        assert "مطعم الشام" in msg
        assert "09:00" in msg

    def test_syria_time(self):
        syria = get_syria_time()
        utc = datetime.utcnow()
        diff_hours = (syria - utc).total_seconds() / 3600
        assert abs(diff_hours - 3) < 0.1


# --- Repeat Order ---

class TestRepeatOrder:
    @pytest.mark.asyncio
    async def test_get_last_order(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963949001001", "m1", "test", "restaurant", "damascus")

        c_svc = CustomerService(db_session)
        customer, _ = await c_svc.get_or_create(merchant.id, "+963957001001")

        p_svc = ProductService(db_session)
        product = await p_svc.create(merchant.id, "Shawarma", "شاورما", 25000, stock_quantity=50)

        o_svc = OrderService(db_session)
        order = await o_svc.create_order(
            merchant.id, customer.id, [{"product_id": product.id, "quantity": 2}]
        )
        await o_svc.update_status(order.id, "completed")

        repeat_svc = RepeatOrderService(db_session)
        items = await repeat_svc.get_last_order_items(merchant.id, customer.id)
        assert items is not None
        assert len(items) == 1
        assert items[0]["name_ar"] == "شاورما"
        assert items[0]["quantity"] == 2

    @pytest.mark.asyncio
    async def test_no_previous_order(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963949002001", "m1", "test", "restaurant", "damascus")

        c_svc = CustomerService(db_session)
        customer, _ = await c_svc.get_or_create(merchant.id, "+963957002001")

        repeat_svc = RepeatOrderService(db_session)
        items = await repeat_svc.get_last_order_items(merchant.id, customer.id)
        assert items is None

    def test_format_empty(self):
        assert "ما لقيت" in format_repeat_order([])

    def test_format_items(self):
        items = [{"name_ar": "شاورما", "quantity": 2, "total": 50000}]
        result = format_repeat_order(items)
        assert "شاورما" in result
        assert "50,000" in result


# --- Onboarding Guide ---

class TestOnboardingGuide:
    def test_step_count(self):
        guide = OnboardingGuide()
        assert guide.get_step_count() >= 5

    def test_get_step(self):
        guide = OnboardingGuide()
        step = guide.get_step(0)
        assert step is not None
        assert step["id"] == "welcome"

    def test_get_invalid_step(self):
        guide = OnboardingGuide()
        assert guide.get_step(999) is None

    def test_progress_bar(self):
        guide = OnboardingGuide()
        progress = guide.get_progress(3)
        assert "●" in progress

    def test_complete_message(self):
        guide = OnboardingGuide()
        last = guide.get_step(guide.get_step_count() - 1)
        assert "جاهز" in last["message"]


# --- API Key Auth ---

class TestAPIKeyAuth:
    def test_generate_api_key(self):
        raw, hashed = generate_api_key()
        assert raw.startswith("noor_")
        assert len(hashed) == 64  # SHA-256 hex

    def test_hash_consistency(self):
        raw, expected_hash = generate_api_key()
        assert hash_api_key(raw) == expected_hash

    def test_different_keys(self):
        raw1, _ = generate_api_key()
        raw2, _ = generate_api_key()
        assert raw1 != raw2
