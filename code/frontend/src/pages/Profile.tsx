import { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { User as UserType } from '../types';
import { Loader2, User, Mail, Calendar, CreditCard, Settings, Save, AlertCircle, CheckCircle } from 'lucide-react';

export function Profile() {
  const [profile, setProfile] = useState<UserType | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [userId] = useState('user_27');
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    date_of_birth: '',
    address: '',
    currency_preference: 'USD',
    risk_tolerance: 'medium',
    notification_preferences: {
      email: true,
      sms: false,
      push: true,
    },
  });

  useEffect(() => {
    loadProfile();
  }, [userId]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const data = await api.getUserOverview(userId);
      setProfile(data as unknown as UserType);
      if (data) {
        setFormData({
          full_name: `User ${data.user_id}`,
          email: 'user@example.com',
          phone: '',
          date_of_birth: '',
          address: '',
          currency_preference: data.currency || 'USD',
          risk_tolerance: 'medium',
          notification_preferences: { email: true, sms: false, push: true },
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      // In a real app, this would call an update API
      await new Promise(resolve => setTimeout(resolve, 500));
      setSuccess('Profile updated successfully');
      setEditMode(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile');
    } finally {
      setSaving(false);
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
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Profile Settings</h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Manage your personal information and preferences</p>
        </div>
        {!editMode && (
          <button
            onClick={() => setEditMode(true)}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
          >
            <Settings className="w-4 h-4" />
            Edit Profile
          </button>
        )}
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 flex gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <p className="text-red-700 dark:text-red-400">{error}</p>
        </div>
      )}

      {success && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4 flex gap-3">
          <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
          <p className="text-green-700 dark:text-green-400">{success}</p>
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {/* Profile Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center gap-6">
          <div className="w-20 h-20 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
            <User className="w-10 h-10 text-green-600" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              {formData.full_name || 'User Profile'}
            </h3>
            <p className="text-gray-500 dark:text-gray-400">{userId}</p>
          </div>
        </div>

        {/* Profile Form */}
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <FormField label="Full Name" icon={User}>
              {editMode ? (
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
                />
              ) : (
                <p className="text-gray-900 dark:text-white">{formData.full_name || 'Not set'}</p>
              )}
            </FormField>

            <FormField label="Email" icon={Mail}>
              {editMode ? (
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
                />
              ) : (
                <p className="text-gray-900 dark:text-white">{formData.email || 'Not set'}</p>
              )}
            </FormField>

            <FormField label="Phone" icon={CreditCard}>
              {editMode ? (
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
                />
              ) : (
                <p className="text-gray-900 dark:text-white">{formData.phone || 'Not set'}</p>
              )}
            </FormField>

            <FormField label="Date of Birth" icon={Calendar}>
              {editMode ? (
                <input
                  type="date"
                  value={formData.date_of_birth}
                  onChange={(e) => setFormData(prev => ({ ...prev, date_of_birth: e.target.value }))}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
                />
              ) : (
                <p className="text-gray-900 dark:text-white">
                  {formData.date_of_birth ? new Date(formData.date_of_birth).toLocaleDateString() : 'Not set'}
                </p>
              )}
            </FormField>
          </div>

          <FormField label="Address" icon={User} fullWidth>
            {editMode ? (
              <textarea
                value={formData.address}
                onChange={(e) => setFormData(prev => ({ ...prev, address: e.target.value }))}
                rows={2}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
              />
            ) : (
              <p className="text-gray-900 dark:text-white">{formData.address || 'Not set'}</p>
            )}
          </FormField>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <FormField label="Currency Preference" icon={CreditCard}>
              {editMode ? (
                <select
                  value={formData.currency_preference}
                  onChange={(e) => setFormData(prev => ({ ...prev, currency_preference: e.target.value }))}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
                >
                  <option value="USD">USD - US Dollar</option>
                  <option value="EUR">EUR - Euro</option>
                  <option value="GBP">GBP - British Pound</option>
                  <option value="JPY">JPY - Japanese Yen</option>
                </select>
              ) : (
                <p className="text-gray-900 dark:text-white">{formData.currency_preference}</p>
              )}
            </FormField>

            <FormField label="Risk Tolerance" icon={Settings}>
              {editMode ? (
                <select
                  value={formData.risk_tolerance}
                  onChange={(e) => setFormData(prev => ({ ...prev, risk_tolerance: e.target.value }))}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
                >
                  <option value="low">Low (Conservative)</option>
                  <option value="medium">Medium (Balanced)</option>
                  <option value="high">High (Aggressive)</option>
                </select>
              ) : (
                <p className="text-gray-900 dark:text-white capitalize">{formData.risk_tolerance}</p>
              )}
            </FormField>
          </div>

          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <h4 className="font-medium text-gray-900 dark:text-white mb-4">Notification Preferences</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { key: 'email', label: 'Email Notifications', icon: Mail },
                { key: 'sms', label: 'SMS Notifications', icon: CreditCard },
                { key: 'push', label: 'Push Notifications', icon: Settings },
              ].map(({ key, label, icon: Icon }) => (
                <label key={key} className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg cursor-pointer">
                  {editMode ? (
                    <input
                      type="checkbox"
                      checked={formData.notification_preferences[key as keyof typeof formData.notification_preferences]}
                      onChange={(e) => setFormData(prev => ({
                        ...prev,
                        notification_preferences: {
                          ...prev.notification_preferences,
                          [key]: e.target.checked,
                        },
                      }))}
                      className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                    />
                  ) : (
                    <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                      formData.notification_preferences[key as keyof typeof formData.notification_preferences]
                        ? 'border-green-500 bg-green-500'
                        : 'border-gray-300 dark:border-gray-600'
                    }`}>
                      {formData.notification_preferences[key as keyof typeof formData.notification_preferences] && (
                        <CheckCircle className="w-3 h-3 text-white" />
                      )}
                    </div>
                  )}
                  <div className="flex items-center gap-2">
                    <Icon className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                    <span className="text-gray-700 dark:text-gray-300">{label}</span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {editMode && (
            <div className="flex gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Save Changes
                  </>
                )}
              </button>
              <button
                onClick={() => {
                  setFormData({
                    full_name: `User ${profile?.user_id || userId}`,
                    email: 'user@example.com',
                    phone: '',
                    date_of_birth: '',
                    address: '',
                    currency_preference: profile?.home_currency || 'USD',
                    risk_tolerance: 'medium',
                    notification_preferences: { email: true, sms: false, push: true },
                  });
                  setEditMode(false);
                }}
                className="px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function FormField({ 
  label, 
  icon: Icon, 
  children, 
  fullWidth = false 
}: { 
  label: string; 
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
  fullWidth?: boolean;
}) {
  return (
    <div className={fullWidth ? 'md:col-span-2' : ''}>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
        <Icon className="w-4 h-4 text-gray-400" />
        {label}
      </label>
      {children}
    </div>
  );
}