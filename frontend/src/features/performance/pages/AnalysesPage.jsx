import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { showConfirm } from '../../../services/dialogs';
import {
  getAnalyses,
  createAnalysis,
  updateAnalysis,
  deleteAnalysis
} from '../api/performanceApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const AnalysesPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;

  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    title: '',
    analysis_type: 'trend',
    period_start: '',
    period_end: '',
    objectives: '',
    methodology: '',
    findings: '',
    conclusions: '',
    recommendations: '',
    status: 'draft'
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const analysisTypeLabels = useMemo(() => ({
    trend: t('modules.performance.analysesPage.types.trend'),
    comparative: t('modules.performance.analysesPage.types.comparative'),
    root_cause: t('modules.performance.analysesPage.types.rootCause'),
    predictive: t('modules.performance.analysesPage.types.predictive'),
    statistical: t('modules.performance.analysesPage.types.statistical'),
  }), [t]);

  const statusLabels = useMemo(() => ({
    draft: t('modules.performance.analysesPage.statuses.draft'),
    in_review: t('modules.performance.analysesPage.statuses.inReview'),
    completed: t('modules.performance.analysesPage.statuses.completed'),
    archived: t('modules.performance.analysesPage.statuses.archived'),
  }), [t]);

  const loadAnalyses = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getAnalyses({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error loading analyses:', error);
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  useEffect(() => {
    if (orgId) {
      loadAnalyses();
    }
  }, [orgId, loadAnalyses]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      setSaving(true);
      setError('');
      const payload = { ...form, organization_id: orgId };
      if (editingId) {
        await updateAnalysis(editingId, payload);
      } else {
        await createAnalysis(payload);
      }
      resetForm();
      await loadAnalyses();
      setShowForm(false);
    } catch (error) {
      console.error('Error saving analysis:', error);
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setForm({
      title: item.title || '',
      analysis_type: item.analysis_type || 'trend',
      period_start: item.period_start || '',
      period_end: item.period_end || '',
      objectives: item.objectives || '',
      methodology: item.methodology || '',
      findings: item.findings || '',
      conclusions: item.conclusions || '',
      recommendations: item.recommendations || '',
      status: item.status || 'draft'
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.performance.analysesPage.deleteConfirm'));
    if (!confirmed) return;
    try {
      setError('');
      await deleteAnalysis(id);
      await loadAnalyses();
    } catch (error) {
      console.error('Error deleting analysis:', error);
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const resetForm = () => {
    setForm({
      title: '',
      analysis_type: 'trend',
      period_start: '',
      period_end: '',
      objectives: '',
      methodology: '',
      findings: '',
      conclusions: '',
      recommendations: '',
      status: 'draft'
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
        title={t('modules.performance.analysesPage.title')}
        actionLabel={t('modules.performance.analysesPage.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.analysesPage.table.title')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.analysesPage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.analysesPage.table.period')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.analysesPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{item.title}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{analysisTypeLabels[item.analysis_type] || item.analysis_type}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.period_start} - {item.period_end}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{statusLabels[item.status] || item.status}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <CrudEmptyState message={t('modules.performance.analysesPage.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.performance.analysesPage.edit') : t('modules.performance.analysesPage.new')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.analysesPage.fields.title')}</label>
              <input
                type="text"
                value={form.title}
                onChange={(event) => setForm({ ...form, title: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.analysesPage.fields.type')}</label>
              <select
                value={form.analysis_type}
                onChange={(event) => setForm({ ...form, analysis_type: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              >
                {Object.entries(analysisTypeLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.analysesPage.fields.startPeriod')}</label>
              <input
                type="date"
                value={form.period_start}
                onChange={(event) => setForm({ ...form, period_start: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.analysesPage.fields.endPeriod')}</label>
              <input
                type="date"
                value={form.period_end}
                onChange={(event) => setForm({ ...form, period_end: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
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
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.analysesPage.fields.objectives')}</label>
              <textarea
                value={form.objectives}
                onChange={(event) => setForm({ ...form, objectives: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                rows="2"
                required
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.analysesPage.fields.methodology')}</label>
              <textarea
                value={form.methodology}
                onChange={(event) => setForm({ ...form, methodology: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                rows="2"
                required
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.analysesPage.fields.findings')}</label>
              <textarea
                value={form.findings}
                onChange={(event) => setForm({ ...form, findings: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                rows="2"
                required
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.analysesPage.fields.conclusions')}</label>
              <textarea
                value={form.conclusions}
                onChange={(event) => setForm({ ...form, conclusions: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                rows="2"
                required
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.analysesPage.fields.recommendations')}</label>
              <textarea
                value={form.recommendations}
                onChange={(event) => setForm({ ...form, recommendations: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                rows="2"
                required
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

export default AnalysesPage;