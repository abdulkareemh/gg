"""Notification service — sends alerts to merchants and customers."""

from src.integrations.whatsapp import WhatsAppClient
from src.integrations.telegram import TelegramClient


class NotificationService:
    """Sends notifications to merchants and customers across platforms."""

    def __init__(self):
        self.whatsapp = WhatsAppClient()
        self.telegram = TelegramClient()

    async def notify_merchant_new_order(
        self, phone: str, platform: str, order_id: int, customer_name: str, total: float, items_summary: str
    ) -> None:
        """Alert merchant about a new incoming order."""
        text = (
            f"🔔 طلبية جديدة #{order_id}\n"
            f"الزبون: {customer_name}\n"
            f"الطلب: {items_summary}\n"
            f"المجموع: {total:,.0f} ل.س\n\n"
            f"ابعت 'تأكيد {order_id}' للموافقة"
        )
        await self._send(phone, text, platform)

    async def notify_customer_order_confirmed(
        self, phone: str, platform: str, order_id: int, estimated_time: str
    ) -> None:
        """Tell customer their order was confirmed."""
        text = (
            f"✅ تم تأكيد طلبيتك #{order_id}\n"
            f"الوقت المتوقع: {estimated_time}\n"
            f"رح نبعتلك تحديث لما تصير جاهزة!"
        )
        await self._send(phone, text, platform)

    async def notify_customer_order_ready(self, phone: str, platform: str, order_id: int) -> None:
        """Tell customer their order is ready."""
        text = f"🎉 طلبيتك #{order_id} جاهزة! تفضل استلمها."
        await self._send(phone, text, platform)

    async def notify_merchant_low_stock(
        self, phone: str, platform: str, products: list[dict]
    ) -> None:
        """Alert merchant about low stock items."""
        items = "\n".join(f"  • {p['name_ar']}: {p['stock']} باقي" for p in products)
        text = f"⚠️ تنبيه مخزون منخفض:\n{items}\n\nحدّث المخزون بإرسال 'تحديث مخزون'"
        await self._send(phone, text, platform)

    async def send_daily_report(
        self, phone: str, platform: str, order_count: int, revenue: float, top_product: str
    ) -> None:
        """Send daily business summary to merchant."""
        text = (
            f"📊 تقرير اليوم:\n"
            f"• الطلبيات: {order_count}\n"
            f"• الإيرادات: {revenue:,.0f} ل.س\n"
            f"• الأكثر طلباً: {top_product}\n\n"
            f"ابعت 'تقرير' للتفاصيل"
        )
        await self._send(phone, text, platform)

    async def _send(self, phone: str, text: str, platform: str) -> None:
        """Send a message on the appropriate platform."""
        try:
            if platform == "whatsapp":
                await self.whatsapp.send_text(phone, text)
            elif platform == "telegram":
                await self.telegram.send_text(phone, text)
        except Exception as e:
            print(f"[NOTIFY ERROR] {platform} {phone}: {e}")
