import { useState, useRef, useEffect } from 'react';
import { api } from '../services/api';
import type { AnalysisResult } from '../types';
import { Send, Sparkles, User, Loader2 } from 'lucide-react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  analysis?: AnalysisResult;
}

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: "Hello! I'm your AI financial assistant. Ask me anything like 'Can I afford this laptop?' or 'Should I invest in stocks?'",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setLoading(true);

    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
    }]);

    try {
      // For demo, use a default user_id
      const response = await api.chat({ user_id: 'user_27', message: userMessage });
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        analysis: response.analysis || undefined,
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Sorry, I encountered an error. Please try again.",
        timestamp: new Date(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((message, index) => (
          <ChatBubble key={index} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about affordability, investments, budgeting..."
              className="w-full px-4 py-3 pr-12 border border-gray-300 dark:border-gray-600 rounded-full bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500"
              disabled={loading}
            />
            {loading && (
              <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-green-500 animate-spin" />
            )}
          </div>
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="px-6 py-3 bg-green-600 text-white rounded-full hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send className="w-5 h-5" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center mt-2">
          Powered by AI financial engine
        </p>
      </form>
    </div>
  );
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : ''}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0">
          <Sparkles className="w-5 h-5 text-green-600" />
        </div>
      )}
      <div className={`max-w-[70%] ${isUser ? 'order-2' : ''}`}>
        <div className={`px-4 py-3 rounded-2xl ${
          isUser 
            ? 'bg-green-600 text-white rounded-br-none' 
            : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-bl-none'
        }`}>
          <p className="whitespace-pre-wrap">{message.content}</p>
          
          {message.analysis && (
            <AnalysisCard analysis={message.analysis} />
          )}
        </div>
        <p className={`text-xs text-gray-400 mt-1 ${isUser ? 'text-right' : ''}`}>
          {message.timestamp.toLocaleTimeString()}
        </p>
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center flex-shrink-0">
          <User className="w-5 h-5 text-gray-600" />
        </div>
      )}
    </div>
  );
}

function AnalysisCard({ analysis }: { analysis: AnalysisResult }) {
  const statusColors: Record<string, string> = {
    affordable_now: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    affordable_with_plan: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    affordable_later: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
    not_affordable: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  };
  
  const methodLabels: Record<string, string> = {
    full_payment: 'Full Payment',
    partial_payment: 'Partial Payment',
    installments: 'Installments',
    wait: 'Wait',
    not_recommended: 'Not Recommended',
  };

  return (
    <div className="mt-3 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="grid grid-cols-2 gap-2 text-sm mb-2">
        <div>
          <p className="text-gray-500 dark:text-gray-400">Status</p>
          <p className="font-medium">
            <span className={`px-2 py-0.5 rounded text-xs ${statusColors[analysis.affordability_status]}`}>
              {analysis.affordability_status.replace('_', ' ')}
            </span>
          </p>
        </div>
        <div>
          <p className="text-gray-500 dark:text-gray-400">Method</p>
          <p className="font-medium">{methodLabels[analysis.recommended_payment_method]}</p>
        </div>
        <div>
          <p className="text-gray-500 dark:text-gray-400">Safe Amount</p>
          <p className="font-medium">${analysis.amount_safe_to_pay.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-gray-500 dark:text-gray-400">Earliest Full Payment</p>
          <p className="font-medium">{analysis.earliest_date_for_full_payment || 'N/A'}</p>
        </div>
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400">{analysis.decision_explanation}</p>
    </div>
  );
}