from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from eth_typing import HexStr
from web3 import Web3
from web3.types import LogReceipt

from mev_tools_py.dex.models import SwapEvent, LiquidityPool, LiquidityEvent


class BaseDexReader(ABC):
    """Abstract base class for DEX data readers."""

    protocol: str

    def __init__(self, w3: Web3, router_address: Optional[str] = None):
        self.w3 = w3
        self.router_address = router_address

    @abstractmethod
    def decode_swap_event(self, log: LogReceipt) -> SwapEvent:
        """Decode a raw log into a structured swap event."""
        raise NotImplementedError

    @abstractmethod
    def get_swaps_from_transaction(self, tx_hash: HexStr) -> List[SwapEvent]:
        """Extract all swap events from a transaction."""
        raise NotImplementedError

    @abstractmethod
    def get_swaps_from_block(self, block_number: int) -> List[SwapEvent]:
        """Extract all swap events from a block."""
        raise NotImplementedError

    @abstractmethod
    def get_pool_info(self, pool_address: str) -> LiquidityPool:
        """Get current pool information including reserves."""
        raise NotImplementedError

    @abstractmethod
    def get_pool_reserves_at_block(
        self, pool_address: str, block_number: int
    ) -> Tuple[Decimal, Decimal]:
        """Get pool reserves at a specific block."""
        raise NotImplementedError

    @abstractmethod
    def find_pool_address(
        self, token0: str, token1: str, fee_tier: Optional[int] = None
    ) -> Optional[str]:
        """Find pool address for a token pair."""
        raise NotImplementedError

    @abstractmethod
    def decode_liquidity_event(self, log: LogReceipt) -> LiquidityEvent:
        """Decode a raw log into a structured liquidity event."""
        raise NotImplementedError

    @abstractmethod
    def get_liquidity_events_from_transaction(
        self, tx_hash: HexStr
    ) -> List[LiquidityEvent]:
        """Extract all liquidity events from a transaction."""
        raise NotImplementedError

    @abstractmethod
    def calculate_price_impact(self, swap: SwapEvent, pool: LiquidityPool) -> Decimal:
        """Calculate price impact of a swap."""
        raise NotImplementedError

    @abstractmethod
    def get_token_price(
        self, token_address: str, block_number: Optional[int] = None
    ) -> Optional[Decimal]:
        """Get token price in ETH or USD."""
        raise NotImplementedError

    @abstractmethod
    def is_swap_transaction(
        self, transaction: Dict[str, Any], logs: List[Dict[str, Any]]
    ) -> Tuple[bool, int]:
        """Detect if a transaction contains swaps from this DEX."""
        raise NotImplementedError

    @abstractmethod
    def is_liquidity_transaction(
        self, transaction: Dict[str, Any], logs: List[Dict[str, Any]]
    ) -> Tuple[bool, int]:
        """Detect if a transaction contains liquidity operations from this DEX."""
        raise NotImplementedError
