"""Tests for middleware components."""

from src.api.middleware import RateLimiter, verify_whatsapp_signature
from src.integrations.payments import PaymentGateway


class TestRateLimiter:
    def test_allows_within_limit(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert limiter.is_allowed("test_key") is True

    def test_blocks_over_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.is_allowed("test_key")
        assert limiter.is_allowed("test_key") is False

    def test_separate_keys(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.is_allowed("key_a")
        limiter.is_allowed("key_a")
        # key_a exhausted, but key_b should work
        assert limiter.is_allowed("key_a") is False
        assert limiter.is_allowed("key_b") is True

    def test_remaining_count(self):
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        limiter.is_allowed("key")
        limiter.is_allowed("key")
        assert limiter.remaining("key") == 8


class TestWhatsAppSignature:
    def test_valid_signature(self):
        import hashlib
        import hmac

        secret = "test_secret"
        payload = b'{"test": "data"}'
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        signature = f"sha256={expected}"

        assert verify_whatsapp_signature(payload, signature, secret) is True

    def test_invalid_signature(self):
        assert verify_whatsapp_signature(b"data", "sha256=invalid", "secret") is False


class TestPaymentGatewayDetection:
    def test_detect_syriatel(self):
        gw = PaymentGateway()
        assert gw.detect_provider("0944123456") == "syriatel_cash"
        assert gw.detect_provider("+963944123456") == "syriatel_cash"
        assert gw.detect_provider("0935123456") == "syriatel_cash"

    def test_detect_mtn(self):
        gw = PaymentGateway()
        assert gw.detect_provider("0961123456") == "mtn_cash"
        assert gw.detect_provider("0988123456") == "mtn_cash"

    def test_detect_unknown(self):
        gw = PaymentGateway()
        assert gw.detect_provider("0111234567") is None
