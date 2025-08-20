from dataclasses import dataclass
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


@dataclass
class TokenInfo:
    address: str
    symbol: str
    decimals: int
    name: Optional[str] = None


@dataclass
class SwapEvent:
    tx_hash: str
    block_number: int
    log_index: int
    dex_protocol: str
    pool_address: str
    trader: str
    token_in: TokenInfo
    token_out: TokenInfo
    amount_in: Decimal
    amount_out: Decimal
    price_impact: Optional[Decimal] = None
    gas_used: Optional[int] = None
    timestamp: Optional[datetime] = None


@dataclass
class LiquidityPool:
    address: str
    dex_protocol: str
    token0: TokenInfo
    token1: TokenInfo
    reserve0: Decimal
    reserve1: Decimal
    total_supply: Decimal
    fee_tier: Optional[Decimal] = None
    tick: Optional[int] = None
    sqrt_price_x96: Optional[int] = None


@dataclass
class LiquidityEvent:
    tx_hash: str
    block_number: int
    log_index: int
    dex_protocol: str
    pool_address: str
    provider: str
    event_type: str
    token0_amount: Decimal
    token1_amount: Decimal
    liquidity_delta: Decimal
    timestamp: Optional[datetime] = None


@dataclass
class ArbitrageOpportunity:
    token_pair: tuple[str, str]
    dex_protocols: List[str]
    price_difference: Decimal
    potential_profit: Decimal
    required_capital: Decimal
    gas_cost_estimate: Optional[int] = None


@dataclass
class VolumeStatistics:
    pool_address: str
    dex_protocol: str
    from_block: int
    to_block: int
    total_volume_token0: Decimal
    total_volume_token1: Decimal
    swap_count: int
    unique_traders: int
    total_volume_usd: Optional[Decimal] = None
    average_swap_size_usd: Optional[Decimal] = None
