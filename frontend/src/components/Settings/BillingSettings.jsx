import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  CreditCard, Loader2, AlertCircle, Check, CalendarClock, Wallet,
  UserCircle2, Save, RefreshCcw, ReceiptText, CheckCircle2, XCircle, History
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import settingsService from '../../services/settingsService';

const STATUS_STYLES = {
  active: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  past_due: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  suspended: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  cancelled: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
};

const PAYMENT_STATUS_STYLES = {
  pending: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  confirmed: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  rejected: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
};

const emptyPayerForm = {
  payer_user_id: '',
  payer_name: '',
  payer_email: '',
  payer_phone: '',
  payment_method: 'bank_transfer',
  grace_days: 8,
  auto_suspend_enabled: true,
  monthly_price: '',
  currency: 'USD',
  notes: '',
};

const emptyPaymentForm = {
  payment_method: 'bank_transfer',
  amount: '',
  currency: 'USD',
  due_date: '',
  reference: '',
  evidence_file: null,
};

const formatDate = (dateValue) => {
  if (!dateValue) return '-';
  try {
    return new Date(dateValue).toLocaleDateString();
  } catch {
    return dateValue;
  }
};

const BillingSettings = ({ organizationId }) => {
  const { t, language } = useI18n();
  const { hasRole } = useAuth();
  const canManageBilling = hasRole(['org_admin', 'iso_manager']);

  const [loading, setLoading] = useState(true);
  const [savingPayer, setSavingPayer] = useState(false);
  const [registeringPayment, setRegisteringPayment] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const [users, setUsers] = useState([]);
  const [subscription, setSubscription] = useState(null);
  const [payments, setPayments] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [timelineLoading, setTimelineLoading] = useState(true);

  const [payerForm, setPayerForm] = useState(emptyPayerForm);
  const [paymentForm, setPaymentForm] = useState(emptyPaymentForm);

  const paymentMethodOptions = useMemo(
    () => [
      { value: 'bank_transfer', label: t('settings.billing.paymentMethods.bankTransfer') },
      { value: 'credit_card', label: t('settings.billing.paymentMethods.creditCard') },
      { value: 'debit_card', label: t('settings.billing.paymentMethods.debitCard') },
      { value: 'other', label: t('settings.billing.paymentMethods.other') },
    ],
    [t]
  );

  const statusLabels = useMemo(() => ({
    active: t('settings.billing.status.active'),
    past_due: t('settings.billing.status.pastDue'),
    suspended: t('settings.billing.status.suspended'),
    cancelled: t('settings.billing.status.cancelled'),
  }), [t]);

  const paymentStatusLabels = useMemo(() => ({
    pending: t('settings.billing.paymentStatus.pending'),
    confirmed: t('settings.billing.paymentStatus.confirmed'),
    rejected: t('settings.billing.paymentStatus.rejected'),
  }), [t]);

  const syncFormsFromSubscription = useCallback((subscriptionData) => {
    if (!subscriptionData) return;
    setPayerForm({
      payer_user_id: subscriptionData.payer_user || '',
      payer_name: subscriptionData.payer_name || '',
      payer_email: subscriptionData.payer_email || '',
      payer_phone: subscriptionData.payer_phone || '',
      payment_method: subscriptionData.payment_method || 'bank_transfer',
      grace_days: subscriptionData.grace_days ?? 8,
      auto_suspend_enabled: Boolean(subscriptionData.auto_suspend_enabled),
      monthly_price: subscriptionData.monthly_price ?? '',
      currency: subscriptionData.currency || 'USD',
      notes: subscriptionData.notes || '',
    });

    setPaymentForm((prev) => ({
      ...prev,
      payment_method: subscriptionData.payment_method || 'bank_transfer',
      amount: subscriptionData.monthly_price ?? '',
      currency: subscriptionData.currency || 'USD',
      due_date: subscriptionData.next_due_date || '',
    }));
  }, []);

  const loadBillingData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setTimelineLoading(true);

      const [billingData, usersData, timelineData] = await Promise.all([
        settingsService.getBillingCurrent(organizationId),
        settingsService.getUsers(organizationId).catch(() => []),
        settingsService.getBillingTimeline(organizationId).catch(() => []),
      ]);

      setUsers(usersData || []);
      setSubscription(billingData?.subscription || null);
      setPayments(billingData?.recent_payments || []);
      setTimeline((timelineData || []).slice(0, 15));
      syncFormsFromSubscription(billingData?.subscription || null);
    } catch (err) {
      console.error('Error cargando billing:', err);
      setError(t('settings.billing.messages.errorLoading'));
    } finally {
      setLoading(false);
      setTimelineLoading(false);
    }
  }, [organizationId, syncFormsFromSubscription, t]);

  const actionStyleMap = {
    create: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
    update: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
    delete: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
    default: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
  };

  useEffect(() => {
    if (organizationId) {
      loadBillingData();
    }
  }, [organizationId, loadBillingData]);

  const showSuccess = (message) => {
    setSuccess(message);
    setTimeout(() => setSuccess(null), 3000);
  };

  const handlePayerChange = (event) => {
    const { name, value, type, checked } = event.target;
    setPayerForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handlePaymentChange = (event) => {
    const { name, value, files, type } = event.target;
    if (type === 'file') {
      setPaymentForm((prev) => ({ ...prev, [name]: files?.[0] || null }));
      return;
    }
    setPaymentForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSavePayer = async (event) => {
    event.preventDefault();
    try {
      setSavingPayer(true);
      setError(null);
      const payload = {
        ...payerForm,
        payer_user_id: payerForm.payer_user_id || null,
      };
      const updated = await settingsService.updateBillingPayer(organizationId, payload);
      setSubscription(updated);
      syncFormsFromSubscription(updated);
      showSuccess(t('settings.billing.messages.payerUpdated'));
    } catch (err) {
      console.error('Error actualizando pagador:', err);
      setError(t('settings.billing.messages.errorPayerUpdate'));
    } finally {
      setSavingPayer(false);
    }
  };

  const handleRegisterPayment = async (event) => {
    event.preventDefault();
    try {
      setRegisteringPayment(true);
      setError(null);

      const payload = {
        payment_method: paymentForm.payment_method,
        amount: paymentForm.amount,
        currency: paymentForm.currency,
        due_date: paymentForm.due_date || null,
        reference: paymentForm.reference,
        evidence_file: paymentForm.evidence_file || null,
      };

      await settingsService.registerBillingPayment(organizationId, payload);
      showSuccess(t('settings.billing.messages.paymentRegistered'));
      await loadBillingData();
      setPaymentForm((prev) => ({ ...prev, reference: '', evidence_file: null }));
    } catch (err) {
      console.error('Error registrando pago:', err);
      setError(t('settings.billing.messages.errorRegisterPayment'));
    } finally {
      setRegisteringPayment(false);
    }
  };

  const handleEvaluateNow = async () => {
    try {
      setEvaluating(true);
      setError(null);
      const updated = await settingsService.evaluateBilling(organizationId);
      setSubscription(updated);
      syncFormsFromSubscription(updated);
      showSuccess(t('settings.billing.messages.statusEvaluated'));
    } catch (err) {
      console.error('Error evaluando billing:', err);
      setError(t('settings.billing.messages.errorEvaluate'));
    } finally {
      setEvaluating(false);
    }
  };

  const handleConfirmPayment = async (paymentId) => {
    try {
      setActionLoadingId(paymentId);
      setError(null);
      await settingsService.confirmBillingPayment(organizationId, paymentId);
      showSuccess(t('settings.billing.messages.paymentConfirmed'));
      await loadBillingData();
    } catch (err) {
      console.error('Error confirmando pago:', err);
      setError(t('settings.billing.messages.errorConfirmPayment'));
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRejectPayment = async (paymentId) => {
    const rejectionReason = window.prompt(t('settings.billing.prompts.rejectionReason'), '') || '';
    try {
      setActionLoadingId(paymentId);
      setError(null);
      await settingsService.rejectBillingPayment(organizationId, paymentId, rejectionReason);
      showSuccess(t('settings.billing.messages.paymentRejected'));
      await loadBillingData();
    } catch (err) {
      console.error('Error rechazando pago:', err);
      setError(t('settings.billing.messages.errorRejectPayment'));
    } finally {
      setActionLoadingId(null);
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/25">
            <CreditCard className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-800 dark:text-white">{t('settings.billing.title')}</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">{t('settings.billing.subtitle')}</p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleEvaluateNow}
          disabled={evaluating}
          className="px-4 py-2.5 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-600 transition-all flex items-center gap-2 disabled:opacity-60"
        >
          {evaluating ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCcw className="w-4 h-4" />}
          {t('settings.billing.actions.evaluateStatus')}
        </button>
      </div>

      {success && (
        <div className="p-4 bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-800 rounded-xl flex items-center gap-3">
          <Check className="w-5 h-5 text-emerald-500" />
          <span className="text-emerald-700 dark:text-emerald-300">{success}</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700 dark:text-red-300">{error}</span>
        </div>
      )}

      {subscription && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-700/40 dark:to-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-700">
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">{t('common.forms.status')}</p>
            <span className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${STATUS_STYLES[subscription.status] || STATUS_STYLES.cancelled}`}>
              {statusLabels[subscription.status] || subscription.status}
            </span>
          </div>

          <div className="p-4 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-700/40 dark:to-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-700">
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">{t('settings.billing.nextCharge')}</p>
            <p className="font-semibold text-slate-800 dark:text-white flex items-center gap-2">
              <CalendarClock className="w-4 h-4 text-indigo-500" />
              {formatDate(subscription.next_due_date)}
            </p>
          </div>

          <div className="p-4 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-700/40 dark:to-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-700">
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">{t('settings.billing.monthlyAmount')}</p>
            <p className="font-semibold text-slate-800 dark:text-white flex items-center gap-2">
              <Wallet className="w-4 h-4 text-indigo-500" />
              {subscription.monthly_price} {subscription.currency}
            </p>
          </div>
        </div>
      )}

      <form onSubmit={handleSavePayer} className="p-6 bg-white dark:bg-slate-800/50 rounded-2xl border border-slate-200 dark:border-slate-700 space-y-5">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
          <UserCircle2 className="w-5 h-5 text-indigo-500" />
          {t('settings.billing.payerConfigTitle')}
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('settings.billing.payerUser')}</label>
            <select
              name="payer_user_id"
              value={payerForm.payer_user_id}
              onChange={handlePayerChange}
              className="w-full px-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            >
              <option value="">{t('settings.billing.unassignedUser')}</option>
              {users.map((profile) => (
                <option key={profile.id} value={profile.user?.id || ''}>
                  {(profile.full_name || profile.user?.username || t('settings.billing.userFallback'))} - {profile.user?.email || t('settings.billing.noEmail')}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('settings.billing.paymentMethod')}</label>
            <select
              name="payment_method"
              value={payerForm.payment_method}
              onChange={handlePayerChange}
              className="w-full px-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            >
              {paymentMethodOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('settings.billing.payerName')}</label>
            <input
              name="payer_name"
              value={payerForm.payer_name}
              onChange={handlePayerChange}
              className="w-full px-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
              placeholder={t('settings.billing.payerNamePlaceholder')}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('settings.billing.payerEmail')}</label>
            <input
              name="payer_email"
              type="email"
              value={payerForm.payer_email}
              onChange={handlePayerChange}
              className="w-full px-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
              placeholder={t('settings.billing.payerEmailPlaceholder')}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('settings.billing.payerPhone')}</label>
            <input
              name="payer_phone"
              value={payerForm.payer_phone}
              onChange={handlePayerChange}
              className="w-full px-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
              placeholder={t('settings.billing.payerPhonePlaceholder')}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('settings.billing.monthlyPrice')}</label>
            <input
              name="monthly_price"
              type="number"
              min="0"
              step="0.01"
              value={payerForm.monthly_price}
              onChange={handlePayerChange}
              className="w-full px-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('settings.billing.currency')}</label>
            <input
              name="currency"
              value={payerForm.currency}
              onChange={handlePayerChange}
              className="w-full px-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
              placeholder={t('settings.billing.currencyPlaceholder')}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('settings.billing.graceDays')}</label>
            <input
              name="grace_days"
              type="number"
              min="0"
              value={payerForm.grace_days}
              onChange={handlePayerChange}
              className="w-full px-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            />
          </div>

          <label className="flex items-center gap-3 mt-8">
            <input
              name="auto_suspend_enabled"
              type="checkbox"
              checked={payerForm.auto_suspend_enabled}
              onChange={handlePayerChange}
              className="w-4 h-4 text-indigo-600 rounded"
            />
            <span className="text-sm text-slate-700 dark:text-slate-300">{t('settings.billing.autoSuspend')}</span>
          </label>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('common.forms.description')}</label>
          <textarea
            name="notes"
            value={payerForm.notes}
            onChange={handlePayerChange}
            rows={3}
            className="w-full px-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            placeholder={t('settings.billing.notesPlaceholder')}
          />
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={savingPayer || !canManageBilling}
            className="px-4 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-xl font-medium shadow-lg shadow-indigo-500/25 transition-all flex items-center gap-2 disabled:opacity-60"
            title={!canManageBilling ? t('settings.billing.noPermissionManage') : ''}
          >
            {savingPayer ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {t('settings.billing.actions.saveConfig')}
          </button>
        </div>
      </form>

      <form onSubmit={handleRegisterPayment} className="p-6 bg-white dark:bg-slate-800/50 rounded-2xl border border-slate-200 dark:border-slate-700 space-y-5">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
          <ReceiptText className="w-5 h-5 text-indigo-500" />
          {t('settings.billing.actions.registerPayment')}
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('settings.billing.paymentMethod')}</label>
            <select
              name="payment_method"
              value={paymentForm.payment_method}
              onChange={handlePaymentChange}
              className="w-full px-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            >
              {paymentMethodOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('settings.billing.amount')}</label>
            <input
              name="amount"
              type="number"
              min="0"
              step="0.01"
              value={paymentForm.amount}
              onChange={handlePaymentChange}
              required
              className="w-full px-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('settings.billing.currency')}</label>
            <input
              name="currency"
              value={paymentForm.currency}
              onChange={handlePaymentChange}
              className="w-full px-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('settings.billing.dueDate')}</label>
            <input
              name="due_date"
              type="date"
              value={paymentForm.due_date}
              onChange={handlePaymentChange}
              className="w-full px-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('settings.billing.paymentReference')}</label>
            <input
              name="reference"
              value={paymentForm.reference}
              onChange={handlePaymentChange}
              placeholder={t('settings.billing.paymentReferencePlaceholder')}
              className="w-full px-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('settings.billing.evidence')}</label>
            <input
              name="evidence_file"
              type="file"
              accept="application/pdf,image/*"
              onChange={handlePaymentChange}
              className="w-full px-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white file:mr-3 file:px-3 file:py-1.5 file:rounded-lg file:border-0 file:bg-indigo-100 file:text-indigo-700"
            />
            {paymentForm.evidence_file && (
              <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{t('settings.billing.selectedFile')}: {paymentForm.evidence_file.name}</p>
            )}
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={registeringPayment || !canManageBilling}
            className="px-4 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white rounded-xl font-medium shadow-lg shadow-emerald-500/25 transition-all flex items-center gap-2 disabled:opacity-60"
            title={!canManageBilling ? t('settings.billing.noPermissionRegister') : ''}
          >
            {registeringPayment ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {t('settings.billing.actions.registerPayment')}
          </button>
        </div>
      </form>

      <div className="p-6 bg-white dark:bg-slate-800/50 rounded-2xl border border-slate-200 dark:border-slate-700">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4">{t('settings.billing.recentPayments')}</h3>

        {payments.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">{t('settings.billing.noPayments')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="text-left py-3 px-2 text-sm font-semibold text-slate-600 dark:text-slate-300">{t('common.forms.date')}</th>
                  <th className="text-left py-3 px-2 text-sm font-semibold text-slate-600 dark:text-slate-300">{t('settings.billing.amount')}</th>
                  <th className="text-left py-3 px-2 text-sm font-semibold text-slate-600 dark:text-slate-300">{t('settings.billing.method')}</th>
                  <th className="text-left py-3 px-2 text-sm font-semibold text-slate-600 dark:text-slate-300">{t('settings.billing.paymentReference')}</th>
                  <th className="text-left py-3 px-2 text-sm font-semibold text-slate-600 dark:text-slate-300">{t('common.forms.status')}</th>
                  <th className="text-left py-3 px-2 text-sm font-semibold text-slate-600 dark:text-slate-300">{t('settings.billing.evidence')}</th>
                  <th className="text-right py-3 px-2 text-sm font-semibold text-slate-600 dark:text-slate-300">{t('settings.billing.tableActions')}</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((payment) => (
                  <tr key={payment.id} className="border-b border-slate-100 dark:border-slate-700/50">
                    <td className="py-3 px-2 text-sm text-slate-700 dark:text-slate-300">{formatDate(payment.created_at)}</td>
                    <td className="py-3 px-2 text-sm text-slate-700 dark:text-slate-300">{payment.amount} {payment.currency}</td>
                    <td className="py-3 px-2 text-sm text-slate-700 dark:text-slate-300">{paymentMethodOptions.find((option) => option.value === payment.payment_method)?.label || payment.payment_method}</td>
                    <td className="py-3 px-2 text-sm text-slate-700 dark:text-slate-300">{payment.reference || '-'}</td>
                    <td className="py-3 px-2">
                      <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold ${PAYMENT_STATUS_STYLES[payment.status] || PAYMENT_STATUS_STYLES.pending}`}>
                        {paymentStatusLabels[payment.status] || payment.status}
                      </span>
                    </td>
                    <td className="py-3 px-2 text-sm">
                      {payment.evidence_file ? (
                        <a
                          href={payment.evidence_file}
                          target="_blank"
                          rel="noreferrer"
                          className="text-indigo-600 dark:text-indigo-400 hover:underline"
                        >
                          {t('settings.billing.viewFile')}
                        </a>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </td>
                    <td className="py-3 px-2 text-right">
                      {payment.status === 'pending' && canManageBilling ? (
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleConfirmPayment(payment.id)}
                            disabled={actionLoadingId === payment.id}
                            className="px-3 py-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-900/40 rounded-lg hover:bg-emerald-200 dark:hover:bg-emerald-900/60 transition-colors flex items-center gap-1 disabled:opacity-60"
                          >
                            {actionLoadingId === payment.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle2 className="w-3 h-3" />}
                            {t('settings.billing.actions.confirm')}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleRejectPayment(payment.id)}
                            disabled={actionLoadingId === payment.id}
                            className="px-3 py-1.5 text-xs font-medium text-red-700 dark:text-red-300 bg-red-100 dark:bg-red-900/40 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/60 transition-colors flex items-center gap-1 disabled:opacity-60"
                          >
                            <XCircle className="w-3 h-3" />
                            {t('settings.billing.actions.reject')}
                          </button>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="p-6 bg-white dark:bg-slate-800/50 rounded-2xl border border-slate-200 dark:border-slate-700">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <History className="w-5 h-5 text-indigo-500" />
          {t('settings.billing.timeline.title')}
        </h3>

        {timelineLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
          </div>
        ) : timeline.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">{t('settings.billing.timeline.empty')}</p>
        ) : (
          <div className="space-y-3">
            {timeline.map((event) => {
              const badgeClass = actionStyleMap[event.action] || actionStyleMap.default;
              return (
                <div key={event.id} className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/60 dark:bg-slate-900/20">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${badgeClass}`}>
                        {event.action_display || event.action}
                      </span>
                      <span className="text-sm font-semibold text-slate-800 dark:text-slate-100">{event.description}</span>
                    </div>
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {new Date(event.created_at).toLocaleString(language === 'es-LATAM' ? 'es-ES' : language)}
                    </span>
                  </div>

                  <div className="text-xs text-slate-500 dark:text-slate-400 mb-2">
                    {t('settings.billing.timeline.user')}: {event.user_name || t('settings.billing.timeline.system')}
                  </div>

                  {(event.old_values && Object.keys(event.old_values).length > 0) || (event.new_values && Object.keys(event.new_values).length > 0) ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/40">
                        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">{t('settings.billing.timeline.before')}</p>
                        <pre className="text-[11px] text-slate-600 dark:text-slate-400 whitespace-pre-wrap break-all">
                          {JSON.stringify(event.old_values || {}, null, 2)}
                        </pre>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/40">
                        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">{t('settings.billing.timeline.after')}</p>
                        <pre className="text-[11px] text-slate-600 dark:text-slate-400 whitespace-pre-wrap break-all">
                          {JSON.stringify(event.new_values || {}, null, 2)}
                        </pre>
                      </div>
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default BillingSettings;
