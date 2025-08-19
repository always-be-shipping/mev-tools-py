from web3 import Web3
from typing import List, Dict, Any, cast


def _ensure_hex_prefix(hex_value: str) -> str:
    """Ensure hex string has 0x prefix."""
    return hex_value if hex_value.startswith("0x") else "0x" + hex_value


def get_mev_bundles(
    w3: Web3,
    block_number: int,
    origin_topic: str,
    refund_address: str,
) -> List[Dict[str, Any]]:
    block = w3.eth.get_block(block_number, full_transactions=True)
    logs = w3.eth.get_logs({"fromBlock": block_number, "toBlock": block_number})

    builder_address = str(block["miner"]).lower()
    txs = block["transactions"]

    logs_by_tx: Dict[str, List[Any]] = {}
    for log in logs:
        tx_hash = _ensure_hex_prefix(log["transactionHash"].hex())
        logs_by_tx.setdefault(tx_hash, []).append(log)

    bundles = []
    refund_txs = []
    last_refund_idx = None

    for i in reversed(range(len(txs))):
        tx = cast(Dict[str, Any], txs[i])
        tx_hash = _ensure_hex_prefix(cast(str, tx["hash"].hex()))

        # Check for refund
        tx_to = tx["to"]
        tx_from = tx["from"]
        if (
            tx_to is not None
            and str(tx_to).lower() == refund_address.lower()
            and str(tx_from).lower() == builder_address
        ):
            print("refund found", i)
            refund_txs.append(tx_hash)
            if last_refund_idx is None or i > last_refund_idx:
                last_refund_idx = i
            continue

        # Check for origin
        for log in logs_by_tx.get(tx_hash, []):
            if len(log["topics"]) == 0:
                continue
            if _ensure_hex_prefix(log["topics"][0].hex()) == origin_topic:
                if last_refund_idx is not None:
                    bundle = {
                        "origin_tx_hash": tx_hash,
                        "refund_tx_hashes": refund_txs[
                            ::-1
                        ],  # maintain chronological order
                        "bundle_tx_hashes": [
                            _ensure_hex_prefix(
                                cast(str, cast(Dict[str, Any], t)["hash"].hex())
                            )
                            for t in txs[i : last_refund_idx + 1]
                        ],
                    }
                    bundles.append(bundle)
                    refund_txs = []
                    last_refund_idx = None
                break  # found origin, move on

    bundles.reverse()

    return bundles
