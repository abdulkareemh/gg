"""Smart product recommendation engine.

Suggests products based on:
1. Customer's past order history
2. Popular items among similar customers
3. Time-of-day patterns (breakfast/lunch/dinner)
4. Complementary products (fries with burger, drink with meal)
"""

from datetime import datetime
from collections import Counter

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.order import Order, OrderItem
from src.models.product import Product
from src.models.customer import Customer


# Complementary product pairs (if customer orders X, suggest Y)
COMPLEMENTARY_PRODUCTS = {
    "ساندويشات": ["مشروبات", "سلطات", "مقبلات"],
    "أطباق رئيسية": ["مشروبات", "سلطات", "حلويات"],
    "بيتزا": ["مشروبات", "سلطات"],
    "برغر": ["مشروبات", "بطاطا"],
    "حلويات": ["مشروبات"],
}

# Time-of-day product categories
TIME_CATEGORIES = {
    "morning": ["مشروبات", "فطور"],       # 6-11
    "lunch": ["ساندويشات", "أطباق رئيسية", "سلطات"],  # 11-15
    "afternoon": ["مشروبات", "حلويات"],   # 15-18
    "dinner": ["أطباق رئيسية", "مشاوي"],  # 18-23
    "late": ["ساندويشات", "مشروبات"],     # 23-6
}


def _get_time_period() -> str:
    hour = datetime.utcnow().hour + 3  # Syria is UTC+3
    if hour >= 24:
        hour -= 24
    if 6 <= hour < 11:
        return "morning"
    elif 11 <= hour < 15:
        return "lunch"
    elif 15 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 23:
        return "dinner"
    return "late"


class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recommendations(
        self, merchant_id: int, customer_id: int | None = None, limit: int = 5
    ) -> list[dict]:
        """Get personalized product recommendations.

        Combines multiple signals:
        1. Customer history (if available)
        2. Popular products overall
        3. Time-of-day relevance
        4. Complementary products
        """
        scores: dict[int, float] = {}
        product_cache: dict[int, Product] = {}

        # Load all available products
        result = await self.db.execute(
            select(Product).where(
                and_(Product.merchant_id == merchant_id, Product.is_available == True, Product.stock_quantity > 0)
            )
        )
        products = result.scalars().all()

        for p in products:
            product_cache[p.id] = p
            scores[p.id] = 0.0

        if not products:
            return []

        # Signal 1: Customer history — boost products they've ordered before
        if customer_id:
            await self._score_from_history(scores, customer_id)

        # Signal 2: Overall popularity
        await self._score_from_popularity(scores, merchant_id)

        # Signal 3: Time of day
        self._score_from_time(scores, product_cache)

        # Signal 4: Complementary products (if customer has a cart)
        # This gets applied when we know what's in the cart

        # Sort by score and return top results
        sorted_ids = sorted(scores.keys(), key=lambda pid: scores[pid], reverse=True)

        recommendations = []
        for pid in sorted_ids[:limit]:
            p = product_cache.get(pid)
            if p:
                recommendations.append({
                    "id": p.id,
                    "name": p.name,
                    "name_ar": p.name_ar,
                    "price": float(p.price),
                    "category": p.category,
                    "score": round(scores[pid], 2),
                    "reason": self._get_reason(scores[pid], pid, customer_id),
                })

        return recommendations

    async def _score_from_history(self, scores: dict[int, float], customer_id: int):
        """Boost products the customer has ordered before."""
        result = await self.db.execute(
            select(OrderItem.product_id, func.count(OrderItem.id).label("times"))
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.customer_id == customer_id)
            .group_by(OrderItem.product_id)
        )
        for row in result.all():
            if row.product_id in scores:
                # More orders = higher score, but with diminishing returns
                scores[row.product_id] += min(row.times * 2.0, 8.0)

    async def _score_from_popularity(self, scores: dict[int, float], merchant_id: int):
        """Boost products that are popular overall."""
        result = await self.db.execute(
            select(OrderItem.product_id, func.count(OrderItem.id).label("total"))
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.merchant_id == merchant_id)
            .group_by(OrderItem.product_id)
            .order_by(func.count(OrderItem.id).desc())
            .limit(20)
        )
        for rank, row in enumerate(result.all()):
            if row.product_id in scores:
                scores[row.product_id] += max(5.0 - rank * 0.3, 0.5)

    def _score_from_time(self, scores: dict[int, float], products: dict[int, Product]):
        """Boost products relevant to current time of day."""
        period = _get_time_period()
        preferred_categories = TIME_CATEGORIES.get(period, [])

        for pid, product in products.items():
            if product.category in preferred_categories:
                scores[pid] += 3.0

    def _get_reason(self, score: float, product_id: int, customer_id: int | None) -> str:
        """Generate a human-readable recommendation reason in Arabic."""
        if score >= 8:
            return "من طلباتك المفضلة"
        elif score >= 5:
            return "الأكثر طلباً"
        elif score >= 3:
            return "مناسب للوقت الحالي"
        return "قد يعجبك"

    async def get_complementary(self, merchant_id: int, cart_categories: list[str], limit: int = 3) -> list[dict]:
        """Suggest complementary products based on what's in the cart."""
        suggested_categories = set()
        for cat in cart_categories:
            complements = COMPLEMENTARY_PRODUCTS.get(cat, [])
            suggested_categories.update(complements)

        # Remove categories already in cart
        suggested_categories -= set(cart_categories)

        if not suggested_categories:
            return []

        result = await self.db.execute(
            select(Product).where(
                and_(
                    Product.merchant_id == merchant_id,
                    Product.is_available == True,
                    Product.stock_quantity > 0,
                    Product.category.in_(list(suggested_categories)),
                )
            ).limit(limit)
        )
        products = result.scalars().all()

        return [
            {
                "id": p.id,
                "name_ar": p.name_ar,
                "price": float(p.price),
                "category": p.category,
                "reason": "بيتناسب مع طلبيتك",
            }
            for p in products
        ]


def format_recommendations(recs: list[dict]) -> str:
    """Format recommendations as an Arabic chat message."""
    if not recs:
        return "ما عندي اقتراحات حالياً."

    lines = ["💡 اقتراحات إلك:"]
    for r in recs:
        lines.append(f"  • {r['name_ar']} — {r['price']:,.0f} ل.س ({r['reason']})")

    return "\n".join(lines)
