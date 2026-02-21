# ClickPesa Python SDK

[![PyPI version](https://badge.fury.io/py/clickpesa-python-sdk.svg)](https://pypi.org/project/clickpesa-python-sdk/)
[![Python](https://img.shields.io/pypi/pyversions/clickpesa-python-sdk)](https://pypi.org/project/clickpesa-python-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Production-grade Python SDK for the [ClickPesa API](https://docs.clickpesa.com) — supports both **sync** and **async** usage, with automatic token management, checksum injection, retry logic, and a full exception hierarchy.

---

## Features

- **Sync & Async** — `ClickPesa` for blocking code, `AsyncClickPesa` for `asyncio` / FastAPI / async frameworks
- **Auto Auth** — JWT tokens are fetched and cached automatically (55-minute window, 1-hour API TTL)
- **Checksum injection** — HMAC-SHA256 checksums added to every mutating request when a `checksum_key` is configured
- **Retries** — exponential backoff on transient 5xx errors (configurable)
- **Thread-safe** — safe to share a single client across threads or async tasks
- **Context manager** — `with` / `async with` support for automatic cleanup
- **Typed exceptions** — structured error hierarchy with `status_code` and `response` attributes
- **PEP 561 compliant** — ships with `py.typed` for mypy / pyright support

---

## Installation

```bash
pip install clickpesa-python-sdk
```

Requires **Python 3.10+**.

---

## Quick Start

### Sync

```python
from clickpesa import ClickPesa

with ClickPesa(
    client_id="YOUR_CLIENT_ID",
    api_key="YOUR_API_KEY",
    checksum_key="YOUR_CHECKSUM_KEY",  # optional but recommended
    sandbox=True,                       # set False for production
) as client:
    balance = client.account.get_balance()
    print(balance)
```

### Async

```python
import asyncio
from clickpesa import AsyncClickPesa

async def main():
    async with AsyncClickPesa(
        client_id="YOUR_CLIENT_ID",
        api_key="YOUR_API_KEY",
        checksum_key="YOUR_CHECKSUM_KEY",
        sandbox=True,
    ) as client:
        balance = await client.account.get_balance()
        print(balance)

asyncio.run(main())
```

---

## Configuration

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `client_id` | `str` | required | Your ClickPesa application Client ID |
| `api_key` | `str` | required | Your ClickPesa application API key |
| `checksum_key` | `str \| None` | `None` | Enables HMAC-SHA256 checksum on every mutating request |
| `sandbox` | `bool` | `False` | Target sandbox (`api-sandbox.clickpesa.com`) instead of production |
| `timeout` | `float` | `30.0` | Per-request timeout in seconds |
| `max_retries` | `int` | `3` | Max retry attempts on transient server errors |

> **Note:** `order_id` / `orderReference` values must be **alphanumeric only** (no hyphens, underscores, or special characters). The API will reject any order reference containing non-alphanumeric characters.

---

## Collections

### USSD Push

```python
# 1. Preview — check available methods and fees before charging
preview = client.payments.preview_ussd_push(
    amount="5000",
    order_id="ORD20240001",
    phone="255712345678",           # optional: include to get sender details
    fetch_sender_details=True,      # optional: returns accountName / accountProvider
)
print(preview["activeMethods"])     # [{"name": "TIGO-PESA", "status": "AVAILABLE", "fee": 580, ...}]

# 2. Initiate — triggers PIN prompt on the customer's phone
transaction = client.payments.initiate_ussd_push(
    amount="5000",
    phone="255712345678",
    order_id="ORD20240001",
    currency="TZS",                 # only TZS supported
)
print(transaction["id"], transaction["status"])
```

### Card Payment

```python
# 1. Preview — check card method availability
preview = client.payments.preview_card(amount="50", order_id="CARD001")

# 2. Initiate — generate a hosted payment link
result = client.payments.initiate_card(
    amount="50",
    order_id="CARD001",
    currency="USD",                 # only USD supported
    customer={
        "fullName": "John Doe",
        "email": "john@example.com",
        "phoneNumber": "255712345678",
    },
    # or use an existing customer ID:
    # customer={"id": "CUST_123"}
)
print(result["cardPaymentLink"])    # redirect customer here
```

### Query Payments

```python
# Single payment by order reference
payments = client.payments.get_status("ORD20240001")

# Paginated list with filters
page = client.payments.list_all(
    status="SUCCESS",
    collectedCurrency="TZS",
    startDate="2024-01-01",
    endDate="2024-12-31",
    limit=20,
    skip=0,
)
print(page["totalCount"], page["data"])
```

---

## Disbursements

### Mobile Money Payout

```python
# 1. Preview — verify fees and recipient before sending
preview = client.payouts.preview_mobile_money(
    amount=10000,
    phone="255712345678",
    order_id="PAY20240001",
    currency="TZS",                 # TZS or USD; recipient always receives TZS
)
print(preview["fee"], preview["receiver"]["accountName"])

# 2. Create — disburse funds
payout = client.payouts.create_mobile_money(
    amount=10000,
    phone="255712345678",
    order_id="PAY20240001",
)
print(payout["id"], payout["status"])  # status: AUTHORIZED → PROCESSING → SUCCESS
```

### Bank Payout (ACH / RTGS)

```python
# Get list of supported banks and their BIC codes
banks = client.payouts.get_banks()
# [{"name": "EQUITY BANK TANZANIA LIMITED", "value": "equity_bank_tanzania_limited", "bic": "EQBLTZTZ"}, ...]

# 1. Preview
preview = client.payouts.preview_bank(
    amount=500000,
    account_number="1234567890",
    bic="EQBLTZTZ",
    order_id="BANK20240001",
    transfer_type="ACH",            # "ACH" or "RTGS"
    currency="TZS",
)

# 2. Create
payout = client.payouts.create_bank(
    amount=500000,
    account_number="1234567890",
    account_name="Jane Doe",
    bic="EQBLTZTZ",
    order_id="BANK20240001",
    transfer_type="RTGS",
    currency="TZS",
)
```

### Query Payouts

```python
# Single payout by order reference
payouts = client.payouts.get_status("PAY20240001")

# All payouts with filters
page = client.payouts.list_all(
    channel="MOBILE MONEY",
    status="SUCCESS",
    limit=50,
)
```

---

## BillPay

ClickPesa BillPay lets customers pay using a numeric control number through mobile money, SIM banking, and CRDB Wakalas. There are two types of control numbers:

- **Order** — one-time, closes after payment. Ideal for invoices and e-commerce orders.
- **Customer** — static and reusable per customer. Ideal for subscriptions and recurring payments.

> **Note:** Every ClickPesa merchant has a 4-digit **Merchant BillPay-Namba** visible on the dashboard. Order control numbers can also be generated *offline* (no API call) by concatenating your Merchant BillPay-Namba with any internal order reference (e.g. `1122` + `231256` = `1122231256`). The SDK only covers API-based generation.

### Create Control Numbers

```python
# Order control number (one-time)
cn = client.billpay.create_order_control_number(
    bill_reference="INVOICE001",    # optional — becomes the control number; auto-generated if omitted
    amount=90900,
    description="Water Bill - July 2024",
    payment_mode="EXACT",           # "EXACT" or "ALLOW_PARTIAL_AND_OVER_PAYMENT"
)
print(cn["billPayNumber"])          # share this with your customer

# Customer control number (persistent / recurring)
cn = client.billpay.create_customer_control_number(
    customer_name="John Doe",
    phone="255712345678",           # phone or email required
    email="john@example.com",
    amount=50000,
    payment_mode="ALLOW_PARTIAL_AND_OVER_PAYMENT",
)
```

### Bulk Create (up to 50 per request)

```python
# Bulk order control numbers
result = client.billpay.bulk_create_order_numbers([
    {"billAmount": 10000, "billDescription": "Invoice #001", "billPaymentMode": "EXACT"},
    {"billAmount": 20000, "billDescription": "Invoice #002"},
    {"billReference": "MYREF003", "billAmount": 5000},
])
print(result["created"], result["failed"])
print(result["billPayNumbers"])

# Bulk customer control numbers
result = client.billpay.bulk_create_customer_numbers([
    {"customerName": "Alice", "customerPhone": "255712345678", "billAmount": 15000},
    {"customerName": "Bob",   "customerEmail": "bob@example.com"},
])
```

### Manage Existing Numbers

```python
# Query details
details = client.billpay.get_details("55042914871931")

# Update amount, description or payment mode
client.billpay.update_reference(
    "55042914871931",
    amount=120000,
    description="Updated Water Bill",
    payment_mode="EXACT",
)

# Activate / deactivate
client.billpay.update_status("55042914871931", "INACTIVE")
client.billpay.update_status("55042914871931", "ACTIVE")
```

---

## Hosted Links

```python
# Checkout link — customer chooses their payment method
result = client.links.generate_checkout(
    order_id="LINK001",
    order_currency="TZS",
    total_price="15000",
    customer_name="Jane Doe",
    customer_email="jane@example.com",
    customer_phone="255712345678",
    description="Order LINK001",
)
print(result["checkoutLink"])       # redirect customer here

# With itemised order instead of a flat total
result = client.links.generate_checkout(
    order_id="LINK002",
    order_currency="USD",
    order_items=[
        {"name": "Widget A", "price": "25.00", "quantity": 2},
        {"name": "Widget B", "price": "10.00", "quantity": 1},
    ],
)

# Payout link — recipient enters their own bank / mobile details
result = client.links.generate_payout(amount="50000", order_id="POUT001")
print(result["payoutLink"])
```

---

## Account & Exchange

```python
# Account balances
result = client.account.get_balance()
# {"balances": [{"currency": "TZS", "balance": 39700}, {"currency": "USD", "balance": 0}]}
print(result["balances"])

# Transaction statement
statement = client.account.get_statement(
    currency="TZS",
    start_date="2024-01-01",
    end_date="2024-12-31",
)
print(statement["accountDetails"])
print(statement["transactions"])

# Exchange rates
rates = client.exchange.get_rates()                          # all pairs
rates = client.exchange.get_rates(source="USD", target="TZS")  # specific pair
# [{"source": "USD", "target": "TZS", "rate": 2510, "date": "..."}]
```

---

## Async Usage

Every method on `AsyncClickPesa` is the `await`-able equivalent:

```python
import asyncio
from clickpesa import AsyncClickPesa

async def run_payments():
    async with AsyncClickPesa(
        client_id="YOUR_CLIENT_ID",
        api_key="YOUR_API_KEY",
        sandbox=True,
    ) as client:
        # Run multiple API calls concurrently
        balance, rates = await asyncio.gather(
            client.account.get_balance(),
            client.exchange.get_rates(source="USD"),
        )
        print(balance, rates)

        # Collections
        tx = await client.payments.initiate_ussd_push(
            amount="3000",
            phone="255712345678",
            order_id="ASYNC001",
        )

        # Disbursements
        payout = await client.payouts.create_mobile_money(
            amount=3000,
            phone="255712345678",
            order_id="ASYNC002",
        )

asyncio.run(run_payments())
```

---

## Webhook Verification

```python
from clickpesa import WebhookValidator

# In your webhook endpoint (Flask / FastAPI / Django etc.)
def webhook_handler(request):
    is_valid = WebhookValidator.verify(
        payload=request.json,
        signature=request.headers["X-ClickPesa-Signature"],
        checksum_key="YOUR_CHECKSUM_KEY",
    )
    if not is_valid:
        return {"error": "Invalid signature"}, 401

    # Process event ...
```

---

## Error Handling

All errors are subclasses of `ClickPesaError` and carry `.status_code` and `.response`:

```python
from clickpesa.exceptions import (
    AuthenticationError,    # 401 — invalid credentials / expired token
    ForbiddenError,         # 403 — feature not enabled on your account
    ValidationError,        # 400 — bad payload
    InsufficientFundsError, # 400 — not enough balance (subclass of ValidationError)
    NotFoundError,          # 404 — resource not found
    ConflictError,          # 409 — duplicate orderReference / billReference
    RateLimitError,         # 429 — payout request already in progress
    ServerError,            # 5xx — ClickPesa server error
    ClickPesaError,         # base class — catches all of the above
)

try:
    client.payments.initiate_ussd_push("5000", "255712345678", "ORD001")

except InsufficientFundsError as e:
    print(f"Not enough balance: {e}")

except ConflictError as e:
    print(f"Order reference already used: {e}")
    print(f"HTTP {e.status_code} — {e.response}")

except ClickPesaError as e:
    print(f"Unexpected API error [{e.status_code}]: {e}")
```

---

## Health Check

```python
# Returns True if the API is reachable and credentials are valid
if client.is_healthy():
    print("Connected to ClickPesa")
else:
    print("API unreachable or credentials invalid")

# Async equivalent
healthy = await client.is_healthy()
```

---

## Development

```bash
git clone https://github.com/JAXPARROW/clickpesa-python-sdk
cd clickpesa-python-sdk

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=clickpesa --cov-report=term-missing
```

---

## License

MIT — see [LICENSE](LICENSE) for details.
