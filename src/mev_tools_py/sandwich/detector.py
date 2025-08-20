from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from collections import defaultdict
import uuid

from mev_tools_py.dex.models import SwapEvent
from mev_tools_py.sandwich.models import (
    SandwichTransaction,
    SandwichAttack,
    SandwichType,
)
from mev_tools_py.sandwich.utils import (
    group_swaps_by_pool,
    sort_swaps_by_block_position,
    is_same_direction_trade,
    is_opposite_direction_trade,
    identify_token_pair,
    calculate_sandwich_profit,
)


class SandwichDetector:
    """Core sandwich attack detection engine."""

    def __init__(
        self,
        min_price_impact: Decimal = Decimal("1.0"),  # 1%
        min_profit_threshold: Decimal = Decimal("0.01"),  # 0.01 ETH equivalent
        max_block_distance: int = 1,  # Look within same block by default
        confidence_threshold: Decimal = Decimal("0.7"),  # 70% confidence
    ):
        self.min_price_impact = min_price_impact
        self.min_profit_threshold = min_profit_threshold
        self.max_block_distance = max_block_distance
        self.confidence_threshold = confidence_threshold

    def detect_sandwich_attacks_in_block(
        self, block_number: int, swaps: List[SwapEvent]
    ) -> List[SandwichAttack]:
        """Detect all sandwich attacks within a single block."""
        if len(swaps) < 3:  # Need at least 3 swaps for a sandwich
            return []

        # Sort swaps by log index to get transaction order
        sorted_swaps = sort_swaps_by_block_position(swaps)

        # Group by pool for analysis
        pool_groups = group_swaps_by_pool(sorted_swaps)

        attacks = []
        for pool_address, pool_swaps in pool_groups.items():
            if len(pool_swaps) < 3:
                continue

            # Look for sandwich patterns in this pool
            pool_attacks = self._detect_sandwiches_in_pool(pool_address, pool_swaps)
            attacks.extend(pool_attacks)

        return attacks

    def detect_sandwich_attacks_in_range(
        self, from_block: int, to_block: int, swaps: List[SwapEvent]
    ) -> List[SandwichAttack]:
        """Detect sandwich attacks across a range of blocks."""
        attacks = []

        # Group swaps by block
        blocks = defaultdict(list)
        for swap in swaps:
            if from_block <= swap.block_number <= to_block:
                blocks[swap.block_number].append(swap)

        # Analyze each block
        for block_number in sorted(blocks.keys()):
            block_swaps = blocks[block_number]
            block_attacks = self.detect_sandwich_attacks_in_block(
                block_number, block_swaps
            )
            attacks.extend(block_attacks)

        return attacks

    def _detect_sandwiches_in_pool(
        self, pool_address: str, swaps: List[SwapEvent]
    ) -> List[SandwichAttack]:
        """Detect sandwich patterns within a specific pool."""
        if len(swaps) < 3:
            return []

        attacks = []

        # Look for sandwich patterns: A -> B -> A (where A is attacker, B is victim)
        for i in range(len(swaps) - 2):
            for j in range(i + 2, len(swaps)):
                # Check if swaps[i] and swaps[j] could be frontrun/backrun by same attacker
                frontrun = swaps[i]
                backrun = swaps[j]

                if not self._could_be_sandwich_pair(frontrun, backrun):
                    continue

                # Find victims between frontrun and backrun
                victims = []
                for k in range(i + 1, j):
                    victim_swap = swaps[k]
                    if self._is_potential_victim(frontrun, victim_swap, backrun):
                        victims.append(victim_swap)

                if victims:
                    # Create sandwich attack object
                    attack = self._create_sandwich_attack(
                        pool_address, frontrun, victims, backrun
                    )
                    if (
                        attack
                        and attack.detection_confidence >= self.confidence_threshold
                    ):
                        attacks.append(attack)

        return attacks

    def _could_be_sandwich_pair(self, frontrun: SwapEvent, backrun: SwapEvent) -> bool:
        """Check if two swaps could be a frontrun/backrun pair."""
        # Same trader
        if frontrun.trader.lower() != backrun.trader.lower():
            return False

        # Opposite directions (buy then sell, or sell then buy)
        if not is_opposite_direction_trade(frontrun, backrun):
            return False

        # Same token pair
        if identify_token_pair(frontrun) != identify_token_pair(backrun):
            return False

        # Within block distance threshold
        if abs(backrun.block_number - frontrun.block_number) > self.max_block_distance:
            return False

        return True

    def _is_potential_victim(
        self, frontrun: SwapEvent, candidate: SwapEvent, backrun: SwapEvent
    ) -> bool:
        """Check if a swap could be a victim between frontrun and backrun."""
        # Different trader than attacker
        if candidate.trader.lower() == frontrun.trader.lower():
            return False

        # Same token pair
        if identify_token_pair(candidate) != identify_token_pair(frontrun):
            return False

        # Same direction as either frontrun or backrun (victim gets sandwiched)
        return is_same_direction_trade(candidate, frontrun) or is_same_direction_trade(
            candidate, backrun
        )

    def _create_sandwich_attack(
        self,
        pool_address: str,
        frontrun: SwapEvent,
        victims: List[SwapEvent],
        backrun: SwapEvent,
    ) -> Optional[SandwichAttack]:
        """Create a SandwichAttack object from detected components."""
        try:
            # Calculate basic metrics
            profit = calculate_sandwich_profit(frontrun, backrun)

            if profit < self.min_profit_threshold:
                return None

            # Create sandwich transactions
            frontrun_tx = SandwichTransaction(
                swap_event=frontrun,
                role="frontrun",
                price_before=Decimal("0"),  # Would need pool state to calculate
                price_after=Decimal("0"),
                price_impact=frontrun.price_impact or Decimal("0"),
            )

            victim_txs = [
                SandwichTransaction(
                    swap_event=victim,
                    role="victim",
                    price_before=Decimal("0"),
                    price_after=Decimal("0"),
                    price_impact=victim.price_impact or Decimal("0"),
                )
                for victim in victims
            ]

            backrun_tx = SandwichTransaction(
                swap_event=backrun,
                role="backrun",
                price_before=Decimal("0"),
                price_after=Decimal("0"),
                price_impact=backrun.price_impact or Decimal("0"),
            )

            # Calculate confidence score
            confidence = self._calculate_confidence_score(frontrun, victims, backrun)

            # Determine sandwich type
            sandwich_type = (
                SandwichType.ATOMIC
                if frontrun.block_number == backrun.block_number
                else SandwichType.FRONT_BACK
            )
            if len(victims) > 1:
                sandwich_type = SandwichType.MULTI_VICTIM

            # Calculate victim losses (simplified)
            total_victim_loss = sum(
                victim.price_impact or Decimal("0") for victim in victims
            )

            attack = SandwichAttack(
                attack_id=str(uuid.uuid4()),
                sandwich_type=sandwich_type,
                block_number=frontrun.block_number,
                block_timestamp=frontrun.timestamp or datetime.now(),
                pool_address=pool_address,
                token_pair=identify_token_pair(frontrun),
                frontrun_txs=[frontrun_tx],
                victim_txs=victim_txs,
                backrun_txs=[backrun_tx],
                attacker_address=frontrun.trader,
                profit_amount=profit,
                profit_token=frontrun.token_out.address,
                victim_loss_amount=total_victim_loss,
                gas_cost=Decimal(str(frontrun.gas_used or 0 + backrun.gas_used or 0)),
                net_profit=profit
                - Decimal(str(frontrun.gas_used or 0 + backrun.gas_used or 0)),
                detection_confidence=confidence,
                price_manipulation_pct=self._calculate_price_manipulation(
                    frontrun, victims, backrun
                ),
                total_volume_manipulated=frontrun.amount_in + backrun.amount_in,
            )

            return attack

        except Exception:
            # Log error in production
            return None

    def _calculate_confidence_score(
        self, frontrun: SwapEvent, victims: List[SwapEvent], backrun: SwapEvent
    ) -> Decimal:
        """Calculate confidence score for sandwich detection."""
        score = Decimal("0")

        # Base score for pattern match
        score += Decimal("0.5")

        # Higher score if multiple victims
        if len(victims) > 1:
            score += Decimal("0.1")

        # Higher score if significant price impact
        total_impact = (frontrun.price_impact or Decimal("0")) + (
            backrun.price_impact or Decimal("0")
        )
        if total_impact > self.min_price_impact:
            score += Decimal("0.2")

        # Higher score if profit is substantial
        profit = calculate_sandwich_profit(frontrun, backrun)
        if profit > self.min_profit_threshold * 10:
            score += Decimal("0.1")

        # Higher score if same block (atomic)
        if frontrun.block_number == backrun.block_number:
            score += Decimal("0.1")

        return min(score, Decimal("1.0"))

    def _calculate_price_manipulation(
        self, frontrun: SwapEvent, victims: List[SwapEvent], backrun: SwapEvent
    ) -> Decimal:
        """Calculate the percentage of price manipulation caused by the sandwich."""
        # This would require detailed pool state tracking
        # For now, return a simplified estimate based on price impacts
        total_impact = (frontrun.price_impact or Decimal("0")) + (
            backrun.price_impact or Decimal("0")
        )
        return total_impact
