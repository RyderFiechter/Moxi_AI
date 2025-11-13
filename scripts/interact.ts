// @ts-ignore - ethers is available at runtime via hardhat-toolbox
import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";
import * as readline from "readline";
import axios from "axios";
// @ts-ignore - systeminformation types may not be available
import * as si from "systeminformation";

/**
 * Interactive script to interact with deployed DePIN Token contract
 * and local storage provider nodes
 * Usage: npx hardhat run scripts/interact.ts --network <network-name>
 */

// Storage Node Configuration
const DEFAULT_NODE_PORT = 8000;
const DEFAULT_NODE_HOST = "http://localhost";

// Storage Node Status Interface
interface NodeStatus {
  wallet_address: string;
  total_storage_gb: number;
  used_storage_gb: number;
  available_storage_gb: number;
  uptime_seconds: number;
  uptime_formatted: string;
  started_at: string;
  last_ping: string | null;
  is_online: boolean;
}

// Storage Registry Contract Interface (placeholder ABI)
const STORAGE_REGISTRY_ABI = [
  "function offerStorage(address provider, uint256 storageGB, uint256 pricePerGB) external",
  "function updateStorage(address provider, uint256 storageGB) external",
  "function getProviderInfo(address provider) external view returns (uint256 storageGB, uint256 pricePerGB, bool isActive)",
  "function registerProvider(address provider, uint256 storageGB, uint256 pricePerGB) external",
  "event StorageOffered(address indexed provider, uint256 storageGB, uint256 pricePerGB)",
  "event StorageUpdated(address indexed provider, uint256 storageGB)"
];

// Create readline interface for user input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

function question(query: string): Promise<string> {
  return new Promise((resolve) => {
    rl.question(query, resolve);
  });
}

