# Integration Tests

This directory contains integration tests for the OEV protocol implementations. These tests validate the protocol processors against real blockchain data using live RPC connections.

## Overview

Integration tests differ from unit tests in that they:
- Make real RPC calls to Ethereum mainnet
- Test with actual liquidation transactions and events
- Validate protocol processors end-to-end
- May take longer to run due to network calls

## Configuration

### RPC Connection

Set your RPC endpoint via environment variable:

```bash
export ANKR_RPC_URL="https://rpc.ankr.com/eth"
```

Or copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your RPC settings
```

### Test Data

Known liquidation transactions are stored in `data/known_liquidations.json`. This file contains:
- Real transaction hashes with liquidations
- Block numbers and metadata
- Expected addresses and tokens
- Protocol-specific details

To add new test cases, update this file with verified liquidation transactions.

## Running Integration Tests

### All Tests (Unit + Integration)
```bash
uv run poe test
```

### Only Unit Tests (Skip Integration)
```bash
uv run pytest -m "not integration"
```

### Only Integration Tests
```bash
uv run pytest -m integration
```

### Specific Integration Test
```bash
uv run pytest tests/integration/test_oev_protocols.py::TestOEVProtocolsIntegration::test_aave_v3_real_liquidation_detection -v
```

### With Custom RPC
```bash
ANKR_RPC_URL=https://your-rpc-endpoint.com uv run pytest -m integration
```

### Skip Slow Tests
```bash
SKIP_SLOW_TESTS=true uv run pytest -m integration
```

## Test Categories

### Basic Validation
- `test_protocol_initialization`: Verify processors initialize correctly
- `test_web3_connection`: Check RPC connectivity
- `test_protocol_event_structure_validation`: Validate processor interfaces

### Protocol-Specific Tests
- `test_aave_v3_real_liquidation_detection`: Test Aave V3 with real liquidations
- `test_euler_protocols_detection`: Test Euler V1/V2 detection
- `test_morpho_protocol_integration`: Test Morpho with market data

### Cross-Protocol Analysis
- `test_cross_protocol_block_analysis`: Analyze blocks for multiple protocols
- `test_gas_efficiency_analysis`: Compare gas usage across protocols

### Robustness Testing
- `test_error_handling_robustness`: Validate error handling with invalid data

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANKR_RPC_URL` | `https://rpc.ankr.com/eth` | Ethereum RPC endpoint |
| `INTEGRATION_TEST_TIMEOUT` | `30` | Timeout for tests in seconds |
| `TEST_BLOCK_START` | `18500000` | Starting block for range tests |
| `TEST_BLOCK_END` | `18500010` | Ending block for range tests |
| `SKIP_SLOW_TESTS` | `false` | Skip slow-running tests |

## Adding New Test Cases

1. **Find a liquidation transaction** using a block explorer or your own analysis
2. **Verify the transaction** contains the expected protocol events
3. **Add to test data**:
   ```json
   {
     "protocol_name": [
       {
         "block": 18500000,
         "tx_hash": "0x...",
         "liquidator": "0x...",
         "user": "0x...",
         "description": "Description of the liquidation"
       }
     ]
   }
   ```
4. **Run the integration test** to validate it works correctly

## Troubleshooting

### RPC Connection Issues
- Verify your RPC URL is correct and accessible
- Check rate limits on your RPC provider
- Try a different RPC endpoint if issues persist

### Test Failures
- Some transactions in test data may no longer exist
- Network issues can cause intermittent failures
- Update test data with current, valid transaction hashes

### Slow Performance
- Set `SKIP_SLOW_TESTS=true` to skip time-intensive tests
- Use a faster RPC endpoint
- Reduce the block range for analysis tests

## Best Practices

1. **Keep test data current** - Verify transactions exist before adding
2. **Use meaningful descriptions** - Document what each test case represents
3. **Handle failures gracefully** - Network issues shouldn't break the test suite
4. **Limit API calls** - Be mindful of RPC rate limits
5. **Test edge cases** - Include failed liquidations, partial liquidations, etc.
