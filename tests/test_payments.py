"""
Tests for PaymentService (sync): checksum injection, USSD Push, Card, status, list.
"""

import json
import pytest
import respx
import httpx

from clickpesa.exceptions import ConflictError

SANDBOX = "https://api-sandbox.clickpesa.com"
AUTH_URL = f"{SANDBOX}/third-parties/generate-token"
USSD_PREVIEW = f"{SANDBOX}/third-parties/payments/preview-ussd-push-request"
USSD_INITIATE = f"{SANDBOX}/third-parties/payments/initiate-ussd-push-request"
CARD_PREVIEW = f"{SANDBOX}/third-parties/payments/preview-card-payment"
CARD_INITIATE = f"{SANDBOX}/third-parties/payments/initiate-card-payment"
PAYMENTS_ALL = f"{SANDBOX}/third-parties/payments/all"


def _auth():
    return respx.post(AUTH_URL).mock(
        return_value=httpx.Response(200, json={"token": "Bearer test_tok"})
    )


@respx.mock
def test_ussd_push_checksum_injected(client):
    """Checksum is automatically injected and is a 64-char hex string."""
    _auth()
    respx.post(USSD_INITIATE).mock(return_value=httpx.Response(200, json={"status": "PROCESSING"}))

    client.payments.initiate_ussd_push(amount="1000", phone="255712345678", order_id="ORD001")

    body = json.loads(respx.calls.last.request.content)
    assert "checksum" in body
    assert len(body["checksum"]) == 64  # HMAC-SHA256 hex digest


@respx.mock
def test_ussd_push_payload_fields(client):
    """All required fields are present in the USSD initiate payload."""
    _auth()
    respx.post(USSD_INITIATE).mock(return_value=httpx.Response(200, json={"status": "PROCESSING"}))

    client.payments.initiate_ussd_push(amount="2000", phone="255700000001", order_id="ORD002")

    body = json.loads(respx.calls.last.request.content)
    assert body["amount"] == "2000"
    assert body["phoneNumber"] == "255700000001"
    assert body["orderReference"] == "ORD002"
    assert body["currency"] == "TZS"


@respx.mock
def test_ussd_preview_fetch_sender_details(client):
    """fetchSenderDetails=True is forwarded in the request payload."""
    _auth()
    respx.post(USSD_PREVIEW).mock(
        return_value=httpx.Response(200, json={"activeMethods": [], "sender": {}})
    )

    client.payments.preview_ussd_push(
        amount="1000", order_id="ORD003", phone="255712345678", fetch_sender_details=True
    )

    body = json.loads(respx.calls.last.request.content)
    assert body["fetchSenderDetails"] is True


@respx.mock
def test_ussd_preview_phone_optional(client):
    """preview_ussd_push works without a phone number."""
    _auth()
    respx.post(USSD_PREVIEW).mock(return_value=httpx.Response(200, json={"activeMethods": []}))

    client.payments.preview_ussd_push(amount="500", order_id="ORD004")

    body = json.loads(respx.calls.last.request.content)
    assert "phoneNumber" not in body


@respx.mock
def test_card_initiate_with_customer_details(client):
    """Card payment can be initiated with full customer details."""
    _auth()
    respx.post(CARD_INITIATE).mock(
        return_value=httpx.Response(200, json={"cardPaymentLink": "https://pay.example.com"})
    )

    result = client.payments.initiate_card(
        amount="50",
        order_id="CARD001",
        customer={"fullName": "John Doe", "email": "john@example.com", "phoneNumber": "255712345678"},
    )
    assert "cardPaymentLink" in result


@respx.mock
def test_list_all_passes_query_params(client):
    """Filters are forwarded as query parameters."""
    _auth()
    respx.get(PAYMENTS_ALL).mock(return_value=httpx.Response(200, json={"data": [], "totalCount": 0}))

    client.payments.list_all(status="SUCCESS", limit=5, skip=10)

    url_str = str(respx.calls.last.request.url)
    assert "status=SUCCESS" in url_str
    assert "limit=5" in url_str
    assert "skip=10" in url_str


@respx.mock
def test_conflict_on_duplicate_order_reference(client):
    """Duplicate order reference raises ConflictError."""
    _auth()
    respx.post(USSD_INITIATE).mock(
        return_value=httpx.Response(409, json={"message": "Order reference ORD001 already used"})
    )

    with pytest.raises(ConflictError):
        client.payments.initiate_ussd_push("1000", "255712345678", "ORD001")
