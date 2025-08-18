from typing import Any, Dict, List

from web3 import Web3

from mev_tools_py.oev.protocols.base import BaseProtocolProcessor


class MorphoProtocolProcessor(BaseProtocolProcessor):
    """Morpho Blue protocol liquidation processor for Ethereum mainnet."""

    protocol = "morpho"

    # Morpho Blue contract address (Ethereum mainnet)
    MORPHO_BLUE_ADDRESS = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"

    # Morpho Blue Liquidate event ABI
    LIQUIDATE_EVENT_ABI = {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "bytes32",
                "name": "id",
                "type": "bytes32",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "caller",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "borrower",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "repaidAssets",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "repaidShares",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "seizedAssets",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "badDebtAssets",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "badDebtShares",
                "type": "uint256",
            },
        ],
        "name": "Liquidate",
        "type": "event",
    }

    # Morpho Blue AccrueInterest event ABI (for market activity detection)
    ACCRUE_INTEREST_EVENT_ABI = {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "bytes32",
                "name": "id",
                "type": "bytes32",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "prevBorrowRate",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "interest",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "feeShares",
                "type": "uint256",
            },
        ],
        "name": "AccrueInterest",
        "type": "event",
    }

    def __init__(self) -> None:
        """Initialize the Morpho protocol processor with web3 instance."""
        self.w3 = Web3()
        # Create event contracts for decoding
        self.liquidate_event = self.w3.eth.contract(
            abi=[self.LIQUIDATE_EVENT_ABI]
        ).events.Liquidate
        self.accrue_interest_event = self.w3.eth.contract(
            abi=[self.ACCRUE_INTEREST_EVENT_ABI]
        ).events.AccrueInterest

    def decode_liquidation(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode a raw Morpho Blue liquidation log into a structured event using web3.py ABI decoding.

        Morpho Blue Liquidate event structure:
        event Liquidate(
            bytes32 indexed id,
            address indexed caller,
            address indexed borrower,
            uint256 repaidAssets,
            uint256 repaidShares,
            uint256 seizedAssets,
            uint256 badDebtAssets,
            uint256 badDebtShares
        )
        """
        try:
            # Decode the log using web3.py
            decoded_log = self.liquidate_event.process_log(log)
            args = decoded_log["args"]

            # Calculate liquidation metrics
            repaid_assets = float(args["repaidAssets"])
            seized_assets = float(args["seizedAssets"])
            bad_debt_assets = float(args["badDebtAssets"])

            # Calculate liquidation bonus/incentive
            liquidation_bonus = 0.0
            if repaid_assets > 0 and seized_assets > 0:
                # Liquidation bonus is the excess collateral received over debt repaid
                liquidation_bonus = (
                    (seized_assets / repaid_assets - 1.0) if repaid_assets > 0 else 0.0
                )

            return {
                "protocol": self.protocol,
                "liquidator": args["caller"],
                "user": args["borrower"],
                "debt_repaid": {
                    "market_id": args["id"].hex(),
                    "assets": str(args["repaidAssets"]),
                    "shares": str(args["repaidShares"]),
                },
                "collateral_seized": {
                    "market_id": args["id"].hex(),
                    "assets": str(args["seizedAssets"]),
                },
                "market_id": args["id"].hex(),
                "liquidation_bonus": liquidation_bonus,
                "bad_debt_assets": str(args["badDebtAssets"]),
                "bad_debt_shares": str(args["badDebtShares"]),
                "has_bad_debt": bad_debt_assets > 0,
                "transaction_hash": log.get("transactionHash", ""),
                "block_number": log.get("blockNumber", 0),
                "log_index": log.get("logIndex", 0),
            }
        except Exception as e:
            raise ValueError(f"Failed to decode Morpho liquidation log: {e}") from e

    def enrich_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a decoded Morpho liquidation event with protocol-specific analytics.
        """
        enriched = event.copy()

        # Add Morpho-specific enrichments
        enriched.update(
            {
                "liquidation_type": "morpho_blue",
                "protocol_version": "blue",
                "is_isolated_market": True,  # Morpho Blue uses isolated markets
                "supports_bad_debt": True,
                "uses_market_id": True,
                "is_permissionless": True,
            }
        )

        # Calculate liquidation metrics
        repaid_assets = float(event.get("debt_repaid", {}).get("assets", "0"))
        seized_assets = float(event.get("collateral_seized", {}).get("assets", "0"))
        bad_debt_assets = float(event.get("bad_debt_assets", "0"))

        if repaid_assets > 0 and seized_assets > 0:
            enriched["liquidation_ratio"] = seized_assets / repaid_assets
            enriched["is_profitable"] = enriched["liquidation_ratio"] > 1.0

            # Calculate liquidation incentive
            liquidation_incentive = enriched["liquidation_ratio"] - 1.0
            enriched["liquidation_incentive"] = liquidation_incentive

            # Classify liquidation size (assume 18 decimal token amounts like ETH/USDC)
            # Convert from wei to token units for size classification
            normalized_repaid = repaid_assets / 1e18
            if normalized_repaid < 1000:  # Small liquidation
                enriched["liquidation_size_category"] = "small"
            elif normalized_repaid < 10000:  # Medium liquidation
                enriched["liquidation_size_category"] = "medium"
            else:  # Large liquidation
                enriched["liquidation_size_category"] = "large"

            # Liquidation efficiency
            if bad_debt_assets > 0:
                enriched["liquidation_efficiency"] = (
                    repaid_assets - bad_debt_assets
                ) / repaid_assets
                enriched["bad_debt_ratio"] = bad_debt_assets / repaid_assets
            else:
                enriched["liquidation_efficiency"] = 1.0
                enriched["bad_debt_ratio"] = 0.0

        # Market-specific information
        enriched["market_based"] = True
        enriched["uses_oracle_pricing"] = True
        enriched["supports_flash_liquidation"] = True
        enriched["immutable_core"] = True

        # Bad debt analysis
        if event.get("has_bad_debt"):
            enriched["liquidation_completeness"] = "partial"
            enriched["requires_bad_debt_handling"] = True
        else:
            enriched["liquidation_completeness"] = "full"
            enriched["requires_bad_debt_handling"] = False

        return enriched

    def is_liquidation_transaction(
        self, transaction: Dict[str, Any], logs: List[Dict[str, Any]]
    ) -> bool:
        """
        Detect if a transaction contains a Morpho Blue liquidation.

        Checks for:
        1. Transaction sent to Morpho Blue contract
        2. Liquidate event logs emitted
        3. Method calls that could trigger liquidations
        """
        to_address = transaction.get("to", "").lower()

        # Check if transaction is sent to Morpho Blue
        morpho_contracts = {
            self.MORPHO_BLUE_ADDRESS.lower(),
        }

        # Get the liquidation event topic from the ABI
        liquidate_event_topic = self.w3.keccak(
            text="Liquidate(bytes32,address,address,uint256,uint256,uint256,uint256,uint256)"
        ).hex()

        # Check for liquidation events in logs
        for log in logs:
            topics = log.get("topics", [])
            if not topics:
                continue

            event_signature = topics[0]

            # Check for Liquidate events
            if event_signature == liquidate_event_topic:
                # Verify the log is from the Morpho Blue contract
                log_address = log.get("address", "").lower()
                if log_address == self.MORPHO_BLUE_ADDRESS.lower():
                    return True

        # Check transaction input for liquidation method calls
        input_data = transaction.get("input", "")
        if input_data and len(input_data) >= 10:  # At least function selector (4 bytes)
            method_signature = input_data[:10]  # First 4 bytes (8 hex chars + 0x)

            # Morpho Blue liquidation method signatures
            liquidation_methods = {
                "0x0748ca67",  # liquidate method signature
                # Morpho Blue has a single liquidate method
            }

            if method_signature in liquidation_methods:
                # Only return True if transaction is to the Morpho Blue contract
                if to_address in morpho_contracts:
                    return True

        return False

    def get_market_info(self, market_id: str) -> Dict[str, Any]:
        """
        Get market information for a specific market ID.
        This would typically query the Morpho Blue contract.
        """
        # This is a placeholder - in a real implementation, this would
        # make calls to the Morpho Blue contract to get market parameters
        return {
            "market_id": market_id,
            "loan_token": "0x0000000000000000000000000000000000000000",  # Would be fetched
            "collateral_token": "0x0000000000000000000000000000000000000000",  # Would be fetched
            "oracle": "0x0000000000000000000000000000000000000000",  # Would be fetched
            "irm": "0x0000000000000000000000000000000000000000",  # Would be fetched
            "lltv": 0.0,  # Loan-to-value ratio, would be fetched
        }

    def calculate_liquidation_incentive(self, market_id: str, lltv: float) -> float:
        """
        Calculate the liquidation incentive for a given market.
        Based on Morpho Blue's liquidation incentive formula.
        """
        # Morpho Blue liquidation incentive calculation:
        # liquidationIncentiveFactor = min(maxLiquidationIncentiveFactor, 1/(1 - cursor*(1 - lltv)))
        # where cursor is typically 0.3 and maxLiquidationIncentiveFactor is typically 1.15

        LIQUIDATION_CURSOR = 0.3
        MAX_LIQUIDATION_INCENTIVE_FACTOR = 1.15

        if lltv >= 1.0:
            return MAX_LIQUIDATION_INCENTIVE_FACTOR

        denominator = 1.0 - LIQUIDATION_CURSOR * (1.0 - lltv)
        if denominator <= 0:
            return MAX_LIQUIDATION_INCENTIVE_FACTOR

        calculated_factor = 1.0 / denominator
        return min(MAX_LIQUIDATION_INCENTIVE_FACTOR, calculated_factor)

    def get_liquidation_threshold(self, market_id: str) -> float:
        """
        Get the liquidation threshold for a specific market.
        This is the LLTV (Loan-to-Liquidation Threshold Value) in Morpho Blue.
        """
        # This is a placeholder - in a real implementation, this would
        # fetch the LLTV from the market parameters
        market_lltv_examples = {
            # Common Morpho Blue market LLTVs (as percentages)
            "weth_usdc_86%": 0.86,  # WETH/USDC at 86% LLTV
            "weth_usdt_86%": 0.86,  # WETH/USDT at 86% LLTV
            "wbtc_usdc_86%": 0.86,  # WBTC/USDC at 86% LLTV
            "wsteth_usdc_86%": 0.86,  # wstETH/USDC at 86% LLTV
        }
        return market_lltv_examples.get(market_id, 0.80)  # Default 80%
