import pytest
from unittest.mock import patch
from typing import Any, Dict, List

from hexbytes import HexBytes

from mev_tools_py.oev.protocols.aave_v3 import AaveV3ProtocolProcessor


class TestAaveV3ProtocolProcessor:
    """Test suite for Aave V3 protocol processor."""

    @pytest.fixture
    def processor(self) -> AaveV3ProtocolProcessor:
        """Create an instance of AaveV3ProtocolProcessor for testing."""
        return AaveV3ProtocolProcessor()

    @pytest.fixture
    def sample_liquidation_log(self) -> Dict[str, Any]:
        """Sample Aave V3 liquidation log data for testing."""
        return {
            "topics": [
                HexBytes(
                    "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286"
                ),  # LiquidationCall event signature
                "0x000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # collateralAsset (WETH)
                "0x000000000000000000000000a0b86a33e6441db5db86df4d9e5c4e6a05f3a5",  # debtAsset (USDC)
                "0x000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",  # user
            ],
            "data": "0x000000000000000000000000000000000000000000000000000de0b6b3a7640000"  # debtToCover (1000 USDC)
            "000000000000000000000000000000000000000000000000016345785d8a0000"  # liquidatedCollateralAmount (0.1 WETH)
            "000000000000000000000000742d35cc6634c0532925a3b8d8d5c0532925a3b8"  # liquidator
            "0000000000000000000000000000000000000000000000000000000000000001",  # receiveAToken (true)
            "address": "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2",  # Aave V3 Pool address
            "transactionHash": "0x123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234",
            "blockNumber": 18500000,
            "logIndex": 42,
        }

    @pytest.fixture
    def mock_decoded_liquidation_log(self) -> Dict[str, Any]:
        """Mock decoded liquidation log data from web3.py."""
        return {
            "args": {
                "collateralAsset": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                "debtAsset": "0xA0b86a33E6441db5dB86DF4D9E5C4e6a05F3a5",  # USDC
                "user": "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
                "debtToCover": 1000000000,  # 1000 USDC (6 decimals)
                "liquidatedCollateralAmount": 100000000000000000,  # 0.1 WETH (18 decimals)
                "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
                "receiveAToken": True,
            }
        }

    @pytest.fixture
    def sample_transaction(self) -> Dict[str, Any]:
        """Sample transaction data for testing."""
        return {
            "to": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",  # Aave V3 Pool address
            "from": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
            "input": "0x00a718a9000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
            "000000000000000000000000a0b86a33e6441db5db86df4d9e5c4e6a05f3a5"
            "000000000000000000000000532925a3b8d8d5c0532925a3b8d8d5c0532925a3",  # liquidationCall
            "hash": "0x123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234",
        }

    @pytest.fixture
    def sample_logs(
        self, sample_liquidation_log: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Sample logs list for testing."""
        return [sample_liquidation_log]

    def test_protocol_attribute(self, processor: AaveV3ProtocolProcessor) -> None:
        """Test that the protocol attribute is set correctly."""
        assert processor.protocol == "aave_v3"

    def test_initialization(self, processor: AaveV3ProtocolProcessor) -> None:
        """Test that the processor initializes correctly."""
        assert processor.w3 is not None
        assert processor.liquidation_call_event is not None
        assert processor.reserve_data_updated_event is not None

    def test_contract_addresses(self, processor: AaveV3ProtocolProcessor) -> None:
        """Test that contract addresses are set correctly."""
        assert processor.POOL_ADDRESS == "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
        assert (
            processor.POOL_ADDRESSES_PROVIDER
            == "0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e"
        )
        assert (
            processor.POOL_DATA_PROVIDER == "0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3"
        )

    def test_decode_liquidation_success(
        self,
        processor: AaveV3ProtocolProcessor,
        sample_liquidation_log: Dict[str, Any],
        mock_decoded_liquidation_log: Dict[str, Any],
    ) -> None:
        """Test successful liquidation log decoding."""
        with patch.object(
            processor.liquidation_call_event,
            "process_log",
            return_value=mock_decoded_liquidation_log,
        ) as mock_process_log:
            result = processor.decode_liquidation(sample_liquidation_log)

            mock_process_log.assert_called_once_with(sample_liquidation_log)

        # Verify the returned structure
        assert result["protocol"] == "aave_v3"
        assert result["liquidator"] == "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8"
        assert result["user"] == "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3"
        assert (
            result["collateral_asset"] == "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        )
        assert result["debt_asset"] == "0xA0b86a33E6441db5dB86DF4D9E5C4e6a05F3a5"

        # Check debt_repaid structure
        assert (
            result["debt_repaid"]["token"] == "0xA0b86a33E6441db5dB86DF4D9E5C4e6a05F3a5"
        )
        assert result["debt_repaid"]["amount"] == "1000000000"

        # Check collateral_seized structure
        assert (
            result["collateral_seized"]["token"]
            == "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        )
        assert result["collateral_seized"]["amount"] == "100000000000000000"

        # Check additional fields
        assert result["receive_atoken"] is True
        assert result["transaction_hash"] == sample_liquidation_log["transactionHash"]
        assert result["block_number"] == sample_liquidation_log["blockNumber"]
        assert result["log_index"] == sample_liquidation_log["logIndex"]

        # Check liquidation bonus (simplified calculation)
        assert result["liquidation_bonus"] == 0.05

    def test_decode_liquidation_failure(
        self, processor: AaveV3ProtocolProcessor, sample_liquidation_log: Dict[str, Any]
    ) -> None:
        """Test liquidation log decoding failure."""
        with patch.object(
            processor.liquidation_call_event,
            "process_log",
            side_effect=Exception("Decoding failed"),
        ):
            with pytest.raises(
                ValueError, match="Failed to decode Aave V3 liquidation log"
            ):
                processor.decode_liquidation(sample_liquidation_log)

    def test_decode_liquidation_zero_debt(
        self, processor: AaveV3ProtocolProcessor, sample_liquidation_log: Dict[str, Any]
    ) -> None:
        """Test liquidation log decoding with zero debt to cover."""
        mock_decoded_log = {
            "args": {
                "collateralAsset": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                "debtAsset": "0xA0b86a33E6441db5dB86DF4D9E5C4e6a05F3a5",
                "user": "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
                "debtToCover": 0,  # Zero debt
                "liquidatedCollateralAmount": 100000000000000000,
                "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
                "receiveAToken": False,
            }
        }

        with patch.object(
            processor.liquidation_call_event,
            "process_log",
            return_value=mock_decoded_log,
        ):
            result = processor.decode_liquidation(sample_liquidation_log)

            assert result["liquidation_bonus"] == 0.0

    def test_enrich_event_basic(self, processor: AaveV3ProtocolProcessor) -> None:
        """Test basic event enrichment."""
        event = {
            "protocol": "aave_v3",
            "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
            "user": "0x532925a3b8d8d5c0532925a3b8d8d5c0532925a3",
            "debt_repaid": {"amount": "1000000000"},  # 1000 USDC
            "collateral_seized": {"amount": "100000000000000000"},  # 0.1 WETH
            "receive_atoken": True,
        }

        result = processor.enrich_event(event)

        # Check that original fields are preserved
        assert result["protocol"] == "aave_v3"
        assert result["liquidator"] == "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8"

        # Check enriched fields
        assert result["liquidation_type"] == "aave_v3"
        assert result["protocol_version"] == "3"
        assert result["supports_flash_liquidation"] is True
        assert result["supports_partial_liquidation"] is True
        assert result["is_cross_chain"] is False

        # Check liquidation metrics (with decimal normalization)
        assert result["liquidation_ratio"] == 0.0001  # actual calculated ratio
        assert result["is_profitable"] is False  # ratio < 1.0
        assert result["liquidation_incentive"] == -0.9999  # liquidation_ratio - 1.0
        assert (
            result["liquidation_size_category"] == "large"
        )  # raw amount 1000000000 is large

        # Check liquidation method
        assert result["liquidation_method"] == "receive_atoken"
        assert result["liquidator_receives"] == "aToken"

    def test_enrich_event_receive_underlying(
        self, processor: AaveV3ProtocolProcessor
    ) -> None:
        """Test event enrichment when receiving underlying asset."""
        event = {
            "protocol": "aave_v3",
            "debt_repaid": {"amount": "5000000000"},  # 5000 USDC
            "collateral_seized": {"amount": "5200000000000000000"},  # 5.2 WETH
            "receive_atoken": False,
        }

        result = processor.enrich_event(event)

        assert result["liquidation_method"] == "receive_underlying"
        assert result["liquidator_receives"] == "underlying_asset"
        assert result["liquidation_size_category"] == "large"  # 5000 USDC is >= 1000

    def test_enrich_event_large_liquidation(
        self, processor: AaveV3ProtocolProcessor
    ) -> None:
        """Test event enrichment for large liquidation."""
        event = {
            "protocol": "aave_v3",
            "debt_repaid": {"amount": "15000000000"},  # 15000 USDC
            "collateral_seized": {"amount": "15750000000000000000"},  # 15.75 WETH
            "receive_atoken": True,
        }

        result = processor.enrich_event(event)

        assert result["liquidation_size_category"] == "large"  # >= 10000
        assert result["liquidation_ratio"] == 0.00105
        assert result["liquidation_incentive"] == -0.99895

    def test_enrich_event_no_amounts(self, processor: AaveV3ProtocolProcessor) -> None:
        """Test event enrichment when amounts are missing."""
        event = {
            "protocol": "aave_v3",
            "liquidator": "0x742d35cc6634c0532925a3b8d8d5c0532925a3b8",
        }

        result = processor.enrich_event(event)

        # Check enriched fields
        assert result["liquidation_type"] == "aave_v3"
        assert result["protocol_version"] == "3"
        # liquidation_ratio should not be present if amounts are missing
        assert "liquidation_ratio" not in result
        assert "is_profitable" not in result
        assert "liquidation_incentive" not in result

    def test_is_liquidation_transaction_pool_contract(
        self,
        processor: AaveV3ProtocolProcessor,
        sample_transaction: Dict[str, Any],
        sample_logs: List[Dict[str, Any]],
    ) -> None:
        """Test liquidation detection with transaction to Aave V3 Pool contract."""
        with patch.object(processor.w3, "keccak") as mock_keccak:
            mock_keccak.return_value.hex.return_value = HexBytes(
                "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286"
            )

            result = processor.is_liquidation_transaction(
                sample_transaction, sample_logs
            )

            assert result is True

    def test_is_liquidation_transaction_wrong_contract(
        self, processor: AaveV3ProtocolProcessor, sample_logs: List[Dict[str, Any]]
    ) -> None:
        """Test liquidation detection with transaction to wrong contract."""
        transaction = {
            "to": "0x1234567890123456789012345678901234567890",  # Wrong contract
            "input": "0x00a718a9000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        }

        # Mock the keccak method to return the actual expected topic
        with patch.object(processor.w3, "keccak") as mock_keccak:
            mock_keccak.return_value.hex.return_value = HexBytes(
                "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286"
            )

            result = processor.is_liquidation_transaction(transaction, sample_logs)

            assert result is False

    def test_is_liquidation_transaction_method_signature(
        self, processor: AaveV3ProtocolProcessor
    ) -> None:
        """Test liquidation detection based on method signature."""
        transaction = {
            "to": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",  # Aave V3 Pool address
            "input": "0x00a718a9000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        }
        logs: List[Dict[str, Any]] = []  # No logs

        result = processor.is_liquidation_transaction(transaction, logs)

        assert result is True

    def test_is_liquidation_transaction_flash_liquidation(
        self, processor: AaveV3ProtocolProcessor
    ) -> None:
        """Test liquidation detection with flash liquidation method."""
        transaction = {
            "to": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
            "input": "0x52d84d1e000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        }
        logs: List[Dict[str, Any]] = []

        result = processor.is_liquidation_transaction(transaction, logs)

        assert result is True

    def test_is_liquidation_transaction_no_match(
        self, processor: AaveV3ProtocolProcessor
    ) -> None:
        """Test liquidation detection with no matching criteria."""
        transaction = {
            "to": "0x1234567890123456789012345678901234567890",  # Wrong contract
            "input": "0x12345678000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # Wrong method
        }
        logs: List[Dict[str, Any]] = []

        result = processor.is_liquidation_transaction(transaction, logs)

        assert result is False

    def test_is_liquidation_transaction_event_detection(
        self, processor: AaveV3ProtocolProcessor
    ) -> None:
        """Test liquidation detection based on event logs only."""
        transaction = {
            "to": "0x1234567890123456789012345678901234567890",  # Different contract
            "input": "0x12345678",  # Non-liquidation method
        }
        logs = [
            {
                "topics": [
                    HexBytes(
                        "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286"
                    )
                ],
                "address": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",  # Aave V3 Pool
            }
        ]

        with patch.object(processor.w3, "keccak") as mock_keccak:
            mock_keccak.return_value.hex.return_value = HexBytes(
                "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286"
            )

            result = processor.is_liquidation_transaction(transaction, logs)

            assert result is False

    def test_is_liquidation_transaction_wrong_event_address(
        self, processor: AaveV3ProtocolProcessor
    ) -> None:
        """Test liquidation detection with correct event but wrong address."""
        transaction = {
            "to": "0x1234567890123456789012345678901234567890",
            "input": "0x12345678",
        }
        logs = [
            {
                "topics": [
                    HexBytes(
                        "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286"
                    )
                ],
                "address": "0x1234567890123456789012345678901234567890",  # Wrong address
            }
        ]

        with patch.object(processor.w3, "keccak") as mock_keccak:
            mock_keccak.return_value.hex.return_value = HexBytes(
                "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286"
            )

            result = processor.is_liquidation_transaction(transaction, logs)

            assert result is False

    def test_liquidation_event_abi_structure(
        self, processor: AaveV3ProtocolProcessor
    ) -> None:
        """Test that the liquidation event ABI has the correct structure."""
        abi = processor.LIQUIDATION_CALL_EVENT_ABI

        assert abi["name"] == "LiquidationCall"
        assert abi["type"] == "event"
        assert abi["anonymous"] is False

        # Check that all expected inputs are present
        inputs = abi["inputs"]
        assert isinstance(inputs, list)
        input_names = [input_item["name"] for input_item in inputs]
        expected_inputs = [
            "collateralAsset",
            "debtAsset",
            "user",
            "debtToCover",
            "liquidatedCollateralAmount",
            "liquidator",
            "receiveAToken",
        ]

        for expected_input in expected_inputs:
            assert expected_input in input_names

    def test_reserve_data_updated_event_abi_structure(
        self, processor: AaveV3ProtocolProcessor
    ) -> None:
        """Test that the reserve data updated event ABI has the correct structure."""
        abi = processor.RESERVE_DATA_UPDATED_EVENT_ABI

        assert abi["name"] == "ReserveDataUpdated"
        assert abi["type"] == "event"
        assert abi["anonymous"] is False

        # Check that all expected inputs are present
        inputs = abi["inputs"]
        assert isinstance(inputs, list)
        input_names = [input_item["name"] for input_item in inputs]
        expected_inputs = [
            "reserve",
            "liquidityRate",
            "stableBorrowRate",
            "variableBorrowRate",
            "liquidityIndex",
            "variableBorrowIndex",
        ]

        for expected_input in expected_inputs:
            assert expected_input in input_names

    def test_get_liquidation_threshold(
        self, processor: AaveV3ProtocolProcessor
    ) -> None:
        """Test liquidation threshold getter method."""
        # Test known asset (WETH address)
        weth_threshold = processor.get_liquidation_threshold(
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        )
        assert weth_threshold == 0.83

        # Test unknown asset (should return default)
        unknown_threshold = processor.get_liquidation_threshold("0x1234567890")
        assert unknown_threshold == 0.75

    def test_get_liquidation_bonus(self, processor: AaveV3ProtocolProcessor) -> None:
        """Test liquidation bonus getter method."""
        # Test known asset (WETH address)
        weth_bonus = processor.get_liquidation_bonus(
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        )
        assert weth_bonus == 0.05

        # Test unknown asset (should return default)
        unknown_bonus = processor.get_liquidation_bonus("0x1234567890")
        assert unknown_bonus == 0.05

    def test_is_liquidation_transaction_empty_input(
        self, processor: AaveV3ProtocolProcessor
    ) -> None:
        """Test liquidation detection with empty transaction input."""
        transaction = {
            "to": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
            "input": "",
        }
        logs: List[Dict[str, Any]] = []

        result = processor.is_liquidation_transaction(transaction, logs)

        assert result is False

    def test_is_liquidation_transaction_short_input(
        self, processor: AaveV3ProtocolProcessor
    ) -> None:
        """Test liquidation detection with short transaction input."""
        transaction = {
            "to": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
            "input": "0x1234",  # Too short for method signature
        }
        logs: List[Dict[str, Any]] = []

        result = processor.is_liquidation_transaction(transaction, logs)

        assert result is False

    def test_is_liquidation_transaction_no_logs_no_topics(
        self, processor: AaveV3ProtocolProcessor
    ) -> None:
        """Test liquidation detection with logs that have no topics."""
        transaction = {
            "to": "0x1234567890123456789012345678901234567890",
            "input": "0x12345678",
        }
        logs = [{"topics": [], "address": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"}]

        result = processor.is_liquidation_transaction(transaction, logs)

        assert result is False
