import React, { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import {
  approveRiskOpportunity,
  createRiskOpportunity,
  deleteRiskOpportunity,
  detectRiskWithAI,
  getRiskHeatmap,
  getRiskVersionHistory,
  getRisksOpportunities,
  updateRiskOpportunity,
} from '../api/planningApi';
import { showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const initialForm = {
  item_type: 'risk',
  code: '',
  title: '',
  description: '',
  category: 'operational',
  context: 'internal',
  probability: 3,
  impact: 3,
  feasibility: 3,
  benefit: 3,
  treatment: 'mitigate',
  treatment_description: '',
};

const RisksOpportunitiesPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [heatmap, setHeatmap] = useState([]);
  const [selected, setSelected] = useState(null);
  const [versions, setVersions] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [filterType, setFilterType] = useState('all');
  const [error, setError] = useState('');
  const [aiText, setAiText] = useState('');
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  const loadData = useCallback(async () => {
    if (!orgId) return;
    try {
      setLoading(true);
      setError('');
      const [itemsData, heatmapData] = await Promise.all([
        getRisksOpportunities({ organization_id: orgId }),
        getRiskHeatmap(orgId),
      ]);
      setItems(normalizeList(itemsData));
      setHeatmap(heatmapData?.matrix || []);
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

  const loadVersions = async (itemId) => {
    try {
      const data = await getRiskVersionHistory(itemId, orgId);
      setVersions(normalizeList(data));
    } catch {
      setVersions([]);
    }
  };

  const handleSelect = (item) => {
    setSelected(item);
    loadVersions(item.id);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = {
        ...form,
        organization_id: orgId,
        organization_name: orgName,
        probability: form.item_type === 'risk' ? Number(form.probability) : null,
        impact: form.item_type === 'risk' ? Number(form.impact) : null,
        feasibility: form.item_type === 'opportunity' ? Number(form.feasibility) : null,
        benefit: form.item_type === 'opportunity' ? Number(form.benefit) : null,
        ai_sources: aiSuggestion?.risk?.sources || [],
        proposed_actions: aiSuggestion?.risk?.actions || [],
      };
      if (editingId) {
        await updateRiskOpportunity(editingId, payload);
      } else {
        await createRiskOpportunity(payload);
      }
      setShowForm(false);
      setForm(initialForm);
      setAiSuggestion(null);
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
      item_type: item.item_type,
      code: item.code,
      title: item.title,
      description: item.description || '',
      category: item.category,
      context: item.context,
      probability: item.probability || 3,
      impact: item.impact || 3,
      feasibility: item.feasibility || 3,
      benefit: item.benefit || 3,
      treatment: item.treatment || 'mitigate',
      treatment_description: item.treatment_description || '',
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!await showConfirm(t('modules.planning.risksOpportunitiesPage.deleteConfirm'))) return;
    try {
      await deleteRiskOpportunity(id);
      if (selected?.id === id) setSelected(null);
      await loadData();
    } catch {
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const handleApprove = async (item) => {
    try {
      await approveRiskOpportunity(item.id);
      await loadData();
      handleSelect({ ...item, approved_at: new Date().toISOString() });
    } catch {
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const handleDetectRisk = async () => {
    if (!aiText.trim()) return;
    try {
      setAiLoading(true);
      const result = await detectRiskWithAI(orgId, { text: aiText, sources: ['manual_input'] });
      setAiSuggestion(result);
      if (result?.risk) {
        setForm((prev) => ({
          ...prev,
          item_type: 'risk',
          title: result.risk.description.slice(0, 120),
          description: result.risk.description,
          category: result.risk.category,
          probability: Math.max(1, Math.round((result.risk.probability || 0.2) * 5)),
          impact: Math.max(1, Math.round((result.risk.impact || 0.2) * 5)),
          treatment_description: (result.risk.actions || []).join('\n'),
        }));
      }
    } catch {
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setAiLoading(false);
    }
  };

  const filteredItems = filterType === 'all' ? items : items.filter((item) => item.item_type === filterType);

  if (loading) {
    return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>;
  }

  return (
    <div className="space-y-6">
      <CrudPageHeader
        title={t('modules.planning.risksOpportunitiesPage.title')}
        actionLabel={t('modules.planning.risksOpportunitiesPage.new')}
        onAction={() => { setEditingId(null); setForm(initialForm); setShowForm(true); }}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">
          <div className="card p-4 space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{t('modules.planning.risksOpportunitiesPage.heatmapTitle')}</h3>
              <div className="flex space-x-2">
                {['all', 'risk', 'opportunity'].map((type) => (
                  <button
                    key={type}
                    onClick={() => setFilterType(type)}
                    className={`px-4 py-2 rounded-lg text-sm ${filterType === type ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300'}`}
                  >
                    {type === 'all'
                      ? t('modules.planning.risksOpportunitiesPage.filters.all')
                      : type === 'risk'
                        ? t('modules.planning.risksOpportunitiesPage.filters.risks')
                        : t('modules.planning.risksOpportunitiesPage.filters.opportunities')}
                  </button>
                ))}
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-center">
                <thead>
                  <tr>
                    <th className="p-2 text-slate-500 dark:text-slate-400">{t('modules.planning.risksOpportunitiesPage.matrixAxis')}</th>
                    {[1, 2, 3, 4, 5].map((impact) => <th key={impact} className="p-2 text-slate-500 dark:text-slate-400">{impact}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {heatmap.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      <td className="p-2 font-semibold text-slate-500 dark:text-slate-400">{rowIndex + 1}</td>
                      {row.map((cell) => {
                        const tone = cell.count >= 3 ? 'bg-red-500/20 text-red-700 dark:text-red-300' : cell.count >= 1 ? 'bg-amber-500/20 text-amber-700 dark:text-amber-300' : 'bg-slate-100 dark:bg-slate-800 text-slate-400';
                        return <td key={`${cell.probability}-${cell.impact}`} className={`p-3 rounded ${tone}`}>{cell.count}</td>;
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{t('modules.planning.risksOpportunitiesPage.aiAssistTitle')}</h3>
              <button onClick={handleDetectRisk} disabled={aiLoading} className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 disabled:opacity-50">
                {aiLoading ? t('modules.planning.risksOpportunitiesPage.aiAnalyzing') : t('modules.planning.risksOpportunitiesPage.aiAnalyzeText')}
              </button>
            </div>
            <textarea value={aiText} onChange={(e) => setAiText(e.target.value)} rows={3} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" placeholder={t('modules.planning.risksOpportunitiesPage.aiPlaceholder')} />
            {aiSuggestion?.risk && (
              <div className="rounded-lg border border-purple-200 dark:border-purple-700 bg-purple-50 dark:bg-purple-900/20 p-4 text-sm">
                <p className="font-semibold text-purple-800 dark:text-purple-200">{aiSuggestion.risk.category} · {t('modules.planning.risksOpportunitiesPage.aiLevelLabel')} {aiSuggestion.risk.level}</p>
                <p className="text-purple-700 dark:text-purple-300 mt-1">{t('modules.planning.risksOpportunitiesPage.aiProbabilityLabel')} {aiSuggestion.risk.probability} · {t('modules.planning.risksOpportunitiesPage.aiImpactLabel')} {aiSuggestion.risk.impact}</p>
                <ul className="mt-2 space-y-1 text-purple-700 dark:text-purple-300">
                  {(aiSuggestion.risk.actions || []).map((action, index) => <li key={index}>• {action}</li>)}
                </ul>
              </div>
            )}
          </div>

          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-100 dark:bg-slate-800/60">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.risksOpportunitiesPage.table.code')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.risksOpportunitiesPage.table.title')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.risksOpportunitiesPage.table.type')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.risksOpportunitiesPage.table.category')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.risksOpportunitiesPage.table.level')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.risksOpportunitiesPage.table.actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                {filteredItems.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60 cursor-pointer" onClick={() => handleSelect(item)}>
                    <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.code}</td>
                    <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{item.title}</td>
                    <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.item_type_display}</td>
                    <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.category_display}</td>
                    <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.level_band || item.risk_level || item.opportunity_score}</td>
                    <td className="px-6 py-4 text-sm space-x-2">
                      <button onClick={(e) => { e.stopPropagation(); handleEdit(item); }} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                      <button onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredItems.length === 0 && <CrudEmptyState message={t('modules.planning.risksOpportunitiesPage.empty')} />}
          </div>
        </div>

        <div className="space-y-6">
          <div className="card p-4">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">{t('modules.planning.risksOpportunitiesPage.auditorDetailTitle')}</h3>
            {selected ? (
              <div className="space-y-3 text-sm">
                <div>
                  <p className="font-semibold text-slate-900 dark:text-white">{selected.title}</p>
                  <p className="text-slate-500 dark:text-slate-400">{selected.code} · {selected.category_display}</p>
                </div>
                <p className="text-slate-700 dark:text-slate-300">{selected.description}</p>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="rounded-lg bg-slate-100 dark:bg-slate-800 p-3">{t('modules.planning.risksOpportunitiesPage.probabilityLabel')}: {selected.normalized_probability ?? '-'}</div>
                  <div className="rounded-lg bg-slate-100 dark:bg-slate-800 p-3">{t('modules.planning.risksOpportunitiesPage.impactLabel')}: {selected.normalized_impact ?? '-'}</div>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400 mb-1">{t('modules.planning.risksOpportunitiesPage.suggestedActionsTitle')}</p>
                  <ul className="space-y-1 text-slate-700 dark:text-slate-300">
                    {(selected.proposed_actions || []).length > 0 ? selected.proposed_actions.map((action, index) => <li key={index}>• {action}</li>) : <li>{t('modules.planning.risksOpportunitiesPage.noActions')}</li>}
                  </ul>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400 mb-1">{t('modules.planning.risksOpportunitiesPage.sourcesTitle')}</p>
                  <ul className="space-y-1 text-slate-700 dark:text-slate-300">
                    {(selected.ai_sources || []).length > 0 ? selected.ai_sources.map((source, index) => <li key={index}>• {source}</li>) : <li>{t('modules.planning.risksOpportunitiesPage.noSources')}</li>}
                  </ul>
                </div>
                {!selected.approved_at && (
                  <button onClick={() => handleApprove(selected)} className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm">{t('modules.planning.risksOpportunitiesPage.approveRecord')}</button>
                )}
                {selected.approved_at && <p className="text-xs text-green-600 dark:text-green-400">{t('modules.planning.risksOpportunitiesPage.approvedAt')}: {selected.approved_at}</p>}
              </div>
            ) : (
              <p className="text-sm text-slate-500 dark:text-slate-400">{t('modules.planning.risksOpportunitiesPage.selectPrompt')}</p>
            )}
          </div>

          <div className="card p-4">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">{t('modules.planning.risksOpportunitiesPage.historyTitle')}</h3>
            <div className="space-y-2 text-xs">
              {versions.length > 0 ? versions.map((version) => (
                <div key={version.id} className="rounded-lg bg-slate-100 dark:bg-slate-800 p-3">
                  <p className="font-semibold text-slate-700 dark:text-slate-300">v{version.version_number}</p>
                  <p className="text-slate-500 dark:text-slate-400">{version.change_reason || t('modules.planning.risksOpportunitiesPage.noReason')} · {version.created_at}</p>
                </div>
              )) : <p className="text-slate-500 dark:text-slate-400">{t('modules.planning.risksOpportunitiesPage.noVersions')}</p>}
            </div>
          </div>
        </div>
      </div>

      <Modal title={editingId ? t('modules.planning.risksOpportunitiesPage.edit') : t('modules.planning.risksOpportunitiesPage.new')} isOpen={showForm} onClose={() => setShowForm(false)}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.type')}</label>
              <select value={form.item_type} onChange={(e) => setForm({ ...form, item_type: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="risk">{t('modules.planning.risksOpportunitiesPage.types.risk')}</option>
                <option value="opportunity">{t('modules.planning.risksOpportunitiesPage.types.opportunity')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.code')}</label>
              <input type="text" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.category')}</label>
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                {['strategic', 'operational', 'financial', 'climatic', 'cyber', 'compliance', 'reputation', 'technology', 'market', 'other'].map((category) => (
                  <option key={category} value={category}>{t(`modules.planning.risksOpportunitiesPage.categories.${category}`)}</option>
                ))}
              </select>
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.title')}</label>
              <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('common.forms.description')}</label>
              <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            {form.item_type === 'risk' ? (
              <>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.probability')}</label>
                  <input type="number" min="1" max="5" value={form.probability} onChange={(e) => setForm({ ...form, probability: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.impact')}</label>
                  <input type="number" min="1" max="5" value={form.impact} onChange={(e) => setForm({ ...form, impact: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.feasibility')}</label>
                  <input type="number" min="1" max="5" value={form.feasibility} onChange={(e) => setForm({ ...form, feasibility: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.benefit')}</label>
                  <input type="number" min="1" max="5" value={form.benefit} onChange={(e) => setForm({ ...form, benefit: e.target.value })} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
                </div>
              </>
            )}
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.treatmentDescription')}</label>
              <textarea value={form.treatment_description} onChange={(e) => setForm({ ...form, treatment_description: e.target.value })} rows={2} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
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

export default RisksOpportunitiesPage;