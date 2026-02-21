"""
Hosted link generation services — Checkout and Payout Links.

Sync:  ``LinkService``      — attach to :class:`~clickpesa.client.ClickPesaClient`.
Async: ``AsyncLinkService`` — attach to :class:`~clickpesa.async_client.AsyncClickPesaClient`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from ..client import ClickPesaClient
    from ..async_client import AsyncClickPesaClient

_CHECKOUT = "/third-parties/checkout-link/generate-checkout-url"
_PAYOUT = "/third-parties/payout-link/generate-payout-url"

OrderCurrency = Literal["TZS", "USD"]


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

class LinkService:
    """Synchronous hosted-link generation methods."""

    def __init__(self, client: "ClickPesaClient") -> None:
        self._c = client

    def generate_checkout(
        self,
        order_id: str,
        order_currency: OrderCurrency,
        total_price: str | None = None,
        order_items: list[dict[str, Any]] | None = None,
        customer_name: str | None = None,
        customer_email: str | None = None,
        customer_phone: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a hosted checkout payment page.

        Supply **either** ``total_price`` **or** ``order_items`` — not both.

        Args:
            order_id:       Unique alphanumeric order reference.
            order_currency: ``"TZS"`` or ``"USD"``.
            total_price:    Order total as a string (Option 1).
            order_items:    List of ``{"name": …, "price": …, "quantity": …}``
                            dicts (Option 2).
            customer_name:  Pre-fill customer name on the checkout page.
            customer_email: Pre-fill customer email.
            customer_phone: Customer phone with country code, no ``+``.
            description:    Order description shown on the checkout page.

        Returns:
            Dict with ``checkoutLink`` (URL string) and ``clientId``.

        Raises:
            ValueError: If neither or both of ``total_price`` / ``order_items``
                        are provided.
        """
        if total_price is None and order_items is None:
            raise ValueError("Provide either 'total_price' or 'order_items'.")
        if total_price is not None and order_items is not None:
            raise ValueError("Provide either 'total_price' or 'order_items', not both.")

        payload: dict[str, Any] = {
            "orderReference": order_id,
            "orderCurrency": order_currency,
        }
        if total_price is not None:
            payload["totalPrice"] = str(total_price)
        if order_items is not None:
            payload["orderItems"] = order_items
        if customer_name is not None:
            payload["customerName"] = customer_name
        if customer_email is not None:
            payload["customerEmail"] = customer_email
        if customer_phone is not None:
            payload["customerPhone"] = customer_phone
        if description is not None:
            payload["description"] = description

        return self._c.request("POST", _CHECKOUT, json=payload)

    def generate_payout(
        self,
        amount: str,
        order_id: str,
    ) -> dict[str, Any]:
        """
        Generate a hosted payout link.

        The recipient uses the link to enter their own bank / mobile-money
        details without you needing to collect them yourself.

        Args:
            amount:   Payout amount.
            order_id: Unique alphanumeric order reference.

        Returns:
            Dict with ``payoutLink`` (URL string) and ``clientId``.
        """
        payload: dict[str, Any] = {
            "amount": str(amount),
            "orderReference": order_id,
        }
        return self._c.request("POST", _PAYOUT, json=payload)


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------

class AsyncLinkService:
    """Asynchronous hosted-link generation methods (mirrors :class:`LinkService`)."""

    def __init__(self, client: "AsyncClickPesaClient") -> None:
        self._c = client

    async def generate_checkout(
        self,
        order_id: str,
        order_currency: OrderCurrency,
        total_price: str | None = None,
        order_items: list[dict[str, Any]] | None = None,
        customer_name: str | None = None,
        customer_email: str | None = None,
        customer_phone: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        if total_price is None and order_items is None:
            raise ValueError("Provide either 'total_price' or 'order_items'.")
        if total_price is not None and order_items is not None:
            raise ValueError("Provide either 'total_price' or 'order_items', not both.")

        payload: dict[str, Any] = {
            "orderReference": order_id,
            "orderCurrency": order_currency,
        }
        if total_price is not None:
            payload["totalPrice"] = str(total_price)
        if order_items is not None:
            payload["orderItems"] = order_items
        if customer_name is not None:
            payload["customerName"] = customer_name
        if customer_email is not None:
            payload["customerEmail"] = customer_email
        if customer_phone is not None:
            payload["customerPhone"] = customer_phone
        if description is not None:
            payload["description"] = description

        return await self._c.request("POST", _CHECKOUT, json=payload)

    async def generate_payout(
        self,
        amount: str,
        order_id: str,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "amount": str(amount),
            "orderReference": order_id,
        }
        return await self._c.request("POST", _PAYOUT, json=payload)
