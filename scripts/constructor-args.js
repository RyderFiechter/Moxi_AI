// Constructor arguments for verification
// Usage: npx hardhat verify --constructor-args scripts/constructor-args.js <contract-address>

module.exports = [
  "Moxi AI",                    // name
  "MOXI",                       // symbol
  "1000000000000000000000000000", // initialSupply (1 billion tokens)
  "1000000000",                 // rewardRate
  "1000000000000000000000",     // minimumStakeAmount (1000 tokens)
  "604800"                      // stakingLockPeriod (7 days in seconds)
];

