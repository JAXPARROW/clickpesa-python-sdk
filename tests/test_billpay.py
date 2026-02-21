"""
Tests for BillPayService (sync): control number creation, bulk, update, validation.
"""

import pytest
import respx
import httpx

from clickpesa.exceptions import ConflictError

SANDBOX = "https://api-sandbox.clickpesa.com"
AUTH_URL = f"{SANDBOX}/third-parties/generate-token"
BILLPAY_BASE = f"{SANDBOX}/third-parties/billpay"


def _auth():
    return respx.post(AUTH_URL).mock(
        return_value=httpx.Response(200, json={"token": "Bearer tok"})
    )


@respx.mock
def test_create_order_control_number_all_optional(client):
    """Creating an order CN with no args sends an empty body (all fields optional)."""
    _auth()
    respx.post(f"{BILLPAY_BASE}/create-order-control-number").mock(
        return_value=httpx.Response(200, json={"billPayNumber": "BP001"})
    )
    result = client.billpay.create_order_control_number()
    assert result["billPayNumber"] == "BP001"


@respx.mock
def test_create_order_control_number_with_fields(client):
    """BillPay order CN includes amount and payment mode when provided."""
    import json

    _auth()
    respx.post(f"{BILLPAY_BASE}/create-order-control-number").mock(
        return_value=httpx.Response(200, json={"billPayNumber": "BP002"})
    )
    client.billpay.create_order_control_number(
        amount=10000, description="Water Bill", payment_mode="EXACT"
    )
    body = json.loads(respx.calls.last.request.content)
    assert body["billAmount"] == 10000
    assert body["billPaymentMode"] == "EXACT"
    assert body["billDescription"] == "Water Bill"


@respx.mock
def test_create_customer_control_number_requires_phone_or_email(client):
    """Omitting both phone and email raises ValueError locally (no network call)."""
    with pytest.raises(ValueError, match="phone.*email"):
        client.billpay.create_customer_control_number(customer_name="John Doe")


@respx.mock
def test_bulk_create_order_numbers_enforces_limit(client):
    """Passing more than 50 items raises ValueError without a network call."""
    items = [{"billAmount": 100}] * 51
    with pytest.raises(ValueError, match="50"):
        client.billpay.bulk_create_order_numbers(items)


@respx.mock
def test_bulk_create_order_numbers_empty_raises(client):
    """Empty list raises ValueError."""
    with pytest.raises(ValueError):
        client.billpay.bulk_create_order_numbers([])


@respx.mock
def test_bulk_create_customer_numbers(client):
    """Bulk customer CN sends correct payload structure."""
    import json

    _auth()
    respx.post(f"{BILLPAY_BASE}/bulk-create-customer-control-numbers").mock(
        return_value=httpx.Response(
            200, json={"billPayNumbers": ["BP1", "BP2"], "created": 2, "failed": 0}
        )
    )
    items = [
        {"customerName": "Alice", "customerPhone": "255712345678"},
        {"customerName": "Bob", "customerEmail": "bob@example.com"},
    ]
    result = client.billpay.bulk_create_customer_numbers(items)
    assert result["created"] == 2

    body = json.loads(respx.calls.last.request.content)
    assert "controlNumbers" in body
    assert len(body["controlNumbers"]) == 2


@respx.mock
def test_update_reference_requires_at_least_one_field(client):
    """update_reference with no fields raises ValueError."""
    with pytest.raises(ValueError, match="At least one"):
        client.billpay.update_reference("BP001")


@respx.mock
def test_update_status_active(client):
    """update_status sends the correct billStatus value."""
    import json

    _auth()
    respx.patch(f"{BILLPAY_BASE}/BP001").mock(
        return_value=httpx.Response(200, json={"billPayNumber": "BP001", "billStatus": "INACTIVE"})
    )
    client.billpay.update_status("BP001", "INACTIVE")
    body = json.loads(respx.calls.last.request.content)
    assert body["billStatus"] == "INACTIVE"
