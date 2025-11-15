import { useReadContract, useWriteContract, useWaitForTransactionReceipt } from 'wagmi';
import { parseEther, formatEther } from 'viem';
import { CONTRACT_ADDRESSES, TOKEN_INFO } from '@/config/networks';
import { useChainId } from 'wagmi';

// ABI for DePINToken contract (key functions)
const DEPIN_TOKEN_ABI = [
  {
    inputs: [],
    name: 'name',
    outputs: [{ internalType: 'string', name: '', type: 'string' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [],
    name: 'symbol',
    outputs: [{ internalType: 'string', name: '', type: 'string' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [{ internalType: 'address', name: 'account', type: 'address' }],
    name: 'balanceOf',
    outputs: [{ internalType: 'uint256', name: '', type: 'uint256' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [],
    name: 'totalSupply',
    outputs: [{ internalType: 'uint256', name: '', type: 'uint256' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [],
    name: 'totalStaked',
    outputs: [{ internalType: 'uint256', name: '', type: 'uint256' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [],
    name: 'rewardRate',
    outputs: [{ internalType: 'uint256', name: '', type: 'uint256' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [],
    name: 'minimumStakeAmount',
    outputs: [{ internalType: 'uint256', name: '', type: 'uint256' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [],
    name: 'stakingLockPeriod',
    outputs: [{ internalType: 'uint256', name: '', type: 'uint256' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [{ internalType: 'address', name: 'user', type: 'address' }],
    name: 'getStakeInfo',
    outputs: [
      { internalType: 'uint256', name: 'amount', type: 'uint256' },
      { internalType: 'uint256', name: 'stakedAt', type: 'uint256' },
      { internalType: 'uint256', name: 'lastRewardClaimed', type: 'uint256' },
      { internalType: 'uint256', name: 'pendingRewards', type: 'uint256' },
      { internalType: 'bool', name: 'isActive', type: 'bool' },
    ],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [{ internalType: 'address', name: 'user', type: 'address' }],
    name: 'calculateRewards',
    outputs: [{ internalType: 'uint256', name: '', type: 'uint256' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [],
    name: 'getStakerCount',
    outputs: [{ internalType: 'uint256', name: '', type: 'uint256' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [{ internalType: 'uint256', name: 'amount', type: 'uint256' }],
    name: 'stake',
    outputs: [],
    stateMutability: 'nonpayable',
    type: 'function',
  },
  {
    inputs: [{ internalType: 'uint256', name: 'amount', type: 'uint256' }],
    name: 'unstake',
    outputs: [],
    stateMutability: 'nonpayable',
    type: 'function',
  },
  {
    inputs: [],
    name: 'claimRewards',
    outputs: [],
    stateMutability: 'nonpayable',
    type: 'function',
  },
  {
    inputs: [
      { internalType: 'address', name: 'to', type: 'address' },
      { internalType: 'uint256', name: 'amount', type: 'uint256' }],
    name: 'transfer',
    outputs: [{ internalType: 'bool', name: '', type: 'bool' }],
    stateMutability: 'nonpayable',
    type: 'function',
  },
] as const;

export function useContractAddress() {
  const chainId = useChainId();
  const isTestnet = chainId === 421614; // Arbitrum Sepolia
  return CONTRACT_ADDRESSES[isTestnet ? 'arbitrum-sepolia' : 'arbitrum'] || CONTRACT_ADDRESSES['arbitrum-sepolia'];
}

export function useDePINToken() {
  const contractAddress = useContractAddress();

  return {
    contractAddress,
    abi: DEPIN_TOKEN_ABI,
  };
}

export function useTokenBalance(address?: `0x${string}`) {
  const { contractAddress, abi } = useDePINToken();
  const { data, isLoading, refetch } = useReadContract({
    address: contractAddress as `0x${string}`,
    abi,
    functionName: 'balanceOf',
    args: address ? [address] : undefined,
    query: {
      enabled: !!address,
    },
  });

  return {
    balance: data ? formatEther(data) : '0',
    rawBalance: data,
    isLoading,
    refetch,
  };
}

export function useStakeInfo(address?: `0x${string}`) {
  const { contractAddress, abi } = useDePINToken();
  const { data, isLoading, refetch } = useReadContract({
    address: contractAddress as `0x${string}`,
    abi,
    functionName: 'getStakeInfo',
    args: address ? [address] : undefined,
    query: {
      enabled: !!address,
    },
  });

  return {
    stakeInfo: data
      ? {
          amount: formatEther(data[0]),
          stakedAt: Number(data[1]),
          lastRewardClaimed: Number(data[2]),
          pendingRewards: formatEther(data[3]),
          isActive: data[4],
        }
      : null,
    isLoading,
    refetch,
  };
}

export function useContractStats() {
  const { contractAddress, abi } = useDePINToken();
  
  const { data: totalStaked } = useReadContract({
    address: contractAddress as `0x${string}`,
    abi,
    functionName: 'totalStaked',
  });

  const { data: stakerCount } = useReadContract({
    address: contractAddress as `0x${string}`,
    abi,
    functionName: 'getStakerCount',
  });

  const { data: totalSupply } = useReadContract({
    address: contractAddress as `0x${string}`,
    abi,
    functionName: 'totalSupply',
  });

  return {
    totalStaked: totalStaked ? formatEther(totalStaked) : '0',
    stakerCount: stakerCount?.toString() || '0',
    totalSupply: totalSupply ? formatEther(totalSupply) : '0',
  };
}

export function useStake() {
  const { contractAddress, abi } = useDePINToken();
  const { writeContract, data: hash, isPending } = useWriteContract();
  const { isLoading: isConfirming, isSuccess } = useWaitForTransactionReceipt({
    hash,
  });

  const stake = (amount: string) => {
    writeContract({
      address: contractAddress as `0x${string}`,
      abi,
      functionName: 'stake',
      args: [parseEther(amount)],
    });
  };

  return {
    stake,
    hash,
    isPending,
    isConfirming,
    isSuccess,
  };
}

export function useUnstake() {
  const { contractAddress, abi } = useDePINToken();
  const { writeContract, data: hash, isPending } = useWriteContract();
  const { isLoading: isConfirming, isSuccess } = useWaitForTransactionReceipt({
    hash,
  });

  const unstake = (amount: string) => {
    writeContract({
      address: contractAddress as `0x${string}`,
      abi,
      functionName: 'unstake',
      args: [parseEther(amount)],
    });
  };

  return {
    unstake,
    hash,
    isPending,
    isConfirming,
    isSuccess,
  };
}

export function useClaimRewards() {
  const { contractAddress, abi } = useDePINToken();
  const { writeContract, data: hash, isPending } = useWriteContract();
  const { isLoading: isConfirming, isSuccess } = useWaitForTransactionReceipt({
    hash,
  });

  const claimRewards = () => {
    writeContract({
      address: contractAddress as `0x${string}`,
      abi,
      functionName: 'claimRewards',
    });
  };

  return {
    claimRewards,
    hash,
    isPending,
    isConfirming,
    isSuccess,
  };
}

