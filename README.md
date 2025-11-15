# DePIN Token - Decentralized Physical Infrastructure Network Token

A comprehensive ERC-20 token implementation designed for DePIN (Decentralized Physical Infrastructure Networks) on Ethereum Layer 2/3 networks. This token incentivizes participants to contribute physical infrastructure (storage, compute, bandwidth, sensors, etc.) to decentralized networks.

## 🚀 Features

- **Standard ERC-20 Token**: Fully compliant with ERC-20 standard
- **Burnable**: Tokens can be burned to reduce supply
- **Pausable**: Emergency pause functionality for transfers
- **Staking Mechanism**: Stake tokens to participate in the network
- **Reward Distribution**: Earn rewards for staking and network participation
- **Flexible Configuration**: Adjustable reward rates, minimum stakes, and lock periods
- **Security**: Built with OpenZeppelin contracts and includes reentrancy protection

## 📋 Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- A wallet with ETH for deployment (on the target network)
- RPC endpoint for your target network (Alchemy, Infura, or public RPC)

## 🛠️ Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd Coin
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the root directory:
```bash
cp .env.example .env
```

4. Update `.env` with your configuration:
   - `PRIVATE_KEY`: Your wallet private key (for deployment)
   - `RPC_URL`: RPC endpoint for your target network
   - API keys for block explorer verification (optional)

## 📝 Configuration

### Network Configuration

The project is configured to deploy on multiple networks:
- **Ethereum Mainnet** (Layer 1)
- **Arbitrum** (Layer 2)
- **Optimism** (Layer 2)
- **Base** (Layer 2)
- **Sepolia Testnet** (for testing)

### Token Parameters

Default deployment parameters (can be modified in `scripts/deploy.ts`):
- **Token Name**: DePIN Network Token
- **Token Symbol**: DePIN
- **Initial Supply**: 1,000,000,000 tokens
- **Reward Rate**: 0.000000001 tokens per second per token staked
- **Minimum Stake**: 1,000 tokens
- **Staking Lock Period**: 7 days

## 🚀 Deployment

### Local Development

1. Start a local Hardhat node:
```bash
npm run node
```

2. In a separate terminal, deploy to local network:
```bash
npm run deploy:local
```

### Deploy to Testnet

1. Deploy to Sepolia testnet:
```bash
npx hardhat run scripts/deploy.ts --network sepolia
```

2. Deploy to Arbitrum Sepolia:
```bash
npx hardhat run scripts/deploy.ts --network arbitrum-sepolia
```

### Deploy to Mainnet (Layer 2/3)

1. Deploy to Arbitrum:
```bash
npm run deploy:arbitrum
```

2. Deploy to Optimism:
```bash
npm run deploy:optimism
```

3. Deploy to Base:
```bash
npm run deploy:base
```

### Verify Contract

After deployment, verify the contract on the block explorer:
```bash
npx hardhat verify --network <network-name> <contract-address> "DePIN Network Token" "DePIN" 1000000000000000000000000000 1000000000 1000000000000000000000 604800
```

## Storage Node & dApp Workflow

1. **Run the storage node**
   - Install Python deps and prep config: `cd node && pip install -r requirements.txt`. Install optional blockchain tooling later via `pip install -r requirements-web3.txt` if you need StorageRegistry calls. Then edit `config.json` with your RPC URL, registry contract, and storage size. Export `PRIVATE_KEY` (or add it to the config) if you want blockchain registration.
   - (Optional) Provision an encrypted sparse volume with `node/scripts/setup_encrypted_volume.sh` and set `storage.mount_path` to the mounted directory so reserved space is visible to the OS and dashboard.
   - Start the provider: `python main.py`. This boots the FastAPI server on port `8000`, begins publishing real disk stats, and serves the dashboard at `http://localhost:8000/ui`.

2. **(Optional) Launch a local chain**
   - From the repo root run `npm run node` to start Hardhat on `localhost:8545`, then `npm run deploy:local` so both the node and dApp have on-chain contracts to talk to.

3. **View stats in the dApp**
   - In another terminal run `cd dapp && npm install && cp .env.example .env`, fill in `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID`, and set the contract addresses you deployed (local or testnet) in `config/networks.ts`.
   - Start the Next.js dev server with `npm run dev` and open `http://localhost:3000`. Connect your wallet (Arbitrum Sepolia or your local Hardhat network) and the dashboard will pull balances, staking data, and the node metrics exposed from `http://localhost:8000`.

