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
uv tools install commitizen poethepoet
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
poe install     # Install dependencies
poe dev         # Full development setup (install + format + lint + test)
poe test        # Run all tests (unit + integration)
poe coverage    # Run tests with coverage report
```

### Code Quality

```bash
poe lint        # Run linting
poe format      # Format code
poe typecheck   # Type checking
poe check       # Run all quality checks
poe fix         # Auto-fix style issues
```

### Testing Specific Files

```bash
poe test-file tests/enrich/test_transactions.py
poe test-function --file tests/oev/protocols/test_euler_v1.py --function test_decode_liquidation
```

### Integration Tests

Integration tests validate OEV protocol processors against real blockchain data using live RPC connections.

#### Setup

1. **Configure RPC endpoint**:

   ```bash
   export ANKR_RPC_URL="https://rpc.ankr.com/eth"
   ```

   Or copy and configure the environment file:

   ```bash
   cp .env.example .env
   # Edit .env with your RPC settings
   ```

2. **Available RPC options**:
   - **Ankr (free)**: `https://rpc.ankr.com/eth`
   - **Ankr (project)**: `https://rpc.ankr.com/eth/YOUR_PROJECT_ID`
   - **Infura**: `https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID`
   - **Alchemy**: `https://eth-mainnet.alchemyapi.io/v2/YOUR_ALCHEMY_API_KEY`

#### Running Integration Tests

```bash
# Run only unit tests (fast, no RPC required)
uv run pytest -m "not integration"

# Run only integration tests (requires RPC connection)
uv run pytest -m integration

# Run all tests (unit + integration)
poe test

# Run integration tests with custom RPC
ANKR_RPC_URL=https://your-rpc-endpoint.com uv run pytest -m integration

# Skip slow-running integration tests
SKIP_SLOW_TESTS=true uv run pytest -m integration

# Run specific integration test
uv run pytest tests/integration/test_oev_protocols.py::TestOEVProtocolsIntegration::test_aave_v3_real_liquidation_detection -v
```

#### Integration Test Categories

- **Protocol Validation**: Test protocol processors with real liquidation transactions
- **Cross-Protocol Analysis**: Analyze blocks containing multiple protocol liquidations
- **Gas Efficiency**: Compare gas usage patterns across different protocols
- **Error Handling**: Validate robustness with invalid data and edge cases
- **Market Data**: Test live contract interactions (Morpho market info, etc.)

#### Environment Variables

| Variable                   | Default                    | Description                    |
| -------------------------- | -------------------------- | ------------------------------ |
| `ANKR_RPC_URL`             | `https://rpc.ankr.com/eth` | Ethereum RPC endpoint          |
| `INTEGRATION_TEST_TIMEOUT` | `30`                       | Test timeout in seconds        |
| `TEST_BLOCK_START`         | `18500000`                 | Starting block for range tests |
| `TEST_BLOCK_END`           | `18500010`                 | Ending block for range tests   |
| `SKIP_SLOW_TESTS`          | `false`                    | Skip slow-running tests        |

#### Adding Test Cases

To add new liquidation test cases:

1. Find a liquidation transaction using a block explorer
2. Verify it contains the expected protocol events
3. Add to `tests/integration/data/known_liquidations.json`:

   ```json
   {
     "protocol_name": [
       {
         "block": 18500000,
         "tx_hash": "0x...",
         "liquidator": "0x...",
         "user": "0x...",
         "description": "Description of liquidation"
       }
     ]
   }
   ```

4. Run integration tests to validate

See `tests/integration/README.md` for detailed documentation.

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
4. Run quality checks: `poe check`
5. Run tests: `poe test`
6. Commit with conventional format: `uv run cz commit`
7. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.
