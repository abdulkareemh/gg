"""Merchant comparison for marketplace."""

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.merchant import Merchant
from src.models.product import Product
from src.models.order import Order
from src.models.review import Review


class MerchantComparisonService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def compare(self, merchant_ids: list[int]) -> list[dict]:
        """Compare multiple merchants side by side."""
        results = []

        for mid in merchant_ids:
            merchant = await self.db.get(Merchant, mid)
            if not merchant or not merchant.is_active:
                continue

            # Product count
            prod_count = await self.db.execute(
                select(func.count(Product.id)).where(
                    and_(Product.merchant_id == mid, Product.is_available == True)
                )
            )

            # Average price
            avg_price = await self.db.execute(
                select(func.avg(Product.price)).where(
                    and_(Product.merchant_id == mid, Product.is_available == True)
                )
            )

            # Order count
            order_count = await self.db.execute(
                select(func.count(Order.id)).where(Order.merchant_id == mid)
            )

            # Rating
            rating = await self.db.execute(
                select(func.avg(Review.rating), func.count(Review.id)).where(Review.merchant_id == mid)
            )
            rating_row = rating.one()

            results.append({
                "id": merchant.id,
                "business_name": merchant.business_name,
                "business_type": merchant.business_type,
                "city": merchant.city,
                "products": prod_count.scalar() or 0,
                "avg_price": round(float(avg_price.scalar() or 0)),
                "total_orders": order_count.scalar() or 0,
                "rating": round(float(rating_row[0] or 0), 1),
                "review_count": rating_row[1] or 0,
            })

        return sorted(results, key=lambda x: x["rating"], reverse=True)


def format_comparison(merchants: list[dict]) -> str:
    """Format merchant comparison as Arabic chat message."""
    if not merchants:
        return "ما لقيت محلات للمقارنة."

    lines = ["📊 مقارنة المحلات:\n"]
    for m in merchants:
        stars = "⭐" * round(m["rating"]) if m["rating"] > 0 else "بدون تقييم"
        lines.append(
            f"🏪 {m['business_name']} ({m['city']})\n"
            f"   {stars} ({m['review_count']} تقييم)\n"
            f"   📦 {m['products']} منتج | 💰 متوسط {m['avg_price']:,.0f} ل.س\n"
        )

    return "\n".join(lines)
