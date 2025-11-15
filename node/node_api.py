"""
FastAPI HTTP API for the storage node.
Exposes endpoints for monitoring node status and receiving pings.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
from decimal import Decimal
import os
from node import Node
from storage_volume import StorageVolumeManager

# Create FastAPI app
app = FastAPI(
    title="Storage Node API",
    description="HTTP API for monitoring storage provider node status",
    version="2.0.0"
)

# Enable CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global node instance (will be set by main.py)
node_instance: Node = None
registry_client = None  # Will be set by main.py if blockchain is configured
storage_volume_manager: Optional[StorageVolumeManager] = None
token_client = None  # Set by main.py when payouts are fully configured

# Request models
class PaymentWalletUpdate(BaseModel):
    payment_wallet: str

class RegistryConfig(BaseModel):
    contract_address: str
    rpc_url: str
    private_key: Optional[str] = None

class RegisterRequest(BaseModel):
    storage_gb: int
    price_per_gb_eth: float


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Storage Node API",
        "version": "2.0.0",
        "endpoints": {
            "/status": "GET - Get node status",
            "/ping": "POST - Update ping timestamp",
            "/config": "GET/PUT - Get/update configuration",
            "/payment-wallet": "PUT - Update payment wallet",
            "/storage-lending": "POST - Enable/disable storage lending",
            "/payout": "POST - Send pending MOXI payout",
            "/registry/register": "POST - Register with StorageRegistry",
            "/registry/update": "POST - Update storage in registry",
            "/registry/status": "GET - Get registry status"
        }
    }


@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    Get current node status.
    
    Returns:
        JSON with node information including:
        - wallet_address
        - storage stats (total, used, available, committed in GB)
        - registry info (registered storage from blockchain)
        - profit information
        - uptime information
        - last ping timestamp
    """
    if node_instance is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Node not initialized"}
        )
    
    status = node_instance.get_status()
    if storage_volume_manager:
        try:
            status['storage_volume'] = storage_volume_manager.describe()
        except Exception as e:
            status['storage_volume'] = {'error': str(e)}
    
    # Add registry information if available
    if registry_client:
        try:
            is_registered = registry_client.is_registered(node_instance.wallet_address)
            if is_registered:
                provider_info = registry_client.get_provider_info(node_instance.wallet_address)
                if provider_info:
                    status['registry'] = {
                        'registered': True,
                        'registered_storage_gb': provider_info['storageGB'],
                        'price_per_gb_eth': float(provider_info['pricePerGB']) / 1e18,
                        'is_active': provider_info['isActive'],
                        'registered_at': provider_info['registeredAt'],
                        'last_update': provider_info['lastUpdate']
                    }
                else:
                    status['registry'] = {'registered': False}
            else:
                status['registry'] = {'registered': False}
        except Exception as e:
            status['registry'] = {'registered': False, 'error': str(e)}
    else:
        status['registry'] = {'registered': False, 'message': 'Registry not configured'}
    
    return status


@app.post("/ping")
async def ping():
    """
    Update the node's last ping timestamp.
    
    This endpoint can be called by external services to verify
    the node is responsive and update its last ping time.
    """
    if node_instance is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Node not initialized"}
        )
    
    node_instance.ping()
    return {
        "message": "Ping received",
        "timestamp": node_instance.last_ping.isoformat() if node_instance.last_ping else None
    }


@app.get("/config")
async def get_config():
    """Get current node configuration."""
    if node_instance is None:
        raise HTTPException(status_code=503, detail="Node not initialized")
    
    return {
        "wallet_address": node_instance.wallet_address,
        "payment_wallet": node_instance.payment_wallet,
        "storage_lending_enabled": node_instance.storage_lending_enabled,
        "ping_interval": node_instance.ping_interval
    }


@app.put("/payment-wallet")
async def update_payment_wallet(request: PaymentWalletUpdate):
    """Update payment wallet address."""
    if node_instance is None:
        raise HTTPException(status_code=503, detail="Node not initialized")
    
    try:
        node_instance.update_payment_wallet(request.payment_wallet)
        return {
            "message": "Payment wallet updated",
            "payment_wallet": node_instance.payment_wallet
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/storage-lending/enable")
async def enable_storage_lending():
    """Enable storage lending (opt-in)."""
    if node_instance is None:
        raise HTTPException(status_code=503, detail="Node not initialized")
    
    volume_info = None
    if storage_volume_manager:
        try:
            volume_info = storage_volume_manager.initialize_volume()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize encrypted storage: {e}"
            )
    
    node_instance.enable_storage_lending()
    return {
        "message": volume_info["message"] if volume_info else "Storage lending enabled",
        "storage_lending_enabled": node_instance.storage_lending_enabled,
        "encrypted_volume": volume_info
    }


