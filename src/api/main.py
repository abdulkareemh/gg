"""Noor AI — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.routes import webhook, health, merchants, analytics, payments, diaspora, customers
from src.api.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    WebhookSecurityMiddleware,
    RequestSizeLimitMiddleware,
    setup_cors,
)
from src.api.error_handler import ErrorHandlerMiddleware
from src.models.database import init_db
from src.services.scheduler import TaskScheduler

scheduler = TaskScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await scheduler.start()
    print("[Noor AI] Server started. Ready to serve Syrian businesses!")
    yield
    await scheduler.stop()
    print("[Noor AI] Server shutting down.")


app = FastAPI(
    title="Noor AI",
    description="AI-powered business assistant for Syrian SMEs",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware (order matters — outermost first)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(WebhookSecurityMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
setup_cors(app)

# Routes
app.include_router(health.router, tags=["Health"])
app.include_router(webhook.router, prefix="/webhook", tags=["Webhooks"])
app.include_router(merchants.router, prefix="/api/merchants", tags=["Merchants"])
app.include_router(analytics.router, prefix="/api/merchants", tags=["Analytics"])
app.include_router(payments.router, prefix="/webhook", tags=["Payments"])
app.include_router(diaspora.router, prefix="/api/diaspora", tags=["Diaspora"])
app.include_router(customers.router, prefix="/api/merchants", tags=["Customers"])

# Static files and landing page
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def landing_page():
    return FileResponse("static/index.html")
