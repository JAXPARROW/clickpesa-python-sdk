"""
Payment collection services — USSD Push and Card Payments.

Sync:  ``PaymentService``      — attach to :class:`~clickpesa.client.ClickPesaClient`.
Async: ``AsyncPaymentService`` — attach to :class:`~clickpesa.async_client.AsyncClickPesaClient`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import ClickPesaClient
    from ..async_client import AsyncClickPesaClient

_BASE = "/third-parties/payments"


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

class PaymentService:
    """Synchronous payment collection methods."""

    def __init__(self, client: "ClickPesaClient") -> None:
        self._c = client

    def preview_ussd_push(
        self,
        amount: str,
        order_id: str,
        phone: str | None = None,
        currency: str = "TZS",
        fetch_sender_details: bool = False,
    ) -> dict[str, Any]:
        """
        Validate a USSD Push request and check available payment methods.

        Args:
            amount:               Payment amount.
            order_id:             Unique alphanumeric order reference.
            phone:                Customer phone with country code, no ``+``
                                  (e.g. ``"255712345678"``).  Optional.
            currency:             Must be ``"TZS"`` (default).
            fetch_sender_details: When ``True`` the response includes the
                                  sender's name, number and provider.

        Returns:
            Dict with ``activeMethods`` list and optional ``sender`` object.
        """
        payload: dict[str, Any] = {
            "amount": str(amount),
            "currency": currency,
            "orderReference": order_id,
            "fetchSenderDetails": fetch_sender_details,
        }
        if phone is not None:
            payload["phoneNumber"] = phone
        return self._c.request("POST", f"{_BASE}/preview-ussd-push-request", json=payload)

    def initiate_ussd_push(
        self,
        amount: str,
        phone: str,
        order_id: str,
        currency: str = "TZS",
    ) -> dict[str, Any]:
        """
        Trigger the USSD PIN prompt on the customer's phone.

        Args:
            amount:    Payment amount.
            phone:     Customer phone with country code, no ``+``.
            order_id:  Unique alphanumeric order reference.
            currency:  Must be ``"TZS"`` (default).

        Returns:
            Transaction object with ``id``, ``status``, ``channel``, etc.
        """
        payload: dict[str, Any] = {
            "amount": str(amount),
            "phoneNumber": phone,
            "currency": currency,
            "orderReference": order_id,
        }
        return self._c.request("POST", f"{_BASE}/initiate-ussd-push-request", json=payload)

    def preview_card(
        self,
        amount: str,
        order_id: str,
        currency: str = "USD",
    ) -> dict[str, Any]:
        """
        Validate card payment details and check available card methods.

        Args:
            amount:    Payment amount.
            order_id:  Unique alphanumeric order reference.
            currency:  Must be ``"USD"`` (default).

        Returns:
            Dict with ``activeMethods`` list (VISA / MASTER CARD).
        """
        payload: dict[str, Any] = {
            "amount": str(amount),
            "currency": currency,
            "orderReference": order_id,
        }
        return self._c.request("POST", f"{_BASE}/preview-card-payment", json=payload)

    def initiate_card(
        self,
        amount: str,
        order_id: str,
        customer: dict[str, str],
        currency: str = "USD",
    ) -> dict[str, Any]:
        """
        Generate a hosted card payment link for the customer.

        Args:
            amount:    Payment amount.
            order_id:  Unique alphanumeric order reference.
            customer:  Either ``{"id": "…"}`` **or**
                       ``{"fullName": "…", "email": "…", "phoneNumber": "…"}``.
            currency:  Must be ``"USD"`` (default).

        Returns:
            Dict with ``cardPaymentLink`` and ``clientId``.
        """
        payload: dict[str, Any] = {
            "amount": str(amount),
            "orderReference": order_id,
            "currency": currency,
            "customer": customer,
        }
        return self._c.request("POST", f"{_BASE}/initiate-card-payment", json=payload)

    def get_status(self, order_reference: str) -> list[dict[str, Any]]:
        """
        Query the status of a payment by its order reference.

        Returns:
            List of payment objects matching the reference.
        """
        return self._c.request("GET", f"{_BASE}/{order_reference}")

    def list_all(self, **filters: Any) -> dict[str, Any]:
        """
        Query all payments with optional filtering and pagination.

        Keyword Args:
            startDate (str):          ``YYYY-MM-DD`` or ``DD-MM-YYYY``.
            endDate (str):            ``YYYY-MM-DD`` or ``DD-MM-YYYY``.
            status (str):             ``SUCCESS`` | ``SETTLED`` | ``PROCESSING``
                                      | ``PENDING`` | ``FAILED``.
            collectedCurrency (str):  e.g. ``"TZS"`` or ``"USD"``.
            channel (str):            Payment channel identifier.
            orderReference (str):     Filter by specific reference.
            sortBy (str):             Any response field (default ``createdAt``).
            orderBy (str):            ``ASC`` or ``DESC`` (default ``DESC``).
            skip (int):               Pagination offset (default ``0``).
            limit (int):              Page size (default ``20``).

        Returns:
            Dict with ``data`` (list) and ``totalCount`` (int).
        """
        return self._c.request("GET", f"{_BASE}/all", params=filters)


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------

class AsyncPaymentService:
    """Asynchronous payment collection methods (mirrors :class:`PaymentService`)."""

    def __init__(self, client: "AsyncClickPesaClient") -> None:
        self._c = client

    async def preview_ussd_push(
        self,
        amount: str,
        order_id: str,
        phone: str | None = None,
        currency: str = "TZS",
        fetch_sender_details: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "amount": str(amount),
            "currency": currency,
            "orderReference": order_id,
            "fetchSenderDetails": fetch_sender_details,
        }
        if phone is not None:
            payload["phoneNumber"] = phone
        return await self._c.request("POST", f"{_BASE}/preview-ussd-push-request", json=payload)

    async def initiate_ussd_push(
        self,
        amount: str,
        phone: str,
        order_id: str,
        currency: str = "TZS",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "amount": str(amount),
            "phoneNumber": phone,
            "currency": currency,
            "orderReference": order_id,
        }
        return await self._c.request("POST", f"{_BASE}/initiate-ussd-push-request", json=payload)

    async def preview_card(
        self,
        amount: str,
        order_id: str,
        currency: str = "USD",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "amount": str(amount),
            "currency": currency,
            "orderReference": order_id,
        }
        return await self._c.request("POST", f"{_BASE}/preview-card-payment", json=payload)

    async def initiate_card(
        self,
        amount: str,
        order_id: str,
        customer: dict[str, str],
        currency: str = "USD",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "amount": str(amount),
            "orderReference": order_id,
            "currency": currency,
            "customer": customer,
        }
        return await self._c.request("POST", f"{_BASE}/initiate-card-payment", json=payload)

    async def get_status(self, order_reference: str) -> list[dict[str, Any]]:
        return await self._c.request("GET", f"{_BASE}/{order_reference}")

    async def list_all(self, **filters: Any) -> dict[str, Any]:
        return await self._c.request("GET", f"{_BASE}/all", params=filters)
