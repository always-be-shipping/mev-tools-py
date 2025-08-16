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
            # tx 3 = origin
            MagicMock(
                __getitem__=lambda self, key: {
                    "to": "0xSomeAddress",
                    "from": "0xnotrefund",
                    "hash": HexBytes("33" * 32),
                }[key],
            ),
            # tx 4 = normal
            MagicMock(
                __getitem__=lambda self, key: {
                    "to": "0xOther",
                    "from": "0xsomeone",
                    "hash": HexBytes("44" * 32),
                }[key],
            ),
            # tx 5 = refund
            MagicMock(
                __getitem__=lambda self, key: {
                    "to": REFUND_ADDRESS,
                    "from": BLOCK_BUILDER,
                    "hash": HexBytes("55" * 32),
                }[key],
            ),
            # tx 6 = normal
            MagicMock(
                __getitem__=lambda self, key: {
                    "to": "0xOther",
                    "from": "0xsomeone",
                    "hash": HexBytes("66" * 32),
                }[key],
            ),
            # tx 7 = normal
            MagicMock(
                __getitem__=lambda self, key: {
                    "to": "0xOther",
                    "from": "0xsomeone",
                    "hash": HexBytes("77" * 32),
                }[key],
            ),
            # tx 8 = origin
            MagicMock(
                __getitem__=lambda self, key: {
                    "to": "0xSomeAddress",
                    "from": "0xnotrefund",
                    "hash": HexBytes("88" * 32),
                }[key],
            ),
            # tx 9 = normal
            MagicMock(
                __getitem__=lambda self, key: {
                    "to": "0xOther",
                    "from": "0xsomeone",
                    "hash": HexBytes("99" * 32),
                }[key],
            ),
            # tx 10 = refund
            MagicMock(
                __getitem__=lambda self, key: {
                    "to": REFUND_ADDRESS,
                    "from": BLOCK_BUILDER,
                    "hash": HexBytes("aa" * 32),
                }[key],
            ),
            # tx 11 = normal
            MagicMock(
                __getitem__=lambda self, key: {
                    "to": "0xOther",
                    "from": "0xsomeone",
                    "hash": HexBytes("bb" * 32),
                }[key],
            ),
            # tx 12 = refund
            MagicMock(
                __getitem__=lambda self, key: {
                    "to": REFUND_ADDRESS,
                    "from": BLOCK_BUILDER,
                    "hash": HexBytes("cc" * 32),
                }[key],
            ),
        ],
    }

    w3.eth.get_logs.return_value = [
        {
            "transactionHash": HexBytes("00" * 32),
            "topics": [HexBytes(ORIGIN_TOPIC0)],
        },
        {
            "transactionHash": HexBytes("33" * 32),
            "topics": [HexBytes(ORIGIN_TOPIC0)],
        },
        {
            "transactionHash": HexBytes("88" * 32),
            "topics": [HexBytes(ORIGIN_TOPIC0)],
        },
    ]
    return w3


def test_single_bundle(mock_web3):
    bundles = get_mev_bundles(mock_web3, 123, ORIGIN_TOPIC0, REFUND_ADDRESS)
    assert len(bundles) == 3

    b = bundles[0]
    assert b["origin_tx_hash"] == "0x" + "00" * 32
    assert b["refund_tx_hashes"] == ["0x" + "22" * 32]
    assert b["bundle_tx_hashes"] == [
        "0x" + "00" * 32,
        "0x" + "11" * 32,
        "0x" + "22" * 32,
    ]

    b = bundles[1]
    assert b["origin_tx_hash"] == "0x" + "33" * 32
    assert b["refund_tx_hashes"] == ["0x" + "55" * 32]
    assert b["bundle_tx_hashes"] == [
        "0x" + "33" * 32,
        "0x" + "44" * 32,
        "0x" + "55" * 32,
    ]

    b = bundles[2]
    assert b["origin_tx_hash"] == "0x" + "88" * 32
    assert b["refund_tx_hashes"] == [
        "0x" + "aa" * 32,
        "0x" + "cc" * 32,
    ]
    assert b["bundle_tx_hashes"] == [
        "0x" + "88" * 32,
        "0x" + "99" * 32,
        "0x" + "aa" * 32,
        "0x" + "bb" * 32,
        "0x" + "cc" * 32,
    ]
