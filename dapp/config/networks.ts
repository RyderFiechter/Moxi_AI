import { arbitrumSepolia, arbitrum } from 'wagmi/chains';

export const CONTRACT_ADDRESSES = {
  'arbitrum-sepolia': '0x5958641992aFc8feCC2DaB76AfdC5DCa91DB6Ea7',
  'arbitrum': '', // Add mainnet address when deployed
} as const;

export const SUPPORTED_CHAINS = {
  testnet: arbitrumSepolia,
  mainnet: arbitrum,
} as const;

export const TOKEN_INFO = {
  name: 'Moxi AI',
  symbol: 'MOXI',
  decimals: 18,
} as const;

export const STAKING_CONFIG = {
  minimumStake: '1000', // 1000 MOXI
  lockPeriod: 604800, // 7 days in seconds
} as const;

