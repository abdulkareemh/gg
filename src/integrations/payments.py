"""Payment provider integrations for Syrian mobile money.

Supports SyriaTel Cash and MTN Cash — the two primary
mobile money providers in Syria.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import httpx

from src.utils.config import settings


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class PaymentResult:
    """Result of a payment operation."""
    success: bool
    transaction_id: str | None
    status: PaymentStatus
    amount: float
    currency: str
    provider: str
    error_message: str | None = None
    timestamp: datetime | None = None


class PaymentProvider(ABC):
    """Base class for payment providers."""

    @abstractmethod
    async def initiate_payment(
        self, phone: str, amount: float, order_id: int, description: str
    ) -> PaymentResult:
        ...

    @abstractmethod
    async def check_status(self, transaction_id: str) -> PaymentResult:
        ...

    @abstractmethod
    async def refund(self, transaction_id: str, amount: float | None = None) -> PaymentResult:
        ...


class SyriaTelCashProvider(PaymentProvider):
    """SyriaTel Cash mobile money integration."""

    def __init__(self):
        self.api_key = settings.syriatel_cash_api_key
        self.base_url = "https://api.syriatel.cash/v1"  # Placeholder

    async def initiate_payment(
        self, phone: str, amount: float, order_id: int, description: str
    ) -> PaymentResult:
        """Send a payment request to customer's SyriaTel Cash wallet."""
        payload = {
            "merchant_key": self.api_key,
            "customer_phone": phone,
            "amount": amount,
            "currency": "SYP",
            "reference": f"NOOR-{order_id}",
            "description": description,
            "callback_url": f"{settings.app_url}/webhook/payment/syriatel",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/payment/request",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                data = response.json()

                if response.status_code == 200 and data.get("success"):
                    return PaymentResult(
                        success=True,
                        transaction_id=data["transaction_id"],
                        status=PaymentStatus.PENDING,
                        amount=amount,
                        currency="SYP",
                        provider="syriatel_cash",
                        timestamp=datetime.utcnow(),
                    )
                else:
                    return PaymentResult(
                        success=False,
                        transaction_id=None,
                        status=PaymentStatus.FAILED,
                        amount=amount,
                        currency="SYP",
                        provider="syriatel_cash",
                        error_message=data.get("error", "Payment request failed"),
                    )
        except httpx.HTTPError as e:
            return PaymentResult(
                success=False,
                transaction_id=None,
                status=PaymentStatus.FAILED,
                amount=amount,
                currency="SYP",
                provider="syriatel_cash",
                error_message=f"Connection error: {str(e)}",
            )

    async def check_status(self, transaction_id: str) -> PaymentResult:
        """Check payment status."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    f"{self.base_url}/payment/status/{transaction_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                data = response.json()

                status_map = {
                    "pending": PaymentStatus.PENDING,
                    "processing": PaymentStatus.PROCESSING,
                    "completed": PaymentStatus.COMPLETED,
                    "failed": PaymentStatus.FAILED,
                }

                return PaymentResult(
                    success=data.get("status") == "completed",
                    transaction_id=transaction_id,
                    status=status_map.get(data.get("status", ""), PaymentStatus.PENDING),
                    amount=data.get("amount", 0),
                    currency="SYP",
                    provider="syriatel_cash",
                )
        except httpx.HTTPError as e:
            return PaymentResult(
                success=False,
                transaction_id=transaction_id,
                status=PaymentStatus.PENDING,
                amount=0,
                currency="SYP",
                provider="syriatel_cash",
                error_message=str(e),
            )

    async def refund(self, transaction_id: str, amount: float | None = None) -> PaymentResult:
        """Refund a payment."""
        payload = {"transaction_id": transaction_id}
        if amount:
            payload["amount"] = amount

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/payment/refund",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                data = response.json()

                return PaymentResult(
                    success=data.get("success", False),
                    transaction_id=data.get("refund_id", transaction_id),
                    status=PaymentStatus.REFUNDED if data.get("success") else PaymentStatus.FAILED,
                    amount=amount or 0,
                    currency="SYP",
                    provider="syriatel_cash",
                )
        except httpx.HTTPError as e:
            return PaymentResult(
                success=False,
                transaction_id=transaction_id,
                status=PaymentStatus.FAILED,
                amount=amount or 0,
                currency="SYP",
                provider="syriatel_cash",
                error_message=str(e),
            )


class MTNCashProvider(PaymentProvider):
    """MTN Cash (MTN Mobile Money) integration."""

    def __init__(self):
        self.api_key = settings.mtn_cash_api_key
        self.base_url = "https://api.mtn.cash/v1"  # Placeholder

    async def initiate_payment(
        self, phone: str, amount: float, order_id: int, description: str
    ) -> PaymentResult:
        """Send a payment request to customer's MTN Cash wallet."""
        payload = {
            "api_key": self.api_key,
            "msisdn": phone,
            "amount": str(amount),
            "currency": "SYP",
            "external_id": f"NOOR-{order_id}",
            "note": description,
            "callback": f"{settings.app_url}/webhook/payment/mtn",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/collection/request",
                    json=payload,
                    headers={"X-API-Key": self.api_key},
                )
                data = response.json()

                if response.status_code in (200, 201, 202):
                    return PaymentResult(
                        success=True,
                        transaction_id=data.get("reference_id"),
                        status=PaymentStatus.PENDING,
                        amount=amount,
                        currency="SYP",
                        provider="mtn_cash",
                        timestamp=datetime.utcnow(),
                    )
                else:
                    return PaymentResult(
                        success=False,
                        transaction_id=None,
                        status=PaymentStatus.FAILED,
                        amount=amount,
                        currency="SYP",
                        provider="mtn_cash",
                        error_message=data.get("message", "Payment failed"),
                    )
        except httpx.HTTPError as e:
            return PaymentResult(
                success=False,
                transaction_id=None,
                status=PaymentStatus.FAILED,
                amount=amount,
                currency="SYP",
                provider="mtn_cash",
                error_message=str(e),
            )

    async def check_status(self, transaction_id: str) -> PaymentResult:
        """Check MTN Cash payment status."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    f"{self.base_url}/collection/{transaction_id}",
                    headers={"X-API-Key": self.api_key},
                )
                data = response.json()
                is_success = data.get("status") == "SUCCESSFUL"

                return PaymentResult(
                    success=is_success,
                    transaction_id=transaction_id,
                    status=PaymentStatus.COMPLETED if is_success else PaymentStatus.PENDING,
                    amount=float(data.get("amount", 0)),
                    currency="SYP",
                    provider="mtn_cash",
                )
        except httpx.HTTPError as e:
            return PaymentResult(
                success=False,
                transaction_id=transaction_id,
                status=PaymentStatus.PENDING,
                amount=0,
                currency="SYP",
                provider="mtn_cash",
                error_message=str(e),
            )

    async def refund(self, transaction_id: str, amount: float | None = None) -> PaymentResult:
        """Refund an MTN Cash payment via disbursement."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/disbursement/refund",
                    json={"reference_id": transaction_id, "amount": str(amount or 0)},
                    headers={"X-API-Key": self.api_key},
                )
                data = response.json()

                return PaymentResult(
                    success=data.get("status") == "SUCCESSFUL",
                    transaction_id=data.get("reference_id", transaction_id),
                    status=PaymentStatus.REFUNDED if data.get("status") == "SUCCESSFUL" else PaymentStatus.FAILED,
                    amount=amount or 0,
                    currency="SYP",
                    provider="mtn_cash",
                )
        except httpx.HTTPError as e:
            return PaymentResult(
                success=False,
                transaction_id=transaction_id,
                status=PaymentStatus.FAILED,
                amount=amount or 0,
                currency="SYP",
                provider="mtn_cash",
                error_message=str(e),
            )


