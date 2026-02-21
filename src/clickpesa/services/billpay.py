"""
BillPay collection services — Order and Customer Control Numbers.

Sync:  ``BillPayService``      — attach to :class:`~clickpesa.client.ClickPesaClient`.
Async: ``AsyncBillPayService`` — attach to :class:`~clickpesa.async_client.AsyncClickPesaClient`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from ..client import ClickPesaClient
    from ..async_client import AsyncClickPesaClient

_BASE = "/third-parties/billpay"
_BULK_LIMIT = 50

BillPaymentMode = Literal["ALLOW_PARTIAL_AND_OVER_PAYMENT", "EXACT"]
BillStatus = Literal["ACTIVE", "INACTIVE"]


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

class BillPayService:
    """Synchronous BillPay control-number management."""

    def __init__(self, client: "ClickPesaClient") -> None:
        self._c = client

    def create_order_control_number(
        self,
        bill_reference: str | None = None,
        amount: float | None = None,
        description: str | None = None,
        payment_mode: BillPaymentMode | None = None,
    ) -> dict[str, Any]:
        """
        Generate a one-time order control number.

        All fields are optional.  If ``bill_reference`` is omitted the API
        auto-generates one.  ``payment_mode`` is only applied when ``amount``
        is also set.

        Args:
            bill_reference: Custom alphanumeric reference (must be unique).
            amount:         Bill amount.
            description:    Human-readable bill description.
            payment_mode:   ``"ALLOW_PARTIAL_AND_OVER_PAYMENT"`` (default) or ``"EXACT"``.

        Returns:
            Dict with ``billPayNumber``, ``billDescription``, ``billAmount``, etc.
        """
        payload: dict[str, Any] = {}
        if bill_reference is not None:
            payload["billReference"] = bill_reference
        if amount is not None:
            payload["billAmount"] = amount
        if description is not None:
            payload["billDescription"] = description
        if payment_mode is not None:
            payload["billPaymentMode"] = payment_mode
        return self._c.request("POST", f"{_BASE}/create-order-control-number", json=payload)

    def create_customer_control_number(
        self,
        customer_name: str,
        phone: str | None = None,
        email: str | None = None,
        bill_reference: str | None = None,
        amount: float | None = None,
        description: str | None = None,
        payment_mode: BillPaymentMode | None = None,
    ) -> dict[str, Any]:
        """
        Generate a persistent control number tied to a specific customer.

        Either ``phone`` or ``email`` (or both) must be supplied.

        Args:
            customer_name:  Customer's full name.
            phone:          Phone with country code, no ``+`` (e.g. ``"255712345678"``).
            email:          Customer email address.
            bill_reference: Custom alphanumeric reference (must be unique).
            amount:         Bill amount.
            description:    Human-readable bill description.
            payment_mode:   ``"ALLOW_PARTIAL_AND_OVER_PAYMENT"`` (default) or ``"EXACT"``.

        Returns:
            Dict with ``billPayNumber``, ``billCustomerName``, ``billAmount``, etc.
        """
        if phone is None and email is None:
            raise ValueError("At least one of 'phone' or 'email' must be provided.")

        payload: dict[str, Any] = {"customerName": customer_name}
        if phone is not None:
            payload["customerPhone"] = phone
        if email is not None:
            payload["customerEmail"] = email
        if bill_reference is not None:
            payload["billReference"] = bill_reference
        if amount is not None:
            payload["billAmount"] = amount
        if description is not None:
            payload["billDescription"] = description
        if payment_mode is not None:
            payload["billPaymentMode"] = payment_mode
        return self._c.request("POST", f"{_BASE}/create-customer-control-number", json=payload)

    def bulk_create_order_numbers(
        self,
        control_numbers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Bulk-create up to 50 order control numbers in a single request.

        Each item may contain: ``billReference``, ``billAmount``,
        ``billDescription``, ``billPaymentMode``.

        Args:
            control_numbers: List of order dicts (1–50 items).

        Returns:
            Dict with ``billPayNumbers``, ``created``, ``failed``, and
            optional ``errors`` list.

        Raises:
            ValueError: If the list exceeds 50 items or is empty.
        """
        if not control_numbers:
            raise ValueError("control_numbers must contain at least 1 item.")
        if len(control_numbers) > _BULK_LIMIT:
            raise ValueError(f"ClickPesa bulk limit is {_BULK_LIMIT} items per request.")
        return self._c.request(
            "POST",
            f"{_BASE}/bulk-create-order-control-numbers",
            json={"controlNumbers": control_numbers},
        )

    def bulk_create_customer_numbers(
        self,
        control_numbers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Bulk-create up to 50 customer control numbers in a single request.

        Each item must contain ``customerName`` and at least one of
        ``customerPhone`` / ``customerEmail``.  Optional fields:
        ``billReference``, ``billAmount``, ``billDescription``, ``billPaymentMode``.

        Args:
            control_numbers: List of customer dicts (1–50 items).

        Returns:
            Dict with ``billPayNumbers``, ``created``, ``failed``, and
            optional ``errors`` list.

        Raises:
            ValueError: If the list exceeds 50 items or is empty.
        """
        if not control_numbers:
            raise ValueError("control_numbers must contain at least 1 item.")
        if len(control_numbers) > _BULK_LIMIT:
            raise ValueError(f"ClickPesa bulk limit is {_BULK_LIMIT} items per request.")
        return self._c.request(
            "POST",
            f"{_BASE}/bulk-create-customer-control-numbers",
            json={"controlNumbers": control_numbers},
        )

    def get_details(self, bill_pay_number: str) -> dict[str, Any]:
        """
        Query details of a specific control number.

        Returns:
            Dict with ``billPayNumber``, ``billDescription``, ``billAmount``,
            ``billPaymentMode``, and ``billCustomerName``.
        """
        return self._c.request("GET", f"{_BASE}/{bill_pay_number}")

    def update_reference(
        self,
        bill_pay_number: str,
        amount: float | None = None,
        description: str | None = None,
        status: BillStatus | None = None,
        payment_mode: BillPaymentMode | None = None,
    ) -> dict[str, Any]:
        """
        Partially update a BillPay reference.

        At least one argument besides ``bill_pay_number`` must be provided.

        Args:
            bill_pay_number: The BillPay number to update.
            amount:          New bill amount (positive, max 2 decimal places).
            description:     New description (max 500 characters).
            status:          ``"ACTIVE"`` or ``"INACTIVE"``.
            payment_mode:    ``"ALLOW_PARTIAL_AND_OVER_PAYMENT"`` or ``"EXACT"``.

        Returns:
            Updated BillPay object.
        """
        data: dict[str, Any] = {}
        if amount is not None:
            data["billAmount"] = amount
        if description is not None:
            data["billDescription"] = description
        if status is not None:
            data["billStatus"] = status
        if payment_mode is not None:
            data["billPaymentMode"] = payment_mode
        if not data:
            raise ValueError("At least one field must be provided to update.")
        return self._c.request("PATCH", f"{_BASE}/{bill_pay_number}", json=data)

    def update_status(self, bill_pay_number: str, status: BillStatus) -> dict[str, Any]:
        """
        Convenience method to activate or deactivate a control number.

        Args:
            bill_pay_number: The BillPay number to update.
            status:          ``"ACTIVE"`` or ``"INACTIVE"``.
        """
        return self.update_reference(bill_pay_number, status=status)


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------

class AsyncBillPayService:
    """Asynchronous BillPay control-number management (mirrors :class:`BillPayService`)."""

    def __init__(self, client: "AsyncClickPesaClient") -> None:
        self._c = client

    async def create_order_control_number(
        self,
        bill_reference: str | None = None,
        amount: float | None = None,
        description: str | None = None,
        payment_mode: BillPaymentMode | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if bill_reference is not None:
            payload["billReference"] = bill_reference
        if amount is not None:
            payload["billAmount"] = amount
        if description is not None:
            payload["billDescription"] = description
        if payment_mode is not None:
            payload["billPaymentMode"] = payment_mode
        return await self._c.request("POST", f"{_BASE}/create-order-control-number", json=payload)

    async def create_customer_control_number(
        self,
        customer_name: str,
        phone: str | None = None,
        email: str | None = None,
        bill_reference: str | None = None,
        amount: float | None = None,
        description: str | None = None,
        payment_mode: BillPaymentMode | None = None,
    ) -> dict[str, Any]:
        if phone is None and email is None:
            raise ValueError("At least one of 'phone' or 'email' must be provided.")
        payload: dict[str, Any] = {"customerName": customer_name}
        if phone is not None:
            payload["customerPhone"] = phone
        if email is not None:
            payload["customerEmail"] = email
        if bill_reference is not None:
            payload["billReference"] = bill_reference
        if amount is not None:
            payload["billAmount"] = amount
        if description is not None:
            payload["billDescription"] = description
        if payment_mode is not None:
            payload["billPaymentMode"] = payment_mode
        return await self._c.request(
            "POST", f"{_BASE}/create-customer-control-number", json=payload
        )

    async def bulk_create_order_numbers(
        self,
        control_numbers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not control_numbers:
            raise ValueError("control_numbers must contain at least 1 item.")
        if len(control_numbers) > _BULK_LIMIT:
            raise ValueError(f"ClickPesa bulk limit is {_BULK_LIMIT} items per request.")
        return await self._c.request(
            "POST",
            f"{_BASE}/bulk-create-order-control-numbers",
            json={"controlNumbers": control_numbers},
        )

    async def bulk_create_customer_numbers(
        self,
        control_numbers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not control_numbers:
            raise ValueError("control_numbers must contain at least 1 item.")
        if len(control_numbers) > _BULK_LIMIT:
            raise ValueError(f"ClickPesa bulk limit is {_BULK_LIMIT} items per request.")
        return await self._c.request(
            "POST",
            f"{_BASE}/bulk-create-customer-control-numbers",
            json={"controlNumbers": control_numbers},
        )

    async def get_details(self, bill_pay_number: str) -> dict[str, Any]:
        return await self._c.request("GET", f"{_BASE}/{bill_pay_number}")

    async def update_reference(
        self,
        bill_pay_number: str,
        amount: float | None = None,
        description: str | None = None,
        status: BillStatus | None = None,
        payment_mode: BillPaymentMode | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if amount is not None:
            data["billAmount"] = amount
        if description is not None:
            data["billDescription"] = description
        if status is not None:
            data["billStatus"] = status
        if payment_mode is not None:
            data["billPaymentMode"] = payment_mode
        if not data:
            raise ValueError("At least one field must be provided to update.")
        return await self._c.request("PATCH", f"{_BASE}/{bill_pay_number}", json=data)

    async def update_status(self, bill_pay_number: str, status: BillStatus) -> dict[str, Any]:
        return await self.update_reference(bill_pay_number, status=status)
