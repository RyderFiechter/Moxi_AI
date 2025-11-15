'use client';

import { useEffect, useState, useCallback } from 'react';
import { Header } from '@/components/Header';

const NODE_API_BASE =
  process.env.NEXT_PUBLIC_NODE_API_BASE || 'http://localhost:8000';

type NodeStatus = {
  wallet_address: string;
  payment_wallet?: string;
  storage_lending_enabled?: boolean;
  total_storage_gb: number;
  used_storage_gb: number;
  available_storage_gb: number;
  committed_storage_gb?: number;
  total_profit_eth?: number;
  uptime_formatted: string;
  is_online: boolean;
  registry?: {
    registered: boolean;
    registered_storage_gb?: number;
    price_per_gb_eth?: number;
    is_active?: boolean;
    registered_at?: number;
    last_update?: number;
    error?: string;
    message?: string;
  };
};

type NodeConfig = {
  wallet_address: string;
  payment_wallet?: string;
  storage_lending_enabled?: boolean;
};

type RegistryProviderInfo = {
  storageGB: number;
  pricePerGB: string;
  isActive: boolean;
};

type RegistryStatus =
  | {
      registered: true;
      provider_info: RegistryProviderInfo;
    }
  | {
      registered: false;
      message?: string;
      wallet_address?: string;
      error?: string;
    };

type ActionState = 'idle' | 'loading' | 'success' | 'error';

