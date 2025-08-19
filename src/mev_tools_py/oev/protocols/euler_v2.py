from typing import Any, Dict, List

from web3 import Web3

from mev_tools_py.oev.protocols.base import BaseProtocolProcessor


class EulerV2ProtocolProcessor(BaseProtocolProcessor):
    """Euler V2 protocol liquidation processor."""

    protocol = "euler_v2"

    # Euler V2 contract addresses (mainnet)
    # Note: These are example addresses - actual V2 addresses would need to be updated
    EULER_V2_FACTORY = "0x835482FE0532f169024d5E9410199369aAD5C77E"
    EULER_V2_ROUTER = "0x0000000000000000000000000000000000000000"  # TBD when deployed

    # Euler V2 Liquidation event ABI
    # V2 has a different event structure compared to V1
    LIQUIDATION_EVENT_ABI = {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "liquidator",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "violator",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "vault",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "collateralVault",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "repayAssets",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "yieldBalance",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "collateralSeized",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "discount",
                "type": "uint256",
            },
        ],
        "name": "Liquidation",
        "type": "event",
    }

    # Euler V2 also has a BatchLiquidation event for multiple liquidations
    BATCH_LIQUIDATION_EVENT_ABI = {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "liquidator",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "numberOfLiquidations",
                "type": "uint256",
            },
        ],
        "name": "BatchLiquidation",
        "type": "event",
    }

    def __init__(self) -> None:
        """Initialize the Euler V2 protocol processor with web3 instance."""
        self.w3 = Web3()
        # Create event contracts for decoding
        self.liquidation_event = self.w3.eth.contract(
            abi=[self.LIQUIDATION_EVENT_ABI]
        ).events.Liquidation
        self.batch_liquidation_event = self.w3.eth.contract(
            abi=[self.BATCH_LIQUIDATION_EVENT_ABI]
        ).events.BatchLiquidation

    def decode_liquidation(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode a raw Euler V2 liquidation log into a structured event using web3.py ABI decoding.

        Euler V2 Liquidation event structure:
        event Liquidation(
            address indexed liquidator,
            address indexed violator,
            address indexed vault,
            address collateralVault,
            uint256 repayAssets,
            uint256 yieldBalance,
            uint256 collateralSeized,
            uint256 discount
        )
        """
        try:
            # Try to decode as regular Liquidation event first
            try:
                decoded_log = self.liquidation_event.process_log(log)
                args = decoded_log["args"]

                # Calculate liquidation bonus from discount (V2 uses discount factor)
                discount = args["discount"]
                liquidation_bonus = float(discount) / 1e18 if discount > 0 else 0.0

                return {
                    "protocol": self.protocol,
                    "liquidator": args["liquidator"],
                    "user": args["violator"],
                    "debt_repaid": {
                        "vault": args["vault"],
                        "amount": str(args["repayAssets"]),
                    },
                    "collateral_seized": {
                        "vault": args["collateralVault"],
                        "amount": str(args["collateralSeized"]),
                    },
                    "debt_vault": args["vault"],
                    "collateral_vault": args["collateralVault"],
                    "yield_balance": str(args["yieldBalance"]),
                    "liquidation_bonus": liquidation_bonus,
                    "discount": str(args["discount"]),
                    "transaction_hash": log.get("transactionHash", ""),
                    "block_number": log.get("blockNumber", 0),
                    "log_index": log.get("logIndex", 0),
                    "event_type": "single_liquidation",
                }
            except Exception:
                # Try to decode as BatchLiquidation event
                decoded_log = self.batch_liquidation_event.process_log(log)
                args = decoded_log["args"]

                return {
                    "protocol": self.protocol,
                    "liquidator": args["liquidator"],
                    "user": "",  # Not available in batch event
                    "debt_repaid": {
                        "vault": "",
                        "amount": "0",
                    },
                    "collateral_seized": {
                        "vault": "",
                        "amount": "0",
                    },
                    "number_of_liquidations": str(args["numberOfLiquidations"]),
                    "transaction_hash": log.get("transactionHash", ""),
                    "block_number": log.get("blockNumber", 0),
                    "log_index": log.get("logIndex", 0),
                    "event_type": "batch_liquidation",
                }

        except Exception as e:
            raise ValueError(f"Failed to decode Euler V2 liquidation log: {e}") from e

    def enrich_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a decoded Euler V2 liquidation event with protocol-specific analytics.
        """
        enriched = event.copy()

        # Add Euler V2-specific enrichments
        enriched.update(
            {
                "liquidation_type": "euler_v2",
                "is_vault_based": True,  # V2 uses vault-based architecture
                "protocol_version": "2",
                "is_batch_liquidation": event.get("event_type") == "batch_liquidation",
            }
        )

        # Calculate additional metrics for single liquidations
        if event.get("event_type") == "single_liquidation":
            # Calculate liquidation efficiency
            repay_amount = float(event.get("debt_repaid", {}).get("amount", "0"))
            collateral_amount = float(
                event.get("collateral_seized", {}).get("amount", "0")
            )

            if repay_amount > 0 and collateral_amount > 0:
                enriched["liquidation_ratio"] = collateral_amount / repay_amount
                enriched["is_profitable"] = enriched["liquidation_ratio"] > 1.0

            # Add vault-specific information
            enriched["uses_vault_system"] = True
            enriched["vault_based_collateral"] = True

        elif event.get("event_type") == "batch_liquidation":
            # Add batch-specific enrichments
            num_liquidations = int(event.get("number_of_liquidations", "0"))
            enriched["batch_size"] = num_liquidations
            enriched["is_bulk_operation"] = num_liquidations > 1

        return enriched

    def is_liquidation_transaction(
        self, transaction: Dict[str, Any], logs: List[Dict[str, Any]]
    ) -> bool:
        """
        Detect if a transaction contains an Euler V2 liquidation.

        Checks for:
        1. Transaction sent to Euler V2 contracts
        2. Liquidation event logs emitted
        3. Method calls that could trigger liquidations
        """
        to_address = transaction.get("to", "").lower()

        # Check if transaction is sent to Euler V2 contracts
        euler_v2_contracts = {
            self.EULER_V2_FACTORY.lower(),
            self.EULER_V2_ROUTER.lower(),
        }

        # Also check against known vault addresses (would need to be maintained)
        # For now, we'll rely on event detection if contract address doesn't match

        # Get the liquidation event topics from the ABIs
        liquidation_event_topic = self.w3.keccak(
            text="Liquidation(address,address,address,address,uint256,uint256,uint256,uint256)"
        ).to_0x_hex()
        batch_liquidation_event_topic = self.w3.keccak(
            text="BatchLiquidation(address,uint256)"
        ).hex()

        # Check for liquidation events in logs
        for log in logs:
            topics = log.get("topics", [])
            if not topics:
                continue

            event_signature = topics[0].to_0x_hex()

            # Check for Liquidation or BatchLiquidation events
            if event_signature in [
                liquidation_event_topic,
                batch_liquidation_event_topic,
            ]:
                return True

        # Check transaction input for liquidation method calls
        input_data = transaction.get("input", "")
        if input_data and len(input_data) >= 10:  # At least function selector (4 bytes)
            method_signature = input_data[:10]  # First 4 bytes (8 hex chars + 0x)

            # Euler V2 liquidation method signatures
            liquidation_methods = {
                "0x7c025200",  # liquidate method signature (example)
                "0xd9627aa4",  # batchLiquidate method signature (example)
                "0xa694fc3a",  # vault liquidation method
            }

            if method_signature in liquidation_methods:
                return True

        # If we found Euler V2 events but contract address doesn't match known addresses,
        # it might be a vault contract - still consider it a liquidation
        if to_address not in euler_v2_contracts:
            # Check if any Euler V2 events were emitted (indicating vault interaction)
            for log in logs:
                topics = log.get("topics", [])
                if topics and topics[0] in [
                    liquidation_event_topic,
                    batch_liquidation_event_topic,
                ]:
                    return True

        return False
