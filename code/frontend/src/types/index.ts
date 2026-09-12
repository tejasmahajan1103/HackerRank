export interface User {
  user_id: string;
  current_balance: number;
  minimum_balance_to_keep: number;
  home_currency: string;
  financial_priorities: string[];
  protected_categories: string[];
  reducible_categories: string[];
  stoppable_categories: string[];
  payment_methods_user_will_consider: string[];
  max_installment_months: number | null;
}

export interface FinancialEvent {
  event_id: string;
  user_id: string;
  event_date: string;
  event_type: string;
  amount: number | null;
  currency: string;
  status: string;
  recurring_frequency: string | null;
  recurring_day_of_month: number | null;
  linked_event_id: string | null;
  description: string;
}

export interface Request {
  request_id: string;
  user_id: string;
  request_date: string;
  request_type: string;
  requested_amount: number;
  desired_completion_date: string;
  allows_partial_payment: boolean;
  request_text: string;
}

export interface PaymentOption {
  payment_option_id: string;
  request_id: string;
  payment_method: string;
  number_of_payments: number;
  first_payment_date: string;
  recurring_interval_days: number;
  financing_fee: number;
  total_payable_amount: number;
}

export interface AnalysisResult {
  request_id: string;
  amount_safe_to_pay: number;
  affordability_status: 'affordable_now' | 'affordable_with_plan' | 'affordable_later' | 'not_affordable';
  recommended_payment_method: 'full_payment' | 'partial_payment' | 'installments' | 'wait' | 'not_recommended';
  payment_plan: PaymentPlanItem[];
  earliest_date_for_full_payment: string | null;
  spending_changes_needed: string[];
  decision_explanation: string;
}

export interface PaymentPlanItem {
  date: string;
  amount: number;
}

export interface ForecastData {
  user_id: string;
  start_date: string;
  forecast_days: number;
  minimum_balance: number;
  min_projected_balance: number;
  min_balance_date: string;
  daily_balances: DailyBalance[];
}

export interface DailyBalance {
  date: string;
  starting_balance: number;
  income: number;
  expenses: number;
  ending_balance: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  analysis?: AnalysisResult;
}

export interface ApiError {
  detail: string;
}