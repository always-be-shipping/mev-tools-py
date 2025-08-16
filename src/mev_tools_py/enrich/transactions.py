from typing import List, Dict
from web3 import Web3


def enrich_tx(w3: Web3, tx_hash: str) -> Dict:
    """Enrich a transaction with additional details.

    Args:
    - w3 (Web3): An instance of Web3 connected to an Ethereum node.
    - tx_hash (str): The hash of the transaction to enrich.

    Returns:
    - Dict: A dictionary containing enriched transaction details.
    """

    tx = w3.eth.get_transaction(tx_hash)
    receipt = w3.eth.get_transaction_receipt(tx_hash)

    return {
        "hash": tx["hash"].hex(),
        "from": tx["from"],
        "to": tx["to"],
        "value": tx["value"],
        "gas": tx["gas"],
        "gas_price": tx["gasPrice"],
        "gas_used": receipt["gasUsed"],
        "input": tx["input"],
        "logs": receipt["logs"],
    }


def enrich_txs(w3: Web3, tx_hashes: List[str]) -> List[Dict]:
    """Enrich a list of transactions with additional details.

    Args:
    - w3 (Web3): An instance of Web3 connected to an Ethereum node.
    - tx_hashes (List[str]): A list of transaction hashes to enrich.

    Returns:
    - List[Dict]: A list of dictionaries containing enriched transaction details.
    """
    enriched = []
    for tx_hash in tx_hashes:
        enriched.append(enrich_tx(w3, tx_hash))

    return enriched
