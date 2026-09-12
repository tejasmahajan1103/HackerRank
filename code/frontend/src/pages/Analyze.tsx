import { useState } from 'react';
import { api } from '../services/api';
import type { AnalysisResult } from '../types';
import { Calculator, Loader2, CheckCircle, AlertTriangle, Info } from 'lucide-react';

interface FormData {
  user_id: string;
  request_date: string;
  request_type: string;
  requested_amount: number;
  desired_completion_date: string;
  allows_partial_payment: boolean;
  request_text: string;
}

const REQUEST_TYPES = [
  'purchase', 'travel', 'education', 'family_transfer',
  'debt_repayment', 'investment', 'housing', 'emergency_expense', 'other'
];

export function Analyze() {
  const [formData, setFormData] = useState<FormData>({
    user_id: 'user_27',
    request_date: new Date().toISOString().split('T')[0],
    request_type: 'purchase',
    requested_amount: 0,
    desired_completion_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    allows_partial_payment: true,
    request_text: '',
  });
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await api.analyze(formData);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: keyof FormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Affordability Analysis</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Enter your expense details to get a personalized recommendation
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField label="User ID" required>
            <select
              value={formData.user_id}
              onChange={(e) => handleChange('user_id', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
            >
              {['user_26', 'user_27', 'user_28', 'user_29', 'user_30'].map(id => (
                <option key={id} value={id}>{id}</option>
              ))}
            </select>
          </FormField>

          <FormField label="Request Date" required>
            <input
              type="date"
              value={formData.request_date}
              onChange={(e) => handleChange('request_date', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
            />
          </FormField>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField label="Request Type" required>
            <select
              value={formData.request_type}
              onChange={(e) => handleChange('request_type', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
            >
              {REQUEST_TYPES.map(type => (
                <option key={type} value={type}>{type.replace('_', ' ')}</option>
              ))}
            </select>
          </FormField>

          <FormField label="Requested Amount" required>
            <input
              type="number"
              step="0.01"
              min="0"
              value={formData.requested_amount}
              onChange={(e) => handleChange('requested_amount', parseFloat(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
              placeholder="e.g., 50000"
            />
          </FormField>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField label="Desired Completion Date" required>
            <input
              type="date"
              value={formData.desired_completion_date}
              onChange={(e) => handleChange('desired_completion_date', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
            />
          </FormField>

          <FormField label="Allow Partial Payment">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.allows_partial_payment}
                onChange={(e) => handleChange('allows_partial_payment', e.target.checked)}
                className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
              />
              <span className="text-gray-700 dark:text-gray-300">Yes, partial payment is allowed</span>
            </label>
          </FormField>
        </div>

        <FormField label="Request Description" required>
          <textarea
            value={formData.request_text}
            onChange={(e) => handleChange('request_text', e.target.value)}
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
            placeholder="Describe your request (e.g., 'Can I afford a new laptop for $2000?')"
          />
        </FormField>

        <button
          type="submit"
          disabled={loading}
          className="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Calculator className="w-5 h-5" />
              Analyze Affordability
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 flex gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <p className="text-red-700 dark:text-red-400">{error}</p>
        </div>
      )}

      {result && (
        <AnalysisResultCard result={result} />
      )}
    </div>
  );
}

function FormField({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      {children}
    </div>
  );
}

function AnalysisResultCard({ result }: { result: AnalysisResult }) {
  const statusColors: Record<string, string> = {
    affordable_now: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 border-green-200 dark:border-green-800',
    affordable_with_plan: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 border-blue-200 dark:border-blue-800',
    affordable_later: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400 border-amber-200 dark:border-amber-800',
    not_affordable: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border-red-200 dark:border-red-800',
  };

  const methodLabels: Record<string, string> = {
    full_payment: 'Full Payment',
    partial_payment: 'Partial Payment',
    installments: 'Installments',
    wait: 'Wait',
    not_recommended: 'Not Recommended',
  };

  const methodIcons: Record<string, React.ComponentType<{ className?: string }>> = {
    full_payment: CheckCircle,
    partial_payment: CheckCircle,
    installments: Info,
    wait: AlertTriangle,
    not_recommended: AlertTriangle,
  };

  const MethodIcon = methodIcons[result.recommended_payment_method] || Info;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className={`px-6 py-4 border-b border-gray-200 dark:border-gray-700 ${statusColors[result.affordability_status]}`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Analysis Result</h3>
            <p className="text-sm mt-1">
              <span className="px-2 py-1 rounded-full text-xs font-medium">
                {result.affordability_status.replace('_', ' ')}
              </span>
            </p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold">${result.amount_safe_to_pay.toLocaleString()}</p>
            <p className="text-sm opacity-80">Safe to Pay Today</p>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ResultItem
            label="Recommended Method"
            value={methodLabels[result.recommended_payment_method]}
            icon={<MethodIcon className="w-5 h-5 text-green-600" />}
          />
          <ResultItem
            label="Earliest Full Payment"
            value={result.earliest_date_for_full_payment || 'Not within forecast period'}
            icon={<Info className="w-5 h-5 text-blue-600" />}
          />
          <ResultItem
            label="Payment Plan"
            value={result.payment_plan.length > 0 
              ? result.payment_plan.map(p => `${p.date}: $${p.amount}`).join(' | ')
              : 'None'}
            icon={<Calculator className="w-5 h-5 text-purple-600" />}
          />
        </div>

        {result.spending_changes_needed.length > 0 && (
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white mb-2">Spending Changes Needed</h4>
            <div className="space-y-1">
              {result.spending_changes_needed.map((change, i) => (
                <div key={i} className="px-3 py-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-sm">
                  {change.replace('stop:', 'Stop: ').replace('reduce_to:', 'Reduce to: ')}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2">Explanation</h4>
          <p className="text-gray-600 dark:text-gray-400">{result.decision_explanation}</p>
        </div>
      </div>
    </div>
  );
}

function ResultItem({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1">
        {icon}
        <span>{label}</span>
      </div>
      <p className="font-medium text-gray-900 dark:text-white text-sm">{value}</p>
    </div>
  );
}