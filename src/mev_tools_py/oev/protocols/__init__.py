"""OEV protocol processors for detecting and analyzing liquidations."""

from mev_tools_py.oev.protocols.base import BaseProtocolProcessor
from mev_tools_py.oev.protocols.aave_v3 import AaveV3ProtocolProcessor
from mev_tools_py.oev.protocols.euler_v1 import EulerProtocolProcessor
from mev_tools_py.oev.protocols.euler_v2 import EulerV2ProtocolProcessor

__all__ = [
    "BaseProtocolProcessor",
    "AaveV3ProtocolProcessor",
    "EulerProtocolProcessor",
    "EulerV2ProtocolProcessor",
]
