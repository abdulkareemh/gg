"""Tests for session service (mocked Redis)."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from src.services.session_service import SessionService


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def session_service(mock_redis):
    svc = SessionService()
    svc.redis = mock_redis
    return svc


class TestSessionService:
    @pytest.mark.asyncio
    async def test_get_empty_session(self, session_service):
        session = await session_service.get_session("+963944000000")
        assert session["state"] == "idle"
        assert session["cart"] == []
        assert session["history"] == []

    @pytest.mark.asyncio
    async def test_get_existing_session(self, session_service, mock_redis):
        stored = json.dumps({"phone": "+963944000000", "state": "ordering", "cart": [], "history": []})
        mock_redis.get.return_value = stored

        session = await session_service.get_session("+963944000000")
        assert session["state"] == "ordering"

    @pytest.mark.asyncio
    async def test_save_session(self, session_service, mock_redis):
        session = {"phone": "+963944000000", "state": "idle", "history": [], "cart": []}
        await session_service.save_session("+963944000000", session)
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_to_history(self, session_service):
        session = await session_service.add_to_history("+963944000000", "user", "مرحبا")
        assert len(session["history"]) == 1
        assert session["history"][0]["role"] == "user"
        assert session["history"][0]["text"] == "مرحبا"

    @pytest.mark.asyncio
    async def test_add_to_cart(self, session_service):
        session = await session_service.add_to_cart(
            "+963944000000", product_id=1, name_ar="شاورما", quantity=2, price=25000
        )
        assert len(session["cart"]) == 1
        assert session["cart"][0]["total"] == 50000

    @pytest.mark.asyncio
    async def test_add_to_cart_stacks(self, session_service, mock_redis):
        """Adding same product twice should stack quantity."""
        existing = json.dumps({
            "phone": "+963944000000",
            "state": "ordering",
            "cart": [{"product_id": 1, "name_ar": "شاورما", "quantity": 1, "price": 25000, "total": 25000}],
            "history": [],
        })
        mock_redis.get.return_value = existing

        session = await session_service.add_to_cart(
            "+963944000000", product_id=1, name_ar="شاورما", quantity=2, price=25000
        )
        assert session["cart"][0]["quantity"] == 3
        assert session["cart"][0]["total"] == 75000

    @pytest.mark.asyncio
    async def test_clear_cart(self, session_service, mock_redis):
        existing = json.dumps({
            "phone": "+963944000000",
            "state": "ordering",
            "cart": [{"product_id": 1, "name_ar": "شاورما", "quantity": 1, "price": 25000, "total": 25000}],
            "history": [],
        })
        mock_redis.get.return_value = existing

        session = await session_service.clear_cart("+963944000000")
        assert session["cart"] == []

    @pytest.mark.asyncio
    async def test_history_limit(self, session_service, mock_redis):
        """Session should cap history at 10 messages."""
        history = [{"role": "user", "text": f"msg {i}"} for i in range(15)]
        session = {
            "phone": "+963944000000",
            "state": "idle",
            "cart": [],
            "history": history,
        }
        await session_service.save_session("+963944000000", session)

        # Check the data that was saved
        saved_data = json.loads(mock_redis.set.call_args[0][1])
        assert len(saved_data["history"]) == 10
