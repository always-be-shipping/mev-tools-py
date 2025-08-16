# mev-tools-py

Python tools for MEV (Maximal Extractable Value) analysis and
monitoring on Ethereum and other EVM-compatible blockchains.

## Installation

```bash
pip install .
```

Or, for development:

```bash
git clone https://github.com/yourusername/mev-tools-py.git
cd mev-tools-py
uv sync
```

## Usage

### As a Library

```python
from web3 import Web3
from mev_tools.mev_share.bundles import get_block_bundles

rpc_url = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
w3 = Web3(Web3.HTTPProvider(rpc_url))

block_number = 123
origin_tx_topic = "0xdeadbeef"
refund_address = "0xfeebdaed"

bundles = get_mev_bundles(
  w3=w3,
  block_number=block_number,
  origin_topic=origin_tx_topic,
  refund_address=refund_address,
)
```

## Project Structure

- `src/mev_tools_py/`: Core library code
- `tests/`: Unit tests

## License

MIT License
