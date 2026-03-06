import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import { useLocation, useNavigate } from 'react-router-dom';
import Modal from '../../../components/Common/Modal';
import { getNonconformities, createNonconformity, updateNonconformity, deleteNonconformity } from '../api/improvementApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const severityColors = { critical: 'bg-red-500/20 text-red-400', major: 'bg-orange-500/20 text-orange-400', minor: 'bg-yellow-500/20 text-yellow-400' };
const statusColors = { open: 'bg-red-500/20 text-red-400', analysis: 'bg-blue-500/20 text-blue-400', action_plan: 'bg-purple-500/20 text-purple-400', implementing: 'bg-orange-500/20 text-orange-400', verification: 'bg-cyan-500/20 text-cyan-400', closed: 'bg-green-500/20 text-green-400', rejected: 'bg-gray-500/20 text-gray-400' };

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
    try { setLoading(true); const data = await getNonconformities({ organization_id: orgId }); setItems(normalizeList(data)); }
    catch (error) { console.error('Error:', error); }
    finally { setLoading(false); }
  }, [orgId]);

  useEffect(() => { if (orgId) loadData(); }, [orgId, loadData]);
  useEffect(() => { if (location.pathname.endsWith('/new')) { resetForm(); setShowForm(true); } }, [location.pathname]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = { ...form, organization_id: orgId, organization_name: orgName, detected_by: user?.id || null, responsible: user?.id || null };
      if (editingId) { await updateNonconformity(editingId, payload); } else { await createNonconformity(payload); }
      resetForm(); await loadData(); setShowForm(false);
      if (location.pathname.endsWith('/new')) navigate(location.pathname.replace(/\/new$/, ''), { replace: true });
    } catch (error) { console.error('Error:', error); } finally { setSaving(false); }
  };

  const handleEdit = (item) => {
    setForm({ nc_number: item.nc_number || '', title: item.title || '', description: item.description || '', source: item.source || 'process_monitoring', detection_date: item.detection_date || '', severity: item.severity || 'minor', affected_process: item.affected_process || '', iso_clause_reference: item.iso_clause_reference || '', impact_description: item.impact_description || '', immediate_action_taken: item.immediate_action_taken || '', containment_measures: item.containment_measures || '', status: item.status || 'open', target_closure_date: item.target_closure_date || '' });
    setEditingId(item.id); setShowForm(true);
  };

  const handleDelete = async (id) => { if (!confirm(t('modules.improvement.nonconformitiesPage.deleteConfirm'))) return; try { await deleteNonconformity(id); await loadData(); } catch (error) { console.error('Error:', error); } };
  const resetForm = () => { setForm(initialForm); setEditingId(null); };
  const openForm = () => { resetForm(); setShowForm(true); };
  const closeForm = () => { resetForm(); setShowForm(false); if (location.pathname.endsWith('/new')) navigate(location.pathname.replace(/\/new$/, ''), { replace: true }); };

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">{t('modules.improvement.nonconformitiesPage.title')}</h1>
          <p className="text-gray-400 mt-1">{t('modules.improvement.nonconformitiesPage.isoClause')}</p>
        </div>
        <button type="button" onClick={openForm} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">{t('modules.improvement.nonconformitiesPage.new')}</button>
      </div>

      <Modal
        title={editingId ? t('modules.improvement.nonconformitiesPage.edit') : t('modules.improvement.nonconformitiesPage.new')}
        isOpen={showForm}
        onClose={closeForm}
        maxWidth="max-w-6xl"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <label className="text-xs text-slate-400">{t('modules.improvement.nonconformitiesPage.fields.code')}
                <input type="text" required value={form.nc_number} onChange={e => setForm({ ...form, nc_number: e.target.value })} placeholder="NC-2026-001" className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" />
              </label>
              <label className="text-xs text-slate-400">{t('modules.improvement.nonconformitiesPage.fields.title')}
                <input type="text" required value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" />
              </label>
              <label className="text-xs text-slate-400">{t('modules.improvement.nonconformitiesPage.fields.detectionDate')}
                <input type="date" required value={form.detection_date} onChange={e => setForm({ ...form, detection_date: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" />
              </label>
            </div>
            <label className="text-xs text-slate-400 block">{t('modules.improvement.nonconformitiesPage.fields.description')}
              <textarea required value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" />
            </label>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="text-xs text-slate-400">{t('modules.improvement.nonconformitiesPage.fields.source')}
                <select value={form.source} onChange={e => setForm({ ...form, source: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                  {Object.entries(sourceLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <label className="text-xs text-slate-400">{t('modules.improvement.nonconformitiesPage.fields.severity')}
                <select value={form.severity} onChange={e => setForm({ ...form, severity: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                  {Object.entries(severityLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <label className="text-xs text-slate-400">{t('common.forms.status')}
                <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                  {Object.entries(statusLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="text-xs text-slate-400">{t('modules.improvement.nonconformitiesPage.fields.affectedProcess')}
                <input type="text" value={form.affected_process} onChange={e => setForm({ ...form, affected_process: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" />
              </label>
              <label className="text-xs text-slate-400">{t('modules.improvement.nonconformitiesPage.fields.isoClauseReference')}
                <input type="text" value={form.iso_clause_reference} onChange={e => setForm({ ...form, iso_clause_reference: e.target.value })} placeholder="8.5, 9.1, etc." className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" />
              </label>
            </div>
            <label className="text-xs text-slate-400 block">{t('modules.improvement.nonconformitiesPage.fields.impactDescription')}
              <textarea value={form.impact_description} onChange={e => setForm({ ...form, impact_description: e.target.value })} className="mt-1 h-16 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" />
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="text-xs text-slate-400">{t('modules.improvement.nonconformitiesPage.fields.immediateAction')}
                <textarea value={form.immediate_action_taken} onChange={e => setForm({ ...form, immediate_action_taken: e.target.value })} className="mt-1 h-16 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" />
              </label>
              <label className="text-xs text-slate-400">{t('modules.improvement.nonconformitiesPage.fields.containmentMeasures')}
                <textarea value={form.containment_measures} onChange={e => setForm({ ...form, containment_measures: e.target.value })} className="mt-1 h-16 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" />
              </label>
            </div>
            <label className="text-xs text-slate-400">{t('modules.improvement.nonconformitiesPage.fields.targetClosureDate')}
              <input type="date" value={form.target_closure_date} onChange={e => setForm({ ...form, target_closure_date: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 max-w-xs" />
            </label>
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
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.improvement.nonconformitiesPage.table.code')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('common.forms.name')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.improvement.nonconformitiesPage.table.source')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.improvement.nonconformitiesPage.table.severity')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.improvement.nonconformitiesPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700/30">
            {items.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-8 text-center text-gray-400">{t('modules.improvement.nonconformitiesPage.empty')}</td></tr>
            ) : items.map(item => (
              <tr key={item.id} className="hover:bg-gray-800/30">
                <td className="px-6 py-4 text-sm font-mono text-blue-400">{item.nc_number}</td>
                <td className="px-6 py-4 text-sm text-gray-200">{item.title}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{sourceLabels[item.source] || item.source}</td>
                <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${severityColors[item.severity] || ''}`}>{severityLabels[item.severity] || item.severity}</span></td>
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

export default ImprovementNonconformitiesPage;