## 🧪 Testing

Run the test suite:
```bash
npm test
```

Run tests with coverage:
```bash
npx hardhat coverage
```

## 📖 Contract Overview

### DePINToken Contract

The main contract includes:

#### Functions for Users:
- `stake(uint256 amount)`: Stake tokens to participate in the network
- `unstake(uint256 amount)`: Unstake tokens after lock period
- `claimRewards()`: Claim accumulated staking rewards
- `calculateRewards(address user)`: View pending rewards
- `getStakeInfo(address user)`: Get staking information

#### Functions for Owner:
- `setRewardRate(uint256 newRate)`: Update reward rate
- `setMinimumStakeAmount(uint256 newAmount)`: Update minimum stake
- `setStakingLockPeriod(uint256 newPeriod)`: Update lock period
- `mint(address to, uint256 amount)`: Mint new tokens
- `pause()`: Pause all transfers
- `unpause()`: Unpause transfers

### Staking Mechanism

1. **Stake Tokens**: Users stake tokens to participate in the DePIN network
2. **Earn Rewards**: Stakers earn rewards based on:
   - Amount staked
   - Time staked
   - Reward rate
3. **Lock Period**: Tokens must be staked for a minimum period before unstaking
4. **Claim Rewards**: Users can claim rewards at any time without unstaking
5. **Unstake**: After the lock period, users can unstake their tokens

## 🔐 Security

- Uses OpenZeppelin's battle-tested contracts
- Reentrancy protection on all state-changing functions
- Access control for admin functions
- Pausable functionality for emergency situations
- Comprehensive test coverage

## 🌐 Layer 3 Deployment

This token is designed to be deployed on Layer 2 networks (Arbitrum, Optimism, Base) which can serve as Layer 3 foundations. For true Layer 3 deployment:

1. **Choose an L2 Network**: Select your preferred L2 (Arbitrum, Optimism, or Base)
2. **Deploy on L2**: Deploy the token contract on your chosen L2
3. **L3 Considerations**: If deploying on a true L3 (like Arbitrum Orbit or OP Stack), adjust the network configuration accordingly

### Recommended Networks for DePIN:

- **Arbitrum**: Low fees, high throughput
- **Optimism**: EVM compatible, fast transactions
- **Base**: Coinbase's L2, growing ecosystem
- **Polygon**: Alternative L2 with low fees

## 📊 Tokenomics

### Initial Distribution
- Total Supply: 1,000,000,000 tokens
- Allocated to deployer initially
- Can be distributed to network participants

### Staking Rewards
- Rewards are minted when claimed (inflationary model)
- Reward rate can be adjusted by owner
- Rewards accumulate based on time staked

### Burning
- Tokens can be burned to reduce supply
- Useful for deflationary mechanisms

## 🔧 Customization

### Modify Token Parameters

Edit `scripts/deploy.ts` to change:
- Token name and symbol
- Initial supply
- Reward rate
- Minimum stake amount
- Staking lock period

### Add Custom Features

The contract can be extended with:
- Governance voting
- Multi-signature support
- Advanced reward mechanisms
- Integration with DePIN protocols

## 📚 Resources

- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts)
- [Hardhat Documentation](https://hardhat.org/docs)
- [Ethereum Documentation](https://ethereum.org/en/developers/docs)
- [DePIN Ecosystem](https://depin.org)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This software is provided as-is without warranty. Always audit smart contracts before deploying to mainnet. Use at your own risk.

## 🆘 Support

For issues and questions:
1. Check the documentation
2. Review the test files for usage examples
3. Open an issue on GitHub

## 🎯 Next Steps

After deployment:

1. **Verify Contract**: Verify on block explorer
2. **Distribute Tokens**: Send tokens to network participants
3. **Set Up Frontend**: Create a dApp for users to interact with the token
4. **Monitor**: Monitor contract activity and adjust parameters as needed
5. **Governance**: Consider adding governance mechanisms for decentralized control

## 📈 Roadmap

- [ ] Governance token functionality
- [ ] Multi-chain bridge support
- [ ] Advanced reward mechanisms
- [ ] Integration with DePIN protocols
- [ ] Frontend dApp
- [ ] Mobile app support

---

Built with ❤️ for the DePIN ecosystem



