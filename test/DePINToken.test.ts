import { expect } from "chai";
import { ethers } from "hardhat";
import { DePINToken } from "../typechain-types";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";

describe("DePINToken", function () {
  let depinToken: DePINToken;
  let owner: HardhatEthersSigner;
  let user1: HardhatEthersSigner;
  let user2: HardhatEthersSigner;
  let user3: HardhatEthersSigner;

  const tokenName = "DePIN Network Token";
  const tokenSymbol = "DePIN";
  const initialSupply = ethers.parseEther("1000000000"); // 1 billion
  const rewardRate = ethers.parseEther("0.000000001"); // 0.000000001 per second
  const minimumStakeAmount = ethers.parseEther("1000");
  const stakingLockPeriod = 7 * 24 * 60 * 60; // 7 days

  beforeEach(async function () {
    [owner, user1, user2, user3] = await ethers.getSigners();

    const DePINTokenFactory = await ethers.getContractFactory("DePINToken");
    depinToken = await DePINTokenFactory.deploy(
      tokenName,
      tokenSymbol,
      initialSupply,
      rewardRate,
      minimumStakeAmount,
      stakingLockPeriod
    );

    await depinToken.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await depinToken.owner()).to.equal(owner.address);
    });

    it("Should assign the total supply of tokens to the owner", async function () {
      const ownerBalance = await depinToken.balanceOf(owner.address);
      expect(ownerBalance).to.equal(initialSupply);
    });

    it("Should set the correct token name and symbol", async function () {
      expect(await depinToken.name()).to.equal(tokenName);
      expect(await depinToken.symbol()).to.equal(tokenSymbol);
    });

    it("Should set the correct staking parameters", async function () {
      expect(await depinToken.rewardRate()).to.equal(rewardRate);
      expect(await depinToken.minimumStakeAmount()).to.equal(minimumStakeAmount);
      expect(await depinToken.stakingLockPeriod()).to.equal(stakingLockPeriod);
    });
  });

  describe("Transactions", function () {
    it("Should transfer tokens between accounts", async function () {
      const transferAmount = ethers.parseEther("1000");
      await depinToken.transfer(user1.address, transferAmount);
      expect(await depinToken.balanceOf(user1.address)).to.equal(transferAmount);
    });

    it("Should fail if sender doesn't have enough tokens", async function () {
      const transferAmount = ethers.parseEther("10000000000"); // More than initial supply
      await expect(
        depinToken.connect(user1).transfer(user2.address, transferAmount)
      ).to.be.reverted;
    });

    it("Should update balances after transfers", async function () {
      const transferAmount = ethers.parseEther("5000");
      await depinToken.transfer(user1.address, transferAmount);
      await depinToken.transfer(user2.address, transferAmount);

      const ownerBalance = await depinToken.balanceOf(owner.address);
      expect(ownerBalance).to.equal(initialSupply - transferAmount * 2n);

      expect(await depinToken.balanceOf(user1.address)).to.equal(transferAmount);
      expect(await depinToken.balanceOf(user2.address)).to.equal(transferAmount);
    });
  });

  describe("Burning", function () {
    it("Should allow token burning", async function () {
      const burnAmount = ethers.parseEther("1000");
      await depinToken.burn(burnAmount);
      expect(await depinToken.balanceOf(owner.address)).to.equal(initialSupply - burnAmount);
      expect(await depinToken.totalSupply()).to.equal(initialSupply - burnAmount);
    });
  });

  describe("Pausing", function () {
    it("Should allow owner to pause transfers", async function () {
      await depinToken.pause();
      expect(await depinToken.paused()).to.be.true;
    });

    it("Should prevent transfers when paused", async function () {
      await depinToken.pause();
      await expect(
        depinToken.transfer(user1.address, ethers.parseEther("1000"))
      ).to.be.revertedWithCustomError(depinToken, "EnforcedPause");
    });

    it("Should allow owner to unpause transfers", async function () {
      await depinToken.pause();
      await depinToken.unpause();
      expect(await depinToken.paused()).to.be.false;
    });
  });

  describe("Staking", function () {
    beforeEach(async function () {
      // Transfer tokens to user1 for staking
      await depinToken.transfer(user1.address, ethers.parseEther("10000"));
    });

    it("Should allow users to stake tokens", async function () {
      const stakeAmount = ethers.parseEther("5000");
      await depinToken.connect(user1).stake(stakeAmount);

      const stakeInfo = await depinToken.getStakeInfo(user1.address);
      expect(stakeInfo.amount).to.equal(stakeAmount);
      expect(stakeInfo.isActive).to.be.true;
      expect(await depinToken.totalStaked()).to.equal(stakeAmount);
    });

    it("Should fail if stake amount is below minimum", async function () {
      const stakeAmount = ethers.parseEther("500"); // Below minimum
      await expect(
        depinToken.connect(user1).stake(stakeAmount)
      ).to.be.revertedWith("DePINToken: Amount below minimum stake");
    });

    it("Should fail if user doesn't have enough balance", async function () {
      const stakeAmount = ethers.parseEther("20000"); // More than balance
      await expect(
        depinToken.connect(user1).stake(stakeAmount)
      ).to.be.revertedWith("DePINToken: Insufficient balance");
    });

    it("Should transfer tokens to contract when staking", async function () {
      const stakeAmount = ethers.parseEther("5000");
      await depinToken.connect(user1).stake(stakeAmount);

      expect(await depinToken.balanceOf(user1.address)).to.equal(ethers.parseEther("5000"));
      expect(await depinToken.balanceOf(await depinToken.getAddress())).to.equal(stakeAmount);
    });
  });

  describe("Rewards", function () {
    beforeEach(async function () {
      // Transfer tokens to user1 for staking
      await depinToken.transfer(user1.address, ethers.parseEther("10000"));
      await depinToken.connect(user1).stake(ethers.parseEther("5000"));
    });

    it("Should calculate rewards correctly", async function () {
      // Wait 1 second
      await ethers.provider.send("evm_increaseTime", [1]);
      await ethers.provider.send("evm_mine", []);

      const rewards = await depinToken.calculateRewards(user1.address);
      // Rewards = 5000 * 0.000000001 * 1 = 0.000005
      expect(rewards).to.be.gt(0);
    });

    it("Should allow users to claim rewards", async function () {
      // Wait 1 day
      await ethers.provider.send("evm_increaseTime", [24 * 60 * 60]);
      await ethers.provider.send("evm_mine", []);

      const rewardsBefore = await depinToken.calculateRewards(user1.address);
      expect(rewardsBefore).to.be.gt(0);

      await depinToken.connect(user1).claimRewards();

      const rewardsAfter = await depinToken.calculateRewards(user1.address);
      expect(rewardsAfter).to.equal(0);

      // Check that user received rewards
      const userBalance = await depinToken.balanceOf(user1.address);
      expect(userBalance).to.be.gt(ethers.parseEther("5000"));
    });
  });

  describe("Unstaking", function () {
    beforeEach(async function () {
      // Transfer tokens to user1 for staking
      await depinToken.transfer(user1.address, ethers.parseEther("10000"));
      await depinToken.connect(user1).stake(ethers.parseEther("5000"));
    });

    it("Should fail if lock period hasn't ended", async function () {
      await expect(
        depinToken.connect(user1).unstake(ethers.parseEther("1000"))
      ).to.be.revertedWith("DePINToken: Staking lock period not ended");
    });

    it("Should allow unstaking after lock period", async function () {
      // Wait for lock period to end
      await ethers.provider.send("evm_increaseTime", [stakingLockPeriod + 1]);
      await ethers.provider.send("evm_mine", []);

      const unstakeAmount = ethers.parseEther("2000");
      await depinToken.connect(user1).unstake(unstakeAmount);

      const stakeInfo = await depinToken.getStakeInfo(user1.address);
      expect(stakeInfo.amount).to.equal(ethers.parseEther("3000"));
      expect(await depinToken.totalStaked()).to.equal(ethers.parseEther("3000"));
    });

    it("Should claim rewards when unstaking", async function () {
      // Wait for lock period to end
      await ethers.provider.send("evm_increaseTime", [stakingLockPeriod + 1]);
      await ethers.provider.send("evm_mine", []);

      const userBalanceBefore = await depinToken.balanceOf(user1.address);
      await depinToken.connect(user1).unstake(ethers.parseEther("1000"));
      const userBalanceAfter = await depinToken.balanceOf(user1.address);

      // User should have received staked tokens + rewards
      expect(userBalanceAfter).to.be.gt(userBalanceBefore);
    });
  });

  describe("Admin Functions", function () {
    it("Should allow owner to update reward rate", async function () {
      const newRate = ethers.parseEther("0.000000002");
      await depinToken.setRewardRate(newRate);
      expect(await depinToken.rewardRate()).to.equal(newRate);
    });

    it("Should allow owner to update minimum stake amount", async function () {
      const newMinimum = ethers.parseEther("2000");
      await depinToken.setMinimumStakeAmount(newMinimum);
      expect(await depinToken.minimumStakeAmount()).to.equal(newMinimum);
    });

    it("Should allow owner to update staking lock period", async function () {
      const newPeriod = 14 * 24 * 60 * 60; // 14 days
      await depinToken.setStakingLockPeriod(newPeriod);
      expect(await depinToken.stakingLockPeriod()).to.equal(newPeriod);
    });

    it("Should allow owner to mint new tokens", async function () {
      const mintAmount = ethers.parseEther("1000000");
      await depinToken.mint(user1.address, mintAmount);
      expect(await depinToken.balanceOf(user1.address)).to.equal(mintAmount);
    });

    it("Should prevent non-owner from calling admin functions", async function () {
      await expect(
        depinToken.connect(user1).setRewardRate(ethers.parseEther("0.000000002"))
      ).to.be.revertedWithCustomError(depinToken, "OwnableUnauthorizedAccount");

      await expect(
        depinToken.connect(user1).mint(user1.address, ethers.parseEther("1000"))
      ).to.be.revertedWithCustomError(depinToken, "OwnableUnauthorizedAccount");
    });
  });
});



