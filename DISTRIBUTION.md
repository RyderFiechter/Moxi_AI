# Token Distribution Guide

This guide explains how to distribute your DePIN tokens to multiple addresses after deployment.

## Quick Start

1. **Edit the distribution script** (`scripts/distribute.ts`)
2. **Add recipients** with addresses and amounts
3. **Run the distribution script**

## Step-by-Step Instructions

### 1. Edit the Distribution Script

Open `scripts/distribute.ts` and edit the `recipients` array:

```typescript
const recipients: Recipient[] = [
  { address: "0x1234567890123456789012345678901234567890", amount: "10000" }, // 10,000 tokens
  { address: "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd", amount: "5000" },  // 5,000 tokens
  { address: "0x9876543210987654321098765432109876543210", amount: "25000" }, // 25,000 tokens
];
```

**Note:** 
- Amounts are in tokens (not wei)
- The script will automatically convert to wei
- Make sure you have enough tokens in your deployer wallet

### 2. Run the Distribution Script

```bash
# For Arbitrum Sepolia testnet
npx hardhat run scripts/distribute.ts --network arbitrum-sepolia

# For Arbitrum mainnet
npx hardhat run scripts/distribute.ts --network arbitrum

# Or use the npm script
npm run distribute -- --network arbitrum-sepolia
```

### 3. Verify Distribution

The script will:
- Show distribution summary
- Execute transfers
- Display transaction hashes
- Verify final balances
- Show remaining balance

## Distribution Methods

### Method 1: Script-Based Distribution (Recommended)

Use the `distribute.ts` script for:
- Multiple recipients
- Automated distribution
- Transaction tracking
- Error handling

### Method 2: Manual Transfer

You can also transfer tokens manually using:

```bash
npx hardhat run scripts/interact.ts --network arbitrum-sepolia
```

Then use a wallet or dApp to transfer tokens.

### Method 3: Programmatic Distribution

For more complex distributions, you can create a custom script:

```typescript
const token = await ethers.getContractAt("DePINToken", contractAddress);
await token.transfer(recipientAddress, ethers.parseEther("1000"));
```

## Example Use Cases

### Airdrop to Early Supporters

```typescript
const recipients: Recipient[] = [
  { address: "0x...", amount: "1000" },
  { address: "0x...", amount: "1000" },
  // ... more addresses
];
```

### Team Allocation

```typescript
const recipients: Recipient[] = [
  { address: "0x...", amount: "100000" }, // Team member 1
  { address: "0x...", amount: "100000" }, // Team member 2
  // ... more team members
];
```

### Initial Distribution

```typescript
const recipients: Recipient[] = [
  { address: "0x...", amount: "1000000" }, // Large holder
  { address: "0x...", amount: "500000" },  // Medium holder
  // ... more addresses
];
```

## Gas Considerations

- Each transfer requires gas fees
- Arbitrum has low fees (~$0.01-0.10 per transaction)
- The script includes delays to avoid rate limiting
- For large distributions, consider batching

## Safety Tips

1. **Test First**: Always test on testnet first
2. **Verify Addresses**: Double-check all recipient addresses
3. **Check Balances**: Ensure you have enough tokens
4. **Monitor Transactions**: Watch transaction status
5. **Keep Records**: Save distribution logs

## Troubleshooting

### Insufficient Balance

```
❌ Insufficient balance!
Required: 1000000.0 MOXI
Available: 500000.0 MOXI
```

**Solution:** Reduce amounts or mint more tokens (if you're the owner)

### Invalid Address

```
❌ Failed: invalid address
```

**Solution:** Check that addresses are valid Ethereum addresses (42 characters, starts with 0x)

### Transaction Failed

```
❌ Failed: transaction reverted
```

**Solution:** 
- Check gas price
- Verify contract is deployed
- Ensure you have ETH for gas fees
- Check if contract is paused

## Advanced: CSV Import

For large distributions, you can modify the script to read from a CSV file:

```typescript
import * as csv from "csv-parse/sync";

const csvData = fs.readFileSync("recipients.csv", "utf8");
const records = csv.parse(csvData, { columns: true });
const recipients = records.map((row: any) => ({
  address: row.address,
  amount: row.amount,
}));
```

## Security Notes

- Never commit your private key
- Verify recipient addresses before distribution
- Test with small amounts first
- Keep distribution records for accounting
- Consider using a multi-sig wallet for large distributions

## Next Steps

After distribution:
1. Verify balances on block explorer
2. Notify recipients
3. Update documentation
4. Track distribution in your records
5. Consider setting up a vesting schedule for team tokens

---

For questions or issues, refer to the main [README.md](README.md) file.

