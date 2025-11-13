// @ts-ignore - ethers is available at runtime via hardhat-toolbox
import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  const signers = await ethers.getSigners();
  
  if (signers.length === 0) {
    throw new Error(
      "No signers found. Please check your .env file:\n" +
      "1. Ensure PRIVATE_KEY is set in .env file\n" +
      "2. Ensure .env file is in the root directory\n" +
      "3. Format: PRIVATE_KEY=your_private_key_here (no quotes, no 0x prefix)"
    );
  }
  
  const deployer = signers[0];
  console.log("Deploying DePIN Token with account:", deployer.address);
  console.log("Account balance:", (await ethers.provider.getBalance(deployer.address)).toString());

  // DePIN Token deployment parameters
  const tokenName = "Moxi AI";
  const tokenSymbol = "MOXI";
  const initialSupply = ethers.parseEther("1000000000"); // 1 billion tokens
  const rewardRate = ethers.parseEther("0.000000001"); // 0.000000001 tokens per second per token staked
  const minimumStakeAmount = ethers.parseEther("1000"); // Minimum 1000 tokens to stake
  const stakingLockPeriod = 7 * 24 * 60 * 60; // 7 days in seconds

  console.log("\nDeployment Parameters:");
  console.log("Token Name:", tokenName);
  console.log("Token Symbol:", tokenSymbol);
  console.log("Initial Supply:", ethers.formatEther(initialSupply), tokenSymbol);
  console.log("Reward Rate:", ethers.formatEther(rewardRate), "tokens/second/token staked");
  console.log("Minimum Stake Amount:", ethers.formatEther(minimumStakeAmount), tokenSymbol);
  console.log("Staking Lock Period:", stakingLockPeriod / (24 * 60 * 60), "days");

  // Deploy the contract
  const DePINToken = await ethers.getContractFactory("DePINToken");
  const depinToken = await DePINToken.deploy(
    tokenName,
    tokenSymbol,
    initialSupply,
    rewardRate,
    minimumStakeAmount,
    stakingLockPeriod
  );

  await depinToken.waitForDeployment();
  const contractAddress = await depinToken.getAddress();

  console.log("\n✅ DePIN Token deployed to:", contractAddress);

  // Get network information
  const network = await ethers.provider.getNetwork();
  const chainId = Number(network.chainId);
  console.log("Network:", network.name, "Chain ID:", chainId);
  
  // Get block explorer URL based on network
  const getExplorerUrl = (chainId: number, address: string): string => {
    switch (chainId) {
      case 42161: // Arbitrum One
        return `https://arbiscan.io/address/${address}`;
      case 421614: // Arbitrum Sepolia
        return `https://sepolia.arbiscan.io/address/${address}`;
      case 10: // Optimism
        return `https://optimistic.etherscan.io/address/${address}`;
      case 11155420: // Optimism Sepolia
        return `https://sepolia-optimism.etherscan.io/address/${address}`;
      case 8453: // Base
        return `https://basescan.org/address/${address}`;
      case 84532: // Base Sepolia
        return `https://sepolia.basescan.org/address/${address}`;
      case 1: // Ethereum Mainnet
        return `https://etherscan.io/address/${address}`;
      case 11155111: // Sepolia
        return `https://sepolia.etherscan.io/address/${address}`;
      default:
        return `Chain ID ${chainId} - Contract: ${address}`;
    }
  };
  
  const explorerUrl = getExplorerUrl(chainId, contractAddress);

  // Save deployment information
  const deploymentInfo = {
    network: network.name,
    chainId: Number(network.chainId),
    contractAddress: contractAddress,
    deployer: deployer.address,
    tokenName: tokenName,
    tokenSymbol: tokenSymbol,
    initialSupply: initialSupply.toString(),
    rewardRate: rewardRate.toString(),
    minimumStakeAmount: minimumStakeAmount.toString(),
    stakingLockPeriod: stakingLockPeriod.toString(),
    deployedAt: new Date().toISOString(),
  };

  // Create deployments directory if it doesn't exist
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir, { recursive: true });
  }

  // Save deployment info to file
  const deploymentFile = path.join(deploymentsDir, `${network.name}-${network.chainId}.json`);
  fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));
  console.log("\n📝 Deployment info saved to:", deploymentFile);

  // Wait for a few block confirmations before verification
  console.log("\n⏳ Waiting for block confirmations...");
  await depinToken.deploymentTransaction()?.wait(5);

  console.log("\n🎉 Deployment completed successfully!");
  console.log("\n📄 Contract URL:", explorerUrl);
  console.log("\n📋 Contract Address:", contractAddress);
  console.log("\nNext steps:");
  console.log("1. View your contract on the block explorer (link above)");
  console.log("2. Update your frontend with the contract address");
  console.log("3. Distribute tokens to your network participants");
  
  // Close provider connection to prevent async handle warnings
  if (ethers.provider && typeof ethers.provider.destroy === 'function') {
    await ethers.provider.destroy();
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });



