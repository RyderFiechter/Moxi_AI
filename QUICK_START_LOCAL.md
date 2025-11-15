# Quick Start Guide - Local Development

## The Problem

Hardhat's default network is **ephemeral** - each script run creates a fresh blockchain. This means:
- Deploy contract → Contract exists
- Run interact script → New blockchain, contract doesn't exist ❌

## Solution: Use Persistent Hardhat Node

### Step 1: Start Hardhat Node (Terminal 1)

```bash
npm run node
```

This starts a persistent Hardhat node on `http://localhost:8545`. Keep this running.

### Step 2: Deploy Contract (Terminal 2)

```bash
npx hardhat run scripts/deploy.ts --network localhost
```

This deploys to the persistent node.

### Step 3: Interact with Contract (Terminal 2)

```bash
npx hardhat run scripts/interact.ts --network localhost
```

Now the contract will be available!

## Alternative: Deploy Each Time

If you don't want to run a persistent node, you can deploy right before interacting:

```bash
# Deploy
npx hardhat run scripts/deploy.ts

# Immediately interact (in same session, contract still exists)
npx hardhat run scripts/interact.ts
```

But this only works if you run both commands in quick succession, as the blockchain state is lost when the script ends.

## Best Practice

For development, always use the persistent node approach:
1. `npm run node` (keep running)
2. Deploy with `--network localhost`
3. Interact with `--network localhost`

This gives you a stable development environment!




