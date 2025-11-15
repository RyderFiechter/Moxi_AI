"""
Example script showing how to use the Node and Network classes programmatically.
This demonstrates the API for future integration.
"""

import asyncio
from node import Node
from network import Network


async def example_single_node():
    """Example: Create and run a single node."""
    print("Example 1: Single Node\n")
    
    # Create network
    network = Network(summary_interval=15)
    await network.start()
    
    # Create node with custom storage
    node = Node(
        total_storage_gb=100.0,
        identity_file="example_node.json",
        ping_interval=5
    )
    
    # Register and start
    network.register_node(node)
    await node.start(network)
    
    # Run for 30 seconds
    print("Running for 30 seconds...\n")
    await asyncio.sleep(30)
    
    # Stop
    await node.stop()
    await network.stop()


async def example_multiple_nodes():
    """Example: Create and run multiple nodes."""
    print("Example 2: Multiple Nodes\n")
    
    # Create network
    network = Network(summary_interval=20)
    await network.start()
    
    # Create multiple nodes
    nodes = []
    for i in range(3):
        node = Node(
            total_storage_gb=50.0 * (i + 1),  # Different storage sizes
            identity_file=f"example_node_{i+1}.json",
            ping_interval=8
        )
        network.register_node(node)
        nodes.append(node)
    
    # Start all nodes
    for node in nodes:
        await node.start(network)
        await asyncio.sleep(1)
    
    # Run for 45 seconds
    print("Running for 45 seconds...\n")
    await asyncio.sleep(45)
    
    # Stop all
    for node in nodes:
        await node.stop()
    await network.stop()


async def example_proof_of_storage():
    """Example: Using the proof of storage stub."""
    print("Example 3: Proof of Storage Stub\n")
    
    node = Node(
        total_storage_gb=200.0,
        identity_file="example_proof_node.json"
    )
    
    # Get node status
    status = node.get_status()
    print(f"Node: {status['wallet_address'][:10]}...")
    print(f"Available Storage: {status['available_storage_gb']} GB\n")
    
    # Test proof of storage (stub)
    chunk_id = "chunk_abc123"
    result = node.proof_of_storage(chunk_id)
    print(f"Proof of storage for {chunk_id}: {result}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        if example == "1":
            asyncio.run(example_single_node())
        elif example == "2":
            asyncio.run(example_multiple_nodes())
        elif example == "3":
            asyncio.run(example_proof_of_storage())
        else:
            print("Usage: python example_usage.py [1|2|3]")
    else:
        print("Running all examples...\n")
        asyncio.run(example_proof_of_storage())
        print("\n" + "="*50 + "\n")
        print("Run 'python example_usage.py 1' for single node example")
        print("Run 'python example_usage.py 2' for multiple nodes example")

