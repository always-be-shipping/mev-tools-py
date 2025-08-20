from decimal import Decimal
from datetime import datetime

from mev_tools_py.dex.models import SwapEvent, TokenInfo
from mev_tools_py.sandwich.models import (
    SandwichType,
    SandwichCandidate,
    SandwichTransaction,
    SandwichAttack,
    SandwichStatistics,
)


def create_test_swap_event(
    tx_hash: str = "0x123",
    trader: str = "0xabc",
    token_in_addr: str = "0xtoken1",
    token_out_addr: str = "0xtoken2",
    amount_in: Decimal = Decimal("100"),
    amount_out: Decimal = Decimal("95"),
    block_number: int = 18000000,
    log_index: int = 0,
) -> SwapEvent:
    """Create a test SwapEvent for testing."""
    token_in = TokenInfo(address=token_in_addr, symbol="TK1", decimals=18)
    token_out = TokenInfo(address=token_out_addr, symbol="TK2", decimals=18)

    return SwapEvent(
        tx_hash=tx_hash,
        block_number=block_number,
        log_index=log_index,
        dex_protocol="uniswap_v2",
        pool_address="0xpool123",
        trader=trader,
        token_in=token_in,
        token_out=token_out,
        amount_in=amount_in,
        amount_out=amount_out,
        price_impact=Decimal("5.0"),
        gas_used=50000,
        timestamp=datetime.now(),
    )


class TestSandwichModels:
    """Test sandwich detection data models."""

    def test_sandwich_candidate_creation(self):
        """Test SandwichCandidate model creation."""
        swaps = [create_test_swap_event()]

        candidate = SandwichCandidate(
            block_number=18000000,
            pool_address="0xpool123",
            token_pair=("0xtoken1", "0xtoken2"),
            transactions=swaps,
            price_movements=[Decimal("5.0")],
            potential_frontrun_indices=[0],
            potential_victim_indices=[1],
            potential_backrun_indices=[2],
            confidence_score=Decimal("0.85"),
        )

        assert candidate.block_number == 18000000
        assert candidate.pool_address == "0xpool123"
        assert len(candidate.transactions) == 1
        assert candidate.confidence_score == Decimal("0.85")

    def test_sandwich_transaction_creation(self):
        """Test SandwichTransaction model creation."""
        swap = create_test_swap_event()

        sandwich_tx = SandwichTransaction(
            swap_event=swap,
            role="frontrun",
            price_before=Decimal("1.0"),
            price_after=Decimal("1.05"),
            price_impact=Decimal("5.0"),
        )

        assert sandwich_tx.role == "frontrun"
        assert sandwich_tx.price_before == Decimal("1.0")
        assert sandwich_tx.price_after == Decimal("1.05")
        assert sandwich_tx.swap_event.tx_hash == "0x123"

    def test_sandwich_attack_creation(self):
        """Test SandwichAttack model creation."""
        frontrun_swap = create_test_swap_event(tx_hash="0x1", trader="0xattacker")
        victim_swap = create_test_swap_event(tx_hash="0x2", trader="0xvictim")
        backrun_swap = create_test_swap_event(tx_hash="0x3", trader="0xattacker")

        frontrun_tx = SandwichTransaction(
            swap_event=frontrun_swap,
            role="frontrun",
            price_before=Decimal("1.0"),
            price_after=Decimal("1.05"),
            price_impact=Decimal("5.0"),
        )

        victim_tx = SandwichTransaction(
            swap_event=victim_swap,
            role="victim",
            price_before=Decimal("1.05"),
            price_after=Decimal("1.08"),
            price_impact=Decimal("3.0"),
        )

        backrun_tx = SandwichTransaction(
            swap_event=backrun_swap,
            role="backrun",
            price_before=Decimal("1.08"),
            price_after=Decimal("1.02"),
            price_impact=Decimal("6.0"),
        )

        attack = SandwichAttack(
            attack_id="test-123",
            sandwich_type=SandwichType.FRONT_BACK,
            block_number=18000000,
            block_timestamp=datetime.now(),
            pool_address="0xpool123",
            token_pair=("0xtoken1", "0xtoken2"),
            frontrun_txs=[frontrun_tx],
            victim_txs=[victim_tx],
            backrun_txs=[backrun_tx],
            attacker_address="0xattacker",
            profit_amount=Decimal("0.5"),
            profit_token="0xtoken2",
            victim_loss_amount=Decimal("0.3"),
            gas_cost=Decimal("0.01"),
            net_profit=Decimal("0.49"),
            detection_confidence=Decimal("0.9"),
            price_manipulation_pct=Decimal("8.0"),
            total_volume_manipulated=Decimal("200"),
        )

        assert attack.attack_id == "test-123"
        assert attack.sandwich_type == SandwichType.FRONT_BACK
        assert attack.attacker_address == "0xattacker"
        assert attack.profit_amount == Decimal("0.5")
        assert len(attack.frontrun_txs) == 1
        assert len(attack.victim_txs) == 1
        assert len(attack.backrun_txs) == 1

    def test_sandwich_statistics_creation(self):
        """Test SandwichStatistics model creation."""
        attack = SandwichAttack(
            attack_id="test-123",
            sandwich_type=SandwichType.FRONT_BACK,
            block_number=18000000,
            block_timestamp=datetime.now(),
            pool_address="0xpool123",
            token_pair=("0xtoken1", "0xtoken2"),
            frontrun_txs=[],
            victim_txs=[],
            backrun_txs=[],
            attacker_address="0xattacker",
            profit_amount=Decimal("0.5"),
            profit_token="0xtoken2",
            victim_loss_amount=Decimal("0.3"),
            gas_cost=Decimal("0.01"),
            net_profit=Decimal("0.49"),
            detection_confidence=Decimal("0.9"),
            price_manipulation_pct=Decimal("8.0"),
            total_volume_manipulated=Decimal("200"),
        )

        stats = SandwichStatistics(
            from_block=18000000,
            to_block=18000100,
            total_attacks=5,
            total_profit=Decimal("2.5"),
            total_victim_loss=Decimal("1.5"),
            average_profit_per_attack=Decimal("0.5"),
            most_profitable_attack=attack,
            top_attackers=[("0xattacker", Decimal("1.0"))],
            most_targeted_pools=[("0xpool123", 3)],
        )

        assert stats.total_attacks == 5
        assert stats.total_profit == Decimal("2.5")
        assert stats.most_profitable_attack == attack
        assert len(stats.top_attackers) == 1
        assert len(stats.most_targeted_pools) == 1

    def test_sandwich_type_enum(self):
        """Test SandwichType enum values."""
        assert SandwichType.FRONT_BACK.value == "front_back"
        assert SandwichType.MULTI_VICTIM.value == "multi_victim"
        assert SandwichType.ATOMIC.value == "atomic"
