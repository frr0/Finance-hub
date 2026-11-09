const BASE_URL = '';

export interface Account {
  id: number;
  name: string;
  type: string;
  currency: string;
  current_balance: number;
  baseline_balance: number;
  last_synced_at?: string;
}

export interface Transaction {
  id: number;
  account_id: number;
  account_name: string;
  date: string;
  amount: number;
  currency: string;
  payee: string;
  description: string;
  category_name?: string;
  transaction_type: string;
  reference_id?: string;
  source_file?: string;
}

export interface RemoteFile {
  filename: string;
  size: number;
  modified_time: number;
}

export interface ReconciliationReport {
  matched_count: number;
  missing_in_statement_count: number;
  missing_in_firefly_count: number;
  amount_mismatch_count: number;
  account_diffs: Array<{
    account_name: string;
    financehub_balance: number;
    firefly_balance: number;
    difference: number;
  }>;
  details: Array<{
    status: string;
    date: string;
    account: string;
    amount: number;
    description: string;
  }>;
}

export interface NetWorthAnalytics {
  net_worth: number;
  assets: number;
  debts: number;
  cash_flow: Array<{
    month: string;
    income: number;
    expense: number;
  }>;
}

export async function fetchAccounts(): Promise<Account[]> {
  const res = await fetch(`${BASE_URL}/api/accounts`);
  if (!res.ok) throw new Error('Failed to fetch accounts');
  return res.json();
}

export async function fetchTransactions(params: {
  accountId?: number;
  search?: string;
  offset?: number;
  limit?: number;
}): Promise<{ total: number; items: Transaction[] }> {
  const query = new URLSearchParams();
  if (params.accountId) query.set('account_id', params.accountId.toString());
  if (params.search) query.set('search', params.search);
  if (params.offset !== undefined) query.set('offset', params.offset.toString());
  if (params.limit !== undefined) query.set('limit', params.limit.toString());

  const res = await fetch(`${BASE_URL}/api/transactions?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch transactions');
  return res.json();
}

export async function uploadFiles(files: File[]): Promise<any> {
  const formData = new FormData();
  files.forEach((f) => formData.append('files', f));
  const res = await fetch(`${BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Failed to upload files');
  return res.json();
}

export async function fetchRemoteFiles(): Promise<RemoteFile[]> {
  const res = await fetch(`${BASE_URL}/api/remote/files`);
  if (!res.ok) throw new Error('Failed to fetch remote files');
  return res.json();
}

export async function triggerSshSync(filenames?: string[]): Promise<any> {
  const res = await fetch(`${BASE_URL}/api/sync/ssh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(filenames || null),
  });
  if (!res.ok) throw new Error('Failed to trigger SSH sync');
  return res.json();
}

export async function fetchReconciliationReport(): Promise<ReconciliationReport> {
  const res = await fetch(`${BASE_URL}/api/reconciliation`);
  if (!res.ok) throw new Error('Failed to fetch reconciliation report');
  return res.json();
}

export async function fetchAnalytics(): Promise<NetWorthAnalytics> {
  const res = await fetch(`${BASE_URL}/api/analytics/net-worth`);
  if (!res.ok) throw new Error('Failed to fetch analytics');
  return res.json();
}
