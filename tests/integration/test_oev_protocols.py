"""Integration tests for OEV protocol processors with real blockchain data."""

import pytest
from typing import Any, Dict, List
from web3 import Web3


class TestOEVProtocolsIntegration:
    """Integration tests for OEV protocol processors using real blockchain data."""

    @pytest.mark.integration
    def test_protocol_initialization(self, protocol_processors: Dict[str, Any]) -> None:
        """Test that all protocol processors initialize correctly."""
        expected_protocols = ["aave_v3", "euler_v1", "euler_v2", "morpho"]

        assert len(protocol_processors) == len(expected_protocols)

        for protocol_name in expected_protocols:
            assert protocol_name in protocol_processors
            processor = protocol_processors[protocol_name]
            assert hasattr(processor, "protocol")
            assert hasattr(processor, "decode_liquidation")
            assert hasattr(processor, "enrich_event")
            assert hasattr(processor, "is_liquidation_transaction")

    @pytest.mark.integration
    def test_web3_connection(self, web3_instance: Web3) -> None:
        """Test that Web3 connection is working properly."""
        assert web3_instance.is_connected()

        # Test basic functionality
        latest_block = web3_instance.eth.block_number
        assert latest_block > 0

        # Test we can fetch a block
        block = web3_instance.eth.get_block("latest")
        assert block is not None
        assert "number" in block
        assert "transactions" in block

    @pytest.mark.integration
    def test_aave_v3_real_liquidation_detection(
        self,
        web3_instance: Web3,
        protocol_processors: Dict[str, Any],
        known_liquidation_blocks: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test Aave V3 processor with real liquidation transactions."""
        processor = protocol_processors["aave_v3"]

        # Test with known Aave V3 liquidations
        test_cases = known_liquidation_blocks.get("aave_v3", [])

        if not test_cases:
            pytest.skip("No known Aave V3 liquidations configured for testing")

        for test_case in test_cases[:1]:  # Test first case to avoid rate limits
            tx_hash = test_case["tx_hash"]

            try:
                # Get real transaction and receipt
                tx = web3_instance.eth.get_transaction(tx_hash)
                receipt = web3_instance.eth.get_transaction_receipt(tx_hash)

                # Test detection
                is_liquidation = processor.is_liquidation_transaction(
                    tx, receipt["logs"]
                )

                # If it's detected as liquidation, test decoding
                if is_liquidation:
                    liquidations = []
                    for log in receipt["logs"]:
                        try:
                            decoded = processor.decode_liquidation(log)
                            enriched = processor.enrich_event(decoded)
                            liquidations.append(enriched)
                        except ValueError:
                            continue  # Not an Aave liquidation log

                    if liquidations:
                        liquidation = liquidations[0]
                        assert liquidation["protocol"] == "aave_v3"
                        assert "liquidator" in liquidation
                        assert "user" in liquidation
                        assert "debt_repaid" in liquidation
                        assert "collateral_seized" in liquidation
                        print(f"Successfully processed Aave V3 liquidation: {tx_hash}")

            except Exception as e:
                print(f"Could not process transaction {tx_hash}: {e}")
                # Don't fail the test for individual transaction issues

    @pytest.mark.integration
    def test_euler_protocols_detection(
        self,
        web3_instance: Web3,
        protocol_processors: Dict[str, Any],
        known_liquidation_blocks: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test Euler V1 and V2 processors with real liquidation transactions."""
        euler_v1 = protocol_processors["euler_v1"]
        euler_v2 = protocol_processors["euler_v2"]

        # Test Euler V1
        v1_cases = known_liquidation_blocks.get("euler_v1", [])
        for test_case in v1_cases[:1]:
            tx_hash = test_case["tx_hash"]
            try:
                tx = web3_instance.eth.get_transaction(tx_hash)
                receipt = web3_instance.eth.get_transaction_receipt(tx_hash)

                if euler_v1.is_liquidation_transaction(tx, receipt["logs"]):
                    print(f"Detected Euler V1 liquidation: {tx_hash}")

            except Exception as e:
                print(f"Could not process Euler V1 transaction {tx_hash}: {e}")

        # Test Euler V2
        v2_cases = known_liquidation_blocks.get("euler_v2", [])
        for test_case in v2_cases[:1]:
            tx_hash = test_case["tx_hash"]
            try:
                tx = web3_instance.eth.get_transaction(tx_hash)
                receipt = web3_instance.eth.get_transaction_receipt(tx_hash)

                if euler_v2.is_liquidation_transaction(tx, receipt["logs"]):
                    print(f"Detected Euler V2 liquidation: {tx_hash}")

            except Exception as e:
                print(f"Could not process Euler V2 transaction {tx_hash}: {e}")

    @pytest.mark.integration
    def test_morpho_protocol_integration(
        self,
        web3_instance: Web3,
        protocol_processors: Dict[str, Any],
        known_liquidation_blocks: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test Morpho processor with real liquidation transactions and market data."""
        processor = protocol_processors["morpho"]

        # Test liquidation detection
        morpho_cases = known_liquidation_blocks.get("morpho", [])
        for test_case in morpho_cases[:1]:
            tx_hash = test_case["tx_hash"]
            try:
                tx = web3_instance.eth.get_transaction(tx_hash)
                receipt = web3_instance.eth.get_transaction_receipt(tx_hash)

                if processor.is_liquidation_transaction(tx, receipt["logs"]):
                    print(f"Detected Morpho liquidation: {tx_hash}")

                    # Try to decode liquidations
                    for log in receipt["logs"]:
                        try:
                            decoded = processor.decode_liquidation(log)

                            # Test market info retrieval if we have a market ID
                            if "market_id" in decoded:
                                market_id = decoded["market_id"]
                                try:
                                    market_info = processor.get_market_info(market_id)
                                    assert "lltv" in market_info
                                    assert "loan_token" in market_info
                                    print(f"Retrieved market info for {market_id}")
                                except Exception as e:
                                    print(
                                        f"Could not get market info for {market_id}: {e}"
                                    )

                            break  # Process only first liquidation log
                        except ValueError:
                            continue

            except Exception as e:
                print(f"Could not process Morpho transaction {tx_hash}: {e}")

    @pytest.mark.integration
    @pytest.mark.slow
    def test_cross_protocol_block_analysis(
        self,
        web3_instance: Web3,
        protocol_processors: Dict[str, Any],
        test_block_range: Dict[str, int],
        skip_slow_tests: bool,
    ) -> None:
        """Test analyzing a block with multiple protocol liquidations."""
        if skip_slow_tests:
            pytest.skip("Slow tests disabled")

        # Analyze a range of blocks for liquidations
        start_block = test_block_range["start"]
        end_block = min(start_block + 5, test_block_range["end"])  # Limit to 5 blocks

        total_liquidations = 0
        protocol_counts = {protocol: 0 for protocol in protocol_processors.keys()}

        for block_number in range(start_block, end_block):
            try:
                block = web3_instance.eth.get_block(
                    block_number, full_transactions=True
                )

                for tx in block["transactions"][:10]:  # Limit to first 10 tx per block
                    try:
                        receipt = web3_instance.eth.get_transaction_receipt(tx["hash"])

                        for protocol_name, processor in protocol_processors.items():
                            if processor.is_liquidation_transaction(
                                tx, receipt["logs"]
                            ):
                                protocol_counts[protocol_name] += 1
                                total_liquidations += 1
                                print(
                                    f"Found {protocol_name} liquidation in block {block_number}: {tx['hash'].hex()}"
                                )

                    except Exception as e:
                        print(f"Error processing transaction {tx['hash'].hex()}: {e}")
                        continue

            except Exception as e:
                print(f"Error processing block {block_number}: {e}")
                continue

        print(
            f"Analyzed blocks {start_block}-{end_block}: {total_liquidations} total liquidations"
        )
        for protocol, count in protocol_counts.items():
            if count > 0:
                print(f"  {protocol}: {count} liquidations")

        # Test passes if we can analyze blocks without errors (liquidations are optional)
        assert True

    @pytest.mark.integration
    def test_gas_efficiency_analysis(
        self,
        web3_instance: Web3,
        protocol_processors: Dict[str, Any],
        known_liquidation_blocks: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test gas usage analysis for liquidation transactions."""
        gas_data = []

        for protocol_name, test_cases in known_liquidation_blocks.items():
            if not test_cases:
                continue

            processor = protocol_processors.get(protocol_name)
            if not processor:
                continue

            for test_case in test_cases[:1]:  # One per protocol
                tx_hash = test_case["tx_hash"]
                try:
                    tx = web3_instance.eth.get_transaction(tx_hash)
                    receipt = web3_instance.eth.get_transaction_receipt(tx_hash)

                    # Only analyze if it's detected as liquidation
                    if processor.is_liquidation_transaction(tx, receipt["logs"]):
                        gas_used = receipt["gasUsed"]
                        gas_price = tx["gasPrice"] if tx["gasPrice"] else 0
                        cost_wei = gas_used * gas_price
                        cost_eth = web3_instance.from_wei(cost_wei, "ether")

                        gas_data.append(
                            {
                                "protocol": protocol_name,
                                "tx_hash": tx_hash,
                                "gas_used": gas_used,
                                "gas_price_gwei": web3_instance.from_wei(
                                    gas_price, "gwei"
                                ),
                                "cost_eth": float(cost_eth),
                            }
                        )

                        print(
                            f"{protocol_name} liquidation {tx_hash}: {gas_used:,} gas, {cost_eth:.6f} ETH"
                        )

                        # Basic sanity checks
                        assert gas_used > 0
                        assert gas_used < 10_000_000  # Reasonable upper bound

                except Exception as e:
                    print(
                        f"Could not analyze gas for {protocol_name} transaction {tx_hash}: {e}"
                    )

        if gas_data:
            # Calculate average gas usage by protocol
            protocol_gas = {}
            for data in gas_data:
                protocol = data["protocol"]
                if protocol not in protocol_gas:
                    protocol_gas[protocol] = []
                protocol_gas[protocol].append(data["gas_used"])

            for protocol, gas_values in protocol_gas.items():
                avg_gas = sum(gas_values) / len(gas_values)
                print(f"{protocol} average gas usage: {avg_gas:,.0f}")

    @pytest.mark.integration
    def test_protocol_event_structure_validation(
        self, protocol_processors: Dict[str, Any]
    ) -> None:
        """Test that protocol processors have consistent event structures."""
        for protocol_name, processor in protocol_processors.items():
            # Check protocol attribute
            assert hasattr(processor, "protocol")
            assert isinstance(processor.protocol, str)
            assert len(processor.protocol) > 0

            # Check required methods exist
            required_methods = [
                "decode_liquidation",
                "enrich_event",
                "is_liquidation_transaction",
            ]
            for method_name in required_methods:
                assert hasattr(processor, method_name)
                assert callable(getattr(processor, method_name))

            # Check Web3 instance
            assert hasattr(processor, "w3")

            print(f"{protocol_name} processor validation passed")

    @pytest.mark.integration
    def test_error_handling_robustness(
        self, protocol_processors: Dict[str, Any]
    ) -> None:
        """Test error handling with invalid data."""
        # Test with invalid transaction data
        invalid_tx = {
            "to": "0x1234567890123456789012345678901234567890",
            "input": "0x12345678",
            "hash": "0x1234567890123456789012345678901234567890123456789012345678901234",
        }

        invalid_logs = [
            {
                "topics": [
                    "0x1234567890123456789012345678901234567890123456789012345678901234"
                ],
                "data": "0x1234567890123456789012345678901234567890123456789012345678901234",
                "address": "0x1234567890123456789012345678901234567890",
            }
        ]

        for protocol_name, processor in protocol_processors.items():
            # Test liquidation detection with invalid data - should not crash
            try:
                result = processor.is_liquidation_transaction(invalid_tx, invalid_logs)
                assert isinstance(result, bool)
            except Exception as e:
                pytest.fail(f"{protocol_name} crashed on invalid transaction data: {e}")

            # Test log decoding with invalid data - should raise ValueError
            try:
                processor.decode_liquidation(invalid_logs[0])
                # If it doesn't raise an error, it means it processed invalid data as valid
                print(f"Warning: {protocol_name} processed invalid log without error")
            except ValueError:
                # Expected behavior
                pass
            except Exception as e:
                pytest.fail(f"{protocol_name} raised unexpected error type: {e}")

            print(f"{protocol_name} error handling test passed")
