"""
ClickPesa HMAC-SHA256 security utilities.

Used for generating request checksums and verifying incoming webhook signatures.
"""

from __future__ import annotations

import hmac
import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _canonicalize(obj: Any) -> Any:
    """Recursively sort all object keys alphabetically at every nesting level."""
    if obj is None or not isinstance(obj, (dict, list)):
        return obj
    if isinstance(obj, list):
        return [_canonicalize(item) for item in obj]
    return {key: _canonicalize(obj[key]) for key in sorted(obj.keys())}


class SecurityManager:
    @staticmethod
    def create_checksum(checksum_key: str, payload: dict) -> str:
        """
        Generate a ClickPesa-compatible HMAC-SHA256 checksum for a request payload.

        Algorithm (per ClickPesa docs):
        1. Canonicalize payload — recursively sort all object keys alphabetically.
        2. Serialize to compact JSON (no extra whitespace).
        3. Return the hex digest of HMAC-SHA256(key, json_string).

        Args:
            checksum_key: Your application's checksum secret key.
            payload:      The request body dict (must NOT include ``checksum`` or
                          ``checksumMethod`` fields).

        Returns:
            Hex-encoded HMAC-SHA256 string, or ``""`` if ``checksum_key`` is falsy.
        """
        if not checksum_key:
            return ""

        canonical = _canonicalize(payload)
        payload_string = json.dumps(canonical, separators=(",", ":"), sort_keys=False)

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
