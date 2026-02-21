"""
Account services — balance and statement.

Sync:  ``AccountService``      — attach to :class:`~clickpesa.client.ClickPesaClient`.
Async: ``AsyncAccountService`` — attach to :class:`~clickpesa.async_client.AsyncClickPesaClient`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import ClickPesaClient
    from ..async_client import AsyncClickPesaClient

_BASE = "/third-parties/account"


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

class AccountService:
    """Synchronous account information methods."""

    def __init__(self, client: "ClickPesaClient") -> None:
        self._c = client

    def get_balance(self) -> list[dict[str, Any]]:
        """
        Retrieve account balances for all active currencies.

        Returns:
            List of ``{"currency": "TZS", "balance": 12345.00}`` dicts.
        """
        return self._c.request("GET", f"{_BASE}/balance")

    def get_statement(
        self,
        currency: str = "TZS",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Fetch a transaction statement for a given currency.

        Args:
            currency:   ``"TZS"`` (default) or ``"USD"``.  Required by the API.
            start_date: Optional filter — ``YYYY-MM-DD`` or ``DD-MM-YYYY``.
            end_date:   Optional filter — ``YYYY-MM-DD`` or ``DD-MM-YYYY``.

        Returns:
            Dict with ``accountDetails`` and ``transactions`` list.
        """
        params: dict[str, Any] = {"currency": currency}
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date
        return self._c.request("GET", f"{_BASE}/statement", params=params)


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------

class AsyncAccountService:
    """Asynchronous account information methods (mirrors :class:`AccountService`)."""

    def __init__(self, client: "AsyncClickPesaClient") -> None:
        self._c = client

    async def get_balance(self) -> list[dict[str, Any]]:
        return await self._c.request("GET", f"{_BASE}/balance")

    async def get_statement(
        self,
        currency: str = "TZS",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"currency": currency}
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date
        return await self._c.request("GET", f"{_BASE}/statement", params=params)
