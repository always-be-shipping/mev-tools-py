from abc import abstractmethod
from typing import List, Tuple
from decimal import Decimal

from mev_tools_py.dex.base import BaseDexReader
from mev_tools_py.dex.models import (
    LiquidityPool,
    ArbitrageOpportunity,
    VolumeStatistics,
)


class EnhancedDexReader(BaseDexReader):
    """Extended DEX reader with additional analytics capabilities."""

    @abstractmethod
    def get_top_pools_by_volume(
        self, limit: int = 10, time_period: str = "24h"
    ) -> List[LiquidityPool]:
        """Get top pools by trading volume."""
        raise NotImplementedError

    @abstractmethod
    def get_arbitrage_opportunities(
        self, token_pairs: List[Tuple[str, str]]
    ) -> List[ArbitrageOpportunity]:
        """Identify potential arbitrage opportunities."""
        raise NotImplementedError

    @abstractmethod
    def calculate_impermanent_loss(
        self, pool_address: str, from_block: int, to_block: int
    ) -> Decimal:
        """Calculate impermanent loss for liquidity providers."""
        raise NotImplementedError

    @abstractmethod
    def get_volume_statistics(
        self, pool_address: str, from_block: int, to_block: int
    ) -> VolumeStatistics:
        """Get volume statistics for a pool over a time period."""
        raise NotImplementedError
