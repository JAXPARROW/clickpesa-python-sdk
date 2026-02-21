"""
Tests for WebhookValidator and the underlying SecurityManager checksum logic.
"""

import pytest

from clickpesa import WebhookValidator
from clickpesa.security import SecurityManager

CHECKSUM_KEY = "test_webhook_secret"
PAYLOAD = {"amount": "5000", "orderReference": "ORD001", "status": "SUCCESS"}


def _sig(payload=PAYLOAD, key=CHECKSUM_KEY):
    return SecurityManager.create_checksum(key, payload)


# ---------------------------------------------------------------------------
# WebhookValidator.verify
# ---------------------------------------------------------------------------

def test_verify_valid_signature():
    """A signature computed from the same payload and key verifies correctly."""
    sig = _sig()
    assert WebhookValidator.verify(PAYLOAD, sig, CHECKSUM_KEY) is True


def test_verify_wrong_signature():
    """A signature that does not match the payload returns False."""
    assert WebhookValidator.verify(PAYLOAD, "deadbeef" * 8, CHECKSUM_KEY) is False


def test_verify_tampered_payload():
    """Changing a field after signing invalidates the signature."""
    sig = _sig()
    tampered = {**PAYLOAD, "amount": "99999"}
    assert WebhookValidator.verify(tampered, sig, CHECKSUM_KEY) is False


def test_verify_wrong_key():
    """A signature produced with a different key does not verify."""
    sig = _sig(key="other_secret")
    assert WebhookValidator.verify(PAYLOAD, sig, CHECKSUM_KEY) is False


def test_verify_empty_signature_returns_false():
    """An empty signature string is rejected immediately."""
    assert WebhookValidator.verify(PAYLOAD, "", CHECKSUM_KEY) is False


def test_verify_nested_fields_excluded():
    """Nested dicts and lists are ignored in the checksum — a flat signature
    still verifies a payload that has extra nested fields."""
    flat_sig = _sig()
    payload_with_nested = {**PAYLOAD, "customer": {"name": "Alice"}, "items": [1, 2, 3]}
    assert WebhookValidator.verify(payload_with_nested, flat_sig, CHECKSUM_KEY) is True


# ---------------------------------------------------------------------------
# SecurityManager.create_checksum
# ---------------------------------------------------------------------------

def test_checksum_is_64_char_hex():
    """HMAC-SHA256 hex digest is always 64 characters."""
    sig = SecurityManager.create_checksum(CHECKSUM_KEY, PAYLOAD)
    assert len(sig) == 64
    assert all(c in "0123456789abcdef" for c in sig)


def test_checksum_empty_key_returns_empty_string():
    """No checksum_key → empty string (checksum injection disabled)."""
    assert SecurityManager.create_checksum("", PAYLOAD) == ""
    assert SecurityManager.create_checksum(None, PAYLOAD) == ""


def test_checksum_sorted_key_order():
    """Key order in the payload dict does not affect the checksum."""
    a = SecurityManager.create_checksum(CHECKSUM_KEY, {"z": "1", "a": "2"})
    b = SecurityManager.create_checksum(CHECKSUM_KEY, {"a": "2", "z": "1"})
    assert a == b
