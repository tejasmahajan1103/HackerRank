import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { User, ForecastData } from '../types';
import type { ReactNode } from 'react';
import { Wallet, TrendingUp, AlertTriangle, CheckCircle, CreditCard, ArrowUpRight, Calculator, MessageSquare } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area } from 'recharts';

interface DashboardData {
  user: User | null;
  overview: {
    user_id: string;
    current_balance: number;
    minimum_balance: number;
    safe_to_spend: number;
    monthly_income: number;
    monthly_expenses: number;
    recurring_expenses_count: number;
    currency: string;
  } | null;
  forecast: ForecastData | null;
  loading: boolean;
  error: string | null;
}

export function Dashboard() {
  const [data, setData] = useState<DashboardData>({
    user: null,
    overview: null,
    forecast: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    // For demo, use a default user_id
    const userId = 'user_27';
    loadData(userId);
  }, []);

  const loadData = async (userId: string) => {
    try {
      setData(prev => ({ ...prev, loading: true, error: null }));
      
      const [overview, forecast] = await Promise.all([
        api.getUserOverview(userId),
        api.getForecast(userId, 90),
      ]);
      
      setData({
        user: null,
        overview,
        forecast,
        loading: false,
        error: null,
      });
    } catch (err) {
      setData(prev => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to load data',
      }));
    }
  };

  if (data.loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-green-500 border-t-transparent" />
      </div>
    );
  }

  if (data.error) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">Failed to load dashboard</h3>
        <p className="text-gray-500 dark:text-gray-400 mt-1">{data.error}</p>
        <button 
          onClick={() => loadData('user_27')}
          className="mt-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const { overview, forecast } = data;

  return (
    <div className="space-y-6">
      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Current Balance"
          value={overview?.current_balance || 0}
          currency={overview?.currency || 'USD'}
          icon={Wallet}
          iconColor="text-green-600"
          bgColor="bg-green-50 dark:bg-green-900/20"
        />
        <MetricCard
          title="Minimum Balance"
          value={overview?.minimum_balance || 0}
          currency={overview?.currency || 'USD'}
          icon={AlertTriangle}
          iconColor="text-amber-600"
          bgColor="bg-amber-50 dark:bg-amber-900/20"
        />
        <MetricCard
          title="Safe to Spend"
          value={overview?.safe_to_spend || 0}
          currency={overview?.currency || 'USD'}
          icon={CheckCircle}
          iconColor="text-blue-600"
          bgColor="bg-blue-50 dark:bg-blue-900/20"
        />
        <MetricCard
          title="Monthly Cash Flow"
          value={(overview?.monthly_income || 0) - (overview?.monthly_expenses || 0)}
          currency={overview?.currency || 'USD'}
          icon={TrendingUp}
          iconColor="text-purple-600"
          bgColor="bg-purple-50 dark:bg-purple-900/20"
          trend={(overview?.monthly_income || 0) > (overview?.monthly_expenses || 0) ? 'positive' : 'negative'}
        />
      </div>

      {/* Forecast Chart & Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card title="90-Day Balance Forecast" subtitle="Projected balance vs minimum threshold">
            {forecast && (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={forecast.daily_balances.slice(0, 90)}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      interval="preserveStartEnd"
                      tick={{ fontSize: 10 }}
                    />
                    <YAxis 
                      tickFormatter={(value) => formatCurrency(value, overview?.currency || 'USD')} 
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
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
            <div className="flex items-center gap-4 mt-4 text-sm">
              <div className="flex items-center gap-2">
                <span className="w-4 h-4 bg-green-500 rounded" />
                <span>Projected Balance</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-dashed border-red-500" />
                <span>Minimum Threshold</span>
              </div>
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card title="Financial Health" subtitle="Key indicators">
            <div className="space-y-3">
              <HealthIndicator
                label="Balance vs Minimum"
                value={overview?.current_balance || 0}
                target={overview?.minimum_balance || 0}
                currency={overview?.currency || 'USD'}
                higherIsBetter
              />
              <HealthIndicator
                label="Monthly Savings Rate"
                value={((overview?.monthly_income || 0) - (overview?.monthly_expenses || 0)) / (overview?.monthly_income || 1) * 100}
                target={20}
                currency="%"
                higherIsBetter
                format="percentage"
              />
              <HealthIndicator
                label="Recurring Expenses"
                value={overview?.recurring_expenses_count || 0}
                target={5}
                currency=" items"
                higherIsBetter={false}
              />
            </div>
          </Card>

          <Card title="Quick Actions" subtitle="Common tasks">
            <div className="space-y-2">
              <ActionButton 
                label="Analyze New Expense" 
                href="/analyze" 
                icon={Calculator}
                description="Check affordability of a purchase"
              />
              <ActionButton 
                label="Chat with AI" 
                href="/chat" 
                icon={MessageSquare}
                description="Ask financial questions"
              />
              <ActionButton 
                label="View Forecast" 
                href="/forecast" 
                icon={TrendingUp}
                description="Detailed 90-day projection"
              />
              <ActionButton 
                label="Payment Plans" 
                href="/plans" 
                icon={CreditCard}
                description="Compare payment options"
              />
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

interface MetricCardProps {
  title: string;
  value: number;
  currency: string;
  icon: React.ComponentType<{ className?: string }>;
  iconColor: string;
  bgColor: string;
  trend?: 'positive' | 'negative';
}

function MetricCard({ title, value, currency, icon: Icon, iconColor, bgColor, trend }: MetricCardProps) {
  return (
    <div className={`p-6 rounded-xl border ${bgColor} border-gray-200 dark:border-gray-700`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            {formatCurrency(value, currency)}
          </p>
          {trend && (
            <p className={`text-sm mt-1 ${trend === 'positive' ? 'text-green-600' : 'text-red-600'}`}>
              {trend === 'positive' ? 'Positive' : 'Negative'} cash flow
            </p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${bgColor}`}>
          <Icon className={`w-6 h-6 ${iconColor}`} />
        </div>
      </div>
    </div>
  );
}

interface CardProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

function Card({ title, subtitle, children }: CardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
        {subtitle && <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

interface HealthIndicatorProps {
  label: string;
  value: number;
  target: number;
  currency: string;
  higherIsBetter: boolean;
  format?: 'percentage' | 'currency' | 'number';
}

function HealthIndicator({ label, value, target, currency, higherIsBetter, format }: HealthIndicatorProps) {
  const isGood = higherIsBetter ? value >= target : value <= target;
  const progress = format === 'percentage' 
    ? Math.min(100, Math.max(0, value))
    : currency === '%'
      ? Math.min(100, Math.max(0, value))
      : 100;
  
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600 dark:text-gray-400">{label}</span>
        <span className="font-medium text-gray-900 dark:text-white">
          {format === 'percentage' ? `${value.toFixed(1)}%` : formatCurrency(value, currency)}
        </span>
      </div>
      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full transition-all ${isGood ? 'bg-green-500' : 'bg-red-500'}`}
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
        Target: {format === 'percentage' ? `${target}%` : formatCurrency(target, currency)}
      </p>
    </div>
  );
}

interface ActionButtonProps {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

function ActionButton({ label, href, icon: Icon, description }: ActionButtonProps) {
  return (
    <a 
      href={href}
      className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
    >
      <Icon className="w-5 h-5 text-gray-500 dark:text-gray-400 flex-shrink-0" />
      <div className="flex-1 text-left">
        <p className="font-medium text-gray-900 dark:text-white text-sm">{label}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">{description}</p>
      </div>
      <ArrowUpRight className="w-4 h-4 text-gray-400" />
    </a>
  );
}

function formatCurrency(value: number, currency: string): string {
  const symbols: Record<string, string> = {
    'USD': '$', 'EUR': '€', 'INR': '₹', 'ZAR': 'R', 'IDR': 'Rp',
  };
  const symbol = symbols[currency] || currency;
  return `${symbol}${value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
}