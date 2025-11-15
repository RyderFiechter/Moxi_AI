# Project Structure

```
Coin/
├── contracts/
│   └── DePINToken.sol          # Main DePIN token contract
├── scripts/
│   ├── deploy.ts               # Deployment script
│   ├── verify.ts               # Contract verification script
│   └── interact.ts             # Contract interaction script
├── test/
│   └── DePINToken.test.ts      # Comprehensive test suite
├── deployments/                # Deployment info (created after deployment)
├── hardhat.config.ts           # Hardhat configuration
├── package.json                # Project dependencies and scripts
├── tsconfig.json               # TypeScript configuration
├── .gitignore                  # Git ignore file
├── README.md                   # Main documentation
├── QUICKSTART.md              # Quick start guide
├── DEPLOYMENT.md              # Deployment guide
├── CONTRACT.md                # Contract documentation
└── PROJECT_STRUCTURE.md       # This file
```

## Key Files

### Contracts
- **DePINToken.sol**: Main token contract with staking and rewards

### Scripts
- **deploy.ts**: Deploys the token to specified network
- **verify.ts**: Verifies contract on block explorer
- **interact.ts**: Interacts with deployed contract

### Tests
- **DePINToken.test.ts**: Comprehensive test coverage

### Configuration
- **hardhat.config.ts**: Network and compiler configuration
- **package.json**: Dependencies and npm scripts
- **tsconfig.json**: TypeScript settings

### Documentation
- **README.md**: Complete project documentation
- **QUICKSTART.md**: Quick start guide
- **DEPLOYMENT.md**: Deployment instructions
- **CONTRACT.md**: Contract API documentation

## Features

✅ ERC-20 compliant token
✅ Staking mechanism
✅ Reward distribution
✅ Burnable tokens
✅ Pausable transfers
✅ Security features (ReentrancyGuard, Access Control)
✅ Comprehensive tests
✅ Multi-network deployment support
✅ Contract verification
✅ Interaction scripts

## Networks Supported

- Ethereum Mainnet
- Arbitrum (L2)
- Optimism (L2)
- Base (L2)
- Sepolia Testnet
- Arbitrum Sepolia
- Optimism Sepolia
- Base Sepolia
- Local Hardhat Network

## Next Steps

1. Install dependencies: `npm install`
2. Configure environment: Create `.env` file
3. Compile contracts: `npm run compile`
4. Run tests: `npm test`
5. Deploy to testnet: `npm run deploy:arbitrum-sepolia`
6. Verify contract: `npm run verify --network arbitrum-sepolia`
7. Deploy to mainnet: `npm run deploy:arbitrum`

---

For more information, see [README.md](README.md)



