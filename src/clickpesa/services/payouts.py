"""
Disbursement services — Mobile Money and Bank Payouts.

Sync:  ``PayoutService``      — attach to :class:`~clickpesa.client.ClickPesaClient`.
Async: ``AsyncPayoutService`` — attach to :class:`~clickpesa.async_client.AsyncClickPesaClient`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import ClickPesaClient
    from ..async_client import AsyncClickPesaClient

_BASE = "/third-parties/payouts"
_BANKS = "/third-parties/list/banks"


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

class PayoutService:
    """Synchronous disbursement methods."""

    def __init__(self, client: "ClickPesaClient") -> None:
        self._c = client

    # --- Mobile Money ---

    def preview_mobile_money(
        self,
        amount: float,
        phone: str,
        order_id: str,
        currency: str = "TZS",
    ) -> dict[str, Any]:
        """
        Check fees and account balance before disbursing to a mobile wallet.

        Args:
            amount:    Payout amount.
            phone:     Recipient phone with country code, no ``+``.
            order_id:  Unique alphanumeric order reference.
            currency:  Source currency — ``"TZS"`` or ``"USD"`` (default ``"TZS"``).
                       Recipient always receives funds in TZS.

        Returns:
            Preview dict with ``amount``, ``balance``, ``fee``, ``receiver``, etc.
        """
        payload: dict[str, Any] = {
            "amount": amount,
            "phoneNumber": phone,
            "currency": currency,
            "orderReference": order_id,
        }
        return self._c.request("POST", f"{_BASE}/preview-mobile-money-payout", json=payload)

    def create_mobile_money(
        self,
        amount: float,
        phone: str,
        order_id: str,
        currency: str = "TZS",
    ) -> dict[str, Any]:
        """
        Disburse funds to a mobile money wallet.

        Args:
            amount:    Payout amount.
            phone:     Recipient phone with country code, no ``+``.
            order_id:  Unique alphanumeric order reference.
            currency:  Source currency — ``"TZS"`` or ``"USD"`` (default ``"TZS"``).

        Returns:
            Transaction object with ``id``, ``status``, ``beneficiary``, etc.
        """
        payload: dict[str, Any] = {
            "amount": amount,
            "phoneNumber": phone,
            "currency": currency,
            "orderReference": order_id,
        }
        return self._c.request("POST", f"{_BASE}/create-mobile-money-payout", json=payload)

    # --- Bank Payouts ---

    def preview_bank(
        self,
        amount: float,
        account_number: str,
        bic: str,
        order_id: str,
        transfer_type: str = "ACH",
        currency: str = "TZS",
        account_currency: str = "TZS",
    ) -> dict[str, Any]:
        """
        Validate bank details and check fees before an ACH / RTGS transfer.

        Args:
            amount:           Payout amount.
            account_number:   Beneficiary bank account number.
            bic:              Bank identifier code — fetch via :meth:`get_banks`.
            order_id:         Unique alphanumeric order reference.
            transfer_type:    ``"ACH"`` (default) or ``"RTGS"``.
            currency:         Source currency — ``"TZS"`` or ``"USD"`` (default ``"TZS"``).
            account_currency: Receiving currency — currently only ``"TZS"`` (default).

        Returns:
            Preview dict with ``amount``, ``balance``, ``fee``, ``receiver``, etc.
        """
        payload: dict[str, Any] = {
            "amount": amount,
            "accountNumber": account_number,
            "bic": bic,
            "orderReference": order_id,
            "transferType": transfer_type,
            "currency": currency,
            "accountCurrency": account_currency,
        }
        return self._c.request("POST", f"{_BASE}/preview-bank-payout", json=payload)

    def create_bank(
        self,
        amount: float,
        account_number: str,
        account_name: str,
        bic: str,
        order_id: str,
        transfer_type: str = "ACH",
        currency: str = "TZS",
        account_currency: str = "TZS",
    ) -> dict[str, Any]:
        """
        Disburse funds to a bank account.

        Args:
            amount:           Payout amount.
            account_number:   Beneficiary bank account number.
            account_name:     Beneficiary name as registered with the bank.
            bic:              Bank identifier code — fetch via :meth:`get_banks`.
            order_id:         Unique alphanumeric order reference.
            transfer_type:    ``"ACH"`` (default) or ``"RTGS"``.
            currency:         Source currency — ``"TZS"`` or ``"USD"`` (default ``"TZS"``).
            account_currency: Receiving currency — currently only ``"TZS"`` (default).

        Returns:
            Transaction object with ``id``, ``status``, ``beneficiary``, etc.
        """
        payload: dict[str, Any] = {
            "amount": amount,
            "accountNumber": account_number,
            "accountName": account_name,
            "bic": bic,
            "orderReference": order_id,
            "transferType": transfer_type,
            "currency": currency,
            "accountCurrency": account_currency,
        }
        return self._c.request("POST", f"{_BASE}/create-bank-payout", json=payload)

    # --- Utilities ---

    def get_banks(self) -> list[dict[str, Any]]:
        """
        Fetch the list of supported banks and their BIC codes.

        Returns:
            List of ``{"name": "…", "bic": "…"}`` dicts.
        """
        return self._c.request("GET", _BANKS)

    def get_status(self, order_reference: str) -> list[dict[str, Any]]:
        """
        Query the status of a payout by its order reference.

        Returns:
            List of payout objects matching the reference.
        """
        return self._c.request("GET", f"{_BASE}/{order_reference}")

    def list_all(self, **filters: Any) -> dict[str, Any]:
        """
        Query payout history with optional filtering and pagination.

        Keyword Args:
            startDate (str):      ``YYYY-MM-DD`` or ``DD-MM-YYYY``.
            endDate (str):        ``YYYY-MM-DD`` or ``DD-MM-YYYY``.
            channel (str):        ``"BANK TRANSFER"`` | ``"MOBILE MONEY"``.
            currency (str):       e.g. ``"TZS"`` or ``"USD"``.
            orderReference (str): Filter by specific reference.
            status (str):         ``SUCCESS`` | ``PROCESSING`` | ``PENDING``
                                  | ``FAILED`` | ``REFUNDED`` | ``REVERSED``.
            transferType (str):   ``"ACH"`` | ``"RTGS"``.
            sortBy (str):         Any response field (default ``createdAt``).
            orderBy (str):        ``ASC`` or ``DESC`` (default ``DESC``).
            skip (int):           Pagination offset (default ``0``).
            limit (int):          Page size (default ``20``).

        Returns:
            Dict with ``data`` (list) and ``totalCount`` (int).
        """
        return self._c.request("GET", f"{_BASE}/all", params=filters)


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------

class AsyncPayoutService:
    """Asynchronous disbursement methods (mirrors :class:`PayoutService`)."""

    def __init__(self, client: "AsyncClickPesaClient") -> None:
        self._c = client

    async def preview_mobile_money(
        self,
        amount: float,
        phone: str,
        order_id: str,
        currency: str = "TZS",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "amount": amount,
            "phoneNumber": phone,
            "currency": currency,
            "orderReference": order_id,
        }
        return await self._c.request("POST", f"{_BASE}/preview-mobile-money-payout", json=payload)

    async def create_mobile_money(
        self,
        amount: float,
        phone: str,
        order_id: str,
        currency: str = "TZS",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "amount": amount,
            "phoneNumber": phone,
            "currency": currency,
            "orderReference": order_id,
        }
        return await self._c.request("POST", f"{_BASE}/create-mobile-money-payout", json=payload)

    async def preview_bank(
        self,
        amount: float,
        account_number: str,
        bic: str,
        order_id: str,
        transfer_type: str = "ACH",
        currency: str = "TZS",
        account_currency: str = "TZS",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "amount": amount,
            "accountNumber": account_number,
            "bic": bic,
            "orderReference": order_id,
            "transferType": transfer_type,
            "currency": currency,
            "accountCurrency": account_currency,
        }
        return await self._c.request("POST", f"{_BASE}/preview-bank-payout", json=payload)

    async def create_bank(
        self,
        amount: float,
        account_number: str,
        account_name: str,
        bic: str,
        order_id: str,
        transfer_type: str = "ACH",
        currency: str = "TZS",
        account_currency: str = "TZS",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "amount": amount,
            "accountNumber": account_number,
            "accountName": account_name,
            "bic": bic,
            "orderReference": order_id,
            "transferType": transfer_type,
            "currency": currency,
            "accountCurrency": account_currency,
        }
        return await self._c.request("POST", f"{_BASE}/create-bank-payout", json=payload)

    async def get_banks(self) -> list[dict[str, Any]]:
        return await self._c.request("GET", _BANKS)

    async def get_status(self, order_reference: str) -> list[dict[str, Any]]:
        return await self._c.request("GET", f"{_BASE}/{order_reference}")

    async def list_all(self, **filters: Any) -> dict[str, Any]:
        return await self._c.request("GET", f"{_BASE}/all", params=filters)
