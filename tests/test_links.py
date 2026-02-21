"""
Tests for LinkService (sync): checkout and payout link generation.
"""

import json
import pytest
import respx
import httpx

SANDBOX = "https://api-sandbox.clickpesa.com"
AUTH_URL = f"{SANDBOX}/third-parties/generate-token"
CHECKOUT_URL = f"{SANDBOX}/third-parties/checkout-link/generate-checkout-url"
PAYOUT_URL = f"{SANDBOX}/third-parties/payout-link/generate-payout-url"


def _auth():
    return respx.post(AUTH_URL).mock(
        return_value=httpx.Response(200, json={"token": "Bearer tok"})
    )


@respx.mock
def test_generate_checkout_with_total_price(client):
    """Checkout link is generated with totalPrice."""
    _auth()
    respx.post(CHECKOUT_URL).mock(
        return_value=httpx.Response(200, json={"checkoutLink": "https://checkout.clickpesa.com/x"})
    )
    result = client.links.generate_checkout(
        order_id="CH001",
        order_currency="TZS",
        total_price="5000",
    )
    assert result["checkoutLink"].startswith("https://")

    body = json.loads(respx.calls.last.request.content)
    assert body["totalPrice"] == "5000"
    assert body["orderCurrency"] == "TZS"
    assert "orderItems" not in body


@respx.mock
def test_generate_checkout_with_order_items(client):
    """Checkout link is generated with orderItems."""
    _auth()
    respx.post(CHECKOUT_URL).mock(
        return_value=httpx.Response(200, json={"checkoutLink": "https://checkout.clickpesa.com/y"})
    )
    items = [{"name": "Widget", "price": "2500", "quantity": 2}]
    client.links.generate_checkout(order_id="CH002", order_currency="USD", order_items=items)

    body = json.loads(respx.calls.last.request.content)
    assert body["orderItems"] == items
    assert "totalPrice" not in body


def test_generate_checkout_requires_price_or_items(client):
    """Providing neither total_price nor order_items raises ValueError."""
    with pytest.raises(ValueError, match="total_price.*order_items"):
        client.links.generate_checkout(order_id="CH003", order_currency="TZS")


def test_generate_checkout_rejects_both_price_and_items(client):
    """Providing both total_price and order_items raises ValueError."""
    with pytest.raises(ValueError, match="not both"):
        client.links.generate_checkout(
            order_id="CH004",
            order_currency="TZS",
            total_price="1000",
            order_items=[{"name": "x", "price": "1000", "quantity": 1}],
        )


@respx.mock
def test_generate_payout_link(client):
    """Payout link is generated with correct payload."""
    _auth()
    respx.post(PAYOUT_URL).mock(
        return_value=httpx.Response(200, json={"payoutLink": "https://payout.clickpesa.com/z"})
    )
    result = client.links.generate_payout(amount="10000", order_id="PO001")
    assert "payoutLink" in result

    body = json.loads(respx.calls.last.request.content)
    assert body["amount"] == "10000"
    assert body["orderReference"] == "PO001"
