from decimal import Decimal

from mev_tools_py.dex.utils import (
    wei_to_decimal,
    decimal_to_wei,
    sort_tokens,
    normalize_address,
    is_zero_address,
    calculate_price_from_reserves,
)


def test_wei_to_decimal():
    result = wei_to_decimal(1000000000000000000, 18)
    assert result == Decimal("1")

    result = wei_to_decimal(1000000, 6)
    assert result == Decimal("1")

    result = wei_to_decimal(500000000000000000, 18)
    assert result == Decimal("0.5")


def test_decimal_to_wei():
    result = decimal_to_wei(Decimal("1"), 18)
    assert result == 1000000000000000000

    result = decimal_to_wei(Decimal("1"), 6)
    assert result == 1000000

    result = decimal_to_wei(Decimal("0.5"), 18)
    assert result == 500000000000000000


def test_sort_tokens():
    token1 = "0xB0B86a33E6441E0079C0b9fea6f4b17cb5F62D9b"
    token2 = "0xA0b86a33E6441E0079C0b9fea6f4b17cb5F62D9b"

    sorted_tokens = sort_tokens(token1, token2)
    assert sorted_tokens == (token2, token1)

    sorted_tokens = sort_tokens(token2, token1)
    assert sorted_tokens == (token2, token1)


def test_normalize_address():
    address = "0xA0B86a33E6441E0079C0b9fea6f4b17cb5F62D9b"
    normalized = normalize_address(address)
    assert normalized == "0xa0b86a33e6441e0079c0b9fea6f4b17cb5f62d9b"


def test_is_zero_address():
    assert is_zero_address("0x0000000000000000000000000000000000000000")
    assert is_zero_address("0X0000000000000000000000000000000000000000")
    assert not is_zero_address("0xA0b86a33E6441E0079C0b9fea6f4b17cb5F62D9b")


def test_calculate_price_from_reserves():
    price = calculate_price_from_reserves(
        Decimal("1000000000000000000"),  # 1 token with 18 decimals
        Decimal("2000000"),  # 2 tokens with 6 decimals
        18,
        6,
    )
    assert price == Decimal("2")

    price = calculate_price_from_reserves(Decimal("0"), Decimal("2000000"), 18, 6)
    assert price == Decimal("0")
