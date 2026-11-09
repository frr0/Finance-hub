import React, { useState } from 'react';
import { Transaction, Account } from '../api/client';
import { Search, Filter, ArrowUpRight, ArrowDownRight, ArrowRightLeft } from 'lucide-react';

interface TransactionsLedgerProps {
  transactions: Transaction[];
  accounts: Account[];
  total: number;
  search: string;
  selectedAccountId?: number;
  onSearchChange: (val: string) => void;
  onAccountFilterChange: (id?: number) => void;
}

export const TransactionsLedger: React.FC<TransactionsLedgerProps> = ({
  transactions,
  accounts,
  total,
  search,
  selectedAccountId,
  onSearchChange,
  onAccountFilterChange,
}) => {
  const formatCur = (val: number) => {
    return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(val);
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-4 shadow-lg flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1 min-w-[240px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search payee or description..."
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full bg-slate-900/80 border border-slate-700/80 rounded-lg pl-9 pr-3 py-1.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={selectedAccountId || ''}
            onChange={(e) => onAccountFilterChange(e.target.value ? Number(e.target.value) : undefined)}
            className="bg-slate-900/80 border border-slate-700/80 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="">All Accounts</option>
            {accounts.map((acc) => (
              <option key={acc.id} value={acc.id}>
                {acc.name}
              </option>
            ))}
          </select>
          <span className="text-xs text-slate-400 font-medium">Total: {total} records</span>
        </div>
      </div>

      {/* Table */}
      <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="text-xs uppercase bg-slate-900/80 text-slate-400 border-b border-slate-700">
              <tr>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Account</th>
                <th className="py-3 px-4">Payee / Entity</th>
                <th className="py-3 px-4">Description</th>
                <th className="py-3 px-4 text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/40">
              {transactions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400 text-sm">
                    No transactions matching your criteria.
                  </td>
                </tr>
              ) : (
                transactions.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-700/20">
                    <td className="py-2.5 px-4">
                      {t.transaction_type === 'TRANSFER' ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-purple-400 bg-purple-950/60 px-2 py-0.5 rounded border border-purple-800/60">
                          <ArrowRightLeft className="w-3 h-3" /> Transfer
                        </span>
                      ) : t.amount > 0 ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/60">
                          <ArrowDownRight className="w-3 h-3" /> Income
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-700">
                          <ArrowUpRight className="w-3 h-3 text-rose-400" /> Expense
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-xs text-slate-400">{t.date}</td>
                    <td className="py-2.5 px-4 font-medium text-slate-200">{t.account_name}</td>
                    <td className="py-2.5 px-4 font-semibold text-white">{t.payee}</td>
                    <td className="py-2.5 px-4 text-xs text-slate-400 truncate max-w-xs">{t.description}</td>
                    <td
                      className={`py-2.5 px-4 text-right font-bold ${
                        t.amount > 0 ? 'text-emerald-400' : 'text-slate-100'
                      }`}
                    >
                      {formatCur(t.amount)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
