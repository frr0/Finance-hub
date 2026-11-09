import React, { useState, useEffect } from 'react';
import { fetchReconciliationReport, ReconciliationReport } from '../api/client';
import { GitCompare, CheckCircle2, AlertCircle, FileX, ArrowRightLeft, RefreshCw } from 'lucide-react';

export const ReconciliationView: React.FC = () => {
  const [report, setReport] = useState<ReconciliationReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterTab, setFilterTab] = useState<'ALL' | 'MATCHED' | 'MISSING_IN_FIREFLY' | 'MISSING_IN_STATEMENT'>('ALL');

  const loadReport = async () => {
    try {
      setLoading(true);
      const data = await fetchReconciliationReport();
      setReport(data);
    } catch (err) {
      console.error('Failed to load reconciliation:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, []);

  const formatCur = (val: number) => {
    return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(val);
  };

  const filteredDetails = report
    ? report.details.filter((d) => {
        if (filterTab === 'ALL') return true;
        return d.status === filterTab;
      })
    : [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <GitCompare className="w-6 h-6 text-indigo-400" />
            Firefly III Reconciliation & Verification
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Compares parsed statements directly against historical numbers from your Firefly III database dump.
          </p>
        </div>

        <button
          onClick={loadReport}
          disabled={loading}
          className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-3 py-1.5 rounded-lg text-sm flex items-center gap-2 font-medium"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Diff
        </button>
      </div>

      {/* Metrics Row */}
      {report && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-4 shadow-lg">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Verified Matched</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-emerald-400">{report.matched_count}</div>
            <p className="text-[11px] text-slate-400 mt-1">Identical amount and date in both</p>
          </div>

          <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-4 shadow-lg">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Missing in Firefly</span>
              <AlertCircle className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-amber-400">{report.missing_in_firefly_count}</div>
            <p className="text-[11px] text-slate-400 mt-1">Found in bank statements only</p>
          </div>

          <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-4 shadow-lg">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Missing in Statements</span>
              <FileX className="w-4 h-4 text-rose-400" />
            </div>
            <div className="text-2xl font-bold text-rose-400">{report.missing_in_statement_count}</div>
            <p className="text-[11px] text-slate-400 mt-1">Found in Firefly history only</p>
          </div>

          <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-4 shadow-lg">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Amount Conflicts</span>
              <ArrowRightLeft className="w-4 h-4 text-sky-400" />
            </div>
            <div className="text-2xl font-bold text-white">{report.amount_mismatch_count}</div>
            <p className="text-[11px] text-slate-400 mt-1">Discrepancy on amounts</p>
          </div>
        </div>
      )}

      {/* Account Balances Comparison */}
      {report && report.account_diffs.length > 0 && (
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-6 shadow-lg">
          <h3 className="font-semibold text-white mb-4">Account Balances Comparison Matrix</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs uppercase bg-slate-900/60 text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="py-2.5 px-4">Account</th>
                  <th className="py-2.5 px-4">FinanceHub Balance</th>
                  <th className="py-2.5 px-4">Firefly III Balance</th>
                  <th className="py-2.5 px-4">Delta / Variance</th>
                  <th className="py-2.5 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/40">
                {report.account_diffs.map((diff) => (
                  <tr key={diff.account_name} className="hover:bg-slate-700/20">
                    <td className="py-2.5 px-4 font-medium text-white">{diff.account_name}</td>
                    <td className="py-2.5 px-4 font-semibold">{formatCur(diff.financehub_balance)}</td>
                    <td className="py-2.5 px-4 text-slate-400">{formatCur(diff.firefly_balance)}</td>
                    <td className="py-2.5 px-4">
                      <span className={diff.difference === 0 ? 'text-emerald-400' : 'text-amber-400 font-bold'}>
                        {diff.difference > 0 ? `+${formatCur(diff.difference)}` : formatCur(diff.difference)}
                      </span>
                    </td>
                    <td className="py-2.5 px-4">
                      {Math.abs(diff.difference) < 0.01 ? (
                        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                          PERFECT MATCH
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-950 text-amber-300 border border-amber-800">
                          DIFFERENCE DETECTED
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Transaction Details */}
      <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-6 shadow-lg">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h3 className="font-semibold text-white">Reconciliation Journal Log</h3>
          <div className="flex bg-slate-900/60 p-1 rounded-lg border border-slate-700 text-xs font-medium">
            <button
              onClick={() => setFilterTab('ALL')}
              className={`px-3 py-1 rounded-md transition ${filterTab === 'ALL' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              All
            </button>
            <button
              onClick={() => setFilterTab('MATCHED')}
              className={`px-3 py-1 rounded-md transition ${filterTab === 'MATCHED' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Matched
            </button>
            <button
              onClick={() => setFilterTab('MISSING_IN_FIREFLY')}
              className={`px-3 py-1 rounded-md transition ${filterTab === 'MISSING_IN_FIREFLY' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Missing in Firefly
            </button>
            <button
              onClick={() => setFilterTab('MISSING_IN_STATEMENT')}
              className={`px-3 py-1 rounded-md transition ${filterTab === 'MISSING_IN_STATEMENT' ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Missing in Statements
            </button>
          </div>
        </div>

        <div className="max-h-96 overflow-y-auto border border-slate-700/50 rounded-lg">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="text-xs uppercase bg-slate-900/80 text-slate-400 sticky top-0">
              <tr>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Date</th>
                <th className="py-2.5 px-3">Account</th>
                <th className="py-2.5 px-3">Amount</th>
                <th className="py-2.5 px-3">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/40">
              {filteredDetails.map((d, i) => (
                <tr key={i} className="hover:bg-slate-700/20">
                  <td className="py-2 px-3">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        d.status === 'MATCHED'
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                          : d.status === 'MISSING_IN_FIREFLY'
                          ? 'bg-amber-950 text-amber-300 border border-amber-800'
                          : 'bg-rose-950 text-rose-300 border border-rose-800'
                      }`}
                    >
                      {d.status.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-slate-300 text-xs">{d.date}</td>
                  <td className="py-2 px-3 font-medium text-slate-200">{d.account}</td>
                  <td className={`py-2 px-3 font-semibold ${d.amount > 0 ? 'text-emerald-400' : 'text-slate-200'}`}>
                    {formatCur(d.amount)}
                  </td>
                  <td className="py-2 px-3 text-slate-400 text-xs truncate max-w-xs">{d.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
