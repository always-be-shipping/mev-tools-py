from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from web3 import Web3
from web3.types import LogReceipt
from eth_typing import HexStr

from mev_tools_py.dex.base import BaseDexReader
from mev_tools_py.dex.models import SwapEvent, LiquidityPool, LiquidityEvent
from mev_tools_py.dex.utils import (
    wei_to_decimal,
    get_token_info,
    sort_tokens,
)


class UniswapV2Reader(BaseDexReader):
    """Uniswap V2 DEX reader implementation."""

    protocol = "uniswap_v2"

    SWAP_EVENT_SIGNATURE = (
        "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
    )
    MINT_EVENT_SIGNATURE = (
        "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f"
    )
    BURN_EVENT_SIGNATURE = (
        "0xdccd412f0b1252819cb1fd330b93224ca42612892bb3f4f789976e6d81936496"
    )

    FACTORY_ADDRESS = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"

    def __init__(self, w3: Web3, factory_address: Optional[str] = None):
        super().__init__(w3, factory_address or self.FACTORY_ADDRESS)
        self._factory_abi = [
            {
                "constant": True,
                "inputs": [
                    {"name": "tokenA", "type": "address"},
                    {"name": "tokenB", "type": "address"},
                ],
                "name": "getPair",
                "outputs": [{"name": "pair", "type": "address"}],
                "type": "function",
            }
        ]

        self._pair_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "getReserves",
                "outputs": [
                    {"name": "_reserve0", "type": "uint112"},
                    {"name": "_reserve1", "type": "uint112"},
                    {"name": "_blockTimestampLast", "type": "uint32"},
                ],
                "type": "function",
            },
            {
                "constant": True,
                "inputs": [],
                "name": "token0",
                "outputs": [{"name": "", "type": "address"}],
                "type": "function",
            },
            {
                "constant": True,
                "inputs": [],
                "name": "token1",
                "outputs": [{"name": "", "type": "address"}],
                "type": "function",
            },
            {
                "constant": True,
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function",
            },
        ]

    def decode_swap_event(self, log: LogReceipt) -> SwapEvent:
        """Decode Uniswap V2 Swap event."""
        if log["topics"][0].hex() != self.SWAP_EVENT_SIGNATURE:
            raise ValueError("Not a Swap event")

        to = "0x" + log["topics"][2].hex()[-40:]
        pool_address = log["address"]

        data = log["data"]
        amount0_in = int.from_bytes(data[0:32], "big")
        amount1_in = int.from_bytes(data[32:64], "big")
        amount0_out = int.from_bytes(data[64:96], "big")
        amount1_out = int.from_bytes(data[96:128], "big")

        pair_contract = self.w3.eth.contract(address=pool_address, abi=self._pair_abi)
        token0_address = pair_contract.functions.token0().call()
        token1_address = pair_contract.functions.token1().call()

        token0_info = get_token_info(self.w3, token0_address)
        token1_info = get_token_info(self.w3, token1_address)

        if amount0_in > 0:
            token_in = token0_info
            token_out = token1_info
            amount_in = wei_to_decimal(amount0_in, token0_info.decimals)
            amount_out = wei_to_decimal(amount1_out, token1_info.decimals)
        else:
            token_in = token1_info
            token_out = token0_info
            amount_in = wei_to_decimal(amount1_in, token1_info.decimals)
            amount_out = wei_to_decimal(amount0_out, token0_info.decimals)

        return SwapEvent(
            tx_hash=log["transactionHash"].hex(),
            block_number=log["blockNumber"],
            log_index=log["logIndex"],
            dex_protocol=self.protocol,
            pool_address=pool_address,
            trader=to,
            token_in=token_in,
            token_out=token_out,
            amount_in=amount_in,
            amount_out=amount_out,
        )

    def get_swaps_from_transaction(self, tx_hash: HexStr) -> List[SwapEvent]:
        """Extract all Uniswap V2 swap events from a transaction."""
        receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        swaps = []

        for log in receipt["logs"]:
            try:
                if log["topics"][0].hex() == self.SWAP_EVENT_SIGNATURE:
                    swap = self.decode_swap_event(log)
                    swaps.append(swap)
            except Exception:
                continue

        return swaps

    def get_swaps_from_block(self, block_number: int) -> List[SwapEvent]:
        """Extract all Uniswap V2 swap events from a block."""
        block = self.w3.eth.get_block(block_number, full_transactions=True)
        swaps = []

        if not block or "transactions" not in block:
            return swaps

        for tx in block["transactions"]:
            tx_swaps = self.get_swaps_from_transaction(tx["hash"].hex())
            swaps.extend(tx_swaps)

        return swaps

    def get_pool_info(self, pool_address: str) -> LiquidityPool:
        """Get Uniswap V2 pool information."""
        pair_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(pool_address),
            abi=self._pair_abi,
        )

        token0_address = pair_contract.functions.token0().call()
        token1_address = pair_contract.functions.token1().call()
        reserves = pair_contract.functions.getReserves().call()
        total_supply = pair_contract.functions.totalSupply().call()

        token0_info = get_token_info(self.w3, token0_address)
        token1_info = get_token_info(self.w3, token1_address)

        return LiquidityPool(
            address=pool_address,
            dex_protocol=self.protocol,
            token0=token0_info,
            token1=token1_info,
            reserve0=wei_to_decimal(reserves[0], token0_info.decimals),
            reserve1=wei_to_decimal(reserves[1], token1_info.decimals),
            total_supply=wei_to_decimal(total_supply, 18),
            fee_tier=Decimal("0.003"),
        )

    def get_pool_reserves_at_block(
        self, pool_address: str, block_number: int
    ) -> Tuple[Decimal, Decimal]:
        """Get pool reserves at a specific block."""
        pair_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(pool_address),
            abi=self._pair_abi,
        )

        token0_address = pair_contract.functions.token0().call()
        token1_address = pair_contract.functions.token1().call()

        token0_info = get_token_info(self.w3, token0_address)
        token1_info = get_token_info(self.w3, token1_address)

        reserves = pair_contract.functions.getReserves().call(
            block_identifier=block_number
        )

        return (
            wei_to_decimal(reserves[0], token0_info.decimals),
            wei_to_decimal(reserves[1], token1_info.decimals),
        )

    def find_pool_address(
        self, token0: str, token1: str, fee_tier: Optional[int] = None
    ) -> Optional[str]:
        """Find Uniswap V2 pool address for token pair."""
        # TODO: is this needed?
        factory_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.router_address),
            abi=self._factory_abi,
        )

        token0, token1 = sort_tokens(token0, token1)

        try:
            pair_address = factory_contract.functions.getPair(token0, token1).call()
            return (
                pair_address
                if not pair_address == "0x0000000000000000000000000000000000000000"
                else None
            )
        except Exception:
            return None

    def decode_liquidity_event(self, log: LogReceipt) -> LiquidityEvent:
        """Decode Uniswap V2 Mint/Burn event."""
        topic = log["topics"][0].hex()

        if topic == self.MINT_EVENT_SIGNATURE:
            event_type = "mint"
            sender = "0x" + log["topics"][1].hex()[-40:]
        elif topic == self.BURN_EVENT_SIGNATURE:
            event_type = "burn"
            sender = "0x" + log["topics"][1].hex()[-40:]
        else:
            raise ValueError("Not a liquidity event")

        pool_address = log["address"]
        data = log["data"]
        amount0 = int.from_bytes(data[0:32], "big")
        amount1 = int.from_bytes(data[32:64], "big")

        pair_contract = self.w3.eth.contract(address=pool_address, abi=self._pair_abi)
        token0_address = pair_contract.functions.token0().call()
        token1_address = pair_contract.functions.token1().call()

        token0_info = get_token_info(self.w3, token0_address)
        token1_info = get_token_info(self.w3, token1_address)

        return LiquidityEvent(
            tx_hash=log["transactionHash"].hex(),
            block_number=log["blockNumber"],
            log_index=log["logIndex"],
            dex_protocol=self.protocol,
            pool_address=pool_address,
            provider=sender,
            event_type=event_type,
            token0_amount=wei_to_decimal(amount0, token0_info.decimals),
            token1_amount=wei_to_decimal(amount1, token1_info.decimals),
            liquidity_delta=Decimal(0),
        )

    def get_liquidity_events_from_transaction(
        self, tx_hash: HexStr
    ) -> List[LiquidityEvent]:
        """Extract all liquidity events from a transaction."""
        receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        events = []

        for log in receipt["logs"]:
            try:
                topic = log["topics"][0].to_0x_hex()
                if topic in [self.MINT_EVENT_SIGNATURE, self.BURN_EVENT_SIGNATURE]:
                    event = self.decode_liquidity_event(log)
                    events.append(event)
            except Exception:
                continue

        return events

    def calculate_price_impact(self, swap: SwapEvent, pool: LiquidityPool) -> Decimal:
        """Calculate price impact using constant product formula."""
        if swap.token_in.address == pool.token0.address:
            x = pool.reserve0
            y = pool.reserve1
            dx = swap.amount_in
        else:
            x = pool.reserve1
            y = pool.reserve0
            dx = swap.amount_in

        if x == 0 or y == 0:
            return Decimal(0)

        price_before = y / x
        x_after = x + dx
        y_after = (x * y) / x_after

        if y_after == 0:
            return Decimal(0)

        price_after = (y - y_after) / dx

        if price_before == 0:
            return Decimal(0)

        return abs((price_after - price_before) / price_before)

    def get_token_price(
        self, token_address: str, block_number: Optional[int] = None
    ) -> Optional[Decimal]:
        """Get token price in ETH."""
        weth_address = "0xC02aaA39b223FE8d0A0e5C4F27eAD9083C756Cc2"

        pool_address = self.find_pool_address(token_address, weth_address)
        if not pool_address:
            return None

        try:
            if block_number:
                reserve0, reserve1 = self.get_pool_reserves_at_block(
                    pool_address, block_number
                )
                pool = self.get_pool_info(pool_address)
            else:
                pool = self.get_pool_info(pool_address)
                reserve0, reserve1 = pool.reserve0, pool.reserve1

            if pool.token0.address.lower() == token_address.lower():
                return reserve1 / reserve0 if reserve0 > 0 else Decimal(0)
            else:
                return reserve0 / reserve1 if reserve1 > 0 else Decimal(0)
        except Exception:
            return None

    def is_swap_transaction(
        self, transaction: Dict[str, Any], logs: List[Dict[str, Any]]
    ) -> Tuple[bool, int]:
        """Detect if transaction contains Uniswap V2 swaps."""
        swap_count = 0

        for log in logs:
            if len(log.get("topics", [])) > 0:
                if log["topics"][0].hex() == self.SWAP_EVENT_SIGNATURE:
                    swap_count += 1

        return swap_count > 0, swap_count

    def is_liquidity_transaction(
        self, transaction: Dict[str, Any], logs: List[Dict[str, Any]]
    ) -> Tuple[bool, int]:
        """Detect if transaction contains Uniswap V2 liquidity operations."""
        liquidity_count = 0

        for log in logs:
            if len(log.get("topics", [])) > 0:
                topic = log["topics"][0].hex()
                if topic in [self.MINT_EVENT_SIGNATURE, self.BURN_EVENT_SIGNATURE]:
                    liquidity_count += 1

        return liquidity_count > 0, liquidity_count
