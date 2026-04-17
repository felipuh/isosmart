import React, { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import {
  approveChange,
  createChange,
  deleteChange,
  generateChangePlan,
  getChangeTimeline,
  getChangeVersionHistory,
  getChanges,
  rejectChange,
  simulateChangeImpact,
  updateChange,
} from '../api/planningApi';
import { showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const initialForm = {
  change_number: '',
  title: '',
  description: '',
  change_type: 'process',
  reason: 'improvement',
  justification: '',
  urgency: 'medium',
  planned_date: '',
  affected_areas: '',
  impact_assessment: '',
  potential_risks: '',
  mitigation_plan: '',
  status: 'draft',
};

const ChangeControlPage = () => {
  const { t } = useI18n();
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [versions, setVersions] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const [rejectNotes, setRejectNotes] = useState('');

  const loadData = useCallback(async () => {
    if (!orgId) return;
    try {
      setLoading(true);
      const data = await getChanges({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch {
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  useEffect(() => {
    if (orgId) loadData();
  }, [orgId, loadData]);

  useEffect(() => {
    if (location.pathname.endsWith('/new')) {
      setEditingId(null);
      setForm(initialForm);
      setShowForm(true);
    }
  }, [location.pathname]);

  const loadSelectedArtifacts = async (item) => {
    setSelected(item);
    try {
      const [timelineData, versionData] = await Promise.all([
        getChangeTimeline(item.id, orgId),
        getChangeVersionHistory(item.id, orgId),
      ]);
      setTimeline(timelineData?.events || []);
      setVersions(normalizeList(versionData));
    } catch {
      setTimeline([]);
      setVersions([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = {
        ...form,
        organization_id: orgId,
        organization_name: orgName,
        requested_by: user?.id || null,
      };
      if (editingId) {
        await updateChange(editingId, payload);
      } else {
        await createChange(payload);
      }
      setShowForm(false);
      setForm(initialForm);
      await loadData();
      if (location.pathname.endsWith('/new')) {
        navigate(location.pathname.replace(/\/new$/, ''), { replace: true });
      }
    } catch (err) {
      setError(err?.response?.data?.impact_assessment || t('common.messages.errorTryAgain'));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setEditingId(item.id);
    setForm({
      change_number: item.change_number,
      title: item.title,
      description: item.description || '',
      change_type: item.change_type,
      reason: item.reason,
      justification: item.justification || '',
      urgency: item.urgency,
      planned_date: item.planned_date,
      affected_areas: item.affected_areas || '',
      impact_assessment: item.impact_assessment || '',
      potential_risks: item.potential_risks || '',
      mitigation_plan: item.mitigation_plan || '',
      status: item.status,
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!await showConfirm(t('modules.planning.changeControlPage.deleteConfirm'))) return;
    try {
      await deleteChange(id);
      if (selected?.id === id) setSelected(null);
      await loadData();
    } catch {
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const handleApprove = async (item) => {
    try {
      await approveChange(item.id);
      await loadData();
      loadSelectedArtifacts({ ...item, status: 'approved' });
    } catch (err) {
      setError(err?.response?.data?.impact_assessment || t('common.messages.errorTryAgain'));
    }
  };

  const handleReject = async (item) => {
    try {
      await rejectChange(item.id, rejectNotes);
      setRejectNotes('');
      await loadData();
      loadSelectedArtifacts({ ...item, status: 'rejected', approval_comments: rejectNotes });
    } catch {
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const handleSimulate = async (item) => {
    try {
      await simulateChangeImpact(item.id, orgId);
      await loadData();
      loadSelectedArtifacts({ ...item, status: item.status });
    } catch {
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const handleGeneratePlan = async (item) => {
    try {
      await generateChangePlan(item.id, orgId);
      await loadData();
      loadSelectedArtifacts({ ...item, status: item.status });
    } catch {
      setError(t('common.messages.errorTryAgain'));
    }
  };

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="space-y-6">
      <CrudPageHeader title={t('modules.planning.changeControlPage.title')} actionLabel={t('modules.planning.changeControlPage.new')} onAction={() => { setEditingId(null); setForm(initialForm); setShowForm(true); }} />
      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-100 dark:bg-slate-800/60">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.changeControlPage.table.number')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.changeControlPage.table.title')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.changeControlPage.table.type')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.changeControlPage.table.urgency')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.changeControlPage.table.actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60 cursor-pointer" onClick={() => loadSelectedArtifacts(item)}>
                    <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.change_number}</td>
                    <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{item.title}</td>
                    <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.change_type_display}</td>
                    <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.urgency_display}</td>
                    <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.status_display}</td>
                    <td className="px-6 py-4 text-sm space-x-2">
                      <button onClick={(e) => { e.stopPropagation(); handleEdit(item); }} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                      <button onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {items.length === 0 && <CrudEmptyState message={t('modules.planning.changeControlPage.empty')} />}
          </div>
        </div>

        <div className="space-y-6">
          <div className="card p-4">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">{t('modules.planning.changeControlPage.reviewTitle')}</h3>
            {selected ? (
              <div className="space-y-3 text-sm">
                <div>
                  <p className="font-semibold text-slate-900 dark:text-white">{selected.title}</p>
                  <p className="text-slate-500 dark:text-slate-400">{selected.change_number} · {selected.status_display}</p>
                </div>
                <p className="text-slate-700 dark:text-slate-300">{selected.impact_assessment || t('modules.planning.changeControlPage.noImpactNarrative')}</p>
                {selected.impact_estimated && Object.keys(selected.impact_estimated).length > 0 && (
                  <div className="rounded-lg bg-slate-100 dark:bg-slate-800 p-3 text-xs space-y-1">
                    <p>{t('modules.planning.changeControlPage.operationalImpact')}: {selected.impact_estimated.operational}</p>
                    <p>{t('modules.planning.changeControlPage.complianceImpact')}: {selected.impact_estimated.compliance}</p>
                    <p>{t('modules.planning.changeControlPage.resourceImpact')}: {selected.impact_estimated.resources}</p>
                  </div>
                )}
                <div className="flex flex-wrap gap-2">
                  <button onClick={() => handleSimulate(selected)} className="px-3 py-2 bg-purple-600 text-white rounded-lg text-xs">{t('modules.planning.changeControlPage.simulateImpact')}</button>
                  <button onClick={() => handleGeneratePlan(selected)} className="px-3 py-2 bg-blue-600 text-white rounded-lg text-xs">{t('modules.planning.changeControlPage.generatePlan')}</button>
                  {['submitted', 'under_review'].includes(selected.status) && <button onClick={() => handleApprove(selected)} className="px-3 py-2 bg-green-600 text-white rounded-lg text-xs">{t('modules.planning.changeControlPage.approve')}</button>}
                </div>
                {['submitted', 'under_review'].includes(selected.status) && (
                  <div className="space-y-2">
                    <textarea value={rejectNotes} onChange={(e) => setRejectNotes(e.target.value)} rows={2} className="w-full px-3 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white text-xs" placeholder={t('modules.planning.changeControlPage.rejectReason')} />
                    <button onClick={() => handleReject(selected)} className="w-full px-3 py-2 bg-red-600 text-white rounded-lg text-xs">{t('modules.planning.changeControlPage.reject')}</button>
                  </div>
                )}
                {(selected.implementation_plan || []).length > 0 && (
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400 mb-1">{t('modules.planning.changeControlPage.implementationPlan')}</p>
                    <ul className="space-y-1 text-xs text-slate-700 dark:text-slate-300">
                      {selected.implementation_plan.map((step, index) => <li key={index}>• {step.title || step.step}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            ) : <p className="text-sm text-slate-500 dark:text-slate-400">{t('modules.planning.changeControlPage.selectPrompt')}</p>}
          </div>

          <div className="card p-4">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">{t('modules.planning.changeControlPage.timelineTitle')}</h3>
            <div className="space-y-2 text-xs">
              {timeline.map((event, index) => (
                <div key={`${event.event}-${index}`} className="rounded-lg bg-slate-100 dark:bg-slate-800 p-3">
                  <p className="font-semibold text-slate-700 dark:text-slate-300">{event.label}</p>
                  <p className="text-slate-500 dark:text-slate-400">{event.date}</p>
                </div>
              ))}
              {versions.map((version) => (
                <div key={`version-${version.id}`} className="rounded-lg border border-slate-200 dark:border-slate-700 p-3">
                  <p className="font-semibold text-slate-700 dark:text-slate-300">v{version.version_number}</p>
                  <p className="text-slate-500 dark:text-slate-400">{version.change_reason || t('modules.planning.changeControlPage.noReason')} · {version.created_at}</p>
                </div>
              ))}
              {timeline.length === 0 && versions.length === 0 && <p className="text-slate-500 dark:text-slate-400">{t('modules.planning.changeControlPage.noTraceability')}</p>}
            </div>
          </div>
        </div>
      </div>

      <Modal title={editingId ? t('modules.planning.changeControlPage.edit') : t('modules.planning.changeControlPage.new')} isOpen={showForm} onClose={() => setShowForm(false)}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.number')}</label>
              <input type="text" value={form.change_number} onChange={(e) => setForm({ ...form, change_number: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.title')}</label>
              <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('common.forms.description')}</label>
              <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.type')}</label>
              <select value={form.change_type} onChange={(e) => setForm({ ...form, change_type: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                {['process', 'procedure', 'resource', 'technology', 'structure', 'scope', 'policy', 'other'].map((entry) => <option key={entry} value={entry}>{t(`modules.planning.changeControlPage.types.${entry}`)}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.reason')}</label>
              <select value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                {[
                  ['improvement', 'improvement'],
                  ['correction', 'correction'],
                  ['compliance', 'compliance'],
                  ['risk_mitigation', 'riskMitigation'],
                  ['opportunity', 'opportunity'],
                  ['external_requirement', 'externalRequirement'],
                ].map(([value, labelKey]) => <option key={value} value={value}>{t(`modules.planning.changeControlPage.reasons.${labelKey}`)}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.urgency')}</label>
              <select value={form.urgency} onChange={(e) => setForm({ ...form, urgency: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                {['low', 'medium', 'high', 'critical'].map((entry) => <option key={entry} value={entry}>{t(`modules.planning.changeControlPage.urgency.${entry}`)}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.plannedDate')}</label>
              <input type="date" value={form.planned_date} onChange={(e) => setForm({ ...form, planned_date: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.justification')}</label>
              <textarea value={form.justification} onChange={(e) => setForm({ ...form, justification: e.target.value })} rows={2} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.affectedAreas')}</label>
              <textarea value={form.affected_areas} onChange={(e) => setForm({ ...form, affected_areas: e.target.value })} rows={2} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.impactAssessment')}</label>
              <textarea value={form.impact_assessment} onChange={(e) => setForm({ ...form, impact_assessment: e.target.value })} rows={2} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.potentialRisks')}</label>
              <textarea value={form.potential_risks} onChange={(e) => setForm({ ...form, potential_risks: e.target.value })} rows={2} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
          </div>
          <div className="flex space-x-3">
            <button type="submit" disabled={saving} className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">{saving ? t('common.messages.saving') : editingId ? t('common.buttons.update') : t('common.buttons.create')}</button>
            <button type="button" onClick={() => setShowForm(false)} className="px-6 py-2 bg-slate-500 hover:bg-slate-600 text-white rounded-lg">{t('common.buttons.cancel')}</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ChangeControlPage;