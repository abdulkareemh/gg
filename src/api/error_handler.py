"""Global error handling for the API."""

import traceback

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Catch all unhandled exceptions and return clean error responses."""

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            # Log the full traceback
            print(f"[ERROR] Unhandled exception on {request.method} {request.url.path}:")
            traceback.print_exc()

            # Return a clean error response (don't leak internals)
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "An internal error occurred. Please try again.",
                    "error_ar": "حصل خطأ داخلي. الرجاء المحاولة لاحقاً.",
                },
            )
