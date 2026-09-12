import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { ForecastData } from '../types';
import { TrendingUp, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area } from 'recharts';

export function Forecast() {
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(90);
  const [userId] = useState('user_27');

  useEffect(() => {
    loadForecast();
  }, [days]);

  const loadForecast = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getForecast(userId, days);
      setForecast(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load forecast');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-12 h-12 text-green-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">Failed to load forecast</h3>
        <p className="text-gray-500 dark:text-gray-400 mt-1">{error}</p>
        <button onClick={loadForecast} className="mt-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
          Retry
        </button>
      </div>
    );
  }

  if (!forecast) return null;

  const { daily_balances, minimum_balance, min_projected_balance, min_balance_date } = forecast;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">90-Day Financial Forecast</h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Projected balance trajectory with minimum threshold</p>
        </div>
        <div className="flex items-center gap-4">
          <select
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value))}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
          >
            <option value={30}>30 Days</option>
            <option value={60}>60 Days</option>
            <option value={90}>90 Days</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard
          title="Current Balance"
          value={daily_balances[0]?.starting_balance || 0}
          icon={CheckCircle}
          color="text-green-600"
          bg="bg-green-50 dark:bg-green-900/20"
        />
        <SummaryCard
          title="Minimum Balance"
          value={minimum_balance}
          icon={AlertTriangle}
          color="text-amber-600"
          bg="bg-amber-50 dark:bg-amber-900/20"
        />
        <SummaryCard
          title="Min Projected Balance"
          value={min_projected_balance}
          icon={min_projected_balance >= minimum_balance ? CheckCircle : AlertTriangle}
          color={min_projected_balance >= minimum_balance ? 'text-green-600' : 'text-red-600'}
          bg={min_projected_balance >= minimum_balance ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20'}
        />
        <SummaryCard
          title="Min Balance Date"
          value={new Date(min_balance_date).toLocaleDateString()}
          icon={TrendingUp}
          color="text-blue-600"
          bg="bg-blue-50 dark:bg-blue-900/20"
          isDate
        />
      </div>

      {/* Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Balance Projection</h3>
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={daily_balances.slice(0, days)}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
              <XAxis 
                dataKey="date" 
                tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                interval="preserveStartEnd"
                tick={{ fontSize: 10 }}
              />
              <YAxis 
                tickFormatter={(value) => formatCurrency(value)} 
                tick={{ fontSize: 10 }}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
              />
              <Area
                type="monotone"
                dataKey="ending_balance"
                stroke="#10b981"
                fill="#10b981"
                fillOpacity={0.1}
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="minimum_balance"
                stroke="#ef4444"
                strokeDasharray="5 5"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="starting_balance"
                stroke="#6366f1"
                strokeDasharray="2 2"
                strokeWidth={1}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center gap-4 mt-4 text-sm flex-wrap">
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 bg-green-500 rounded" />
            <span>Projected Balance</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 border-2 border-dashed border-red-500" />
            <span>Minimum Threshold</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 border-2 border-dashed border-indigo-500" />
            <span>Starting Balance</span>
          </div>
        </div>
      </div>

      {/* Key Events */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Key Events in Forecast Period</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                <th className="pb-2">Date</th>
                <th className="pb-2">Starting Balance</th>
                <th className="pb-2">Income</th>
                <th className="pb-2">Expenses</th>
                <th className="pb-2">Ending Balance</th>
              </tr>
            </thead>
            <tbody>
              {daily_balances
                .filter(d => d.income > 0 || d.expenses > 1000)
                .slice(0, 20)
                .map((day, i) => (
                  <tr key={i} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="py-2">{new Date(day.date).toLocaleDateString()}</td>
                    <td className="py-2">{formatCurrency(day.starting_balance)}</td>
                    <td className="py-2 text-green-600">{day.income > 0 ? '+' + formatCurrency(day.income) : '-'}</td>
                    <td className="py-2 text-red-600">{day.expenses > 0 ? '-' + formatCurrency(day.expenses) : '-'}</td>
                    <td className="py-2 font-medium">{formatCurrency(day.ending_balance)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({ title, value, icon: Icon, color, bg, isDate }: { 
  title: string; 
  value: number | string; 
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bg: string;
  isDate?: boolean;
}) {
  return (
    <div className={`p-4 rounded-xl border ${bg} border-gray-200 dark:border-gray-700`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">
            {isDate ? value : formatCurrency(value as number)}
          </p>
        </div>
        <div className={`p-2 rounded-lg ${bg}`}>
          <Icon className={`w-5 h-5 ${color}`} />
        </div>
      </div>
    </div>
  );
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}