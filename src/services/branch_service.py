"""Branch management for multi-location merchants."""

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.branch import Branch


class BranchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_branch(
        self,
        merchant_id: int,
        name: str,
        city: str,
        address: str | None = None,
        phone: str | None = None,
        is_main: bool = False,
        opening_hours: str | None = None,
    ) -> Branch:
        branch = Branch(
            merchant_id=merchant_id,
            name=name,
            city=city,
            address=address,
            phone=phone,
            is_main=is_main,
            opening_hours=opening_hours,
        )
        self.db.add(branch)
        await self.db.commit()
        await self.db.refresh(branch)
        return branch

    async def get_branches(self, merchant_id: int) -> list[Branch]:
        result = await self.db.execute(
            select(Branch).where(
                and_(Branch.merchant_id == merchant_id, Branch.is_active == True)
            ).order_by(Branch.is_main.desc(), Branch.name)
        )
        return list(result.scalars().all())

    async def get_branch(self, branch_id: int) -> Branch | None:
        return await self.db.get(Branch, branch_id)

    async def deactivate_branch(self, branch_id: int) -> bool:
        branch = await self.get_branch(branch_id)
        if branch:
            branch.is_active = False
            await self.db.commit()
            return True
        return False


def format_branches(branches: list[Branch]) -> str:
    """Format branches as Arabic chat message."""
    if not branches:
        return "ما في فروع مسجلة."

    lines = ["🏢 الفروع:"]
    for b in branches:
        main = " (الفرع الرئيسي)" if b.is_main else ""
        hours = f" | {b.opening_hours}" if b.opening_hours else ""
        lines.append(f"  • {b.name} — {b.city}{main}{hours}")

    return "\n".join(lines)
