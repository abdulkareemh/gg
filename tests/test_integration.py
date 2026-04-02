"""Integration tests using a real SQLite database."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.merchant_service import MerchantService
from src.services.customer_service import CustomerService
from src.services.product_service import ProductService
from src.services.order_service import OrderService


class TestMerchantServiceIntegration:
    @pytest.mark.asyncio
    async def test_create_merchant(self, db_session: AsyncSession):
        svc = MerchantService(db_session)
        merchant = await svc.create(
            phone="+963944111111",
            name="أحمد",
            business_name="مطعم الشام",
            business_type="restaurant",
            city="دمشق",
        )
        assert merchant.id is not None
        assert merchant.name == "أحمد"
        assert merchant.plan == "free"

    @pytest.mark.asyncio
    async def test_get_by_phone(self, db_session: AsyncSession):
        svc = MerchantService(db_session)
        await svc.create(
            phone="+963944222222",
            name="سارة",
            business_name="بوتيك سارة",
            business_type="shop",
            city="حلب",
        )
        found = await svc.get_by_phone("+963944222222")
        assert found is not None
        assert found.business_name == "بوتيك سارة"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, db_session: AsyncSession):
        svc = MerchantService(db_session)
        found = await svc.get_by_phone("+963999999999")
        assert found is None

    @pytest.mark.asyncio
    async def test_update_plan(self, db_session: AsyncSession):
        svc = MerchantService(db_session)
        merchant = await svc.create(
            phone="+963944333333",
            name="خالد",
            business_name="خالد للإلكترونيات",
            business_type="shop",
            city="حمص",
        )
        updated = await svc.update_plan(merchant.id, "pro")
        assert updated.plan == "pro"


class TestCustomerServiceIntegration:
    @pytest.mark.asyncio
    async def test_get_or_create_new(self, db_session: AsyncSession):
        # Create a merchant first
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963944444444",
            name="merchant",
            business_name="test shop",
            business_type="shop",
            city="damascus",
        )

        c_svc = CustomerService(db_session)
        customer, is_new = await c_svc.get_or_create(merchant.id, "+963955111111")
        assert is_new is True
        assert customer.merchant_id == merchant.id

    @pytest.mark.asyncio
    async def test_get_or_create_existing(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963944555555",
            name="merchant2",
            business_name="test2",
            business_type="shop",
            city="aleppo",
        )

        c_svc = CustomerService(db_session)
        customer1, is_new1 = await c_svc.get_or_create(merchant.id, "+963955222222")
        customer2, is_new2 = await c_svc.get_or_create(merchant.id, "+963955222222")

        assert is_new1 is True
        assert is_new2 is False
        assert customer1.id == customer2.id

    @pytest.mark.asyncio
    async def test_increment_orders(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963944666666",
            name="m3",
            business_name="t3",
            business_type="shop",
            city="homs",
        )

        c_svc = CustomerService(db_session)
        customer, _ = await c_svc.get_or_create(merchant.id, "+963955333333")
        assert customer.total_orders == 0

        await c_svc.increment_orders(customer.id)
        await c_svc.increment_orders(customer.id)

        # Re-fetch
        updated, _ = await c_svc.get_or_create(merchant.id, "+963955333333")
        assert updated.total_orders == 2


class TestProductServiceIntegration:
    @pytest.mark.asyncio
    async def test_create_product(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963944777777",
            name="m4",
            business_name="مطعم تست",
            business_type="restaurant",
            city="damascus",
        )

        p_svc = ProductService(db_session)
        product = await p_svc.create(
            merchant_id=merchant.id,
            name="Shawarma",
            name_ar="شاورما",
            price=25000,
            category="ساندويشات",
            stock_quantity=50,
        )
        assert product.id is not None
        assert product.name_ar == "شاورما"
        assert float(product.price) == 25000

    @pytest.mark.asyncio
    async def test_get_catalog(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963944888888",
            name="m5",
            business_name="test5",
            business_type="restaurant",
            city="damascus",
        )

        p_svc = ProductService(db_session)
        await p_svc.create(merchant.id, "Shawarma", "شاورما", 25000, "ساندويشات", 50)
        await p_svc.create(merchant.id, "Falafel", "فلافل", 15000, "ساندويشات", 30)
        await p_svc.create(merchant.id, "Juice", "عصير", 5000, "مشروبات", 100)

        catalog = await p_svc.get_catalog(merchant.id)
        assert len(catalog) == 3

        # Filter by category
        sandwiches = await p_svc.get_catalog(merchant.id, category="ساندويشات")
        assert len(sandwiches) == 2

    @pytest.mark.asyncio
    async def test_search(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963944999999",
            name="m6",
            business_name="test6",
            business_type="restaurant",
            city="damascus",
        )

        p_svc = ProductService(db_session)
        await p_svc.create(merchant.id, "Shawarma", "شاورما دجاج", 25000)
        await p_svc.create(merchant.id, "Falafel", "فلافل", 15000)

        results = await p_svc.search(merchant.id, "شاورما")
        assert len(results) == 1
        assert results[0].name_ar == "شاورما دجاج"

    @pytest.mark.asyncio
    async def test_bulk_create(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963945111111",
            name="m7",
            business_name="test7",
            business_type="restaurant",
            city="damascus",
        )

        p_svc = ProductService(db_session)
        products = await p_svc.bulk_create_from_list(merchant.id, [
            {"name": "Shawarma", "name_ar": "شاورما", "price": 25000},
            {"name": "Falafel", "name_ar": "فلافل", "price": 15000},
            {"name": "Hummus", "name_ar": "حمص", "price": 10000},
        ])
        assert len(products) == 3

    @pytest.mark.asyncio
    async def test_low_stock(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963945222222",
            name="m8",
            business_name="test8",
            business_type="shop",
            city="damascus",
        )

        p_svc = ProductService(db_session)
        await p_svc.create(merchant.id, "Item A", "صنف أ", 1000, stock_quantity=3)  # Low
        await p_svc.create(merchant.id, "Item B", "صنف ب", 2000, stock_quantity=50)  # OK

        low = await p_svc.get_low_stock(merchant.id)
        assert len(low) == 1
        assert low[0].name_ar == "صنف أ"


class TestOrderServiceIntegration:
    @pytest.mark.asyncio
    async def test_create_order(self, db_session: AsyncSession):
        # Setup: merchant, customer, products
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963945333333",
            name="m9",
            business_name="test9",
            business_type="restaurant",
            city="damascus",
        )

        c_svc = CustomerService(db_session)
        customer, _ = await c_svc.get_or_create(merchant.id, "+963955444444")

        p_svc = ProductService(db_session)
        p1 = await p_svc.create(merchant.id, "Shawarma", "شاورما", 25000, stock_quantity=10)
        p2 = await p_svc.create(merchant.id, "Juice", "عصير", 5000, stock_quantity=20)

        # Create order
        o_svc = OrderService(db_session)
        order = await o_svc.create_order(
            merchant_id=merchant.id,
            customer_id=customer.id,
            items=[
                {"product_id": p1.id, "quantity": 2},
                {"product_id": p2.id, "quantity": 1},
            ],
            notes="بدون بصل",
        )

        assert order.id is not None
        assert float(order.total_amount) == 55000  # 2*25000 + 1*5000
        assert order.status == "pending"
        assert order.notes == "بدون بصل"

    @pytest.mark.asyncio
    async def test_update_order_status(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963945444444",
            name="m10",
            business_name="test10",
            business_type="restaurant",
            city="damascus",
        )

        c_svc = CustomerService(db_session)
        customer, _ = await c_svc.get_or_create(merchant.id, "+963955555555")

        p_svc = ProductService(db_session)
        product = await p_svc.create(merchant.id, "Item", "صنف", 10000, stock_quantity=5)

        o_svc = OrderService(db_session)
        order = await o_svc.create_order(
            merchant_id=merchant.id,
            customer_id=customer.id,
            items=[{"product_id": product.id, "quantity": 1}],
        )

        # Walk through statuses
        for status in ["confirmed", "preparing", "ready", "delivered", "completed"]:
            updated = await o_svc.update_status(order.id, status)
            assert updated.status == status

    @pytest.mark.asyncio
    async def test_daily_summary(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963945555555",
            name="m11",
            business_name="test11",
            business_type="restaurant",
            city="damascus",
        )

        c_svc = CustomerService(db_session)
        customer, _ = await c_svc.get_or_create(merchant.id, "+963955666666")

        p_svc = ProductService(db_session)
        product = await p_svc.create(merchant.id, "Item", "صنف", 10000, stock_quantity=100)

        o_svc = OrderService(db_session)
        await o_svc.create_order(
            merchant_id=merchant.id,
            customer_id=customer.id,
            items=[{"product_id": product.id, "quantity": 3}],
        )

        summary = await o_svc.get_daily_summary(merchant.id)
        assert summary["order_count"] == 1
        assert summary["total_revenue"] == 30000
