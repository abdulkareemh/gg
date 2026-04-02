"""Review and rating service."""

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.review import Review


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_review(
        self,
        merchant_id: int,
        customer_id: int,
        rating: int,
        comment: str | None = None,
        order_id: int | None = None,
    ) -> Review:
        """Create a new review."""
        rating = max(1, min(5, rating))  # Clamp 1-5
        review = Review(
            merchant_id=merchant_id,
            customer_id=customer_id,
            order_id=order_id,
            rating=rating,
            comment=comment,
        )
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def add_reply(self, review_id: int, reply: str) -> Review | None:
        """Merchant replies to a review."""
        review = await self.db.get(Review, review_id)
        if review:
            review.reply = reply
            await self.db.commit()
            await self.db.refresh(review)
        return review

    async def get_merchant_reviews(
        self, merchant_id: int, limit: int = 20
    ) -> list[Review]:
        result = await self.db.execute(
            select(Review)
            .where(Review.merchant_id == merchant_id)
            .order_by(Review.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_merchant_rating(self, merchant_id: int) -> dict:
        """Get average rating and distribution for a merchant."""
        result = await self.db.execute(
            select(
                func.avg(Review.rating).label("avg"),
                func.count(Review.id).label("total"),
            ).where(Review.merchant_id == merchant_id)
        )
        row = result.one()

        # Rating distribution
        dist_result = await self.db.execute(
            select(Review.rating, func.count(Review.id))
            .where(Review.merchant_id == merchant_id)
            .group_by(Review.rating)
        )
        distribution = {i: 0 for i in range(1, 6)}
        for r in dist_result.all():
            distribution[r[0]] = r[1]

        avg_rating = float(row.avg) if row.avg else 0.0

        return {
            "average": round(avg_rating, 1),
            "total_reviews": row.total or 0,
            "distribution": distribution,
            "stars_display": "⭐" * round(avg_rating),
        }


def format_reviews(reviews: list[Review]) -> str:
    """Format reviews as Arabic chat message."""
    if not reviews:
        return "ما في تقييمات بعد."

    lines = ["⭐ التقييمات:"]
    for r in reviews:
        stars = "⭐" * r.rating
        line = f"  {stars}"
        if r.comment:
            line += f" — {r.comment}"
        lines.append(line)
        if r.reply:
            lines.append(f"    ↳ رد المحل: {r.reply}")

    return "\n".join(lines)


def format_rating_summary(rating: dict) -> str:
    """Format rating summary as Arabic chat message."""
    return (
        f"⭐ التقييم: {rating['average']}/5 ({rating['total_reviews']} تقييم)\n"
        f"{rating['stars_display']}"
    )
