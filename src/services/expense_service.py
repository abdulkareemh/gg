"""Expense tracking service for merchants."""

from datetime import datetime, timedelta

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.expense import Expense


EXPENSE_CATEGORIES = {
    "مواد_أولية": "مواد أولية",
    "إيجار": "إيجار",
    "رواتب": "رواتب",
    "كهرباء": "كهرباء وماء",
    "نقل": "نقل وتوصيل",
    "تسويق": "تسويق وإعلان",
    "صيانة": "صيانة",
    "أخرى": "أخرى",
}


class ExpenseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_expense(
        self,
        merchant_id: int,
        amount: float,
        category: str,
        description: str | None = None,
        date: datetime | None = None,
    ) -> Expense:
        expense = Expense(
            merchant_id=merchant_id,
            amount=amount,
            category=category,
            description=description,
            date=date or datetime.utcnow(),
        )
        self.db.add(expense)
        await self.db.commit()
        await self.db.refresh(expense)
        return expense

    async def get_monthly_expenses(self, merchant_id: int, month: datetime | None = None) -> dict:
        """Get expense breakdown for a month."""
        if month is None:
            month = datetime.utcnow()

        month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month.month == 12:
            month_end = month_start.replace(year=month.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month.month + 1)

        result = await self.db.execute(
            select(
                Expense.category,
                func.sum(Expense.amount).label("total"),
                func.count(Expense.id).label("count"),
            ).where(and_(
                Expense.merchant_id == merchant_id,
                Expense.date >= month_start,
                Expense.date < month_end,
            )).group_by(Expense.category)
        )

        categories = []
        grand_total = 0.0
        for row in result.all():
            total = float(row.total)
            grand_total += total
            categories.append({
                "category": row.category,
                "label": EXPENSE_CATEGORIES.get(row.category, row.category),
                "total": total,
                "count": row.count,
            })

        return {
            "month": month_start.strftime("%Y-%m"),
            "total": grand_total,
            "categories": sorted(categories, key=lambda x: x["total"], reverse=True),
            "currency": "SYP",
        }

    async def get_profit_loss(self, merchant_id: int, month: datetime | None = None) -> dict:
        """Calculate simple profit/loss for a month."""
        from src.models.order import Order

        if month is None:
            month = datetime.utcnow()

        month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month.month == 12:
            month_end = month_start.replace(year=month.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month.month + 1)

        # Revenue
        revenue_result = await self.db.execute(
            select(func.sum(Order.total_amount)).where(and_(
                Order.merchant_id == merchant_id,
                Order.created_at >= month_start,
                Order.created_at < month_end,
            ))
        )
        revenue = float(revenue_result.scalar() or 0)

        # Expenses
        expense_result = await self.db.execute(
            select(func.sum(Expense.amount)).where(and_(
                Expense.merchant_id == merchant_id,
                Expense.date >= month_start,
                Expense.date < month_end,
            ))
        )
        expenses = float(expense_result.scalar() or 0)

        profit = revenue - expenses

        return {
            "month": month_start.strftime("%Y-%m"),
            "revenue": revenue,
            "expenses": expenses,
            "profit": profit,
            "margin_pct": round((profit / revenue * 100), 1) if revenue > 0 else 0,
            "currency": "SYP",
        }


def format_expense_report(data: dict) -> str:
    """Format expense report as Arabic chat message."""
    lines = [
        f"💸 تقرير المصاريف — {data['month']}",
        f"",
        f"💰 إجمالي المصاريف: {data['total']:,.0f} ل.س",
        f"",
    ]

    for cat in data["categories"]:
        pct = (cat["total"] / data["total"] * 100) if data["total"] > 0 else 0
        bar = "█" * int(pct / 5)
        lines.append(f"  {cat['label']}: {cat['total']:,.0f} ل.س {bar} ({pct:.0f}%)")

    return "\n".join(lines)


def format_profit_loss(data: dict) -> str:
    """Format P&L as Arabic chat message."""
    emoji = "📈" if data["profit"] >= 0 else "📉"

    return (
        f"{emoji} تقرير الأرباح — {data['month']}\n"
        f"\n"
        f"💰 الإيرادات: {data['revenue']:,.0f} ل.س\n"
        f"💸 المصاريف: {data['expenses']:,.0f} ل.س\n"
        f"{'✅' if data['profit'] >= 0 else '❌'} "
        f"{'الربح' if data['profit'] >= 0 else 'الخسارة'}: "
        f"{abs(data['profit']):,.0f} ل.س ({data['margin_pct']}%)"
    )
