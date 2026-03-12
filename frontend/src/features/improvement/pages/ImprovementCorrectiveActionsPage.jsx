import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import { useLocation, useNavigate } from 'react-router-dom';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { getCorrectiveActions, createCorrectiveAction, updateCorrectiveAction, deleteCorrectiveAction, getNonconformities } from '../api/improvementApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];
const statusColors = { planned: 'bg-gray-500/20 text-gray-400', in_progress: 'bg-blue-500/20 text-blue-400', implemented: 'bg-purple-500/20 text-purple-400', verified: 'bg-cyan-500/20 text-cyan-400', effective: 'bg-green-500/20 text-green-400', not_effective: 'bg-red-500/20 text-red-400', cancelled: 'bg-gray-500/20 text-gray-400' };

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

  const handleDelete = async (id) => { if (!confirm(t('modules.improvement.correctiveActionsPage.deleteConfirm'))) return; try { setError(''); await deleteCorrectiveAction(id); await loadData(); } catch (error) { console.error('Error:', error); setError(t('common.messages.errorTryAgain')); } };
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
              <label className="text-xs text-slate-400">{t('modules.improvement.correctiveActionsPage.fields.actionNumber')}<input type="text" required value={form.action_number} onChange={e => setForm({ ...form, action_number: e.target.value })} placeholder={t('modules.improvement.correctiveActionsPage.placeholders.actionNumber')} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"  /></label>
              <label className="text-xs text-slate-400">{t('modules.improvement.correctiveActionsPage.fields.relatedNc')}
                <select required value={form.nonconformity} onChange={e => setForm({ ...form, nonconformity: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                  <option value="">{t('modules.improvement.correctiveActionsPage.fields.selectNc')}</option>
                  {ncs.map(nc => <option key={nc.id} value={nc.id}>{nc.nc_number} - {nc.title}</option>)}
                </select>
              </label>
              <label className="text-xs text-slate-400">{t('modules.improvement.correctiveActionsPage.fields.type')}
                <select value={form.action_type} onChange={e => setForm({ ...form, action_type: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                  {Object.entries(actionTypeLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="text-xs text-slate-400">{t('modules.improvement.correctiveActionsPage.fields.rootCauseAnalysis')}<textarea required value={form.root_cause_analysis} onChange={e => setForm({ ...form, root_cause_analysis: e.target.value })} placeholder={t('modules.improvement.correctiveActionsPage.placeholders.rootCauseAnalysis')} className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"  /></label>
              <label className="text-xs text-slate-400">{t('modules.improvement.correctiveActionsPage.fields.rootCauseIdentified')}<textarea required value={form.root_cause_identified} onChange={e => setForm({ ...form, root_cause_identified: e.target.value })} className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"  /></label>
            </div>
            <label className="text-xs text-slate-400 block">{t('modules.improvement.correctiveActionsPage.fields.analysisMethod')}<input type="text" value={form.analysis_method} onChange={e => setForm({ ...form, analysis_method: e.target.value })} placeholder={t('modules.improvement.correctiveActionsPage.placeholders.analysisMethod')} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"  /></label>
            <label className="text-xs text-slate-400 block">{t('modules.improvement.correctiveActionsPage.fields.actionDescription')}<textarea required value={form.action_description} onChange={e => setForm({ ...form, action_description: e.target.value })} className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"  /></label>
            <label className="text-xs text-slate-400 block">{t('modules.improvement.correctiveActionsPage.fields.implementationSteps')}<textarea required value={form.implementation_steps} onChange={e => setForm({ ...form, implementation_steps: e.target.value })} className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"  /></label>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="text-xs text-slate-400">{t('modules.improvement.correctiveActionsPage.fields.requiredResources')}<textarea value={form.resources_required} onChange={e => setForm({ ...form, resources_required: e.target.value })} className="mt-1 h-16 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"  /></label>
              <label className="text-xs text-slate-400">{t('modules.improvement.correctiveActionsPage.fields.plannedStart')}<input type="date" required value={form.planned_start_date} onChange={e => setForm({ ...form, planned_start_date: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"  /></label>
              <label className="text-xs text-slate-400">{t('modules.improvement.correctiveActionsPage.fields.plannedEnd')}<input type="date" required value={form.planned_completion_date} onChange={e => setForm({ ...form, planned_completion_date: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"  /></label>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="text-xs text-slate-400">{t('common.forms.status')}
                <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                  {Object.entries(statusLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <label className="text-xs text-slate-400">{t('modules.improvement.correctiveActionsPage.fields.completionPercentage')}<input type="number" min="0" max="100" value={form.completion_percentage} onChange={e => setForm({ ...form, completion_percentage: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"  /></label>
              <label className="text-xs text-slate-400">{t('modules.improvement.correctiveActionsPage.fields.comments')}<input type="text" value={form.comments} onChange={e => setForm({ ...form, comments: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"  /></label>
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="submit" disabled={saving || !orgId} className="rounded-lg bg-emerald-500/80 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50">{saving ? t('common.messages.saving') : editingId ? t('common.buttons.update') : t('common.buttons.create')}</button>
              <button type="button" onClick={closeForm} className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-200">{t('common.buttons.cancel')}</button>
            </div>
        </form>
      </Modal>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.improvement.correctiveActionsPage.table.code')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.improvement.correctiveActionsPage.table.nc')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.improvement.correctiveActionsPage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.improvement.correctiveActionsPage.table.progress')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.improvement.correctiveActionsPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700/30">
            {items.length === 0 ? (
              <CrudEmptyState colSpan={6} message={t('modules.improvement.correctiveActionsPage.empty')} />
            ) : items.map(item => (
              <tr key={item.id} className="hover:bg-gray-800/30">
                <td className="px-6 py-4 text-sm font-mono text-blue-400">{item.action_number}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{item.nonconformity_number || t('modules.improvement.correctiveActionsPage.table.ncFallback').replace('{id}', item.nonconformity)}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{actionTypeLabels[item.action_type] || item.action_type}</td>
                <td className="px-6 py-4"><div className="flex items-center gap-2"><div className="w-20 bg-gray-700 rounded-full h-2"><div className="bg-blue-500 h-2 rounded-full" style={{ width: `${item.completion_percentage || 0}%` }}></div></div><span className="text-xs text-gray-400">{item.completion_percentage || 0}%</span></div></td>
                <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${statusColors[item.status] || ''}`}>{statusLabels[item.status] || item.status}</span></td>
                <td className="px-6 py-4 space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-400 hover:text-blue-300 text-sm">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-400 hover:text-red-300 text-sm">{t('common.buttons.delete')}</button>
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