"""
ClickPesa Python SDK
====================

Sync usage::

    from clickpesa import ClickPesa

    with ClickPesa(client_id="…", api_key="…", sandbox=True) as cp:
        balance = cp.account.get_balance()
        cp.payments.initiate_ussd_push(amount="5000", phone="255712345678", order_id="ORD001")

Async usage::

    from clickpesa import AsyncClickPesa

    async with AsyncClickPesa(client_id="…", api_key="…", sandbox=True) as cp:
        balance = await cp.account.get_balance()
"""

from __future__ import annotations

from ._version import __version__
from .client import ClickPesaClient
from .async_client import AsyncClickPesaClient
from .security import SecurityManager
from .webhooks import WebhookValidator
from .exceptions import (
    ClickPesaError,
    AuthenticationError,
    ForbiddenError,
    ValidationError,
    InsufficientFundsError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ServerError,
)
from .services.payments import PaymentService, AsyncPaymentService
from .services.payouts import PayoutService, AsyncPayoutService
from .services.billpay import BillPayService, AsyncBillPayService
from .services.account import AccountService, AsyncAccountService
from .services.exchange import ExchangeService, AsyncExchangeService
from .services.links import LinkService, AsyncLinkService


class ClickPesa(ClickPesaClient):
    """
    Synchronous ClickPesa client with all service namespaces attached.

    Attributes:
        payments:  :class:`~clickpesa.services.payments.PaymentService`
        payouts:   :class:`~clickpesa.services.payouts.PayoutService`
        billpay:   :class:`~clickpesa.services.billpay.BillPayService`
        account:   :class:`~clickpesa.services.account.AccountService`
        exchange:  :class:`~clickpesa.services.exchange.ExchangeService`
        links:     :class:`~clickpesa.services.links.LinkService`
    """

    def __init__(
        self,
        client_id: str,
        api_key: str,
        checksum_key: str | None = None,
        sandbox: bool = False,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        super().__init__(client_id, api_key, checksum_key, sandbox, timeout, max_retries)
        self.payments = PaymentService(self)
        self.payouts = PayoutService(self)
        self.billpay = BillPayService(self)
        self.account = AccountService(self)
        self.exchange = ExchangeService(self)
        self.links = LinkService(self)


class AsyncClickPesa(AsyncClickPesaClient):
    """
    Asynchronous ClickPesa client with all service namespaces attached.

    Attributes:
        payments:  :class:`~clickpesa.services.payments.AsyncPaymentService`
        payouts:   :class:`~clickpesa.services.payouts.AsyncPayoutService`
        billpay:   :class:`~clickpesa.services.billpay.AsyncBillPayService`
        account:   :class:`~clickpesa.services.account.AsyncAccountService`
        exchange:  :class:`~clickpesa.services.exchange.AsyncExchangeService`
        links:     :class:`~clickpesa.services.links.AsyncLinkService`
    """

    def __init__(
        self,
        client_id: str,
        api_key: str,
        checksum_key: str | None = None,
        sandbox: bool = False,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        super().__init__(client_id, api_key, checksum_key, sandbox, timeout, max_retries)
        self.payments = AsyncPaymentService(self)
        self.payouts = AsyncPayoutService(self)
        self.billpay = AsyncBillPayService(self)
        self.account = AsyncAccountService(self)
        self.exchange = AsyncExchangeService(self)
        self.links = AsyncLinkService(self)


__all__ = [
    # Main clients
    "ClickPesa",
    "AsyncClickPesa",
    # Base clients (for advanced subclassing)
    "ClickPesaClient",
    "AsyncClickPesaClient",
    # Utilities
    "SecurityManager",
    "WebhookValidator",
    # Exceptions
    "ClickPesaError",
    "AuthenticationError",
    "ForbiddenError",
    "ValidationError",
    "InsufficientFundsError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
    # Services (for type hints)
    "PaymentService",
    "AsyncPaymentService",
    "PayoutService",
    "AsyncPayoutService",
    "BillPayService",
    "AsyncBillPayService",
    "AccountService",
    "AsyncAccountService",
    "ExchangeService",
    "AsyncExchangeService",
    "LinkService",
    "AsyncLinkService",
    # Version
    "__version__",
]
