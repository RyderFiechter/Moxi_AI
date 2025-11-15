"""
Main entry point for the real storage node.
Launches FastAPI server and starts the node with real system stats.
"""

import asyncio
import argparse
import json
import os
import uvicorn
from node import Node
from node_api import (
    app,
    set_node,
    set_registry_client,
    set_storage_volume_manager,
    set_token_client,
)
from storage_volume import StorageVolumeManager
from blockchain.registry import StorageRegistryClient, WEB3_AVAILABLE
from blockchain.token import ERC20TokenClient


def load_config(config_file: str = "config.json") -> dict:
    """Load configuration from JSON file."""
    default_config = {
        "port": 8000,
        "host": "0.0.0.0",
        "ping_interval": 30,
        "identity_file": "node_identity.json",
        "wallet_address": None,
        "payment_wallet": None,
        "storage_lending_enabled": False,
        "storage": {
            "mount_path": "/",
            "mapper_name": "moxi-node",
            "backing_file": ""
        },
        "registry": {
            "contract_address": "",
            "rpc_url": "",
            "chain_id": 421614,
            "auto_register": False,
            "auto_update_interval": 300,
            "price_per_gb_eth": "0.001"
        },
        "token": {
            "address": "",
            "rpc_url": "",
            "private_key": ""
        }
    }
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            # Merge with defaults
            default_config.update(config)
            return default_config
    except FileNotFoundError:
        # Create default config file
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"📝 Created default config file: {config_file}")
        return default_config
    except json.JSONDecodeError as e:
        print(f"⚠️  Error reading config file: {e}. Using defaults.")
        return default_config


