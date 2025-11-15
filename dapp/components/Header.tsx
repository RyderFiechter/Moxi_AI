'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ConnectButton } from '@rainbow-me/rainbowkit';
import { TOKEN_INFO } from '@/config/networks';

const NAV_ITEMS = [
  { href: '/', label: 'Staking' },
  { href: '/storage', label: 'Storage' },
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="bg-white dark:bg-gray-900 shadow-sm border-b border-gray-200 dark:border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {TOKEN_INFO.name}
              </h1>
              <span className="ml-2 inline-flex items-center px-2 py-1 text-xs font-semibold text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 rounded">
                {TOKEN_INFO.symbol}
              </span>
            </div>
            <nav className="ml-8 flex space-x-1">
              {NAV_ITEMS.map(({ href, label }) => {
                const isActive = pathname === href;
                return (
                  <Link
                    key={href}
                    href={href}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-indigo-600 text-white dark:bg-indigo-500'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-white dark:hover:bg-gray-800'
                    }`}
                  >
                    {label}
                  </Link>
                );
              })}
            </nav>
          </div>
          <ConnectButton />
        </div>
      </div>
    </header>
  );
}

