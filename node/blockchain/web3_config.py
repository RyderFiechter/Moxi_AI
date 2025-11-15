"""
Web3 configuration and setup for blockchain interactions.
"""

import os
from web3 import Web3
from typing import Optional


def get_web3_instance(rpc_url: Optional[str] = None) -> Optional[Web3]:
    """
    Create and return a Web3 instance.
    
    Args:
        rpc_url: Optional RPC URL. If None, tries to get from environment.
    
    Returns:
        Web3 instance or None if no RPC URL available.
    """
    if not rpc_url:
        # Try to get from environment variables
        rpc_url = os.getenv("ARBITRUM_SEPOLIA_RPC_URL") or os.getenv("RPC_URL")
    
    if not rpc_url:
        return None
    
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if w3.is_connected():
            return w3
        else:
            print("⚠️  Warning: Could not connect to RPC endpoint")
            return None
    except Exception as e:
        print(f"⚠️  Warning: Error connecting to blockchain: {e}")
        return None


def get_chain_id(w3: Web3) -> Optional[int]:
    """Get chain ID from Web3 instance."""
    try:
        return w3.eth.chain_id
    except Exception:
        return None

