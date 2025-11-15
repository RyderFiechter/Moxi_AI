// @ts-ignore - ethers is available at runtime via hardhat-toolbox
import { run, ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

/**
 * Verify deployed contract on block explorer
 * Usage: npx hardhat run scripts/verify.ts --network <network-name>
 */

async function main() {
  const hre = await import("hardhat");
  const network = await hre.ethers.provider.getNetwork();
  const networkName = hre.network.name;
  console.log("Network:", networkName, "Chain ID:", network.chainId);

  // Load deployment info
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  const deploymentFile = path.join(deploymentsDir, `${networkName}-${network.chainId}.json`);

  if (!fs.existsSync(deploymentFile)) {
    console.error("Deployment file not found. Please deploy the contract first.");
    process.exit(1);
  }

  const deploymentInfo = JSON.parse(fs.readFileSync(deploymentFile, "utf8"));
  const contractAddress = deploymentInfo.contractAddress;

  console.log("Contract Address:", contractAddress);
  console.log("\nVerifying contract...");

  try {
    await run("verify:verify", {
      address: contractAddress,
      constructorArguments: [
        deploymentInfo.tokenName,
        deploymentInfo.tokenSymbol,
        deploymentInfo.initialSupply,
        deploymentInfo.rewardRate,
        deploymentInfo.minimumStakeAmount,
        deploymentInfo.stakingLockPeriod,
      ],
    });

    console.log("\n✅ Contract verified successfully!");
  } catch (error: any) {
    if (error.message.toLowerCase().includes("already verified")) {
      console.log("\n✅ Contract already verified!");
    } else if (error.message.toLowerCase().includes("deprecated") || error.message.toLowerCase().includes("v1")) {
      console.warn("\n⚠️  API Version Warning (non-critical):", error.message);
      console.log("\n💡 The contract may still verify. Check Arbiscan manually:");
      console.log(`   https://sepolia.arbiscan.io/address/${contractAddress}#code`);
    } else {
      console.error("\n❌ Verification failed:", error.message);
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

