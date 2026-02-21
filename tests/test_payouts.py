"""
Tests for PayoutService (sync): mobile money, bank payouts, status, list.
"""

import json
import pytest
import respx
import httpx

from clickpesa.exceptions import InsufficientFundsError, ConflictError

SANDBOX = "https://api-sandbox.clickpesa.com"
AUTH_URL = f"{SANDBOX}/third-parties/generate-token"
BANKS_URL = f"{SANDBOX}/third-parties/list/banks"
PAYOUTS_BASE = f"{SANDBOX}/third-parties/payouts"
PREVIEW_MM = f"{PAYOUTS_BASE}/preview-mobile-money-payout"
CREATE_MM = f"{PAYOUTS_BASE}/create-mobile-money-payout"
PREVIEW_BANK = f"{PAYOUTS_BASE}/preview-bank-payout"
CREATE_BANK = f"{PAYOUTS_BASE}/create-bank-payout"
PAYOUTS_ALL = f"{PAYOUTS_BASE}/all"


def _auth():
    return respx.post(AUTH_URL).mock(
        return_value=httpx.Response(200, json={"token": "Bearer test_tok"})
    )


# ---------------------------------------------------------------------------
# Mobile Money — Preview
# ---------------------------------------------------------------------------

@respx.mock
def test_mobile_money_preview_payload(client):
    """All required fields are present in the preview request body."""
    _auth()
    respx.post(PREVIEW_MM).mock(return_value=httpx.Response(200, json={"fee": "234"}))

    client.payouts.preview_mobile_money(
        amount=5000, phone="255712345678", order_id="PAY001", currency="TZS"
    )

    body = json.loads(respx.calls.last.request.content)
    assert body["amount"] == 5000
    assert body["phoneNumber"] == "255712345678"
    assert body["orderReference"] == "PAY001"
    assert body["currency"] == "TZS"


@respx.mock
def test_mobile_money_preview_default_currency(client):
    """currency defaults to TZS when not supplied."""
    _auth()
    respx.post(PREVIEW_MM).mock(return_value=httpx.Response(200, json={"fee": "234"}))

    client.payouts.preview_mobile_money(amount=1000, phone="255712345678", order_id="PAY002")

    body = json.loads(respx.calls.last.request.content)
    assert body["currency"] == "TZS"


# ---------------------------------------------------------------------------
# Mobile Money — Create
# ---------------------------------------------------------------------------

@respx.mock
def test_create_mobile_money_checksum_injected(client):
    """Checksum is injected into the create mobile money request."""
    _auth()
    respx.post(CREATE_MM).mock(
        return_value=httpx.Response(200, json={"id": "PAYC001", "status": "AUTHORIZED"})
    )

    client.payouts.create_mobile_money(amount=5000, phone="255712345678", order_id="PAY003")

    body = json.loads(respx.calls.last.request.content)
    assert "checksum" in body
    assert len(body["checksum"]) == 64


@respx.mock
def test_create_mobile_money_payload_fields(client):
    """All required fields forwarded in create mobile money."""
    _auth()
    respx.post(CREATE_MM).mock(
        return_value=httpx.Response(200, json={"id": "PAYC002", "status": "AUTHORIZED"})
    )

    client.payouts.create_mobile_money(
        amount=10000, phone="255700000001", order_id="PAY004", currency="USD"
    )

    body = json.loads(respx.calls.last.request.content)
    assert body["amount"] == 10000
    assert body["phoneNumber"] == "255700000001"
    assert body["orderReference"] == "PAY004"
    assert body["currency"] == "USD"


@respx.mock
def test_insufficient_funds_on_mobile_money_payout(client):
    """400 with 'Insufficient balance' raises InsufficientFundsError."""
    _auth()
    respx.post(CREATE_MM).mock(
        return_value=httpx.Response(
            400, json={"message": "Insufficient balance: available balance is 0 TZS"}
        )
    )

    with pytest.raises(InsufficientFundsError):
        client.payouts.create_mobile_money(amount=999999, phone="255712345678", order_id="PAY005")


# ---------------------------------------------------------------------------
# Bank Payout — Preview
# ---------------------------------------------------------------------------

