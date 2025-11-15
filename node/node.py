"""
Node class for a real storage provider in a decentralized storage network.
Uses real system stats (psutil) for storage and uptime.
"""

import json
import os
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import secrets
import psutil


class Node:
    """Represents a storage provider node in the network."""
    
    def __init__(
        self,
        wallet_address: Optional[str] = None,
        payment_wallet: Optional[str] = None,
        identity_file: str = "node_identity.json",
        ping_interval: int = 30,
        storage_lending_enabled: bool = False,
        storage_mount_path: str = "/",
        storage_backing_file: Optional[str] = None,
        storage_mapper_name: Optional[str] = None
    ):
        """
        Initialize a node with real system stats.
        
        Args:
            wallet_address: Optional wallet address. If None, will generate or load from file.
            payment_wallet: Optional payment wallet address (for receiving payments). Defaults to wallet_address.
            identity_file: Path to JSON file storing node identity.
            ping_interval: Seconds between uptime pings (default: 30s).
            storage_lending_enabled: Whether storage lending is enabled (opt-in).
            storage_mount_path: Filesystem path that should be tracked for committed space.
        """
        self.identity_file = identity_file
        self.ping_interval = ping_interval
        self.uptime_start = datetime.now()
        self.last_ping = None
        self.is_running = False
        self._ping_task: Optional[asyncio.Task] = None
        self.storage_lending_enabled = storage_lending_enabled
        self.storage_mount_path = storage_mount_path or "/"
        self.storage_backing_file = storage_backing_file
        self.storage_mapper_name = storage_mapper_name
        
        # Track committed storage (storage registered on-chain, no longer available)
        self.committed_storage_gb: float = 0.0
        
        # Track profits/rewards earned from storage lending
        self.total_profit_eth: float = 0.0
        self.profit_start_time: Optional[datetime] = None
        
        # Load or generate identity
        if wallet_address:
            self.wallet_address = wallet_address
        else:
            self.wallet_address = self._load_or_generate_identity()
        
        # Set payment wallet (defaults to wallet_address if not specified)
        self.payment_wallet = payment_wallet if payment_wallet else self.wallet_address
        
        # Save identity
        self._save_identity()
    
    def _generate_wallet_address(self) -> str:
        """Generate a random wallet address (hex string)."""
        return "0x" + secrets.token_hex(20)
    
    def _load_or_generate_identity(self) -> str:
        """Load wallet address from file or generate a new one."""
        if os.path.exists(self.identity_file):
            try:
                with open(self.identity_file, 'r') as f:
                    data = json.load(f)
                    wallet = data.get('wallet_address')
                    if wallet:
                        print(f"📂 Loaded existing identity: {wallet[:10]}...")
                        # Also load payment_wallet and storage_lending_enabled if present
                        if 'payment_wallet' in data:
                            self.payment_wallet = data['payment_wallet']
                        if 'storage_lending_enabled' in data:
                            self.storage_lending_enabled = data['storage_lending_enabled']
                        if 'storage_mount_path' in data and data['storage_mount_path']:
                            self.storage_mount_path = data['storage_mount_path']
                        if 'storage_backing_file' in data and data['storage_backing_file']:
                            self.storage_backing_file = data['storage_backing_file']
                        if 'storage_mapper_name' in data and data['storage_mapper_name']:
                            self.storage_mapper_name = data['storage_mapper_name']
                        if 'committed_storage_gb' in data:
                            self.committed_storage_gb = float(data['committed_storage_gb'])
                        if 'total_profit_eth' in data:
                            self.total_profit_eth = float(data['total_profit_eth'])
                        if 'profit_start_time' in data:
                            try:
                                self.profit_start_time = datetime.fromisoformat(data['profit_start_time'])
                            except (ValueError, TypeError):
                                self.profit_start_time = None
                        return wallet
            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️  Error loading identity file: {e}. Generating new identity.")
        
        wallet = self._generate_wallet_address()
        print(f"🆕 Generated new wallet address: {wallet[:10]}...")
        return wallet
    
    def _save_identity(self):
        """Save node identity to JSON file."""
        data = {
            'wallet_address': self.wallet_address,
            'payment_wallet': self.payment_wallet,
            'storage_lending_enabled': self.storage_lending_enabled,
            'committed_storage_gb': self.committed_storage_gb,
            'total_profit_eth': self.total_profit_eth,
            'profit_start_time': self.profit_start_time.isoformat() if self.profit_start_time else None,
            'created_at': self.uptime_start.isoformat(),
            'storage_mount_path': self.storage_mount_path,
            'storage_backing_file': self.storage_backing_file,
            'storage_mapper_name': self.storage_mapper_name
        }
        
        try:
            with open(self.identity_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"⚠️  Warning: Could not save identity file: {e}")
    
    def update_payment_wallet(self, new_payment_wallet: str):
        """Update payment wallet address."""
        self.payment_wallet = new_payment_wallet
        self._save_identity()
        print(f"✅ Payment wallet updated to: {new_payment_wallet}")
    
    def enable_storage_lending(self):
        """Enable storage lending (opt-in)."""
        self.storage_lending_enabled = True
        self._save_identity()
        print("✅ Storage lending enabled")
    
    def disable_storage_lending(self):
        """Disable storage lending (opt-out)."""
        self.storage_lending_enabled = False
        self._save_identity()
        print("✅ Storage lending disabled")
    
    def _get_disk_stats(self) -> tuple[float, float]:
        """
        Get real disk storage stats using psutil for the configured mount path.
        
        Returns:
            Tuple of (total_gb, free_gb) for the selected filesystem.
        """
        try:
            # Try configured filesystem first
            try:
                disk = psutil.disk_usage(self.storage_mount_path)
            except (PermissionError, OSError):
                # On Windows, try C: drive
                import platform
                if platform.system() == 'Windows':
                    disk = psutil.disk_usage('C:\\')
                else:
                    raise
            
            total_gb = disk.total / (1024 ** 3)
            free_gb = disk.free / (1024 ** 3)
            return total_gb, free_gb
        except Exception as e:
            # Fallback if psutil fails
            print(f"⚠️  Warning: Could not get disk stats for {self.storage_mount_path}: {e}")
            # Return default values
            return 1000.0, 500.0
    
    def get_available_storage_gb(self) -> float:
        """Get real available storage in GB from system (excluding committed storage)."""
        _, free_gb = self._get_disk_stats()
        # Available storage = free storage - committed storage
        available = max(0.0, free_gb - self.committed_storage_gb)
        return available
    
    def get_total_storage_gb(self) -> float:
        """Get real total storage in GB from system."""
        total_gb, _ = self._get_disk_stats()
        return total_gb
    
    def get_used_storage_gb(self) -> float:
        """Get real used storage in GB from system."""
        total_gb, free_gb = self._get_disk_stats()
        return total_gb - free_gb
    
    def get_uptime_seconds(self) -> int:
        """Get uptime in seconds since node started."""
        return int((datetime.now() - self.uptime_start).total_seconds())
    
    def format_uptime(self) -> str:
        """Format uptime as human-readable string (e.g., '2m 30s')."""
        seconds = self.get_uptime_seconds()
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs}s"
    
    def set_committed_storage(self, committed_gb: float):
        """Set the amount of storage committed to the registry."""
        self.committed_storage_gb = max(0.0, committed_gb)
        self._save_identity()
    
    def add_profit(self, profit_eth: float):
        """Add profit earned from storage lending."""
        self.total_profit_eth += profit_eth
        if self.profit_start_time is None:
            self.profit_start_time = datetime.now()
        self._save_identity()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current node status with real system stats."""
        total_gb, free_gb = self._get_disk_stats()
        uptime_seconds = self.get_uptime_seconds()
        available_gb = max(0.0, free_gb - self.committed_storage_gb)
        
        return {
            'wallet_address': self.wallet_address,
            'payment_wallet': self.payment_wallet,
            'storage_lending_enabled': self.storage_lending_enabled,
            'total_storage_gb': round(total_gb, 2),
            'used_storage_gb': round(total_gb - free_gb, 2),
            'available_storage_gb': round(available_gb, 2),
            'committed_storage_gb': round(self.committed_storage_gb, 2),
            'total_profit_eth': round(self.total_profit_eth, 6),
            'storage_mount_path': self.storage_mount_path,
            'uptime_seconds': uptime_seconds,
            'uptime_formatted': self.format_uptime(),
            'started_at': self.uptime_start.isoformat(),
            'last_ping': self.last_ping.isoformat() if self.last_ping else None,
            'is_online': self.is_running
        }
    
    async def _ping_loop(self, callback=None):
        """Periodically update last ping timestamp and log status."""
        while self.is_running:
            try:
                self.last_ping = datetime.now()
                
                # Log ping status
                uptime_str = self.format_uptime()
                free_gb = self.get_available_storage_gb()
                total_gb = self.get_total_storage_gb()
                print(f"[PING] Online for {uptime_str} | Free: {free_gb:.1f} GB / {total_gb:.1f} GB")
                
                # Call optional callback (e.g., for network registration)
                if callback:
                    callback(self)
                
                await asyncio.sleep(self.ping_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Error in ping loop: {e}")
                await asyncio.sleep(self.ping_interval)
    
    def ping(self):
        """Manually update ping timestamp (called by API)."""
        self.last_ping = datetime.now()
    
    async def start(self, callback=None):
        """Start the node and begin sending pings."""
        if self.is_running:
            print(f"⚠️  Node is already running")
            return
        
        self.is_running = True
        self.uptime_start = datetime.now()
        
        # Print startup info
        total_gb, free_gb = self._get_disk_stats()
        print(f"[NODE] Wallet: {self.wallet_address}")
        print(f"[NODE] Started at {self.uptime_start.strftime('%Y-%m-%d %H:%M')}")
        print(f"[NODE] Storage: {total_gb:.1f} GB total, {free_gb:.1f} GB free @ {self.storage_mount_path}")
        
        # Start ping loop
        self._ping_task = asyncio.create_task(self._ping_loop(callback))
    
    async def stop(self):
        """Stop the node."""
        self.is_running = False
        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
        print(f"🛑 Node {self.wallet_address[:10]}... stopped")
    
    def proof_of_storage(self, file_chunk_id: str) -> bool:
        """
        Placeholder for proof of storage verification.
        
        Args:
            file_chunk_id: Identifier for the file chunk to verify.
        
        Returns:
            bool: True if chunk is verified (placeholder always returns True).
        
        Note:
            This is a stub function for future implementation.
            In a real system, this would verify cryptographic proofs
            that the node still has the file chunk.
        """
        # TODO: Implement actual proof of storage verification
        # This would involve:
        # 1. Checking if chunk exists locally
        # 2. Generating/verifying cryptographic proof
        # 3. Returning verification result
        print(f"🔍 [{self.wallet_address[:10]}...] Proof of storage check for chunk {file_chunk_id[:8]}... (stub)")
        return True

