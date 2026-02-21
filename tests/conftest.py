"""
Shared pytest fixtures for the ClickPesa SDK test suite.
"""

import pytest
from clickpesa import ClickPesa, AsyncClickPesa

SANDBOX_BASE = "https://api-sandbox.clickpesa.com"
MOCK_TOKEN = "Bearer mock_token_123"


@pytest.fixture
def client():
    """Sync ClickPesa client pointed at the sandbox."""
    return ClickPesa(
        client_id="test_id",
        api_key="test_key",
        checksum_key="test_secret",
        sandbox=True,
    )


@pytest.fixture
def async_client():
    """Async ClickPesa client pointed at the sandbox."""
    return AsyncClickPesa(
        client_id="test_id",
        api_key="test_key",
        checksum_key="test_secret",
        sandbox=True,
    )
