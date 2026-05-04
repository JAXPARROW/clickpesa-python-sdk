"""
Tests for AsyncClickPesa: token caching, checksum injection, error mapping,
and async context-manager support.
"""

import json
from unittest.mock import patch

import pytest
import respx
import httpx

from clickpesa import AsyncClickPesa
from clickpesa.exceptions import AuthenticationError, ClickPesaError, ConflictError, ValidationError

SANDBOX = "https://api-sandbox.clickpesa.com"
AUTH_URL = f"{SANDBOX}/third-parties/generate-token"
BALANCE_URL = f"{SANDBOX}/third-parties/account/balance"
USSD_INITIATE = f"{SANDBOX}/third-parties/payments/initiate-ussd-push-request"


@respx.mock
@pytest.mark.asyncio
async def test_async_token_fetched_on_first_request(async_client):
    """Async client fetches a token on the first request and caches it."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer async_tok"}))
    respx.get(BALANCE_URL).mock(return_value=httpx.Response(200, json=[]))

    await async_client.account.get_balance()

    assert async_client._token == "Bearer async_tok"
    assert respx.calls.call_count == 2


@respx.mock
@pytest.mark.asyncio
async def test_async_token_reused_on_second_request(async_client):
    """Async client reuses cached token without re-authenticating."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer async_tok"}))
    respx.get(BALANCE_URL).mock(return_value=httpx.Response(200, json=[]))

    await async_client.account.get_balance()
    await async_client.account.get_balance()

    assert respx.calls.call_count == 3  # 1 auth + 2 balance


@respx.mock
@pytest.mark.asyncio
async def test_async_auth_error_on_401():
    """Async: invalid credentials raise AuthenticationError."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(401, json={"message": "Unauthorized"}))

    async with AsyncClickPesa(client_id="bad", api_key="bad", sandbox=True) as cp:
        with pytest.raises(AuthenticationError):
            await cp.account.get_balance()


@respx.mock
@pytest.mark.asyncio
async def test_async_checksum_injected(async_client):
    """Async: checksum is injected into mutating requests."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.post(USSD_INITIATE).mock(return_value=httpx.Response(200, json={"status": "PROCESSING"}))

    await async_client.payments.initiate_ussd_push(
        amount="1000", phone="255712345678", order_id="ASYNC001"
    )

    body = json.loads(respx.calls.last.request.content)
    assert "checksum" in body
    assert len(body["checksum"]) == 64


@respx.mock
@pytest.mark.asyncio
async def test_async_caller_dict_not_mutated(async_client):
    """Async: the caller's dict is not modified by checksum injection."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.post(USSD_INITIATE).mock(return_value=httpx.Response(200, json={"status": "PROCESSING"}))

    original = {
        "amount": "500",
        "phoneNumber": "255712345678",
        "currency": "TZS",
        "orderReference": "ASYNC002",
    }
    await async_client.request(
        "POST", "/third-parties/payments/initiate-ussd-push-request", json=original
    )
    assert "checksum" not in original


@respx.mock
@pytest.mark.asyncio
async def test_async_context_manager_closes_session():
    """Async context manager closes the httpx.AsyncClient on exit."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.get(BALANCE_URL).mock(return_value=httpx.Response(200, json=[]))

    async with AsyncClickPesa(client_id="x", api_key="y", sandbox=True) as cp:
        await cp.account.get_balance()

    assert cp._http.is_closed


@respx.mock
@pytest.mark.asyncio
async def test_async_conflict_error(async_client):
    """Async: duplicate order reference raises ConflictError."""
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.post(USSD_INITIATE).mock(
        return_value=httpx.Response(409, json={"message": "Order reference already used"})
    )

    with pytest.raises(ConflictError):
        await async_client.payments.initiate_ussd_push("1000", "255712345678", "DUP001")


@respx.mock
@pytest.mark.asyncio
async def test_async_is_healthy_true(async_client):
    respx.post(AUTH_URL).mock(return_value=httpx.Response(200, json={"token": "Bearer tok"}))
    respx.get(BALANCE_URL).mock(return_value=httpx.Response(200, json=[]))

    assert await async_client.is_healthy() is True


@respx.mock
@pytest.mark.asyncio
async def test_async_auth_retries_on_transport_error_then_succeeds():
    """Async auth TransportError is retried; succeeds on the second attempt."""
    auth_seq = iter([
        httpx.TransportError("timed out"),
        httpx.Response(200, json={"token": "Bearer async_tok"}),
    ])

    def auth_side_effect(req):
        val = next(auth_seq)
        if isinstance(val, Exception):
            raise val
        return val

    respx.post(AUTH_URL).mock(side_effect=auth_side_effect)
    respx.get(BALANCE_URL).mock(return_value=httpx.Response(200, json=[]))

    cp = AsyncClickPesa(client_id="x", api_key="y", sandbox=True)
    with patch("clickpesa.async_client.asyncio.sleep"):
        await cp.account.get_balance()

    assert cp._token == "Bearer async_tok"
    assert respx.calls.call_count == 3  # 2 auth attempts + 1 balance


@respx.mock
@pytest.mark.asyncio
async def test_async_auth_raises_after_all_transport_error_retries():
    """Async auth raises ClickPesaError after all retry attempts fail on TransportError."""
    respx.post(AUTH_URL).mock(side_effect=httpx.TransportError("connection refused"))

    cp = AsyncClickPesa(client_id="x", api_key="y", sandbox=True)
    with patch("clickpesa.async_client.asyncio.sleep"):
        with pytest.raises(ClickPesaError, match="Network error during authentication"):
            await cp.account.get_balance()


@respx.mock
@pytest.mark.asyncio
async def test_async_auth_error_response_attached_to_exception():
    """Async: AuthenticationError on 401 carries the response payload."""
    respx.post(AUTH_URL).mock(
        return_value=httpx.Response(401, json={"message": "Invalid credentials"})
    )

    cp = AsyncClickPesa(client_id="bad", api_key="bad", sandbox=True)
    with pytest.raises(AuthenticationError) as exc_info:
        await cp.account.get_balance()

    assert exc_info.value.response is not None
    assert exc_info.value.status_code == 401
