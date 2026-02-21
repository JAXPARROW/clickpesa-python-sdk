"""
Exchange rate services.

Sync:  ``ExchangeService``      — attach to :class:`~clickpesa.client.ClickPesaClient`.
Async: ``AsyncExchangeService`` — attach to :class:`~clickpesa.async_client.AsyncClickPesaClient`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import ClickPesaClient
    from ..async_client import AsyncClickPesaClient

_ENDPOINT = "/third-parties/exchange-rates/all"


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

class ExchangeService:
    """Synchronous exchange rate methods."""

    def __init__(self, client: "ClickPesaClient") -> None:
        self._c = client

    def get_rates(
        self,
        source: str | None = None,
        target: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch the latest exchange rates.

        Args:
            source: ISO 4217 source currency code (e.g. ``"USD"``).
                    When omitted all available source currencies are returned.
            target: ISO 4217 target currency code (e.g. ``"TZS"``).
                    When omitted all available target currencies are returned.

        Returns:
            List of ``{"source": "…", "target": "…", "rate": 2510, "date": "…"}`` dicts.
        """
        params: dict[str, Any] = {}
        if source is not None:
            params["source"] = source
        if target is not None:
            params["target"] = target
        return self._c.request("GET", _ENDPOINT, params=params)


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------

class AsyncExchangeService:
    """Asynchronous exchange rate methods (mirrors :class:`ExchangeService`)."""

    def __init__(self, client: "AsyncClickPesaClient") -> None:
        self._c = client

    async def get_rates(
        self,
        source: str | None = None,
        target: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if source is not None:
            params["source"] = source
        if target is not None:
            params["target"] = target
        return await self._c.request("GET", _ENDPOINT, params=params)
