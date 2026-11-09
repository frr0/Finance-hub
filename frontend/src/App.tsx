import React, { useState, useEffect } from 'react';
import {
  fetchAccounts,
  fetchTransactions,
  fetchAnalytics,
  Account,
  Transaction,
  NetWorthAnalytics
} from './api/client';
import { Dashboard } from './components/Dashboard';
import { IngestionCenter } from './components/IngestionCenter';
import { ReconciliationView } from './components/ReconciliationView';
import { TransactionsLedger } from './components/TransactionsLedger';
import { LayoutDashboard, UploadCloud, GitCompare, Receipt, RefreshCw, Sparkles } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'ingestion' | 'reconciliation' | 'transactions'>('dashboard');
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [totalTx, setTotalTx] = useState(0);
  const [analytics, setAnalytics] = useState<NetWorthAnalytics | null>(null);
  const [search, setSearch] = useState('');
  const [selectedAccountId, setSelectedAccountId] = useState<number | undefined>();
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [accs, txRes, ana] = await Promise.all([
        fetchAccounts(),
        fetchTransactions({ accountId: selectedAccountId, search, limit: 50 }),
        fetchAnalytics()
      ]);
      setAccounts(accs);
      setTransactions(txRes.items);
      setTotalTx(txRes.total);
      setAnalytics(ana);
    } catch (err) {
      console.error('Failed to load application data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedAccountId, search]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="bg-slate-900/90 border-b border-slate-800 sticky top-0 z-50 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600/30 p-2 rounded-xl border border-indigo-500/40 text-indigo-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-indigo-400 via-sky-400 to-emerald-400 bg-clip-text text-transparent">
                FinanceHub
              </h1>
              <span className="text-[10px] text-slate-400 tracking-wider uppercase font-semibold">
                Firefly-Inspired Finance Appliance
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center gap-1 bg-slate-950/70 p-1 rounded-xl border border-slate-800/80 text-sm font-medium">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-3.5 py-1.5 rounded-lg flex items-center gap-2 transition ${
                activeTab === 'dashboard'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('ingestion')}
              className={`px-3.5 py-1.5 rounded-lg flex items-center gap-2 transition ${
                activeTab === 'ingestion'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <UploadCloud className="w-4 h-4" />
              Ingestion & Sync
            </button>
            <button
              onClick={() => setActiveTab('reconciliation')}
              className={`px-3.5 py-1.5 rounded-lg flex items-center gap-2 transition ${
                activeTab === 'reconciliation'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <GitCompare className="w-4 h-4" />
              Firefly Diff
            </button>
            <button
              onClick={() => setActiveTab('transactions')}
              className={`px-3.5 py-1.5 rounded-lg flex items-center gap-2 transition ${
                activeTab === 'transactions'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Receipt className="w-4 h-4" />
              Ledger
            </button>
          </nav>

          <button
            onClick={loadData}
            disabled={loading}
            title="Refresh application data"
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        {activeTab === 'dashboard' && (
          <Dashboard accounts={accounts} analytics={analytics} onNavigate={setActiveTab} />
        )}
        {activeTab === 'ingestion' && <IngestionCenter onRefreshData={loadData} />}
        {activeTab === 'reconciliation' && <ReconciliationView />}
        {activeTab === 'transactions' && (
          <TransactionsLedger
            transactions={transactions}
            accounts={accounts}
            total={totalTx}
            search={search}
            selectedAccountId={selectedAccountId}
            onSearchChange={setSearch}
            onAccountFilterChange={setSelectedAccountId}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/40 py-4 text-center text-xs text-slate-400">
        FinanceHub • Inspired by Firefly III • Local Docker Appliance on Port 30095
      </footer>
    </div>
  );
};
export default App;
