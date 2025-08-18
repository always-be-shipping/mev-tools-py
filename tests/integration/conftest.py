"""Configuration and fixtures for integration tests."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pytest
from web3 import Web3

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


@pytest.fixture(scope="session")
def ankr_rpc_url() -> str:
    """Get Ankr RPC URL from environment or use default."""
    return os.getenv("ANKR_RPC_URL", "https://rpc.ankr.com/eth")


@pytest.fixture(scope="session")
def web3_instance(ankr_rpc_url: str) -> Web3:
    """Create Web3 instance with Ankr RPC connection.

    Skip tests if unable to connect to RPC.
    """
    try:
        w3 = Web3(Web3.HTTPProvider(ankr_rpc_url))
        if not w3.is_connected():
            pytest.skip(f"Unable to connect to Ankr RPC at {ankr_rpc_url}")

        # Verify we can make a basic call
        latest_block = w3.eth.block_number
        print(f"Connected to Ethereum mainnet, latest block: {latest_block}")

        return w3
    except Exception as e:
        pytest.skip(f"Failed to connect to RPC: {e}")


@pytest.fixture
def known_liquidation_blocks() -> Dict[str, List[Dict[str, Any]]]:
    """Load known liquidation blocks from test data file."""
    data_file = Path(__file__).parent / "data" / "known_liquidations.json"

    if data_file.exists():
        with open(data_file) as f:
            return json.load(f)

    # Fallback to hardcoded test data if file doesn't exist
    return {
        "aave_v3": [
            {
                "block": 18500000,
                "tx_hash": "0xa1b2c3d4e5f6789012345678901234567890123456789012345678901234567890",
                "description": "Example Aave V3 liquidation",
            }
        ],
        "euler_v1": [
            {
                "block": 18400000,
                "tx_hash": "0xb2c3d4e5f6789012345678901234567890123456789012345678901234567890a1",
                "description": "Example Euler V1 liquidation",
            }
        ],
        "euler_v2": [
            {
                "block": 18450000,
                "tx_hash": "0xc3d4e5f6789012345678901234567890123456789012345678901234567890a1b2",
                "description": "Example Euler V2 liquidation",
            }
        ],
        "morpho": [
            {
                "block": 18600000,
                "tx_hash": "0xd4e5f6789012345678901234567890123456789012345678901234567890a1b2c3",
                "description": "Example Morpho Blue liquidation",
            }
        ],
    }


@pytest.fixture
def integration_test_timeout() -> int:
    """Timeout for integration tests in seconds."""
    return int(os.getenv("INTEGRATION_TEST_TIMEOUT", "30"))


@pytest.fixture
def test_block_range() -> Dict[str, int]:
    """Block range for integration testing."""
    return {
        "start": int(os.getenv("TEST_BLOCK_START", "18500000")),
        "end": int(os.getenv("TEST_BLOCK_END", "18500010")),
    }


@pytest.fixture(scope="session")
def skip_slow_tests() -> bool:
    """Whether to skip slow-running integration tests."""
    return os.getenv("SKIP_SLOW_TESTS", "false").lower() == "true"


@pytest.fixture
def protocol_processors(web3_instance: Web3) -> Dict[str, Any]:
    """Initialize all protocol processors for testing."""
    from mev_tools_py.oev.protocols.aave_v3 import AaveV3ProtocolProcessor
    from mev_tools_py.oev.protocols.euler_v1 import EulerProtocolProcessor
    from mev_tools_py.oev.protocols.euler_v2 import EulerV2ProtocolProcessor
    from mev_tools_py.oev.protocols.morpho import MorphoProtocolProcessor

    return {
        "aave_v3": AaveV3ProtocolProcessor(),
        "euler_v1": EulerProtocolProcessor(),
        "euler_v2": EulerV2ProtocolProcessor(),
        "morpho": MorphoProtocolProcessor(
            web3_provider=web3_instance.provider.endpoint_uri
        ),
    }


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")


def pytest_collection_modifyitems(config, items):
    """Automatically mark integration tests and add skip conditions."""
    integration_marker = pytest.mark.integration
    slow_marker = pytest.mark.slow

    for item in items:
        # Mark all tests in integration directory as integration tests
        if "integration" in str(item.fspath):
            item.add_marker(integration_marker)

        # Mark tests containing 'slow' in name as slow
        if "slow" in item.name.lower():
            item.add_marker(slow_marker)

        # Skip integration tests if no RPC URL is configured
        if item.get_closest_marker("integration") and not os.getenv("ANKR_RPC_URL"):
            item.add_marker(pytest.mark.skip(reason="ANKR_RPC_URL not configured"))

