from abc import ABC, abstractmethod
from typing import Any, Dict, List


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

    @abstractmethod
    def is_liquidation_transaction(
        self, transaction: Dict[str, Any], logs: List[Dict[str, Any]]
    ) -> bool:
        """
        Detect if a given transaction contains a liquidation from this protocol.

        Args:
            transaction: The transaction data (hash, to, from, input, etc.)
            logs: List of event logs emitted by the transaction

        Returns:
            True if the transaction contains a liquidation from this protocol, False otherwise
        """
        raise NotImplementedError
