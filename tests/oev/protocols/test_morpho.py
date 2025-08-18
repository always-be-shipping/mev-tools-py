import pytest
from unittest.mock import patch
from typing import Any, Dict, List

from mev_tools_py.oev.protocols.morpho import MorphoProtocolProcessor


class TestMorphoProtocolProcessor:
    """Test suite for Morpho protocol processor."""

    @pytest.fixture
    def processor(self) -> MorphoProtocolProcessor:
        """Create an instance of MorphoProtocolProcessor for testing."""
        return MorphoProtocolProcessor()

    @pytest.fixture
    def sample_liquidation_log(self) -> Dict[str, Any]:
        """Sample Morpho liquidation log data for testing."""
        return {
            "topics": [
                "0x0eb2ba42ef0de4b5b5b79c5ae8edcd6e93bb29dc5a9b2d12f51e8a8e66a40b5a",  # Liquidate event signature
                "0x7b00000000000000000000000000000000000000000000000000000000000001",  # market id
                "0x000000000000000000000000742d35cc6634c0532925a3b8d8d5c0532925a3b8",  # caller (liquidator)
                "0x000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",  # borrower
            ],
            "data": "0x000000000000000000000000000000000000000000000000000de0b6b3a7640000"  # repaidAssets (1000 * 1e18)
            "000000000000000000000000000000000000000000000000000de0b6b3a7640000"  # repaidShares (1000 * 1e18)
            "000000000000000000000000000000000000000000000000016345785d8a0000"  # seizedAssets (0.1 * 1e18)
            "0000000000000000000000000000000000000000000000000000000000000000"  # badDebtAssets (0)
            "0000000000000000000000000000000000000000000000000000000000000000",  # badDebtShares (0)
            "address": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",  # Morpho Blue address
            "transactionHash": "0x123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234",
            "blockNumber": 18500000,
            "logIndex": 42,
        }

    @pytest.fixture
    def mock_decoded_liquidation_log(self) -> Dict[str, Any]:
        """Mock decoded liquidation log data from web3.py."""
        return {
            "args": {
                "id": b"{\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01",
                "caller": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
                "borrower": "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
                "repaidAssets": 1000000000000000000000,  # 1000 tokens
                "repaidShares": 1000000000000000000000,  # 1000 shares
                "seizedAssets": 100000000000000000,  # 0.1 tokens
                "badDebtAssets": 0,
                "badDebtShares": 0,
            }
        }

    @pytest.fixture
    def mock_decoded_liquidation_with_bad_debt(self) -> Dict[str, Any]:
        """Mock decoded liquidation log with bad debt."""
        return {
            "args": {
                "id": b"{\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02",
                "caller": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
                "borrower": "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
                "repaidAssets": 500000000000000000000,  # 500 tokens
                "repaidShares": 500000000000000000000,  # 500 shares
                "seizedAssets": 50000000000000000,  # 0.05 tokens
                "badDebtAssets": 100000000000000000000,  # 100 tokens bad debt
                "badDebtShares": 100000000000000000000,  # 100 shares bad debt
            }
        }

    @pytest.fixture
    def sample_transaction(self) -> Dict[str, Any]:
        """Sample transaction data for testing."""
        return {
            "to": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",  # Morpho Blue address
            "from": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
            "input": "0x0748ca67000000000000000000000000a0b86a33e6441db5db86df4d9e5c4e6a05f3a5"
            "000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
            "000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",  # liquidate call
            "hash": "0x123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234",
        }

    @pytest.fixture
    def sample_logs(
        self, sample_liquidation_log: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Sample logs list for testing."""
        return [sample_liquidation_log]

    def test_protocol_attribute(self, processor: MorphoProtocolProcessor) -> None:
        """Test that the protocol attribute is set correctly."""
        assert processor.protocol == "morpho"

    def test_initialization(self, processor: MorphoProtocolProcessor) -> None:
        """Test that the processor initializes correctly."""
        assert processor.w3 is not None
        assert processor.liquidate_event is not None
        assert processor.accrue_interest_event is not None

    def test_contract_addresses(self, processor: MorphoProtocolProcessor) -> None:
        """Test that contract addresses are set correctly."""
        assert (
            processor.MORPHO_BLUE_ADDRESS
            == "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"
        )

    def test_decode_liquidation_success(
        self,
        processor: MorphoProtocolProcessor,
        sample_liquidation_log: Dict[str, Any],
        mock_decoded_liquidation_log: Dict[str, Any],
    ) -> None:
        """Test successful liquidation log decoding."""
        with patch.object(
            processor.liquidate_event,
            "process_log",
            return_value=mock_decoded_liquidation_log,
        ) as mock_process_log:
            result = processor.decode_liquidation(sample_liquidation_log)

            mock_process_log.assert_called_once_with(sample_liquidation_log)

        # Verify the returned structure
        assert result["protocol"] == "morpho"
        assert result["liquidator"] == "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8"
        assert result["user"] == "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3"

        # Check market ID
        expected_market_id = mock_decoded_liquidation_log["args"]["id"].hex()
        assert result["market_id"] == expected_market_id

        # Check debt_repaid structure
        assert result["debt_repaid"]["market_id"] == expected_market_id
        assert result["debt_repaid"]["assets"] == "1000000000000000000000"
        assert result["debt_repaid"]["shares"] == "1000000000000000000000"

        # Check collateral_seized structure
        assert result["collateral_seized"]["market_id"] == expected_market_id
        assert result["collateral_seized"]["assets"] == "100000000000000000"

        # Check additional fields
        assert result["bad_debt_assets"] == "0"
        assert result["bad_debt_shares"] == "0"
        assert result["has_bad_debt"] is False
        assert result["transaction_hash"] == sample_liquidation_log["transactionHash"]
        assert result["block_number"] == sample_liquidation_log["blockNumber"]
        assert result["log_index"] == sample_liquidation_log["logIndex"]

        # Check liquidation bonus calculation
        # liquidation_bonus = (seized_assets / repaid_assets - 1.0)
        # = (100000000000000000 / 1000000000000000000000 - 1.0) = (0.0001 - 1.0) = -0.9999
        assert result["liquidation_bonus"] == -0.9999

    def test_decode_liquidation_with_bad_debt(
        self,
        processor: MorphoProtocolProcessor,
        sample_liquidation_log: Dict[str, Any],
        mock_decoded_liquidation_with_bad_debt: Dict[str, Any],
    ) -> None:
        """Test liquidation log decoding with bad debt."""
        with patch.object(
            processor.liquidate_event,
            "process_log",
            return_value=mock_decoded_liquidation_with_bad_debt,
        ):
            result = processor.decode_liquidation(sample_liquidation_log)

        # Verify bad debt handling
        assert result["bad_debt_assets"] == "100000000000000000000"
        assert result["bad_debt_shares"] == "100000000000000000000"
        assert result["has_bad_debt"] is True

        # Check liquidation metrics
        # (50000000000000000 / 500000000000000000000 - 1.0) = (0.0001 - 1.0) = -0.9999
        assert result["liquidation_bonus"] == -0.9999

    def test_decode_liquidation_failure(
        self, processor: MorphoProtocolProcessor, sample_liquidation_log: Dict[str, Any]
    ) -> None:
        """Test liquidation log decoding failure."""
        with patch.object(
            processor.liquidate_event,
            "process_log",
            side_effect=Exception("Decoding failed"),
        ):
            with pytest.raises(
                ValueError, match="Failed to decode Morpho liquidation log"
            ):
                processor.decode_liquidation(sample_liquidation_log)

    def test_enrich_event_basic(self, processor: MorphoProtocolProcessor) -> None:
        """Test basic event enrichment."""
        event = {
            "protocol": "morpho",
            "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
            "user": "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
            "debt_repaid": {"assets": "1000000000000000000000"},  # 1000 tokens
            "collateral_seized": {"assets": "1050000000000000000000"},  # 1050 tokens
            "bad_debt_assets": "0",
            "has_bad_debt": False,
        }

        result = processor.enrich_event(event)

        # Check that original fields are preserved
        assert result["protocol"] == "morpho"
        assert result["liquidator"] == "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8"

        # Check enriched fields
        assert result["liquidation_type"] == "morpho_blue"
        assert result["protocol_version"] == "blue"
        assert result["is_isolated_market"] is True
        assert result["supports_bad_debt"] is True
        assert result["uses_market_id"] is True
        assert result["is_permissionless"] is True

        # Check liquidation metrics
        assert result["liquidation_ratio"] == 1.05  # 1050 / 1000
        assert result["is_profitable"] is True
        assert (
            abs(result["liquidation_incentive"] - 0.05) < 0.001
        )  # floating point precision
        assert (
            result["liquidation_size_category"] == "medium"
        )  # 1000 tokens is between 1000-10000 range

        # Check liquidation efficiency
        assert result["liquidation_efficiency"] == 1.0  # No bad debt
        assert result["bad_debt_ratio"] == 0.0

        # Check Morpho-specific features
        assert result["market_based"] is True
        assert result["uses_oracle_pricing"] is True
        assert result["supports_flash_liquidation"] is True
        assert result["immutable_core"] is True
        assert result["liquidation_completeness"] == "full"
        assert result["requires_bad_debt_handling"] is False

    def test_enrich_event_with_bad_debt(
        self, processor: MorphoProtocolProcessor
    ) -> None:
        """Test event enrichment with bad debt."""
        event = {
            "protocol": "morpho",
            "debt_repaid": {"assets": "500000000000000000000"},  # 500 tokens
            "collateral_seized": {"assets": "525000000000000000000"},  # 525 tokens
            "bad_debt_assets": "100000000000000000000",  # 100 tokens bad debt
            "has_bad_debt": True,
        }

        result = processor.enrich_event(event)

        assert result["liquidation_ratio"] == 1.05
        assert result["liquidation_efficiency"] == 0.8  # (500 - 100) / 500
        assert result["bad_debt_ratio"] == 0.2  # 100 / 500
        assert result["liquidation_completeness"] == "partial"
        assert result["requires_bad_debt_handling"] is True

    def test_enrich_event_small_liquidation(
        self, processor: MorphoProtocolProcessor
    ) -> None:
        """Test event enrichment for small liquidation."""
        event = {
            "protocol": "morpho",
            "debt_repaid": {"assets": "500000000000000000000"},  # 500 tokens
            "collateral_seized": {"assets": "525000000000000000000"},  # 525 tokens
            "bad_debt_assets": "0",
            "has_bad_debt": False,
        }

        result = processor.enrich_event(event)

        assert result["liquidation_size_category"] == "small"  # < 1000

    def test_enrich_event_medium_liquidation(
        self, processor: MorphoProtocolProcessor
    ) -> None:
        """Test event enrichment for medium liquidation."""
        event = {
            "protocol": "morpho",
            "debt_repaid": {"assets": "5000000000000000000000"},  # 5000 tokens
            "collateral_seized": {"assets": "5250000000000000000000"},  # 5250 tokens
            "bad_debt_assets": "0",
            "has_bad_debt": False,
        }

        result = processor.enrich_event(event)

        assert result["liquidation_size_category"] == "medium"  # >= 1000, < 10000

    def test_enrich_event_no_amounts(self, processor: MorphoProtocolProcessor) -> None:
        """Test event enrichment when amounts are missing."""
        event = {
            "protocol": "morpho",
            "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
            "bad_debt_assets": "0",
            "has_bad_debt": False,
        }

        result = processor.enrich_event(event)

        # Check enriched fields
        assert result["liquidation_type"] == "morpho_blue"
        assert result["protocol_version"] == "blue"
        # liquidation_ratio should not be present if amounts are missing
        assert "liquidation_ratio" not in result
        assert "is_profitable" not in result
        assert "liquidation_incentive" not in result

    def test_is_liquidation_transaction_morpho_contract(
        self,
        processor: MorphoProtocolProcessor,
        sample_transaction: Dict[str, Any],
        sample_logs: List[Dict[str, Any]],
    ) -> None:
        """Test liquidation detection with transaction to Morpho Blue contract."""
        with patch.object(processor.w3, "keccak") as mock_keccak:
            mock_keccak.return_value.hex.return_value = (
                "0x0eb2ba42ef0de4b5b5b79c5ae8edcd6e93bb29dc5a9b2d12f51e8a8e66a40b5a"
            )

            result = processor.is_liquidation_transaction(
                sample_transaction, sample_logs
            )

            assert result is True

    def test_is_liquidation_transaction_wrong_contract(
        self, processor: MorphoProtocolProcessor, sample_logs: List[Dict[str, Any]]
    ) -> None:
        """Test liquidation detection with transaction to wrong contract."""
        transaction = {
            "to": "0x1234567890123456789012345678901234567890",  # Wrong contract
            "input": "0x0748ca67000000000000000000000000a0b86a33e6441db5db86df4d9e5c4e6a05f3a5",
        }

        # Mock the keccak method to return the correct liquidation event topic
        with patch.object(processor.w3, "keccak") as mock_keccak:
            mock_keccak.return_value.hex.return_value = (
                "0x0eb2ba42ef0de4b5b5b79c5ae8edcd6e93bb29dc5a9b2d12f51e8a8e66a40b5a"
            )

            result = processor.is_liquidation_transaction(transaction, sample_logs)

            # Should return True because of the liquidation event in logs from correct address
            assert result is True

    def test_is_liquidation_transaction_method_signature(
        self, processor: MorphoProtocolProcessor
    ) -> None:
        """Test liquidation detection based on method signature."""
        transaction = {
            "to": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",  # Morpho Blue address
            "input": "0x0748ca67000000000000000000000000a0b86a33e6441db5db86df4d9e5c4e6a05f3a5",
        }
        logs: List[Dict[str, Any]] = []  # No logs

        result = processor.is_liquidation_transaction(transaction, logs)

        assert result is True

    def test_is_liquidation_transaction_no_match(
        self, processor: MorphoProtocolProcessor
    ) -> None:
        """Test liquidation detection with no matching criteria."""
        transaction = {
            "to": "0x1234567890123456789012345678901234567890",  # Wrong contract
            "input": "0x12345678000000000000000000000000a0b86a33e6441db5db86df4d9e5c4e6a05f3a5",  # Wrong method
        }
        logs: List[Dict[str, Any]] = []

        result = processor.is_liquidation_transaction(transaction, logs)

        assert result is False

    def test_is_liquidation_transaction_event_detection(
        self, processor: MorphoProtocolProcessor
    ) -> None:
        """Test liquidation detection based on event logs only."""
        transaction = {
            "to": "0x1234567890123456789012345678901234567890",  # Different contract
            "input": "0x12345678",  # Non-liquidation method
        }
        logs = [
            {
                "topics": [
                    "0x0eb2ba42ef0de4b5b5b79c5ae8edcd6e93bb29dc5a9b2d12f51e8a8e66a40b5a"
                ],
                "address": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",  # Morpho Blue
            }
        ]

        with patch.object(processor.w3, "keccak") as mock_keccak:
            mock_keccak.return_value.hex.return_value = (
                "0x0eb2ba42ef0de4b5b5b79c5ae8edcd6e93bb29dc5a9b2d12f51e8a8e66a40b5a"
            )

            result = processor.is_liquidation_transaction(transaction, logs)

            assert result is True

    def test_is_liquidation_transaction_wrong_event_address(
        self, processor: MorphoProtocolProcessor
    ) -> None:
        """Test liquidation detection with correct event but wrong address."""
        transaction = {
            "to": "0x1234567890123456789012345678901234567890",
            "input": "0x12345678",
        }
        logs = [
            {
                "topics": [
                    "0x0eb2ba42ef0de4b5b5b79c5ae8edcd6e93bb29dc5a9b2d12f51e8a8e66a40b5a"
                ],
                "address": "0x1234567890123456789012345678901234567890",  # Wrong address
            }
        ]

        with patch.object(processor.w3, "keccak") as mock_keccak:
            mock_keccak.return_value.hex.return_value = (
                "0x0eb2ba42ef0de4b5b5b79c5ae8edcd6e93bb29dc5a9b2d12f51e8a8e66a40b5a"
            )

            result = processor.is_liquidation_transaction(transaction, logs)

            assert result is False

    def test_is_liquidation_transaction_empty_input(
        self, processor: MorphoProtocolProcessor
    ) -> None:
        """Test liquidation detection with empty transaction input."""
        transaction = {
            "to": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",
            "input": "",
        }
        logs: List[Dict[str, Any]] = []

        result = processor.is_liquidation_transaction(transaction, logs)

        assert result is False

    def test_is_liquidation_transaction_short_input(
        self, processor: MorphoProtocolProcessor
    ) -> None:
        """Test liquidation detection with short transaction input."""
        transaction = {
            "to": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",
            "input": "0x1234",  # Too short for method signature
        }
        logs: List[Dict[str, Any]] = []

        result = processor.is_liquidation_transaction(transaction, logs)

        assert result is False

    def test_is_liquidation_transaction_no_logs_no_topics(
        self, processor: MorphoProtocolProcessor
    ) -> None:
        """Test liquidation detection with logs that have no topics."""
        transaction = {
            "to": "0x1234567890123456789012345678901234567890",
            "input": "0x12345678",
        }
        logs = [{"topics": [], "address": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"}]

        result = processor.is_liquidation_transaction(transaction, logs)

        assert result is False

    def test_liquidate_event_abi_structure(
        self, processor: MorphoProtocolProcessor
    ) -> None:
        """Test that the liquidation event ABI has the correct structure."""
        abi = processor.LIQUIDATE_EVENT_ABI

        assert abi["name"] == "Liquidate"
        assert abi["type"] == "event"
        assert abi["anonymous"] is False

        # Check that all expected inputs are present
        inputs = abi["inputs"]
        assert isinstance(inputs, list)
        input_names = [input_item["name"] for input_item in inputs]
        expected_inputs = [
            "id",
            "caller",
            "borrower",
            "repaidAssets",
            "repaidShares",
            "seizedAssets",
            "badDebtAssets",
            "badDebtShares",
        ]

        for expected_input in expected_inputs:
            assert expected_input in input_names

    def test_accrue_interest_event_abi_structure(
        self, processor: MorphoProtocolProcessor
    ) -> None:
        """Test that the accrue interest event ABI has the correct structure."""
        abi = processor.ACCRUE_INTEREST_EVENT_ABI

        assert abi["name"] == "AccrueInterest"
        assert abi["type"] == "event"
        assert abi["anonymous"] is False

        # Check that all expected inputs are present
        inputs = abi["inputs"]
        assert isinstance(inputs, list)
        input_names = [input_item["name"] for input_item in inputs]
        expected_inputs = [
            "id",
            "prevBorrowRate",
            "interest",
            "feeShares",
        ]

        for expected_input in expected_inputs:
            assert expected_input in input_names

    def test_get_market_info(self, processor: MorphoProtocolProcessor) -> None:
        """Test market info getter method."""
        market_id = "0x7b00000000000000000000000000000000000000000000000000000000000001"
        market_info = processor.get_market_info(market_id)

        assert market_info["market_id"] == market_id
        assert "loan_token" in market_info
        assert "collateral_token" in market_info
        assert "oracle" in market_info
        assert "irm" in market_info
        assert "lltv" in market_info

    def test_calculate_liquidation_incentive(
        self, processor: MorphoProtocolProcessor
    ) -> None:
        """Test liquidation incentive calculation."""
        # Test normal case
        market_id = "0x7b00000000000000000000000000000000000000000000000000000000000001"
        lltv = 0.86  # 86% LLTV
        incentive = processor.calculate_liquidation_incentive(market_id, lltv)

        # Should be calculated as: min(1.15, 1/(1 - 0.3*(1 - 0.86)))
        # = min(1.15, 1/(1 - 0.3*0.14)) = min(1.15, 1/0.958) ≈ min(1.15, 1.044) = 1.044
        expected = min(1.15, 1.0 / (1.0 - 0.3 * (1.0 - 0.86)))
        assert abs(incentive - expected) < 0.001

        # Test edge case with high LLTV
        high_lltv = 0.95
        incentive_high = processor.calculate_liquidation_incentive(market_id, high_lltv)
        assert incentive_high <= 1.15

        # Test edge case with LLTV >= 1.0
        max_lltv = 1.0
        incentive_max = processor.calculate_liquidation_incentive(market_id, max_lltv)
        assert incentive_max == 1.15

    def test_get_liquidation_threshold(
        self, processor: MorphoProtocolProcessor
    ) -> None:
        """Test liquidation threshold getter method."""
        market_id = "weth_usdc_86%"
        threshold = processor.get_liquidation_threshold(market_id)
        assert threshold == 0.86

        # Test unknown market (should return default)
        unknown_threshold = processor.get_liquidation_threshold("unknown_market")
        assert unknown_threshold == 0.80

    def test_decode_liquidation_zero_amounts(
        self,
        processor: MorphoProtocolProcessor,
        sample_liquidation_log: Dict[str, Any],
    ) -> None:
        """Test liquidation log decoding with zero amounts."""
        mock_decoded_log = {
            "args": {
                "id": b"{\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03",
                "caller": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
                "borrower": "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
                "repaidAssets": 0,  # Zero repaid
                "repaidShares": 0,
                "seizedAssets": 100000000000000000,
                "badDebtAssets": 0,
                "badDebtShares": 0,
            }
        }

        with patch.object(
            processor.liquidate_event, "process_log", return_value=mock_decoded_log
        ):
            result = processor.decode_liquidation(sample_liquidation_log)

            assert result["liquidation_bonus"] == 0.0
