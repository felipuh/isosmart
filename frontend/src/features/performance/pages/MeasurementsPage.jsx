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
  getMeasurements,
  createMeasurement,
  updateMeasurement,
  deleteMeasurement
} from '../api/performanceApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const MeasurementsPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;

  const [indicators, setIndicators] = useState([]);
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    indicator: '',
    measurement_date: '',
    actual_value: '',
    target_value: '',
    status: 'on_target',
    comments: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const statusLabels = useMemo(() => ({
    on_target: t('modules.performance.measurementsPage.statuses.onTarget'),
    below_target: t('modules.performance.measurementsPage.statuses.belowTarget'),
    above_target: t('modules.performance.measurementsPage.statuses.aboveTarget'),
    needs_attention: t('modules.performance.measurementsPage.statuses.needsAttention'),
  }), [t]);

  const indicatorMap = useMemo(() => {
    return indicators.reduce((acc, indicator) => {
      acc[indicator.id] = indicator;
      return acc;
    }, {});
  }, [indicators]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const [indicatorsData, measurementsData] = await Promise.all([
        getIndicators({ organization_id: orgId }),
        getMeasurements({ organization_id: orgId })
      ]);
      setIndicators(normalizeList(indicatorsData));
      setItems(normalizeList(measurementsData));
    } catch (error) {
      console.error('Error loading measurements:', error);
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  useEffect(() => {
    if (orgId) {
      loadData();
    }
  }, [orgId, loadData]);

  const handleIndicatorChange = (value) => {
    const selected = indicatorMap[value];
    setForm((prev) => ({
      ...prev,
      indicator: value,
      target_value: selected?.target_value ?? prev.target_value
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      setSaving(true);
      setError('');
      const payload = {
        ...form,
        organization_id: orgId,
        indicator: Number(form.indicator),
        actual_value: form.actual_value === '' ? null : Number(form.actual_value),
        target_value: form.target_value === '' ? null : Number(form.target_value)
      };
      if (editingId) {
        await updateMeasurement(editingId, payload);
      } else {
        await createMeasurement(payload);
      }
      resetForm();
      await loadData();
      setShowForm(false);
    } catch (error) {
      console.error('Error saving measurement:', error);
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setForm({
      indicator: item.indicator,
      measurement_date: item.measurement_date || '',
      actual_value: item.actual_value ?? '',
      target_value: item.target_value ?? '',
      status: item.status || 'on_target',
      comments: item.comments || ''
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.performance.measurementsPage.deleteConfirm'));
    if (!confirmed) return;
    try {
      setError('');
      await deleteMeasurement(id);
      await loadData();
    } catch (error) {
      console.error('Error deleting measurement:', error);
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const resetForm = () => {
    setForm({
      indicator: '',
      measurement_date: '',
      actual_value: '',
      target_value: '',
      status: 'on_target',
      comments: ''
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
        title={t('modules.performance.measurementsPage.title')}
        actionLabel={t('modules.performance.measurementsPage.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.date')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.measurementsPage.table.indicator')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.measurementsPage.table.actual')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.measurementsPage.table.target')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.measurementsPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.measurement_date}</td>
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">
                  {item.indicator_detail?.code || indicatorMap[item.indicator]?.code}
                </td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.actual_value}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.target_value}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{statusLabels[item.status] || item.status}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <CrudEmptyState message={t('modules.performance.measurementsPage.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.performance.measurementsPage.edit') : t('modules.performance.measurementsPage.new')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.measurementsPage.fields.indicator')}</label>
              <select
                value={form.indicator}
                onChange={(event) => handleIndicatorChange(event.target.value)}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              >
                <option value="">{t('modules.performance.measurementsPage.fields.selectIndicator')}</option>
                {indicators.map((indicator) => (
                  <option key={indicator.id} value={indicator.id}>
                    {indicator.code} - {indicator.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.measurementsPage.fields.measurementDate')}</label>
              <input
                type="date"
                value={form.measurement_date}
                onChange={(event) => setForm({ ...form, measurement_date: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.measurementsPage.fields.status')}</label>
              <select
                value={form.status}
                onChange={(event) => setForm({ ...form, status: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              >
                {Object.entries(statusLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.measurementsPage.fields.actualValue')}</label>
              <input
                type="number"
                step="0.01"
                value={form.actual_value}
                onChange={(event) => setForm({ ...form, actual_value: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.measurementsPage.fields.targetValue')}</label>
              <input
                type="number"
                step="0.01"
                value={form.target_value}
                onChange={(event) => setForm({ ...form, target_value: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.measurementsPage.fields.comments')}</label>
              <textarea
                value={form.comments}
                onChange={(event) => setForm({ ...form, comments: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                rows="3"
              />
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

export default MeasurementsPage;