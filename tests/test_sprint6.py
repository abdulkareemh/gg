"""Tests for Sprint 6 features — loyalty, reviews, expenses, scheduling, QR, retry."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.merchant_service import MerchantService
from src.services.customer_service import CustomerService
from src.services.product_service import ProductService
from src.services.loyalty_service import LoyaltyService, format_loyalty_status
from src.services.review_service import ReviewService, format_rating_summary
from src.services.expense_service import ExpenseService, format_profit_loss
from src.services.delivery_service import DeliveryService, format_delivery_zones
from src.services.retry_queue import RetryQueue, RetryItem
from src.utils.qrcode import generate_whatsapp_link, generate_share_text, generate_merchant_card
from src.services.report_service import format_daily_report, format_weekly_report


# --- Loyalty Tests ---

class TestLoyaltyService:
    @pytest.mark.asyncio
    async def test_setup_program(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963947001001", "m1", "test", "restaurant", "damascus")

        loyalty = LoyaltyService(db_session)
        program = await loyalty.setup_program(merchant.id)
        assert program.name == "برنامج الولاء"
        assert program.is_active is True

    @pytest.mark.asyncio
    async def test_earn_points(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963947002001", "m1", "test", "restaurant", "damascus")

        c_svc = CustomerService(db_session)
        customer, _ = await c_svc.get_or_create(merchant.id, "+963956001001")

        loyalty = LoyaltyService(db_session)
        await loyalty.setup_program(merchant.id)

        result = await loyalty.earn_points(customer.id, merchant.id, 50000)  # 50,000 SYP order
        assert result["earned"] == 50  # 0.001 * 50000
        assert result["total"] == 50

    @pytest.mark.asyncio
    async def test_redeem_points(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963947003001", "m1", "test", "restaurant", "damascus")

        c_svc = CustomerService(db_session)
        customer, _ = await c_svc.get_or_create(merchant.id, "+963956002001")

        loyalty = LoyaltyService(db_session)
        await loyalty.setup_program(merchant.id, min_redeem=50)

        # Earn enough points
        await loyalty.earn_points(customer.id, merchant.id, 200000)  # 200 points

        # Redeem
        result = await loyalty.redeem_points(customer.id, merchant.id, 100)
        assert result["success"] is True
        assert result["discount_syp"] == 10000  # 100 * 100 SYP
        assert result["remaining_points"] == 100

    @pytest.mark.asyncio
    async def test_insufficient_points(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963947004001", "m1", "test", "shop", "aleppo")

        c_svc = CustomerService(db_session)
        customer, _ = await c_svc.get_or_create(merchant.id, "+963956003001")

        loyalty = LoyaltyService(db_session)
        await loyalty.setup_program(merchant.id)

        result = await loyalty.redeem_points(customer.id, merchant.id, 500)
        assert result["success"] is False


# --- Review Tests ---

class TestReviewService:
    @pytest.mark.asyncio
    async def test_create_review(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963947005001", "m1", "test", "restaurant", "damascus")

        c_svc = CustomerService(db_session)
        customer, _ = await c_svc.get_or_create(merchant.id, "+963956004001")

        review_svc = ReviewService(db_session)
        review = await review_svc.create_review(merchant.id, customer.id, 5, "ممتاز!")
        assert review.rating == 5
        assert review.comment == "ممتاز!"

    @pytest.mark.asyncio
    async def test_merchant_rating(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963947006001", "m1", "test", "restaurant", "damascus")

        c_svc = CustomerService(db_session)
        c1, _ = await c_svc.get_or_create(merchant.id, "+963956005001")
        c2, _ = await c_svc.get_or_create(merchant.id, "+963956005002")

        review_svc = ReviewService(db_session)
        await review_svc.create_review(merchant.id, c1.id, 5)
        await review_svc.create_review(merchant.id, c2.id, 3)

        rating = await review_svc.get_merchant_rating(merchant.id)
        assert rating["average"] == 4.0
        assert rating["total_reviews"] == 2

    @pytest.mark.asyncio
    async def test_merchant_reply(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963947007001", "m1", "test", "restaurant", "damascus")

        c_svc = CustomerService(db_session)
        customer, _ = await c_svc.get_or_create(merchant.id, "+963956006001")

        review_svc = ReviewService(db_session)
        review = await review_svc.create_review(merchant.id, customer.id, 4, "جيد")
        updated = await review_svc.add_reply(review.id, "شكراً لتقييمك!")
        assert updated.reply == "شكراً لتقييمك!"


# --- Expense Tests ---

class TestExpenseService:
    @pytest.mark.asyncio
    async def test_add_expense(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963947008001", "m1", "test", "restaurant", "damascus")

        exp_svc = ExpenseService(db_session)
        expense = await exp_svc.add_expense(merchant.id, 500000, "مواد_أولية", "لحمة ودجاج")
        assert float(expense.amount) == 500000

    @pytest.mark.asyncio
    async def test_monthly_expenses(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963947009001", "m1", "test", "restaurant", "damascus")

        exp_svc = ExpenseService(db_session)
        await exp_svc.add_expense(merchant.id, 500000, "مواد_أولية")
        await exp_svc.add_expense(merchant.id, 200000, "إيجار")

        report = await exp_svc.get_monthly_expenses(merchant.id)
        assert report["total"] == 700000
        assert len(report["categories"]) == 2


# --- Delivery Tests ---

class TestDeliveryService:
    @pytest.mark.asyncio
    async def test_create_and_find_zone(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963947010001", "m1", "test", "restaurant", "damascus")

        del_svc = DeliveryService(db_session)
        await del_svc.create_zone(merchant.id, "المزة", "دمشق", delivery_fee=10000, estimated_minutes=25)

        zone = await del_svc.find_zone(merchant.id, "المزة")
        assert zone is not None
        assert float(zone.delivery_fee) == 10000

    @pytest.mark.asyncio
    async def test_calculate_delivery(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963947011001", "m1", "test", "restaurant", "damascus")

        del_svc = DeliveryService(db_session)
        await del_svc.create_zone(merchant.id, "باب توما", "دمشق", delivery_fee=8000, min_order_amount=20000)

        # Order above minimum
        result = await del_svc.calculate_delivery(merchant.id, "باب توما", 50000)
        assert result["available"] is True
        assert result["total_with_delivery"] == 58000

        # Order below minimum
        result = await del_svc.calculate_delivery(merchant.id, "باب توما", 10000)
        assert result["available"] is False

    @pytest.mark.asyncio
    async def test_unknown_zone(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963947012001", "m1", "test", "restaurant", "damascus")

        del_svc = DeliveryService(db_session)
        result = await del_svc.calculate_delivery(merchant.id, "القمر", 50000)
        assert result["available"] is False


# --- QR Code Tests ---

class TestQRCode:
    def test_whatsapp_link(self):
        link = generate_whatsapp_link("+963944123456")
        assert "wa.me/963944123456" in link

    def test_share_text(self):
        text = generate_share_text("مطعم الشام", "+963944123456")
        assert "مطعم الشام" in text
        assert "wa.me" in text

    def test_merchant_card(self):
        card = generate_merchant_card({
            "business_name": "مطعم الشام",
            "city": "دمشق",
            "phone": "+963944123456",
            "business_type": "restaurant",
            "rating": 4.5,
        })
        assert "مطعم الشام" in card
        assert "دمشق" in card
        assert "4.5" in card


# --- Retry Queue Tests ---

class TestRetryQueue:
    def test_enqueue(self):
        queue = RetryQueue()
        queue.enqueue("+963944000000", "مرحبا", "whatsapp")
        assert queue.pending_count == 1

    @pytest.mark.asyncio
    async def test_process_success(self):
        queue = RetryQueue()
        queue.enqueue("+963944000000", "test", "whatsapp")

        async def mock_send(phone, text, platform):
            return True

        await queue.process(mock_send)
        assert queue.pending_count == 0

    @pytest.mark.asyncio
    async def test_process_failure_retries(self):
        queue = RetryQueue()
        queue.enqueue("+963944000000", "test", "whatsapp")

        call_count = 0

        async def mock_send(phone, text, platform):
            nonlocal call_count
            call_count += 1
            return False

        await queue.process(mock_send)
        assert call_count == 1
        assert queue.pending_count == 1  # Re-queued for retry

    def test_backoff_calculation(self):
        item = RetryItem(phone="x", text="y", platform="whatsapp", attempts=0)
        assert item.backoff_seconds == 2

        item.attempts = 1
        assert item.backoff_seconds == 4

        item.attempts = 2
        assert item.backoff_seconds == 8

    def test_max_attempts(self):
        item = RetryItem(phone="x", text="y", platform="whatsapp", attempts=4, max_attempts=4)
        assert item.should_retry is False


# --- Report Formatting Tests ---

class TestReportFormatting:
    def test_daily_report_format(self):
        report = {
            "date": "2026-04-02",
            "orders": {"total": 15, "revenue": 450000, "status_breakdown": {"completed": 12, "cancelled": 1}},
            "top_products": [{"name_ar": "شاورما", "quantity": 20, "revenue": 500000}],
            "new_customers": 3,
        }
        result = format_daily_report(report)
        assert "15" in result
        assert "450,000" in result
        assert "شاورما" in result

    def test_weekly_report_format(self):
        report = {
            "period": "2026-03-26 to 2026-04-02",
            "total_orders": 89,
            "total_revenue": 2500000,
            "avg_order_value": 28090,
            "best_day": {"date": "2026-03-30", "revenue": 500000},
            "daily_breakdown": [
                {"date": "2026-03-26", "orders": 10, "revenue": 300000},
            ],
        }
        result = format_weekly_report(report)
        assert "89" in result
        assert "2,500,000" in result

    def test_profit_loss_format(self):
        data = {
            "month": "2026-04",
            "revenue": 5000000,
            "expenses": 3000000,
            "profit": 2000000,
            "margin_pct": 40.0,
        }
        result = format_profit_loss(data)
        assert "الربح" in result
        assert "40" in result

    def test_loss_format(self):
        data = {
            "month": "2026-04",
            "revenue": 1000000,
            "expenses": 1500000,
            "profit": -500000,
            "margin_pct": -50.0,
        }
        result = format_profit_loss(data)
        assert "الخسارة" in result

    def test_rating_summary(self):
        rating = {"average": 4.5, "total_reviews": 50, "stars_display": "⭐⭐⭐⭐⭐"}
        result = format_rating_summary(rating)
        assert "4.5" in result
        assert "50" in result

    def test_loyalty_status(self):
        info = {
            "active": True,
            "program_name": "برنامج الولاء",
            "points": 250,
            "total_earned": 500,
            "total_redeemed": 250,
            "potential_discount": 25000,
            "min_redeem": 100,
            "can_redeem": True,
        }
        result = format_loyalty_status(info)
        assert "250" in result
        assert "استبدال" in result
