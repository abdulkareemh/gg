"""Product/inventory database operations."""

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.product import Product


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        merchant_id: int,
        name: str,
        name_ar: str,
        price: float,
        category: str | None = None,
        stock_quantity: int = 0,
        description: str | None = None,
    ) -> Product:
        product = Product(
            merchant_id=merchant_id,
            name=name,
            name_ar=name_ar,
            price=price,
            category=category,
            stock_quantity=stock_quantity,
            description=description,
        )
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def get_catalog(self, merchant_id: int, category: str | None = None) -> list[Product]:
        query = select(Product).where(
            and_(Product.merchant_id == merchant_id, Product.is_available == True)
        )
        if category:
            query = query.where(Product.category == category)
        query = query.order_by(Product.category, Product.name_ar)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search(self, merchant_id: int, query_text: str) -> list[Product]:
        """Search products by Arabic or English name."""
        pattern = f"%{query_text}%"
        result = await self.db.execute(
            select(Product).where(
                and_(
                    Product.merchant_id == merchant_id,
                    Product.is_available == True,
                    (Product.name_ar.ilike(pattern) | Product.name.ilike(pattern)),
                )
            )
        )
        return list(result.scalars().all())

    async def update_stock(self, product_id: int, quantity: int) -> Product | None:
        product = await self.db.get(Product, product_id)
        if product:
            product.stock_quantity = quantity
            await self.db.commit()
            await self.db.refresh(product)
        return product

    async def get_low_stock(self, merchant_id: int) -> list[Product]:
        result = await self.db.execute(
            select(Product).where(
                and_(
                    Product.merchant_id == merchant_id,
                    Product.is_available == True,
                    Product.stock_quantity <= Product.low_stock_threshold,
                )
            )
        )
        return list(result.scalars().all())

    async def toggle_availability(self, product_id: int) -> Product | None:
        product = await self.db.get(Product, product_id)
        if product:
            product.is_available = not product.is_available
            await self.db.commit()
            await self.db.refresh(product)
        return product

    async def bulk_create_from_list(self, merchant_id: int, products_data: list[dict]) -> list[Product]:
        """Bulk create products from a list of dicts."""
        created = []
        for data in products_data:
            product = Product(
                merchant_id=merchant_id,
                name=data.get("name", data.get("name_ar", "")),
                name_ar=data.get("name_ar", data.get("name", "")),
                price=data["price"],
                category=data.get("category"),
                stock_quantity=data.get("stock", 0),
                description=data.get("description"),
            )
            self.db.add(product)
            created.append(product)
        await self.db.commit()
        for p in created:
            await self.db.refresh(p)
        return created
