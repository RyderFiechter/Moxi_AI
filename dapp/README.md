# Moxi AI dApp

A modern decentralized application (dApp) for interacting with the Moxi AI (MOXI) DePIN token on Arbitrum.

## Features

- 🔐 **Wallet Connection**: Connect with MetaMask, WalletConnect, and other popular wallets
- 💰 **Token Balance**: View your MOXI token balance
- 📊 **Staking**: Stake tokens to earn rewards
- 🎁 **Rewards**: Claim staking rewards
- 📈 **Statistics**: View network-wide statistics
- 🌐 **Multi-Network**: Supports Arbitrum Sepolia (testnet) and Arbitrum (mainnet)

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- A Web3 wallet (MetaMask recommended)

### Installation

1. Install dependencies:
```bash
cd dapp
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env
```

3. Get a WalletConnect Project ID:
   - Go to [WalletConnect Cloud](https://cloud.walletconnect.com)
   - Create a new project
   - Copy your Project ID
   - Add it to `.env` as `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID`

4. Run the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser

## Configuration

### Network Configuration

The dApp automatically detects the network you're connected to:
- **Arbitrum Sepolia** (Testnet): Chain ID 421614
- **Arbitrum One** (Mainnet): Chain ID 42161

Contract addresses are configured in `config/networks.ts`. Update the mainnet address when you deploy to Arbitrum mainnet.

### Contract Addresses

- **Arbitrum Sepolia**: `0x5958641992aFc8feCC2DaB76AfdC5DCa91DB6Ea7`
- **Arbitrum Mainnet**: (Update when deployed)

## Building for Production

```bash
npm run build
npm start
```

## Deployment

### Vercel

1. Push your code to GitHub
2. Import your repository to Vercel
3. Add environment variables in Vercel dashboard
4. Deploy!

### Other Platforms

The dApp can be deployed to any platform that supports Next.js:
- Netlify
- AWS Amplify
- Railway
- Your own server

## Features in Detail

### Staking

- Minimum stake: 1,000 MOXI
- Lock period: 7 days
- Rewards accumulate continuously
- Claim rewards without unstaking

### Wallet Integration

The dApp uses RainbowKit for wallet connection, supporting:
- MetaMask
- WalletConnect
- Coinbase Wallet
- And more...

## Troubleshooting

### "Contract not found" error

- Make sure you're connected to the correct network (Arbitrum Sepolia for testnet)
- Verify the contract address in `config/networks.ts`

### Transaction fails

- Ensure you have enough ETH for gas fees
- Check that you have sufficient token balance
- Verify you're meeting minimum stake requirements

### Wallet connection issues

- Make sure your wallet is unlocked
- Try disconnecting and reconnecting
- Clear browser cache if issues persist

## Development

### Project Structure

```
dapp/
├── app/              # Next.js app directory
│   ├── layout.tsx   # Root layout with providers
│   ├── page.tsx     # Main dashboard page
│   └── globals.css  # Global styles
├── components/       # React components
│   ├── Header.tsx
│   ├── StatsCard.tsx
│   └── StakingCard.tsx
├── config/          # Configuration files
│   ├── networks.ts  # Network and contract config
│   └── wagmi.ts     # Wagmi configuration
└── hooks/           # Custom React hooks
    └── useDePINToken.ts  # Contract interaction hooks
```

### Adding Features

1. Contract interactions: Add to `hooks/useDePINToken.ts`
2. UI components: Add to `components/`
3. Pages: Add to `app/`

## License

MIT