async function main() {
  const [signer] = await ethers.getSigners();
  console.log("Interacting with account:", signer.address);

  // Load deployment info
  const hre = await import("hardhat");
  const network = await ethers.provider.getNetwork();
  const networkName = hre.network.name;
  const chainId = Number(network.chainId);
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  const deploymentFile = path.join(deploymentsDir, `${networkName}-${chainId}.json`);

  if (!fs.existsSync(deploymentFile)) {
    console.error("Deployment file not found. Please deploy the contract first.");
    process.exit(1);
  }

  const deploymentInfo = JSON.parse(fs.readFileSync(deploymentFile, "utf8"));
  const contractAddress = deploymentInfo.contractAddress;

  console.log("Contract Address:", contractAddress);
  console.log("Network:", networkName, "Chain ID:", chainId);

  // Get contract instance
  const DePINToken = await ethers.getContractFactory("DePINToken");
  const depinToken = DePINToken.attach(contractAddress) as any;

  // Display initial contract information
  console.log("\n" + "=".repeat(50));
  console.log("=== DePIN Token Contract ===");
  console.log("=".repeat(50));
  
  // Check if contract exists by trying to get code
  const code = await ethers.provider.getCode(contractAddress);
  if (code === "0x") {
    console.error("\n❌ ERROR: No contract deployed at this address!");
    console.error("The contract address exists in the deployment file, but no contract code was found.");
    console.error("\n💡 Solution: Deploy the contract first:");
    console.error("   npx hardhat run scripts/deploy.ts");
    console.error("\n   Or use a persistent Hardhat node:");
    console.error("   Terminal 1: npm run node");
    console.error("   Terminal 2: npx hardhat run scripts/deploy.ts --network localhost");
    console.error("   Terminal 2: npm run interact -- --network localhost");
    process.exit(1);
  }
  
  const name = await depinToken.name();
  const symbol = await depinToken.symbol();
  const totalSupply = await depinToken.totalSupply();
  const totalStaked = await depinToken.totalStaked();
  const rewardRate = await depinToken.rewardRate();
  const minimumStake = await depinToken.minimumStakeAmount();
  const lockPeriod = await depinToken.stakingLockPeriod();

  console.log("Token Name:", name);
  console.log("Token Symbol:", symbol);
  console.log("Total Supply:", ethers.formatEther(totalSupply), symbol);
  console.log("Total Staked:", ethers.formatEther(totalStaked), symbol);
  console.log("Reward Rate:", ethers.formatEther(rewardRate), "tokens/second/token");
  console.log("Minimum Stake:", ethers.formatEther(minimumStake), symbol);
  console.log("Lock Period:", Number(lockPeriod) / (24 * 60 * 60), "days");

  // Main interaction loop
  let continueLoop = true;
  while (continueLoop) {
    console.log("\n" + "=".repeat(50));
    console.log("=== Available Actions ===");
    console.log("=".repeat(50));
    console.log("1. View my account info");
    console.log("2. Stake tokens");
    console.log("3. Unstake tokens");
    console.log("4. Claim rewards");
    console.log("5. View pending rewards");
    console.log("6. View staking info for any address");
    console.log("7. Transfer tokens");
    console.log("8. View contract statistics");
    console.log("9. Storage Node Operations");
    console.log("0. Exit");
    console.log("=".repeat(50));

    const choice = await question("\nSelect an action (0-9): ");

    try {
      switch (choice.trim()) {
        case "1":
          await viewAccountInfo(depinToken, signer.address, symbol, lockPeriod);
          break;

        case "2":
          await stakeTokens(depinToken, signer.address, symbol, minimumStake);
          break;

        case "3":
          await unstakeTokens(depinToken, signer.address, symbol);
          break;

        case "4":
          await claimRewards(depinToken, signer.address, symbol);
          break;

        case "5":
          await viewPendingRewards(depinToken, signer.address, symbol);
          break;

        case "6":
          const address = await question("Enter address to check: ");
          await viewStakingInfo(depinToken, address.trim(), symbol, lockPeriod);
          break;

        case "7":
          await transferTokens(depinToken, signer.address, symbol);
          break;

        case "8":
          await viewContractStats(depinToken, symbol);
          break;

        case "9":
          await storageNodeMenu(signer.address);
          break;

        case "0":
          console.log("\n👋 Exiting...");
          continueLoop = false;
          break;

        default:
          console.log("\n❌ Invalid choice. Please select 0-9.");
      }
    } catch (error: any) {
      console.error("\n❌ Error:", error.message);
    }

    if (continueLoop && choice !== "0") {
      const continueChoice = await question("\nContinue? (y/n): ");
      if (continueChoice.toLowerCase() !== "y") {
        continueLoop = false;
      }
    }
  }

  rl.close();
}

// Helper functions
async function viewAccountInfo(token: any, address: string, symbol: string, lockPeriod: bigint) {
  console.log("\n=== Your Account Information ===");
  const balance = await token.balanceOf(address);
  console.log("Token Balance:", ethers.formatEther(balance), symbol);

  const stakeInfo = await token.getStakeInfo(address);
  if (stakeInfo.isActive) {
    console.log("Staked Amount:", ethers.formatEther(stakeInfo.amount), symbol);
    console.log("Staked At:", new Date(Number(stakeInfo.stakedAt) * 1000).toLocaleString());
    console.log("Last Reward Claimed:", new Date(Number(stakeInfo.lastRewardClaimed) * 1000).toLocaleString());
    console.log("Pending Rewards:", ethers.formatEther(stakeInfo.pendingRewards), symbol);

    const lockEndTime = Number(stakeInfo.stakedAt) + Number(lockPeriod);
    const currentTime = Math.floor(Date.now() / 1000);
    if (currentTime < lockEndTime) {
      const remainingTime = lockEndTime - currentTime;
      console.log("Lock Period Ends:", new Date(lockEndTime * 1000).toLocaleString());
      console.log("Remaining Lock Time:", Math.floor(remainingTime / (24 * 60 * 60)), "days");
    } else {
      console.log("✅ Lock Period Ended: You can unstake now!");
    }
  } else {
    console.log("No active stake");
  }
}

