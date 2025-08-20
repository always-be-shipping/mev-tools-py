from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from web3 import Web3
from web3.types import LogReceipt

from ..base import BaseDexReader
from ..models import SwapEvent, LiquidityPool, LiquidityEvent
from ..utils import wei_to_decimal, get_token_info, sort_tokens


class UniswapV3Reader(BaseDexReader):
    """Uniswap V3 DEX reader implementation."""

    protocol = "uniswap_v3"

    SWAP_EVENT_SIGNATURE = (
        "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
    )
    MINT_EVENT_SIGNATURE = (
        "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
    )
    BURN_EVENT_SIGNATURE = (
        "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c"
    )

    FACTORY_ADDRESS = "0x1F98431c8aD98523631AE4a59f267346ea31F984"

    def __init__(self, w3: Web3, factory_address: Optional[str] = None):
        super().__init__(w3, factory_address or self.FACTORY_ADDRESS)
        self._factory_abi = [
            {
                "inputs": [
                    {"name": "tokenA", "type": "address"},
                    {"name": "tokenB", "type": "address"},
                    {"name": "fee", "type": "uint24"},
                ],
                "name": "getPool",
                "outputs": [{"name": "pool", "type": "address"}],
                "stateMutability": "view",
                "type": "function",
            }
        ]

        self._pool_abi = [
            {
                "inputs": [],
                "name": "slot0",
                "outputs": [
                    {"name": "sqrtPriceX96", "type": "uint160"},
                    {"name": "tick", "type": "int24"},
                    {"name": "observationIndex", "type": "uint16"},
                    {"name": "observationCardinality", "type": "uint16"},
                    {"name": "observationCardinalityNext", "type": "uint16"},
                    {"name": "feeProtocol", "type": "uint8"},
                    {"name": "unlocked", "type": "bool"},
                ],
                "stateMutability": "view",
                "type": "function",
            },
            {
                "inputs": [],
                "name": "token0",
                "outputs": [{"name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function",
            },
            {
                "inputs": [],
                "name": "token1",
                "outputs": [{"name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function",
            },
            {
                "inputs": [],
                "name": "fee",
                "outputs": [{"name": "", "type": "uint24"}],
                "stateMutability": "view",
                "type": "function",
            },
            {
                "inputs": [],
                "name": "liquidity",
                "outputs": [{"name": "", "type": "uint128"}],
                "stateMutability": "view",
                "type": "function",
            },
        ]

    def decode_swap_event(self, log: LogReceipt) -> SwapEvent:
        """Decode Uniswap V3 Swap event."""
        if log["topics"][0].hex() != self.SWAP_EVENT_SIGNATURE:
            raise ValueError("Not a Swap event")

        sender = "0x" + log["topics"][1].hex()[-40:]  # noqa
        recipient = "0x" + log["topics"][2].hex()[-40:]
        pool_address = log["address"]

        data = log["data"]
        amount0 = int.from_bytes(data[0:32], "big", signed=True)
        amount1 = int.from_bytes(data[32:64], "big", signed=True)
        sqrt_price_x96 = int.from_bytes(data[64:96], "big")  # noqa
        liquidity = int.from_bytes(data[96:128], "big")  # noqa
        tick = int.from_bytes(data[128:160], "big", signed=True)  # noqa

        pool_contract = self.w3.eth.contract(address=pool_address, abi=self._pool_abi)
        token0_address = pool_contract.functions.token0().call()
        token1_address = pool_contract.functions.token1().call()

        token0_info = get_token_info(self.w3, token0_address)
        token1_info = get_token_info(self.w3, token1_address)

        if amount0 > 0:
            token_in = token0_info
            token_out = token1_info
            amount_in = wei_to_decimal(amount0, token0_info.decimals)
            amount_out = wei_to_decimal(abs(amount1), token1_info.decimals)
        else:
            token_in = token1_info
            token_out = token0_info
            amount_in = wei_to_decimal(amount1, token1_info.decimals)
            amount_out = wei_to_decimal(abs(amount0), token0_info.decimals)

        return SwapEvent(
            tx_hash=log["transactionHash"].hex(),
            block_number=log["blockNumber"],
            log_index=log["logIndex"],
            dex_protocol=self.protocol,
            pool_address=pool_address,
            trader=recipient,
            token_in=token_in,
            token_out=token_out,
            amount_in=amount_in,
            amount_out=amount_out,
        )

    def get_swaps_from_transaction(self, tx_hash: str) -> List[SwapEvent]:
        """Extract all Uniswap V3 swap events from a transaction."""
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
        """Extract all Uniswap V3 swap events from a block."""
        block = self.w3.eth.get_block(block_number, full_transactions=True)
        swaps = []

        for tx in block["transactions"]:
            tx_swaps = self.get_swaps_from_transaction(tx["hash"].hex())
            swaps.extend(tx_swaps)

        return swaps

    def get_pool_info(self, pool_address: str) -> LiquidityPool:
        """Get Uniswap V3 pool information."""
        pool_contract = self.w3.eth.contract(address=pool_address, abi=self._pool_abi)

        token0_address = pool_contract.functions.token0().call()
        token1_address = pool_contract.functions.token1().call()
        fee = pool_contract.functions.fee().call()
        liquidity = pool_contract.functions.liquidity().call()
        slot0 = pool_contract.functions.slot0().call()

        token0_info = get_token_info(self.w3, token0_address)
        token1_info = get_token_info(self.w3, token1_address)

        sqrt_price_x96 = slot0[0]
        tick = slot0[1]

        reserve0 = Decimal(0)
        reserve1 = Decimal(0)

        return LiquidityPool(
            address=pool_address,
            dex_protocol=self.protocol,
            token0=token0_info,
            token1=token1_info,
            reserve0=reserve0,
            reserve1=reserve1,
            total_supply=wei_to_decimal(liquidity, 18),
            fee_tier=Decimal(fee) / Decimal(1000000),
            tick=tick,
            sqrt_price_x96=sqrt_price_x96,
        )

    def get_pool_reserves_at_block(
        self, pool_address: str, block_number: int
    ) -> Tuple[Decimal, Decimal]:
        """Get pool reserves at a specific block (approximated for V3)."""
        pool_contract = self.w3.eth.contract(address=pool_address, abi=self._pool_abi)

        try:
            liquidity = pool_contract.functions.liquidity().call(  # noqa
                block_identifier=block_number
            )
            slot0 = pool_contract.functions.slot0().call(block_identifier=block_number)

            sqrt_price_x96 = slot0[0]  # noqa
            tick = slot0[1]  # noqa

            reserve0 = Decimal(0)
            reserve1 = Decimal(0)

            return reserve0, reserve1
        except Exception:
            return Decimal(0), Decimal(0)

    def find_pool_address(
        self, token0: str, token1: str, fee_tier: Optional[int] = None
    ) -> Optional[str]:
        """Find Uniswap V3 pool address for token pair and fee tier."""
        if not fee_tier:
            fee_tiers = [500, 3000, 10000]
        else:
            fee_tiers = [fee_tier]

        factory_contract = self.w3.eth.contract(
            address=self.router_address, abi=self._factory_abi
        )

        token0, token1 = sort_tokens(token0, token1)

        for fee in fee_tiers:
            try:
                pool_address = factory_contract.functions.getPool(
                    token0, token1, fee
                ).call()
                if not pool_address == "0x0000000000000000000000000000000000000000":
                    return pool_address
            except Exception:
                continue

        return None

    def decode_liquidity_event(self, log: LogReceipt) -> LiquidityEvent:
        """Decode Uniswap V3 Mint/Burn event."""
        topic = log["topics"][0].hex()

        if topic == self.MINT_EVENT_SIGNATURE:
            event_type = "mint"
            sender = "0x" + log["topics"][1].hex()[-40:]
            owner = "0x" + log["topics"][2].hex()[-40:]
        elif topic == self.BURN_EVENT_SIGNATURE:
            event_type = "burn"
            owner = "0x" + log["topics"][1].hex()[-40:]
            sender = owner
        else:
            raise ValueError("Not a liquidity event")

        pool_address = log["address"]
        data = log["data"]

        tick_lower = int.from_bytes(data[0:32], "big", signed=True)  # noqa
        tick_upper = int.from_bytes(data[32:64], "big", signed=True)  # noqa
        amount = int.from_bytes(data[64:96], "big")
        amount0 = int.from_bytes(data[96:128], "big")
        amount1 = int.from_bytes(data[128:160], "big")

        pool_contract = self.w3.eth.contract(address=pool_address, abi=self._pool_abi)
        token0_address = pool_contract.functions.token0().call()
        token1_address = pool_contract.functions.token1().call()

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
            liquidity_delta=wei_to_decimal(amount, 18),
        )

    def get_liquidity_events_from_transaction(
        self, tx_hash: str
    ) -> List[LiquidityEvent]:
        """Extract all liquidity events from a transaction."""
        receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        events = []

        for log in receipt["logs"]:
            try:
                topic = log["topics"][0].hex()
                if topic in [self.MINT_EVENT_SIGNATURE, self.BURN_EVENT_SIGNATURE]:
                    event = self.decode_liquidity_event(log)
                    events.append(event)
            except Exception:
                continue

        return events

    def calculate_price_impact(self, swap: SwapEvent, pool: LiquidityPool) -> Decimal:
        """Calculate price impact for Uniswap V3 (simplified)."""
        if not pool.sqrt_price_x96:
            return Decimal(0)

        current_price = Decimal(pool.sqrt_price_x96) ** 2 / (Decimal(2) ** 192)

        if swap.amount_in == 0:
            return Decimal(0)

        price_change = swap.amount_out / swap.amount_in

        if current_price == 0:
            return Decimal(0)

        return abs((price_change - current_price) / current_price)

    def get_token_price(
        self, token_address: str, block_number: Optional[int] = None
    ) -> Optional[Decimal]:
        """Get token price in ETH using Uniswap V3."""
        weth_address = "0xC02aaA39b223FE8d0A0e5C4F27eAD9083C756Cc2"

        pool_address = self.find_pool_address(token_address, weth_address)
        if not pool_address:
            return None

        try:
            pool_contract = self.w3.eth.contract(
                address=pool_address, abi=self._pool_abi
            )

            if block_number:
                slot0 = pool_contract.functions.slot0().call(
                    block_identifier=block_number
                )
            else:
                slot0 = pool_contract.functions.slot0().call()

            sqrt_price_x96 = slot0[0]

            if sqrt_price_x96 == 0:
                return Decimal(0)

            price = (Decimal(sqrt_price_x96) ** 2) / (Decimal(2) ** 192)

            pool = self.get_pool_info(pool_address)
            if pool.token0.address.lower() == token_address.lower():
                return price
            else:
                return Decimal(1) / price if price > 0 else Decimal(0)
        except Exception:
            return None

    def is_swap_transaction(
        self,
        transaction: Dict[str, Any],  # noqa
        logs: List[Dict[str, Any]],
    ) -> Tuple[bool, int]:
        """Detect if transaction contains Uniswap V3 swaps."""
        swap_count = 0

        for log in logs:
            if len(log.get("topics", [])) > 0:
                if log["topics"][0].hex() == self.SWAP_EVENT_SIGNATURE:
                    swap_count += 1

        return swap_count > 0, swap_count

    def is_liquidity_transaction(
        self,
        transaction: Dict[str, Any],  # noqa
        logs: List[Dict[str, Any]],
    ) -> Tuple[bool, int]:
        """Detect if transaction contains Uniswap V3 liquidity operations."""
        liquidity_count = 0

        for log in logs:
            if len(log.get("topics", [])) > 0:
                topic = log["topics"][0].hex()
                if topic in [self.MINT_EVENT_SIGNATURE, self.BURN_EVENT_SIGNATURE]:
                    liquidity_count += 1

        return liquidity_count > 0, liquidity_count