@app.post("/storage-lending/disable")
async def disable_storage_lending():
    """Disable storage lending (opt-out)."""
    if node_instance is None:
        raise HTTPException(status_code=503, detail="Node not initialized")
    
    release_info = None
    if storage_volume_manager:
        try:
            release_info = storage_volume_manager.release_storage()
            node_instance.set_committed_storage(0)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to release encrypted storage: {e}"
            )
    
    node_instance.disable_storage_lending()
    return {
        "message": release_info["message"] if release_info else "Storage lending disabled",
        "storage_lending_enabled": node_instance.storage_lending_enabled,
        "encrypted_volume": release_info
    }


@app.post("/payout")
async def send_payout():
    """Send accumulated MOXI earnings to the configured wallet."""
    if node_instance is None:
        raise HTTPException(status_code=503, detail="Node not initialized")
    if token_client is None:
        raise HTTPException(
            status_code=503,
            detail="Token payout client not configured. Set token.address, RPC URL, and private key in config.json.",
        )

    payout_preview = node_instance.claim_earnings(commit=False)
    amount = payout_preview.get("amount_moxi", 0.0)
    payout_wallet = payout_preview.get("payout_wallet") or node_instance.wallet_address

    if amount <= 0:
        raise HTTPException(status_code=400, detail="No earnings available for payout")

    try:
        transfer_result = token_client.transfer_tokens(payout_wallet, Decimal(str(amount)))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Payout failed: {exc}") from exc

    payout_record = node_instance.record_payout(float(transfer_result.amount_tokens))
    pending_after = node_instance.get_pending_earnings_moxi()

    amount_display = format(transfer_result.amount_tokens.normalize(), "f")
    status_label = "confirmed" if transfer_result.receipt.status == 1 else "failed"
    return {
        "message": f"Sent {amount_display} {token_client.symbol} to {payout_wallet}",
        "amount_moxi": payout_record.get("amount_moxi", float(transfer_result.amount_tokens)),
        "payout_wallet": payout_wallet,
        "last_payout_at": payout_record.get("payout_at"),
        "transaction": {
            "hash": transfer_result.tx_hash,
            "status": status_label,
            "block_number": transfer_result.receipt.blockNumber,
            "gas_used": int(transfer_result.receipt.gasUsed),
        },
        "token": {
            "symbol": token_client.symbol,
            "decimals": token_client.decimals,
            "contract": token_client.contract_address,
        },
        "pending_earnings_moxi": pending_after,
    }


@app.post("/registry/register")
async def register_with_registry(request: RegisterRequest):
    """Register node with StorageRegistry contract."""
    if node_instance is None:
        raise HTTPException(status_code=503, detail="Node not initialized")
    
    storage_gb = int(request.storage_gb)
    if storage_gb <= 0:
        raise HTTPException(status_code=400, detail="Storage amount must be positive")
    if request.price_per_gb_eth <= 0:
        raise HTTPException(status_code=400, detail="Price per GB must be positive")

    previous_committed = getattr(node_instance, "committed_storage_gb", 0.0)

    volume_info = None
    if storage_volume_manager:
        try:
            volume_info = storage_volume_manager.reserve_storage(storage_gb)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to resize encrypted storage file: {e}"
            )
    
    try:
        node_instance.set_committed_storage(storage_gb)
    except Exception as e:
        if storage_volume_manager:
            storage_volume_manager.reserve_storage(previous_committed)
        raise HTTPException(status_code=500, detail=f"Failed to record commitment: {e}")

    registry_result: Dict[str, Any]
    if registry_client:
        try:
            from web3 import Web3
            price_per_gb_wei = int(Web3.to_wei(request.price_per_gb_eth, 'ether'))
            receipt = registry_client.register_provider(
                payment_wallet=node_instance.payment_wallet,
                storage_gb=storage_gb,
                price_per_gb_wei=price_per_gb_wei
            )
            registry_result = {
                "transaction_hash": receipt.transactionHash.hex(),
                "block_number": receipt.blockNumber,
                "status": "submitted"
            }
        except Exception as e:
            if storage_volume_manager:
                storage_volume_manager.reserve_storage(previous_committed)
            node_instance.set_committed_storage(previous_committed)
            raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")
    else:
        registry_result = {
            "status": "skipped",
            "message": "Registry not configured. Commitment recorded locally."
        }

    node_instance.enable_storage_lending()
    payout_wallet = node_instance.payment_wallet or node_instance.wallet_address
    return {
        "message": f"Reserved {storage_gb} GB and started payouts to {payout_wallet}.",
        "committed_storage_gb": node_instance.committed_storage_gb,
        "payment_wallet": payout_wallet,
        "encrypted_volume": volume_info,
        "registry": registry_result
    }


