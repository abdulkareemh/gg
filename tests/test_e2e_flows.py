"""End-to-end flow tests — simulate complete user journeys."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.merchant_service import MerchantService
from src.services.customer_service import CustomerService
from src.services.product_service import ProductService
from src.services.order_service import OrderService
from src.services.delivery_service import DeliveryService
from src.services.promotion_service import PromotionService, Promotion
from src.nlp.syrian_arabic import detect_intent, normalize_arabic
from src.nlp.fuzzy_search import fuzzy_match_product
from src.nlp.conversation import format_order_summary, format_product_menu
from src.services.diaspora_service import convert_to_syp, convert_from_syp


class TestFullOrderFlow:
    """Simulate: merchant signs up → adds products → customer orders → delivery."""

    @pytest.mark.asyncio
    async def test_complete_order_lifecycle(self, db_session: AsyncSession):
        # 1. Merchant registers
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963944800001",
            name="أبو خالد",
            business_name="شاورما أبو خالد",
            business_type="restaurant",
            city="دمشق",
        )
        assert merchant.plan == "free"

        # 2. Merchant adds products
        p_svc = ProductService(db_session)
        shawarma = await p_svc.create(merchant.id, "Shawarma", "شاورما دجاج", 25000, "ساندويشات", 50)
        falafel = await p_svc.create(merchant.id, "Falafel", "فلافل", 15000, "ساندويشات", 30)
        juice = await p_svc.create(merchant.id, "Juice", "عصير برتقال", 5000, "مشروبات", 100)

        # 3. Verify catalog
        catalog = await p_svc.get_catalog(merchant.id)
        assert len(catalog) == 3

        # 4. Customer messages "بدي اطلب"
        intent, confidence = detect_intent("بدي اطلب شاورما")
        assert intent == "new_order"
        assert confidence > 0

        # 5. Fuzzy search matches "شاورما"
        products_data = [{"name_ar": p.name_ar, "name": p.name, "price": float(p.price)} for p in catalog]
        matches = fuzzy_match_product("شاورما", products_data)
        assert len(matches) >= 1
        assert matches[0]["name_ar"] == "شاورما دجاج"

        # 6. Customer profile is created
        c_svc = CustomerService(db_session)
        customer, is_new = await c_svc.get_or_create(merchant.id, "+963955800001")
        assert is_new is True

        # 7. Order is created
        o_svc = OrderService(db_session)
        order = await o_svc.create_order(
            merchant_id=merchant.id,
            customer_id=customer.id,
            items=[
                {"product_id": shawarma.id, "quantity": 2},
                {"product_id": juice.id, "quantity": 1},
            ],
            notes="بدون بصل",
        )
        assert float(order.total_amount) == 55000
        assert order.status == "pending"

        # 8. Merchant confirms
        order = await o_svc.update_status(order.id, "confirmed")
        assert order.status == "confirmed"

        # 9. Order progresses
        order = await o_svc.update_status(order.id, "preparing")
        order = await o_svc.update_status(order.id, "ready")
        order = await o_svc.update_status(order.id, "delivered")
        order = await o_svc.update_status(order.id, "completed")
        assert order.status == "completed"

        # 10. Customer order count incremented
        await c_svc.increment_orders(customer.id)
        updated_customer, _ = await c_svc.get_or_create(merchant.id, "+963955800001")
        assert updated_customer.total_orders == 1

        # 11. Stock decreased
        updated_catalog = await p_svc.get_catalog(merchant.id)
        shawarma_updated = next(p for p in updated_catalog if p.name == "Shawarma")
        assert shawarma_updated.stock_quantity == 48  # 50 - 2

        # 12. Daily summary
        summary = await o_svc.get_daily_summary(merchant.id)
        assert summary["order_count"] == 1
        assert summary["total_revenue"] == 55000


class TestNLPPipeline:
    """Test the full NLP pipeline with various Syrian Arabic inputs."""

    def test_various_greetings(self):
        greetings = ["مرحبا", "هلا", "أهلا", "السلام عليكم", "صباح الخير", "hi", "hello"]
        for g in greetings:
            intent, _ = detect_intent(g)
            assert intent == "greeting", f"Failed for: {g}"

    def test_various_order_intents(self):
        orders = ["بدي اطلب", "بدي طلب", "طلبية جديدة", "بدي اشتري", "order"]
        for o in orders:
            intent, _ = detect_intent(o)
            assert intent == "new_order", f"Failed for: {o}"

    def test_order_tracking(self):
        queries = ["وين طلبيتي", "شو صار بالطلب", "جاهز"]
        for q in queries:
            intent, _ = detect_intent(q)
            assert intent == "check_order", f"Failed for: {q}"

    def test_normalization_consistency(self):
        # These should normalize to the same text
        v1 = normalize_arabic("أهلاً وسهلاً")
        v2 = normalize_arabic("اهلا وسهلا")
        assert v1 == v2

    def test_product_menu_formatting(self):
        products = [
            {"name_ar": "شاورما", "price": 25000, "stock": 10, "category": "ساندويشات"},
            {"name_ar": "عصير", "price": 5000, "stock": 0, "category": "مشروبات"},
        ]
        menu = format_product_menu(products)
        assert "شاورما" in menu
        assert "✅" in menu  # In stock
        assert "❌" in menu  # Out of stock

    def test_order_summary_formatting(self):
        items = [
            {"name_ar": "شاورما", "quantity": 2, "price": 25000},
            {"name_ar": "عصير", "quantity": 1, "price": 5000},
        ]
        summary = format_order_summary(items)
        assert "55,000" in summary


class TestCurrencyFlow:
    """Test diaspora currency conversion end-to-end."""

    def test_round_trip_conversion(self):
        """USD → SYP → USD should return roughly the same amount."""
        original = 100.0
        syp = convert_to_syp(original, "USD")
        back = convert_from_syp(syp, "USD")
        assert abs(back - original) < 0.01

    def test_multi_currency_pricing(self):
        """A product priced in SYP should show correct foreign prices."""
        syp_price = 145000  # ~$10

        usd = convert_from_syp(syp_price, "USD")
        eur = convert_from_syp(syp_price, "EUR")
        try_val = convert_from_syp(syp_price, "TRY")

        assert usd is not None
        assert eur is not None
        assert try_val is not None
        assert usd < eur  # EUR is worth more
        assert try_val > usd  # TRY is worth less


class TestPromotionTargeting:
    @pytest.mark.asyncio
    async def test_target_all_customers(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963946010001", "m1", "test", "restaurant", "دمشق")

        c_svc = CustomerService(db_session)
        await c_svc.get_or_create(merchant.id, "+963955010001")
        await c_svc.get_or_create(merchant.id, "+963955010002")

        promo_svc = PromotionService(db_session)
        promo = Promotion(
            merchant_id=merchant.id,
            title="عرض",
            message="خصم 20%",
            target="all",
        )
        customers = await promo_svc.get_target_customers(promo)
        assert len(customers) == 2

    @pytest.mark.asyncio
    async def test_promo_stats(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963946011001", "m1", "test", "shop", "حلب")

        c_svc = CustomerService(db_session)
        await c_svc.get_or_create(merchant.id, "+963955011001")

        promo_svc = PromotionService(db_session)
        stats = await promo_svc.get_promotion_stats(merchant.id)
        assert stats["segments"]["all"]["count"] == 1
