# dApp Setup Guide

This guide will help you set up and run the Moxi AI dApp locally.

## Quick Start

1. **Navigate to the dApp directory:**
   ```bash
   cd dapp
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and add your WalletConnect Project ID:
   ```
   NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=your_project_id_here
   ```
   
   To get a WalletConnect Project ID:
   - Go to https://cloud.walletconnect.com
   - Sign up or log in
   - Create a new project
   - Copy the Project ID

4. **Run the development server:**
   ```bash
   npm run dev
   ```

5. **Open your browser:**
   Navigate to http://localhost:3000

## Features

- ✅ Connect wallet (MetaMask, WalletConnect, etc.)
- ✅ View token balance
- ✅ Stake tokens
- ✅ Unstake tokens (after lock period)
- ✅ Claim rewards
- ✅ View network statistics
- ✅ Automatic network detection (testnet/mainnet)

## Network Configuration

The dApp automatically detects which network you're connected to:

- **Arbitrum Sepolia (Testnet)**: Chain ID 421614
  - Contract: `0x5958641992aFc8feCC2DaB76AfdC5DCa91DB6Ea7`
  
- **Arbitrum One (Mainnet)**: Chain ID 42161
  - Contract: (Update in `config/networks.ts` when deployed)

## Updating Contract Address

When you deploy to Arbitrum mainnet, update the contract address in `dapp/config/networks.ts`:

```typescript
export const CONTRACT_ADDRESSES = {
  'arbitrum-sepolia': '0x5958641992aFc8feCC2DaB76AfdC5DCa91DB6Ea7',
  'arbitrum': 'YOUR_MAINNET_ADDRESS_HERE', // Add this
} as const;
```

## Building for Production

```bash
npm run build
npm start
```

## Deployment

### Deploy to Vercel (Recommended)

1. Push your code to GitHub
2. Go to [Vercel](https://vercel.com)
3. Import your repository
4. Add environment variable: `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID`
5. Deploy!

### Deploy to Other Platforms

The dApp can be deployed to any platform supporting Next.js:
- Netlify
- AWS Amplify
- Railway
- Your own server

## Troubleshooting

### "Invalid Project ID" Error

Make sure you've set `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID` in your `.env` file and restarted the dev server.

### Contract Not Found

- Ensure you're connected to Arbitrum Sepolia (testnet) or Arbitrum (mainnet)
- Check that the contract address in `config/networks.ts` is correct
- Verify the contract is deployed on the network you're using

### Wallet Connection Issues

- Make sure your wallet is unlocked
- Try disconnecting and reconnecting
- Clear browser cache if issues persist
- Ensure you're on a supported network

### Transaction Failures

- Check you have enough ETH for gas fees
- Verify you have sufficient token balance
- Ensure you meet minimum stake requirements (1000 MOXI)
- Check that the lock period has ended before unstaking

## Development Tips

- The dApp uses React Query for data fetching and caching
- Contract interactions are handled through wagmi hooks
- All contract calls are type-safe using TypeScript
- The UI is responsive and works on mobile devices

## Next Steps

1. Test all features on testnet
2. Deploy to mainnet when ready
3. Update contract address in config
4. Deploy dApp to production
5. Share with your community!

