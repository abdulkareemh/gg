"""Audit trail and event logging service."""

import json
from datetime import datetime, timedelta

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit import AuditLog


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        event_type: str,
        actor: str,
        description: str,
        merchant_id: int | None = None,
        metadata: dict | None = None,
        platform: str | None = None,
    ) -> AuditLog:
        """Record an audit event."""
        entry = AuditLog(
            merchant_id=merchant_id,
            event_type=event_type,
            actor=actor,
            description=description,
            metadata_json=json.dumps(metadata, ensure_ascii=False) if metadata else None,
            platform=platform,
        )
        self.db.add(entry)
        await self.db.commit()
        return entry

    async def get_recent(
        self, merchant_id: int | None = None, event_type: str | None = None, limit: int = 50
    ) -> list[AuditLog]:
        stmt = select(AuditLog)
        if merchant_id:
            stmt = stmt.where(AuditLog.merchant_id == merchant_id)
        if event_type:
            stmt = stmt.where(AuditLog.event_type == event_type)
        stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_event_counts(self, merchant_id: int, hours: int = 24) -> dict:
        """Get event type counts for the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await self.db.execute(
            select(AuditLog.event_type, func.count(AuditLog.id))
            .where(and_(AuditLog.merchant_id == merchant_id, AuditLog.created_at >= cutoff))
            .group_by(AuditLog.event_type)
        )
        return {row[0]: row[1] for row in result.all()}
