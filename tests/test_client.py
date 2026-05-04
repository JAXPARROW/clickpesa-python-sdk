"""
Tests for the core sync client: authentication, token caching,
error mapping, retry logic, and context-manager support.
"""

from unittest.mock import patch

import pytest
import respx
import httpx

from clickpesa import ClickPesa
from clickpesa.exceptions import (
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    InsufficientFundsError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)

SANDBOX = "https://api-sandbox.clickpesa.com"
AUTH_URL = f"{SANDBOX}/third-parties/generate-token"
BALANCE_URL = f"{SANDBOX}/third-parties/account/balance"
USSD_INITIATE = f"{SANDBOX}/third-parties/payments/initiate-ussd-push-request"


@respx.mock
def test_token_is_fetched_on_first_request(client):
    """Client fetches a token on the first API call and caches it."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok123"}))
    respx.get(BALANCE_URL).mock(return_value=httpx.Response(200, json=[]))

    client.account.get_balance()

    assert client._token == "Bearer tok123"
    assert respx.calls.call_count == 2


@respx.mock
def test_token_is_reused_across_requests(client):
    """Second request reuses the cached token without calling auth again."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.get(BALANCE_URL).mock(return_value=httpx.Response(200, json=[]))

    client.account.get_balance()
    client.account.get_balance()

    # 1 auth + 2 balance = 3
    assert respx.calls.call_count == 3


@respx.mock
def test_authentication_error_on_401(client):
    """Invalid credentials raise AuthenticationError."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(401, json={"message": "Unauthorized"}))

    with pytest.raises(AuthenticationError):
        client.account.get_balance()


@respx.mock
def test_validation_error_on_400(client):
    """API 400 raises ValidationError with correct status_code."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.post(USSD_INITIATE).mock(
        return_value=httpx.Response(400, json={"message": "Invalid order reference"})
    )

    with pytest.raises(ValidationError) as exc_info:
        client.payments.initiate_ussd_push("1000", "255712345678", "BAD REF")

    assert exc_info.value.status_code == 400


@respx.mock
def test_insufficient_funds_raises_specific_error(client):
    """400 with 'Insufficient balance' in message raises InsufficientFundsError."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.post(USSD_INITIATE).mock(
        return_value=httpx.Response(
            400, json={"message": "Insufficient balance: available balance is 0 TZS"}
        )
    )

    with pytest.raises(InsufficientFundsError):
        client.payments.initiate_ussd_push("99999", "255712345678", "ORD001")


@respx.mock
def test_conflict_error_on_409(client):
    """Duplicate order reference raises ConflictError."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.post(USSD_INITIATE).mock(
        return_value=httpx.Response(409, json={"message": "Order reference ORD001 already used"})
    )

    with pytest.raises(ConflictError) as exc_info:
        client.payments.initiate_ussd_push("1000", "255712345678", "ORD001")

    assert exc_info.value.status_code == 409


@respx.mock
def test_not_found_error_on_404(client):
    """Missing resource raises NotFoundError."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.get(f"{SANDBOX}/third-parties/payments/UNKNOWN_REF").mock(
        return_value=httpx.Response(404, json={"message": "Invalid or missing payment"})
    )

    with pytest.raises(NotFoundError):
        client.payments.get_status("UNKNOWN_REF")


@respx.mock
def test_caller_dict_is_not_mutated(client):
    """The SDK never adds 'checksum' to the caller's original dict."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.post(USSD_INITIATE).mock(return_value=httpx.Response(200, json={"status": "PROCESSING"}))

    original = {
        "amount": "1000",
        "phoneNumber": "255712345678",
        "currency": "TZS",
        "orderReference": "ORD002",
    }
    client.request("POST", "/third-parties/payments/initiate-ussd-push-request", json=original)

    assert "checksum" not in original


@respx.mock
def test_context_manager_closes_session():
    """Client used as context manager closes the HTTP session on exit."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.get(BALANCE_URL).mock(return_value=httpx.Response(200, json=[]))

    with ClickPesa(client_id="x", api_key="y", sandbox=True) as cp:
        cp.account.get_balance()

    assert cp._http.is_closed


@respx.mock
def test_is_healthy_returns_true(client):
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.get(BALANCE_URL).mock(return_value=httpx.Response(200, json=[]))

    assert client.is_healthy() is True


@respx.mock
def test_is_healthy_returns_false_on_auth_error(client):
    respx.post(AUTH_URL).mock(return_value=httpx.Response(401, json={"message": "Unauthorized"}))

    assert client.is_healthy() is False


@respx.mock
def test_forbidden_error_on_403(client):
    """API 403 raises ForbiddenError with correct status_code."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.get(BALANCE_URL).mock(
        return_value=httpx.Response(403, json={"message": "Feature not enabled on your account"})
    )

    with pytest.raises(ForbiddenError) as exc_info:
        client.account.get_balance()

    assert exc_info.value.status_code == 403


