"""
Webhook signature verification helpers.

Usage::

    from clickpesa import WebhookValidator

    is_valid = WebhookValidator.verify(
        payload=request.json(),
        signature=request.headers["X-ClickPesa-Signature"],
        checksum_key="your-checksum-secret",
    )
"""

from __future__ import annotations

from .security import SecurityManager


class WebhookValidator:
    """Static helper for validating ClickPesa webhook payloads."""

    @staticmethod
    def verify(payload: dict, signature: str, checksum_key: str) -> bool:
        """
        Verify that an incoming webhook was genuinely sent by ClickPesa.

        Uses constant-time comparison (``hmac.compare_digest``) to prevent
        timing-based attacks.

        Args:
            payload:      Parsed JSON body of the webhook request.
            signature:    Value of the ``X-ClickPesa-Signature`` header.
            checksum_key: Your application's checksum secret key.

        Returns:
            ``True`` if the signature is valid, ``False`` otherwise.
        """
        return SecurityManager.verify_webhook(checksum_key, payload, signature)


__all__ = ["WebhookValidator"]
