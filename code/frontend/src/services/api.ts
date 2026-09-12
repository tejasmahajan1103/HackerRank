import type { 
  AnalysisResult, 
  PaymentOption, 
  User, 
  ForecastData 
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class ApiError extends Error {
  public readonly status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, error.detail || 'Request failed');
  }

  return response.json();
}

export const api = {
  // Health
  health: () => fetchApi<{ status: string }>('/health'),

  // Analysis
  analyze: (data: {
    user_id: string;
    request_date: string;
    request_type: string;
    requested_amount: number;
    desired_completion_date: string;
    allows_partial_payment: boolean;
    request_text: string;
  }) => fetchApi<AnalysisResult>('/analyze', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // Chat
  chat: (data: { user_id: string; message: string }) => fetchApi<{
    response: string;
    analysis: AnalysisResult | null;
  }>('/chat', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // User
  getUser: (userId: string) => fetchApi<User>(`/users/${userId}`),
  getUserOverview: (userId: string) => fetchApi<{
    user_id: string;
    current_balance: number;
    minimum_balance: number;
    safe_to_spend: number;
    monthly_income: number;
    monthly_expenses: number;
    recurring_expenses_count: number;
    currency: string;
  }>(`/users/${userId}/overview`),

  // Forecast
  getForecast: (userId: string, days: number = 90) => fetchApi<ForecastData>(
    `/users/${userId}/forecast?days=${days}`
  ),

  // Requests
  getRequest: (requestId: string) => fetchApi<{
    request_id: string;
    user_id: string;
    request_date: string;
    request_type: string;
    requested_amount: number;
    desired_completion_date: string;
    allows_partial_payment: boolean;
    request_text: string;
    analysis: AnalysisResult;
  }>(`/requests/${requestId}`),

  getPaymentOptions: (requestId: string) => fetchApi<{
    request_id: string;
    options: PaymentOption[];
  }>(`/payment-options/${requestId}`),

  // Upload
  uploadFile: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    }).then(res => res.json());
  },
};