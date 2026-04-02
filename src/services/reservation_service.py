"""Reservation and waitlist service for restaurants."""

from datetime import datetime, timedelta

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.reservation import Reservation


class ReservationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_reservation(
        self,
        merchant_id: int,
        customer_phone: str,
        reserved_for: datetime,
        party_size: int = 2,
        customer_name: str | None = None,
        notes: str | None = None,
    ) -> Reservation:
        reservation = Reservation(
            merchant_id=merchant_id,
            customer_phone=customer_phone,
            customer_name=customer_name,
            party_size=party_size,
            reserved_for=reserved_for,
            notes=notes,
        )
        self.db.add(reservation)
        await self.db.commit()
        await self.db.refresh(reservation)
        return reservation

    async def add_to_waitlist(
        self,
        merchant_id: int,
        customer_phone: str,
        party_size: int = 2,
        customer_name: str | None = None,
    ) -> Reservation:
        """Add customer to waitlist (no specific time)."""
        reservation = Reservation(
            merchant_id=merchant_id,
            customer_phone=customer_phone,
            customer_name=customer_name,
            party_size=party_size,
            reserved_for=datetime.utcnow(),
            is_waitlist=True,
        )
        self.db.add(reservation)
        await self.db.commit()
        await self.db.refresh(reservation)
        return reservation

    async def get_upcoming(self, merchant_id: int, hours_ahead: int = 12) -> list[Reservation]:
        now = datetime.utcnow()
        cutoff = now + timedelta(hours=hours_ahead)

        result = await self.db.execute(
            select(Reservation).where(
                and_(
                    Reservation.merchant_id == merchant_id,
                    Reservation.status.in_(["pending", "confirmed"]),
                    Reservation.is_waitlist == False,
                    Reservation.reserved_for >= now,
                    Reservation.reserved_for <= cutoff,
                )
            ).order_by(Reservation.reserved_for)
        )
        return list(result.scalars().all())

    async def get_waitlist(self, merchant_id: int) -> list[Reservation]:
        result = await self.db.execute(
            select(Reservation).where(
                and_(
                    Reservation.merchant_id == merchant_id,
                    Reservation.is_waitlist == True,
                    Reservation.status == "pending",
                )
            ).order_by(Reservation.created_at)
        )
        return list(result.scalars().all())

    async def update_status(self, reservation_id: int, status: str) -> Reservation | None:
        reservation = await self.db.get(Reservation, reservation_id)
        if reservation:
            reservation.status = status
            await self.db.commit()
            await self.db.refresh(reservation)
        return reservation

    async def get_today_count(self, merchant_id: int) -> int:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        result = await self.db.execute(
            select(func.count(Reservation.id)).where(
                and_(
                    Reservation.merchant_id == merchant_id,
                    Reservation.reserved_for >= today,
                    Reservation.reserved_for < tomorrow,
                    Reservation.status.in_(["pending", "confirmed"]),
                )
            )
        )
        return result.scalar() or 0


def format_reservations(reservations: list[Reservation]) -> str:
    """Format reservations as Arabic chat message."""
    if not reservations:
        return "ما في حجوزات قادمة."

    lines = ["📅 الحجوزات القادمة:"]
    for r in reservations:
        time_str = r.reserved_for.strftime("%H:%M")
        name = r.customer_name or r.customer_phone
        lines.append(f"  🕐 {time_str} — {name} ({r.party_size} أشخاص)")

    return "\n".join(lines)


def format_waitlist(waitlist: list[Reservation]) -> str:
    """Format waitlist as Arabic chat message."""
    if not waitlist:
        return "قائمة الانتظار فاضية ✅"

    lines = [f"⏳ قائمة الانتظار ({len(waitlist)}):"]
    for i, r in enumerate(waitlist, 1):
        name = r.customer_name or r.customer_phone
        lines.append(f"  {i}. {name} ({r.party_size} أشخاص)")

    return "\n".join(lines)
