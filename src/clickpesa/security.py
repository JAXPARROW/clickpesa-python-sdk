"""
ClickPesa HMAC-SHA256 security utilities.

Used for generating request checksums and verifying incoming webhook signatures.
"""

from __future__ import annotations

import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)


class SecurityManager:
    @staticmethod
    def create_checksum(checksum_key: str, payload: dict) -> str:
        """
        Generate a ClickPesa-compatible HMAC-SHA256 checksum for a request payload.

        Algorithm:
        1. Sort payload keys alphabetically.
        2. Concatenate the string representation of all top-level scalar values
           (nested dicts and lists are excluded, matching ClickPesa's specification).
        3. Return the hex digest of HMAC-SHA256(key, concatenated_string).

        Args:
            checksum_key: Your application's checksum secret key.
            payload:      The request body dict (before the checksum field is added).

        Returns:
            Hex-encoded HMAC-SHA256 string, or ``""`` if ``checksum_key`` is falsy.
        """
        if not checksum_key:
            return ""

        sorted_keys = sorted(payload.keys())
        payload_string = "".join(
            str(payload[k])
            for k in sorted_keys
            if not isinstance(payload[k], (dict, list))
        )

        return hmac.new(
            checksum_key.encode("utf-8"),
            payload_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def verify_webhook(checksum_key: str, payload: dict, signature: str) -> bool:
        """
        Verify an incoming ClickPesa webhook signature.

        Uses ``hmac.compare_digest`` for constant-time comparison to prevent
        timing-based side-channel attacks.

        Args:
            checksum_key: Your application's checksum secret key.
            payload:      The parsed webhook body dict.
            signature:    The ``X-ClickPesa-Signature`` header value.

        Returns:
            ``True`` if the signature is valid, ``False`` otherwise.
        """
        if not signature:
            return False

        computed = SecurityManager.create_checksum(checksum_key, payload)
        return hmac.compare_digest(computed, signature)


__all__ = ["SecurityManager"]
