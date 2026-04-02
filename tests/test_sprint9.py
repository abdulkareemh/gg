"""Tests for Sprint 9 — order modification, auto-reply, merchant comparison."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.merchant_service import MerchantService
from src.services.customer_service import CustomerService
from src.services.product_service import ProductService
from src.services.order_service import OrderService
from src.services.order_modification_service import OrderModificationService
from src.services.auto_reply import get_auto_reply, get_faq_list
from src.services.merchant_comparison import format_comparison


class TestOrderModification:
    @pytest.mark.asyncio
    async def test_add_item_to_order(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963950001001", "m1", "test", "restaurant", "damascus")

        c_svc = CustomerService(db_session)
        customer, _ = await c_svc.get_or_create(merchant.id, "+963958001001")

        p_svc = ProductService(db_session)
        p1 = await p_svc.create(merchant.id, "Shawarma", "شاورما", 25000, stock_quantity=50)
        p2 = await p_svc.create(merchant.id, "Juice", "عصير", 5000, stock_quantity=100)

        o_svc = OrderService(db_session)
        order = await o_svc.create_order(merchant.id, customer.id, [{"product_id": p1.id, "quantity": 1}])
        assert float(order.total_amount) == 25000

        mod_svc = OrderModificationService(db_session)
        result = await mod_svc.add_item(order.id, p2.id, 2)
        assert result["success"] is True
        assert result["new_total"] == 35000  # 25000 + 2*5000

    @pytest.mark.asyncio
    async def test_remove_item_from_order(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963950002001", "m1", "test", "restaurant", "damascus")

        c_svc = CustomerService(db_session)
        customer, _ = await c_svc.get_or_create(merchant.id, "+963958002001")

        p_svc = ProductService(db_session)
        p1 = await p_svc.create(merchant.id, "A", "صنف أ", 10000, stock_quantity=50)
        p2 = await p_svc.create(merchant.id, "B", "صنف ب", 20000, stock_quantity=50)

        o_svc = OrderService(db_session)
        order = await o_svc.create_order(
            merchant.id, customer.id,
            [{"product_id": p1.id, "quantity": 1}, {"product_id": p2.id, "quantity": 1}]
        )
        assert float(order.total_amount) == 30000

        mod_svc = OrderModificationService(db_session)
        result = await mod_svc.remove_item(order.id, p2.id)
        assert result["success"] is True
        assert result["new_total"] == 10000

    @pytest.mark.asyncio
    async def test_change_quantity(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963950003001", "m1", "test", "restaurant", "damascus")

        c_svc = CustomerService(db_session)
        customer, _ = await c_svc.get_or_create(merchant.id, "+963958003001")

        p_svc = ProductService(db_session)
        product = await p_svc.create(merchant.id, "Item", "صنف", 10000, stock_quantity=50)

        o_svc = OrderService(db_session)
        order = await o_svc.create_order(merchant.id, customer.id, [{"product_id": product.id, "quantity": 2}])
        assert float(order.total_amount) == 20000

        mod_svc = OrderModificationService(db_session)
        result = await mod_svc.change_quantity(order.id, product.id, 5)
        assert result["success"] is True
        assert result["new_total"] == 50000

    @pytest.mark.asyncio
    async def test_cannot_modify_preparing_order(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963950004001", "m1", "test", "restaurant", "damascus")

        c_svc = CustomerService(db_session)
        customer, _ = await c_svc.get_or_create(merchant.id, "+963958004001")

        p_svc = ProductService(db_session)
        product = await p_svc.create(merchant.id, "Item", "صنف", 10000, stock_quantity=50)

        o_svc = OrderService(db_session)
        order = await o_svc.create_order(merchant.id, customer.id, [{"product_id": product.id, "quantity": 1}])
        await o_svc.update_status(order.id, "preparing")

        mod_svc = OrderModificationService(db_session)
        result = await mod_svc.add_item(order.id, product.id, 1)
        assert result["success"] is False


class TestAutoReply:
    def test_match_hours(self):
        ctx = {"opening_time": "09:00", "closing_time": "23:00", "closed_days": "الجمعة"}
        reply = get_auto_reply("ساعات العمل", ctx)
        assert reply is not None
        assert "09:00" in reply

    def test_match_delivery(self):
        reply = get_auto_reply("في توصيل", {})
        assert reply is not None
        assert "توصيل" in reply

    def test_match_payment(self):
        reply = get_auto_reply("كيف بدفع", {})
        assert reply is not None
        assert "كاش" in reply

    def test_match_english(self):
        reply = get_auto_reply("do you deliver?", {})
        assert reply is not None

    def test_no_match(self):
        reply = get_auto_reply("xyz random text", {})
        assert reply is None

    def test_faq_list(self):
        faq = get_faq_list()
        assert "ساعات العمل" in faq
        assert "التوصيل" in faq


class TestMerchantComparison:
    def test_format_empty(self):
        assert "ما لقيت" in format_comparison([])

    def test_format_merchants(self):
        data = [
            {
                "business_name": "مطعم الشام",
                "city": "دمشق",
                "rating": 4.5,
                "review_count": 50,
                "products": 15,
                "avg_price": 25000,
            }
        ]
        result = format_comparison(data)
        assert "مطعم الشام" in result
        assert "دمشق" in result
        assert "⭐" in result
