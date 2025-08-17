# mev-tools-py

Python tools for MEV (Maximal Extractable Value) and OEV (Oracle Extractable Value) analysis, monitoring, and research on Ethereum and other EVM-compatible blockchains.

## Features

- **MEV Share Bundle Analysis**: Extract and analyze MEV Share bundles from blocks
- **Transaction Enrichment**: Add detailed information to transaction data
- **OEV Protocol Support**: Analyze liquidations across multiple DeFi protocols
- **Extensible Architecture**: Plugin-based system for adding new protocols

## Installation

### From PyPI

```bash
pip install mev-tools-py
```

### For Development

```bash
git clone https://github.com/yourusername/mev-tools-py.git
cd mev-tools-py
uv sync
```

## Quick Start

### MEV Share Bundle Analysis

```python
from web3 import Web3
from mev_tools_py.mev_share.bundles import get_mev_bundles

# Setup Web3 connection
rpc_url = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Extract MEV bundles from a block
bundles = get_mev_bundles(
    w3=w3,
    block_number=18500000,
    origin_topic="0x...", # MEV Share origin transaction topic
    refund_address="0x..." # Builder refund address
)

for bundle in bundles:
    print(f"Bundle with {len(bundle['bundle_tx_hashes'])} transactions")
    print(f"Origin: {bundle['origin_tx_hash']}")
    print(f"Refunds: {bundle['refund_tx_hashes']}")
```

### Transaction Enrichment

```python
from web3 import Web3
from mev_tools_py.enrich.transactions import enrich_tx, enrich_txs

w3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"))

# Enrich a single transaction
tx_hash = "0x..."
enriched_tx = enrich_tx(w3, tx_hash)
print(f"Gas used: {enriched_tx['gas_used']}")
print(f"Logs: {len(enriched_tx['logs'])}")

# Enrich multiple transactions
tx_hashes = ["0x...", "0x..."]
enriched_txs = enrich_txs(w3, tx_hashes)
```

### OEV Protocol Analysis

```python
from mev_tools_py.oev.protocols.euler_v1 import EulerProtocolProcessor
from mev_tools_py.oev.protocols.euler_v2 import EulerV2ProtocolProcessor

# Initialize protocol processors
euler_v1 = EulerProtocolProcessor()
euler_v2 = EulerV2ProtocolProcessor()

# Analyze a transaction for liquidations
transaction = w3.eth.get_transaction("0x...")
receipt = w3.eth.get_transaction_receipt("0x...")

if euler_v1.is_liquidation_transaction(transaction, receipt['logs']):
    for log in receipt['logs']:
        try:
            liquidation = euler_v1.decode_liquidation(log)
            enriched = euler_v1.enrich_event(liquidation)
            print(f"Euler V1 liquidation: {enriched}")
        except ValueError:
            continue  # Not an Euler liquidation log
```

## Development

This project uses [poethepoet](https://poethepoet.natn.io/) as a task runner. Available commands:

### Setup and Testing

```bash
uv run poe install     # Install dependencies
uv run poe dev         # Full development setup (install + format + lint + test)
uv run poe test        # Run all tests
uv run poe coverage    # Run tests with coverage report
```

### Code Quality

```bash
uv run poe lint        # Run linting
uv run poe format      # Format code
uv run poe typecheck   # Type checking
uv run poe check       # Run all quality checks
uv run poe fix         # Auto-fix style issues
```

### Testing Specific Files

```bash
uv run poe test-file tests/enrich/test_transactions.py
uv run poe test-function --file tests/oev/protocols/test_euler_v1.py --function test_decode_liquidation
```

## Project Structure

```
src/mev_tools_py/
├── __init__.py              # Main package
├── mev_share/
│   └── bundles.py          # MEV Share bundle extraction
├── enrich/
│   └── transactions.py     # Transaction enrichment utilities
└── oev/
    ├── __init__.py
    └── protocols/
        ├── base.py         # Abstract base for protocol processors
        ├── euler_v1.py     # Euler V1 liquidation processor
        └── euler_v2.py     # Euler V2 liquidation processor
tests/                      # Unit tests mirroring src structure
```

## Supported Protocols

### OEV/Liquidation Analysis

- **Euler V1**: Complete liquidation event decoding and analysis
- **Euler V2**: Vault-based liquidation support with batch operations
- **Extensible**: Easy to add new protocols via `BaseProtocolProcessor`

## Requirements

- Python ≥ 3.13
- web3.py ≥ 7.13.0

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run quality checks: `uv run poe check`
5. Run tests: `uv run poe test`
6. Commit with conventional format: `uv run cz commit`
7. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.
