"""
Network class for managing and aggregating storage provider nodes.
Handles node registration, ping aggregation, and periodic status summaries.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
try:
    from .node import Node
except ImportError:  # pragma: no cover
    from node import Node  # type: ignore


class Network:
    """Manages the decentralized storage network and node communications."""
    
    def __init__(self, summary_interval: int = 30):
        """
        Initialize the network.
        
        Args:
            summary_interval: Seconds between network status summaries.
        """
        self.nodes: Dict[str, Node] = {}
        self.node_pings: Dict[str, datetime] = {}
        self.summary_interval = summary_interval
        self.is_running = False
        self._summary_task: Optional[asyncio.Task] = None
        self.start_time = datetime.now()
    
    def register_node(self, node: Node):
        """
        Register a node with the network.
        
        Args:
            node: Node instance to register.
        """
        if node.wallet_address in self.nodes:
            print(f"⚠️  Node {node.wallet_address[:10]}... is already registered")
            return
        
        self.nodes[node.wallet_address] = node
        self.node_pings[node.wallet_address] = datetime.now()
        print(f"✅ Node {node.wallet_address[:10]}... registered with network")
    
    def receive_ping(self, node: Node):
        """
        Receive an uptime ping from a node.
        
        Args:
            node: Node that sent the ping.
        """
        if node.wallet_address not in self.nodes:
            print(f"⚠️  Received ping from unregistered node: {node.wallet_address[:10]}...")
            return
        
        self.node_pings[node.wallet_address] = datetime.now()
    
    def get_online_nodes(self, timeout_seconds: int = 20) -> List[str]:
        """
        Get list of online node addresses (nodes that pinged within timeout).
        
        Args:
            timeout_seconds: Seconds since last ping to consider node offline.
        
        Returns:
            List of wallet addresses of online nodes.
        """
        now = datetime.now()
        online = []
        
        for wallet, last_ping in self.node_pings.items():
            if (now - last_ping).total_seconds() <= timeout_seconds:
                online.append(wallet)
        
        return online
    
    def get_network_stats(self) -> Dict:
        """
        Get network-wide statistics.
        
        Returns:
            Dictionary with network statistics.
        """
        online_nodes = self.get_online_nodes()
        offline_nodes = [addr for addr in self.nodes.keys() if addr not in online_nodes]
        
        total_storage = sum(node.total_storage_gb for node in self.nodes.values())
        total_available = sum(node.get_available_storage_gb() for node in self.nodes.values())
        total_used = sum(node.used_storage_gb for node in self.nodes.values())
        
        online_storage = sum(
            node.get_available_storage_gb()
            for addr, node in self.nodes.items()
            if addr in online_nodes
        )
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'total_nodes': len(self.nodes),
            'online_nodes': len(online_nodes),
            'offline_nodes': len(offline_nodes),
            'total_storage_gb': round(total_storage, 2),
            'total_available_gb': round(total_available, 2),
            'total_used_gb': round(total_used, 2),
            'online_available_storage_gb': round(online_storage, 2),
            'network_uptime_seconds': int(uptime)
        }
    
    async def _summary_loop(self):
        """Periodically print network status summary."""
        while self.is_running:
            try:
                await asyncio.sleep(self.summary_interval)
                self._print_summary()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Error in summary loop: {e}")
    
    def _print_summary(self):
        """Print a formatted network status summary."""
        stats = self.get_network_stats()
        online_nodes = self.get_online_nodes()
        
        print("\n" + "=" * 80)
        print("📊 NETWORK STATUS SUMMARY")
        print("=" * 80)
        print(f"⏱️  Network Uptime: {stats['network_uptime_seconds']} seconds")
        print(f"🌐 Total Nodes: {stats['total_nodes']}")
        print(f"🟢 Online Nodes: {stats['online_nodes']}")
        print(f"🔴 Offline Nodes: {stats['offline_nodes']}")
        print(f"💾 Total Storage: {stats['total_storage_gb']:.2f} GB")
        print(f"📦 Available Storage: {stats['total_available_gb']:.2f} GB")
        print(f"✅ Online Available Storage: {stats['online_available_storage_gb']:.2f} GB")
        print(f"📊 Used Storage: {stats['total_used_gb']:.2f} GB")
        
        if online_nodes:
            print("\n🟢 ONLINE NODES:")
            for addr in online_nodes:
                node = self.nodes[addr]
                status = node.get_status()
                print(f"   • {addr[:10]}... | "
                      f"Available: {status['available_storage_gb']:.2f} GB | "
                      f"Uptime: {status['uptime_seconds']}s")
        
        if stats['offline_nodes'] > 0:
            offline = [addr for addr in self.nodes.keys() if addr not in online_nodes]
            print("\n🔴 OFFLINE NODES:")
            for addr in offline:
                node = self.nodes[addr]
                last_ping = self.node_pings.get(addr)
                if last_ping:
                    seconds_ago = (datetime.now() - last_ping).total_seconds()
                    print(f"   • {addr[:10]}... | Last ping: {int(seconds_ago)}s ago")
        
        print("=" * 80 + "\n")
    
    async def start(self):
        """Start the network monitoring."""
        self.is_running = True
        self.start_time = datetime.now()
        print("🌐 Network started - monitoring nodes...")
        self._summary_task = asyncio.create_task(self._summary_loop())
        # Print initial summary after a short delay
        await asyncio.sleep(2)
        self._print_summary()
    
    async def stop(self):
        """Stop the network monitoring."""
        self.is_running = False
        if self._summary_task:
            self._summary_task.cancel()
            try:
                await self._summary_task
            except asyncio.CancelledError:
                pass
        print("🌐 Network stopped")
    
    def print_immediate_summary(self):
        """Print network summary immediately (useful for debugging)."""
        self._print_summary()

