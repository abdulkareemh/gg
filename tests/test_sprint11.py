"""Tests for Sprint 11 — caching, smart responder, subscriptions, memory session."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.response_cache import (
    LRUCache, cached_intent, cache_intent,
    cached_response, cache_response, get_all_cache_stats,
)
from src.services.smart_responder import SmartResponder
from src.services.subscription_service import SubscriptionService, PLANS, get_plan_comparison, format_usage_warning
from src.services.memory_session import MemorySessionService
from src.services.notification_queue import NotificationQueue, Notification, NotificationType
from src.services.merchant_service import MerchantService


# --- LRU Cache ---

class TestLRUCache:
    def test_set_and_get(self):
        cache = LRUCache(max_size=100)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_miss(self):
        cache = LRUCache(max_size=100)
        assert cache.get("nonexistent") is None

    def test_max_size_eviction(self):
        cache = LRUCache(max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # Should evict "a"
        assert cache.get("a") is None
        assert cache.get("d") == 4

    def test_ttl_expiry(self):
        cache = LRUCache(max_size=100, default_ttl=0)  # Expire immediately
        cache.set("key", "value", ttl=0)
        import time
        time.sleep(0.01)
        assert cache.get("key") is None

    def test_hit_rate(self):
        cache = LRUCache(max_size=100)
        cache.set("key", "value")
        cache.get("key")  # hit
        cache.get("key")  # hit
        cache.get("miss")  # miss
        assert cache.hit_rate > 0.5

    def test_stats(self):
        cache = LRUCache(max_size=100)
        cache.set("key", "value")
        cache.get("key")
        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["hits"] == 1

    def test_delete(self):
        cache = LRUCache(max_size=100)
        cache.set("key", "value")
        assert cache.delete("key") is True
        assert cache.get("key") is None

    def test_clear(self):
        cache = LRUCache(max_size=100)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.size == 0


class TestCacheHelpers:
    def test_intent_cache(self):
        cache_intent("مرحبا", "greeting", 0.9)
        result = cached_intent("مرحبا")
        assert result == ("greeting", 0.9)

    def test_response_cache(self):
        cache_response(1, "ساعات العمل", "09:00 - 23:00")
        result = cached_response(1, "ساعات العمل")
        assert result == "09:00 - 23:00"

    def test_all_stats(self):
        stats = get_all_cache_stats()
        assert "intent_cache" in stats
        assert "response_cache" in stats
        assert "search_cache" in stats


# --- Smart Responder ---

class TestSmartResponder:
    def setup_method(self):
        self.responder = SmartResponder()
        self.ctx = {"id": 1, "business_name": "مطعم تست", "opening_time": "09:00", "closing_time": "23:00"}

    def test_greeting(self):
        resp, action, handled = self.responder.try_respond("مرحبا", self.ctx)
        assert handled is True
        assert action == "greeting"
        assert "مطعم تست" in resp

    def test_thank_you(self):
        resp, action, handled = self.responder.try_respond("شكرا", self.ctx)
        assert handled is True
        assert action == "thanks"

    def test_goodbye(self):
        resp, action, handled = self.responder.try_respond("مع السلامه", self.ctx)
        assert handled is True
        assert action == "goodbye"

    def test_faq_hours(self):
        resp, action, handled = self.responder.try_respond("ساعات العمل", self.ctx)
        assert handled is True
        assert "09:00" in resp

    def test_help(self):
        resp, action, handled = self.responder.try_respond("مساعدة", self.ctx)
        assert handled is True

    def test_menu_request(self):
        products = [{"name_ar": "شاورما", "price": 25000, "stock": 10, "category": "ساندويشات"}]
        resp, action, handled = self.responder.try_respond("القائمة", self.ctx, products=products)
        assert handled is True
        assert "شاورما" in resp

    def test_product_search(self):
        products = [{"name_ar": "شاورما دجاج", "name": "Shawarma", "price": 25000, "stock": 10}]
        resp, action, handled = self.responder.try_respond("شاورما", self.ctx, products=products)
        assert handled is True
        assert "25,000" in resp

    def test_unknown_falls_through(self):
        resp, action, handled = self.responder.try_respond("xyz random gibberish 123", self.ctx)
        assert handled is False


# --- Memory Session ---

class TestMemorySession:
    @pytest.mark.asyncio
    async def test_new_session(self):
        svc = MemorySessionService()
        session = await svc.get_session("+963944000000")
        assert session["state"] == "idle"
        assert session["cart"] == []

    @pytest.mark.asyncio
    async def test_save_and_retrieve(self):
        svc = MemorySessionService()
        session = await svc.get_session("+963944000001")
        session["state"] = "ordering"
        await svc.save_session("+963944000001", session)

        retrieved = await svc.get_session("+963944000001")
        assert retrieved["state"] == "ordering"

    @pytest.mark.asyncio
    async def test_add_to_cart(self):
        svc = MemorySessionService()
        session = await svc.add_to_cart("+963944000002", 1, "شاورما", 2, 25000)
        assert len(session["cart"]) == 1
        assert session["cart"][0]["total"] == 50000

    @pytest.mark.asyncio
    async def test_clear_cart(self):
        svc = MemorySessionService()
        await svc.add_to_cart("+963944000003", 1, "test", 1, 1000)
        session = await svc.clear_cart("+963944000003")
        assert session["cart"] == []

    @pytest.mark.asyncio
    async def test_history_limit(self):
        svc = MemorySessionService()
        session = await svc.get_session("+963944000004")
        session["history"] = [{"role": "user", "text": f"msg{i}"} for i in range(15)]
        await svc.save_session("+963944000004", session)
        retrieved = await svc.get_session("+963944000004")
        assert len(retrieved["history"]) == 10


# --- Subscription Service ---

class TestSubscriptionService:
    @pytest.mark.asyncio
    async def test_create_default_subscription(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963951001001", "m1", "test", "restaurant", "damascus")

        sub_svc = SubscriptionService(db_session)
        sub = await sub_svc.get_or_create(merchant.id)
        assert sub.plan == "free"

    @pytest.mark.asyncio
    async def test_upgrade_plan(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963951002001", "m1", "test", "restaurant", "damascus")

        sub_svc = SubscriptionService(db_session)
        result = await sub_svc.upgrade_plan(merchant.id, "pro")
        assert result["success"] is True
        assert result["plan"] == "pro"

    @pytest.mark.asyncio
    async def test_check_limit_free(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963951003001", "m1", "test", "restaurant", "damascus")

        sub_svc = SubscriptionService(db_session)
        check = await sub_svc.check_limit(merchant.id, "orders")
        assert check["allowed"] is True
        assert check["limit"] == 50  # Free plan

    @pytest.mark.asyncio
    async def test_increment_usage(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963951004001", "m1", "test", "restaurant", "damascus")

        sub_svc = SubscriptionService(db_session)
        await sub_svc.increment_usage(merchant.id, "orders", 5)
        check = await sub_svc.check_limit(merchant.id, "orders")
        assert check["used"] == 5

    @pytest.mark.asyncio
    async def test_usage_summary(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963951005001", "m1", "test", "shop", "aleppo")

        sub_svc = SubscriptionService(db_session)
        summary = await sub_svc.get_usage_summary(merchant.id)
        assert summary["plan"] == "free"
        assert summary["plan_name"] == "مجاني"
        assert "features" in summary

    @pytest.mark.asyncio
    async def test_start_trial(self, db_session: AsyncSession):
        m_svc = MerchantService(db_session)
        merchant = await m_svc.create("+963951006001", "m1", "test", "restaurant", "damascus")

        sub_svc = SubscriptionService(db_session)
        result = await sub_svc.start_trial(merchant.id, "pro", days=14)
        assert result["success"] is True
        assert "trial_ends" in result

    def test_plan_comparison(self):
        plans = get_plan_comparison()
        assert len(plans) == 4
        assert plans[0]["plan"] == "free"

    def test_usage_warning_high(self):
        msg = format_usage_warning("orders", 45, 50)
        assert "⚠️" in msg

    def test_usage_warning_ok(self):
        msg = format_usage_warning("orders", 10, 50)
        assert msg == ""


# --- Notification Queue ---

class TestNotificationQueue:
    @pytest.mark.asyncio
    async def test_enqueue(self):
        q = NotificationQueue()
        await q.enqueue_simple("+963944000000", "test message")
        assert q.pending == 1

    @pytest.mark.asyncio
    async def test_stats(self):
        q = NotificationQueue()
        stats = q.stats()
        assert "pending" in stats
        assert "sent" in stats
        assert "failed" in stats
