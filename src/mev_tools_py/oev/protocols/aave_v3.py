from typing import Any, Dict, List, Tuple

from web3 import Web3

from mev_tools_py.oev.protocols.base import BaseProtocolProcessor


class AaveV3ProtocolProcessor(BaseProtocolProcessor):
    """Aave V3 protocol liquidation processor for Ethereum mainnet."""

    protocol = "aave_v3"

    # Aave V3 contract addresses (Ethereum mainnet)
    POOL_ADDRESS = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
    POOL_ADDRESSES_PROVIDER = "0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e"
    POOL_DATA_PROVIDER = "0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3"

    # Aave V3 LiquidationCall event ABI
    LIQUIDATION_CALL_EVENT_ABI = {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "collateralAsset",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "debtAsset",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "user",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "debtToCover",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "liquidatedCollateralAmount",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "liquidator",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "bool",
                "name": "receiveAToken",
                "type": "bool",
            },
        ],
        "name": "LiquidationCall",
        "type": "event",
    }

    # Aave V3 ReserveDataUpdated event ABI (for tracking reserve state changes)
    RESERVE_DATA_UPDATED_EVENT_ABI = {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "reserve",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "liquidityRate",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "stableBorrowRate",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "variableBorrowRate",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "liquidityIndex",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "variableBorrowIndex",
                "type": "uint256",
            },
        ],
        "name": "ReserveDataUpdated",
        "type": "event",
    }

    def __init__(self) -> None:
        """Initialize the Aave V3 protocol processor with web3 instance."""
        self.w3 = Web3()
        # Create event contracts for decoding
        self.liquidation_call_event = self.w3.eth.contract(
            abi=[self.LIQUIDATION_CALL_EVENT_ABI]
        ).events.LiquidationCall
        self.reserve_data_updated_event = self.w3.eth.contract(
            abi=[self.RESERVE_DATA_UPDATED_EVENT_ABI]
        ).events.ReserveDataUpdated

    def decode_liquidation(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode a raw Aave V3 liquidation log into a structured event using web3.py ABI decoding.

        Aave V3 LiquidationCall event structure:
        event LiquidationCall(
            address indexed collateralAsset,
            address indexed debtAsset,
            address indexed user,
            uint256 debtToCover,
            uint256 liquidatedCollateralAmount,
            address liquidator,
            bool receiveAToken
        )
        """
        try:
            # Decode the log using web3.py
            decoded_log = self.liquidation_call_event.process_log(log)
            args = decoded_log["args"]

            # Calculate liquidation bonus (need to account for different decimals)
            # For accurate calculation, we'd need to know token decimals and prices
            # This is a simplified calculation assuming proper price conversion
            debt_to_cover = float(args["debtToCover"])

            if debt_to_cover > 0:
                # Simplified bonus calculation - in practice would need price feeds
                liquidation_bonus = 0.05  # Default 5% for Aave V3
            else:
                liquidation_bonus = 0.0

            return {
                "protocol": self.protocol,
                "liquidator": args["liquidator"],
                "user": args["user"],
                "debt_repaid": {
                    "token": args["debtAsset"],
                    "amount": str(args["debtToCover"]),
                },
                "collateral_seized": {
                    "token": args["collateralAsset"],
                    "amount": str(args["liquidatedCollateralAmount"]),
                },
                "collateral_asset": args["collateralAsset"],
                "debt_asset": args["debtAsset"],
                "liquidation_bonus": liquidation_bonus,
                "receive_atoken": args["receiveAToken"],
                "transaction_hash": log.get("transactionHash", ""),
                "block_number": log.get("blockNumber", 0),
                "log_index": log.get("logIndex", 0),
            }
        except Exception as e:
            raise ValueError(f"Failed to decode Aave V3 liquidation log: {e}") from e

    def enrich_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a decoded Aave V3 liquidation event with protocol-specific analytics.
        """
        enriched = event.copy()

        # Add Aave V3-specific enrichments
        enriched.update(
            {
                "liquidation_type": "aave_v3",
                "protocol_version": "3",
                "is_emode_liquidation": False,  # Would need to check eMode status
                "supports_flash_liquidation": True,
                "supports_partial_liquidation": True,
                "is_cross_chain": False,  # Mainnet deployment
            }
        )

        # Calculate liquidation metrics
        debt_amount = float(event.get("debt_repaid", {}).get("amount", "0"))
        collateral_amount = float(event.get("collateral_seized", {}).get("amount", "0"))

        if debt_amount > 0 and collateral_amount > 0:
            # For proper ratio calculation, we'd need to normalize by token decimals and prices
            # This is a simplified calculation - in practice would use price oracles
            # Assuming USDC (6 decimals) vs WETH (18 decimals) example
            # Convert USDC to 18 decimals for comparison: debt_amount * 1e12
            normalized_debt = debt_amount * 1e12 if debt_amount < 1e12 else debt_amount
            enriched["liquidation_ratio"] = collateral_amount / normalized_debt
            enriched["is_profitable"] = enriched["liquidation_ratio"] > 1.0

            # Estimate liquidation incentive (typical Aave V3 range)
            liquidation_incentive = enriched["liquidation_ratio"] - 1.0
            enriched["liquidation_incentive"] = liquidation_incentive

            # Classify liquidation size based on debt amount (assume USDC scale)
            debt_usdc = debt_amount if debt_amount < 1e12 else debt_amount / 1e12
            if debt_usdc < 1000:  # Small liquidation
                enriched["liquidation_size_category"] = "small"
            elif debt_usdc < 10000:  # Medium liquidation
                enriched["liquidation_size_category"] = "medium"
            else:  # Large liquidation
                enriched["liquidation_size_category"] = "large"

        # Add Aave-specific features
        enriched["uses_isolation_mode"] = False  # Would need to check reserve config
        enriched["uses_efficiency_mode"] = False  # Would need to check user config
        enriched["supports_stable_debt"] = True
        enriched["supports_variable_debt"] = True

        # Add liquidation method information
        if event.get("receive_atoken"):
            enriched["liquidation_method"] = "receive_atoken"
            enriched["liquidator_receives"] = "aToken"
        else:
            enriched["liquidation_method"] = "receive_underlying"
            enriched["liquidator_receives"] = "underlying_asset"

        return enriched

    def is_liquidation_transaction(
        self, transaction: Dict[str, Any], logs: List[Dict[str, Any]]
    ) -> Tuple[bool, int]:
        """
        Detect if a transaction contains an Aave V3 liquidation.

        Checks for:
        1. Transaction sent to Aave V3 Pool contract
        2. LiquidationCall event logs emitted
        3. Method calls that could trigger liquidations
        """
        to_address = transaction.get("to", "").lower()

        # Check if transaction is sent to Aave V3 Pool
        aave_v3_contracts = {
            self.POOL_ADDRESS.lower(),
        }

        if to_address not in aave_v3_contracts:
            # Also check if it's sent to a flashloan aggregator or router
            # that might interact with Aave V3
            return False, -1

        # Get the liquidation event topic from the ABI
        liquidation_call_event_topic = self.w3.keccak(
            text="LiquidationCall(address,address,address,uint256,uint256,address,bool)"
        ).to_0x_hex()

        # Check for liquidation events in logs
        for idx, log in enumerate(logs):
            topics = log.get("topics", [])
            if not topics:
                continue

            event_signature = topics[0].to_0x_hex()

            # Check for LiquidationCall events
            if event_signature == liquidation_call_event_topic:
                # Verify the log is from the Aave V3 Pool contract
                log_address = log.get("address", "").lower()
                if log_address == self.POOL_ADDRESS.lower():
                    return True, idx

        # Check transaction input for liquidation method calls
        input_data = transaction.get("input", "")
        if input_data and len(input_data) >= 10:  # At least function selector (4 bytes)
            method_signature = input_data[:10]  # First 4 bytes (8 hex chars + 0x)

            # Aave V3 liquidation method signatures
            liquidation_methods = {
                "0x00a718a9",  # liquidationCall method signature
                "0x52d84d1e",  # flashLiquidation method signature (example)
            }

            if method_signature in liquidation_methods:
                # Only return True if transaction is to the Aave V3 Pool contract
                if to_address in aave_v3_contracts:
                    return True, -1

        return False, -1

    def get_liquidation_threshold(self, asset: str) -> float:
        """
        Get the liquidation threshold for a specific asset.
        This would typically query the Aave V3 protocol data provider.
        """
        # This is a placeholder - in a real implementation, this would
        # make a call to the PoolDataProvider contract
        asset_thresholds = {
            # Common Aave V3 liquidation thresholds (as percentages)
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": 0.83,  # WETH (83%)
            "0x6b175474e89094c44da98b954eedeac495271d0f": 0.77,  # DAI (77%)
            "0xa0b86a33e6441db5db86df4d9e5c4e6a05f3a9": 0.825,  # USDC (82.5%)
            "0xdac17f958d2ee523a2206206994597c13d831ec7": 0.80,  # USDT (80%)
            "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": 0.70,  # WBTC (70%)
        }
        return asset_thresholds.get(asset.lower(), 0.75)  # Default 75%

    def get_liquidation_bonus(self, asset: str) -> float:
        """
        Get the liquidation bonus for a specific asset.
        This would typically query the Aave V3 protocol data provider.
        """
        # This is a placeholder - in a real implementation, this would
        # make a call to the PoolDataProvider contract
        asset_bonuses = {
            # Common Aave V3 liquidation bonuses (as percentages)
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": 0.05,  # WETH (5%)
            "0x6b175474e89094c44da98b954eedeac495271d0f": 0.045,  # DAI (4.5%)
            "0xa0b86a33e6441db5db86df4d9e5c4e6a05f3a9": 0.045,  # USDC (4.5%)
            "0xdac17f958d2ee523a2206206994597c13d831ec7": 0.045,  # USDT (4.5%)
            "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": 0.075,  # WBTC (7.5%)
        }
        return asset_bonuses.get(asset.lower(), 0.05)  # Default 5%
