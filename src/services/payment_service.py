"""Payment service — handles payment flows and DB persistence."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.integrations.payments import PaymentGateway, PaymentStatus, PaymentResult
from src.models.payment import Payment


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.gateway = PaymentGateway()

    async def initiate_payment(
        self,
        order_id: int,
        merchant_id: int,
        customer_phone: str,
        amount: float,
        provider: str | None = None,
    ) -> PaymentResult:
        """Initiate a payment and record it in the database."""
        # Auto-detect provider if not specified
        if not provider:
            provider = self.gateway.detect_provider(customer_phone)
            if not provider:
                return PaymentResult(
                    success=False,
                    transaction_id=None,
                    status=PaymentStatus.FAILED,
                    amount=amount,
                    currency="SYP",
                    provider="unknown",
                    error_message="Could not detect payment provider from phone number",
                )

        # Process the payment
        result = await self.gateway.process_payment(
            provider_name=provider,
            phone=customer_phone,
            amount=amount,
            order_id=order_id,
        )

        # Record in database
        payment = Payment(
            order_id=order_id,
            merchant_id=merchant_id,
            transaction_id=result.transaction_id,
            provider=provider,
            amount=amount,
            customer_phone=customer_phone,
            status=result.status.value,
            error_message=result.error_message,
        )
        self.db.add(payment)
        await self.db.commit()

        return result

    async def handle_callback(self, provider: str, transaction_id: str, status: str) -> Payment | None:
        """Handle a payment callback from the provider."""
        result = await self.db.execute(
            select(Payment).where(Payment.transaction_id == transaction_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            return None

        payment.status = status
        if status == "completed":
            payment.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def get_order_payments(self, order_id: int) -> list[Payment]:
        result = await self.db.execute(
            select(Payment).where(Payment.order_id == order_id).order_by(Payment.created_at.desc())
        )
        return list(result.scalars().all())
