# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-02-21

### Added
- Sync (`ClickPesa`) and async (`AsyncClickPesa`) clients via `httpx`
- Automatic JWT token management with thread-safe caching (55-minute TTL)
- HMAC-SHA256 checksum injection on mutating requests (`checksum_key`)
- Exponential backoff retries on transient 5xx errors (configurable `max_retries`)
- Context manager support (`with` / `async with`)
- **Collections** — USSD Push (preview + initiate), Card Payment (preview + initiate), payment status query, paginated list
- **Disbursements** — Mobile Money and Bank (ACH/RTGS) payouts with preview, payout status query, paginated list, bank list
- **BillPay** — Order and Customer control numbers: create, bulk create (up to 50), get details, update reference, update status
- **Hosted Links** — Checkout and Payout link generation
- **Account** — balance and transaction statement
- **Exchange rates** — all pairs or filtered by source/target currency
- **Webhook verification** — `WebhookValidator.verify()` with constant-time HMAC comparison
- Full exception hierarchy: `AuthenticationError`, `ForbiddenError`, `ValidationError`, `InsufficientFundsError`, `NotFoundError`, `ConflictError`, `RateLimitError`, `ServerError`
- PEP 561 compliant (`py.typed` marker)
- 64 unit tests covering all services, error mapping, retry logic, checksum injection, and webhook verification
