"""
Node class for a real storage provider in a decentralized storage network.
Uses real system stats (psutil) for storage and uptime.
"""

import json
import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import secrets
import psutil
try:
    from .storage_volume import DEFAULT_BACKING_DIR, DEFAULT_BACKING_FILENAME
except ImportError:  # pragma: no cover
    from storage_volume import DEFAULT_BACKING_DIR, DEFAULT_BACKING_FILENAME

MOXI_PER_HOUR_PER_10_GB = 1.0  # Base accrual rate
MOXI_PER_SECOND_PER_10_GB = MOXI_PER_HOUR_PER_10_GB / 3600.0
MOXI_PER_SECOND_PER_GB = MOXI_PER_SECOND_PER_10_GB / 10.0


class Node:
    """Represents a storage provider node in the network."""
    
    def __init__(
        self,
        wallet_address: Optional[str] = None,
        payment_wallet: Optional[str] = None,
        identity_file: str = "node_identity.json",
        ping_interval: int = 30,
        storage_lending_enabled: bool = False,
        storage_mount_path: Optional[str] = None,
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
        self._storage_mount_path_provided = storage_mount_path is not None
        self._storage_backing_file_provided = storage_backing_file is not None
        self._storage_mapper_provided = storage_mapper_name is not None
        self.storage_mount_path = storage_mount_path or "/"
        self.storage_backing_file = storage_backing_file
        self.storage_mapper_name = storage_mapper_name
        
        # Track committed storage (storage registered on-chain, no longer available)
        self.committed_storage_gb: float = 0.0
        
        # Track MOXI payouts
        self.total_earned_moxi: float = 0.0
        self.earnings_balance_moxi: float = 0.0
        self.earnings_start_time: Optional[datetime] = None
        self.last_earnings_update: Optional[datetime] = None
        self.last_payout_at: Optional[datetime] = None
        
        # Load or generate identity
        if wallet_address:
            self.wallet_address = wallet_address
        else:
            self.wallet_address = self._load_or_generate_identity()
        
        # Set payment wallet (defaults to wallet_address if not specified)
        self.payment_wallet = payment_wallet if payment_wallet else self.wallet_address

        if self.last_earnings_update is None:
            self.last_earnings_update = datetime.now()
        
        self._ensure_storage_defaults()

        # Save identity
        self._save_identity()
    
    def _ensure_storage_defaults(self) -> None:
        """Fill in default storage values when absent."""
        if not self.storage_backing_file:
            if os.name != "nt":
                default_path = (DEFAULT_BACKING_DIR / DEFAULT_BACKING_FILENAME).expanduser()
            else:
                default_path = Path(self.storage_mount_path).expanduser() / ".moxi_encrypted.bin"
            self.storage_backing_file = str(default_path)
        if not self.storage_mapper_name:
            self.storage_mapper_name = "moxi-node"

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
                        if (
                            not self._storage_mount_path_provided
                            and 'storage_mount_path' in data
                            and data['storage_mount_path']
                        ):
                            self.storage_mount_path = data['storage_mount_path']
                        if (
                            not self._storage_backing_file_provided
                            and 'storage_backing_file' in data
                            and data['storage_backing_file']
                        ):
                            self.storage_backing_file = data['storage_backing_file']
                        if (
                            not self._storage_mapper_provided
                            and 'storage_mapper_name' in data
                            and data['storage_mapper_name']
                        ):
                            self.storage_mapper_name = data['storage_mapper_name']
                        if 'committed_storage_gb' in data:
                            self.committed_storage_gb = float(data['committed_storage_gb'])
                        if 'total_earned_moxi' in data:
                            self.total_earned_moxi = float(data['total_earned_moxi'])
                        elif 'total_profit_eth' in data:
                            # Backwards compatibility with ETH payout field
                            self.total_earned_moxi = float(data['total_profit_eth'])
                        if 'earnings_balance_moxi' in data:
                            self.earnings_balance_moxi = float(data['earnings_balance_moxi'])
                        elif 'total_profit_eth' in data and self.earnings_balance_moxi == 0.0:
                            self.earnings_balance_moxi = float(data['total_profit_eth'])
                        earnings_start_raw = data.get('earnings_start_time') or data.get('profit_start_time')
                        if earnings_start_raw:
                            try:
                                self.earnings_start_time = datetime.fromisoformat(earnings_start_raw)
                            except (ValueError, TypeError):
                                self.earnings_start_time = None
                        last_update_raw = data.get('last_earnings_update')
                        if last_update_raw:
                            try:
                                self.last_earnings_update = datetime.fromisoformat(last_update_raw)
                            except (ValueError, TypeError):
                                self.last_earnings_update = None
                        payout_raw = data.get('last_payout_at')
                        if payout_raw:
                            try:
                                self.last_payout_at = datetime.fromisoformat(payout_raw)
                            except (ValueError, TypeError):
                                self.last_payout_at = None
                        if self.last_earnings_update is None:
                            self.last_earnings_update = datetime.now()
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
            'total_earned_moxi': self.total_earned_moxi,
            'earnings_balance_moxi': self.earnings_balance_moxi,
            'earnings_start_time': self.earnings_start_time.isoformat() if self.earnings_start_time else None,
            'last_earnings_update': self.last_earnings_update.isoformat() if self.last_earnings_update else None,
            'last_payout_at': self.last_payout_at.isoformat() if self.last_payout_at else None,
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
        self._accumulate_earnings()
        self.committed_storage_gb = max(0.0, committed_gb)
        self.last_earnings_update = datetime.now()
        self._save_identity()
    
    def add_profit(self, profit_moxi: float):
        """Add profit earned from storage lending (manual adjustment)."""
        if profit_moxi <= 0:
            return
        self.total_earned_moxi += profit_moxi
        self.earnings_balance_moxi += profit_moxi
        if self.earnings_start_time is None:
            self.earnings_start_time = datetime.now()
        self._save_identity()

    def _current_payout_rate(self) -> float:
        """Return the current payout rate in MOXI per second."""
        return max(0.0, self.committed_storage_gb / 10.0 * MOXI_PER_SECOND_PER_10_GB)

    def get_payout_rate_moxi_per_second(self) -> float:
        """Public accessor for the payout rate."""
        return self._current_payout_rate()

    def _accumulate_earnings(self) -> None:
        """Update accrued earnings based on elapsed time and committed storage."""
        now = datetime.now()
        if self.last_earnings_update is None:
            self.last_earnings_update = now
            return
        elapsed = (now - self.last_earnings_update).total_seconds()
        if elapsed <= 0:
            return
        rate = self._current_payout_rate()
        earned = rate * elapsed
        if earned > 0:
            self.earnings_balance_moxi += earned
            self.total_earned_moxi += earned
            if self.earnings_start_time is None:
                self.earnings_start_time = now
        self.last_earnings_update = now
        if earned > 0:
            self._save_identity()

    def get_pending_earnings_moxi(self) -> float:
        """Return up-to-date pending earnings in MOXI."""
        self._accumulate_earnings()
        return self.earnings_balance_moxi

    def claim_earnings(self, commit: bool = True) -> Dict[str, Any]:
        """
        Claim accumulated earnings.

        Args:
            commit: When False, returns the payout payload without mutating balances.
        """
        self._accumulate_earnings()
        payout_amount = self.earnings_balance_moxi
        payout_time = datetime.now()

        if commit and payout_amount > 0:
            self.earnings_balance_moxi = 0.0
            self.last_payout_at = payout_time
            self._save_identity()

        return {
            'amount_moxi': payout_amount,
            'payout_wallet': self.payment_wallet,
            'payout_at': payout_time.isoformat()
        }

    def record_payout(self, payout_amount: float) -> Dict[str, Any]:
        """
        Persist a successful payout by deducting the transferred amount.

        Args:
            payout_amount: Amount of MOXI that was actually transferred.
        """
        self._accumulate_earnings()
        payout_time = datetime.now()
        if payout_amount <= 0:
            return {
                'amount_moxi': 0.0,
                'payout_wallet': self.payment_wallet,
                'payout_at': payout_time.isoformat()
            }

        amount_to_record = min(payout_amount, self.earnings_balance_moxi)
        self.earnings_balance_moxi -= amount_to_record
        self.last_payout_at = payout_time
        self._save_identity()

        return {
            'amount_moxi': amount_to_record,
            'payout_wallet': self.payment_wallet,
            'payout_at': payout_time.isoformat()
        }

    
    def get_status(self) -> Dict[str, Any]:
        """Get current node status with real system stats."""
        total_gb, free_gb = self._get_disk_stats()
        uptime_seconds = self.get_uptime_seconds()
        available_gb = max(0.0, free_gb - self.committed_storage_gb)
        self._accumulate_earnings()
        payout_rate = self.get_payout_rate_moxi_per_second()
        
        return {
            'wallet_address': self.wallet_address,
            'payment_wallet': self.payment_wallet,
            'storage_lending_enabled': self.storage_lending_enabled,
            'total_storage_gb': round(total_gb, 2),
            'used_storage_gb': round(total_gb - free_gb, 2),
            'available_storage_gb': round(available_gb, 2),
            'committed_storage_gb': round(self.committed_storage_gb, 2),
            'total_earned_moxi': round(self.total_earned_moxi, 6),
            'pending_earnings_moxi': round(self.earnings_balance_moxi, 6),
            'payout_rate_moxi_per_second': round(payout_rate, 6),
            'last_payout_at': self.last_payout_at.isoformat() if self.last_payout_at else None,
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
