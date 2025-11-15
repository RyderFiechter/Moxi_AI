// @ts-ignore - ethers is available at runtime via hardhat-toolbox
import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

/**
 * Deploy contract and then run interact script in the same session
 * This ensures the contract is available for interaction
 */

async function main() {
  console.log("🚀 Deploying contract first...\n");
  
  // Import and run deploy logic
  const signers = await ethers.getSigners();
  const deployer = signers[0];
  console.log("Deploying DePIN Token with account:", deployer.address);

  const tokenName = "Moxi AI";
  const tokenSymbol = "MOXI";
  const initialSupply = ethers.parseEther("1000000000");
  const rewardRate = ethers.parseEther("0.000000001");
  const minimumStakeAmount = ethers.parseEther("1000");
  const stakingLockPeriod = 7 * 24 * 60 * 60;

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
  
  console.log("\n✅ Contract deployed to:", contractAddress);
  console.log("📝 Now you can interact with it!\n");
  
  // Now import and run interact
  console.log("=".repeat(50));
  console.log("Starting interactive session...");
  console.log("=".repeat(50) + "\n");
  
  // Import the interact functions
  const { default: interactMain } = await import("./interact");
  
  // Note: This won't work directly because interact.ts exports main()
  // Instead, we'll just show the contract info
  const name = await depinToken.name();
  const symbol = await depinToken.symbol();
  const totalSupply = await depinToken.totalSupply();
  
  console.log("Contract Info:");
  console.log("Name:", name);
  console.log("Symbol:", symbol);
  console.log("Total Supply:", ethers.formatEther(totalSupply), symbol);
  console.log("\n✅ Contract is ready! You can now use the interact script.");
  console.log("💡 Tip: For persistent state, use 'npm run node' in one terminal,");
  console.log("   then deploy and interact with --network localhost");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });




