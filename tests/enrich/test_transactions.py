from hexbytes import HexBytes
import pytest
from unittest.mock import MagicMock
from mev_tools_py.enrich.transactions import enrich_txs, enrich_tx


@pytest.fixture
def mock_web3():
    w3 = MagicMock()

    # Mock get_transaction
    def get_transaction(tx_hash):
        return MagicMock(
            hash=bytes.fromhex(tx_hash[2:]),
            **{
                "__getitem__": lambda self, key: {
                    "hash": HexBytes(tx_hash),
                    "from": "0xorigin",
                    "to": "0xtarget",
                    "value": 123,
                    "gas": 21000,
                    "gasPrice": 1000000000,
                    "input": "0xdeadbeef",
                }[key]
            },
        )

    # Mock get_transaction_receipt
    def get_receipt(tx_hash):
        return {
            "gasUsed": 21000,
            "logs": [
                {
                    "address": "0xlogsource",
                    "topics": [HexBytes("abcd" * 8)],
                    "data": "0xdata",
                    "logIndex": 0,
                    "transactionIndex": 1,
                    "blockNumber": 123,
                }
            ],
        }

    w3.eth.get_transaction.side_effect = get_transaction
    w3.eth.get_transaction_receipt.side_effect = get_receipt

    return w3


def test_enrich_tx(mock_web3):
    tx_hash = "0x" + "aa" * 32
    tx = enrich_tx(mock_web3, tx_hash)

    assert tx["from"] == "0xorigin"
    assert tx["to"] == "0xtarget"
    assert tx["value"] == 123
    assert tx["gas"] == 21000
    assert tx["gas_price"] == 1000000000
    assert tx["gas_used"] == 21000
    assert tx["input"] == "0xdeadbeef"
    assert len(tx["logs"]) == 1
    assert tx["logs"][0]["address"] == "0xlogsource"
    assert tx["logs"][0]["topics"][0].to_0x_hex() == "0x" + "abcd" * 8


def test_enrich_txs(mock_web3):
    tx_hashes = ["0x" + "aa" * 32, "0x" + "bb" * 32]
    result = enrich_txs(mock_web3, tx_hashes)

    for tx in result:
        assert tx["from"] == "0xorigin"
        assert tx["to"] == "0xtarget"
        assert tx["value"] == 123
        assert tx["gas"] == 21000
        assert tx["gas_price"] == 1000000000
        assert tx["gas_used"] == 21000
        assert tx["input"] == "0xdeadbeef"
        assert len(tx["logs"]) == 1
        assert tx["logs"][0]["address"] == "0xlogsource"
        assert tx["logs"][0]["topics"][0].to_0x_hex() == "0x" + "abcd" * 8
