# Storage Provider Node - Complete Client Application

A complete, modular client-side application for running a storage provider node in a decentralized storage network. Features real system statistics, blockchain integration, and a web-based dashboard.

## Features

- 🆔 **Unique Node Identity**: Generates or loads wallet address from JSON file
- 💾 **Real System Stats**: Uses `psutil` to report actual disk storage (total, used, free)
- ⏱️ **Real Uptime**: Tracks actual process uptime since node start
- 📡 **HTTP API**: FastAPI-based REST API for monitoring and configuration
- 🔗 **Blockchain Integration**: Register and manage storage on-chain via StorageRegistry contract
- 💰 **Payment Wallet Management**: Separate wallet for receiving payments
- ✅ **Opt-in/Opt-out**: Enable or disable storage lending
- 🌐 **Web Dashboard**: Beautiful web UI for node management
- 🔄 **Auto-updates**: Automatic storage updates to blockchain registry
- ⚙️ **Configurable**: JSON config file for all settings

## Requirements

- Python 3.10 or higher
- Core dependencies: `fastapi`, `uvicorn`, `psutil`
- **Optional (blockchain features)**: `web3` and friends. Install only if you plan to use the registry client.

## Installation

1. Install the core dependencies:
```bash
cd node
pip install -r requirements.txt
```

2. (Optional) Enable blockchain/registry integrations. This step requires a compiler toolchain (MSVC on Windows, build-essential on Linux). When you're ready:
```bash
pip install -r requirements-web3.txt
```

3. Configure your node in `config.json` (see Configuration section)

4. (Optional) Set `PRIVATE_KEY` environment variable for blockchain transactions:
```bash
export PRIVATE_KEY=your_private_key_here
```

## Quick Start

### Basic Usage

Run the node with default settings:

```bash
python main.py
```

The node will:
- Generate or load a wallet address
- Start reporting real system storage stats
- Launch HTTP API on port 8000
- Serve web dashboard at `http://localhost:8000/ui`

### With Blockchain Integration

1. Deploy the `StorageRegistry` contract (see `contracts/StorageRegistry.sol`)
2. Update `config.json` with registry settings:
```json
{
  "registry": {
    "contract_address": "0x...",
    "rpc_url": "https://arbitrum-sepolia.infura.io/v3/YOUR_KEY",
    "auto_register": true,
    "auto_update_interval": 300
  }
}
```
3. Set `PRIVATE_KEY` environment variable
4. Run the node: `python main.py`

## Command Line Interface

Install the dependencies and then use the bundled CLI to start the node or mirror every control available on the storage dashboard without opening the dapp:

```bash
# From the repository root
cd node
python -m node.cli --help
```

Key commands:

- `python -m node.cli run --config config.json` – start the node and HTTP API (same as `python main.py`).
- `python -m node.cli status` – show live metrics identical to `/storage` in the dapp.
- `python -m node.cli config set-payment 0xabc...` – update the payment wallet.
- `python -m node.cli storage enable|disable` – toggle storage lending.
- `python -m node.cli registry register --storage-gb 100 --price-per-gb 0.001` – register or update offers.
- `python -m node.cli registry activate|deactivate` – manage registry activity state.
- `python -m node.cli rewards payout` – send pending MOXI payouts.
- `python -m node.cli dashboard` – launch an interactive Rich-powered dashboard that mirrors the `/storage` page (live metrics, buttons for every action).

Pass `--api-base http://host:port` (or set `MOXI_NODE_API`) to point the CLI at a remote node.

## Desktop GUI

Prefer a desktop window instead of the terminal? Launch the Tkinter-based UI that mirrors the storage page:

```bash
cd node
python -m node.gui --api-base http://localhost:8000 --refresh 5
```

