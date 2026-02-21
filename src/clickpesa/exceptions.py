"""
ClickPesa SDK exception hierarchy.

All exceptions inherit from ``ClickPesaError`` so callers can catch the
base class when they don't need to distinguish between error types.
"""

from __future__ import annotations

from typing import Any


class ClickPesaError(Exception):
    """Base exception for all ClickPesa SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={str(self)!r}, "
            f"status_code={self.status_code!r})"
        )


class AuthenticationError(ClickPesaError):
    """
    Raised on HTTP 401.
    Credentials (client-id / api-key) are invalid or the JWT token has expired.
    """


class ForbiddenError(ClickPesaError):
    """
    Raised on HTTP 403.
    The API key is valid but does not have access to the requested feature.
    """


class ValidationError(ClickPesaError):
    """
    Raised on HTTP 400.
    The request payload failed server-side validation.
    """


class InsufficientFundsError(ValidationError):
    """
    Raised on HTTP 400 when the error message indicates insufficient balance.
    Subclass of ValidationError so it is caught by the same broad handler.
    """


class NotFoundError(ClickPesaError):
    """
    Raised on HTTP 404.
    The requested resource (payment, payout, BillPay number, etc.) does not exist.
    """


class ConflictError(ClickPesaError):
    """
    Raised on HTTP 409.
    Typically means the ``orderReference`` or ``billReference`` has already been used.
    """


class RateLimitError(ClickPesaError):
    """
    Raised on HTTP 429.
    A payout request is already in progress; retry after the indicated delay.
    """


class ServerError(ClickPesaError):
    """
    Raised on HTTP 5xx.
    An unexpected error occurred on the ClickPesa server side.
    """


__all__ = [
    "ClickPesaError",
    "AuthenticationError",
    "ForbiddenError",
    "ValidationError",
    "InsufficientFundsError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
]
