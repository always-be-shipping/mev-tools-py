from web3 import Web3
from typing import List, Dict


def get_mev_bundles(
    w3: Web3,
    block_number: int,
    origin_topic: str,
    refund_address: str,
) -> List[Dict]:
    block = w3.eth.get_block(block_number, full_transactions=True)
    logs = w3.eth.get_logs({"fromBlock": block_number, "toBlock": block_number})

    builder_address = block["miner"].lower()
    txs = block["transactions"]

    logs_by_tx = {}
    for log in logs:
        tx_hash = log["transactionHash"].to_0x_hex()
        logs_by_tx.setdefault(tx_hash, []).append(log)

    bundles = []
    refund_txs = []
    last_refund_idx = None

    for i in reversed(range(len(txs))):
        tx = txs[i]
        tx_hash = tx["hash"].to_0x_hex()

        # Check for refund
        if (
            tx["to"].lower() == refund_address.lower()
            and tx["from"].lower() == builder_address
        ):
            print("refund found", i)
            refund_txs.append(tx_hash)
            if last_refund_idx is None or i > last_refund_idx:
                last_refund_idx = i
            continue

        # Check for origin
        for log in logs_by_tx.get(tx_hash, []):
            if log["topics"][0].to_0x_hex() == origin_topic:
                if last_refund_idx is not None:
                    bundle = {
                        "origin_tx_hash": tx_hash,
                        "refund_tx_hashes": refund_txs[
                            ::-1
                        ],  # maintain chronological order
                        "bundle_tx_hashes": [
                            t["hash"].to_0x_hex() for t in txs[i : last_refund_idx + 1]
                        ],
                    }
                    bundles.append(bundle)
                    refund_txs = []
                    last_refund_idx = None
                break  # found origin, move on

    bundles.reverse()

    return bundles