async function stakeTokens(token: any, address: string, symbol: string, minimumStake: bigint) {
  console.log("\n=== Stake Tokens ===");
  const balance = await token.balanceOf(address);
  console.log("Your balance:", ethers.formatEther(balance), symbol);
  console.log("Minimum stake:", ethers.formatEther(minimumStake), symbol);

  const amountStr = await question(`Enter amount to stake (in ${symbol}): `);
  const amount = ethers.parseEther(amountStr.trim());

  if (amount < minimumStake) {
    console.log(`❌ Amount must be at least ${ethers.formatEther(minimumStake)} ${symbol}`);
    return;
  }

  if (amount > balance) {
    console.log(`❌ Insufficient balance. You have ${ethers.formatEther(balance)} ${symbol}`);
    return;
  }

  console.log(`\n⏳ Staking ${ethers.formatEther(amount)} ${symbol}...`);
  const tx = await token.stake(amount);
  console.log("Transaction hash:", tx.hash);
  console.log("⏳ Waiting for confirmation...");
  await tx.wait();
  console.log("✅ Tokens staked successfully!");
}

async function unstakeTokens(token: any, address: string, symbol: string) {
  console.log("\n=== Unstake Tokens ===");
  const stakeInfo = await token.getStakeInfo(address);

  if (!stakeInfo.isActive) {
    console.log("❌ You don't have an active stake");
    return;
  }

  console.log("Staked amount:", ethers.formatEther(stakeInfo.amount), symbol);
  const amountStr = await question(`Enter amount to unstake (in ${symbol}): `);
  const amount = ethers.parseEther(amountStr.trim());

  if (amount > stakeInfo.amount) {
    console.log(`❌ Cannot unstake more than staked amount`);
    return;
  }

  console.log(`\n⏳ Unstaking ${ethers.formatEther(amount)} ${symbol}...`);
  const tx = await token.unstake(amount);
  console.log("Transaction hash:", tx.hash);
  console.log("⏳ Waiting for confirmation...");
  await tx.wait();
  console.log("✅ Tokens unstaked successfully!");
}

async function claimRewards(token: any, address: string, symbol: string) {
  console.log("\n=== Claim Rewards ===");
  const pendingRewards = await token.calculateRewards(address);
  
  if (pendingRewards === 0n) {
    console.log("❌ No rewards to claim");
    return;
  }

  console.log("Pending rewards:", ethers.formatEther(pendingRewards), symbol);
  const confirm = await question("Claim rewards? (y/n): ");

  if (confirm.toLowerCase() !== "y") {
    return;
  }

  console.log("\n⏳ Claiming rewards...");
  const tx = await token.claimRewards();
  console.log("Transaction hash:", tx.hash);
  console.log("⏳ Waiting for confirmation...");
  await tx.wait();
  console.log("✅ Rewards claimed successfully!");
}

async function viewPendingRewards(token: any, address: string, symbol: string) {
  console.log("\n=== Pending Rewards ===");
  const rewards = await token.calculateRewards(address);
  console.log("Pending rewards:", ethers.formatEther(rewards), symbol);
}

async function viewStakingInfo(token: any, address: string, symbol: string, lockPeriod: bigint) {
  console.log(`\n=== Staking Info for ${address} ===`);
  try {
    const stakeInfo = await token.getStakeInfo(address);
    if (stakeInfo.isActive) {
      console.log("Staked Amount:", ethers.formatEther(stakeInfo.amount), symbol);
      console.log("Staked At:", new Date(Number(stakeInfo.stakedAt) * 1000).toLocaleString());
      console.log("Pending Rewards:", ethers.formatEther(stakeInfo.pendingRewards), symbol);
    } else {
      console.log("No active stake");
    }
  } catch (error) {
    console.log("❌ Invalid address or error fetching info");
  }
}

async function transferTokens(token: any, fromAddress: string, symbol: string) {
  console.log("\n=== Transfer Tokens ===");
  const balance = await token.balanceOf(fromAddress);
  console.log("Your balance:", ethers.formatEther(balance), symbol);

  const toAddress = await question("Enter recipient address: ");
  const amountStr = await question(`Enter amount to transfer (in ${symbol}): `);
  const amount = ethers.parseEther(amountStr.trim());

  if (amount > balance) {
    console.log(`❌ Insufficient balance`);
    return;
  }

  console.log(`\n⏳ Transferring ${ethers.formatEther(amount)} ${symbol} to ${toAddress.trim()}...`);
  const tx = await token.transfer(toAddress.trim(), amount);
  console.log("Transaction hash:", tx.hash);
  console.log("⏳ Waiting for confirmation...");
  await tx.wait();
  console.log("✅ Transfer successful!");
}