@respx.mock
def test_bank_preview_payload(client):
    """All required bank preview fields are forwarded correctly."""
    _auth()
    respx.post(PREVIEW_BANK).mock(return_value=httpx.Response(200, json={"fee": "2360"}))

    client.payouts.preview_bank(
        amount=50000,
        account_number="1234567890",
        bic="EQBLTZTZ",
        order_id="BANK001",
        transfer_type="RTGS",
        currency="TZS",
    )

    body = json.loads(respx.calls.last.request.content)
    assert body["amount"] == 50000
    assert body["accountNumber"] == "1234567890"
    assert body["bic"] == "EQBLTZTZ"
    assert body["orderReference"] == "BANK001"
    assert body["transferType"] == "RTGS"
    assert body["currency"] == "TZS"
    assert body["accountCurrency"] == "TZS"


@respx.mock
def test_bank_preview_default_transfer_type(client):
    """transfer_type defaults to ACH when not supplied."""
    _auth()
    respx.post(PREVIEW_BANK).mock(return_value=httpx.Response(200, json={"fee": "1000"}))

    client.payouts.preview_bank(
        amount=5000, account_number="0987654321", bic="EQBLTZTZ", order_id="BANK002"
    )

    body = json.loads(respx.calls.last.request.content)
    assert body["transferType"] == "ACH"


# ---------------------------------------------------------------------------
# Bank Payout — Create
# ---------------------------------------------------------------------------

@respx.mock
def test_create_bank_payload_includes_account_name(client):
    """account_name is forwarded in the create bank payout body."""
    _auth()
    respx.post(CREATE_BANK).mock(
        return_value=httpx.Response(200, json={"id": "BANKPAY001", "status": "AUTHORIZED"})
    )

    client.payouts.create_bank(
        amount=50000,
        account_number="1234567890",
        account_name="Jane Doe",
        bic="EQBLTZTZ",
        order_id="BANK003",
        transfer_type="ACH",
        currency="TZS",
    )

    body = json.loads(respx.calls.last.request.content)
    assert body["accountName"] == "Jane Doe"
    assert body["accountNumber"] == "1234567890"
    assert body["bic"] == "EQBLTZTZ"
    assert body["orderReference"] == "BANK003"


@respx.mock
def test_create_bank_conflict_on_duplicate_reference(client):
    """Duplicate order reference on bank payout raises ConflictError."""
    _auth()
    respx.post(CREATE_BANK).mock(
        return_value=httpx.Response(409, json={"message": "Order reference BANK003 already used"})
    )

    with pytest.raises(ConflictError):
        client.payouts.create_bank(
            amount=50000,
            account_number="1234567890",
            account_name="Jane Doe",
            bic="EQBLTZTZ",
            order_id="BANK003",
        )


# ---------------------------------------------------------------------------
# Utilities — get_banks, get_status, list_all
# ---------------------------------------------------------------------------

@respx.mock
def test_get_banks_returns_list(client):
    """get_banks() calls the correct URL and returns the bank list."""
    _auth()
    banks = [{"name": "EQUITY BANK", "value": "equity_bank", "bic": "EQBLTZTZ"}]
    respx.get(BANKS_URL).mock(return_value=httpx.Response(200, json=banks))

    result = client.payouts.get_banks()

    assert isinstance(result, list)
    assert result[0]["bic"] == "EQBLTZTZ"


@respx.mock
def test_get_status_by_order_reference(client):
    """get_status() hits the correct URL path."""
    _auth()
    respx.get(f"{PAYOUTS_BASE}/PAY001").mock(
        return_value=httpx.Response(200, json=[{"id": "PAYC001", "status": "SUCCESS"}])
    )

    result = client.payouts.get_status("PAY001")

    assert isinstance(result, list)
    assert result[0]["status"] == "SUCCESS"


@respx.mock
def test_list_all_passes_filters(client):
    """Filters are forwarded as query parameters to the list endpoint."""
    _auth()
    respx.get(PAYOUTS_ALL).mock(
        return_value=httpx.Response(200, json={"data": [], "totalCount": 0})
    )

    client.payouts.list_all(channel="MOBILE MONEY", status="SUCCESS", limit=10, skip=5)

    url_str = str(respx.calls.last.request.url)
    assert "channel=MOBILE+MONEY" in url_str or "channel=MOBILE%20MONEY" in url_str
    assert "status=SUCCESS" in url_str
    assert "limit=10" in url_str
    assert "skip=5" in url_str
