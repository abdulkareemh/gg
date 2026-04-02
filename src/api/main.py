"""Noor AI — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import webhook, health, merchants, analytics
from src.models.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Noor AI",
    description="AI-powered business assistant for Syrian SMEs",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router, tags=["Health"])
app.include_router(webhook.router, prefix="/webhook", tags=["Webhooks"])
app.include_router(merchants.router, prefix="/api/merchants", tags=["Merchants"])
app.include_router(analytics.router, prefix="/api/merchants", tags=["Analytics"])
