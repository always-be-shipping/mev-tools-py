from dataclasses import dataclass
from typing import List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
from enum import Enum

from mev_tools_py.dex.models import SwapEvent


class SandwichType(Enum):
    """Type of sandwich attack detected."""

    FRONT_BACK = "front_back"  # Classic frontrun-victim-backrun
    MULTI_VICTIM = "multi_victim"  # Multiple victims sandwiched
    ATOMIC = "atomic"  # All transactions in same block


@dataclass
class SandwichCandidate:
    """A potential sandwich attack pattern identified in a block."""

    block_number: int
    pool_address: str
    token_pair: Tuple[str, str]
    transactions: List[SwapEvent]
    price_movements: List[Decimal]
    potential_frontrun_indices: List[int]
    potential_victim_indices: List[int]
    potential_backrun_indices: List[int]
    confidence_score: Decimal


@dataclass
class SandwichTransaction:
    """A single transaction within a sandwich attack."""

    swap_event: SwapEvent
    role: str  # "frontrun", "victim", "backrun"
    price_before: Decimal
    price_after: Decimal
    price_impact: Decimal


@dataclass
class SandwichAttack:
    """A confirmed sandwich attack with all constituent transactions."""

    attack_id: str
    sandwich_type: SandwichType
    block_number: int
    block_timestamp: datetime
    pool_address: str
    token_pair: Tuple[str, str]

    # Attack components
    frontrun_txs: List[SandwichTransaction]
    victim_txs: List[SandwichTransaction]
    backrun_txs: List[SandwichTransaction]

    # Financial metrics
    attacker_address: str
    profit_amount: Decimal
    profit_token: str
    victim_loss_amount: Decimal
    gas_cost: Decimal
    net_profit: Decimal

    # Analysis metadata
    detection_confidence: Decimal
    price_manipulation_pct: Decimal
    total_volume_manipulated: Decimal


@dataclass
class SandwichStatistics:
    """Aggregated statistics for sandwich attacks in a time period."""

    from_block: int
    to_block: int
    total_attacks: int
    total_profit: Decimal
    total_victim_loss: Decimal
    average_profit_per_attack: Decimal
    most_profitable_attack: Optional[SandwichAttack]
    top_attackers: List[Tuple[str, Decimal]]  # (address, total_profit)
    most_targeted_pools: List[Tuple[str, int]]  # (pool_address, attack_count)
