// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title DePINToken
 * @dev DePIN (Decentralized Physical Infrastructure Network) Token
 * 
 * This token is designed for DePIN networks where participants contribute
 * physical infrastructure (storage, compute, bandwidth, sensors, etc.)
 * and earn rewards in return.
 * 
 * Features:
 * - Standard ERC-20 functionality
 * - Burnable tokens
 * - Pausable transfers (for emergency situations)
 * - Staking mechanism for infrastructure providers
 * - Reward distribution for network participation
 * - Governance-ready (can be extended)
 */
contract DePINToken is ERC20, ERC20Burnable, ERC20Pausable, Ownable, ReentrancyGuard {
    // Staking structure
    struct Stake {
        uint256 amount;
        uint256 stakedAt;
        uint256 lastRewardClaimed;
        bool isActive;
    }

    // Reward configuration
    uint256 public rewardRate; // Rewards per second per token staked (in wei)
    uint256 public minimumStakeAmount;
    uint256 public stakingLockPeriod; // Minimum time tokens must be staked (in seconds)
    
    // Total staked amount
    uint256 public totalStaked;
    
    // Mapping from user to their stake
    mapping(address => Stake) public stakes;
    
    // List of all stakers (for reward distribution tracking)
    address[] public stakers;
    mapping(address => bool) public isStaker;
    
    // Events
    event Staked(address indexed user, uint256 amount, uint256 timestamp);
    event Unstaked(address indexed user, uint256 amount, uint256 timestamp);
    event RewardsClaimed(address indexed user, uint256 amount, uint256 timestamp);
    event RewardRateUpdated(uint256 oldRate, uint256 newRate);
    event MinimumStakeUpdated(uint256 oldAmount, uint256 newAmount);
    event StakingLockPeriodUpdated(uint256 oldPeriod, uint256 newPeriod);
    
    /**
     * @dev Constructor
     * @param name Token name
     * @param symbol Token symbol
     * @param initialSupply Initial token supply
     * @param _rewardRate Initial reward rate (rewards per second per token)
     * @param _minimumStakeAmount Minimum amount required to stake
     * @param _stakingLockPeriod Minimum staking period in seconds
     */
    constructor(
        string memory name,
        string memory symbol,
        uint256 initialSupply,
        uint256 _rewardRate,
        uint256 _minimumStakeAmount,
        uint256 _stakingLockPeriod
    ) ERC20(name, symbol) Ownable(msg.sender) {
        _mint(msg.sender, initialSupply);
        rewardRate = _rewardRate;
        minimumStakeAmount = _minimumStakeAmount;
        stakingLockPeriod = _stakingLockPeriod;
    }
    
    /**
     * @dev Stake tokens to participate in the DePIN network
     * @param amount Amount of tokens to stake
     */
    function stake(uint256 amount) external nonReentrant whenNotPaused {
        require(amount >= minimumStakeAmount, "DePINToken: Amount below minimum stake");
        require(balanceOf(msg.sender) >= amount, "DePINToken: Insufficient balance");
        require(!stakes[msg.sender].isActive || stakes[msg.sender].amount == 0, "DePINToken: Already staking");
        
        // Transfer tokens from user to contract
        _transfer(msg.sender, address(this), amount);
        
        // Create or update stake
        if (!isStaker[msg.sender]) {
            stakers.push(msg.sender);
            isStaker[msg.sender] = true;
        }
        
        stakes[msg.sender] = Stake({
            amount: amount,
            stakedAt: block.timestamp,
            lastRewardClaimed: block.timestamp,
            isActive: true
        });
        
        totalStaked += amount;
        
        emit Staked(msg.sender, amount, block.timestamp);
    }
    
    /**
     * @dev Unstake tokens
     * @param amount Amount of tokens to unstake
     */
    function unstake(uint256 amount) external nonReentrant {
        Stake storage userStake = stakes[msg.sender];
        require(userStake.isActive, "DePINToken: No active stake");
        require(userStake.amount >= amount, "DePINToken: Insufficient staked amount");
        require(
            block.timestamp >= userStake.stakedAt + stakingLockPeriod,
            "DePINToken: Staking lock period not ended"
        );
        
        // Calculate and claim pending rewards before unstaking
        uint256 pendingRewards = calculateRewards(msg.sender);
        if (pendingRewards > 0) {
            userStake.lastRewardClaimed = block.timestamp;
            _mint(msg.sender, pendingRewards);
            emit RewardsClaimed(msg.sender, pendingRewards, block.timestamp);
        }
        
        // Update stake
        userStake.amount -= amount;
        totalStaked -= amount;
        
        // Transfer tokens back to user
        _transfer(address(this), msg.sender, amount);
        
        // If all tokens unstaked, mark stake as inactive
        if (userStake.amount == 0) {
            userStake.isActive = false;
        }
        
        emit Unstaked(msg.sender, amount, block.timestamp);
    }
    
    /**
     * @dev Claim staking rewards
     */
    function claimRewards() external nonReentrant {
        Stake storage userStake = stakes[msg.sender];
        require(userStake.isActive, "DePINToken: No active stake");
        
        uint256 pendingRewards = calculateRewards(msg.sender);
        require(pendingRewards > 0, "DePINToken: No rewards to claim");
        
        userStake.lastRewardClaimed = block.timestamp;
        _mint(msg.sender, pendingRewards);
        
        emit RewardsClaimed(msg.sender, pendingRewards, block.timestamp);
    }
    
    /**
     * @dev Calculate pending rewards for a user
     * @param user Address of the user
     * @return Amount of pending rewards
     */
    function calculateRewards(address user) public view returns (uint256) {
        Stake memory userStake = stakes[user];
        if (!userStake.isActive || userStake.amount == 0) {
            return 0;
        }
        
        uint256 timeStaked = block.timestamp - userStake.lastRewardClaimed;
        return (userStake.amount * rewardRate * timeStaked) / 1e18;
    }
    
    /**
     * @dev Get staking information for a user
     * @param user Address of the user
     * @return amount Staked amount
     * @return stakedAt Timestamp when staking started
     * @return lastRewardClaimed Timestamp of last reward claim
     * @return pendingRewards Current pending rewards
     * @return isActive Whether the stake is active
     */
    function getStakeInfo(address user) external view returns (
        uint256 amount,
        uint256 stakedAt,
        uint256 lastRewardClaimed,
        uint256 pendingRewards,
        bool isActive
    ) {
        Stake memory userStake = stakes[user];
        return (
            userStake.amount,
            userStake.stakedAt,
            userStake.lastRewardClaimed,
            calculateRewards(user),
            userStake.isActive
        );
    }
    
    /**
     * @dev Get total number of stakers
     * @return Number of stakers
     */
    function getStakerCount() external view returns (uint256) {
        return stakers.length;
    }
    
    // Admin functions
    
    /**
     * @dev Update reward rate (only owner)
     * @param newRate New reward rate
     */
    function setRewardRate(uint256 newRate) external onlyOwner {
        uint256 oldRate = rewardRate;
        rewardRate = newRate;
        emit RewardRateUpdated(oldRate, newRate);
    }
    
    /**
     * @dev Update minimum stake amount (only owner)
     * @param newAmount New minimum stake amount
     */
    function setMinimumStakeAmount(uint256 newAmount) external onlyOwner {
        uint256 oldAmount = minimumStakeAmount;
        minimumStakeAmount = newAmount;
        emit MinimumStakeUpdated(oldAmount, newAmount);
    }
    
    /**
     * @dev Update staking lock period (only owner)
     * @param newPeriod New staking lock period in seconds
     */
    function setStakingLockPeriod(uint256 newPeriod) external onlyOwner {
        uint256 oldPeriod = stakingLockPeriod;
        stakingLockPeriod = newPeriod;
        emit StakingLockPeriodUpdated(oldPeriod, newPeriod);
    }
    
    /**
     * @dev Mint new tokens (only owner)
     * @param to Address to mint to
     * @param amount Amount to mint
     */
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
    
    /**
     * @dev Pause token transfers (only owner)
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause token transfers (only owner)
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    // Override required functions
    
    function _update(address from, address to, uint256 value)
        internal
        override(ERC20, ERC20Pausable)
    {
        super._update(from, to, value);
    }
}

