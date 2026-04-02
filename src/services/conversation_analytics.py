"""Conversation analytics — message patterns, peak hours, popular intents.

Analyzes message history to provide insights about customer behavior.
All computed from audit logs — no external analytics service needed.
"""

from datetime import datetime, timedelta
from collections import Counter

from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit import AuditLog


class ConversationAnalytics:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_message_volume(self, merchant_id: int, days: int = 7) -> dict:
        """Get daily message volume for the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(
                func.date(AuditLog.created_at).label("day"),
                func.count(AuditLog.id).label("count"),
            ).where(and_(
                AuditLog.merchant_id == merchant_id,
                AuditLog.event_type == "message_in",
                AuditLog.created_at >= cutoff,
            )).group_by(func.date(AuditLog.created_at))
            .order_by(func.date(AuditLog.created_at))
        )

        return {
            "period": f"Last {days} days",
            "daily": [{"date": str(r.day), "messages": r.count} for r in result.all()],
        }

    async def get_peak_hours(self, merchant_id: int, days: int = 30) -> dict:
        """Analyze which hours of the day are busiest."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(
                extract("hour", AuditLog.created_at).label("hour"),
                func.count(AuditLog.id).label("count"),
            ).where(and_(
                AuditLog.merchant_id == merchant_id,
                AuditLog.event_type == "message_in",
                AuditLog.created_at >= cutoff,
            )).group_by(extract("hour", AuditLog.created_at))
            .order_by(extract("hour", AuditLog.created_at))
        )

        hours = {i: 0 for i in range(24)}
        for r in result.all():
            hours[int(r.hour)] = r.count

        # Find peak hours (Syria UTC+3)
        peak_hour = max(hours, key=hours.get)
        syria_peak = (peak_hour + 3) % 24

        return {
            "hourly_distribution": hours,
            "peak_hour_utc": peak_hour,
            "peak_hour_syria": syria_peak,
            "peak_hour_label": f"{syria_peak}:00",
        }

    async def get_platform_breakdown(self, merchant_id: int, days: int = 30) -> dict:
        """Break down messages by platform (WhatsApp vs Telegram)."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(
                AuditLog.platform,
                func.count(AuditLog.id).label("count"),
            ).where(and_(
                AuditLog.merchant_id == merchant_id,
                AuditLog.event_type == "message_in",
                AuditLog.created_at >= cutoff,
                AuditLog.platform != None,
            )).group_by(AuditLog.platform)
        )

        platforms = {r.platform: r.count for r in result.all()}
        total = sum(platforms.values())

        return {
            "platforms": platforms,
            "total": total,
            "primary": max(platforms, key=platforms.get) if platforms else "none",
        }

    async def get_response_rate(self, merchant_id: int, days: int = 7) -> dict:
        """Calculate bot response rate (messages answered vs total)."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        incoming = await self.db.execute(
            select(func.count(AuditLog.id)).where(and_(
                AuditLog.merchant_id == merchant_id,
                AuditLog.event_type == "message_in",
                AuditLog.created_at >= cutoff,
            ))
        )
        outgoing = await self.db.execute(
            select(func.count(AuditLog.id)).where(and_(
                AuditLog.merchant_id == merchant_id,
                AuditLog.event_type == "message_out",
                AuditLog.created_at >= cutoff,
            ))
        )

        in_count = incoming.scalar() or 0
        out_count = outgoing.scalar() or 0
        rate = (out_count / in_count * 100) if in_count > 0 else 0

        return {
            "incoming": in_count,
            "outgoing": out_count,
            "response_rate": f"{rate:.1f}%",
        }

    async def get_full_analytics(self, merchant_id: int) -> dict:
        """Get comprehensive conversation analytics."""
        return {
            "volume": await self.get_message_volume(merchant_id),
            "peak_hours": await self.get_peak_hours(merchant_id),
            "platforms": await self.get_platform_breakdown(merchant_id),
            "response_rate": await self.get_response_rate(merchant_id),
        }


def format_analytics_report(data: dict) -> str:
    """Format analytics as Arabic chat message."""
    volume = data.get("volume", {})
    peak = data.get("peak_hours", {})
    platforms = data.get("platforms", {})
    response = data.get("response_rate", {})

    daily = volume.get("daily", [])
    total_msgs = sum(d["messages"] for d in daily)

    lines = [
        "📊 تحليلات المحادثات\n",
        f"💬 إجمالي الرسائل (7 أيام): {total_msgs}",
        f"🕐 ساعة الذروة: {peak.get('peak_hour_label', '?')}",
        f"📱 المنصة الرئيسية: {platforms.get('primary', '?')}",
        f"✅ نسبة الرد: {response.get('response_rate', '?')}",
    ]

    return "\n".join(lines)
