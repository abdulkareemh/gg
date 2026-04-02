"""Tests for Sprint 7 features — coupons, receipts, templates, reservations, exports."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.merchant_service import MerchantService
from src.services.customer_service import CustomerService
from src.services.product_service import ProductService
from src.services.coupon_service import CouponService, generate_code, format_coupon_list
from src.services.reservation_service import ReservationService, format_reservations, format_waitlist
from src.services.settings_service import SettingsService
from src.services.export_service import ExportService
from src.services.audit_service import AuditService
from src.nlp.templates import get_template, get_available_languages
from src.utils.receipt import generate_receipt, generate_simple_receipt


# --- Coupon Tests ---

class TestCouponService:
    @pytest.mark.asyncio
    async def test_create_percentage_coupon(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963948001001", "m1", "test", "restaurant", "damascus")

        coupon_svc = CouponService(db_session)
        coupon = await coupon_svc.create_coupon(
            merchant.id, "percentage", 20, code="WELCOME20", max_discount=50000
        )
        assert coupon.code == "WELCOME20"
        assert float(coupon.discount_value) == 20

    @pytest.mark.asyncio
    async def test_validate_percentage(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963948002001", "m1", "test", "restaurant", "damascus")

        coupon_svc = CouponService(db_session)
        await coupon_svc.create_coupon(merchant.id, "percentage", 10, code="SAVE10")

        result = await coupon_svc.validate_coupon("SAVE10", merchant.id, 100000)
        assert result["valid"] is True
        assert result["discount"] == 10000  # 10% of 100,000
        assert result["new_total"] == 90000

    @pytest.mark.asyncio
    async def test_validate_fixed_discount(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963948003001", "m1", "test", "restaurant", "damascus")

        coupon_svc = CouponService(db_session)
        await coupon_svc.create_coupon(merchant.id, "fixed", 15000, code="FLAT15K")

        result = await coupon_svc.validate_coupon("FLAT15K", merchant.id, 50000)
        assert result["valid"] is True
        assert result["discount"] == 15000
        assert result["new_total"] == 35000

    @pytest.mark.asyncio
    async def test_validate_invalid_code(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963948004001", "m1", "test", "shop", "aleppo")

        coupon_svc = CouponService(db_session)
        result = await coupon_svc.validate_coupon("FAKE", merchant.id, 50000)
        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_max_discount_cap(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963948005001", "m1", "test", "restaurant", "damascus")

        coupon_svc = CouponService(db_session)
        await coupon_svc.create_coupon(
            merchant.id, "percentage", 50, code="BIG50", max_discount=20000
        )

        result = await coupon_svc.validate_coupon("BIG50", merchant.id, 100000)
        assert result["discount"] == 20000  # Capped at max_discount

    def test_generate_code(self):
        code = generate_code()
        assert code.startswith("NOOR-")
        assert len(code) == 13


# --- Template Tests ---

class TestTemplates:
    def test_syrian_arabic(self):
        text = get_template("welcome", "ar-SY")
        assert "نور" in text

    def test_english(self):
        text = get_template("welcome", "en")
        assert "Noor" in text

    def test_with_variables(self):
        text = get_template("order_confirmed", "ar-SY", order_id=42, total="55,000")
        assert "42" in text
        assert "55,000" in text

    def test_fallback_to_syrian(self):
        text = get_template("welcome", "unknown_lang")
        # Should fall back to ar-SY
        assert text == "" or "نور" in text

    def test_available_languages(self):
        langs = get_available_languages()
        assert len(langs) == 3
        codes = [l["code"] for l in langs]
        assert "ar-SY" in codes
        assert "en" in codes


# --- Receipt Tests ---

class TestReceiptGenerator:
    def test_full_receipt(self):
        receipt = generate_receipt(
            merchant_name="مطعم الشام",
            order_id=42,
            items=[
                {"name_ar": "شاورما", "quantity": 2, "total": 50000},
                {"name_ar": "عصير", "quantity": 1, "total": 5000},
            ],
            subtotal=55000,
            delivery_fee=10000,
            discount=5000,
            payment_method="syriatel_cash",
            customer_name="محمد",
        )
        assert "مطعم الشام" in receipt
        assert "#42" in receipt
        assert "محمد" in receipt
        assert "شاورما" in receipt
        assert "60,000" in receipt  # 55000 + 10000 - 5000
        assert "سيرياتيل كاش" in receipt

    def test_simple_receipt(self):
        receipt = generate_simple_receipt(
            order_id=42,
            items=[{"name_ar": "شاورما", "quantity": 2, "price": 25000}],
            total=50000,
        )
        assert "#42" in receipt
        assert "شاورما" in receipt
        assert "50,000" in receipt


# --- Reservation Tests ---

class TestReservationService:
    @pytest.mark.asyncio
    async def test_create_reservation(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963948006001", "m1", "test", "restaurant", "damascus")

        res_svc = ReservationService(db_session)
        future = datetime.utcnow() + timedelta(hours=3)
        reservation = await res_svc.create_reservation(
            merchant.id, "+963955100001", future, party_size=4, customer_name="أحمد"
        )
        assert reservation.party_size == 4
        assert reservation.status == "pending"

    @pytest.mark.asyncio
    async def test_waitlist(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963948007001", "m1", "test", "restaurant", "damascus")

        res_svc = ReservationService(db_session)
        await res_svc.add_to_waitlist(merchant.id, "+963955200001", 2, "سارة")
        await res_svc.add_to_waitlist(merchant.id, "+963955200002", 3, "خالد")

        waitlist = await res_svc.get_waitlist(merchant.id)
        assert len(waitlist) == 2

    def test_format_empty_reservations(self):
        assert "ما في" in format_reservations([])

    def test_format_empty_waitlist(self):
        assert "فاضية" in format_waitlist([])


# --- Settings Tests ---

class TestSettingsService:
    @pytest.mark.asyncio
    async def test_get_or_create(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963948008001", "m1", "test", "restaurant", "damascus")

        svc = SettingsService(db_session)
        settings = await svc.get_or_create(merchant.id)
        assert settings.notify_new_orders is True
        assert settings.opening_time == "09:00"

    @pytest.mark.asyncio
    async def test_update_settings(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963948009001", "m1", "test", "restaurant", "damascus")

        svc = SettingsService(db_session)
        settings = await svc.update(merchant.id, auto_confirm_orders=True, closing_time="22:00")
        assert settings.auto_confirm_orders is True
        assert settings.closing_time == "22:00"


# --- Export Tests ---

class TestExportService:
    @pytest.mark.asyncio
    async def test_export_products_csv(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963948010001", "m1", "test", "restaurant", "damascus")

        p_svc = ProductService(db_session)
        await p_svc.create(merchant.id, "Shawarma", "شاورما", 25000, "ساندويشات", 50)

        export_svc = ExportService(db_session)
        csv_str = await export_svc.export_products_csv(merchant.id)
        assert "شاورما" in csv_str
        assert "25000" in csv_str

    @pytest.mark.asyncio
    async def test_export_customers_csv(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963948011001", "m1", "test", "shop", "aleppo")

        c_svc = CustomerService(db_session)
        await c_svc.get_or_create(merchant.id, "+963955300001")

        export_svc = ExportService(db_session)
        csv_str = await export_svc.export_customers_csv(merchant.id)
        assert "+963955300001" in csv_str


# --- Audit Tests ---

class TestAuditService:
    @pytest.mark.asyncio
    async def test_log_event(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963948012001", "m1", "test", "restaurant", "damascus")

        audit = AuditService(db_session)
        entry = await audit.log(
            "order_created", "+963955400001", "New order #42",
            merchant_id=merchant.id, metadata={"order_id": 42}, platform="whatsapp"
        )
        assert entry.event_type == "order_created"

    @pytest.mark.asyncio
    async def test_get_recent(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963948013001", "m1", "test", "shop", "homs")

        audit = AuditService(db_session)
        await audit.log("message_in", "phone1", "msg1", merchant_id=merchant.id)
        await audit.log("order_created", "phone2", "msg2", merchant_id=merchant.id)

        recent = await audit.get_recent(merchant.id)
        assert len(recent) == 2

    @pytest.mark.asyncio
    async def test_event_counts(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963948014001", "m1", "test", "restaurant", "damascus")

        audit = AuditService(db_session)
        await audit.log("message_in", "p1", "m1", merchant_id=merchant.id)
        await audit.log("message_in", "p2", "m2", merchant_id=merchant.id)
        await audit.log("order_created", "p3", "m3", merchant_id=merchant.id)

        counts = await audit.get_event_counts(merchant.id)
        assert counts.get("message_in") == 2
        assert counts.get("order_created") == 1
