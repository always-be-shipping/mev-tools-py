from hexbytes import HexBytes
import pytest
from unittest.mock import MagicMock
from mev_tools_py.mev_share.bundles import get_mev_bundles

ORIGIN_TOPIC0 = "0xdeadbeef"
REFUND_ADDRESS = "0xrefundaddress"
BLOCK_BUILDER = "0xblockbuilder"


@pytest.fixture
def mock_web3():
    w3 = MagicMock()
    w3.eth.get_block.return_value = {
        "miner": BLOCK_BUILDER,
        "transactions": [
            # tx 0 = origin
            MagicMock(
                __getitem__=lambda self, key: {
                    "to": "0xSomeAddress",
                    "from": "0xnotrefund",
                    "hash": HexBytes("00" * 32),
                }[key],
            ),
            # tx 1 = normal
            MagicMock(
                __getitem__=lambda self, key: {
                    "to": "0xOther",
                    "from": "0xsomeone",
                    "hash": HexBytes("11" * 32),
                }[key],
            ),
            # tx 2 = refund
            MagicMock(
                __getitem__=lambda self, key: {
                    "to": REFUND_ADDRESS,
                    "from": BLOCK_BUILDER,
                    "hash": HexBytes("22" * 32),
                }[key],
            ),
        ],
    }

    # origin topic at tx 0
    w3.eth.get_logs.return_value = [
        {
            "transactionHash": HexBytes("00" * 32),
            "topics": [HexBytes(ORIGIN_TOPIC0)],
        }
    ]
    return w3


def test_single_bundle(mock_web3):
    bundles = get_mev_bundles(mock_web3, 123, ORIGIN_TOPIC0, REFUND_ADDRESS)
    assert len(bundles) == 1

    b = bundles[0]
    assert b["origin_tx_hash"] == "0x" + "00" * 32
    assert b["refund_tx_hashes"] == ["0x" + "22" * 32]
    assert b["bundle_tx_hashes"] == [
        "0x" + "00" * 32,
        "0x" + "11" * 32,
        "0x" + "22" * 32,
    ]