async def run_node(config: dict):
    """
    Run the storage node with FastAPI server.
    
    Args:
        config: Configuration dictionary.
    """
    # Create node with wallet from config if provided
    wallet_address = config.get("wallet_address")
    if wallet_address:
        # Convert None string to actual None
        if wallet_address == "None" or wallet_address == "":
            wallet_address = None
    
    payment_wallet = config.get("payment_wallet")
    if payment_wallet == "None" or payment_wallet == "":
        payment_wallet = None
    
    storage_lending_enabled = config.get("storage_lending_enabled", False)
    storage_config = config.get("storage", {})
    storage_mount_path = storage_config.get("mount_path") or "/"
    if storage_mount_path and not os.path.exists(storage_mount_path):
        print(f"⚠️  Storage mount path '{storage_mount_path}' does not exist yet. Falling back to '/'.")
        storage_mount_path = "/"
    storage_backing_file = storage_config.get("backing_file")
    storage_mapper_name = storage_config.get("mapper_name")
    
    node = Node(
        wallet_address=wallet_address,
        payment_wallet=payment_wallet,
        identity_file=config.get("identity_file", "node_identity.json"),
        ping_interval=config.get("ping_interval", 30),
        storage_lending_enabled=storage_lending_enabled,
        storage_mount_path=storage_mount_path,
        storage_backing_file=storage_backing_file,
        storage_mapper_name=storage_mapper_name
    )
    
    # Set node in API
    set_node(node)

    # Attach storage manager for encrypted volume handling
    storage_manager = StorageVolumeManager(
        mount_path=storage_mount_path,
        backing_file=storage_backing_file,
        mapper_name=storage_mapper_name,
    )
    set_storage_volume_manager(storage_manager)
    
    # Initialize blockchain/registry if configured
    registry_config = config.get("registry", {})
    registry_client = None
    token_client = None
    
    if not WEB3_AVAILABLE:
        print("⚠️  Web3.py not installed. Blockchain registry features are disabled.")
        print("   Install optional deps via: pip install -r node/requirements-web3.txt")
    elif registry_config.get("contract_address") and registry_config.get("rpc_url"):
        try:
            # Get private key from environment or config
            private_key = os.getenv("PRIVATE_KEY") or registry_config.get("private_key")
            
            if private_key:
                registry_client = StorageRegistryClient(
                    contract_address=registry_config["contract_address"],
                    rpc_url=registry_config["rpc_url"],
                    private_key=private_key
                )
                set_registry_client(registry_client)
                print("✅ Blockchain registry client initialized")
                print(f"   Contract: {registry_config['contract_address']}")
                print(f"   Network: Arbitrum Sepolia (Chain ID: {registry_config.get('chain_id', 421614)})")
                
                # Auto-register if enabled
                if registry_config.get("auto_register", False):
                    try:
                        if not registry_client.is_registered(node.wallet_address):
                            storage_gb = int(node.get_available_storage_gb())
                            price_per_gb_eth = float(registry_config.get("price_per_gb_eth", "0.001"))
                            from web3 import Web3
                            price_per_gb_wei = int(Web3.to_wei(price_per_gb_eth, 'ether'))
                            
                            print(f"📝 Auto-registering with StorageRegistry...")
                            receipt = registry_client.register_provider(
                                payment_wallet=node.payment_wallet,
                                storage_gb=storage_gb,
                                price_per_gb_wei=price_per_gb_wei
                            )
                            print(f"✅ Registered! TX: {receipt.transactionHash.hex()}")
                    except Exception as e:
                        print(f"⚠️  Auto-registration failed: {e}")
                
                # Set up auto-update task if enabled
                if registry_config.get("auto_update_interval", 0) > 0:
                    asyncio.create_task(auto_update_storage(node, registry_client, registry_config))
            else:
                print("⚠️  Registry configured but no private key found.")
                print("   To enable blockchain features:")
                print("   1. Set PRIVATE_KEY environment variable: $env:PRIVATE_KEY='your_key'")
                print("   2. Or add 'private_key' to registry config in config.json")
                print("   3. Restart the node after setting the private key")
        except ImportError as e:
            print(f"⚠️  Registry disabled: {e}")
        except Exception as e:
            print(f"⚠️  Could not initialize registry client: {e}")
            print("   Node will run without blockchain features.")
            print("   Check that PRIVATE_KEY is set correctly and the RPC URL is valid.")

    # Initialize ERC-20 payout client
    token_config = config.get("token") or {}
    token_address = (
        token_config.get("address")
        or config.get("token_address")
        or os.getenv("TOKEN_ADDRESS")
    )
    token_rpc_url = token_config.get("rpc_url") or registry_config.get("rpc_url")
    token_private_key = (
        os.getenv("PRIVATE_KEY")
        or token_config.get("private_key")
        or registry_config.get("private_key")
    )

    if token_address:
        if not WEB3_AVAILABLE:
            print("⚠️  Token payouts require web3.py. Install via `pip install -r node/requirements-web3.txt`.")
        elif not token_rpc_url:
            print("⚠️  Token payouts configured without an RPC URL.")
        elif not token_private_key:
            print("⚠️  Token payouts require a PRIVATE_KEY in the environment or token config.")
        else:
            try:
                token_client = ERC20TokenClient(
                    token_address,
                    token_rpc_url,
                    token_private_key,
                )
                set_token_client(token_client)
                print("✅ Token payout client initialized")
                print(f"   Token: {token_client.symbol} ({token_client.contract_address})")
                print(f"   Signer: {token_client.account_address}")
            except Exception as e:
                print(f"⚠️  Could not initialize token client: {e}")
    
    # Start node (this starts the ping loop)
    await node.start()
    
    # Start FastAPI server
    port = config.get("port", 8000)
    host = config.get("host", "0.0.0.0")
    
    print(f"\n🌐 API Server starting on http://{host}:{port}")
    print(f"📡 Endpoints:")
    print(f"   GET  http://{host}:{port}/status - Node status")
    print(f"   GET  http://{host}:{port}/config - Get configuration")
    print(f"   PUT  http://{host}:{port}/payment-wallet - Update payment wallet")
    print(f"   POST http://{host}:{port}/storage-lending/enable - Enable storage lending")
    print(f"   POST http://{host}:{port}/storage-lending/disable - Disable storage lending")
    print(f"   POST http://{host}:{port}/payout - Send pending MOXI payout")
    if registry_client:
        print(f"   POST http://{host}:{port}/registry/register - Register with registry")
        print(f"   POST http://{host}:{port}/registry/update - Update storage")
        print(f"   GET  http://{host}:{port}/registry/status - Registry status")
    print(f"   GET  http://{host}:{port}/docs - API documentation")
    print(f"   🌐 Web UI: http://{host}:{port}/ui\n")
    
    # Run server in background
    config_uvicorn = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config_uvicorn)
    
    # Run server and node concurrently
    try:
        await asyncio.gather(
            server.serve(),
            asyncio.sleep(float('inf'))  # Keep node running
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down node...")
        await node.stop()
        print("✅ Node stopped. Goodbye!")


def main():
    """Parse command line arguments and run node."""
    parser = argparse.ArgumentParser(
        description="Run a real storage provider node with HTTP API"
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="config.json",
        help="Path to config file (default: config.json)"
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        help="API server port (overrides config)"
    )
    parser.add_argument(
        "--ping-interval",
        type=int,
        help="Seconds between pings (overrides config)"
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Override with command line args if provided
    if args.port:
        config["port"] = args.port
    if args.ping_interval:
        config["ping_interval"] = args.ping_interval
    
    # Validate
    if config["port"] < 1 or config["port"] > 65535:
        print("❌ Error: Port must be between 1 and 65535")
        return
    
    if config["ping_interval"] < 1:
        print("❌ Error: Ping interval must be at least 1 second")
        return
    
    # Run node
    try:
        asyncio.run(run_node(config))
    except KeyboardInterrupt:
        print("\n👋 Node interrupted by user")


async def auto_update_storage(node: Node, registry_client, registry_config: dict):
    """Background task to auto-update storage in registry."""
    interval = registry_config.get("auto_update_interval", 300)
    
    while node.is_running:
        try:
            await asyncio.sleep(interval)
            if node.storage_lending_enabled:
                storage_gb = int(node.get_available_storage_gb())
                receipt = registry_client.update_storage(storage_gb)
                print(f"📤 Auto-updated storage in registry: {storage_gb} GB - TX: {receipt.transactionHash.hex()}")
        except Exception as e:
            print(f"⚠️  Auto-update error: {e}")
            await asyncio.sleep(60)  # Wait before retrying


if __name__ == "__main__":
    main()
