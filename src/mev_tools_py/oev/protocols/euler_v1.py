from typing import Any, Dict, List, Tuple

from web3 import Web3

from mev_tools_py.oev.protocols.base import BaseProtocolProcessor


class EulerProtocolProcessor(BaseProtocolProcessor):
    """Euler protocol liquidation processor."""

    protocol = "euler"

    # Euler V1 contract addresses (mainnet)
    EULER_MAINNET_ADDRESS = "0x27182842E098f60e3D576794A5bFFb0777E025d3"
    EXEC_PROXY_ADDRESS = "0x59828FdF7ee634AaaD3f58B19fDBa3b03E2a9d80"

    # Euler Liquidation event ABI
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
                "name": "underlying",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "collateral",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "repay",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "yield",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "healthScore",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "baseDiscount",
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

    def __init__(self) -> None:
        """Initialize the Euler protocol processor with web3 instance."""
        self.w3 = Web3()
        # Create event contract for decoding
        self.liquidation_event = self.w3.eth.contract(
            abi=[self.LIQUIDATION_EVENT_ABI]
        ).events.Liquidation

    def decode_liquidation(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode a raw Euler liquidation log into a structured event using web3.py ABI decoding.

        Euler Liquidation event structure:
        event Liquidation(
            address indexed liquidator,
            address indexed violator,
            address indexed underlying,
            address collateral,
            uint256 repay,
            uint256 yield,
            uint256 healthScore,
            uint256 baseDiscount,
            uint256 discount
        )
        """
        try:
            # Decode the log using web3.py
            decoded_log = self.liquidation_event.process_log(log)
            args = decoded_log["args"]

            # Calculate liquidation bonus from discount (Euler uses discount factor)
            discount = args["discount"]
            base_discount = args["baseDiscount"]
            liquidation_bonus = (
                float(discount - base_discount) / 1e18
                if discount > base_discount
                else 0.0
            )

            return {
                "protocol": self.protocol,
                "liquidator": args["liquidator"],
                "user": args["violator"],
                "debt_repaid": {
                    "token": args["underlying"],
                    "amount": str(args["repay"]),
                },
                "collateral_seized": {
                    "token": args["collateral"],
                    "amount": str(args["yield"]),
                },
                "underlying_asset": args["underlying"],
                "collateral_asset": args["collateral"],
                "liquidation_bonus": liquidation_bonus,
                "health_score": str(args["healthScore"]),
                "base_discount": str(args["baseDiscount"]),
                "discount": str(args["discount"]),
                "transaction_hash": log.get("transactionHash", ""),
                "block_number": log.get("blockNumber", 0),
                "log_index": log.get("logIndex", 0),
            }
        except Exception as e:
            raise ValueError(f"Failed to decode Euler liquidation log: {e}") from e

    def enrich_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a decoded Euler liquidation event with protocol-specific analytics.
        """
        enriched = event.copy()

        # Add Euler-specific enrichments
        enriched.update(
            {
                "liquidation_type": "euler_v1",
                "is_soft_liquidation": False,  # Euler uses soft liquidations
                "risk_adjusted_value": 0.0,  # Would calculate based on risk factors
                "liquidation_incentive": 0.0,  # Would extract from discount parameters
                "protocol_version": "1",
            }
        )

        # Calculate additional metrics
        if event.get("health_score"):
            enriched["health_factor"] = float(event["health_score"]) / 1e18
            enriched["is_undercollateralized"] = enriched["health_factor"] < 1.0

        return enriched

    def is_liquidation_transaction(
        self, transaction: Dict[str, Any], logs: List[Dict[str, Any]]
    ) -> Tuple[bool, int]:
        """
        Detect if a transaction contains an Euler liquidation.

        Checks for:
        1. Transaction sent to Euler main contract or execution proxy
        2. Liquidation event logs emitted
        3. Method calls that could trigger liquidations
        """
        to_address = transaction.get("to", "").lower()

        # Check if transaction is sent to Euler contracts
        euler_contracts = {
            self.EULER_MAINNET_ADDRESS.lower(),
            self.EXEC_PROXY_ADDRESS.lower(),
        }

        if to_address not in euler_contracts:
            return False, -1

        # Get the liquidation event topic from the ABI
        liquidation_event_topic = self.w3.keccak(
            text="Liquidation(address,address,address,address,uint256,uint256,uint256,uint256,uint256)"
        ).to_0x_hex()

        print(liquidation_event_topic)
        # Check for liquidation events in logs
        for idx, log in enumerate(logs):
            topics = log.get("topics", [])
            if not topics:
                continue

            event_signature = topics[0].to_0x_hex()

            # Check for Liquidation events
            if event_signature == liquidation_event_topic:
                return True, idx

        return False, -1
