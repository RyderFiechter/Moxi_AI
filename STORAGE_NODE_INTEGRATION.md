# Storage Node Integration Guide

This document describes the storage node integration features added to `scripts/interact.ts`.

## Overview

The `interact.ts` script has been extended to integrate with local storage provider nodes, allowing you to:
- Detect and communicate with storage nodes
- Report storage availability to blockchain
- Interact with StorageRegistry smart contracts
- Automatically report storage updates

## New Dependencies

The following packages have been added:
- `systeminformation` - For getting real system disk information
- `axios` - For HTTP communication with storage node APIs

Install with:
```bash
npm install
```

## Features

### 1. Node Detection

**Function**: `detectLocalNode(host, port)`
- Detects storage nodes running on localhost
- Checks common ports (8000-8004)
- Returns node status including wallet address and storage info

**Usage in CLI**: Option 9 → Option 1

### 2. Node Lookup by Wallet

**Function**: `getNodeByWallet(walletAddress)`
- Searches multiple ports to find a node by wallet address
- Returns full node status information

**Usage in CLI**: Option 9 → Option 2

### 3. Storage Information

**Functions**:
- `getNodeStorage(walletAddress)` - Get available storage from node
- `getSystemDiskInfo()` - Get real system disk stats using systeminformation

**Usage in CLI**: Option 9 → Options 3-4

### 4. Storage Registry Integration

**Functions**:
- `offerStorage(registryAddress, providerAddress, storageGB, pricePerGB, signer)` - Offer storage to registry
- `updateStorage(registryAddress, providerAddress, storageGB, signer)` - Update storage availability

**Usage in CLI**: Option 9 → Options 6-7

### 5. Auto-Reporting

**Feature**: Periodic storage updates to registry
- Configurable interval (default: 300 seconds)
- Automatically detects node or uses system storage
- Updates registry contract with current availability

**Usage in CLI**: Option 9 → Option 8

## Storage Registry Contract Interface

The script includes a placeholder ABI for the StorageRegistry contract:

```typescript
const STORAGE_REGISTRY_ABI = [
  "function offerStorage(address provider, uint256 storageGB, uint256 pricePerGB) external",
  "function updateStorage(address provider, uint256 storageGB) external",
  "function getProviderInfo(address provider) external view returns (uint256 storageGB, uint256 pricePerGB, bool isActive)",
  "function registerProvider(address provider, uint256 storageGB, uint256 pricePerGB) external",
  "event StorageOffered(address indexed provider, uint256 storageGB, uint256 pricePerGB)",
  "event StorageUpdated(address indexed provider, uint256 storageGB)"
];
```

**Note**: Update this ABI to match your actual StorageRegistry contract when deployed.

## Usage Examples

### Basic Node Detection

1. Start your storage node: `cd node && python main.py`
2. Run interact script: `npm run interact`
3. Select option 9 (Storage Node Operations)
4. Select option 1 (Detect local storage node)

### Offer Storage to Registry

1. Run interact script
2. Select option 9 → Option 6
3. Enter StorageRegistry contract address
4. Enter provider address (defaults to your wallet)
5. Enter price per GB in ETH
6. Storage will be automatically detected from node or system

### Auto-Report Storage

1. Run interact script
2. Select option 9 → Option 8
3. Enter StorageRegistry contract address
4. Enter update interval (default: 300 seconds)
5. Script will periodically update storage availability
6. Press Enter to stop

## Node API Endpoints Used

The script communicates with storage nodes via HTTP:

- `GET /status` - Get node status (wallet, storage, uptime)
- `POST /ping` - Update node ping timestamp

Default node URL: `http://localhost:8000`

## Configuration

You can modify these constants in `interact.ts`:

```typescript
const DEFAULT_NODE_PORT = 8000;
const DEFAULT_NODE_HOST = "http://localhost";
```

## Integration with Existing Features

The storage node features are fully integrated with the existing CLI:
- All token operations (staking, rewards, transfers) remain unchanged
- Storage operations are accessible via option 9
- Storage functions work alongside blockchain interactions

## Error Handling

The script handles:
- Node not found (returns null, shows friendly message)
- Connection timeouts (2 second timeout)
- Invalid contract addresses
- Transaction failures

## Future Enhancements

Potential additions:
- Support for multiple nodes simultaneously
- Storage capacity planning and alerts
- Integration with DePIN token staking for storage providers
- Proof of storage verification
- Storage marketplace features

## Troubleshooting

### Node Not Detected

- Ensure storage node is running: `cd node && python main.py`
- Check node is on expected port (default: 8000)
- Verify node API is accessible: `curl http://localhost:8000/status`

### System Disk Info Errors

- Ensure `systeminformation` package is installed
- On some systems, may need elevated permissions
- Falls back gracefully if disk info unavailable

### Contract Interaction Errors

- Verify StorageRegistry contract address is correct
- Ensure contract ABI matches your deployed contract
- Check you have sufficient gas and permissions

## TypeScript Compatibility

- Fully typed with TypeScript
- Compatible with ethers.js v6
- Uses proper async/await patterns
- Type-safe contract interactions




