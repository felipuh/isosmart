import React, { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import {
  approveObjective,
  createObjective,
  deleteObjective,
  forecastObjective,
  generateSmartObjectiveWithAI,
  getObjectiveVersionHistory,
  getObjectives,
  getUsers,
  updateObjective,
  validateSmartObjective,
} from '../api/planningApi';
import { showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const initialForm = (ownerId) => ({
  code: '',
  title: '',
  description: '',
  alignment: 'policy',
  metric: '',
  baseline: '',
  target: '',
  current_value: '',
  unit: '',
  owner: ownerId || '',
  start_date: '',
  target_date: '',
  status: 'draft',
  progress_percentage: 0,
  is_specific: false,
  is_measurable: false,
  is_achievable: false,
  is_relevant: false,
  is_time_bound: false,
  required_resources: '',
  budget: '',
});

const QualityObjectivesPage = () => {
  const { t } = useI18n();
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [users, setUsers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [versions, setVersions] = useState([]);
  const [forecast, setForecast] = useState(null);
  const [smartCheck, setSmartCheck] = useState(null);
  const [aiDraft, setAiDraft] = useState(null);
  const [form, setForm] = useState(initialForm(user?.id));
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const [aiLoading, setAiLoading] = useState(false);

  const resetForm = useCallback(() => {
    setForm(initialForm(user?.id));
    setEditingId(null);
    setSmartCheck(null);
    setAiDraft(null);
  }, [user?.id]);

  const loadData = useCallback(async () => {
    if (!orgId) return;
    try {
      setLoading(true);
      const [objectivesData, usersData] = await Promise.all([
        getObjectives({ organization_id: orgId }),
        getUsers({ organization_id: orgId }),
      ]);
      setItems(normalizeList(objectivesData));
      setUsers(normalizeList(usersData));
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
      resetForm();
      setShowForm(true);
    }
  }, [location.pathname, resetForm]);

  const handleSelect = async (item) => {
    setSelected(item);
    try {
      const [forecastData, versionData] = await Promise.all([
        forecastObjective(item.id, orgId),
        getObjectiveVersionHistory(item.id, orgId),
      ]);
      setForecast(forecastData?.forecast || null);
      setVersions(normalizeList(versionData));
    } catch {
      setForecast(null);
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
        baseline: form.baseline === '' ? null : Number(form.baseline),
        target: form.target === '' ? null : Number(form.target),
        current_value: form.current_value === '' ? null : Number(form.current_value),
        budget: form.budget === '' ? null : Number(form.budget),
        owner: form.owner || null,
        ai_recommendations: aiDraft?.draft || {},
      };
      if (editingId) {
        await updateObjective(editingId, payload);
      } else {
        await createObjective(payload);
      }
      setShowForm(false);
      resetForm();
      await loadData();
      if (location.pathname.endsWith('/new')) {
        navigate(location.pathname.replace(/\/new$/, ''), { replace: true });
      }
    } catch {
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setEditingId(item.id);
    setForm({
      code: item.code,
      title: item.title,
      description: item.description || '',
      alignment: item.alignment,
      metric: item.metric,
      baseline: item.baseline ?? '',
      target: item.target ?? '',
      current_value: item.current_value ?? '',
      unit: item.unit || '',
      owner: item.owner || '',
      start_date: item.start_date,
      target_date: item.target_date,
      status: item.status,
      progress_percentage: item.progress_percentage || 0,
      is_specific: item.is_specific,
      is_measurable: item.is_measurable,
      is_achievable: item.is_achievable,
      is_relevant: item.is_relevant,
      is_time_bound: item.is_time_bound,
      required_resources: item.required_resources || '',
      budget: item.budget ?? '',
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!await showConfirm(t('modules.planning.qualityObjectivesPage.deleteConfirm'))) return;
    try {
      await deleteObjective(id);
      if (selected?.id === id) setSelected(null);
      await loadData();
    } catch {
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const handleValidateSmart = async () => {
    try {
      const result = await validateSmartObjective(form);
      setSmartCheck(result);
      setForm((prev) => ({
        ...prev,
        is_specific: result?.checks?.specific || false,
        is_measurable: result?.checks?.measurable || false,
        is_achievable: result?.checks?.achievable || false,
        is_relevant: result?.checks?.relevant || false,
        is_time_bound: result?.checks?.time_bound || false,
      }));
    } catch {
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const handleGenerateDraft = async () => {
    try {
      setAiLoading(true);
      const result = await generateSmartObjectiveWithAI(orgId, {
        title: form.title,
        strategy: form.description,
        indicator: form.metric,
        baseline: form.baseline || 0,
        target: form.target || 0,
        deadline: form.target_date,
        resources: form.required_resources,
      });
      setAiDraft(result);
      const draft = result?.draft || {};
      setForm((prev) => ({
        ...prev,
        title: draft.objective || prev.title,
        metric: draft.indicator || prev.metric,
        baseline: draft.baseline ?? prev.baseline,
        target: draft.target ?? prev.target,
        target_date: draft.deadline || prev.target_date,
        required_resources: draft.resources || prev.required_resources,
        is_specific: !!draft.specific,
        is_measurable: !!draft.measurable,
        is_achievable: !!draft.achievable,
        is_relevant: !!draft.relevant,
        is_time_bound: !!draft.time_bound,
      }));
    } catch {
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setAiLoading(false);
    }
  };

  const handleApprove = async (item) => {
    try {
      await approveObjective(item.id);
      await loadData();
      handleSelect({ ...item, approval_date: new Date().toISOString() });
    } catch {
      setError(t('common.messages.errorTryAgain'));
    }
  };

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="space-y-6">
      <CrudPageHeader title={t('modules.planning.qualityObjectivesPage.title')} actionLabel={t('modules.planning.qualityObjectivesPage.new')} onAction={() => { resetForm(); setShowForm(true); }} />
      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-100 dark:bg-slate-800/60">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.qualityObjectivesPage.table.code')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.qualityObjectivesPage.table.title')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.qualityObjectivesPage.table.smart')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.qualityObjectivesPage.table.progress')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.qualityObjectivesPage.table.actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60 cursor-pointer" onClick={() => handleSelect(item)}>
                    <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.code}</td>
                    <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{item.title}</td>
                    <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.status_display}</td>
                    <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.is_smart ? '✓' : '−'}</td>
                    <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.progress_percentage}%</td>
                    <td className="px-6 py-4 text-sm space-x-2">
                      <button onClick={(e) => { e.stopPropagation(); handleEdit(item); }} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                      <button onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {items.length === 0 && <CrudEmptyState message={t('modules.planning.qualityObjectivesPage.empty')} />}
          </div>
        </div>

        <div className="space-y-6">
          <div className="card p-4">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">{t('modules.planning.qualityObjectivesPage.detailTitle')}</h3>
            {selected ? (
              <div className="space-y-3 text-sm">
                <div>
                  <p className="font-semibold text-slate-900 dark:text-white">{selected.title}</p>
                  <p className="text-slate-500 dark:text-slate-400">{selected.metric} · {selected.owner_name || t('modules.planning.qualityObjectivesPage.noOwner')}</p>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-3 overflow-hidden">
                  <div className={`h-3 ${selected.progress_percentage < 50 ? 'bg-amber-500' : 'bg-green-500'}`} style={{ width: `${selected.progress_percentage}%` }}></div>
                </div>
                {forecast && (
                  <div className="rounded-lg bg-slate-100 dark:bg-slate-800 p-3 text-xs">
                    <p className="font-semibold text-slate-700 dark:text-slate-300">{t('modules.planning.qualityObjectivesPage.forecastTitle')}</p>
                    <p className="text-slate-500 dark:text-slate-400">{t('modules.planning.qualityObjectivesPage.projectedStatus')}: {forecast.projected_status}</p>
                    <p className="text-slate-500 dark:text-slate-400">{t('modules.planning.qualityObjectivesPage.recommendedAction')}: {forecast.recommended_action}</p>
                  </div>
                )}
                {!selected.approval_date && selected.status !== 'approved' && (
                  <button onClick={() => handleApprove(selected)} className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm">{t('modules.planning.qualityObjectivesPage.approveObjective')}</button>
                )}
              </div>
            ) : <p className="text-sm text-slate-500 dark:text-slate-400">{t('modules.planning.qualityObjectivesPage.selectPrompt')}</p>}
          </div>

          <div className="card p-4">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">{t('modules.planning.qualityObjectivesPage.historyTitle')}</h3>
            <div className="space-y-2 text-xs">
              {versions.length > 0 ? versions.map((version) => (
                <div key={version.id} className="rounded-lg bg-slate-100 dark:bg-slate-800 p-3">
                  <p className="font-semibold text-slate-700 dark:text-slate-300">v{version.version_number}</p>
                  <p className="text-slate-500 dark:text-slate-400">{version.change_reason || t('modules.planning.qualityObjectivesPage.noReason')} · {version.created_at}</p>
                </div>
              )) : <p className="text-slate-500 dark:text-slate-400">{t('modules.planning.qualityObjectivesPage.noVersions')}</p>}
            </div>
          </div>
        </div>
      </div>

      <Modal title={editingId ? t('modules.planning.qualityObjectivesPage.edit') : t('modules.planning.qualityObjectivesPage.new')} isOpen={showForm} onClose={() => setShowForm(false)}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={handleValidateSmart} className="px-3 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-sm">{t('modules.planning.qualityObjectivesPage.validateSmart')}</button>
            <button type="button" onClick={handleGenerateDraft} disabled={aiLoading} className="px-3 py-2 bg-purple-600 text-white rounded-lg text-sm disabled:opacity-50">{aiLoading ? t('modules.planning.qualityObjectivesPage.generating') : t('modules.planning.qualityObjectivesPage.generateAiDraft')}</button>
          </div>

          {smartCheck && (
            <div className={`rounded-lg p-3 text-xs ${smartCheck.passed ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300' : 'bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300'}`}>
              {smartCheck.passed ? t('modules.planning.qualityObjectivesPage.smartValid') : smartCheck.issues.join(' ')}
            </div>
          )}

          {aiDraft?.draft && (
            <div className="rounded-lg p-3 text-xs bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300">
              {t('modules.planning.qualityObjectivesPage.aiRationale')}: {aiDraft.draft.rationale}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.qualityObjectivesPage.fields.code')}</label>
              <input type="text" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.qualityObjectivesPage.fields.title')}</label>
              <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('common.forms.description')}</label>
              <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.qualityObjectivesPage.fields.alignment')}</label>
              <select value={form.alignment} onChange={(e) => setForm({ ...form, alignment: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                {['policy', 'strategic', 'customer', 'compliance', 'improvement'].map((alignment) => <option key={alignment} value={alignment}>{t(`modules.planning.qualityObjectivesPage.alignment.${alignment}`)}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.qualityObjectivesPage.fields.metric')}</label>
              <input type="text" value={form.metric} onChange={(e) => setForm({ ...form, metric: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.qualityObjectivesPage.fields.unit')}</label>
              <input type="text" value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.qualityObjectivesPage.fields.baseline')}</label>
              <input type="number" value={form.baseline} onChange={(e) => setForm({ ...form, baseline: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.qualityObjectivesPage.fields.target')}</label>
              <input type="number" value={form.target} onChange={(e) => setForm({ ...form, target: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.qualityObjectivesPage.fields.currentValue')}</label>
              <input type="number" value={form.current_value} onChange={(e) => setForm({ ...form, current_value: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.qualityObjectivesPage.fields.owner')}</label>
              <select value={form.owner} onChange={(e) => setForm({ ...form, owner: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="">{t('modules.planning.qualityObjectivesPage.fields.unassigned')}</option>
                {users.map((entry) => <option key={entry.id} value={entry.id}>{entry.full_name || entry.username || entry.email}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.qualityObjectivesPage.fields.startDate')}</label>
              <input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.qualityObjectivesPage.fields.targetDate')}</label>
              <input type="date" value={form.target_date} onChange={(e) => setForm({ ...form, target_date: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.qualityObjectivesPage.fields.progress')}</label>
              <input type="number" min="0" max="100" value={form.progress_percentage} onChange={(e) => setForm({ ...form, progress_percentage: Number(e.target.value || 0) })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.qualityObjectivesPage.fields.requiredResources')}</label>
              <textarea value={form.required_resources} onChange={(e) => setForm({ ...form, required_resources: e.target.value })} rows={2} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
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

export default QualityObjectivesPage;