The window refreshes the same metrics (wallets, storage totals, earnings, registry state) and provides identical buttons: update payment wallet, toggle storage lending, register/update offers, activate/deactivate, refresh storage, and send payouts.  
The register flow now reuses the node's configured on-chain price—just enter the storage amount and the app handles the rest. The payout button shows the destination wallet and only enables when there is a non-zero pending balance.
To ship it as a standalone app, use your favorite packager—for example:

```bash
pip install pyinstaller
cd node
pyinstaller --windowed --name MoxiNodeDashboard gui.py
```

The generated binary under `dist/` can be pinned to your desktop/dock.

## Configuration

### Config File (`config.json`)

```json
{
  "port": 8000,
  "host": "0.0.0.0",
  "ping_interval": 30,
  "identity_file": "node_identity.json",
  "wallet_address": "0x4d6e685750fc78647b60589bee395d12b154b900",
  "payment_wallet": "0x4d6e685750fc78647b60589bee395d12b154b900",
  "storage_lending_enabled": false,
  "storage": {
    "mount_path": "/mnt/moxi-node",
    "mapper_name": "moxi-node",
    "backing_file": "/var/moxi-node/storage-node.img"
  },
  "registry": {
    "contract_address": "",
    "rpc_url": "",
    "chain_id": 421614,
    "auto_register": false,
    "auto_update_interval": 300,
    "price_per_gb_eth": "0.001"
  }
}
```

### Configuration Options

- **port**: HTTP API port (default: 8000)
- **host**: Bind address (default: "0.0.0.0")
- **ping_interval**: Seconds between internal pings (default: 30)
- **wallet_address**: Node identity wallet (auto-generated if not set)
- **payment_wallet**: Wallet to receive payments (defaults to wallet_address)
- **storage_lending_enabled**: Whether storage lending is enabled
- **storage.mount_path**: Filesystem path the node measures/commits against
- **storage.mapper_name**: Logical name for the encrypted mapper (documentation only)
- **storage.backing_file**: Sparse file or block device for the encrypted volume (defaults to `/var/moxi-node/storage-node.img`; create the directory via `sudo mkdir -p /var/moxi-node && sudo chown $USER /var/moxi-node`)
- **registry.contract_address**: StorageRegistry contract address
- **registry.rpc_url**: Blockchain RPC endpoint
- **registry.auto_register**: Automatically register on startup
- **registry.auto_update_interval**: Auto-update storage every N seconds (0 to disable)

## Encrypted Storage Provisioning

1. **Create the encrypted volume (Linux example)**
   ```bash
   cd node/scripts
   sudo CONTROLLER_PRIVATE_KEY=0xyourcontrollerkey \
        VOLUME_SIZE_GB=200 \
        VOLUME_FILE=/var/moxi-node/storage-node01.img \
        MAPPER_NAME=node01-crypt \
        MOUNT_POINT=/mnt/node01 \
        ./setup_encrypted_volume.sh create
   ```
   The script derives a LUKS passphrase from `CONTROLLER_PRIVATE_KEY`, creates a sparse image, encrypts it with `cryptsetup`, formats it, and mounts it. Use `open` / `close` modes later to remount without wiping data.

2. **Point the node at the mount path**
   Update `config.json` with the same mount point:
   ```json
   "storage": {
     "mount_path": "/mnt/node01",
     "mapper_name": "node01-crypt",
     "backing_file": "/var/moxi-node/storage-node01.img"
   }
   ```
   The node now reports totals/availables from this filesystem instead of `/`, so the “locked” capacity shows up as an actual mounted volume.

3. **Unlock via the controller key**
   The same controller/private key that coordinates your nodes is also the source of truth for the LUKS passphrase. Rotate the controller key to rotate storage keys; nodes never see plaintext credentials beyond their derived key material.

## Remote Access & Controller Workflow

- **Expose mounted storage securely**: Share `/mnt/node01` via SSHFS/NFS/Samba once it is opened. Example from another host:
  ```bash
  sshfs nodeuser@node-ip:/mnt/node01 /mnt/controller/node01
  ```
  Reads/writes flow through the encrypted filesystem; data at rest remains sealed inside the LUKS volume.
- **Controller orchestration**: Your controller/load-balancer keeps the private key, unlocks volumes via `setup_encrypted_volume.sh open`, and instructs each node how much to commit. Because the node process tracks `storage.mount_path`, `committed_storage_gb`, and registry state, the dashboard reflects only the space that the controller has actually unlocked.
- **Shutdown / rotation**: Run `sudo ./setup_encrypted_volume.sh close` before powering down or migrating disks so the mapper detaches cleanly. Ship the `*.img` file to a new machine, rerun `open`, and the node will immediately detect the filesystem.

## Web Dashboard

Access the web dashboard at `http://localhost:8000/ui`

Features:
- View real-time node status
- Update payment wallet address
- Enable/disable storage lending
- Trigger on-demand MOXI payouts without disabling lending
- Register with blockchain registry
- Update storage availability
- Activate/deactivate in registry

Rewards accrue at a fixed rate of **1 MOXI per hour for every 10 GB** of committed storage. Pending balances remain active while lending is enabled and can be sent to your payment wallet via the payout endpoint or dashboard button at any time.

## HTTP API Endpoints

### Node Status

- **GET `/status`** - Get current node status
- **GET `/config`** - Get node configuration
- **GET `/health`** - Health check

### Configuration

- **PUT `/payment-wallet`** - Update payment wallet address
- **POST `/storage-lending/enable`** - Enable storage lending
- **POST `/storage-lending/disable`** - Disable storage lending
- **POST `/payout`** - Send pending MOXI earnings to the payment wallet

### Blockchain Registry

- **GET `/registry/status`** - Get registry status
- **POST `/registry/register`** - Register with StorageRegistry
- **POST `/registry/update`** - Update storage in registry
- **POST `/registry/activate`** - Activate provider (opt-in)
- **POST `/registry/deactivate`** - Deactivate provider (opt-out)
- **PUT `/registry/payment-wallet`** - Update payment wallet in registry

### Documentation

- **GET `/docs`** - Interactive API documentation (Swagger UI)
- **GET `/ui`** - Web dashboard

## MOXI Payout Configuration

Triggering `POST /payout` (or the dashboard button) now signs and broadcasts a real ERC-20 `transfer` so your payment wallet receives MOXI on-chain. Configure it by:

1. Deploying/funding the `DePINToken` (or whichever ERC-20 you want to distribute) with the wallet whose private key the node controls.
2. Filling in the `token` block inside `node/config.json`:
   ```jsonc
   "token": {
     "address": "0xYourTokenAddress",
     "rpc_url": "https://arb-sepolia.example", // leave blank to reuse registry.rpc_url
     "private_key": ""                         // optional override; falls back to PRIVATE_KEY
   }
   ```
   You can also set `TOKEN_ADDRESS` as an environment variable; when unset, payouts reuse the registry RPC URL and the `PRIVATE_KEY`.
3. Restarting the node. Startup logs will include `✅ Token payout client initialized` once everything is wired up.

If any field is missing the `/payout` endpoint returns `503` so you know to finish configuration. Successful calls return the actual transaction hash, block number, gas used, and the pending balance after settlement.

## Project Structure

```
node/
├── main.py                  # Entry point - launches node and API server
├── node.py                  # Node class with real system stats
├── node_api.py              # FastAPI application with endpoints
├── config.json              # Configuration file
├── node_identity.json       # Generated node identity
├── requirements.txt         # Python dependencies
├── contracts/
│   └── StorageRegistry.sol  # Smart contract for storage registry
├── blockchain/
│   ├── __init__.py
│   ├── web3_config.py       # Web3 configuration
│   └── registry.py          # StorageRegistry client
└── ui/
    ├── index.html           # Web dashboard
    ├── style.css            # Dashboard styles
    └── app.js               # Dashboard JavaScript
```

## StorageRegistry Smart Contract

The `StorageRegistry` contract allows providers to:
- Register with payment wallet, storage amount, and pricing
- Update storage availability
- Update pricing
- Update payment wallet
- Activate/deactivate (opt-in/opt-out)

Deploy the contract from `contracts/StorageRegistry.sol` and set the address in `config.json`.

## Node Identity

The node saves its identity to `node_identity.json`:

```json
{
  "wallet_address": "0xA9f23...E21",
  "payment_wallet": "0xA9f23...E21",
  "storage_lending_enabled": false,
  "created_at": "2025-11-11T19:45:00"
}
```

The wallet address persists between runs, so your node keeps the same identity.

## System Stats

The node uses `psutil` to report:
- **Total Storage**: Real disk capacity in GB
- **Free Storage**: Available disk space in GB
- **Used Storage**: Calculated as total - free
- **Uptime**: Time since node process started

On Windows, it uses the `C:\` drive. On Linux/Mac, it uses the root filesystem (`/`).

## Usage Examples

### Using the Web Dashboard

1. Start the node: `python main.py`
2. Open browser: `http://localhost:8000/ui`
3. Configure payment wallet, enable storage lending
4. Register with blockchain registry (if configured)

### Using the API

```bash
# Get node status
curl http://localhost:8000/status

# Update payment wallet
curl -X PUT http://localhost:8000/payment-wallet \
  -H "Content-Type: application/json" \
  -d '{"payment_wallet": "0x..."}'

# Enable storage lending
curl -X POST http://localhost:8000/storage-lending/enable

# Register with registry
curl -X POST http://localhost:8000/registry/register \
  -H "Content-Type: application/json" \
  -d '{"storage_gb": 100, "price_per_gb_eth": 0.001}'
```

### Using Python

```python
import requests

# Get status
response = requests.get("http://localhost:8000/status")
print(response.json())

# Update payment wallet
response = requests.put(
    "http://localhost:8000/payment-wallet",
    json={"payment_wallet": "0x..."}
)
print(response.json())
```

## Blockchain Integration

### Prerequisites

1. Deploy `StorageRegistry` contract
2. Get RPC URL (e.g., from Infura, Alchemy, or public RPC)
3. Set `PRIVATE_KEY` environment variable (for signing transactions)

### Auto-Registration

Set `auto_register: true` in config to automatically register on startup.

### Auto-Updates

Set `auto_update_interval` (in seconds) to automatically update storage availability. Set to `0` to disable.

## Security Notes

- **Never commit private keys** to version control
- Use environment variables for sensitive data
- In production, restrict CORS origins in `node_api.py`
- Consider using a hardware wallet or secure key management

## Troubleshooting

### Port Already in Use

Change the port in `config.json` or use `-p` flag:
```bash
python main.py -p 8001
```

### Blockchain Connection Issues

- Verify RPC URL is correct
- Check network connectivity
- Ensure `PRIVATE_KEY` is set correctly
- Verify contract address is correct

### Permission Errors (Disk Stats)

On some systems, you may need elevated permissions. The node will fall back to default values if it can't read disk stats.

### API Not Accessible

- Check firewall settings
- Verify `host` in config (use `127.0.0.1` for local-only)
- Ensure port is not blocked

## Development

### Adding New Endpoints

Edit `node_api.py` to add new FastAPI endpoints.

### Modifying Node Behavior

Edit `node.py` to change node logic, storage calculations, or ping behavior.

### Extending Blockchain Integration

Edit `blockchain/registry.py` to add new contract interactions.

## Future Enhancements

- **File Operations**: Store/retrieve file chunks
- **Proof of Storage**: Actual file chunk verification
- **Metrics**: Prometheus/Graphite integration
- **Multi-chain Support**: Support for multiple blockchains
- **Advanced Pricing**: Dynamic pricing models

## License

MIT License - feel free to use and modify as needed.
