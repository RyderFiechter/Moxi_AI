kill # Manual Verification Steps for Arbiscan

## Quick Steps

### 1. Go to Verification Page
https://sepolia.arbiscan.io/verifycontract?a=0x1629161cc7BDD3f51428CfE1bC1b8cb54FdaDdFD

### 2. Select "Via Standard JSON Input"

### 3. Fill in the Form

**Contract Address:**
```
0x1629161cc7BDD3f51428CfE1bC1b8cb54FdaDdFD
```

**Compiler Type:**
```
Solidity (Standard JSON Input)
```

**Compiler Version:**
```
v0.8.20+commit.a1b79de6
```

**License:**
```
MIT License (MIT)
```

**Standard JSON Input:**
- Open the file `standard-json-input.json` in your project
- Copy the **entire contents** (it's a large JSON object)
- Paste it into the "Standard JSON Input" field

**Contract Name:**
```
DePINToken
```

**Constructor Arguments (comma-separated):**
```
"Moxi AI","MOXI",1000000000000000000000000000,1000000000,1000000000000000000000,604800
```

### 4. Click "Verify and Publish"

## If You Don't Have standard-json-input.json

Run this command to generate it:
```bash
node scripts/get-verification-input.js
```

This will create `standard-json-input.json` in your project root.

## Alternative: Try "Via Metadata JSON"

If "Via Standard JSON Input" doesn't work, try:
1. Select "Via Metadata JSON"
2. Upload the metadata JSON file from: `artifacts/contracts/DePINToken.sol/DePINToken.metadata.json`
3. Enter constructor arguments as above

## Troubleshooting

### Error: "Invalid JSON"
- Make sure you copied the entire JSON file
- Don't modify the JSON
- Check for any extra characters

### Error: "Constructor arguments mismatch"
- Use exact format: `"Moxi AI","MOXI",1000000000000000000000000000,1000000000,1000000000000000000000,604800`
- Strings in quotes, numbers without quotes
- No spaces after commas

### Error: "Compiler version mismatch"
- Use exactly: `v0.8.20+commit.a1b79de6`
- Make sure optimization was enabled (200 runs)

