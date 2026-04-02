"""Tests for marketplace, recommendations, and delivery."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.merchant_service import MerchantService
from src.services.product_service import ProductService
from src.services.customer_service import CustomerService
from src.services.order_service import OrderService
from src.services.marketplace_service import MarketplaceService, format_merchant_list
from src.services.recommendation_service import RecommendationService, format_recommendations
from src.services.delivery_service import DeliveryService, format_delivery_zones
from src.services.branch_service import BranchService, format_branches


class TestMarketplaceService:
    @pytest.mark.asyncio
    async def test_search_by_city(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        await m_svc.create("+963946001001", "m1", "مطعم أ", "restaurant", "دمشق")
        await m_svc.create("+963946001002", "m2", "مطعم ب", "restaurant", "حلب")

        mp_svc = MarketplaceService(db_session)
        results = await mp_svc.search_merchants(city="دمشق")
        assert len(results) == 1
        assert results[0]["city"] == "دمشق"

    @pytest.mark.asyncio
    async def test_search_by_type(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        await m_svc.create("+963946002001", "m1", "مطعم", "restaurant", "دمشق")
        await m_svc.create("+963946002002", "m2", "محل", "shop", "دمشق")

        mp_svc = MarketplaceService(db_session)
        results = await mp_svc.search_merchants(business_type="restaurant")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_by_name(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        await m_svc.create("+963946003001", "m1", "مطعم الشام", "restaurant", "دمشق")
        await m_svc.create("+963946003002", "m2", "بوتيك سارة", "shop", "دمشق")

        mp_svc = MarketplaceService(db_session)
        results = await mp_svc.search_merchants(query="شام")
        assert len(results) == 1
        assert "الشام" in results[0]["business_name"]

    @pytest.mark.asyncio
    async def test_get_cities(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        await m_svc.create("+963946004001", "m1", "a", "restaurant", "دمشق")
        await m_svc.create("+963946004002", "m2", "b", "restaurant", "دمشق")
        await m_svc.create("+963946004003", "m3", "c", "shop", "حلب")

        mp_svc = MarketplaceService(db_session)
        cities = await mp_svc.get_cities()
        assert len(cities) == 2
        assert cities[0]["city"] == "دمشق"  # More merchants
        assert cities[0]["merchants"] == 2

    def test_format_merchant_list_empty(self):
        assert "ما لقيت" in format_merchant_list([])

    def test_format_merchant_list(self):
        merchants = [
            {"business_name": "مطعم الشام", "business_type": "restaurant", "city": "دمشق"},
        ]
        result = format_merchant_list(merchants)
        assert "مطعم الشام" in result
        assert "🍽️" in result


class TestRecommendationService:
    @pytest.mark.asyncio
    async def test_basic_recommendations(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963946005001", "m1", "test", "restaurant", "دمشق")

        p_svc = ProductService(db_session)
        await p_svc.create(merchant.id, "Shawarma", "شاورما", 25000, "ساندويشات", 50)
        await p_svc.create(merchant.id, "Juice", "عصير", 5000, "مشروبات", 100)

        rec_svc = RecommendationService(db_session)
        recs = await rec_svc.get_recommendations(merchant.id, limit=5)
        assert len(recs) >= 1

    @pytest.mark.asyncio
    async def test_no_out_of_stock(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963946006001", "m1", "test", "restaurant", "دمشق")

        p_svc = ProductService(db_session)
        await p_svc.create(merchant.id, "In Stock", "متوفر", 25000, stock_quantity=10)
        await p_svc.create(merchant.id, "Out", "خلصان", 5000, stock_quantity=0)

        rec_svc = RecommendationService(db_session)
        recs = await rec_svc.get_recommendations(merchant.id)
        names = [r["name_ar"] for r in recs]
        assert "متوفر" in names
        assert "خلصان" not in names

    def test_format_recommendations_empty(self):
        assert "ما عندي" in format_recommendations([])

    def test_format_recommendations(self):
        recs = [{"name_ar": "شاورما", "price": 25000, "reason": "الأكثر طلباً"}]
        result = format_recommendations(recs)
        assert "شاورما" in result
        assert "25,000" in result


class TestBranchService:
    @pytest.mark.asyncio
    async def test_create_and_list_branches(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963946007001", "m1", "chain", "restaurant", "دمشق")

        b_svc = BranchService(db_session)
        await b_svc.create_branch(merchant.id, "فرع المزة", "دمشق", is_main=True)
        await b_svc.create_branch(merchant.id, "فرع حلب", "حلب")

        branches = await b_svc.get_branches(merchant.id)
        assert len(branches) == 2
        # Main branch should be first
        assert branches[0].is_main is True

    def test_format_branches(self):
        from src.models.branch import Branch
        branches = [
            Branch(id=1, merchant_id=1, name="فرع المزة", city="دمشق", is_main=True, opening_hours="9:00-23:00"),
        ]
        result = format_branches(branches)
        assert "فرع المزة" in result
        assert "الرئيسي" in result
