# Quick Start Guide

Get your DePIN token up and running in minutes!

## 🚀 Quick Setup (5 minutes)

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
Create a `.env` file:
```bash
PRIVATE_KEY=your_private_key_here
ARBITRUM_RPC_URL=https://arb-mainnet.g.alchemy.com/v2/YOUR_API_KEY
```

### 3. Compile Contracts
```bash
npm run compile
```

### 4. Run Tests
```bash
npm test
```

### 5. Deploy to Testnet
```bash
npx hardhat run scripts/deploy.ts --network arbitrum-sepolia
```

## 📝 Common Commands

### Development
```bash
# Start local node
npm run node

# Deploy to local network
npm run deploy:local

# Run tests
npm test

# Compile contracts
npm run compile
```

### Deployment
```bash
# Deploy to Arbitrum
npm run deploy:arbitrum

# Deploy to Optimism
npm run deploy:optimism

# Deploy to Base
npm run deploy:base
```

### Interaction
```bash
# Interact with deployed contract
npx hardhat run scripts/interact.ts --network <network-name>
```

## 🔧 Configuration

### Modify Token Parameters

Edit `scripts/deploy.ts`:
```typescript
const tokenName = "DePIN Network Token";
const tokenSymbol = "DePIN";
const initialSupply = ethers.parseEther("1000000000"); // 1 billion
const rewardRate = ethers.parseEther("0.000000001");
const minimumStakeAmount = ethers.parseEther("1000");
const stakingLockPeriod = 7 * 24 * 60 * 60; // 7 days
```

## 📚 Next Steps

1. **Deploy to Testnet**: Test on Sepolia or Arbitrum Sepolia
2. **Verify Contract**: Verify on block explorer
3. **Distribute Tokens**: Send tokens to network participants
4. **Set Up Frontend**: Create a dApp for users
5. **Monitor**: Track contract activity

## 🆘 Troubleshooting

### Installation Issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Compilation Errors
```bash
# Clean and recompile
npx hardhat clean
npm run compile
```

### Deployment Issues
- Check your `.env` file has correct RPC URL
- Ensure wallet has sufficient funds
- Verify network is accessible

## 📖 Documentation

- [README.md](README.md) - Full documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [CONTRACT.md](CONTRACT.md) - Contract documentation

## 🎯 Example Usage

### Stake Tokens
```javascript
const token = await ethers.getContractAt("DePINToken", contractAddress);
await token.stake(ethers.parseEther("5000"));
```

### Claim Rewards
```javascript
await token.claimRewards();
```

### Unstake Tokens
```javascript
await token.unstake(ethers.parseEther("2000"));
```

## ✅ Checklist

- [ ] Dependencies installed
- [ ] Environment configured
- [ ] Contracts compiled
- [ ] Tests passing
- [ ] Deployed to testnet
- [ ] Contract verified
- [ ] Tokens distributed

---

Ready to deploy! 🚀



