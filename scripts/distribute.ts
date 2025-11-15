// @ts-ignore - ethers is available at runtime via hardhat-toolbox
import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

/**
 * Distribute tokens to multiple addresses
 * Usage: npx hardhat run scripts/distribute.ts --network <network-name>
 * 
 * Edit the recipients array below with addresses and amounts
 */

interface Recipient {
  address: string;
  amount: string; // Amount in tokens (will be converted to wei)
}

// Recipients list - Edit this with your addresses and amounts
const recipients: Recipient[] = [
  { address: "0x82a9337252d946933225bf0e2285991f5207f043", amount: "10000" }
  // Example format:
  // { address: "0x1234567890123456789012345678901234567890", amount: "10000" }, // 10,000 tokens
  // { address: "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd", amount: "5000" },  // 5,000 tokens
];

async function main() {
  const signers = await ethers.getSigners();
  
  if (signers.length === 0) {
    throw new Error("No signers found. Please check your .env file.");
  }
  
  const deployer = signers[0];
  console.log("Distributing tokens from:", deployer.address);
  console.log("Deployer balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)), "ETH");

  // Load deployment info
  const hre = await import("hardhat");
  const network = await ethers.provider.getNetwork();
  const networkName = hre.network.name;
  const chainId = Number(network.chainId);
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  const deploymentFile = path.join(deploymentsDir, `${networkName}-${chainId}.json`);

  if (!fs.existsSync(deploymentFile)) {
    console.error("Deployment file not found. Please deploy the contract first.");
    console.error("Expected file:", deploymentFile);
    process.exit(1);
  }

  const deploymentInfo = JSON.parse(fs.readFileSync(deploymentFile, "utf8"));
  const contractAddress = deploymentInfo.contractAddress;
  const tokenSymbol = deploymentInfo.tokenSymbol;

  console.log("\nContract Address:", contractAddress);
  console.log("Token Symbol:", tokenSymbol);
  console.log("Network:", networkName, "Chain ID:", chainId);

  // Get contract instance
  const DePINToken = await ethers.getContractFactory("DePINToken");
  const token = DePINToken.attach(contractAddress);

  // Check deployer token balance
  const deployerBalance = await token.balanceOf(deployer.address);
  console.log("\nDeployer token balance:", ethers.formatEther(deployerBalance), tokenSymbol);

  // Validate recipients
  if (recipients.length === 0) {
    console.error("\n❌ No recipients specified!");
    console.log("\nPlease edit scripts/distribute.ts and add recipients to the recipients array:");
    console.log('Example:');
    console.log('const recipients: Recipient[] = [');
    console.log('  { address: "0x1234...", amount: "10000" },');
    console.log('  { address: "0x5678...", amount: "5000" },');
    console.log('];');
    process.exit(1);
  }

  // Calculate total amount to distribute
  let totalAmount = BigInt(0);
  for (const recipient of recipients) {
    totalAmount += ethers.parseEther(recipient.amount);
  }

  console.log("\n📊 Distribution Summary:");
  console.log("Number of recipients:", recipients.length);
  console.log("Total amount to distribute:", ethers.formatEther(totalAmount), tokenSymbol);

  if (deployerBalance < totalAmount) {
    console.error("\n❌ Insufficient balance!");
    console.error("Required:", ethers.formatEther(totalAmount), tokenSymbol);
    console.error("Available:", ethers.formatEther(deployerBalance), tokenSymbol);
    process.exit(1);
  }

  // Confirm distribution
  console.log("\n⚠️  Ready to distribute tokens to the following addresses:");
  recipients.forEach((r, i) => {
    console.log(`  ${i + 1}. ${r.address}: ${r.amount} ${tokenSymbol}`);
  });

  console.log("\n⏳ Starting distribution...\n");

  // Distribute tokens
  let successCount = 0;
  let failCount = 0;

  for (let i = 0; i < recipients.length; i++) {
    const recipient = recipients[i];
    const amount = ethers.parseEther(recipient.amount);
    
    try {
      console.log(`[${i + 1}/${recipients.length}] Sending ${recipient.amount} ${tokenSymbol} to ${recipient.address}...`);
      
      const tx = await token.transfer(recipient.address, amount);
      console.log(`  Transaction hash: ${tx.hash}`);
      
      const receipt = await tx.wait();
      console.log(`  ✅ Success! Gas used: ${receipt.gasUsed.toString()}`);
      
      successCount++;
    } catch (error: any) {
      console.error(`  ❌ Failed: ${error.message}`);
      failCount++;
    }
    
    // Small delay to avoid rate limiting
    if (i < recipients.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  // Final summary
  console.log("\n" + "=".repeat(50));
  console.log("📊 Distribution Complete!");
  console.log("=".repeat(50));
  console.log(`✅ Successful: ${successCount}`);
  console.log(`❌ Failed: ${failCount}`);
  console.log(`📦 Total distributed: ${ethers.formatEther(totalAmount)} ${tokenSymbol}`);
  
  // Check final balances
  console.log("\n🔍 Verifying distributions...");
  for (const recipient of recipients) {
    try {
      const balance = await token.balanceOf(recipient.address);
      console.log(`  ${recipient.address}: ${ethers.formatEther(balance)} ${tokenSymbol}`);
    } catch (error) {
      console.log(`  ${recipient.address}: Failed to check balance`);
    }
  }

  const finalBalance = await token.balanceOf(deployer.address);
  console.log(`\n💰 Remaining balance: ${ethers.formatEther(finalBalance)} ${tokenSymbol}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

