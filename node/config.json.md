# Node config.json template

This repo ships a `node/config.json` that contains operator-specific values (keys, RPC URLs, etc.). To avoid committing secrets we keep the real file ignored and provide this Markdown template to document the shape of the config. Copy the JSON below into `node/config.json` and replace each placeholder with your own values.

```jsonc
{
  "port": 8000,
  "host": "0.0.0.0",
  "ping_interval": 30,
  "identity_file": "node_identity.json",
  "wallet_address": "<PUBLIC_WALLET_ADDRESS>",
  "payment_wallet": "<PAYMENT_WALLET_OR_SAME_AS_ABOVE>",
  "storage_lending_enabled": false,
  "storage": {
    "mount_path": "/mnt/c/Users/Ryder/moxi-node",
    "mapper_name": "moxi-node",
    "backing_file": "/var/moxi-node/storage-node.img"
  },
  "registry": {
    "contract_address": "<STORAGE_REGISTRY_ADDRESS>",
    "rpc_url": "<RPC_URL>",
    "private_key": "<CONTROLLER_PRIVATE_KEY>",
    "chain_id": 421614,
    "auto_register": false,
    "auto_update_interval": 300,
    "price_per_gb_eth": "0.001"
  },
  "token": {
    "address": "<DEPIN_TOKEN_ADDRESS>",
    "rpc_url": "<RPC_URL_OR_EMPTY_TO_USE_REGISTRY_RPC>",
    "private_key": "<PRIVATE_KEY_OVERRIDE_OR_EMPTY>"
  }
}
```

> **Note:** Token payouts reuse the same `PRIVATE_KEY` and RPC URL if you leave the token fields blank. Override them when the payout signer lives on a different network or wallet.

Create the backing directory ahead of time (`sudo mkdir -p /var/moxi-node && sudo chown $USER /var/moxi-node`) so the node can place `storage-node.img` under `/var/moxi-node/`.
