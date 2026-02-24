import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useLocation, useNavigate } from 'react-router-dom';
import Modal from '../../../components/Common/Modal';
import { getContinualImprovements, createContinualImprovement, updateContinualImprovement, deleteContinualImprovement } from '../api/improvementApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];
const improvementTypeLabels = { process: 'Mejora de proceso', product: 'Mejora de producto', service: 'Mejora de servicio', system: 'Mejora del SGC', technology: 'Mejora tecnológica', methodology: 'Mejora metodológica' };
const priorityLabels = { critical: 'Crítica', high: 'Alta', medium: 'Media', low: 'Baja' };
const statusLabels = { proposed: 'Propuesta', under_evaluation: 'En evaluación', approved: 'Aprobada', in_progress: 'En progreso', implemented: 'Implementada', measuring_results: 'Midiendo resultados', successful: 'Exitosa', unsuccessful: 'No exitosa', cancelled: 'Cancelada' };
const statusColors = { proposed: 'bg-gray-500/20 text-gray-400', under_evaluation: 'bg-blue-500/20 text-blue-400', approved: 'bg-cyan-500/20 text-cyan-400', in_progress: 'bg-orange-500/20 text-orange-400', implemented: 'bg-purple-500/20 text-purple-400', measuring_results: 'bg-yellow-500/20 text-yellow-400', successful: 'bg-green-500/20 text-green-400', unsuccessful: 'bg-red-500/20 text-red-400', cancelled: 'bg-gray-500/20 text-gray-400' };
const priorityColors = { critical: 'bg-red-500/20 text-red-400', high: 'bg-orange-500/20 text-orange-400', medium: 'bg-yellow-500/20 text-yellow-400', low: 'bg-green-500/20 text-green-400' };

const initialForm = { initiative_number: '', title: '', description: '', improvement_type: 'process', current_situation: '', proposed_improvement: '', expected_benefits: '', alignment_with_objectives: '', estimated_investment: '', estimated_savings: '', expected_roi: '', priority: 'medium', proposed_date: '', status: 'proposed', completion_percentage: 0 };

