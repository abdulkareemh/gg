"""Order modification service — add/remove items after order creation."""

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.order import Order, OrderItem
from src.models.product import Product


class OrderModificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_item(self, order_id: int, product_id: int, quantity: int = 1) -> dict:
        """Add an item to an existing order (only if pending/confirmed)."""
        order = await self.db.get(Order, order_id)
        if not order:
            return {"success": False, "message": "طلبية غير موجودة"}

        if order.status not in ("pending", "confirmed"):
            return {"success": False, "message": "ما بنقدر نعدل على طلبية بدأت بالتحضير"}

        product = await self.db.get(Product, product_id)
        if not product or not product.is_available:
            return {"success": False, "message": "المنتج غير متوفر"}

        if product.stock_quantity < quantity:
            return {"success": False, "message": f"ما في كمية كافية. باقي {product.stock_quantity}"}

        # Check if item already in order
        result = await self.db.execute(
            select(OrderItem).where(
                and_(OrderItem.order_id == order_id, OrderItem.product_id == product_id)
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.quantity += quantity
            existing.total_price = float(existing.unit_price) * existing.quantity
        else:
            item = OrderItem(
                order_id=order_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=float(product.price),
                total_price=float(product.price) * quantity,
            )
            self.db.add(item)

        # Update stock and order total
        product.stock_quantity -= quantity
        order.total_amount = float(order.total_amount) + (float(product.price) * quantity)

        await self.db.commit()

        return {
            "success": True,
            "message": f"تمت إضافة {product.name_ar} × {quantity} ✅",
            "new_total": float(order.total_amount),
        }

    async def remove_item(self, order_id: int, product_id: int) -> dict:
        """Remove an item from an existing order."""
        order = await self.db.get(Order, order_id)
        if not order:
            return {"success": False, "message": "طلبية غير موجودة"}

        if order.status not in ("pending", "confirmed"):
            return {"success": False, "message": "ما بنقدر نعدل على طلبية بدأت بالتحضير"}

        result = await self.db.execute(
            select(OrderItem).where(
                and_(OrderItem.order_id == order_id, OrderItem.product_id == product_id)
            )
        )
        item = result.scalar_one_or_none()

        if not item:
            return {"success": False, "message": "هالصنف مش بالطلبية"}

        # Restore stock
        product = await self.db.get(Product, product_id)
        if product:
            product.stock_quantity += item.quantity

        # Update order total
        order.total_amount = float(order.total_amount) - float(item.total_price)

        await self.db.delete(item)
        await self.db.commit()

        return {
            "success": True,
            "message": f"تم حذف {product.name_ar if product else 'الصنف'} من الطلبية ✅",
            "new_total": float(order.total_amount),
        }

    async def change_quantity(self, order_id: int, product_id: int, new_quantity: int) -> dict:
        """Change the quantity of an item in an order."""
        order = await self.db.get(Order, order_id)
        if not order or order.status not in ("pending", "confirmed"):
            return {"success": False, "message": "ما بنقدر نعدل على هالطلبية"}

        result = await self.db.execute(
            select(OrderItem).where(
                and_(OrderItem.order_id == order_id, OrderItem.product_id == product_id)
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return {"success": False, "message": "هالصنف مش بالطلبية"}

        product = await self.db.get(Product, product_id)
        old_quantity = item.quantity
        diff = new_quantity - old_quantity

        if product and product.stock_quantity < diff:
            return {"success": False, "message": f"ما في كمية كافية. باقي {product.stock_quantity}"}

        # Update stock
        if product:
            product.stock_quantity -= diff

        # Update item
        old_total = float(item.total_price)
        item.quantity = new_quantity
        item.total_price = float(item.unit_price) * new_quantity
        new_total_diff = float(item.total_price) - old_total

        order.total_amount = float(order.total_amount) + new_total_diff

        await self.db.commit()

        return {
            "success": True,
            "message": f"تم تعديل الكمية إلى {new_quantity} ✅",
            "new_total": float(order.total_amount),
        }