@respx.mock
def test_rate_limit_error_on_429(client):
    """API 429 raises RateLimitError."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.post(USSD_INITIATE).mock(
        return_value=httpx.Response(429, json={"message": "Payout request already in progress"})
    )

    with pytest.raises(RateLimitError) as exc_info:
        client.payments.initiate_ussd_push("1000", "255712345678", "ORD001")

    assert exc_info.value.status_code == 429


@respx.mock
def test_server_error_after_all_retries(client):
    """Persistent 500 raises ServerError after exhausting all retry attempts."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.post(USSD_INITIATE).mock(
        return_value=httpx.Response(500, json={"message": "Internal Server Error"})
    )

    with patch("clickpesa.client.time.sleep"):  # skip backoff delays in tests
        with pytest.raises(ServerError):
            client.payments.initiate_ussd_push("1000", "255712345678", "ORD001")


@respx.mock
def test_retries_then_succeeds():
    """Client succeeds on the third attempt after two 500 responses."""
    responses = iter([
        httpx.Response(500, json={"message": "Server Error"}),
        httpx.Response(500, json={"message": "Server Error"}),
        httpx.Response(200, json={"id": "TX001", "status": "PROCESSING"}),
    ])

    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.post(USSD_INITIATE).mock(side_effect=lambda req: next(responses))

    cp = ClickPesa(client_id="x", api_key="y", checksum_key="s", sandbox=True)
    with patch("clickpesa.client.time.sleep"):
        result = cp.payments.initiate_ussd_push("1000", "255712345678", "ORD001")

    assert result["status"] == "PROCESSING"
    # 1 auth call + 3 endpoint attempts
    assert respx.calls.call_count == 4


@respx.mock
def test_auth_retries_on_transport_error_then_succeeds():
    """Auth TransportError is retried; succeeds on the second attempt."""
    auth_seq = iter([
        httpx.TransportError("timed out"),
        httpx.Response(200, json={"token": "Bearer tok"}),
    ])

    def auth_side_effect(req):
        val = next(auth_seq)
        if isinstance(val, Exception):
            raise val
        return val

    respx.post(AUTH_URL).mock(side_effect=auth_side_effect)
    respx.get(BALANCE_URL).mock(return_value=httpx.Response(200, json=[]))

    cp = ClickPesa(client_id="x", api_key="y", sandbox=True)
    with patch("clickpesa.client.time.sleep"):
        cp.account.get_balance()

    assert cp._token == "Bearer tok"
    # 2 auth attempts + 1 balance call
    assert respx.calls.call_count == 3


@respx.mock
def test_auth_raises_after_all_transport_error_retries():
    """Auth raises ClickPesaError after exhausting all retry attempts on TransportError."""
    from clickpesa.exceptions import ClickPesaError as CPError

    respx.post(AUTH_URL).mock(side_effect=httpx.TransportError("connection refused"))

    cp = ClickPesa(client_id="x", api_key="y", sandbox=True)
    with patch("clickpesa.client.time.sleep"):
        with pytest.raises(CPError, match="Network error during authentication"):
            cp.account.get_balance()


@respx.mock
def test_auth_retries_on_server_error_then_succeeds():
    """Auth 500 is retried; succeeds on the second attempt."""
    auth_responses = iter([
        httpx.Response(500, json={"message": "Internal Server Error"}),
        httpx.Response(200, json={"token": "Bearer tok2"}),
    ])
    respx.post(AUTH_URL).mock(side_effect=lambda req: next(auth_responses))
    respx.get(BALANCE_URL).mock(return_value=httpx.Response(200, json=[]))

    cp = ClickPesa(client_id="x", api_key="y", sandbox=True)
    with patch("clickpesa.client.time.sleep"):
        cp.account.get_balance()

    assert cp._token == "Bearer tok2"


@respx.mock
def test_auth_error_response_is_attached_to_exception():
    """AuthenticationError raised on 401 carries the response payload."""
    respx.post(AUTH_URL).mock(
        return_value=httpx.Response(401, json={"message": "Invalid credentials"})
    )

    cp = ClickPesa(client_id="bad", api_key="bad", sandbox=True)
    with pytest.raises(AuthenticationError) as exc_info:
        cp.account.get_balance()

    assert exc_info.value.response is not None
    assert exc_info.value.status_code == 401
