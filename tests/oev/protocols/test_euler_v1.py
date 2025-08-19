import pytest
from unittest.mock import patch
from typing import Any, Dict, List

from hexbytes import HexBytes

from mev_tools_py.oev.protocols.euler_v1 import EulerProtocolProcessor


class TestEulerProtocolProcessor:
    """Test suite for Euler V1 protocol processor."""

    liquidation_topic = HexBytes(
        "0xbba0f1d6fb8b9abe2bbc543b7c13d43faba91c6f78da4700381c94041ac7267d"
    )

    @pytest.fixture
    def processor(self) -> EulerProtocolProcessor:
        """Create an instance of EulerProtocolProcessor for testing."""
        return EulerProtocolProcessor()

    @pytest.fixture
    def sample_liquidation_log(self) -> Dict[str, Any]:
        """Sample liquidation log data for testing."""
        return {
            "topics": [
                self.liquidation_topic,  # Event signature
                "0x000000000000000000000000742d35cc6634c0532925a3b8d8d5c0532925a3b8",  # liquidator
                "0x000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",  # violator
                "0x000000000000000000000000a0b86a33e6ba3b93b63e1fbb4f4bb4f4bb4f4bb4",  # underlying
            ],
            "data": "0x000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
            "000000000000000000000000000000000000000000000000016345785d8a0000"
            "000000000000000000000000000000000000000000000000016345785d8a0000"
            "000000000000000000000000000000000000000000000000016345785d8a0000"
            "000000000000000000000000000000000000000000000000000de0b6b3a7640000"
            "000000000000000000000000000000000000000000000000000de0b6b3a7640000",
            "transactionHash": "0x123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234",
            "blockNumber": 18500000,
            "logIndex": 42,
        }

    @pytest.fixture
    def mock_decoded_log(self) -> Dict[str, Any]:
        """Mock decoded log data from web3.py."""
        return {
            "args": {
                "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
                "violator": "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
                "underlying": "0xa0b86a33e6ba3b93b63e1fbb4f4bb4f4bb4f4bb4",
                "collateral": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                "repay": 100000000000000000,  # 0.1 ETH
                "yield": 110000000000000000,  # 0.11 ETH
                "healthScore": 950000000000000000,  # 0.95
                "baseDiscount": 1000000000000000000,  # 1.0
                "discount": 1050000000000000000,  # 1.05
            }
        }

    @pytest.fixture
    def sample_transaction(self) -> Dict[str, Any]:
        """Sample transaction data for testing."""
        return {
            "to": "0x27182842E098f60e3D576794A5bFFb0777E025d3",  # Euler mainnet address
            "from": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
            "input": "0x96cd4ddb000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
            "hash": "0x123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234",
        }

    @pytest.fixture
    def sample_logs(
        self, sample_liquidation_log: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Sample logs list for testing."""
        return [sample_liquidation_log]

    def test_protocol_attribute(self, processor: EulerProtocolProcessor) -> None:
        """Test that the protocol attribute is set correctly."""
        assert processor.protocol == "euler"

    def test_initialization(self, processor: EulerProtocolProcessor) -> None:
        """Test that the processor initializes correctly."""
        assert processor.w3 is not None
        assert processor.liquidation_event is not None

    def test_decode_liquidation_success(
        self,
        processor: EulerProtocolProcessor,
        sample_liquidation_log: Dict[str, Any],
        mock_decoded_log: Dict[str, Any],
    ) -> None:
        """Test successful liquidation log decoding."""
        # Mock the process_log method on the instance
        with patch.object(
            processor.liquidation_event, "process_log", return_value=mock_decoded_log
        ) as mock_process_log:
            result = processor.decode_liquidation(sample_liquidation_log)

            # Verify the method was called with the correct log
            mock_process_log.assert_called_once_with(sample_liquidation_log)

        # Verify the returned structure
        assert result["protocol"] == "euler"
        assert result["liquidator"] == "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8"
        assert result["user"] == "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3"
        assert (
            result["underlying_asset"] == "0xa0b86a33e6ba3b93b63e1fbb4f4bb4f4bb4f4bb4"
        )
        assert (
            result["collateral_asset"] == "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
        )

        # Check debt_repaid structure
        assert (
            result["debt_repaid"]["token"]
            == "0xa0b86a33e6ba3b93b63e1fbb4f4bb4f4bb4f4bb4"
        )
        assert result["debt_repaid"]["amount"] == "100000000000000000"

        # Check collateral_seized structure
        assert (
            result["collateral_seized"]["token"]
            == "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
        )
        assert result["collateral_seized"]["amount"] == "110000000000000000"

        # Check additional fields
        assert result["health_score"] == "950000000000000000"
        assert result["liquidation_bonus"] == 0.05  # (1.05 - 1.0) / 1e18 * 1e18
        assert result["transaction_hash"] == sample_liquidation_log["transactionHash"]
        assert result["block_number"] == sample_liquidation_log["blockNumber"]
        assert result["log_index"] == sample_liquidation_log["logIndex"]

    def test_decode_liquidation_failure(
        self, processor: EulerProtocolProcessor, sample_liquidation_log: Dict[str, Any]
    ) -> None:
        """Test liquidation log decoding failure."""
        # Mock the process_log method to raise an exception
        with patch.object(
            processor.liquidation_event,
            "process_log",
            side_effect=Exception("Decoding failed"),
        ):
            with pytest.raises(
                ValueError, match="Failed to decode Euler liquidation log"
            ):
                processor.decode_liquidation(sample_liquidation_log)

    def test_enrich_event_basic(self, processor: EulerProtocolProcessor) -> None:
        """Test basic event enrichment."""
        event = {
            "protocol": "euler",
            "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
            "user": "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
            "health_score": "950000000000000000",
        }

        result = processor.enrich_event(event)

        # Check that original fields are preserved
        assert result["protocol"] == "euler"
        assert result["liquidator"] == "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8"

        # Check enriched fields
        assert result["liquidation_type"] == "euler_v1"
        assert result["is_soft_liquidation"] is False
        assert result["protocol_version"] == "1"
        assert result["health_factor"] == 0.95  # 950000000000000000 / 1e18
        assert result["is_undercollateralized"] is True  # health_factor < 1.0

    def test_enrich_event_no_health_score(
        self, processor: EulerProtocolProcessor
    ) -> None:
        """Test event enrichment when health score is missing."""
        event = {
            "protocol": "euler",
            "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
        }

        result = processor.enrich_event(event)

        # Check enriched fields
        assert result["liquidation_type"] == "euler_v1"
        assert result["protocol_version"] == "1"
        # health_factor should not be present if health_score is missing
        assert "health_factor" not in result
        assert "is_undercollateralized" not in result

    def test_is_liquidation_transaction_euler_contract(
        self,
        processor: EulerProtocolProcessor,
        sample_transaction: Dict[str, Any],
        sample_logs: List[Dict[str, Any]],
    ) -> None:
        """Test liquidation detection with transaction to Euler contract."""
        is_liquidation, log_idx = processor.is_liquidation_transaction(
            sample_transaction, sample_logs
        )

        assert is_liquidation is True
        assert log_idx == 0

    def test_is_liquidation_transaction_exec_proxy(
        self, processor: EulerProtocolProcessor, sample_logs: List[Dict[str, Any]]
    ) -> None:
        """Test liquidation detection with transaction to execution proxy."""
        transaction = {
            "to": "0x59828FdF7ee634AaaD3f58B19fDBa3b03E2a9d80",  # Exec proxy address
            "input": "0x96cd4ddb000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
        }

        is_liquidation, log_idx = processor.is_liquidation_transaction(
            transaction, sample_logs
        )

        assert is_liquidation is True
        assert log_idx == 0

    def test_is_liquidation_transaction_wrong_contract(
        self, processor: EulerProtocolProcessor, sample_logs: List[Dict[str, Any]]
    ) -> None:
        """Test liquidation detection with transaction to wrong contract."""
        transaction = {
            "to": "0x1234567890123456789012345678901234567890",  # Wrong contract
            "input": "0x96cd4ddb000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
        }

        is_liquidation, log_idx = processor.is_liquidation_transaction(
            transaction, sample_logs
        )

        assert is_liquidation is False
        assert log_idx == -1

    def test_is_liquidation_transaction_batch_method(
        self, processor: EulerProtocolProcessor
    ) -> None:
        """Test liquidation detection with batch liquidation method."""
        transaction = {
            "to": "0x27182842E098f60e3D576794A5bFFb0777E025d3",
            "input": "0xb2a02ff1000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
        }
        logs: List[Dict[str, Any]] = []

        is_liquidation, log_idx = processor.is_liquidation_transaction(
            transaction, logs
        )

        assert is_liquidation is False
        assert log_idx == -1  # No event logs, just method signature

    def test_is_liquidation_transaction_no_match(
        self, processor: EulerProtocolProcessor
    ) -> None:
        """Test liquidation detection with no matching criteria."""
        transaction = {
            "to": "0x1234567890123456789012345678901234567890",  # Wrong contract
            "input": "0x12345678000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",  # Wrong method
        }
        logs: List[Dict[str, Any]] = []

        is_liquidation, log_idx = processor.is_liquidation_transaction(
            transaction, logs
        )

        assert is_liquidation is False
        assert log_idx == -1

    def test_is_liquidation_transaction_empty_input(
        self, processor: EulerProtocolProcessor
    ) -> None:
        """Test liquidation detection with empty transaction input."""
        transaction = {
            "to": "0x1234567890123456789012345678901234567890",
            "input": "",
        }
        logs: List[Dict[str, Any]] = []

        is_liquidation, log_idx = processor.is_liquidation_transaction(
            transaction, logs
        )

        assert is_liquidation is False
        assert log_idx == -1

    def test_is_liquidation_transaction_short_input(
        self, processor: EulerProtocolProcessor
    ) -> None:
        """Test liquidation detection with short transaction input."""
        transaction = {
            "to": "0x27182842E098f60e3D576794A5bFFb0777E025d3",
            "input": "0x1234",  # Too short for method signature
        }
        logs: List[Dict[str, Any]] = []

        is_liquidation, log_idx = processor.is_liquidation_transaction(
            transaction, logs
        )

        assert is_liquidation is False
        assert log_idx == -1

    def test_constants(self, processor: EulerProtocolProcessor) -> None:
        """Test that contract constants are set correctly."""
        assert (
            processor.EULER_MAINNET_ADDRESS
            == "0x27182842E098f60e3D576794A5bFFb0777E025d3"
        )
        assert (
            processor.EXEC_PROXY_ADDRESS == "0x59828FdF7ee634AaaD3f58B19fDBa3b03E2a9d80"
        )

    def test_liquidation_event_abi_structure(
        self, processor: EulerProtocolProcessor
    ) -> None:
        """Test that the liquidation event ABI has the correct structure."""
        abi = processor.LIQUIDATION_EVENT_ABI

        assert abi["name"] == "Liquidation"
        assert abi["type"] == "event"
        assert abi["anonymous"] is False

        # Check that all expected inputs are present
        inputs = abi["inputs"]
        assert isinstance(inputs, list)  # Type guard for mypy
        input_names = [input_item["name"] for input_item in inputs]
        expected_inputs = [
            "liquidator",
            "violator",
            "underlying",
            "collateral",
            "repay",
            "yield",
            "healthScore",
            "baseDiscount",
            "discount",
        ]

        for expected_input in expected_inputs:
            assert expected_input in input_names

    def test_liquidation_bonus_calculation(
        self, processor: EulerProtocolProcessor
    ) -> None:
        """Test liquidation bonus calculation in decode_liquidation."""
        mock_decoded_log = {
            "args": {
                "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
                "violator": "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
                "underlying": "0xa0b86a33e6ba3b93b63e1fbb4f4bb4f4bb4f4bb4",
                "collateral": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                "repay": 100000000000000000,
                "yield": 110000000000000000,
                "healthScore": 950000000000000000,
                "baseDiscount": 1000000000000000000,  # 1.0
                "discount": 1100000000000000000,  # 1.1
            }
        }

        with patch.object(
            processor.liquidation_event, "process_log", return_value=mock_decoded_log
        ):
            result = processor.decode_liquidation({})

            # liquidation_bonus = (1.1 - 1.0) / 1e18 = 0.1
            assert result["liquidation_bonus"] == 0.1

    def test_liquidation_bonus_zero_discount(
        self, processor: EulerProtocolProcessor
    ) -> None:
        """Test liquidation bonus calculation when discount equals base discount."""
        mock_decoded_log = {
            "args": {
                "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
                "violator": "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
                "underlying": "0xa0b86a33e6ba3b93b63e1fbb4f4bb4f4bb4f4bb4",
                "collateral": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                "repay": 100000000000000000,
                "yield": 110000000000000000,
                "healthScore": 950000000000000000,
                "baseDiscount": 1000000000000000000,  # 1.0
                "discount": 1000000000000000000,  # 1.0 (same as base)
            }
        }

        with patch.object(
            processor.liquidation_event, "process_log", return_value=mock_decoded_log
        ):
            result = processor.decode_liquidation({})

            assert result["liquidation_bonus"] == 0.0
