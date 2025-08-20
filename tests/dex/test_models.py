from decimal import Decimal

from mev_tools_py.dex.models import (
    TokenInfo,
    SwapEvent,
    LiquidityPool,
    LiquidityEvent,
    ArbitrageOpportunity,
    VolumeStatistics,
)


def test_token_info():
    token = TokenInfo(
        address="0xA0b86a33E6441E0079C0b9fea6f4b17cb5F62D9b",
        symbol="USDC",
        decimals=6,
        name="USD Coin",
    )

    assert token.address == "0xA0b86a33E6441E0079C0b9fea6f4b17cb5F62D9b"
    assert token.symbol == "USDC"
    assert token.decimals == 6
    assert token.name == "USD Coin"


def test_swap_event():
    token_in = TokenInfo("0xAddress1", "USDC", 6)
    token_out = TokenInfo("0xAddress2", "WETH", 18)

    swap = SwapEvent(
        tx_hash="0x123",
        block_number=12345,
        log_index=0,
        dex_protocol="uniswap_v2",
        pool_address="0xPoolAddress",
        trader="0xTraderAddress",
        token_in=token_in,
        token_out=token_out,
        amount_in=Decimal("1000"),
        amount_out=Decimal("0.5"),
        price_impact=Decimal("0.01"),
    )

    assert swap.tx_hash == "0x123"
    assert swap.dex_protocol == "uniswap_v2"
    assert swap.amount_in == Decimal("1000")
    assert swap.amount_out == Decimal("0.5")


def test_liquidity_pool():
    token0 = TokenInfo("0xAddress1", "USDC", 6)
    token1 = TokenInfo("0xAddress2", "WETH", 18)

    pool = LiquidityPool(
        address="0xPoolAddress",
        dex_protocol="uniswap_v2",
        token0=token0,
        token1=token1,
        reserve0=Decimal("1000000"),
        reserve1=Decimal("500"),
        total_supply=Decimal("10000"),
        fee_tier=Decimal("0.003"),
    )

    assert pool.address == "0xPoolAddress"
    assert pool.dex_protocol == "uniswap_v2"
    assert pool.reserve0 == Decimal("1000000")
    assert pool.fee_tier == Decimal("0.003")


def test_liquidity_event():
    event = LiquidityEvent(
        tx_hash="0x123",
        block_number=12345,
        log_index=1,
        dex_protocol="uniswap_v2",
        pool_address="0xPoolAddress",
        provider="0xProviderAddress",
        event_type="mint",
        token0_amount=Decimal("1000"),
        token1_amount=Decimal("0.5"),
        liquidity_delta=Decimal("100"),
    )

    assert event.tx_hash == "0x123"
    assert event.event_type == "mint"
    assert event.token0_amount == Decimal("1000")
    assert event.liquidity_delta == Decimal("100")


def test_arbitrage_opportunity():
    opportunity = ArbitrageOpportunity(
        token_pair=("USDC", "WETH"),
        dex_protocols=["uniswap_v2", "uniswap_v3"],
        price_difference=Decimal("0.02"),
        potential_profit=Decimal("100"),
        required_capital=Decimal("10000"),
    )

    assert opportunity.token_pair == ("USDC", "WETH")
    assert "uniswap_v2" in opportunity.dex_protocols
    assert opportunity.price_difference == Decimal("0.02")


def test_volume_statistics():
    stats = VolumeStatistics(
        pool_address="0xPoolAddress",
        dex_protocol="uniswap_v2",
        from_block=12000,
        to_block=12100,
        total_volume_token0=Decimal("1000000"),
        total_volume_token1=Decimal("500"),
        swap_count=50,
        unique_traders=25,
        total_volume_usd=Decimal("2000000"),
    )

    assert stats.pool_address == "0xPoolAddress"
    assert stats.from_block == 12000
    assert stats.swap_count == 50
    assert stats.total_volume_usd == Decimal("2000000")
