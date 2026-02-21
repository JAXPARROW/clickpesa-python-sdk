"""
Asynchronous ClickPesa HTTP client.

Drop-in async counterpart to :class:`~clickpesa.client.ClickPesaClient`.
Requires Python 3.10+ and ``httpx`` with async support (included by default).

Usage::

    async with AsyncClickPesaClient(client_id="…", api_key="…") as client:
        balance = await client.account.get_balance()
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from .exceptions import (
    AuthenticationError,
    ClickPesaError,
    ConflictError,
    ForbiddenError,
    InsufficientFundsError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .security import SecurityManager

logger = logging.getLogger(__name__)

_SANDBOX_URL = "https://api-sandbox.clickpesa.com"
_PRODUCTION_URL = "https://api.clickpesa.com"
_AUTH_PATH = "/third-parties/generate-token"
_TOKEN_TTL = 3300
_DEFAULT_TIMEOUT = 30.0
_MAX_RETRIES = 3
_RETRY_STATUSES = {500, 502, 503, 504}
_INSUFFICIENT_FUNDS_PHRASE = "Insufficient balance"


class AsyncClickPesaClient:
    """
    Production-grade asynchronous HTTP client for the ClickPesa API.

    Features
    --------
    - Automatic JWT token acquisition and async-safe caching via ``asyncio.Lock``.
    - Optional HMAC-SHA256 checksum injection on every mutating request.
    - Exponential-backoff retries on transient 5xx errors.
    - Structured exception hierarchy — never raises a bare ``Exception``.
    - Async context-manager support (``async with`` statement).

    Parameters
    ----------
    client_id:
        Your ClickPesa application Client ID.
    api_key:
        Your ClickPesa application API key.
    checksum_key:
        Optional checksum secret.  When provided every POST/PUT/PATCH request
        automatically receives a ``checksum`` field.
    sandbox:
        Set ``True`` to target the sandbox environment.
    timeout:
        Request timeout in seconds (default: 30).
    max_retries:
        Maximum number of retry attempts on transient server errors (default: 3).
    """

    def __init__(
        self,
        client_id: str,
        api_key: str,
        checksum_key: str | None = None,
        sandbox: bool = False,
        timeout: float = _DEFAULT_TIMEOUT,
        max_retries: int = _MAX_RETRIES,
    ) -> None:
        self.client_id = client_id
        self.api_key = api_key
        self.checksum_key = checksum_key
        self.base_url = _SANDBOX_URL if sandbox else _PRODUCTION_URL
        self.timeout = timeout
        self.max_retries = max_retries

        # Async-safe token cache
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._lock: asyncio.Lock | None = None  # created lazily inside the event loop

        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout,
        )

    def _get_lock(self) -> asyncio.Lock:
        """Lazily create the asyncio.Lock inside the running event loop."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def _authenticate(self) -> str:
        """Return a valid Bearer token, refreshing if necessary."""
        async with self._get_lock():
            now = time.monotonic()
            if self._token and now < self._token_expires_at:
                return self._token

            logger.debug("Refreshing ClickPesa access token …")
            try:
                response = await self._http.post(
                    _AUTH_PATH,
                    headers={
                        "client-id": self.client_id,
                        "api-key": self.api_key,
                    },
                )
            except httpx.TransportError as exc:
                raise ClickPesaError(
                    f"Network error during authentication: {exc}"
                ) from exc

            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid client-id or api-key", status_code=401
                )
            if response.status_code == 403:
                data = _safe_json(response)
                raise ForbiddenError(
                    data.get("message", "Forbidden"),
                    status_code=403,
                    response=data,
                )
            if not response.is_success:
                raise ClickPesaError(
                    f"Authentication failed ({response.status_code}): {response.text}",
                    status_code=response.status_code,
                )

            data = _safe_json(response)
            token = data.get("token")
            if not token:
                raise ClickPesaError("Authentication response missing 'token' field")

            self._token = token
            self._token_expires_at = now + _TOKEN_TTL
            logger.debug("Access token cached for %d seconds.", _TOKEN_TTL)
            return self._token

    # ------------------------------------------------------------------
    # Core request dispatcher
    # ------------------------------------------------------------------

    async def request(
        self,
        method: str,
        endpoint: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """
        Execute an authenticated API request with automatic retry on 5xx errors.

        Parameters
        ----------
        method:   HTTP verb (``"GET"``, ``"POST"``, ``"PATCH"``, etc.).
        endpoint: API path relative to the base URL (leading slash optional).
        json:     Request body — will NOT be mutated; a shallow copy is made.
        params:   Query-string parameters.

        Returns
        -------
        Parsed JSON response body.

        Raises
        ------
        :class:`~clickpesa.exceptions.ClickPesaError` or one of its subclasses.
        """
        token = await self._authenticate()
        path = endpoint if endpoint.startswith("/") else f"/{endpoint}"

        payload: dict[str, Any] | None = None
        if json is not None:
            payload = dict(json)
            if self.checksum_key and method.upper() in {"POST", "PUT", "PATCH"}:
                if "checksum" not in payload:
                    payload["checksum"] = SecurityManager.create_checksum(
                        self.checksum_key, payload
                    )

        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self._http.request(
                    method=method,
                    url=path,
                    json=payload,
                    params=params,
                    headers={"Authorization": token},
                )
            except httpx.TransportError as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    await _async_backoff(attempt)
                    continue
                raise ClickPesaError(f"Network error: {exc}") from exc

            if response.status_code in _RETRY_STATUSES and attempt < self.max_retries:
                logger.warning(
                    "Received %d on attempt %d/%d — retrying …",
                    response.status_code,
                    attempt,
                    self.max_retries,
                )
                await _async_backoff(attempt)
                continue

            return _handle_response(response)

        raise ClickPesaError(
            f"Request failed after {self.max_retries} attempts"
        ) from last_exc

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    async def is_healthy(self) -> bool:
        """
        Perform a lightweight connectivity and credential check.

        Returns ``True`` if the API is reachable and credentials are valid.
        """
        try:
            await self.request("GET", "/third-parties/account/balance")
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close the underlying async HTTP connection pool."""
        await self._http.aclose()

    # Async context-manager protocol
    async def __aenter__(self) -> "AsyncClickPesaClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()


# ------------------------------------------------------------------
# Private helpers (module-level to share with sync client)
# ------------------------------------------------------------------

def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return {"message": response.text}


def _handle_response(response: httpx.Response) -> Any:
    """Map HTTP status codes to structured exceptions."""
    data = _safe_json(response)

    if response.is_success:
        return data

    msg = data.get("message", "Unknown API error") if isinstance(data, dict) else str(data)
    status = response.status_code

    if status == 400:
        if _INSUFFICIENT_FUNDS_PHRASE in msg:
            raise InsufficientFundsError(msg, status_code=status, response=data)
        raise ValidationError(msg, status_code=status, response=data)
    if status == 401:
        raise AuthenticationError(msg, status_code=status, response=data)
    if status == 403:
        raise ForbiddenError(msg, status_code=status, response=data)
    if status == 404:
        raise NotFoundError(msg, status_code=status, response=data)
    if status == 409:
        raise ConflictError(msg, status_code=status, response=data)
    if status == 429:
        raise RateLimitError(msg, status_code=status, response=data)
    if status >= 500:
        raise ServerError(msg, status_code=status, response=data)

    raise ClickPesaError(msg, status_code=status, response=data)


async def _async_backoff(attempt: int) -> None:
    delay = 2 ** (attempt - 1)
    logger.debug("Retrying in %d second(s) …", delay)
    await asyncio.sleep(delay)
