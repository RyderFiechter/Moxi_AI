# Deployment Guide

This guide provides step-by-step instructions for deploying the DePIN Token to various networks.

## Prerequisites

1. **Wallet Setup**: Ensure you have a wallet with sufficient funds for deployment
2. **Environment Variables**: Set up your `.env` file with required variables
3. **Network Access**: Have RPC endpoints configured for your target network

## Environment Setup

### 1. Create `.env` File

Copy the example file and fill in your values:
```bash
cp .env.example .env
```

### 2. Required Variables

```env
# Private key (NEVER commit this)
PRIVATE_KEY=your_private_key_here

# RPC URLs (use Alchemy, Infura, or public RPCs)
ARBITRUM_RPC_URL=https://arb-mainnet.g.alchemy.com/v2/YOUR_API_KEY
OPTIMISM_RPC_URL=https://opt-mainnet.g.alchemy.com/v2/YOUR_API_KEY
BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/YOUR_API_KEY

# API Keys for verification (optional but recommended)
ARBISCAN_API_KEY=your_arbiscan_api_key
OPTIMISM_API_KEY=your_optimism_api_key
BASESCAN_API_KEY=your_basescan_api_key
```

## Deployment Steps

### Step 1: Compile Contracts

```bash
npm run compile
```

### Step 2: Run Tests

```bash
npm test
```

### Step 3: Deploy to Network

Choose your target network:

#### Arbitrum Mainnet
```bash
npm run deploy:arbitrum
```

#### Optimism Mainnet
```bash
npm run deploy:optimism
```

#### Base Mainnet
```bash
npm run deploy:base
```

#### Testnet (Recommended for First Deployment)
```bash
npx hardhat run scripts/deploy.ts --network arbitrum-sepolia
```

### Step 4: Verify Contract

After deployment, verify the contract on the block explorer:

```bash
npx hardhat verify --network <network-name> <contract-address> "DePIN Network Token" "DePIN" 1000000000000000000000000000 1000000000 1000000000000000000000 604800
```

Replace:
- `<network-name>` with your network (e.g., `arbitrum`, `optimism`, `base`)
- `<contract-address>` with your deployed contract address

## Deployment Parameters

The deployment script uses the following parameters (can be modified in `scripts/deploy.ts`):

- **Token Name**: "DePIN Network Token"
- **Token Symbol**: "DePIN"
- **Initial Supply**: 1,000,000,000 tokens (1e27 wei)
- **Reward Rate**: 0.000000001 tokens/second/token staked (1e9 wei)
- **Minimum Stake**: 1,000 tokens (1e21 wei)
- **Lock Period**: 7 days (604,800 seconds)

## Gas Estimation

Approximate gas costs (varies by network):
- **Arbitrum**: ~1-2 million gas (~$1-5)
- **Optimism**: ~1-2 million gas (~$1-5)
- **Base**: ~1-2 million gas (~$0.5-2)
- **Ethereum Mainnet**: ~2-3 million gas (~$50-150)

## Post-Deployment

### 1. Save Deployment Info

Deployment information is automatically saved to `deployments/` directory.

### 2. Transfer Ownership (Optional)

If you want to transfer contract ownership:
```bash
npx hardhat run scripts/transferOwnership.ts --network <network-name>
```

### 3. Distribute Tokens

Transfer tokens to network participants:
```javascript
const token = await ethers.getContractAt("DePINToken", contractAddress);
await token.transfer(recipientAddress, ethers.parseEther("1000000"));
```

### 4. Configure Parameters

Adjust staking parameters if needed:
```javascript
await token.setRewardRate(newRewardRate);
await token.setMinimumStakeAmount(newMinimum);
await token.setStakingLockPeriod(newPeriod);
```

## Network-Specific Notes

### Arbitrum
- Fast transactions, low fees
- Full EVM compatibility
- Recommended for high-volume DePIN networks

### Optimism
- Optimistic rollup
- Fast finality
- Good for DePIN applications

### Base
- Coinbase's L2
- Growing ecosystem
- Low fees

### Ethereum Mainnet
- Highest security
- Highest fees
- Consider L2 alternatives

## Troubleshooting

### Insufficient Funds
```
Error: insufficient funds for gas
```
**Solution**: Add more ETH to your wallet

### Network Connection Issues
```
Error: could not detect network
```
**Solution**: Check your RPC URL in `.env` file

### Contract Verification Failed
```
Error: Contract verification failed
```
**Solution**: 
1. Wait a few minutes after deployment
2. Check that constructor parameters match
3. Verify network and contract address are correct

## Security Checklist

- [ ] Contracts compiled without errors
- [ ] All tests passing
- [ ] Contract verified on block explorer
- [ ] Private keys secured (never committed)
- [ ] Deployment parameters reviewed
- [ ] Gas limits sufficient
- [ ] Owner address correct
- [ ] Initial supply verified

## Next Steps

After successful deployment:

1. **Monitor Contract**: Use block explorers to monitor activity
2. **Set Up Frontend**: Create a dApp for users
3. **Distribute Tokens**: Allocate tokens to participants
4. **Configure Rewards**: Adjust reward rates as needed
5. **Documentation**: Update documentation with contract address

## Support

For deployment issues:
1. Check network status
2. Verify RPC endpoints
3. Review gas prices
4. Check contract verification status

---

Happy Deploying! 🚀