export default function StorageDashboard() {
  const [status, setStatus] = useState<NodeStatus | null>(null);
  const [config, setConfig] = useState<NodeConfig | null>(null);
  const [registryStatus, setRegistryStatus] = useState<RegistryStatus | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);
  const [paymentWalletInput, setPaymentWalletInput] = useState('');
  const [registerStorageInput, setRegisterStorageInput] = useState('');
  const [registerPriceInput, setRegisterPriceInput] = useState('');
  const [actionState, setActionState] = useState<ActionState>('idle');
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const fetchJson = useCallback(async (path: string, init?: RequestInit) => {
    const response = await fetch(`${NODE_API_BASE}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers || {}),
      },
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(
        data?.detail || data?.error || data?.message || 'Request failed'
      );
    }
    return data;
  }, []);

  const loadStatus = useCallback(async () => {
    try {
      const data = await fetchJson('/status', { cache: 'no-store' });
      setStatus(data);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }, [fetchJson]);

  const loadConfig = useCallback(async () => {
    try {
      const data = await fetchJson('/config', { cache: 'no-store' });
      setConfig(data);
      setPaymentWalletInput(data.payment_wallet ?? '');
    } catch (err) {
      // ignore while node starting
    }
  }, [fetchJson]);

  const loadRegistryStatus = useCallback(async () => {
    try {
      const data = await fetchJson('/registry/status', { cache: 'no-store' });
      setRegistryStatus(data);
      if (data.registered) {
        setRegisterStorageInput(String(data.provider_info.storageGB || ''));
        setRegisterPriceInput(
          (Number(data.provider_info.pricePerGB) / 1e18).toFixed(6)
        );
      }
    } catch (err) {
      setRegistryStatus({
        registered: false,
        message: (err as Error).message,
      });
    }
  }, [fetchJson]);

  useEffect(() => {
    loadStatus();
    loadConfig();
    loadRegistryStatus();

    const interval = setInterval(() => {
      loadStatus();
      loadRegistryStatus();
    }, 5000);

    return () => clearInterval(interval);
  }, [loadStatus, loadConfig, loadRegistryStatus]);

  const handleAction = async (fn: () => Promise<unknown>, success: string) => {
    try {
      setActionState('loading');
      setActionMessage(null);
      await fn();
      setActionState('success');
      setActionMessage(success);
      await Promise.all([loadStatus(), loadConfig(), loadRegistryStatus()]);
    } catch (err) {
      setActionState('error');
      setActionMessage((err as Error).message);
    } finally {
      setTimeout(() => setActionState('idle'), 2500);
    }
  };

  const updatePaymentWallet = () =>
    handleAction(async () => {
      if (!paymentWalletInput.startsWith('0x')) {
        throw new Error('Invalid address');
      }
      await fetchJson('/payment-wallet', {
        method: 'PUT',
        body: JSON.stringify({ payment_wallet: paymentWalletInput }),
      });
    }, 'Payment wallet updated');

  const toggleStorageLending = (enabled: boolean) =>
    handleAction(
      () =>
        fetchJson(`/storage-lending/${enabled ? 'enable' : 'disable'}`, {
          method: 'POST',
        }),
      enabled ? 'Storage lending enabled' : 'Storage lending disabled'
    );

  const registerWithRegistry = () =>
    handleAction(async () => {
      const storageGB = parseInt(registerStorageInput, 10);
      const pricePerGB = parseFloat(registerPriceInput);
      if (!storageGB || storageGB <= 0) {
        throw new Error('Enter storage amount');
      }
      if (!pricePerGB || pricePerGB <= 0) {
        throw new Error('Enter price per GB');
      }
      await fetchJson('/registry/register', {
        method: 'POST',
        body: JSON.stringify({
          storage_gb: storageGB,
          price_per_gb_eth: pricePerGB,
        }),
      });
    }, 'Registered with StorageRegistry');

  const updateRegistryStorage = () =>
    handleAction(
      () =>
        fetchJson('/registry/update', {
          method: 'POST',
        }),
      'Storage updated on-chain'
    );

  const activateRegistry = () =>
    handleAction(
      () =>
        fetchJson('/registry/activate', {
          method: 'POST',
        }),
      'Provider activated'
    );

  const deactivateRegistry = () =>
    handleAction(
      () =>
        fetchJson('/registry/deactivate', {
          method: 'POST',
        }),
      'Provider deactivated'
    );

  const actionStateClass =
    actionState === 'loading'
      ? 'text-indigo-600'
      : actionState === 'success'
      ? 'text-green-600'
      : actionState === 'error'
      ? 'text-red-600'
      : 'text-gray-600';

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Storage Provider Dashboard
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Monitor your local storage node and manage blockchain registration.
          </p>
        </div>

        {error && (
          <div className="mb-6 rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-500 dark:bg-red-900/30 dark:text-red-200">
            Unable to connect to storage node API: {error}
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-2">
          {/* Status Card */}
          <section className="rounded-lg border border-gray-200 bg-white p-6 shadow dark:border-gray-700 dark:bg-gray-800">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Node Status
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Real-time metrics from your running storage node.
            </p>

            {status ? (
              <dl className="mt-4 grid grid-cols-1 gap-4 text-sm md:grid-cols-2">
                <div className="rounded-md bg-gray-50 p-3 dark:bg-gray-900/40">
                  <dt className="text-gray-500 dark:text-gray-400">
                    Wallet Address
                  </dt>
                  <dd className="font-mono text-sm text-gray-900 dark:text-gray-100">
                    {status.wallet_address}
                  </dd>
                </div>
                <div className="rounded-md bg-gray-50 p-3 dark:bg-gray-900/40">
                  <dt className="text-gray-500 dark:text-gray-400">
                    Payment Wallet
                  </dt>
                  <dd className="font-mono text-sm text-gray-900 dark:text-gray-100">
                    {status.payment_wallet ?? '—'}
                  </dd>
                </div>
                <div className="rounded-md bg-gray-50 p-3 dark:bg-gray-900/40">
                  <dt className="text-gray-500 dark:text-gray-400">
                    Total Storage
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {status.total_storage_gb.toFixed(2)} GB
                  </dd>
                </div>
                <div className="rounded-md bg-gray-50 p-3 dark:bg-gray-900/40">
                  <dt className="text-gray-500 dark:text-gray-400">
                    Available Storage
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {status.available_storage_gb.toFixed(2)} GB
                  </dd>
                </div>
                {status.registry?.registered && status.registry.registered_storage_gb !== undefined && (
                  <div className="rounded-md bg-blue-50 p-3 dark:bg-blue-900/20">
                    <dt className="text-blue-600 dark:text-blue-400 font-medium">
                      Registered Storage (On-Chain)
                    </dt>
                    <dd className="text-lg font-semibold text-blue-700 dark:text-blue-300">
                      {status.registry.registered_storage_gb.toFixed(2)} GB
                    </dd>
                  </div>
                )}
                {status.committed_storage_gb !== undefined && status.committed_storage_gb > 0 && (
                  <div className="rounded-md bg-amber-50 p-3 dark:bg-amber-900/20">
                    <dt className="text-amber-600 dark:text-amber-400 font-medium">
                      Committed Storage (Unavailable)
                    </dt>
                    <dd className="text-lg font-semibold text-amber-700 dark:text-amber-300">
                      {status.committed_storage_gb.toFixed(2)} GB
                    </dd>
                    <dd className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                      Reserved for storage lending
                    </dd>
                  </div>
                )}
                {status.total_profit_eth !== undefined && (
                  <div className="rounded-md bg-emerald-50 p-3 dark:bg-emerald-900/20">
                    <dt className="text-emerald-600 dark:text-emerald-400 font-medium">
                      Total Profit (ETH)
                    </dt>
                    <dd className="text-lg font-semibold text-emerald-700 dark:text-emerald-300">
                      {status.total_profit_eth.toFixed(6)} ETH
                    </dd>
                    <dd className="text-xs text-emerald-600 dark:text-emerald-400 mt-1">
                      From storage lending
                    </dd>
                  </div>
                )}
                <div className="rounded-md bg-gray-50 p-3 dark:bg-gray-900/40">
                  <dt className="text-gray-500 dark:text-gray-400">Uptime</dt>
                  <dd className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {status.uptime_formatted}
                  </dd>
                </div>
                <div className="rounded-md bg-gray-50 p-3 dark:bg-gray-900/40">
                  <dt className="text-gray-500 dark:text-gray-400">Status</dt>
                  <dd
                    className={`text-sm font-semibold ${
                      status.is_online ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {status.is_online ? 'Online' : 'Offline'}
                  </dd>
                </div>
                <div className="rounded-md bg-gray-50 p-3 dark:bg-gray-900/40">
                  <dt className="text-gray-500 dark:text-gray-400">
                    Storage Lending
                  </dt>
                  <dd className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {status.storage_lending_enabled ? 'Enabled' : 'Disabled'}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                Waiting for node status...
              </p>
            )}
          </section>

          {/* Configuration Card */}
          <section className="rounded-lg border border-gray-200 bg-white p-6 shadow dark:border-gray-700 dark:bg-gray-800">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Node Configuration
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Update local configuration values.
            </p>

            <div className="mt-4 space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Payment Wallet
                </label>
                <input
                  type="text"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
                  placeholder="0x..."
                  value={paymentWalletInput}
                  onChange={(event) => setPaymentWalletInput(event.target.value)}
                />
                <button
                  onClick={updatePaymentWallet}
                  className="mt-2 inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-60"
                  disabled={actionState === 'loading'}
                >
                  Update Payment Wallet
                </button>
              </div>

              <div className="rounded-md border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900/40">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  Storage Lending
                </p>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                  {config?.storage_lending_enabled
                    ? 'Currently offering storage to the network.'
                    : 'Currently opted out of storage lending.'}
                </p>
                <div className="mt-3 flex space-x-3">
                  <button
                    onClick={() => toggleStorageLending(true)}
                    className="inline-flex items-center rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-60"
                    disabled={
                      actionState === 'loading' ||
                      config?.storage_lending_enabled === true
                    }
                  >
                    Enable
                  </button>
                  <button
                    onClick={() => toggleStorageLending(false)}
                    className="inline-flex items-center rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-60"
                    disabled={
                      actionState === 'loading' ||
                      config?.storage_lending_enabled === false
                    }
                  >
                    Disable
                  </button>
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* Registry Section */}
        <section className="mt-6 rounded-lg border border-gray-200 bg-white p-6 shadow dark:border-gray-700 dark:bg-gray-800">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Storage Registry
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Manage on-chain registration with the StorageRegistry contract.
              </p>
            </div>
            {actionMessage && (
              <p className={`text-sm font-medium ${actionStateClass}`}>
                {actionState === 'loading' ? 'Working...' : actionMessage}
              </p>
            )}
          </div>

          <div className="mt-4 grid gap-6 md:grid-cols-2">
            <div>
              <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                Registry Status
              </h4>
              <div className="mt-2 rounded-md border border-gray-200 bg-gray-50 p-4 text-sm dark:border-gray-700 dark:bg-gray-900/40">
                {status?.registry ? (
                  status.registry.registered ? (
                    <div>
                      <p className="font-medium text-green-600 dark:text-green-400">
                        ✅ Registered
                      </p>
                      <p className="mt-2 text-gray-700 dark:text-gray-300">
                        Registered Storage: {status.registry.registered_storage_gb?.toFixed(2) ?? 'N/A'} GB
                      </p>
                      {status.committed_storage_gb !== undefined && status.committed_storage_gb > 0 && (
                        <p className="text-gray-700 dark:text-gray-300">
                          Committed: {status.committed_storage_gb.toFixed(2)} GB
                        </p>
                      )}
                      <p className="text-gray-700 dark:text-gray-300">
                        Price:{' '}
                        {status.registry.price_per_gb_eth?.toFixed(6) ?? 'N/A'}{' '}
                        ETH / GB
                      </p>
                      <p className="text-gray-700 dark:text-gray-300">
                        Status:{' '}
                        {status.registry.is_active ? 'Active' : 'Inactive'}
                      </p>
                    </div>
                  ) : (
                    <div>
                      <p className="font-medium text-amber-600 dark:text-amber-400">
                        ⚠️ Not registered
                      </p>
                      <p className="mt-2 text-gray-700 dark:text-gray-300">
                        {status.registry.message ??
                          'Set registry details in config.json to enable on-chain registration.'}
                      </p>
                    </div>
                  )
                ) : registryStatus ? (
                  registryStatus.registered ? (
                    <div>
                      <p className="font-medium text-green-600 dark:text-green-400">
                        ✅ Registered
                      </p>
                      <p className="mt-2 text-gray-700 dark:text-gray-300">
                        Storage: {registryStatus.provider_info.storageGB} GB
                      </p>
                      <p className="text-gray-700 dark:text-gray-300">
                        Price:{' '}
                        {(
                          Number(registryStatus.provider_info.pricePerGB) /
                          1e18
                        ).toFixed(6)}{' '}
                        ETH / GB
                      </p>
                      <p className="text-gray-700 dark:text-gray-300">
                        Status:{' '}
                        {registryStatus.provider_info.isActive
                          ? 'Active'
                          : 'Inactive'}
                      </p>
                    </div>
                  ) : (
                    <div>
                      <p className="font-medium text-amber-600 dark:text-amber-400">
                        ⚠️ Not registered
                      </p>
                      <p className="mt-2 text-gray-700 dark:text-gray-300">
                        {registryStatus.message ??
                          'Set registry details in config.json to enable on-chain registration.'}
                      </p>
                    </div>
                  )
                ) : (
                  <p className="text-gray-600 dark:text-gray-400">
                    Loading registry status...
                  </p>
                )}
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                Registration Actions
              </h4>
              <div className="mt-2 space-y-4">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Available Storage (GB)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="1"
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
                    value={registerStorageInput}
                    onChange={(event) =>
                      setRegisterStorageInput(event.target.value)
                    }
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Price per GB (ETH)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.001"
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
                    value={registerPriceInput}
                    onChange={(event) =>
                      setRegisterPriceInput(event.target.value)
                    }
                  />
                </div>

                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={registerWithRegistry}
                    className="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-60"
                    disabled={actionState === 'loading'}
                  >
                    Register / Update Offer
                  </button>
                  <button
                    onClick={updateRegistryStorage}
                    className="inline-flex items-center rounded-md bg-gray-200 px-4 py-2 text-sm font-medium text-gray-800 shadow hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2 disabled:opacity-60 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
                    disabled={actionState === 'loading'}
                  >
                    Refresh Storage Now
                  </button>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={activateRegistry}
                    className="inline-flex flex-1 items-center justify-center rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-60"
                    disabled={
                      actionState === 'loading' ||
                      registryStatus?.registered !== true ||
                      registryStatus.provider_info.isActive
                    }
                  >
                    Activate
                  </button>
                  <button
                    onClick={deactivateRegistry}
                    className="inline-flex flex-1 items-center justify-center rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-60"
                    disabled={
                      actionState === 'loading' ||
                      registryStatus?.registered !== true ||
                      !registryStatus.provider_info.isActive
                    }
                  >
                    Deactivate
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

