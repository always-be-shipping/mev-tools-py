from typing import List, Dict, Tuple, Set
from decimal import Decimal
from collections import defaultdict

from mev_tools_py.dex.models import SwapEvent


def calculate_price_impact(
    swap: SwapEvent, pool_reserves_before: Tuple[Decimal, Decimal]
) -> Decimal:
    """Calculate the price impact of a swap based on pool reserves before the swap."""
    if swap.amount_in == 0 or swap.amount_out == 0:
        return Decimal("0")

    reserve_in, reserve_out = pool_reserves_before

    # Calculate price before swap
    price_before = reserve_out / reserve_in if reserve_in > 0 else Decimal("0")

    # Calculate price after swap (considering the swap moved the reserves)
    new_reserve_in = reserve_in + swap.amount_in
    new_reserve_out = reserve_out - swap.amount_out
    price_after = (
        new_reserve_out / new_reserve_in if new_reserve_in > 0 else Decimal("0")
    )

    # Price impact as percentage change
    if price_before > 0:
        return abs((price_after - price_before) / price_before) * Decimal("100")
    return Decimal("0")


def identify_token_pair(swap: SwapEvent) -> Tuple[str, str]:
    """Extract and normalize token pair from a swap event."""
    token_in = swap.token_in.address.lower()
    token_out = swap.token_out.address.lower()

    # Always return in sorted order for consistency
    return (token_in, token_out) if token_in < token_out else (token_out, token_in)


def group_swaps_by_pool(swaps: List[SwapEvent]) -> Dict[str, List[SwapEvent]]:
    """Group swaps by pool address for analysis."""
    pool_groups = defaultdict(list)

    for swap in swaps:
        pool_groups[swap.pool_address.lower()].append(swap)

    return dict(pool_groups)


def group_swaps_by_token_pair(
    swaps: List[SwapEvent],
) -> Dict[Tuple[str, str], List[SwapEvent]]:
    """Group swaps by token pair for analysis."""
    pair_groups = defaultdict(list)

    for swap in swaps:
        token_pair = identify_token_pair(swap)
        pair_groups[token_pair].append(swap)

    return dict(pair_groups)


def sort_swaps_by_block_position(swaps: List[SwapEvent]) -> List[SwapEvent]:
    """Sort swaps by their position within blocks (block_number, log_index)."""
    return sorted(swaps, key=lambda s: (s.block_number, s.log_index))


def detect_potential_mev_addresses(
    swaps: List[SwapEvent], min_frequency: int = 3
) -> Set[str]:
    """Identify addresses that appear frequently in swaps (potential MEV bots)."""
    trader_counts = defaultdict(int)

    for swap in swaps:
        trader_counts[swap.trader.lower()] += 1

    return {
        address for address, count in trader_counts.items() if count >= min_frequency
    }


def calculate_price_movement(swaps: List[SwapEvent]) -> List[Decimal]:
    """Calculate price movements across a sequence of swaps in the same pool."""
    if len(swaps) < 2:
        return []

    prices = []
    for i, swap in enumerate(swaps):
        if swap.amount_in > 0:
            # Price as amount_out / amount_in
            price = swap.amount_out / swap.amount_in
            prices.append(price)

    # Calculate percentage changes
    price_movements = []
    for i in range(1, len(prices)):
        if prices[i - 1] > 0:
            movement = ((prices[i] - prices[i - 1]) / prices[i - 1]) * Decimal("100")
            price_movements.append(movement)

    return price_movements


def is_same_direction_trade(swap1: SwapEvent, swap2: SwapEvent) -> bool:
    """Check if two swaps are trading in the same direction (same input/output tokens)."""
    return (
        swap1.token_in.address.lower() == swap2.token_in.address.lower()
        and swap1.token_out.address.lower() == swap2.token_out.address.lower()
    )


def is_opposite_direction_trade(swap1: SwapEvent, swap2: SwapEvent) -> bool:
    """Check if two swaps are trading in opposite directions."""
    return (
        swap1.token_in.address.lower() == swap2.token_out.address.lower()
        and swap1.token_out.address.lower() == swap2.token_in.address.lower()
    )


def calculate_sandwich_profit(frontrun: SwapEvent, backrun: SwapEvent) -> Decimal:
    """Calculate profit from a sandwich attack (simplified)."""
    if not is_opposite_direction_trade(frontrun, backrun):
        return Decimal("0")

    # Profit = tokens received in backrun - tokens spent in frontrun
    # This is a simplified calculation - real profit calculation would need to account for gas costs
    if frontrun.token_out.address.lower() == backrun.token_in.address.lower():
        # If we got token X in frontrun and spent token X in backrun
        profit_in_intermediate_token = frontrun.amount_out - backrun.amount_in
        return profit_in_intermediate_token

    return Decimal("0")
