import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { showConfirm } from '../../../services/dialogs';
import {
  getAudits,
  getFindings,
  createFinding,
  updateFinding,
  deleteFinding
} from '../api/performanceApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const FindingsPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;

  const [audits, setAudits] = useState([]);
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    audit: '',
    finding_number: '',
    finding_type: 'nc_minor',
    clause_reference: '',
    description: '',
    evidence: '',
    status: 'open',
    due_date: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const findingTypeLabels = useMemo(() => ({
    nc_major: t('modules.performance.findingsPage.types.ncMajor'),
    nc_minor: t('modules.performance.findingsPage.types.ncMinor'),
    observation: t('modules.performance.findingsPage.types.observation'),
    opportunity: t('modules.performance.findingsPage.types.opportunity'),
    conformity: t('modules.performance.findingsPage.types.conformity'),
  }), [t]);

  const statusLabels = useMemo(() => ({
    open: t('modules.performance.findingsPage.statuses.open'),
    in_progress: t('modules.performance.findingsPage.statuses.inProgress'),
    resolved: t('modules.performance.findingsPage.statuses.resolved'),
    verified: t('modules.performance.findingsPage.statuses.verified'),
    closed: t('modules.performance.findingsPage.statuses.closed'),
  }), [t]);

  const auditMap = useMemo(() => {
    return audits.reduce((acc, audit) => {
      acc[audit.id] = audit;
      return acc;
    }, {});
  }, [audits]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const [auditsData, findingsData] = await Promise.all([
        getAudits({ organization_id: orgId }),
        getFindings({ organization_id: orgId })
      ]);
      setAudits(normalizeList(auditsData));
      setItems(normalizeList(findingsData));
    } catch (error) {
      console.error('Error loading findings:', error);
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

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      setSaving(true);
      setError('');
      const payload = {
        ...form,
        organization_id: orgId,
        audit: Number(form.audit) || null
      };
      if (editingId) {
        await updateFinding(editingId, payload);
      } else {
        await createFinding(payload);
      }
      resetForm();
      await loadData();
      setShowForm(false);
    } catch (error) {
      console.error('Error saving finding:', error);
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setForm({
      audit: item.audit,
      finding_number: item.finding_number || '',
      finding_type: item.finding_type || 'nc_minor',
      clause_reference: item.clause_reference || '',
      description: item.description || '',
      evidence: item.evidence || '',
      status: item.status || 'open',
      due_date: item.due_date || ''
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.performance.findingsPage.deleteConfirm'));
    if (!confirmed) return;
    try {
      setError('');
      await deleteFinding(id);
      await loadData();
    } catch (error) {
      console.error('Error deleting finding:', error);
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const resetForm = () => {
    setForm({
      audit: '',
      finding_number: '',
      finding_type: 'nc_minor',
      clause_reference: '',
      description: '',
      evidence: '',
      status: 'open',
      due_date: ''
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
        title={t('modules.performance.findingsPage.title')}
        actionLabel={t('modules.performance.findingsPage.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.findingsPage.table.finding')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.findingsPage.table.audit')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.findingsPage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.performance.findingsPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.finding_number}</td>
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">
                  {auditMap[item.audit]?.audit_code || item.audit}
                </td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{findingTypeLabels[item.finding_type] || item.finding_type}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{statusLabels[item.status] || item.status}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <CrudEmptyState message={t('modules.performance.findingsPage.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.performance.findingsPage.edit') : t('modules.performance.findingsPage.new')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.findingsPage.fields.audit')}</label>
              <select
                value={form.audit}
                onChange={(event) => setForm({ ...form, audit: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              >
                <option value="">{t('modules.performance.findingsPage.fields.selectAudit')}</option>
                {audits.map((audit) => (
                  <option key={audit.id} value={audit.id}>
                    {audit.audit_code} - {audit.title}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.findingsPage.fields.findingNumber')}</label>
              <input
                type="text"
                value={form.finding_number}
                onChange={(event) => setForm({ ...form, finding_number: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.findingsPage.fields.type')}</label>
              <select
                value={form.finding_type}
                onChange={(event) => setForm({ ...form, finding_type: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              >
                {Object.entries(findingTypeLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.findingsPage.fields.clauseReference')}</label>
              <input
                type="text"
                value={form.clause_reference}
                onChange={(event) => setForm({ ...form, clause_reference: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.findingsPage.fields.dueDate')}</label>
              <input
                type="date"
                value={form.due_date}
                onChange={(event) => setForm({ ...form, due_date: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
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
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.findingsPage.fields.description')}</label>
              <textarea
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                rows="3"
                required
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.performance.findingsPage.fields.evidence')}</label>
              <textarea
                value={form.evidence}
                onChange={(event) => setForm({ ...form, evidence: event.target.value })}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                rows="2"
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

export default FindingsPage;