async function viewContractStats(token: any, symbol: string) {
  console.log("\n=== Contract Statistics ===");
  const totalStaked = await token.totalStaked();
  const stakerCount = await token.getStakerCount();
  console.log("Total Staked:", ethers.formatEther(totalStaked), symbol);
  console.log("Total Stakers:", stakerCount.toString());
}

// ============================================================================
// Storage Node Functions
// ============================================================================

/**
 * Detect local storage node by checking common ports
 */
async function detectLocalNode(host: string = DEFAULT_NODE_HOST, port: number = DEFAULT_NODE_PORT): Promise<NodeStatus | null> {
  try {
    const url = `${host}:${port}/status`;
    const response = await axios.get<NodeStatus>(url, { timeout: 2000 });
    return response.data;
  } catch (error: any) {
    if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
      return null;
    }
    throw error;
  }
}

/**
 * Get node status by wallet address (searches common ports)
 */
async function getNodeByWallet(walletAddress: string): Promise<NodeStatus | null> {
  const ports = [8000, 8001, 8002, 8003, 8004];
  
  for (const port of ports) {
    const node = await detectLocalNode(DEFAULT_NODE_HOST, port);
    if (node && node.wallet_address.toLowerCase() === walletAddress.toLowerCase()) {
      return node;
    }
  }
  
  return null;
}

/**
 * Get available storage for a node by wallet address
 */
async function getNodeStorage(walletAddress: string): Promise<number | null> {
  const node = await getNodeByWallet(walletAddress);
  return node ? node.available_storage_gb : null;
}

/**
 * Get system disk information using systeminformation
 */
async function getSystemDiskInfo(): Promise<{ totalGB: number; freeGB: number; usedGB: number }> {
  try {
    const disks = await si.fsSize();
    // Get root filesystem (first disk or C: on Windows)
    const rootDisk = disks[0] || disks.find((d: any) => d.mount === '/' || d.mount === 'C:\\');
    
    if (!rootDisk) {
      throw new Error("Could not find root filesystem");
    }
    
    return {
      totalGB: rootDisk.size / (1024 ** 3),
      freeGB: rootDisk.available / (1024 ** 3),
      usedGB: (rootDisk.size - rootDisk.available) / (1024 ** 3)
    };
  } catch (error: any) {
    console.error("Error getting disk info:", error.message);
    throw error;
  }
}

/**
 * Send ping to storage node
 */
async function pingStorageNode(host: string = DEFAULT_NODE_HOST, port: number = DEFAULT_NODE_PORT): Promise<boolean> {
  try {
    const url = `${host}:${port}/ping`;
    await axios.post(url, {}, { timeout: 2000 });
    return true;
  } catch (error: any) {
    return false;
  }
}

/**
 * Offer storage to StorageRegistry contract
 */
async function offerStorage(
  registryAddress: string,
  providerAddress: string,
  storageGB: number,
  pricePerGB: bigint,
  signer: ethers.Signer
): Promise<ethers.ContractTransactionResponse> {
  const registry = new ethers.Contract(registryAddress, STORAGE_REGISTRY_ABI, signer);
  const storageGBWei = ethers.parseUnits(storageGB.toString(), 0); // Convert to uint256
  
  console.log(`\n📤 Offering storage to registry...`);
  console.log(`   Provider: ${providerAddress}`);
  console.log(`   Storage: ${storageGB} GB`);
  console.log(`   Price per GB: ${ethers.formatEther(pricePerGB)} ETH`);
  
  const tx = await registry.offerStorage(providerAddress, storageGBWei, pricePerGB);
  return tx;
}

/**
 * Update storage availability in registry
 */
