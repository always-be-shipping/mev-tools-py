from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseProtocolProcessor(ABC):
    """Abstract base class for protocol-specific liquidation processors."""

    protocol: str  # e.g. "aave", "compound", "maker"

    @abstractmethod
    def decode_liquidation(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode a raw log into a structured liquidation event.

        Must return a dict with at least:
          - protocol
          - liquidator
          - user
          - debt_repaid
          - collateral_seized
        """
        raise NotImplementedError

    @abstractmethod
    def enrich_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a decoded liquidation event with protocol-specific analytics.
        Example: health factor, liquidation bonus, etc.
        """
        raise NotImplementedError
