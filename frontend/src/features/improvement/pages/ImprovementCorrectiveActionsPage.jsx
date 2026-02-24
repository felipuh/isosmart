import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import { useLocation, useNavigate } from 'react-router-dom';
import Modal from '../../../components/Common/Modal';
import { getCorrectiveActions, createCorrectiveAction, updateCorrectiveAction, deleteCorrectiveAction, getNonconformities } from '../api/improvementApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];
const actionTypeLabels = { corrective: 'Correctiva', preventive: 'Preventiva', improvement: 'Mejora' };
const statusLabels = { planned: 'Planificada', in_progress: 'En progreso', implemented: 'Implementada', verified: 'Verificada', effective: 'Efectiva', not_effective: 'No efectiva', cancelled: 'Cancelada' };
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

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [actionsData, ncsData] = await Promise.all([getCorrectiveActions({ organization_id: orgId }), getNonconformities({ organization_id: orgId })]);
      setItems(normalizeList(actionsData));
      setNcs(normalizeList(ncsData));
    } catch (error) { console.error('Error:', error); } finally { setLoading(false); }
  }, [orgId]);

  useEffect(() => { if (orgId) loadData(); }, [orgId, loadData]);
  useEffect(() => { if (location.pathname.endsWith('/new')) { resetForm(); setShowForm(true); } }, [location.pathname]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = { ...form, organization_id: orgId, responsible: user?.id || null, completion_percentage: Number(form.completion_percentage), nonconformity: form.nonconformity || null };
      if (editingId) { await updateCorrectiveAction(editingId, payload); } else { await createCorrectiveAction(payload); }
      resetForm(); await loadData(); setShowForm(false);
      if (location.pathname.endsWith('/new')) navigate(location.pathname.replace(/\/new$/, ''), { replace: true });
    } catch (error) { console.error('Error:', error); } finally { setSaving(false); }
  };

  const handleEdit = (item) => {
    setForm({ nonconformity: item.nonconformity || '', action_number: item.action_number || '', action_type: item.action_type || 'corrective', root_cause_analysis: item.root_cause_analysis || '', root_cause_identified: item.root_cause_identified || '', analysis_method: item.analysis_method || '', action_description: item.action_description || '', implementation_steps: item.implementation_steps || '', resources_required: item.resources_required || '', planned_start_date: item.planned_start_date || '', planned_completion_date: item.planned_completion_date || '', verification_method: item.verification_method || '', effectiveness_criteria: item.effectiveness_criteria || '', status: item.status || 'planned', completion_percentage: item.completion_percentage || 0, comments: item.comments || '' });
    setEditingId(item.id); setShowForm(true);
  };

  const handleDelete = async (id) => { if (!confirm('¿Eliminar esta acción correctiva?')) return; try { await deleteCorrectiveAction(id); await loadData(); } catch (error) { console.error('Error:', error); } };
  const resetForm = () => { setForm(initialForm); setEditingId(null); };
  const openForm = () => { resetForm(); setShowForm(true); };
  const closeForm = () => { resetForm(); setShowForm(false); if (location.pathname.endsWith('/new')) navigate(location.pathname.replace(/\/new$/, ''), { replace: true }); };

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h1 className="text-3xl font-bold text-white">Acciones Correctivas</h1><p className="text-gray-400 mt-1">ISO 9001:2015 - Cláusula 10.2</p></div>
        <button type="button" onClick={openForm} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">Nueva acción correctiva</button>
      </div>

      <Modal
        title={editingId ? 'Editar acción correctiva' : 'Nueva acción correctiva'}
        isOpen={showForm}
        onClose={closeForm}
        maxWidth="max-w-6xl"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="text-xs text-slate-400">Número de acción *<input type="text" required value={form.action_number} onChange={e => setForm({ ...form, action_number: e.target.value })} placeholder="AC-2026-001" className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
              <label className="text-xs text-slate-400">No conformidad asociada *
                <select required value={form.nonconformity} onChange={e => setForm({ ...form, nonconformity: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                  <option value="">Seleccionar NC…</option>
                  {ncs.map(nc => <option key={nc.id} value={nc.id}>{nc.nc_number} - {nc.title}</option>)}
                </select>
              </label>
              <label className="text-xs text-slate-400">Tipo
                <select value={form.action_type} onChange={e => setForm({ ...form, action_type: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                  {Object.entries(actionTypeLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="text-xs text-slate-400">Análisis de causa raíz *<textarea required value={form.root_cause_analysis} onChange={e => setForm({ ...form, root_cause_analysis: e.target.value })} placeholder="5 porqués, Ishikawa, etc." className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
              <label className="text-xs text-slate-400">Causa raíz identificada *<textarea required value={form.root_cause_identified} onChange={e => setForm({ ...form, root_cause_identified: e.target.value })} className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
            </div>
            <label className="text-xs text-slate-400 block">Método de análisis<input type="text" value={form.analysis_method} onChange={e => setForm({ ...form, analysis_method: e.target.value })} placeholder="5 porqués, Ishikawa, Pareto..." className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
            <label className="text-xs text-slate-400 block">Descripción de la acción *<textarea required value={form.action_description} onChange={e => setForm({ ...form, action_description: e.target.value })} className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
            <label className="text-xs text-slate-400 block">Pasos de implementación *<textarea required value={form.implementation_steps} onChange={e => setForm({ ...form, implementation_steps: e.target.value })} className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="text-xs text-slate-400">Recursos requeridos<textarea value={form.resources_required} onChange={e => setForm({ ...form, resources_required: e.target.value })} className="mt-1 h-16 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
              <label className="text-xs text-slate-400">Inicio planificado *<input type="date" required value={form.planned_start_date} onChange={e => setForm({ ...form, planned_start_date: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
              <label className="text-xs text-slate-400">Fin planificado *<input type="date" required value={form.planned_completion_date} onChange={e => setForm({ ...form, planned_completion_date: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="text-xs text-slate-400">Estado
                <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                  {Object.entries(statusLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <label className="text-xs text-slate-400">% Completado<input type="number" min="0" max="100" value={form.completion_percentage} onChange={e => setForm({ ...form, completion_percentage: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
              <label className="text-xs text-slate-400">Comentarios<input type="text" value={form.comments} onChange={e => setForm({ ...form, comments: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
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
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acción #</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">NC</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Tipo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Progreso</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700/30">
            {items.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-8 text-center text-gray-400">No hay acciones correctivas registradas</td></tr>
            ) : items.map(item => (
              <tr key={item.id} className="hover:bg-gray-800/30">
                <td className="px-6 py-4 text-sm font-mono text-blue-400">{item.action_number}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{item.nonconformity_number || `NC #${item.nonconformity}`}</td>
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