import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import { useLocation, useNavigate } from 'react-router-dom';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { showConfirm } from '../../../services/dialogs';
import { getCorrectiveActions, createCorrectiveAction, updateCorrectiveAction, deleteCorrectiveAction, getNonconformities } from '../api/improvementApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];
const statusColors = { planned: 'badge-base badge-neutral', in_progress: 'badge-base badge-info', implemented: 'badge-base badge-accent', verified: 'badge-base badge-cyan', effective: 'badge-base badge-success', not_effective: 'badge-base badge-danger', cancelled: 'badge-base badge-neutral' };

const initialForm = { nonconformity: '', action_number: '', action_type: 'corrective', root_cause_analysis: '', root_cause_identified: '', analysis_method: '', action_description: '', implementation_steps: '', resources_required: '', planned_start_date: '', planned_completion_date: '', verification_method: '', effectiveness_criteria: '', status: 'planned', completion_percentage: 0, comments: '' };

const ImprovementCorrectiveActionsPage = () => {
  const { t } = useI18n();
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [ncs, setNcs] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const actionTypeLabels = useMemo(() => ({
    corrective: t('modules.improvement.correctiveActionsPage.types.corrective'),
    preventive: t('modules.improvement.correctiveActionsPage.types.preventive'),
    improvement: t('modules.improvement.correctiveActionsPage.types.improvement'),
  }), [t]);

  const statusLabels = useMemo(() => ({
    planned: t('modules.improvement.correctiveActionsPage.statuses.planned'),
    in_progress: t('modules.improvement.correctiveActionsPage.statuses.inProgress'),
    implemented: t('modules.improvement.correctiveActionsPage.statuses.implemented'),
    verified: t('modules.improvement.correctiveActionsPage.statuses.verified'),
    effective: t('modules.improvement.correctiveActionsPage.statuses.effective'),
    not_effective: t('modules.improvement.correctiveActionsPage.statuses.notEffective'),
    cancelled: t('modules.improvement.correctiveActionsPage.statuses.cancelled'),
  }), [t]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const [actionsData, ncsData] = await Promise.all([getCorrectiveActions({ organization_id: orgId }), getNonconformities({ organization_id: orgId })]);
      setItems(normalizeList(actionsData));
      setNcs(normalizeList(ncsData));
    } catch (error) { console.error('Error:', error); setError(t('common.messages.errorTryAgain')); } finally { setLoading(false); }
  }, [orgId, t]);

  useEffect(() => { if (orgId) loadData(); }, [orgId, loadData]);
  useEffect(() => { if (location.pathname.endsWith('/new')) { resetForm(); setShowForm(true); } }, [location.pathname]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError('');
      const payload = { ...form, organization_id: orgId, responsible: user?.id || null, completion_percentage: Number(form.completion_percentage), nonconformity: form.nonconformity || null };
      if (editingId) { await updateCorrectiveAction(editingId, payload); } else { await createCorrectiveAction(payload); }
      resetForm(); await loadData(); setShowForm(false);
      if (location.pathname.endsWith('/new')) navigate(location.pathname.replace(/\/new$/, ''), { replace: true });
    } catch (error) { console.error('Error:', error); setError(t('common.messages.errorTryAgain')); } finally { setSaving(false); }
  };

  const handleEdit = (item) => {
    setForm({ nonconformity: item.nonconformity || '', action_number: item.action_number || '', action_type: item.action_type || 'corrective', root_cause_analysis: item.root_cause_analysis || '', root_cause_identified: item.root_cause_identified || '', analysis_method: item.analysis_method || '', action_description: item.action_description || '', implementation_steps: item.implementation_steps || '', resources_required: item.resources_required || '', planned_start_date: item.planned_start_date || '', planned_completion_date: item.planned_completion_date || '', verification_method: item.verification_method || '', effectiveness_criteria: item.effectiveness_criteria || '', status: item.status || 'planned', completion_percentage: item.completion_percentage || 0, comments: item.comments || '' });
    setEditingId(item.id); setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.improvement.correctiveActionsPage.deleteConfirm'));
    if (!confirmed) return;
    try {
      setError('');
      await deleteCorrectiveAction(id);
      await loadData();
    } catch (error) {
      console.error('Error:', error);
      setError(t('common.messages.errorTryAgain'));
    }
  };
  const resetForm = () => { setForm(initialForm); setEditingId(null); };
  const openForm = () => { resetForm(); setShowForm(true); };
  const closeForm = () => { resetForm(); setShowForm(false); if (location.pathname.endsWith('/new')) navigate(location.pathname.replace(/\/new$/, ''), { replace: true }); };

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="space-y-6">
      <CrudPageHeader
        title={t('modules.improvement.correctiveActionsPage.title')}
        subtitle={t('modules.improvement.correctiveActionsPage.isoClause')}
        actionLabel={t('modules.improvement.correctiveActionsPage.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <Modal
        title={editingId ? t('modules.improvement.correctiveActionsPage.edit') : t('modules.improvement.correctiveActionsPage.new')}
        isOpen={showForm}
        onClose={closeForm}
        maxWidth="max-w-6xl"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="form-label-muted">{t('modules.improvement.correctiveActionsPage.fields.actionNumber')}<input type="text" required value={form.action_number} onChange={e => setForm({ ...form, action_number: e.target.value })} placeholder={t('modules.improvement.correctiveActionsPage.placeholders.actionNumber')} className="field-control"  /></label>
              <label className="form-label-muted">{t('modules.improvement.correctiveActionsPage.fields.relatedNc')}
                <select required value={form.nonconformity} onChange={e => setForm({ ...form, nonconformity: e.target.value })} className="field-control">
                  <option value="">{t('modules.improvement.correctiveActionsPage.fields.selectNc')}</option>
                  {ncs.map(nc => <option key={nc.id} value={nc.id}>{nc.nc_number} - {nc.title}</option>)}
                </select>
              </label>
              <label className="form-label-muted">{t('modules.improvement.correctiveActionsPage.fields.type')}
                <select value={form.action_type} onChange={e => setForm({ ...form, action_type: e.target.value })} className="field-control">
                  {Object.entries(actionTypeLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="form-label-muted">{t('modules.improvement.correctiveActionsPage.fields.rootCauseAnalysis')}<textarea required value={form.root_cause_analysis} onChange={e => setForm({ ...form, root_cause_analysis: e.target.value })} placeholder={t('modules.improvement.correctiveActionsPage.placeholders.rootCauseAnalysis')} className="field-control h-20"  /></label>
              <label className="form-label-muted">{t('modules.improvement.correctiveActionsPage.fields.rootCauseIdentified')}<textarea required value={form.root_cause_identified} onChange={e => setForm({ ...form, root_cause_identified: e.target.value })} className="field-control h-20"  /></label>
            </div>
            <label className="form-label-muted block">{t('modules.improvement.correctiveActionsPage.fields.analysisMethod')}<input type="text" value={form.analysis_method} onChange={e => setForm({ ...form, analysis_method: e.target.value })} placeholder={t('modules.improvement.correctiveActionsPage.placeholders.analysisMethod')} className="field-control"  /></label>
            <label className="form-label-muted block">{t('modules.improvement.correctiveActionsPage.fields.actionDescription')}<textarea required value={form.action_description} onChange={e => setForm({ ...form, action_description: e.target.value })} className="field-control h-20"  /></label>
            <label className="form-label-muted block">{t('modules.improvement.correctiveActionsPage.fields.implementationSteps')}<textarea required value={form.implementation_steps} onChange={e => setForm({ ...form, implementation_steps: e.target.value })} className="field-control h-20"  /></label>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="form-label-muted">{t('modules.improvement.correctiveActionsPage.fields.requiredResources')}<textarea value={form.resources_required} onChange={e => setForm({ ...form, resources_required: e.target.value })} className="field-control h-16"  /></label>
              <label className="form-label-muted">{t('modules.improvement.correctiveActionsPage.fields.plannedStart')}<input type="date" required value={form.planned_start_date} onChange={e => setForm({ ...form, planned_start_date: e.target.value })} className="field-control"  /></label>
              <label className="form-label-muted">{t('modules.improvement.correctiveActionsPage.fields.plannedEnd')}<input type="date" required value={form.planned_completion_date} onChange={e => setForm({ ...form, planned_completion_date: e.target.value })} className="field-control"  /></label>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="form-label-muted">{t('common.forms.status')}
                <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className="field-control">
                  {Object.entries(statusLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <label className="form-label-muted">{t('modules.improvement.correctiveActionsPage.fields.completionPercentage')}<input type="number" min="0" max="100" value={form.completion_percentage} onChange={e => setForm({ ...form, completion_percentage: e.target.value })} className="field-control"  /></label>
              <label className="form-label-muted">{t('modules.improvement.correctiveActionsPage.fields.comments')}<input type="text" value={form.comments} onChange={e => setForm({ ...form, comments: e.target.value })} className="field-control"  /></label>
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="submit" disabled={saving || !orgId} className="rounded-lg bg-emerald-500/80 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50">{saving ? t('common.messages.saving') : editingId ? t('common.buttons.update') : t('common.buttons.create')}</button>
              <button type="button" onClick={closeForm} className="rounded-lg border border-slate-300 dark:border-slate-700 px-4 py-2 text-sm text-slate-700 dark:text-slate-200">{t('common.buttons.cancel')}</button>
            </div>
        </form>
      </Modal>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.improvement.correctiveActionsPage.table.code')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.improvement.correctiveActionsPage.table.nc')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.improvement.correctiveActionsPage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.improvement.correctiveActionsPage.table.progress')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.improvement.correctiveActionsPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.length === 0 ? (
              <CrudEmptyState colSpan={6} message={t('modules.improvement.correctiveActionsPage.empty')} />
            ) : items.map(item => (
              <tr key={item.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 table-code">{item.action_number}</td>
                <td className="px-6 py-4 table-secondary-text">{item.nonconformity_number || t('modules.improvement.correctiveActionsPage.table.ncFallback').replace('{id}', item.nonconformity)}</td>
                <td className="px-6 py-4 table-secondary-text">{actionTypeLabels[item.action_type] || item.action_type}</td>
                <td className="px-6 py-4"><div className="flex items-center gap-2"><div className="progress-track"><div className="progress-fill-info" style={{ width: `${item.completion_percentage || 0}%` }}></div></div><span className="table-tertiary-text">{item.completion_percentage || 0}%</span></div></td>
                <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${statusColors[item.status] || ''}`}>{statusLabels[item.status] || item.status}</span></td>
                <td className="px-6 py-4 space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 text-sm">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 text-sm">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ImprovementCorrectiveActionsPage;