async function updateStorage(
  registryAddress: string,
  providerAddress: string,
  storageGB: number,
  signer: ethers.Signer
): Promise<ethers.ContractTransactionResponse> {
  const registry = new ethers.Contract(registryAddress, STORAGE_REGISTRY_ABI, signer);
  const storageGBWei = ethers.parseUnits(storageGB.toString(), 0);
  
  console.log(`\n📤 Updating storage in registry...`);
  console.log(`   Provider: ${providerAddress}`);
  console.log(`   New Storage: ${storageGB} GB`);
  
  const tx = await registry.updateStorage(providerAddress, storageGBWei);
  return tx;
}

/**
 * Storage Node Operations Menu
 */
async function storageNodeMenu(userAddress: string) {
  console.log("\n" + "=".repeat(50));
  console.log("=== Storage Node Operations ===");
  console.log("=".repeat(50));
  console.log("1. Detect local storage node");
  console.log("2. Get node status by wallet address");
  console.log("3. Get available storage by wallet");
  console.log("4. Get system disk information");
  console.log("5. Ping storage node");
  console.log("6. Offer storage to registry (requires registry address)");
  console.log("7. Update storage in registry");
  console.log("8. Auto-report storage (periodic updates)");
  console.log("0. Back to main menu");
  console.log("=".repeat(50));
  
  const choice = await question("\nSelect an action (0-8): ");
  
  try {
    switch (choice.trim()) {
      case "1": {
        const portStr = await question(`Enter node port (default ${DEFAULT_NODE_PORT}): `);
        const port = portStr.trim() ? parseInt(portStr.trim()) : DEFAULT_NODE_PORT;
        const node = await detectLocalNode(DEFAULT_NODE_HOST, port);
        if (node) {
          console.log("\n✅ Node detected!");
          console.log("Wallet Address:", node.wallet_address);
          console.log("Total Storage:", node.total_storage_gb, "GB");
          console.log("Available Storage:", node.available_storage_gb, "GB");
          console.log("Uptime:", node.uptime_formatted);
          console.log("Status:", node.is_online ? "Online" : "Offline");
        } else {
          console.log("\n❌ No node detected on port", port);
        }
        break;
      }
      
      case "2": {
        const wallet = await question("Enter wallet address: ");
        const node = await getNodeByWallet(wallet.trim());
        if (node) {
          console.log("\n✅ Node found!");
          console.log("Wallet Address:", node.wallet_address);
          console.log("Total Storage:", node.total_storage_gb, "GB");
          console.log("Used Storage:", node.used_storage_gb, "GB");
          console.log("Available Storage:", node.available_storage_gb, "GB");
          console.log("Uptime:", node.uptime_formatted);
          console.log("Started At:", node.started_at);
          console.log("Last Ping:", node.last_ping || "Never");
        } else {
          console.log("\n❌ No node found with that wallet address");
        }
        break;
      }
      
      case "3": {
        const wallet = await question("Enter wallet address: ");
        const storage = await getNodeStorage(wallet.trim());
        if (storage !== null) {
          console.log(`\n✅ Available storage: ${storage.toFixed(2)} GB`);
        } else {
          console.log("\n❌ Node not found or not accessible");
        }
        break;
      }
      
      case "4": {
        console.log("\n⏳ Getting system disk information...");
        const diskInfo = await getSystemDiskInfo();
        console.log("\n💾 System Disk Information:");
        console.log("Total:", diskInfo.totalGB.toFixed(2), "GB");
        console.log("Used:", diskInfo.usedGB.toFixed(2), "GB");
        console.log("Free:", diskInfo.freeGB.toFixed(2), "GB");
        break;
      }
      
      case "5": {
        const portStr = await question(`Enter node port (default ${DEFAULT_NODE_PORT}): `);
        const port = portStr.trim() ? parseInt(portStr.trim()) : DEFAULT_NODE_PORT;
        console.log("\n⏳ Pinging node...");
        const success = await pingStorageNode(DEFAULT_NODE_HOST, port);
        if (success) {
          console.log("✅ Node responded to ping");
        } else {
          console.log("❌ Node did not respond");
        }
        break;
      }
      
      case "6": {
        const [signer] = await ethers.getSigners();
        const registryAddr = await question("Enter StorageRegistry contract address: ");
        const providerAddr = await question(`Enter provider address (default: ${userAddress}): `);
        const provider = providerAddr.trim() || userAddress;
        
        // Get storage from node or system
        const node = await getNodeByWallet(provider);
        let storageGB: number;
        
        if (node) {
          storageGB = node.available_storage_gb;
          console.log(`\n📊 Using node storage: ${storageGB.toFixed(2)} GB`);
        } else {
          const diskInfo = await getSystemDiskInfo();
          storageGB = diskInfo.freeGB;
          console.log(`\n📊 Using system storage: ${storageGB.toFixed(2)} GB`);
        }
        
        const priceStr = await question("Enter price per GB (in ETH): ");
        const pricePerGB = ethers.parseEther(priceStr.trim());
        
        const tx = await offerStorage(registryAddr.trim(), provider, storageGB, pricePerGB, signer);
        console.log("Transaction hash:", tx.hash);
        console.log("⏳ Waiting for confirmation...");
        await tx.wait();
        console.log("✅ Storage offered successfully!");
        break;
      }
      
      case "7": {
        const [signer] = await ethers.getSigners();
        const registryAddr = await question("Enter StorageRegistry contract address: ");
        const providerAddr = await question(`Enter provider address (default: ${userAddress}): `);
        const provider = providerAddr.trim() || userAddress;
        
        // Get current storage
        const node = await getNodeByWallet(provider);
        let storageGB: number;
        
        if (node) {
          storageGB = node.available_storage_gb;
          console.log(`\n📊 Current node storage: ${storageGB.toFixed(2)} GB`);
        } else {
          const diskInfo = await getSystemDiskInfo();
          storageGB = diskInfo.freeGB;
          console.log(`\n📊 Current system storage: ${storageGB.toFixed(2)} GB`);
        }
        
        const tx = await updateStorage(registryAddr.trim(), provider, storageGB, signer);
        console.log("Transaction hash:", tx.hash);
        console.log("⏳ Waiting for confirmation...");
        await tx.wait();
        console.log("✅ Storage updated successfully!");
        break;
      }
      
      case "8": {
        const registryAddr = await question("Enter StorageRegistry contract address: ");
        const intervalStr = await question("Enter update interval in seconds (default: 300): ");
        const interval = intervalStr.trim() ? parseInt(intervalStr.trim()) : 300;
        
        console.log(`\n🔄 Starting auto-reporting every ${interval} seconds...`);
        console.log("Press Enter to stop");
        
        const [signer] = await ethers.getSigners();
        const provider = userAddress;
        
        let shouldStop = false;
        
        // Set up stop handler
        const stopPromise = question("").then(() => {
          shouldStop = true;
          console.log("\n🛑 Stopping auto-reporting...");
        });
        
        // Auto-report loop
        while (!shouldStop) {
          try {
            const node = await getNodeByWallet(provider);
            let storageGB: number;
            
            if (node) {
              storageGB = node.available_storage_gb;
              console.log(`\n[${new Date().toLocaleTimeString()}] Node storage: ${storageGB.toFixed(2)} GB`);
            } else {
              const diskInfo = await getSystemDiskInfo();
              storageGB = diskInfo.freeGB;
              console.log(`\n[${new Date().toLocaleTimeString()}] System storage: ${storageGB.toFixed(2)} GB`);
            }
            
            const tx = await updateStorage(registryAddr.trim(), provider, storageGB, signer);
            console.log(`✅ Updated registry - TX: ${tx.hash}`);
            await tx.wait();
            
            // Wait for interval or stop signal
            await Promise.race([
              new Promise(resolve => setTimeout(resolve, interval * 1000)),
              stopPromise.catch(() => {})
            ]);
          } catch (error: any) {
            console.error(`❌ Error in auto-report: ${error.message}`);
            // Wait before retrying
            await new Promise(resolve => setTimeout(resolve, interval * 1000));
          }
        }
        break;
      }
      
      case "0":
        return;
      
      default:
        console.log("\n❌ Invalid choice.");
    }
  } catch (error: any) {
    console.error("\n❌ Error:", error.message);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    rl.close();
    process.exit(1);
  });