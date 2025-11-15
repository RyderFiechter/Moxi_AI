"""
FastAPI HTTP API for the storage node.
Exposes endpoints for monitoring node status and receiving pings.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
from node import Node

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
    
    node_instance.enable_storage_lending()
    return {
        "message": "Storage lending enabled",
        "storage_lending_enabled": node_instance.storage_lending_enabled
    }


@app.post("/storage-lending/disable")
async def disable_storage_lending():
    """Disable storage lending (opt-out)."""
    if node_instance is None:
        raise HTTPException(status_code=503, detail="Node not initialized")
    
    node_instance.disable_storage_lending()
    return {
        "message": "Storage lending disabled",
        "storage_lending_enabled": node_instance.storage_lending_enabled
    }


@app.post("/registry/register")
async def register_with_registry(request: RegisterRequest):
    """Register node with StorageRegistry contract."""
    if node_instance is None:
        raise HTTPException(status_code=503, detail="Node not initialized")
    
    if registry_client is None:
        raise HTTPException(
            status_code=503, 
            detail="Registry not configured. Set PRIVATE_KEY environment variable or add private_key to registry config in config.json. Restart the node after setting the private key."
        )
    
    try:
        from web3 import Web3
        
        # Convert ETH to wei
        price_per_gb_wei = int(Web3.to_wei(request.price_per_gb_eth, 'ether'))
        
        receipt = registry_client.register_provider(
            payment_wallet=node_instance.payment_wallet,
            storage_gb=request.storage_gb,
            price_per_gb_wei=price_per_gb_wei
        )
        
        # Update committed storage
        node_instance.set_committed_storage(request.storage_gb)
        
        return {
            "message": "Registered with StorageRegistry",
            "transaction_hash": receipt.transactionHash.hex(),
            "block_number": receipt.blockNumber,
            "committed_storage_gb": request.storage_gb
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")


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
        # Get current registered storage from registry
        provider_info = registry_client.get_provider_info(node_instance.wallet_address)
        current_registered = provider_info['storageGB'] if provider_info else 0
        
        # Get total free storage (not accounting for committed)
        # Use total storage - used storage to get free storage
        total_gb = node_instance.get_total_storage_gb()
        used_gb = node_instance.get_used_storage_gb()
        free_gb = total_gb - used_gb
        
        # New registered storage = total free storage
        new_storage_gb = int(free_gb)
        
        receipt = registry_client.update_storage(new_storage_gb)
        
        # Update committed storage to match what's registered
        node_instance.set_committed_storage(new_storage_gb)
        
        return {
            "message": "Storage updated in registry",
            "storage_gb": new_storage_gb,
            "committed_storage_gb": new_storage_gb,
            "transaction_hash": receipt.transactionHash.hex(),
            "block_number": receipt.blockNumber
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