@app.post("/registry/update")
async def update_registry_storage():
    """Update storage availability in registry."""
    if node_instance is None:
        raise HTTPException(status_code=503, detail="Node not initialized")
    
    if registry_client is None:
        raise HTTPException(
            status_code=503, 
            detail="Registry not configured. Set PRIVATE_KEY environment variable or add private_key to registry config in config.json. Restart the node after setting the private key."
        )
    
    try:
        # Get total free storage (not accounting for committed)
        # Use total storage - used storage to get free storage
        total_gb = node_instance.get_total_storage_gb()
        used_gb = node_instance.get_used_storage_gb()
        free_gb = total_gb - used_gb
        
        # New registered storage = total free storage
        new_storage_gb = int(free_gb)

        volume_info = None
        if storage_volume_manager:
            try:
                volume_info = storage_volume_manager.reserve_storage(new_storage_gb)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to resize encrypted storage: {e}"
                )
        
        receipt = registry_client.update_storage(new_storage_gb)
        
        # Update committed storage to match what's registered
        node_instance.set_committed_storage(new_storage_gb)
        
        return {
            "message": "Storage updated in registry",
            "storage_gb": new_storage_gb,
            "committed_storage_gb": new_storage_gb,
            "transaction_hash": receipt.transactionHash.hex(),
            "block_number": receipt.blockNumber,
            "encrypted_volume": volume_info
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Update failed: {str(e)}")


@app.get("/registry/status")
async def get_registry_status():
    """Get registry status for this node."""
    if node_instance is None:
        raise HTTPException(status_code=503, detail="Node not initialized")
    
    if registry_client is None:
        return {
            "registered": False,
            "message": "Registry not configured"
        }
    
    try:
        is_registered = registry_client.is_registered(node_instance.wallet_address)
        
        if not is_registered:
            return {
                "registered": False,
                "wallet_address": node_instance.wallet_address
            }
        
        provider_info = registry_client.get_provider_info(node_instance.wallet_address)
        
        return {
            "registered": True,
            "provider_info": provider_info
        }
    except Exception as e:
        return {
            "registered": False,
            "error": str(e)
        }


@app.post("/registry/activate")
async def activate_in_registry():
    """Activate provider in registry (opt-in to storage lending)."""
    if node_instance is None:
        raise HTTPException(status_code=503, detail="Node not initialized")
    
    if registry_client is None:
        raise HTTPException(
            status_code=503, 
            detail="Registry not configured. Set PRIVATE_KEY environment variable or add private_key to registry config in config.json. Restart the node after setting the private key."
        )
    
    try:
        receipt = registry_client.activate()
        node_instance.enable_storage_lending()
        
        return {
            "message": "Activated in registry",
            "transaction_hash": receipt.transactionHash.hex()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Activation failed: {str(e)}")


@app.post("/registry/deactivate")
async def deactivate_in_registry():
    """Deactivate provider in registry (opt-out of storage lending)."""
    if node_instance is None:
        raise HTTPException(status_code=503, detail="Node not initialized")
    
    if registry_client is None:
        raise HTTPException(
            status_code=503, 
            detail="Registry not configured. Set PRIVATE_KEY environment variable or add private_key to registry config in config.json. Restart the node after setting the private key."
        )
    
    try:
        receipt = registry_client.deactivate()
        node_instance.disable_storage_lending()
        
        return {
            "message": "Deactivated in registry",
            "transaction_hash": receipt.transactionHash.hex()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Deactivation failed: {str(e)}")


@app.put("/registry/payment-wallet")
async def update_registry_payment_wallet(request: PaymentWalletUpdate):
    """Update payment wallet in registry."""
    if node_instance is None:
        raise HTTPException(status_code=503, detail="Node not initialized")
    
    if registry_client is None:
        raise HTTPException(
            status_code=503, 
            detail="Registry not configured. Set PRIVATE_KEY environment variable or add private_key to registry config in config.json. Restart the node after setting the private key."
        )
    
    try:
        # Update in node first
        node_instance.update_payment_wallet(request.payment_wallet)
        
        # Update in registry
        receipt = registry_client.update_payment_wallet(request.payment_wallet)
        
        return {
            "message": "Payment wallet updated in registry",
            "payment_wallet": request.payment_wallet,
            "transaction_hash": receipt.transactionHash.hex()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Update failed: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    if node_instance is None:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "reason": "Node not initialized"}
        )
    
    return {
        "status": "healthy" if node_instance.is_running else "stopped",
        "wallet_address": node_instance.wallet_address if node_instance else None
    }


# Serve web UI
ui_dir = os.path.join(os.path.dirname(__file__), "ui")

@app.get("/ui")
async def serve_ui():
    """Serve the web UI."""
    ui_file = os.path.join(ui_dir, "index.html")
    if os.path.exists(ui_file):
        return FileResponse(ui_file)
    else:
        raise HTTPException(status_code=404, detail="UI not found")


@app.get("/ui/{filename}")
async def serve_ui_file(filename: str):
    """Serve UI static files."""
    file_path = os.path.join(ui_dir, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")


def set_node(node: Node):
    """Set the global node instance (called by main.py)."""
    global node_instance
    node_instance = node


def set_registry_client(client):
    """Set the global registry client (called by main.py)."""
    global registry_client
    registry_client = client


def set_token_client(client):
    """Configure the ERC-20 payout client (called by main.py)."""
    global token_client
    token_client = client


def set_storage_volume_manager(manager: StorageVolumeManager):
    """Set the storage volume manager for encrypted file operations."""
    global storage_volume_manager
    storage_volume_manager = manager

