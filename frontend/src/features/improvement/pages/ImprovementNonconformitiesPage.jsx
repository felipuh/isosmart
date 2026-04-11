import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import { useLocation, useNavigate } from 'react-router-dom';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { showConfirm } from '../../../services/dialogs';
import { getNonconformities, createNonconformity, updateNonconformity, deleteNonconformity } from '../api/improvementApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const severityColors = { critical: 'badge-base badge-danger', major: 'badge-base badge-caution', minor: 'badge-base badge-warning' };
const statusColors = { open: 'badge-base badge-danger', analysis: 'badge-base badge-info', action_plan: 'badge-base badge-accent', implementing: 'badge-base badge-caution', verification: 'badge-base badge-cyan', closed: 'badge-base badge-success', rejected: 'badge-base badge-neutral' };

const initialForm = { nc_number: '', title: '', description: '', source: 'process_monitoring', detection_date: '', severity: 'minor', affected_process: '', iso_clause_reference: '', impact_description: '', immediate_action_taken: '', containment_measures: '', status: 'open', target_closure_date: '' };

const ImprovementNonconformitiesPage = () => {
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

  const sourceLabels = useMemo(() => ({
    internal_audit: t('modules.improvement.nonconformitiesPage.sources.internalAudit'),
    customer_complaint: t('modules.improvement.nonconformitiesPage.sources.customerComplaint'),
    process_monitoring: t('modules.improvement.nonconformitiesPage.sources.processMonitoring'),
    product_inspection: t('modules.improvement.nonconformitiesPage.sources.productInspection'),
    management_review: t('modules.improvement.nonconformitiesPage.sources.managementReview'),
    supplier_issue: t('modules.improvement.nonconformitiesPage.sources.supplierIssue'),
    other: t('modules.improvement.nonconformitiesPage.sources.other'),
  }), [t]);

  const severityLabels = useMemo(() => ({
    critical: t('modules.improvement.nonconformitiesPage.severities.critical'),
    major: t('modules.improvement.nonconformitiesPage.severities.major'),
    minor: t('modules.improvement.nonconformitiesPage.severities.minor'),
  }), [t]);

  const statusLabels = useMemo(() => ({
    open: t('modules.improvement.nonconformitiesPage.statuses.open'),
    analysis: t('modules.improvement.nonconformitiesPage.statuses.analysis'),
    action_plan: t('modules.improvement.nonconformitiesPage.statuses.actionPlan'),
    implementing: t('modules.improvement.nonconformitiesPage.statuses.implementing'),
    verification: t('modules.improvement.nonconformitiesPage.statuses.verification'),
    closed: t('modules.improvement.nonconformitiesPage.statuses.closed'),
    rejected: t('modules.improvement.nonconformitiesPage.statuses.rejected'),
  }), [t]);

  const loadData = useCallback(async () => {
    try { setLoading(true); setError(''); const data = await getNonconformities({ organization_id: orgId }); setItems(normalizeList(data)); }
    catch (error) { console.error('Error:', error); setError(t('common.messages.errorTryAgain')); }
    finally { setLoading(false); }
  }, [orgId, t]);

  useEffect(() => { if (orgId) loadData(); }, [orgId, loadData]);
  useEffect(() => { if (location.pathname.endsWith('/new')) { resetForm(); setShowForm(true); } }, [location.pathname]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError('');
      const payload = { ...form, organization_id: orgId, organization_name: orgName, detected_by: user?.id || null, responsible: user?.id || null };
      if (editingId) { await updateNonconformity(editingId, payload); } else { await createNonconformity(payload); }
      resetForm(); await loadData(); setShowForm(false);
      if (location.pathname.endsWith('/new')) navigate(location.pathname.replace(/\/new$/, ''), { replace: true });
    } catch (error) { console.error('Error:', error); setError(t('common.messages.errorTryAgain')); } finally { setSaving(false); }
  };

  const handleEdit = (item) => {
    setForm({ nc_number: item.nc_number || '', title: item.title || '', description: item.description || '', source: item.source || 'process_monitoring', detection_date: item.detection_date || '', severity: item.severity || 'minor', affected_process: item.affected_process || '', iso_clause_reference: item.iso_clause_reference || '', impact_description: item.impact_description || '', immediate_action_taken: item.immediate_action_taken || '', containment_measures: item.containment_measures || '', status: item.status || 'open', target_closure_date: item.target_closure_date || '' });
    setEditingId(item.id); setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.improvement.nonconformitiesPage.deleteConfirm'));
    if (!confirmed) return;
    try {
      setError('');
      await deleteNonconformity(id);
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
        title={t('modules.improvement.nonconformitiesPage.title')}
        subtitle={t('modules.improvement.nonconformitiesPage.isoClause')}
        actionLabel={t('modules.improvement.nonconformitiesPage.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <Modal
        title={editingId ? t('modules.improvement.nonconformitiesPage.edit') : t('modules.improvement.nonconformitiesPage.new')}
        isOpen={showForm}
        onClose={closeForm}
        maxWidth="max-w-6xl"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <label className="form-label-muted">{t('modules.improvement.nonconformitiesPage.fields.code')}
                <input type="text" required value={form.nc_number} onChange={e => setForm({ ...form, nc_number: e.target.value })} placeholder={t('modules.improvement.nonconformitiesPage.placeholders.code')} className="field-control" />
              </label>
              <label className="form-label-muted">{t('modules.improvement.nonconformitiesPage.fields.title')}
                <input type="text" required value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} className="field-control" />
              </label>
              <label className="form-label-muted">{t('modules.improvement.nonconformitiesPage.fields.detectionDate')}
                <input type="date" required value={form.detection_date} onChange={e => setForm({ ...form, detection_date: e.target.value })} className="field-control" />
              </label>
            </div>
            <label className="form-label-muted block">{t('modules.improvement.nonconformitiesPage.fields.description')}
              <textarea required value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} className="field-control h-20" />
            </label>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="form-label-muted">{t('modules.improvement.nonconformitiesPage.fields.source')}
                <select value={form.source} onChange={e => setForm({ ...form, source: e.target.value })} className="field-control">
                  {Object.entries(sourceLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <label className="form-label-muted">{t('modules.improvement.nonconformitiesPage.fields.severity')}
                <select value={form.severity} onChange={e => setForm({ ...form, severity: e.target.value })} className="field-control">
                  {Object.entries(severityLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <label className="form-label-muted">{t('common.forms.status')}
                <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className="field-control">
                  {Object.entries(statusLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="form-label-muted">{t('modules.improvement.nonconformitiesPage.fields.affectedProcess')}
                <input type="text" value={form.affected_process} onChange={e => setForm({ ...form, affected_process: e.target.value })} className="field-control" />
              </label>
              <label className="form-label-muted">{t('modules.improvement.nonconformitiesPage.fields.isoClauseReference')}
                <input type="text" value={form.iso_clause_reference} onChange={e => setForm({ ...form, iso_clause_reference: e.target.value })} placeholder={t('modules.improvement.nonconformitiesPage.placeholders.isoClauseReference')} className="field-control" />
              </label>
            </div>
            <label className="form-label-muted block">{t('modules.improvement.nonconformitiesPage.fields.impactDescription')}
              <textarea value={form.impact_description} onChange={e => setForm({ ...form, impact_description: e.target.value })} className="field-control h-16" />
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="form-label-muted">{t('modules.improvement.nonconformitiesPage.fields.immediateAction')}
                <textarea value={form.immediate_action_taken} onChange={e => setForm({ ...form, immediate_action_taken: e.target.value })} className="field-control h-16" />
              </label>
              <label className="form-label-muted">{t('modules.improvement.nonconformitiesPage.fields.containmentMeasures')}
                <textarea value={form.containment_measures} onChange={e => setForm({ ...form, containment_measures: e.target.value })} className="field-control h-16" />
              </label>
            </div>
            <label className="form-label-muted">{t('modules.improvement.nonconformitiesPage.fields.targetClosureDate')}
              <input type="date" value={form.target_closure_date} onChange={e => setForm({ ...form, target_closure_date: e.target.value })} className="field-control max-w-xs" />
            </label>
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
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.improvement.nonconformitiesPage.table.code')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.name')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.improvement.nonconformitiesPage.table.source')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.improvement.nonconformitiesPage.table.severity')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.improvement.nonconformitiesPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.length === 0 ? (
              <CrudEmptyState colSpan={6} message={t('modules.improvement.nonconformitiesPage.empty')} />
            ) : items.map(item => (
              <tr key={item.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 table-code">{item.nc_number}</td>
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{item.title}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{sourceLabels[item.source] || item.source}</td>
                <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${severityColors[item.severity] || ''}`}>{severityLabels[item.severity] || item.severity}</span></td>
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

export default ImprovementNonconformitiesPage;