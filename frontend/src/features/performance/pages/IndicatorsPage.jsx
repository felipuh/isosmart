import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { showConfirm } from '../../../services/dialogs';
import {
  getIndicators,
  createIndicator,
  updateIndicator,
  deleteIndicator
} from '../api/performanceApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const IndicatorsPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';

  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    code: '',
    name: '',
    description: '',
    indicator_type: 'quality',
    measurement_method: '',
    formula: '',
    target_value: '',
    unit_of_measure: '',
    frequency: 'monthly',
    status: 'active'
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const indicatorTypeLabels = useMemo(() => ({
    quality: t('modules.performance.indicatorsPage.types.quality'),
    efficiency: t('modules.performance.indicatorsPage.types.efficiency'),
    effectiveness: t('modules.performance.indicatorsPage.types.effectiveness'),
    customer_satisfaction: t('modules.performance.indicatorsPage.types.customerSatisfaction'),
    process: t('modules.performance.indicatorsPage.types.processPerformance'),
    financial: t('modules.performance.indicatorsPage.types.financial'),
    operational: t('modules.performance.indicatorsPage.types.operational'),
  }), [t]);

  const frequencyLabels = useMemo(() => ({
    daily: t('modules.performance.indicatorsPage.frequencies.daily'),
    weekly: t('modules.performance.indicatorsPage.frequencies.weekly'),
    monthly: t('modules.performance.indicatorsPage.frequencies.monthly'),
    quarterly: t('modules.performance.indicatorsPage.frequencies.quarterly'),
    annually: t('modules.performance.indicatorsPage.frequencies.annually'),
  }), [t]);

  const statusLabels = useMemo(() => ({
    active: t('modules.performance.indicatorsPage.statuses.active'),
    inactive: t('modules.performance.indicatorsPage.statuses.inactive'),
    archived: t('modules.performance.indicatorsPage.statuses.archived'),
  }), [t]);

  const loadIndicators = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getIndicators({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error loading indicators:', error);
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  useEffect(() => {
    if (orgId) {
      loadIndicators();
    }
  }, [orgId, loadIndicators]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      setSaving(true);
      setError('');
      const payload = {
        ...form,
        organization_id: orgId,
        organization_name: orgName,
        target_value: form.target_value === '' ? null : Number(form.target_value)
      };
      if (editingId) {
        await updateIndicator(editingId, payload);
      } else {
        await createIndicator(payload);
      }
      resetForm();
      await loadIndicators();
      setShowForm(false);
    } catch (error) {
      console.error('Error saving indicator:', error);
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setForm({
      code: item.code || '',
      name: item.name || '',
      description: item.description || '',
      indicator_type: item.indicator_type || 'quality',
      measurement_method: item.measurement_method || '',
      formula: item.formula || '',
      target_value: item.target_value ?? '',
      unit_of_measure: item.unit_of_measure || '',
      frequency: item.frequency || 'monthly',
      status: item.status || 'active'
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.performance.indicatorsPage.deleteConfirm'));
    if (!confirmed) return;
    try {
      setError('');
      await deleteIndicator(id);
      await loadIndicators();
    } catch (error) {
      console.error('Error deleting indicator:', error);
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const resetForm = () => {
    setForm({
      code: '',
      name: '',
      description: '',
      indicator_type: 'quality',
      measurement_method: '',
      formula: '',
      target_value: '',
      unit_of_measure: '',
      frequency: 'monthly',
      status: 'active'
    });
    setEditingId(null);
  };

  const openForm = () => {
    resetForm();
    setShowForm(true);
  };

  const closeForm = () => {
    resetForm();
    setShowForm(false);
  };

  if (loading) {
    return (
      <div className="flex justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <CrudPageHeader
        title={t('modules.performance.indicatorsPage.title')}
        actionLabel={t('modules.performance.indicatorsPage.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.indicatorsPage.table.code')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.name')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.indicatorsPage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.indicatorsPage.table.frequency')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.indicatorsPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.code}</td>
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{item.name}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{indicatorTypeLabels[item.indicator_type] || item.indicator_type}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{frequencyLabels[item.frequency] || item.frequency}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{statusLabels[item.status] || item.status}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <CrudEmptyState message={t('modules.performance.indicatorsPage.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.performance.indicatorsPage.edit') : t('modules.performance.indicatorsPage.new')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.indicatorsPage.fields.code')}</label>
              <input
                type="text"
                value={form.code}
                onChange={(event) => setForm({ ...form, code: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.indicatorsPage.fields.name')}</label>
              <input
                type="text"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.indicatorsPage.fields.type')}</label>
              <select
                value={form.indicator_type}
                onChange={(event) => setForm({ ...form, indicator_type: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              >
                {Object.entries(indicatorTypeLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.indicatorsPage.fields.frequency')}</label>
              <select
                value={form.frequency}
                onChange={(event) => setForm({ ...form, frequency: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              >
                {Object.entries(frequencyLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.indicatorsPage.fields.measurementMethod')}</label>
              <input
                type="text"
                value={form.measurement_method}
                onChange={(event) => setForm({ ...form, measurement_method: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.indicatorsPage.fields.targetValue')}</label>
              <input
                type="number"
                step="0.01"
                value={form.target_value}
                onChange={(event) => setForm({ ...form, target_value: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.indicatorsPage.fields.unit')}</label>
              <input
                type="text"
                value={form.unit_of_measure}
                onChange={(event) => setForm({ ...form, unit_of_measure: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.indicatorsPage.fields.formula')}</label>
              <input
                type="text"
                value={form.formula}
                onChange={(event) => setForm({ ...form, formula: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.indicatorsPage.fields.description')}</label>
              <textarea
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                rows="3"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('common.forms.status')}</label>
              <select
                value={form.status}
                onChange={(event) => setForm({ ...form, status: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
              >
                {Object.entries(statusLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex space-x-3">
            <button type="submit" disabled={saving} className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
              {saving ? t('common.messages.saving') : editingId ? t('common.buttons.update') : t('common.buttons.create')}
            </button>
            <button type="button" onClick={closeForm} className="px-6 py-2 bg-slate-500 hover:bg-slate-600 dark:bg-slate-600 dark:hover:bg-slate-500 text-white rounded-lg">{t('common.buttons.cancel')}</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default IndicatorsPage;