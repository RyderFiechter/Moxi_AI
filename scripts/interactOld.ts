// @ts-ignore - ethers is available at runtime via hardhat-toolbox
import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

/**
 * Helper script to interact with deployed DePIN Token contract
 * Usage: npx hardhat run scripts/interact.ts --network <network-name>
 */

async function main() {
  const [signer] = await ethers.getSigners();
  console.log("Interacting with account:", signer.address);

  // Load deployment info
  const network = await ethers.provider.getNetwork();
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  const deploymentFile = path.join(deploymentsDir, `${network.name}-${network.chainId}.json`);

  if (!fs.existsSync(deploymentFile)) {
    console.error("Deployment file not found. Please deploy the contract first.");
    process.exit(1);
  }

  const deploymentInfo = JSON.parse(fs.readFileSync(deploymentFile, "utf8"));
  const contractAddress = deploymentInfo.contractAddress;

  console.log("Contract Address:", contractAddress);
  console.log("Network:", network.name, "Chain ID:", network.chainId);

  // Get contract instance
  const DePINToken = await ethers.getContractFactory("DePINToken");
  const depinToken = DePINToken.attach(contractAddress) as any;

  // Display contract information
  console.log("\n=== Contract Information ===");
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

  // Display user information
  console.log("\n=== User Information ===");
  const balance = await depinToken.balanceOf(signer.address);
  console.log("Balance:", ethers.formatEther(balance), symbol);

  const stakeInfo = await depinToken.getStakeInfo(signer.address);
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
      console.log("Lock Period Ended: Can unstake now");
    }
  } else {
    console.log("No active stake");
  }

  // Display staker count
  const stakerCount = await depinToken.getStakerCount();
  console.log("\nTotal Stakers:", stakerCount.toString());

  console.log("\n✅ Interaction complete!");
  console.log("\nTo interact with the contract, you can use:");
  console.log("1. stake(amount) - Stake tokens");
  console.log("2. unstake(amount) - Unstake tokens");
  console.log("3. claimRewards() - Claim rewards");
  console.log("4. calculateRewards(address) - Calculate rewards");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });



