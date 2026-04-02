"""Diaspora ordering service.

Enables Syrians abroad to order products from local businesses
and have them delivered to family/friends in Syria.
"""

from datetime import datetime
from dataclasses import dataclass

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.customer import Customer
from src.models.order import Order


@dataclass
class DiasporaOrder:
    """A cross-border order from the diaspora."""
    sender_phone: str       # Person abroad
    sender_name: str
    sender_country: str     # DE, TR, LB, JO, etc.
    recipient_phone: str    # Person in Syria
    recipient_name: str
    recipient_city: str
    merchant_id: int
    items: list[dict]
    message: str            # Personal message to include
    payment_currency: str   # USD, EUR, TRY
    is_gift: bool = True


# Exchange rates (updated periodically)
EXCHANGE_RATES = {
    "USD": 14500,   # 1 USD = 14,500 SYP (approximate)
    "EUR": 15800,
    "TRY": 450,
    "SAR": 3860,
    "AED": 3950,
    "JOD": 20450,
    "LBP": 0.16,    # Lebanese Lira
}


DIASPORA_COUNTRIES = {
    "DE": "ألمانيا",
    "TR": "تركيا",
    "LB": "لبنان",
    "JO": "الأردن",
    "SA": "السعودية",
    "AE": "الإمارات",
    "SE": "السويد",
    "NL": "هولندا",
    "US": "أمريكا",
    "CA": "كندا",
    "EG": "مصر",
    "IQ": "العراق",
}


def convert_to_syp(amount: float, currency: str) -> float | None:
    """Convert foreign currency amount to Syrian Pounds."""
    rate = EXCHANGE_RATES.get(currency.upper())
    if rate is None:
        return None
    return round(amount * rate, 2)


def convert_from_syp(amount_syp: float, currency: str) -> float | None:
    """Convert SYP to foreign currency."""
    rate = EXCHANGE_RATES.get(currency.upper())
    if rate is None or rate == 0:
        return None
    return round(amount_syp / rate, 2)


def format_price_multi_currency(amount_syp: float, foreign_currency: str) -> str:
    """Format price showing both SYP and foreign currency."""
    foreign = convert_from_syp(amount_syp, foreign_currency)
    if foreign is not None:
        return f"{amount_syp:,.0f} ل.س (~{foreign:.2f} {foreign_currency})"
    return f"{amount_syp:,.0f} ل.س"


class DiasporaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def mark_customer_as_diaspora(self, customer_id: int, country_code: str) -> None:
        """Mark a customer as being from the diaspora."""
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if customer:
            customer.is_diaspora = True
            customer.notes = f"Diaspora: {DIASPORA_COUNTRIES.get(country_code, country_code)}"
            await self.db.commit()

    async def create_diaspora_order(self, order_data: DiasporaOrder) -> dict:
        """Create a cross-border diaspora order.

        Returns order details with prices in both SYP and sender's currency.
        """
        # Calculate total in SYP
        total_syp = sum(
            item.get("price", 0) * item.get("quantity", 1)
            for item in order_data.items
        )

        # Convert to sender's currency
        total_foreign = convert_from_syp(total_syp, order_data.payment_currency)

        return {
            "type": "diaspora",
            "sender": {
                "name": order_data.sender_name,
                "phone": order_data.sender_phone,
                "country": order_data.sender_country,
            },
            "recipient": {
                "name": order_data.recipient_name,
                "phone": order_data.recipient_phone,
                "city": order_data.recipient_city,
            },
            "items": order_data.items,
            "total_syp": total_syp,
            "total_foreign": total_foreign,
            "foreign_currency": order_data.payment_currency,
            "message": order_data.message,
            "is_gift": order_data.is_gift,
            "delivery_fee_syp": 15000,  # Standard delivery fee
        }

    async def get_diaspora_stats(self, merchant_id: int) -> dict:
        """Get diaspora order statistics for a merchant."""
        result = await self.db.execute(
            select(Customer).where(
                and_(
                    Customer.merchant_id == merchant_id,
                    Customer.is_diaspora == True,
                )
            )
        )
        diaspora_customers = result.scalars().all()

        return {
            "diaspora_customers": len(diaspora_customers),
            "top_countries": self._count_countries(diaspora_customers),
        }

    def _count_countries(self, customers: list[Customer]) -> list[dict]:
        """Count customers by country from their notes."""
        country_counts: dict[str, int] = {}
        for c in customers:
            if c.notes and c.notes.startswith("Diaspora:"):
                country = c.notes.replace("Diaspora: ", "").strip()
                country_counts[country] = country_counts.get(country, 0) + 1

        return sorted(
            [{"country": k, "count": v} for k, v in country_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )


def format_diaspora_order_message(order: dict) -> str:
    """Format a diaspora order as a chat message."""
    items_text = "\n".join(
        f"  • {item.get('name_ar', item.get('name', '?'))} × {item.get('quantity', 1)}"
        for item in order["items"]
    )

    msg = order.get("message", "")
    gift_text = f"\n💌 رسالة: {msg}" if msg else ""

    total_display = format_price_multi_currency(
        order["total_syp"], order["foreign_currency"]
    )

    return (
        f"🌍 طلبية من المغترب\n"
        f"المرسل: {order['sender']['name']} ({DIASPORA_COUNTRIES.get(order['sender']['country'], order['sender']['country'])})\n"
        f"المستلم: {order['recipient']['name']} — {order['recipient']['city']}\n\n"
        f"الطلب:\n{items_text}\n\n"
        f"💰 المجموع: {total_display}\n"
        f"🚚 التوصيل: {order.get('delivery_fee_syp', 0):,.0f} ل.س"
        f"{gift_text}"
    )
