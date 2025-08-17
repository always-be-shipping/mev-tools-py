import pytest
from unittest.mock import patch
from typing import Any, Dict, List

from mev_tools_py.oev.protocols.euler_v2 import EulerV2ProtocolProcessor


class TestEulerV2ProtocolProcessor:
    """Test suite for Euler V2 protocol processor."""

    @pytest.fixture
    def processor(self) -> EulerV2ProtocolProcessor:
        """Create an instance of EulerV2ProtocolProcessor for testing."""
        return EulerV2ProtocolProcessor()

    @pytest.fixture
    def sample_single_liquidation_log(self) -> Dict[str, Any]:
        """Sample single liquidation log data for testing."""
        return {
            "topics": [
                "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",  # Event signature
                "0x000000000000000000000000742d35cc6634c0532925a3b8d8d5c0532925a3b8",  # liquidator
                "0x000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",  # violator
                "0x000000000000000000000000a0b86a33e6ba3b93b63e1fbb4f4bb4f4bb4f4bb4",  # vault
            ],
            "data": "0x000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"  # collateralVault
                    "000000000000000000000000000000000000000000000000016345785d8a0000"  # repayAssets
                    "000000000000000000000000000000000000000000000000016345785d8a0000"  # yieldBalance
                    "000000000000000000000000000000000000000000000000016345785d8a0000"  # collateralSeized
                    "000000000000000000000000000000000000000000000000000de0b6b3a7640000",  # discount
            "transactionHash": "0x123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234",
            "blockNumber": 18500000,
            "logIndex": 42,
        }

    @pytest.fixture
    def sample_batch_liquidation_log(self) -> Dict[str, Any]:
        """Sample batch liquidation log data for testing."""
        return {
            "topics": [
                "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",  # Event signature
                "0x000000000000000000000000742d35cc6634c0532925a3b8d8d5c0532925a3b8",  # liquidator
            ],
            "data": "0x0000000000000000000000000000000000000000000000000000000000000005",  # numberOfLiquidations
            "transactionHash": "0x123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234",
            "blockNumber": 18500000,
            "logIndex": 43,
        }

    @pytest.fixture
    def mock_single_liquidation_decoded_log(self) -> Dict[str, Any]:
        """Mock decoded single liquidation log data from web3.py."""
        return {
            "args": {
                "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
                "violator": "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
                "vault": "0xa0b86a33e6ba3b93b63e1fbb4f4bb4f4bb4f4bb4",
                "collateralVault": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                "repayAssets": 100000000000000000,  # 0.1 ETH
                "yieldBalance": 105000000000000000,  # 0.105 ETH
                "collateralSeized": 110000000000000000,  # 0.11 ETH
                "discount": 1050000000000000000,  # 1.05
            }
        }

    @pytest.fixture
    def mock_batch_liquidation_decoded_log(self) -> Dict[str, Any]:
        """Mock decoded batch liquidation log data from web3.py."""
        return {
            "args": {
                "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
                "numberOfLiquidations": 5,
            }
        }

    @pytest.fixture
    def sample_transaction(self) -> Dict[str, Any]:
        """Sample transaction data for testing."""
        return {
            "to": "0x835482FE0532f169024d5E9410199369aAD5C77E",  # Euler V2 factory address
            "from": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
            "input": "0x7c025200000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
            "hash": "0x123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234",
        }

    @pytest.fixture
    def sample_logs_single(self, sample_single_liquidation_log: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sample logs list with single liquidation for testing."""
        return [sample_single_liquidation_log]

    @pytest.fixture
    def sample_logs_batch(self, sample_batch_liquidation_log: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sample logs list with batch liquidation for testing."""
        return [sample_batch_liquidation_log]

    def test_protocol_attribute(self, processor: EulerV2ProtocolProcessor) -> None:
        """Test that the protocol attribute is set correctly."""
        assert processor.protocol == "euler_v2"

    def test_initialization(self, processor: EulerV2ProtocolProcessor) -> None:
        """Test that the processor initializes correctly."""
        assert processor.w3 is not None
        assert processor.liquidation_event is not None
        assert processor.batch_liquidation_event is not None

    def test_decode_single_liquidation_success(
        self,
        processor: EulerV2ProtocolProcessor,
        sample_single_liquidation_log: Dict[str, Any],
        mock_single_liquidation_decoded_log: Dict[str, Any]
    ) -> None:
        """Test successful single liquidation log decoding."""
        # Mock the process_log method on the instance
        with patch.object(processor.liquidation_event, 'process_log', return_value=mock_single_liquidation_decoded_log) as mock_process_log:
            result = processor.decode_liquidation(sample_single_liquidation_log)

            # Verify the method was called with the correct log
            mock_process_log.assert_called_once_with(sample_single_liquidation_log)

            # Verify the returned structure
            assert result["protocol"] == "euler_v2"
            assert result["liquidator"] == "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8"
            assert result["user"] == "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3"
            assert result["debt_vault"] == "0xa0b86a33e6ba3b93b63e1fbb4f4bb4f4bb4f4bb4"
            assert result["collateral_vault"] == "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
            
            # Check debt_repaid structure
            assert result["debt_repaid"]["vault"] == "0xa0b86a33e6ba3b93b63e1fbb4f4bb4f4bb4f4bb4"
            assert result["debt_repaid"]["amount"] == "100000000000000000"
            
            # Check collateral_seized structure
            assert result["collateral_seized"]["vault"] == "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
            assert result["collateral_seized"]["amount"] == "110000000000000000"
            
            # Check additional fields
            assert result["yield_balance"] == "105000000000000000"
            assert result["liquidation_bonus"] == 1.05  # 1.05 (discount value from mock)
            assert result["event_type"] == "single_liquidation"
            assert result["transaction_hash"] == sample_single_liquidation_log["transactionHash"]
            assert result["block_number"] == sample_single_liquidation_log["blockNumber"]
            assert result["log_index"] == sample_single_liquidation_log["logIndex"]

    def test_decode_batch_liquidation_success(
        self,
        processor: EulerV2ProtocolProcessor,
        sample_batch_liquidation_log: Dict[str, Any],
        mock_batch_liquidation_decoded_log: Dict[str, Any]
    ) -> None:
        """Test successful batch liquidation log decoding."""
        # Mock single liquidation to fail, batch to succeed
        with patch.object(processor.liquidation_event, 'process_log', side_effect=Exception("Not single liquidation")):
            with patch.object(processor.batch_liquidation_event, 'process_log', return_value=mock_batch_liquidation_decoded_log) as mock_batch_process_log:
                result = processor.decode_liquidation(sample_batch_liquidation_log)

                # Verify the batch method was called with the correct log
                mock_batch_process_log.assert_called_once_with(sample_batch_liquidation_log)

                # Verify the returned structure for batch liquidation
                assert result["protocol"] == "euler_v2"
                assert result["liquidator"] == "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8"
                assert result["user"] == ""  # Not available in batch event
                assert result["number_of_liquidations"] == "5"
                assert result["event_type"] == "batch_liquidation"
                assert result["transaction_hash"] == sample_batch_liquidation_log["transactionHash"]
                assert result["block_number"] == sample_batch_liquidation_log["blockNumber"]
                assert result["log_index"] == sample_batch_liquidation_log["logIndex"]

    def test_decode_liquidation_failure(
        self,
        processor: EulerV2ProtocolProcessor,
        sample_single_liquidation_log: Dict[str, Any]
    ) -> None:
        """Test liquidation log decoding failure."""
        # Mock both process_log methods to raise exceptions
        with patch.object(processor.liquidation_event, 'process_log', side_effect=Exception("Single liquidation failed")):
            with patch.object(processor.batch_liquidation_event, 'process_log', side_effect=Exception("Batch liquidation failed")):
                with pytest.raises(ValueError, match="Failed to decode Euler V2 liquidation log"):
                    processor.decode_liquidation(sample_single_liquidation_log)

    def test_enrich_single_liquidation_event(self, processor: EulerV2ProtocolProcessor) -> None:
        """Test enrichment of single liquidation event."""
        event = {
            "protocol": "euler_v2",
            "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
            "user": "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
            "event_type": "single_liquidation",
            "debt_repaid": {"amount": "100000000000000000"},
            "collateral_seized": {"amount": "110000000000000000"},
        }

        result = processor.enrich_event(event)

        # Check that original fields are preserved
        assert result["protocol"] == "euler_v2"
        assert result["liquidator"] == "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8"
        
        # Check enriched fields
        assert result["liquidation_type"] == "euler_v2"
        assert result["is_vault_based"] is True
        assert result["protocol_version"] == "2"
        assert result["is_batch_liquidation"] is False
        assert result["uses_vault_system"] is True
        assert result["vault_based_collateral"] is True
        
        # Check calculated metrics
        assert result["liquidation_ratio"] == 1.1  # 110 / 100
        assert result["is_profitable"] is True  # ratio > 1.0

    def test_enrich_batch_liquidation_event(self, processor: EulerV2ProtocolProcessor) -> None:
        """Test enrichment of batch liquidation event."""
        event = {
            "protocol": "euler_v2",
            "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
            "event_type": "batch_liquidation",
            "number_of_liquidations": "5",
        }

        result = processor.enrich_event(event)

        # Check enriched fields
        assert result["liquidation_type"] == "euler_v2"
        assert result["is_vault_based"] is True
        assert result["protocol_version"] == "2"
        assert result["is_batch_liquidation"] is True
        assert result["batch_size"] == 5
        assert result["is_bulk_operation"] is True

    def test_enrich_event_zero_amounts(self, processor: EulerV2ProtocolProcessor) -> None:
        """Test enrichment when amounts are zero."""
        event = {
            "protocol": "euler_v2",
            "event_type": "single_liquidation",
            "debt_repaid": {"amount": "0"},
            "collateral_seized": {"amount": "0"},
        }

        result = processor.enrich_event(event)

        # liquidation_ratio should not be calculated with zero amounts
        assert "liquidation_ratio" not in result
        assert "is_profitable" not in result

    def test_is_liquidation_transaction_factory_contract(
        self,
        processor: EulerV2ProtocolProcessor,
        sample_transaction: Dict[str, Any],
        sample_logs_single: List[Dict[str, Any]]
    ) -> None:
        """Test liquidation detection with transaction to Euler V2 factory contract."""
        # Mock the keccak method to return predictable hashes
        with patch.object(processor.w3, 'keccak') as mock_keccak:
            mock_keccak.return_value.hex.return_value = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
            
            result = processor.is_liquidation_transaction(sample_transaction, sample_logs_single)
            
            assert result is True

    def test_is_liquidation_transaction_batch_event(
        self,
        processor: EulerV2ProtocolProcessor,
        sample_logs_batch: List[Dict[str, Any]]
    ) -> None:
        """Test liquidation detection with batch liquidation event."""
        transaction = {
            "to": "0x835482FE0532f169024d5E9410199369aAD5C77E",  # Factory address
            "input": "0xd9627aa4000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
        }

        with patch.object(processor.w3, 'keccak') as mock_keccak:
            # Return different hashes for single and batch events
            mock_keccak.return_value.hex.side_effect = [
                "0x1111111111111111111111111111111111111111111111111111111111111111",  # single liquidation
                "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",  # batch liquidation
            ]
            
            result = processor.is_liquidation_transaction(transaction, sample_logs_batch)
            
            assert result is True

    def test_is_liquidation_transaction_method_signature(
        self,
        processor: EulerV2ProtocolProcessor
    ) -> None:
        """Test liquidation detection based on method signature."""
        transaction = {
            "to": "0x835482FE0532f169024d5E9410199369aAD5C77E",  # Factory address
            "input": "0x7c025200000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
        }
        logs: List[Dict[str, Any]] = []  # No logs

        result = processor.is_liquidation_transaction(transaction, logs)
        
        assert result is True

    def test_is_liquidation_transaction_vault_contract(
        self,
        processor: EulerV2ProtocolProcessor,
        sample_logs_single: List[Dict[str, Any]]
    ) -> None:
        """Test liquidation detection with transaction to unknown vault contract."""
        transaction = {
            "to": "0x1234567890123456789012345678901234567890",  # Unknown vault contract
            "input": "0xa694fc3a000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
        }

        with patch.object(processor.w3, 'keccak') as mock_keccak:
            mock_keccak.return_value.hex.return_value = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
            
            result = processor.is_liquidation_transaction(transaction, sample_logs_single)
            
            # Should return True because Euler V2 events are present
            assert result is True

    def test_is_liquidation_transaction_no_match(
        self,
        processor: EulerV2ProtocolProcessor
    ) -> None:
        """Test liquidation detection with no matching criteria."""
        transaction = {
            "to": "0x1234567890123456789012345678901234567890",  # Unknown contract
            "input": "0x12345678000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",  # Wrong method
        }
        logs: List[Dict[str, Any]] = []

        result = processor.is_liquidation_transaction(transaction, logs)
        
        assert result is False

    def test_constants(self, processor: EulerV2ProtocolProcessor) -> None:
        """Test that V2 contract constants are set correctly."""
        assert processor.EULER_V2_FACTORY == "0x835482FE0532f169024d5E9410199369aAD5C77E"
        assert processor.EULER_V2_ROUTER == "0x0000000000000000000000000000000000000000"

    def test_liquidation_event_abi_structure(self, processor: EulerV2ProtocolProcessor) -> None:
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
            "liquidator", "violator", "vault", "collateralVault", 
            "repayAssets", "yieldBalance", "collateralSeized", "discount"
        ]
        
        for expected_input in expected_inputs:
            assert expected_input in input_names

    def test_batch_liquidation_event_abi_structure(self, processor: EulerV2ProtocolProcessor) -> None:
        """Test that the batch liquidation event ABI has the correct structure."""
        abi = processor.BATCH_LIQUIDATION_EVENT_ABI
        
        assert abi["name"] == "BatchLiquidation"
        assert abi["type"] == "event"
        assert abi["anonymous"] is False
        
        # Check that all expected inputs are present
        inputs = abi["inputs"]
        assert isinstance(inputs, list)  # Type guard for mypy
        input_names = [input_item["name"] for input_item in inputs]
        expected_inputs = ["liquidator", "numberOfLiquidations"]
        
        for expected_input in expected_inputs:
            assert expected_input in input_names

    def test_liquidation_bonus_calculation(self, processor: EulerV2ProtocolProcessor) -> None:
        """Test liquidation bonus calculation in decode_liquidation."""
        mock_decoded_log = {
            "args": {
                "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
                "violator": "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
                "vault": "0xa0b86a33e6ba3b93b63e1fbb4f4bb4f4bb4f4bb4",
                "collateralVault": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                "repayAssets": 100000000000000000,
                "yieldBalance": 105000000000000000,
                "collateralSeized": 110000000000000000,
                "discount": 2000000000000000000,  # 2.0
            }
        }

        with patch.object(processor.liquidation_event, 'process_log', return_value=mock_decoded_log):
            result = processor.decode_liquidation({})
            
            # liquidation_bonus = 2.0 / 1e18 = 0.000000000000000002 ≈ 0.0
            # Actually: 2000000000000000000 / 1e18 = 2.0
            assert result["liquidation_bonus"] == 2.0

    def test_liquidation_bonus_zero_discount(self, processor: EulerV2ProtocolProcessor) -> None:
        """Test liquidation bonus calculation when discount is zero."""
        mock_decoded_log = {
            "args": {
                "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
                "violator": "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
                "vault": "0xa0b86a33e6ba3b93b63e1fbb4f4bb4f4bb4f4bb4",
                "collateralVault": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                "repayAssets": 100000000000000000,
                "yieldBalance": 105000000000000000,
                "collateralSeized": 110000000000000000,
                "discount": 0,  # Zero discount
            }
        }

        with patch.object(processor.liquidation_event, 'process_log', return_value=mock_decoded_log):
            result = processor.decode_liquidation({})
            
            assert result["liquidation_bonus"] == 0.0

    def test_batch_liquidation_single_operation(self, processor: EulerV2ProtocolProcessor) -> None:
        """Test batch liquidation enrichment with single operation."""
        event = {
            "protocol": "euler_v2",
            "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
            "event_type": "batch_liquidation",
            "number_of_liquidations": "1",
        }

        result = processor.enrich_event(event)

        assert result["batch_size"] == 1
        assert result["is_bulk_operation"] is False  # Only 1 liquidation

    def test_batch_liquidation_multiple_operations(self, processor: EulerV2ProtocolProcessor) -> None:
        """Test batch liquidation enrichment with multiple operations."""
        event = {
            "protocol": "euler_v2",
            "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
            "event_type": "batch_liquidation",
            "number_of_liquidations": "3",
        }

        result = processor.enrich_event(event)

        assert result["batch_size"] == 3
        assert result["is_bulk_operation"] is True  # More than 1 liquidation