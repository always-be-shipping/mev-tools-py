#!/usr/bin/env python3
"""
Demo script showing sandwich attack detection capabilities.

This script demonstrates how to use the sandwich detection module
to identify potential MEV attacks in DEX transactions.
"""

from decimal import Decimal
from datetime import datetime

# Import our sandwich detection modules
from mev_tools_py.dex.models import SwapEvent, TokenInfo
from mev_tools_py.sandwich.detector import SandwichDetector
from mev_tools_py.sandwich.analyzer import SandwichAnalyzer


def create_demo_swap(
    tx_hash: str,
    trader: str,
    token_in_addr: str,
    token_out_addr: str,
    amount_in: str,
    amount_out: str,
    block_number: int = 18000000,
    log_index: int = 0,
) -> SwapEvent:
    """Create a demo swap event for testing."""
    token_in = TokenInfo(address=token_in_addr, symbol="WETH", decimals=18)
    token_out = TokenInfo(address=token_out_addr, symbol="USDC", decimals=6)

    return SwapEvent(
        tx_hash=tx_hash,
        block_number=block_number,
        log_index=log_index,
        dex_protocol="uniswap_v2",
        pool_address="0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",  # WETH/USDC
        trader=trader,
        token_in=token_in,
        token_out=token_out,
        amount_in=Decimal(amount_in),
        amount_out=Decimal(amount_out),
        price_impact=Decimal("2.5"),
        gas_used=150000,
        timestamp=datetime.now(),
    )


def demo_sandwich_detection():
    """Demonstrate sandwich attack detection."""
    print("🥪 Sandwich Attack Detection Demo")
    print("=" * 50)

    # Create a realistic sandwich scenario
    print("\n1. Creating simulated transaction data...")

    # Frontrun: Attacker buys before victim
    frontrun = create_demo_swap(
        tx_hash="0xfrontrun123",
        trader="0xAttacker123456789",
        token_in_addr="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
        token_out_addr="0xA0b86a33E6441db5dB86DF4D9E5C4e6a05F3a5db",  # USDC
        amount_in="10.0",
        amount_out="30000.0",
        log_index=0,
    )

    # Victim: Regular user's transaction gets sandwiched
    victim = create_demo_swap(
        tx_hash="0xvictim456",
        trader="0xVictim789012345",
        token_in_addr="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
        token_out_addr="0xA0b86a33E6441db5dB86DF4D9E5C4e6a05F3a5db",  # USDC
        amount_in="5.0",
        amount_out="14500.0",  # Worse rate due to frontrun
        log_index=1,
    )

    # Backrun: Attacker sells for profit
    backrun = create_demo_swap(
        tx_hash="0xbackrun789",
        trader="0xAttacker123456789",  # Same attacker
        token_in_addr="0xA0b86a33E6441db5dB86DF4D9E5C4e6a05F3a5db",  # USDC
        token_out_addr="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
        amount_in="30200.0",
        amount_out="10.2",  # Profit of 0.2 WETH
        log_index=2,
    )

    swaps = [frontrun, victim, backrun]

    print(f"   - Frontrun: {frontrun.trader[:10]}... buys {frontrun.amount_in} WETH")
    print(
        f"   - Victim:   {victim.trader[:10]}... buys {victim.amount_in} WETH (worse rate)"
    )
    print(
        f"   - Backrun:  {backrun.trader[:10]}... sells for {backrun.amount_out} WETH"
    )

    # Initialize detector
    print("\n2. Initializing sandwich detector...")
    detector = SandwichDetector(
        min_price_impact=Decimal("1.0"),
        min_profit_threshold=Decimal("0.1"),
        confidence_threshold=Decimal("0.7"),
    )

    # Detect sandwich attacks
    print("\n3. Analyzing transactions for sandwich patterns...")
    attacks = detector.detect_sandwich_attacks_in_block(18000000, swaps)

    print(f"   Found {len(attacks)} potential sandwich attacks")

    # Analyze results
    if attacks:
        attack = attacks[0]
        print("\n4. Sandwich Attack Details:")
        print(f"   - Attack ID: {attack.attack_id}")
        print(f"   - Type: {attack.sandwich_type.value}")
        print(f"   - Attacker: {attack.attacker_address}")
        print(f"   - Profit: {attack.profit_amount} {attack.profit_token[:10]}...")
        print(f"   - Victim Loss: {attack.victim_loss_amount}")
        print(f"   - Confidence: {attack.detection_confidence:.1%}")
        print(f"   - Price Manipulation: {attack.price_manipulation_pct}%")

        # Use analyzer for additional insights
        print("\n5. Advanced Analysis:")
        analyzer = SandwichAnalyzer()

        efficiency = analyzer.calculate_attack_efficiency(attack)
        print(f"   - Profit per gas: {efficiency['profit_per_gas']:.6f}")
        print(f"   - Profit per victim: {efficiency['profit_per_victim']:.6f}")

        # Generate statistics
        stats = analyzer.analyze_attacks([attack])
        print("\n6. Statistics:")
        print(f"   - Total attacks: {stats.total_attacks}")
        print(f"   - Total profit: {stats.total_profit}")
        print(f"   - Average profit: {stats.average_profit_per_attack}")

    else:
        print("   No sandwich attacks detected with current parameters")

    print("\n✅ Demo completed!")


if __name__ == "__main__":
    demo_sandwich_detection()
