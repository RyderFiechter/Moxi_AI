'use client';

import { useAccount } from 'wagmi';
import { Header } from '@/components/Header';
import { StatsCard } from '@/components/StatsCard';
import { StakingCard } from '@/components/StakingCard';
import { useContractStats, useTokenBalance, useStakeInfo } from '@/hooks/useDePINToken';
import { TOKEN_INFO } from '@/config/networks';
import { Coins, Users, TrendingUp } from 'lucide-react';

export default function Home() {
  const { address, isConnected } = useAccount();
  const { totalStaked, stakerCount, totalSupply } = useContractStats();
  const { balance } = useTokenBalance(address);
  const { stakeInfo } = useStakeInfo(address);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatsCard
            title="Total Supply"
            value={`${parseFloat(totalSupply).toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
            subtitle={TOKEN_INFO.symbol}
            icon={<Coins className="w-8 h-8" />}
          />
          <StatsCard
            title="Total Staked"
            value={`${parseFloat(totalStaked).toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
            subtitle={TOKEN_INFO.symbol}
            icon={<TrendingUp className="w-8 h-8" />}
          />
          <StatsCard
            title="Active Stakers"
            value={parseInt(stakerCount).toLocaleString()}
            subtitle="Network participants"
            icon={<Users className="w-8 h-8" />}
          />
        </div>

        {/* User Stats */}
        {isConnected && address && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <StatsCard
              title="Your Balance"
              value={`${parseFloat(balance).toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
              subtitle={TOKEN_INFO.symbol}
            />
            {stakeInfo?.isActive && (
              <StatsCard
                title="Your Staked"
                value={`${parseFloat(stakeInfo.amount).toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
                subtitle={`${parseFloat(stakeInfo.pendingRewards).toLocaleString(undefined, { maximumFractionDigits: 4 })} rewards pending`}
              />
            )}
          </div>
        )}

        {/* Staking Interface */}
        <StakingCard />

        {/* Info Section */}
        <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            About Staking
          </h2>
          <div className="prose dark:prose-invert max-w-none">
            <ul className="list-disc list-inside space-y-2 text-gray-700 dark:text-gray-300">
              <li>Stake your {TOKEN_INFO.symbol} tokens to participate in the DePIN network</li>
              <li>Earn rewards based on the amount and duration of your stake</li>
              <li>Minimum stake: 1,000 {TOKEN_INFO.symbol}</li>
              <li>Lock period: 7 days (tokens must remain staked for this period)</li>
              <li>Claim rewards at any time without unstaking</li>
              <li>Unstake after the lock period ends</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}

