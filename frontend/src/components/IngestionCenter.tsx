import React, { useState } from 'react';
import { uploadFiles, triggerSshSync, fetchRemoteFiles, RemoteFile } from '../api/client';
import { UploadCloud, Server, RefreshCw, CheckCircle2, AlertTriangle, FileSpreadsheet } from 'lucide-react';

interface IngestionCenterProps {
  onRefreshData: () => void;
}

export const IngestionCenter: React.FC<IngestionCenterProps> = ({ onRefreshData }) => {
  const [remoteFiles, setRemoteFiles] = useState<RemoteFile[]>([]);
  const [selectedRemote, setSelectedRemote] = useState<string[]>([]);
  const [loadingRemote, setLoadingRemote] = useState(false);
  const [syncingSsh, setSyncingSsh] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [syncResults, setSyncResults] = useState<any[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleListRemote = async () => {
    try {
      setLoadingRemote(true);
      setErrorMsg(null);
      const files = await fetchRemoteFiles();
      setRemoteFiles(files);
      setSelectedRemote(files.map((f) => f.filename));
    } catch (err: any) {
      setErrorMsg(err.message || 'Error listing remote SSH files');
    } finally {
      setLoadingRemote(false);
    }
  };

  const handleRunSshSync = async () => {
    try {
      setSyncingSsh(true);
      setErrorMsg(null);
      const res = await triggerSshSync(selectedRemote.length > 0 ? selectedRemote : undefined);
      setSyncResults(res.results || []);
      onRefreshData();
    } catch (err: any) {
      setErrorMsg(err.message || 'Error syncing from SSH');
    } finally {
      setSyncingSsh(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    try {
      setUploading(true);
      setErrorMsg(null);
      const fileList = Array.from(e.target.files);
      const res = await uploadFiles(fileList);
      setSyncResults(res.results || []);
      onRefreshData();
    } catch (err: any) {
      setErrorMsg(err.message || 'Error uploading files');
    } finally {
      setUploading(false);
    }
  };

  const toggleSelectRemote = (fn: string) => {
    if (selectedRemote.includes(fn)) {
      setSelectedRemote(selectedRemote.filter((f) => f !== fn));
    } else {
      setSelectedRemote([...selectedRemote, fn]);
    }
  };

  return (
    <div className="space-y-8">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* SSH Section */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-6 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 text-indigo-400 mb-3">
              <Server className="w-6 h-6" />
              <h3 className="text-lg font-semibold text-white">Remote SSH Ingestion</h3>
            </div>
            <p className="text-sm text-slate-300 mb-2">
              Pull files directly from <code className="bg-slate-900 px-2 py-0.5 rounded text-indigo-300">192.168.1.185</code> at{' '}
              <code className="bg-slate-900 px-2 py-0.5 rounded text-indigo-300">~/Scaricati/robe/Scaricati</code>.
            </p>
            <p className="text-xs text-slate-400">
              Auto-parses BBVA, Amex, Revolut, Satispay, Directa, and PayPal exports with zero manual formatting.
            </p>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <button
              onClick={handleListRemote}
              disabled={loadingRemote}
              className="bg-slate-700 hover:bg-slate-600 text-white font-medium px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loadingRemote ? 'animate-spin' : ''}`} />
              {loadingRemote ? 'Scanning...' : 'Scan Remote Files'}
            </button>

            <button
              onClick={handleRunSshSync}
              disabled={syncingSsh}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition disabled:opacity-50 shadow-md shadow-indigo-600/20"
            >
              <Server className="w-4 h-4" />
              {syncingSsh ? 'Ingesting from SSH...' : 'Sync All Selected'}
            </button>
          </div>
        </div>

        {/* Local Web Upload */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-6 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 text-emerald-400 mb-3">
              <UploadCloud className="w-6 h-6" />
              <h3 className="text-lg font-semibold text-white">Manual File Upload</h3>
            </div>
            <p className="text-sm text-slate-300 mb-2">
              Upload bank exports (<code className="bg-slate-900 px-2 py-0.5 rounded text-emerald-300">.csv, .xlsx, .xls</code>) directly from your browser.
            </p>
            <p className="text-xs text-slate-400">
              The engine automatically skips preamble lines, standardizes commas/decimals, and cleans emojis.
            </p>
          </div>

          <div className="mt-6">
            <label className="cursor-pointer bg-emerald-600 hover:bg-emerald-500 text-white font-medium px-4 py-2 rounded-lg text-sm inline-flex items-center gap-2 transition shadow-md shadow-emerald-600/20">
              <UploadCloud className="w-4 h-4" />
              {uploading ? 'Processing files...' : 'Select & Upload Files'}
              <input
                type="file"
                multiple
                accept=".csv,.xlsx,.xls"
                onChange={handleFileUpload}
                className="hidden"
                disabled={uploading}
              />
            </label>
          </div>
        </div>
      </div>

      {/* Error alert */}
      {errorMsg && (
        <div className="bg-rose-950/60 border border-rose-800/80 text-rose-200 px-4 py-3 rounded-xl flex items-center gap-3 text-sm">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Results Banner */}
      {syncResults.length > 0 && (
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-6 shadow-lg">
          <h4 className="font-semibold text-white mb-3 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" /> Ingestion Results
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs uppercase bg-slate-900/60 text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="py-2 px-3">File</th>
                  <th className="py-2 px-3">Detected Bank</th>
                  <th className="py-2 px-3">Imported</th>
                  <th className="py-2 px-3">Skipped (Duplicates)</th>
                  <th className="py-2 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {syncResults.map((r, i) => (
                  <tr key={i} className="hover:bg-slate-700/30">
                    <td className="py-2 px-3 font-medium text-slate-200">{r.filename}</td>
                    <td className="py-2 px-3 text-indigo-300">{r.bank || 'Unknown'}</td>
                    <td className="py-2 px-3 text-emerald-400 font-bold">{r.imported}</td>
                    <td className="py-2 px-3 text-slate-400">{r.skipped}</td>
                    <td className="py-2 px-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        r.status === 'SUCCESS' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-slate-700 text-slate-300'
                      }`}>
                        {r.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Remote Files Table */}
      {remoteFiles.length > 0 && (
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-semibold text-white flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-indigo-400" />
              Discovered Files on Remote Server ({remoteFiles.length})
            </h4>
            <div className="space-x-2">
              <button
                onClick={() => setSelectedRemote(remoteFiles.map((f) => f.filename))}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
              >
                Select All
              </button>
              <span className="text-slate-600">|</span>
              <button
                onClick={() => setSelectedRemote([])}
                className="text-xs text-slate-400 hover:text-slate-300 font-medium"
              >
                Deselect All
              </button>
            </div>
          </div>

          <div className="max-h-96 overflow-y-auto border border-slate-700/50 rounded-lg">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs uppercase bg-slate-900/80 text-slate-400 sticky top-0">
                <tr>
                  <th className="py-2 px-3 w-10">Sync</th>
                  <th className="py-2 px-3">Filename</th>
                  <th className="py-2 px-3">Size</th>
                  <th className="py-2 px-3">Last Modified</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/40">
                {remoteFiles.map((rf) => (
                  <tr key={rf.filename} className="hover:bg-slate-700/30">
                    <td className="py-2 px-3">
                      <input
                        type="checkbox"
                        checked={selectedRemote.includes(rf.filename)}
                        onChange={() => toggleSelectRemote(rf.filename)}
                        className="rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                      />
                    </td>
                    <td className="py-2 px-3 font-medium text-slate-200">{rf.filename}</td>
                    <td className="py-2 px-3 text-slate-400">{(rf.size / 1024).toFixed(1)} KB</td>
                    <td className="py-2 px-3 text-slate-400">
                      {rf.modified_time ? new Date(rf.modified_time * 1000).toLocaleString() : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
