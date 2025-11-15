# Contract Documentation

## DePINToken.sol

### Overview

The DePINToken is an ERC-20 token designed for Decentralized Physical Infrastructure Networks (DePIN). It extends standard ERC-20 functionality with staking, rewards, and network participation incentives.

### Inheritance

- `ERC20`: Standard token functionality
- `ERC20Burnable`: Token burning capability
- `ERC20Pausable`: Emergency pause functionality
- `Ownable`: Access control
- `ReentrancyGuard`: Protection against reentrancy attacks

### State Variables

#### Public Variables
- `rewardRate` (uint256): Rewards per second per token staked
- `minimumStakeAmount` (uint256): Minimum tokens required to stake
- `stakingLockPeriod` (uint256): Minimum staking period in seconds
- `totalStaked` (uint256): Total amount of tokens currently staked

#### Mappings
- `stakes` (mapping): User address => Stake struct
- `stakers` (address[]): Array of all staker addresses
- `isStaker` (mapping): User address => boolean

### Structs

#### Stake
```solidity
struct Stake {
    uint256 amount;           // Amount of tokens staked
    uint256 stakedAt;         // Timestamp when staking started
    uint256 lastRewardClaimed; // Timestamp of last reward claim
    bool isActive;            // Whether the stake is active
}
```

### Functions

#### Public Functions

##### `stake(uint256 amount)`
Stake tokens to participate in the DePIN network.

**Parameters:**
- `amount`: Amount of tokens to stake

**Requirements:**
- Amount must be >= minimumStakeAmount
- User must have sufficient balance
- User must not have an active stake

**Effects:**
- Transfers tokens from user to contract
- Creates or updates stake record
- Updates totalStaked

##### `unstake(uint256 amount)`
Unstake tokens after the lock period has ended.

**Parameters:**
- `amount`: Amount of tokens to unstake

**Requirements:**
- User must have an active stake
- Amount must be <= staked amount
- Lock period must have ended

**Effects:**
- Claims pending rewards
- Transfers tokens back to user
- Updates stake record

##### `claimRewards()`
Claim accumulated staking rewards.

**Requirements:**
- User must have an active stake
- Must have pending rewards

**Effects:**
- Mints reward tokens to user
- Updates lastRewardClaimed timestamp

##### `calculateRewards(address user)`
Calculate pending rewards for a user.

**Parameters:**
- `user`: Address of the user

**Returns:**
- `uint256`: Amount of pending rewards

##### `getStakeInfo(address user)`
Get comprehensive staking information for a user.

**Parameters:**
- `user`: Address of the user

**Returns:**
- `amount`: Staked amount
- `stakedAt`: Staking start timestamp
- `lastRewardClaimed`: Last reward claim timestamp
- `pendingRewards`: Current pending rewards
- `isActive`: Whether stake is active

##### `getStakerCount()`
Get total number of stakers.

**Returns:**
- `uint256`: Number of stakers

#### Owner Functions

##### `setRewardRate(uint256 newRate)`
Update the reward rate.

**Parameters:**
- `newRate`: New reward rate

**Access:** Owner only

##### `setMinimumStakeAmount(uint256 newAmount)`
Update the minimum stake amount.

**Parameters:**
- `newAmount`: New minimum stake amount

**Access:** Owner only

##### `setStakingLockPeriod(uint256 newPeriod)`
Update the staking lock period.

**Parameters:**
- `newPeriod`: New lock period in seconds

**Access:** Owner only

##### `mint(address to, uint256 amount)`
Mint new tokens.

**Parameters:**
- `to`: Address to mint to
- `amount`: Amount to mint

**Access:** Owner only

##### `pause()`
Pause all token transfers.

**Access:** Owner only

##### `unpause()`
Unpause token transfers.

**Access:** Owner only

### Events

#### `Staked(address indexed user, uint256 amount, uint256 timestamp)`
Emitted when tokens are staked.

#### `Unstaked(address indexed user, uint256 amount, uint256 timestamp)`
Emitted when tokens are unstaked.

#### `RewardsClaimed(address indexed user, uint256 amount, uint256 timestamp)`
Emitted when rewards are claimed.

#### `RewardRateUpdated(uint256 oldRate, uint256 newRate)`
Emitted when reward rate is updated.

#### `MinimumStakeUpdated(uint256 oldAmount, uint256 newAmount)`
Emitted when minimum stake is updated.

#### `StakingLockPeriodUpdated(uint256 oldPeriod, uint256 newPeriod)`
Emitted when lock period is updated.

### Reward Calculation

Rewards are calculated using the formula:
```
rewards = (stakedAmount * rewardRate * timeStaked) / 1e18
```

Where:
- `stakedAmount`: Amount of tokens staked
- `rewardRate`: Rewards per second per token (in wei)
- `timeStaked`: Time since last reward claim (in seconds)

### Security Features

1. **Reentrancy Protection**: All state-changing functions use `nonReentrant` modifier
2. **Access Control**: Admin functions restricted to owner
3. **Pausable**: Emergency pause functionality
4. **Input Validation**: All inputs are validated
5. **Safe Math**: Uses Solidity 0.8.20 built-in overflow protection

### Usage Examples

#### Staking Tokens
```solidity
// Stake 5000 tokens
await depinToken.stake(ethers.parseEther("5000"));
```

#### Claiming Rewards
```solidity
// Claim accumulated rewards
await depinToken.claimRewards();
```

#### Unstaking Tokens
```solidity
// Unstake 2000 tokens (after lock period)
await depinToken.unstake(ethers.parseEther("2000"));
```

#### Viewing Stake Info
```solidity
// Get staking information
const stakeInfo = await depinToken.getStakeInfo(userAddress);
console.log("Staked:", stakeInfo.amount);
console.log("Pending Rewards:", stakeInfo.pendingRewards);
```

### Gas Optimization

- Uses `storage` references to minimize SLOAD operations
- Efficient reward calculation
- Minimal state updates
- Packed structs where possible

### Upgradeability

The contract is not upgradeable by design for security. To make it upgradeable:
1. Use OpenZeppelin's Upgradeable contracts
2. Implement a proxy pattern
3. Add upgrade functionality with proper access control

### Limitations

1. **Fixed Reward Rate**: Reward rate is set at deployment (can be updated by owner)
2. **Single Stake per User**: Each user can have only one active stake
3. **No Partial Unstaking During Lock**: Must wait for lock period to end
4. **Inflationary Model**: Rewards are minted, increasing total supply

### Future Enhancements

Potential improvements:
- Multiple stake pools with different rates
- Governance voting for parameter changes
- Multi-signature support
- Integration with DePIN protocols
- Advanced reward mechanisms
- Vesting schedules

---

For more information, see the main [README.md](README.md) file.



