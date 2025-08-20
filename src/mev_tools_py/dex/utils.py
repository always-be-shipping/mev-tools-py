from typing import Dict, Any, List
from decimal import Decimal
from eth_typing import Address
from web3 import Web3
from web3.types import LogReceipt

from mev_tools_py.dex.models import TokenInfo


def parse_log_data(log: LogReceipt, abi: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Parse log data using ABI."""
    w3 = Web3()
    contract = w3.eth.contract(abi=abi)

    for event_abi in abi:
        if event_abi.get("type") == "event":
            try:
                decoded = contract.events[event_abi["name"]]().process_log(log)
                return decoded["args"]
            except Exception:
                continue

    raise ValueError(f"Could not decode log: {log}")


def wei_to_decimal(wei_amount: int, decimals: int) -> Decimal:
    """Convert wei amount to decimal with proper scaling."""
    return Decimal(wei_amount) / (Decimal(10) ** decimals)


def decimal_to_wei(decimal_amount: Decimal, decimals: int) -> int:
    """Convert decimal amount to wei with proper scaling."""
    return int(decimal_amount * (Decimal(10) ** decimals))


def get_token_info(w3: Web3, token_address: Address) -> TokenInfo:
    """Get token information from contract."""
    erc20_abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function",
        },
    ]

    contract = w3.eth.contract(address=token_address, abi=erc20_abi)

    try:
        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()

        return TokenInfo(
            address=token_address.hex(),
            symbol=symbol,
            decimals=decimals,
            name=name,
        )
    except Exception:
        return TokenInfo(
            address=token_address.hex(),
            symbol="UNKNOWN",
            decimals=18,
            name=None,
        )


def calculate_sqrt_price(reserve0: Decimal, reserve1: Decimal) -> int:
    """Calculate sqrt price for Uniswap V3 style pricing."""
    if reserve1 == 0:
        return 0

    price = reserve1 / reserve0
    sqrt_price = price.sqrt()

    return int(sqrt_price * (Decimal(2) ** 96))


def normalize_address(address: str) -> str:
    """Normalize Ethereum address to lowercase."""
    return address.lower()


def is_zero_address(address: str) -> bool:
    """Check if address is zero address."""
    return address.lower() == "0x0000000000000000000000000000000000000000"


def sort_tokens(token0: str, token1: str) -> tuple[str, str]:
    """Sort token addresses in ascending order (Uniswap convention)."""
    if token0.lower() < token1.lower():
        return token0, token1
    return token1, token0


def calculate_price_from_reserves(
    reserve0: Decimal, reserve1: Decimal, decimals0: int, decimals1: int
) -> Decimal:
    """Calculate price of token0 in terms of token1."""
    if reserve0 == 0:
        return Decimal(0)

    normalized_reserve0 = reserve0 / (Decimal(10) ** decimals0)
    normalized_reserve1 = reserve1 / (Decimal(10) ** decimals1)

    return normalized_reserve1 / normalized_reserve0
