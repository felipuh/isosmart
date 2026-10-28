import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import { useLocation, useNavigate } from 'react-router-dom';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { showConfirm } from '../../../services/dialogs';
import { getContinualImprovements, createContinualImprovement, updateContinualImprovement, deleteContinualImprovement } from '../api/improvementApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];
const statusColors = { proposed: 'badge-base badge-neutral', under_evaluation: 'badge-base badge-info', approved: 'badge-base badge-cyan', in_progress: 'badge-base badge-caution', implemented: 'badge-base badge-accent', measuring_results: 'badge-base badge-warning', successful: 'badge-base badge-success', unsuccessful: 'badge-base badge-danger', cancelled: 'badge-base badge-neutral' };
const priorityColors = { critical: 'badge-base badge-danger', high: 'badge-base badge-caution', medium: 'badge-base badge-warning', low: 'badge-base badge-success' };

const initialForm = { initiative_number: '', title: '', description: '', improvement_type: 'process', current_situation: '', proposed_improvement: '', expected_benefits: '', alignment_with_objectives: '', estimated_investment: '', estimated_savings: '', expected_roi: '', priority: 'medium', proposed_date: '', status: 'proposed', completion_percentage: 0 };

const ImprovementContinualPage = () => {
  const { t } = useI18n();
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const improvementTypeLabels = useMemo(() => ({
    process: t('modules.improvement.continualPage.types.process'),
    product: t('modules.improvement.continualPage.types.product'),
    service: t('modules.improvement.continualPage.types.service'),
    system: t('modules.improvement.continualPage.types.system'),
    technology: t('modules.improvement.continualPage.types.technology'),
    methodology: t('modules.improvement.continualPage.types.methodology'),
  }), [t]);

  const priorityLabels = useMemo(() => ({
    critical: t('modules.improvement.continualPage.priorities.critical'),
    high: t('modules.improvement.continualPage.priorities.high'),
    medium: t('modules.improvement.continualPage.priorities.medium'),
    low: t('modules.improvement.continualPage.priorities.low'),
  }), [t]);

  const statusLabels = useMemo(() => ({
    proposed: t('modules.improvement.continualPage.statuses.proposed'),
    under_evaluation: t('modules.improvement.continualPage.statuses.underEvaluation'),
    approved: t('modules.improvement.continualPage.statuses.approved'),
    in_progress: t('modules.improvement.continualPage.statuses.inProgress'),
    implemented: t('modules.improvement.continualPage.statuses.implemented'),
    measuring_results: t('modules.improvement.continualPage.statuses.measuringResults'),
    successful: t('modules.improvement.continualPage.statuses.successful'),
    unsuccessful: t('modules.improvement.continualPage.statuses.unsuccessful'),
    cancelled: t('modules.improvement.continualPage.statuses.cancelled'),
  }), [t]);

  const loadData = useCallback(async () => {
    try { setLoading(true); setError(''); const data = await getContinualImprovements({ organization_id: orgId }); setItems(normalizeList(data)); }
    catch (error) { console.error('Error:', error); setError(t('common.messages.errorTryAgain')); } finally { setLoading(false); }
  }, [orgId, t]);

  useEffect(() => { if (orgId) loadData(); }, [orgId, loadData]);
  useEffect(() => { if (location.pathname.endsWith('/new')) { resetForm(); setShowForm(true); } }, [location.pathname]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError('');
      const payload = { ...form, organization_id: orgId, organization_name: orgName, champion: user?.id || null, completion_percentage: Number(form.completion_percentage), estimated_investment: form.estimated_investment === '' ? null : Number(form.estimated_investment), estimated_savings: form.estimated_savings === '' ? null : Number(form.estimated_savings), expected_roi: form.expected_roi === '' ? null : Number(form.expected_roi) };
      if (editingId) { await updateContinualImprovement(editingId, payload); } else { await createContinualImprovement(payload); }
      resetForm(); await loadData(); setShowForm(false);
      if (location.pathname.endsWith('/new')) navigate(location.pathname.replace(/\/new$/, ''), { replace: true });
    } catch (error) { console.error('Error:', error); setError(t('common.messages.errorTryAgain')); } finally { setSaving(false); }
  };

  const handleEdit = (item) => {
    setForm({ initiative_number: item.initiative_number || '', title: item.title || '', description: item.description || '', improvement_type: item.improvement_type || 'process', current_situation: item.current_situation || '', proposed_improvement: item.proposed_improvement || '', expected_benefits: item.expected_benefits || '', alignment_with_objectives: item.alignment_with_objectives || '', estimated_investment: item.estimated_investment ?? '', estimated_savings: item.estimated_savings ?? '', expected_roi: item.expected_roi ?? '', priority: item.priority || 'medium', proposed_date: item.proposed_date || '', status: item.status || 'proposed', completion_percentage: item.completion_percentage || 0 });
    setEditingId(item.id); setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.improvement.continualPage.deleteConfirm'));
    if (!confirmed) return;
    try {
      setError('');
      await deleteContinualImprovement(id);
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
        title={t('modules.improvement.continualPage.title')}
        subtitle={t('modules.improvement.continualPage.isoClause')}
        actionLabel={t('modules.improvement.continualPage.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <Modal
        title={editingId ? t('modules.improvement.continualPage.edit') : t('modules.improvement.continualPage.newDetailed')}
        isOpen={showForm}
        onClose={closeForm}
        maxWidth="max-w-6xl"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="form-label-muted">{t('modules.improvement.continualPage.fields.number')}<input type="text" required value={form.initiative_number} onChange={e => setForm({ ...form, initiative_number: e.target.value })} placeholder={t('modules.improvement.continualPage.placeholders.number')} className="field-control"  /></label>
              <label className="form-label-muted">{t('modules.improvement.continualPage.fields.title')}<input type="text" required value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} className="field-control"  /></label>
              <label className="form-label-muted">{t('modules.improvement.continualPage.fields.proposedDate')}<input type="date" required value={form.proposed_date} onChange={e => setForm({ ...form, proposed_date: e.target.value })} className="field-control"  /></label>
            </div>
            <label className="form-label-muted block">{t('modules.improvement.continualPage.fields.description')}<textarea required value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} className="field-control h-20"  /></label>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="form-label-muted">{t('modules.improvement.continualPage.fields.type')}
                <select value={form.improvement_type} onChange={e => setForm({ ...form, improvement_type: e.target.value })} className="field-control">
                  {Object.entries(improvementTypeLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <label className="form-label-muted">{t('modules.improvement.continualPage.fields.priority')}
                <select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })} className="field-control">
                  {Object.entries(priorityLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <label className="form-label-muted">{t('common.forms.status')}
                <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className="field-control">
                  {Object.entries(statusLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="form-label-muted">{t('modules.improvement.continualPage.fields.currentSituation')}<textarea required value={form.current_situation} onChange={e => setForm({ ...form, current_situation: e.target.value })} className="field-control h-20"  /></label>
              <label className="form-label-muted">{t('modules.improvement.continualPage.fields.proposedImprovement')}<textarea required value={form.proposed_improvement} onChange={e => setForm({ ...form, proposed_improvement: e.target.value })} className="field-control h-20"  /></label>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="form-label-muted">{t('modules.improvement.continualPage.fields.expectedBenefits')}<textarea required value={form.expected_benefits} onChange={e => setForm({ ...form, expected_benefits: e.target.value })} className="field-control h-16"  /></label>
              <label className="form-label-muted">{t('modules.improvement.continualPage.fields.alignmentWithObjectives')}<textarea value={form.alignment_with_objectives} onChange={e => setForm({ ...form, alignment_with_objectives: e.target.value })} className="field-control h-16"  /></label>
            </div>
            <div className="grid gap-4 sm:grid-cols-4">
              <label className="form-label-muted">{t('modules.improvement.continualPage.fields.estimatedInvestment')}<input type="number" step="0.01" value={form.estimated_investment} onChange={e => setForm({ ...form, estimated_investment: e.target.value })} className="field-control"  /></label>
              <label className="form-label-muted">{t('modules.improvement.continualPage.fields.estimatedSavings')}<input type="number" step="0.01" value={form.estimated_savings} onChange={e => setForm({ ...form, estimated_savings: e.target.value })} className="field-control"  /></label>
              <label className="form-label-muted">{t('modules.improvement.continualPage.fields.expectedRoi')}<input type="number" step="0.01" value={form.expected_roi} onChange={e => setForm({ ...form, expected_roi: e.target.value })} className="field-control"  /></label>
              <label className="form-label-muted">{t('modules.improvement.continualPage.fields.completionPercentage')}<input type="number" min="0" max="100" value={form.completion_percentage} onChange={e => setForm({ ...form, completion_percentage: e.target.value })} className="field-control"  /></label>
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
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.improvement.continualPage.table.code')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.name')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.improvement.continualPage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.improvement.continualPage.table.priority')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.improvement.continualPage.table.progress')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.improvement.continualPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.length === 0 ? (
              <CrudEmptyState colSpan={7} message={t('modules.improvement.continualPage.empty')} />
            ) : items.map(item => (
              <tr key={item.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 table-code">{item.initiative_number}</td>
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{item.title}</td>
                <td className="px-6 py-4 table-secondary-text">{improvementTypeLabels[item.improvement_type] || item.improvement_type}</td>
                <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${priorityColors[item.priority] || ''}`}>{priorityLabels[item.priority] || item.priority}</span></td>
                <td className="px-6 py-4"><div className="flex items-center gap-2"><div className="progress-track"><div className="progress-fill-success" style={{ width: `${item.completion_percentage || 0}%` }}></div></div><span className="table-tertiary-text">{item.completion_percentage || 0}%</span></div></td>
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

export default ImprovementContinualPage;