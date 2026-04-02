"""Health check and metrics endpoints."""

from fastapi import APIRouter

from src.utils.metrics import metrics

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "noor-ai", "version": "0.2.0"}


@router.get("/metrics")
async def get_metrics():
    """Application metrics for monitoring."""
    return metrics.get_report()
