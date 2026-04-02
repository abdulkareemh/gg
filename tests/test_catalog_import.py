"""Tests for CSV catalog import."""

import pytest

from src.services.catalog_import import import_catalog_from_csv, format_import_result, ImportResult
from src.services.product_service import ProductService
from src.services.merchant_service import MerchantService


class TestCSVParsing:
    @pytest.mark.asyncio
    async def test_valid_csv(self, db_session):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963945900001",
            name="test",
            business_name="test",
            business_type="restaurant",
            city="damascus",
        )
        p_svc = ProductService(db_session)

        csv = "name_ar,name,price,category,stock\nشاورما,Shawarma,25000,ساندويشات,50\nفلافل,Falafel,15000,ساندويشات,30"
        result = await import_catalog_from_csv(csv, merchant.id, p_svc)

        assert result.success is True
        assert result.imported == 2
        assert result.skipped == 0

    @pytest.mark.asyncio
    async def test_missing_price(self, db_session):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963945900002",
            name="test",
            business_name="test",
            business_type="shop",
            city="aleppo",
        )
        p_svc = ProductService(db_session)

        csv = "name_ar,price\nشاورما,25000\nفلافل,"
        result = await import_catalog_from_csv(csv, merchant.id, p_svc)

        assert result.imported == 1
        assert result.skipped == 1
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_arabic_headers(self, db_session):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963945900003",
            name="test",
            business_name="test",
            business_type="shop",
            city="homs",
        )
        p_svc = ProductService(db_session)

        csv = "الاسم,السعر,التصنيف\nشاورما,25000,ساندويشات"
        result = await import_catalog_from_csv(csv, merchant.id, p_svc)

        assert result.success is True
        assert result.imported == 1

    @pytest.mark.asyncio
    async def test_empty_csv(self, db_session):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create(
            phone="+963945900004",
            name="test",
            business_name="test",
            business_type="shop",
            city="latakia",
        )
        p_svc = ProductService(db_session)

        csv = "name_ar,price"
        result = await import_catalog_from_csv(csv, merchant.id, p_svc)

        assert result.success is False
        assert result.imported == 0


class TestFormatImportResult:
    def test_success_message(self):
        result = ImportResult(success=True, imported=5, skipped=0, errors=[])
        msg = format_import_result(result)
        assert "5" in msg
        assert "✅" in msg

    def test_partial_success(self):
        result = ImportResult(success=True, imported=3, skipped=2, errors=["Row 4: missing price"])
        msg = format_import_result(result)
        assert "3" in msg
        assert "2" in msg
        assert "⚠️" in msg

    def test_failure_message(self):
        result = ImportResult(success=False, imported=0, skipped=0, errors=["Invalid CSV"])
        msg = format_import_result(result)
        assert "❌" in msg