class PaymentGateway:
    """Unified payment gateway that routes to the right provider."""

    def __init__(self):
        self.providers: dict[str, PaymentProvider] = {
            "syriatel_cash": SyriaTelCashProvider(),
            "mtn_cash": MTNCashProvider(),
        }

    async def process_payment(
        self,
        provider_name: str,
        phone: str,
        amount: float,
        order_id: int,
        description: str = "",
    ) -> PaymentResult:
        """Process a payment through the specified provider."""
        provider = self.providers.get(provider_name)
        if not provider:
            return PaymentResult(
                success=False,
                transaction_id=None,
                status=PaymentStatus.FAILED,
                amount=amount,
                currency="SYP",
                provider=provider_name,
                error_message=f"Unknown payment provider: {provider_name}",
            )

        if not description:
            description = f"Noor AI - طلبية #{order_id}"

        return await provider.initiate_payment(phone, amount, order_id, description)

    async def check_payment(self, provider_name: str, transaction_id: str) -> PaymentResult:
        """Check the status of a payment."""
        provider = self.providers.get(provider_name)
        if not provider:
            return PaymentResult(
                success=False,
                transaction_id=transaction_id,
                status=PaymentStatus.FAILED,
                amount=0,
                currency="SYP",
                provider=provider_name,
                error_message=f"Unknown provider: {provider_name}",
            )
        return await provider.check_status(transaction_id)

    def detect_provider(self, phone: str) -> str | None:
        """Auto-detect payment provider from phone number prefix.

        SyriaTel: 093X, 094X, 095X
        MTN:      096X, 098X
        """
        cleaned = phone.replace("+963", "0").replace(" ", "").replace("-", "")
        if cleaned.startswith(("093", "094", "095")):
            return "syriatel_cash"
        elif cleaned.startswith(("096", "098")):
            return "mtn_cash"
        return None