const ImprovementContinualPage = () => {
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

  const loadData = useCallback(async () => {
    try { setLoading(true); const data = await getContinualImprovements({ organization_id: orgId }); setItems(normalizeList(data)); }
    catch (error) { console.error('Error:', error); } finally { setLoading(false); }
  }, [orgId]);

  useEffect(() => { if (orgId) loadData(); }, [orgId, loadData]);
  useEffect(() => { if (location.pathname.endsWith('/new')) { resetForm(); setShowForm(true); } }, [location.pathname]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = { ...form, organization_id: orgId, organization_name: orgName, champion: user?.id || null, completion_percentage: Number(form.completion_percentage), estimated_investment: form.estimated_investment === '' ? null : Number(form.estimated_investment), estimated_savings: form.estimated_savings === '' ? null : Number(form.estimated_savings), expected_roi: form.expected_roi === '' ? null : Number(form.expected_roi) };
      if (editingId) { await updateContinualImprovement(editingId, payload); } else { await createContinualImprovement(payload); }
      resetForm(); await loadData(); setShowForm(false);
      if (location.pathname.endsWith('/new')) navigate(location.pathname.replace(/\/new$/, ''), { replace: true });
    } catch (error) { console.error('Error:', error); } finally { setSaving(false); }
  };

  const handleEdit = (item) => {
    setForm({ initiative_number: item.initiative_number || '', title: item.title || '', description: item.description || '', improvement_type: item.improvement_type || 'process', current_situation: item.current_situation || '', proposed_improvement: item.proposed_improvement || '', expected_benefits: item.expected_benefits || '', alignment_with_objectives: item.alignment_with_objectives || '', estimated_investment: item.estimated_investment ?? '', estimated_savings: item.estimated_savings ?? '', expected_roi: item.expected_roi ?? '', priority: item.priority || 'medium', proposed_date: item.proposed_date || '', status: item.status || 'proposed', completion_percentage: item.completion_percentage || 0 });
    setEditingId(item.id); setShowForm(true);
  };

  const handleDelete = async (id) => { if (!confirm('¿Eliminar esta iniciativa de mejora?')) return; try { await deleteContinualImprovement(id); await loadData(); } catch (error) { console.error('Error:', error); } };
  const resetForm = () => { setForm(initialForm); setEditingId(null); };
  const openForm = () => { resetForm(); setShowForm(true); };
  const closeForm = () => { resetForm(); setShowForm(false); if (location.pathname.endsWith('/new')) navigate(location.pathname.replace(/\/new$/, ''), { replace: true }); };

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h1 className="text-3xl font-bold text-white">Mejora Continua</h1><p className="text-gray-400 mt-1">ISO 9001:2015 - Cláusula 10.3</p></div>
        <button type="button" onClick={openForm} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">Nueva iniciativa</button>
      </div>

      <Modal
        title={editingId ? 'Editar iniciativa de mejora' : 'Nueva iniciativa de mejora'}
        isOpen={showForm}
        onClose={closeForm}
        maxWidth="max-w-6xl"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="text-xs text-slate-400">Número *<input type="text" required value={form.initiative_number} onChange={e => setForm({ ...form, initiative_number: e.target.value })} placeholder="MI-2026-001" className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
              <label className="text-xs text-slate-400">Título *<input type="text" required value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
              <label className="text-xs text-slate-400">Fecha propuesta *<input type="date" required value={form.proposed_date} onChange={e => setForm({ ...form, proposed_date: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
            </div>
            <label className="text-xs text-slate-400 block">Descripción *<textarea required value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="text-xs text-slate-400">Tipo
                <select value={form.improvement_type} onChange={e => setForm({ ...form, improvement_type: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                  {Object.entries(improvementTypeLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <label className="text-xs text-slate-400">Prioridad
                <select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                  {Object.entries(priorityLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <label className="text-xs text-slate-400">Estado
                <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                  {Object.entries(statusLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="text-xs text-slate-400">Situación actual *<textarea required value={form.current_situation} onChange={e => setForm({ ...form, current_situation: e.target.value })} className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
              <label className="text-xs text-slate-400">Mejora propuesta *<textarea required value={form.proposed_improvement} onChange={e => setForm({ ...form, proposed_improvement: e.target.value })} className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="text-xs text-slate-400">Beneficios esperados *<textarea required value={form.expected_benefits} onChange={e => setForm({ ...form, expected_benefits: e.target.value })} className="mt-1 h-16 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
              <label className="text-xs text-slate-400">Alineación con objetivos<textarea value={form.alignment_with_objectives} onChange={e => setForm({ ...form, alignment_with_objectives: e.target.value })} className="mt-1 h-16 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
            </div>
            <div className="grid gap-4 sm:grid-cols-4">
              <label className="text-xs text-slate-400">Inversión ($)<input type="number" step="0.01" value={form.estimated_investment} onChange={e => setForm({ ...form, estimated_investment: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
              <label className="text-xs text-slate-400">Ahorro ($)<input type="number" step="0.01" value={form.estimated_savings} onChange={e => setForm({ ...form, estimated_savings: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
              <label className="text-xs text-slate-400">ROI (%)<input type="number" step="0.01" value={form.expected_roi} onChange={e => setForm({ ...form, expected_roi: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
              <label className="text-xs text-slate-400">% Completado<input type="number" min="0" max="100" value={form.completion_percentage} onChange={e => setForm({ ...form, completion_percentage: e.target.value })} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" /></label>
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="submit" disabled={saving || !orgId} className="rounded-lg bg-emerald-500/80 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50">{saving ? 'Guardando...' : editingId ? 'Actualizar' : 'Crear'}</button>
              <button type="button" onClick={closeForm} className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-200">Cancelar</button>
            </div>
        </form>
      </Modal>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Iniciativa #</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Título</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Tipo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Prioridad</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Progreso</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Estado</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700/30">
            {items.length === 0 ? (
              <tr><td colSpan={7} className="px-6 py-8 text-center text-gray-400">No hay iniciativas de mejora registradas</td></tr>
            ) : items.map(item => (
              <tr key={item.id} className="hover:bg-gray-800/30">
                <td className="px-6 py-4 text-sm font-mono text-blue-400">{item.initiative_number}</td>
                <td className="px-6 py-4 text-sm text-gray-200">{item.title}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{improvementTypeLabels[item.improvement_type] || item.improvement_type}</td>
                <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${priorityColors[item.priority] || ''}`}>{priorityLabels[item.priority] || item.priority}</span></td>
                <td className="px-6 py-4"><div className="flex items-center gap-2"><div className="w-20 bg-gray-700 rounded-full h-2"><div className="bg-green-500 h-2 rounded-full" style={{ width: `${item.completion_percentage || 0}%` }}></div></div><span className="text-xs text-gray-400">{item.completion_percentage || 0}%</span></div></td>
                <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${statusColors[item.status] || ''}`}>{statusLabels[item.status] || item.status}</span></td>
                <td className="px-6 py-4 space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-400 hover:text-blue-300 text-sm">Editar</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-400 hover:text-red-300 text-sm">Eliminar</button>
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