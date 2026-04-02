"""Security and utility middleware for Noor AI."""

import time
import hashlib
import hmac
from collections import defaultdict

from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.utils.config import settings


# --- Rate Limiting ---

class RateLimiter:
    """In-memory rate limiter per IP/phone. Use Redis in production."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window

        # Clean old entries
        self._requests[key] = [t for t in self._requests[key] if t > window_start]

        if len(self._requests[key]) >= self.max_requests:
            return False

        self._requests[key].append(now)
        return True

    def remaining(self, key: str) -> int:
        now = time.time()
        window_start = now - self.window
        recent = [t for t in self._requests[key] if t > window_start]
        return max(0, self.max_requests - len(recent))


rate_limiter = RateLimiter(max_requests=60, window_seconds=60)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit requests per client IP."""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"ip:{client_ip}"

        if not rate_limiter.is_allowed(key):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(rate_limiter.remaining(key))
        return response


# --- Request Logging ---

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests with timing."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000

        # Log non-health requests
        if request.url.path != "/health":
            print(
                f"[{request.method}] {request.url.path} "
                f"-> {response.status_code} ({duration_ms:.1f}ms)"
            )

        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"
        return response


# --- WhatsApp Signature Verification ---

def verify_whatsapp_signature(payload: bytes, signature: str, app_secret: str) -> bool:
    """Verify that a WhatsApp webhook payload is authentic.

    WhatsApp signs payloads with HMAC SHA-256 using the app secret.
    """
    expected = hmac.new(
        app_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


class WebhookSecurityMiddleware(BaseHTTPMiddleware):
    """Validate webhook signatures for WhatsApp requests."""

    async def dispatch(self, request: Request, call_next):
        # Only verify POST requests to webhook endpoints
        if request.method == "POST" and "/webhook/whatsapp" in request.url.path:
            signature = request.headers.get("X-Hub-Signature-256", "")

            # Skip verification in development
            if settings.app_env != "development" and signature:
                body = await request.body()
                app_secret = settings.whatsapp_verify_token

                if app_secret and not verify_whatsapp_signature(body, signature, app_secret):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid webhook signature"},
                    )

        return await call_next(request)


# --- CORS Setup ---

def setup_cors(app):
    """Configure CORS for the API."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # Local dev dashboard
            "http://localhost:8080",
            "https://noor-ai.sy",  # Production domain
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# --- Request Size Limit ---

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with bodies larger than the limit."""

    MAX_BODY_SIZE = 1 * 1024 * 1024  # 1 MB

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )
        return await call_next(request)
