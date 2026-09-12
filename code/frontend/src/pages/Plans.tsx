import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Loader2, Calendar, CreditCard, MinusCircle, PlusCircle, CheckCircle } from 'lucide-react';

interface PaymentPlan {
  method: string;
  installments?: Array<{ date: string; amount: number }>;
  partial_payments?: Array<{ date: string; amount: number }>;
  total_amount: number;
  months_to_complete: number;
  feasible: boolean;
  notes?: string;
}

export function Plans() {
  const [plans, setPlans] = useState<PaymentPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userId] = useState('user_27');

  useEffect(() => {
    loadPlans();
  }, [userId]);

  const loadPlans = async () => {
    try {
      setLoading(true);
      // Get the latest analysis result which includes payment plans
      const response = await api.analyze({
        user_id: userId,
        request_date: new Date().toISOString().split('T')[0],
        request_type: 'purchase',
        requested_amount: 10000,
        desired_completion_date: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        allows_partial_payment: true,
        request_text: 'Generate payment plans for $10,000',
      });
      
      // Build plans from analysis
      const generatedPlans: PaymentPlan[] = [
        {
          method: 'full_payment',
          total_amount: response.amount_safe_to_pay,
          months_to_complete: 0,
          feasible: response.affordability_status === 'affordable_now',
          notes: response.amount_safe_to_pay >= 10000 
            ? 'Can pay full amount today' 
            : `Can only afford $${response.amount_safe_to_pay.toLocaleString()} today`,
        },
      ];

      if (response.amount_safe_to_pay > 0 && response.amount_safe_to_pay < 10000) {
        generatedPlans.push({
          method: 'partial_payment',
          partial_payments: response.payment_plan,
          total_amount: response.payment_plan.reduce((sum: number, p: { amount: number }) => sum + p.amount, 0),
          months_to_complete: response.payment_plan.length,
          feasible: response.affordability_status === 'affordable_with_plan',
          notes: `Pay $${response.amount_safe_to_pay.toLocaleString()} now, rest later`,
        });
      }

      if (response.recommended_payment_method === 'installments' || response.payment_plan.length > 1) {
        generatedPlans.push({
          method: 'installments',
          installments: response.payment_plan,
          total_amount: response.payment_plan.reduce((sum: number, p: { amount: number }) => sum + p.amount, 0),
          months_to_complete: Math.ceil(response.payment_plan.length / 2),
          feasible: response.affordability_status !== 'not_affordable',
          notes: 'Equal monthly installments',
        });
      }

      if (response.earliest_date_for_full_payment) {
        generatedPlans.push({
          method: 'wait',
          total_amount: 10000,
          months_to_complete: Math.ceil(
            (new Date(response.earliest_date_for_full_payment).getTime() - Date.now()) / (30 * 24 * 60 * 60 * 1000)
          ),
          feasible: true,
          notes: `Wait until ${new Date(response.earliest_date_for_full_payment).toLocaleDateString()} to pay in full`,
        });
      }

      setPlans(generatedPlans);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load plans');
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

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Payment Plans</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Compare different ways to fund your request</p>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
          <p className="text-red-700 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Plan Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {plans.map((plan, index) => (
          <PlanCard key={index} plan={plan} />
        ))}
      </div>

      {/* Detailed View */}
      {plans.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Plan Comparison</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                  <th className="px-4 py-3">Plan</th>
                  <th className="px-4 py-3">Total Amount</th>
                  <th className="px-4 py-3">Duration</th>
                  <th className="px-4 py-3">Feasibility</th>
                  <th className="px-4 py-3">Details</th>
                </tr>
              </thead>
              <tbody>
                {plans.map((plan, i) => (
                  <tr key={i} className="border-b border-gray-100 dark:border-gray-700">
                    <td className="px-4 py-3 font-medium capitalize">{plan.method.replace('_', ' ')}</td>
                    <td className="px-4 py-3">${plan.total_amount.toLocaleString()}</td>
                    <td className="px-4 py-3">
                      {plan.months_to_complete === 0 
                        ? 'Immediate' 
                        : `${plan.months_to_complete} month${plan.months_to_complete !== 1 ? 's' : ''}`}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        plan.feasible 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                      }`}>
                        {plan.feasible ? 'Feasible' : 'Not Feasible'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400 text-sm">{plan.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Custom Plan Builder */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Custom Plan Builder</h3>
        <CustomPlanBuilder userId={userId} />
      </div>
    </div>
  );
}

function PlanCard({ plan }: { plan: PaymentPlan }) {
  const methodColors: Record<string, string> = {
    full_payment: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    partial_payment: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    installments: 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800',
    wait: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800',
  };

  const methodIcons: Record<string, React.ComponentType<{ className?: string }>> = {
    full_payment: CheckCircle,
    partial_payment: MinusCircle,
    installments: CreditCard,
    wait: Calendar,
  };

  const Icon = methodIcons[plan.method] || CheckCircle;

  return (
    <div className={`p-6 rounded-xl border ${methodColors[plan.method] || 'border-gray-200 dark:border-gray-700'}`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600">
            <Icon className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">{plan.method.replace('_', ' ')}</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">${plan.total_amount.toLocaleString()}</p>
          </div>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          plan.feasible 
            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
            : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
        }`}>
          {plan.feasible ? '✓ Feasible' : '✗ Not Feasible'}
        </span>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500 dark:text-gray-400">Duration</span>
          <span className="font-medium">
            {plan.months_to_complete === 0 ? 'Immediate' : `${plan.months_to_complete} month${plan.months_to_complete !== 1 ? 's' : ''}`}
          </span>
        </div>
        
        {plan.installments && plan.installments.length > 0 && (
          <div className="flex justify-between">
            <span className="text-gray-500 dark:text-gray-400">Installments</span>
            <span className="font-medium">{plan.installments.length} payments</span>
          </div>
        )}
        
        {plan.partial_payments && plan.partial_payments.length > 0 && (
          <div className="flex justify-between">
            <span className="text-gray-500 dark:text-gray-400">Payments</span>
            <span className="font-medium">{plan.partial_payments.length} partial payments</span>
          </div>
        )}
      </div>

      <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">{plan.notes}</p>
    </div>
  );
}

function CustomPlanBuilder({ }: { userId: string }) {
  const [amount, setAmount] = useState(5000);
  const [months, setMonths] = useState(6);
  const [calculating, setCalculating] = useState(false);

  const calculate = () => {
    setCalculating(true);
    try {
      // Simple calculation - in real app would call API
      const monthly = amount / months;
      console.log('Custom plan calculated:', { monthly, total: amount });
    } finally {
      setCalculating(false);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Total Amount</label>
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(parseInt(e.target.value))}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
          min="100"
          step="100"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Duration (months)</label>
        <input
          type="number"
          value={months}
          onChange={(e) => setMonths(parseInt(e.target.value))}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
          min="1"
          max="60"
        />
      </div>
      <div className="flex items-end">
        <button
          onClick={calculate}
          disabled={calculating}
          className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {calculating ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <>
              <PlusCircle className="w-4 h-4" />
              Calculate
            </>
          )}
        </button>
      </div>
    </div>
  );
}