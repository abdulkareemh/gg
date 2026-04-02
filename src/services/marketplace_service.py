"""Marketplace service — discover merchants and browse catalogs.

Enables customers to find businesses by type, city, and search.
"""

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.merchant import Merchant
from src.models.product import Product


class MarketplaceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_merchants(
        self,
        city: str | None = None,
        business_type: str | None = None,
        query: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Search for merchants by city, type, or name."""
        stmt = select(Merchant).where(Merchant.is_active == True)

        if city:
            stmt = stmt.where(Merchant.city == city)

        if business_type:
            stmt = stmt.where(Merchant.business_type == business_type)

        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Merchant.business_name.ilike(pattern),
                    Merchant.name.ilike(pattern),
                )
            )

        stmt = stmt.order_by(Merchant.business_name).limit(limit)

        result = await self.db.execute(stmt)
        merchants = result.scalars().all()

        return [
            {
                "id": m.id,
                "business_name": m.business_name,
                "business_type": m.business_type,
                "city": m.city,
                "phone": m.phone,
                "platform": m.platform,
            }
            for m in merchants
        ]

    async def get_merchant_profile(self, merchant_id: int) -> dict | None:
        """Get a full merchant profile with product categories and stats."""
        result = await self.db.execute(
            select(Merchant).where(and_(Merchant.id == merchant_id, Merchant.is_active == True))
        )
        merchant = result.scalar_one_or_none()
        if not merchant:
            return None

        # Get product count and categories
        prod_result = await self.db.execute(
            select(
                Product.category,
                func.count(Product.id).label("count"),
            )
            .where(and_(Product.merchant_id == merchant_id, Product.is_available == True))
            .group_by(Product.category)
        )
        categories = [
            {"name": row.category or "عام", "count": row.count}
            for row in prod_result.all()
        ]

        total_products = sum(c["count"] for c in categories)

        return {
            "id": merchant.id,
            "business_name": merchant.business_name,
            "business_type": merchant.business_type,
            "city": merchant.city,
            "phone": merchant.phone,
            "platform": merchant.platform,
            "categories": categories,
            "total_products": total_products,
        }

    async def get_cities(self) -> list[dict]:
        """Get list of cities with merchant counts."""
        result = await self.db.execute(
            select(Merchant.city, func.count(Merchant.id).label("count"))
            .where(Merchant.is_active == True)
            .group_by(Merchant.city)
            .order_by(func.count(Merchant.id).desc())
        )
        return [{"city": row.city, "merchants": row.count} for row in result.all()]

    async def get_business_types(self) -> list[dict]:
        """Get list of business types with counts."""
        result = await self.db.execute(
            select(Merchant.business_type, func.count(Merchant.id).label("count"))
            .where(Merchant.is_active == True)
            .group_by(Merchant.business_type)
            .order_by(func.count(Merchant.id).desc())
        )

        type_labels = {
            "restaurant": "مطاعم",
            "shop": "محلات",
            "service": "خدمات",
            "other": "أخرى",
        }

        return [
            {
                "type": row.business_type,
                "label": type_labels.get(row.business_type, row.business_type),
                "count": row.count,
            }
            for row in result.all()
        ]


def format_merchant_list(merchants: list[dict]) -> str:
    """Format merchant search results as Arabic chat message."""
    if not merchants:
        return "ما لقيت محلات بهالبحث. جرب كلمات تانية."

    type_icons = {
        "restaurant": "🍽️",
        "shop": "🏪",
        "service": "🔧",
    }

    lines = ["📍 النتائج:"]
    for m in merchants:
        icon = type_icons.get(m["business_type"], "📦")
        lines.append(f"  {icon} {m['business_name']} — {m['city']}")

    return "\n".join(lines)
