"""
StorageRegistry contract interaction.
Handles registration, updates, and queries to the StorageRegistry.
"""

import json
from typing import Optional, Dict, Any
from web3 import Web3
from web3.types import TxReceipt
from .web3_config import get_web3_instance


# StorageRegistry ABI (minimal for interaction)
STORAGE_REGISTRY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "paymentWallet", "type": "address"},
            {"internalType": "uint256", "name": "storageGB", "type": "uint256"},
            {"internalType": "uint256", "name": "pricePerGB", "type": "uint256"}
        ],
        "name": "registerProvider",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "storageGB", "type": "uint256"}],
        "name": "updateStorage",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "pricePerGB", "type": "uint256"}],
        "name": "updatePrice",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "newPaymentWallet", "type": "address"}],
        "name": "updatePaymentWallet",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "activate",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "deactivate",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "provider", "type": "address"}],
        "name": "getProviderInfo",
        "outputs": [
            {
                "components": [
                    {"internalType": "address", "name": "providerAddress", "type": "address"},
                    {"internalType": "address", "name": "paymentWallet", "type": "address"},
                    {"internalType": "uint256", "name": "storageGB", "type": "uint256"},
                    {"internalType": "uint256", "name": "pricePerGB", "type": "uint256"},
                    {"internalType": "bool", "name": "isActive", "type": "bool"},
                    {"internalType": "uint256", "name": "registeredAt", "type": "uint256"},
                    {"internalType": "uint256", "name": "lastUpdate", "type": "uint256"}
                ],
                "internalType": "struct StorageRegistry.Provider",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "provider", "type": "address"}],
        "name": "isRegistered",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]


class StorageRegistryClient:
    """Client for interacting with StorageRegistry contract."""
    
    def __init__(self, contract_address: str, rpc_url: Optional[str] = None, private_key: Optional[str] = None):
        """
        Initialize StorageRegistry client.
        
        Args:
            contract_address: Address of StorageRegistry contract
            rpc_url: RPC URL for blockchain connection
            private_key: Private key for signing transactions (optional for read-only)
        """
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.w3 = get_web3_instance(rpc_url)
        
        if not self.w3:
            raise ValueError("Could not connect to blockchain. Check RPC URL.")
        
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=STORAGE_REGISTRY_ABI
        )
        
        self.private_key = private_key
        if private_key:
            # Remove 0x prefix if present
            if private_key.startswith("0x"):
                private_key = private_key[2:]
            self.account = self.w3.eth.account.from_key(private_key)
            self.account_address = self.account.address
        else:
            self.account = None
            self.account_address = None
    
    def _send_transaction(self, function_call) -> TxReceipt:
        """Send a transaction and wait for receipt."""
        if not self.account:
            raise ValueError("Private key required for transactions")
        
        # Build transaction
        transaction = function_call.build_transaction({
            'from': self.account_address,
            'nonce': self.w3.eth.get_transaction_count(self.account_address),
            'gas': 500000,  # Adjust as needed
            'gasPrice': self.w3.eth.gas_price
        })
        
        # Sign transaction - use account object directly
        signed_txn = self.account.sign_transaction(transaction)
        
        # web3.py 6.x exposes both camelCase and snake_case depending on release
        raw_tx = getattr(signed_txn, "raw_transaction", None) or getattr(
            signed_txn, "rawTransaction", None
        )
        if raw_tx is None:
            raise ValueError("Signed transaction missing raw transaction bytes")
        
        tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
        
        # Wait for receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt
    
    def register_provider(
        self,
        payment_wallet: str,
        storage_gb: int,
        price_per_gb_wei: int
    ) -> TxReceipt:
        """
        Register as a storage provider.
        
        Args:
            payment_wallet: Address to receive payments
            storage_gb: Available storage in GB
            price_per_gb_wei: Price per GB per month in wei
        
        Returns:
            Transaction receipt
        """
        payment_wallet = Web3.to_checksum_address(payment_wallet)
        function_call = self.contract.functions.registerProvider(
            payment_wallet,
            storage_gb,
            price_per_gb_wei
        )
        return self._send_transaction(function_call)
    
    def update_storage(self, storage_gb: int) -> TxReceipt:
        """Update available storage."""
        function_call = self.contract.functions.updateStorage(storage_gb)
        return self._send_transaction(function_call)
    
    def update_price(self, price_per_gb_wei: int) -> TxReceipt:
        """Update price per GB."""
        function_call = self.contract.functions.updatePrice(price_per_gb_wei)
        return self._send_transaction(function_call)
    
    def update_payment_wallet(self, new_payment_wallet: str) -> TxReceipt:
        """Update payment wallet address."""
        new_payment_wallet = Web3.to_checksum_address(new_payment_wallet)
        function_call = self.contract.functions.updatePaymentWallet(new_payment_wallet)
        return self._send_transaction(function_call)
    
    def activate(self) -> TxReceipt:
        """Activate provider (opt-in to storage lending)."""
        function_call = self.contract.functions.activate()
        return self._send_transaction(function_call)
    
    def deactivate(self) -> TxReceipt:
        """Deactivate provider (opt-out of storage lending)."""
        function_call = self.contract.functions.deactivate()
        return self._send_transaction(function_call)
    
    def get_provider_info(self, provider_address: str) -> Optional[Dict[str, Any]]:
        """
        Get provider information (read-only).
        
        Args:
            provider_address: Address of the provider
        
        Returns:
            Provider info dict or None if not registered
        """
        try:
            provider_address = Web3.to_checksum_address(provider_address)
            is_registered = self.contract.functions.isRegistered(provider_address).call()
            
            if not is_registered:
                return None
            
            info = self.contract.functions.getProviderInfo(provider_address).call()
            
            return {
                'providerAddress': info[0],
                'paymentWallet': info[1],
                'storageGB': info[2],
                'pricePerGB': info[3],
                'isActive': info[4],
                'registeredAt': info[5],
                'lastUpdate': info[6]
            }
        except Exception as e:
            print(f"Error getting provider info: {e}")
            return None
    
    def is_registered(self, provider_address: str) -> bool:
        """Check if address is registered."""
        try:
            provider_address = Web3.to_checksum_address(provider_address)
            return self.contract.functions.isRegistered(provider_address).call()
        except Exception:
            return False

