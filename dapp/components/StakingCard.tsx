'use client';

import { useState } from 'react';
import { useAccount } from 'wagmi';
import { useStakeInfo, useStake, useUnstake, useClaimRewards, useTokenBalance } from '@/hooks/useDePINToken';
import { TOKEN_INFO, STAKING_CONFIG } from '@/config/networks';
import { formatEther, parseEther } from 'viem';

export function StakingCard() {
  const { address } = useAccount();
  const { balance, refetch: refetchBalance } = useTokenBalance(address);
  const { stakeInfo, refetch: refetchStake } = useStakeInfo(address);
  const { stake, isPending: isStaking, isSuccess: stakeSuccess } = useStake();
  const { unstake, isPending: isUnstaking, isSuccess: unstakeSuccess } = useUnstake();
  const { claimRewards, isPending: isClaiming, isSuccess: claimSuccess } = useClaimRewards();

  const [stakeAmount, setStakeAmount] = useState('');
  const [unstakeAmount, setUnstakeAmount] = useState('');

  // Refetch on success
  if (stakeSuccess || unstakeSuccess || claimSuccess) {
    refetchBalance();
    refetchStake();
  }

  const canUnstake = stakeInfo?.isActive && stakeInfo.stakedAt
    ? Date.now() / 1000 >= stakeInfo.stakedAt + STAKING_CONFIG.lockPeriod
    : false;

  const lockEndDate = stakeInfo?.stakedAt
    ? new Date((stakeInfo.stakedAt + STAKING_CONFIG.lockPeriod) * 1000)
    : null;

  if (!address) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
        <p className="text-center text-gray-500 dark:text-gray-400">
          Please connect your wallet to view staking options
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Staking
      </h2>

      {/* Current Balance */}
      <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
        <p className="text-sm text-gray-600 dark:text-gray-400">Your Balance</p>
        <p className="text-2xl font-bold text-gray-900 dark:text-white">
          {parseFloat(balance).toLocaleString(undefined, { maximumFractionDigits: 2 })} {TOKEN_INFO.symbol}
        </p>
      </div>

      {/* Active Stake Info */}
      {stakeInfo?.isActive && (
        <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
            Active Stake
          </h3>
          <div className="space-y-1 text-sm">
            <p className="text-gray-700 dark:text-gray-300">
              Staked: <span className="font-semibold">{parseFloat(stakeInfo.amount).toLocaleString(undefined, { maximumFractionDigits: 2 })} {TOKEN_INFO.symbol}</span>
            </p>
            <p className="text-gray-700 dark:text-gray-300">
              Pending Rewards: <span className="font-semibold text-green-600 dark:text-green-400">
                {parseFloat(stakeInfo.pendingRewards).toLocaleString(undefined, { maximumFractionDigits: 4 })} {TOKEN_INFO.symbol}
              </span>
            </p>
            {lockEndDate && (
              <p className="text-gray-700 dark:text-gray-300">
                Lock Ends: <span className="font-semibold">{lockEndDate.toLocaleString()}</span>
              </p>
            )}
            {!canUnstake && lockEndDate && (
              <p className="text-orange-600 dark:text-orange-400 text-xs mt-2">
                ⏳ You can unstake after the lock period ends
              </p>
            )}
          </div>
        </div>
      )}

      {/* Stake Section */}
      {!stakeInfo?.isActive && (
        <div className="mb-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
            Stake Tokens
          </h3>
          <div className="flex gap-2">
            <input
              type="number"
              value={stakeAmount}
              onChange={(e) => setStakeAmount(e.target.value)}
              placeholder={`Min: ${STAKING_CONFIG.minimumStake} ${TOKEN_INFO.symbol}`}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
            />
            <button
              onClick={() => {
                if (stakeAmount) {
                  stake(stakeAmount);
                  setStakeAmount('');
                }
              }}
              disabled={isStaking || !stakeAmount || parseFloat(stakeAmount) < parseFloat(STAKING_CONFIG.minimumStake)}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isStaking ? 'Staking...' : 'Stake'}
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Minimum stake: {STAKING_CONFIG.minimumStake} {TOKEN_INFO.symbol}
          </p>
        </div>
      )}

      {/* Unstake Section */}
      {stakeInfo?.isActive && canUnstake && (
        <div className="mb-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
            Unstake Tokens
          </h3>
          <div className="flex gap-2">
            <input
              type="number"
              value={unstakeAmount}
              onChange={(e) => setUnstakeAmount(e.target.value)}
              placeholder={`Max: ${parseFloat(stakeInfo.amount).toFixed(2)} ${TOKEN_INFO.symbol}`}
              max={stakeInfo.amount}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
            />
            <button
              onClick={() => {
                if (unstakeAmount) {
                  unstake(unstakeAmount);
                  setUnstakeAmount('');
                }
              }}
              disabled={isUnstaking || !unstakeAmount || parseFloat(unstakeAmount) > parseFloat(stakeInfo.amount)}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUnstaking ? 'Unstaking...' : 'Unstake'}
            </button>
          </div>
        </div>
      )}

      {/* Claim Rewards */}
      {stakeInfo?.isActive && parseFloat(stakeInfo.pendingRewards) > 0 && (
        <div className="mb-6">
          <button
            onClick={() => claimRewards()}
            disabled={isClaiming}
            className="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
          >
            {isClaiming ? 'Claiming...' : `Claim ${parseFloat(stakeInfo.pendingRewards).toLocaleString(undefined, { maximumFractionDigits: 4 })} ${TOKEN_INFO.symbol} Rewards`}
          </button>
        </div>
      )}
    </div>
  );
}

