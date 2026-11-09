import React from 'react';
import { Account, NetWorthAnalytics } from '../api/client';
import { Wallet, TrendingUp, TrendingDown, Landmark, ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface DashboardProps {
  accounts: Account[];
  analytics: NetWorthAnalytics | null;
  onNavigate: (tab: 'dashboard' | 'ingestion' | 'reconciliation' | 'transactions') => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ accounts, analytics, onNavigate }) => {
  const formatCur = (val: number) => {
    return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(val);
  };

  return (
    <div className="space-y-8">
      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-sm font-medium">Net Worth</span>
            <Wallet className="w-5 h-5 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {formatCur(analytics ? analytics.net_worth : 0)}
          </div>
          <p className="text-xs text-slate-400 mt-2">Combined balance across all tracked accounts</p>
        </div>

        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-sm font-medium">Total Assets</span>
            <TrendingUp className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">
            {formatCur(analytics ? analytics.assets : 0)}
          </div>
          <p className="text-xs text-slate-400 mt-2">Checking, savings & investment portfolios</p>
        </div>

        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-sm font-medium">Liabilities / Credit</span>
            <TrendingDown className="w-5 h-5 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400">
            {formatCur(analytics ? analytics.debts : 0)}
          </div>
          <p className="text-xs text-slate-400 mt-2">Outstanding cards & negative balances</p>
        </div>

        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-sm font-medium">Active Accounts</span>
            <Landmark className="w-5 h-5 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-white">{accounts.length}</div>
          <button
            onClick={() => onNavigate('ingestion')}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium mt-2 flex items-center gap-1"
          >
            Import new files <ArrowUpRight className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Cash Flow Bars */}
      {analytics && analytics.cash_flow && analytics.cash_flow.length > 0 && (
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-6 shadow-lg">
          <h3 className="text-lg font-semibold text-white mb-4">Monthly Cash Flow</h3>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            {analytics.cash_flow.map((m) => (
              <div key={m.month} className="bg-slate-900/60 border border-slate-700/40 rounded-lg p-3 text-center">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{m.month}</span>
                <div className="mt-2 space-y-1">
                  <div className="text-xs text-emerald-400 flex items-center justify-center gap-1 font-medium">
                    <ArrowDownRight className="w-3 h-3" /> +{formatCur(m.income)}
                  </div>
                  <div className="text-xs text-rose-400 flex items-center justify-center gap-1 font-medium">
                    <ArrowUpRight className="w-3 h-3" /> -{formatCur(m.expense)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Accounts Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Your Bank & Investment Accounts</h3>
          <span className="text-xs text-slate-400">Synced from statements and SSH remote</span>
        </div>
        {accounts.length === 0 ? (
          <div className="bg-slate-800/40 border border-dashed border-slate-700 rounded-xl p-8 text-center text-slate-400">
            No accounts imported yet. Head over to the{' '}
            <button onClick={() => onNavigate('ingestion')} className="text-indigo-400 underline font-medium">
              Ingestion Center
            </button>{' '}
            to upload your bank files or pull them from SSH!
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {accounts.map((acc) => (
              <div
                key={acc.id}
                className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 hover:border-indigo-500/50 transition duration-200"
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-slate-100">{acc.name}</h4>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-700/60 text-slate-300">
                    {acc.type}
                  </span>
                </div>
                <div className="text-xl font-bold text-slate-100 mb-2">
                  {formatCur(acc.current_balance)}
                </div>
                <div className="text-xs text-slate-400 flex items-center justify-between border-t border-slate-700/40 pt-2 mt-3">
                  <span>Currency: {acc.currency}</span>
                  <span>{acc.last_synced_at ? new Date(acc.last_synced_at).toLocaleDateString() : 'Baseline'}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
