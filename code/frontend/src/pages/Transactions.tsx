import { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { FinancialEvent } from '../types';
import { Loader2, Search, ChevronDown, ChevronUp, Download } from 'lucide-react';

export function Transactions() {
  const [transactions, setTransactions] = useState<FinancialEvent[]>([]);
  const [filtered, setFiltered] = useState<FinancialEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [sortColumn, setSortColumn] = useState<keyof FinancialEvent>('event_date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [userId] = useState('user_27');

  useEffect(() => {
    loadTransactions();
  }, [userId]);

  useEffect(() => {
    applyFilters();
  }, [transactions, search, typeFilter, categoryFilter, sortColumn, sortDirection]);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      await api.getUserOverview(userId);
      // Generate mock transactions from events
      // In a real app, this would call a transactions endpoint
      setTransactions([]);
    } catch (err) {
      // Silently fail for demo
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let result = [...transactions];

    if (search) {
      const s = search.toLowerCase();
      result = result.filter(t => 
        (t.description || '').toLowerCase().includes(s) ||
        (t.linked_event_id || '').toLowerCase().includes(s)
      );
    }

    if (typeFilter !== 'all') {
      result = result.filter(t => t.event_type === typeFilter);
    }

    if (categoryFilter !== 'all') {
      result = result.filter(t => t.description === categoryFilter);
    }

    result.sort((a, b) => {
      const aVal = a[sortColumn] ?? '';
      const bVal = b[sortColumn] ?? '';
      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    setFiltered(result);
  };

  const handleSort = (col: string) => {
    if (sortColumn === col) {
      setSortDirection(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(col as keyof FinancialEvent);
      setSortDirection('desc');
    }
  };

  const totalPages = Math.ceil(filtered.length / 20);
  const paginated = filtered.slice((page - 1) * 20, page * 20);

  const categories = [...new Set(transactions.map(t => t.description))].sort();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-12 h-12 text-green-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Transactions</h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">View and filter your financial transactions</p>
        </div>
        <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2">
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search transactions..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-4 py-2 pl-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
            />
          </div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
          >
            <option value="all">All Types</option>
            <option value="income">Income</option>
            <option value="expense">Expense</option>
          </select>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
          >
            <option value="all">All Categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Showing {filtered.length} of {transactions.length} transactions
        </p>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700/50">
              <tr>
                {[
                  { key: 'event_date', label: 'Date' },
                  { key: 'event_type', label: 'Type' },
                  { key: 'description', label: 'Category' },
                  { key: 'amount', label: 'Amount' },
                  { key: 'currency', label: 'Currency' },
                  { key: 'linked_event_id', label: 'Linked Event' },
                ].map(col => (
                  <th
                    key={col.key}
                    className="px-4 py-3 text-left text-gray-500 dark:text-gray-400 font-medium cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={() => handleSort(col.key)}
                  >
                    <div className="flex items-center gap-1">
                      {col.label}
                      {sortColumn === col.key && (
                        sortDirection === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paginated.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-500 dark:text-gray-400">
                    No transactions found
                  </td>
                </tr>
              ) : (
                paginated.map((txn, i) => (
                  <tr key={i} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3">{new Date(txn.event_date).toLocaleDateString()}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        txn.event_type === 'income' 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                      }`}>
                        {txn.event_type}
                      </span>
                    </td>
                    <td className="px-4 py-3">{txn.description}</td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">
                      {txn.amount !== null && txn.amount !== undefined ? (txn.amount > 0 ? '+' : '') + formatCurrency(txn.amount) : '-'}
                    </td>
                    <td className="px-4 py-3">{txn.currency}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{txn.linked_event_id || '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Page {page} of {totalPages}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}