import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import Modal from '../../../components/Common/Modal';
import { getObjectives, createObjective, updateObjective, deleteObjective, getUsers } from '../api/planningApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const QualityObjectivesPage = () => {
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({
    code: '',
    title: '',
    description: '',
    alignment: 'policy',
    metric: '',
    baseline: '',
    target: '',
    current_value: '',
    unit: '',
    owner: user?.id || '',
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
    budget: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    if (orgId) {
      loadData();
      loadUsers();
    }
  }, [orgId]);

  useEffect(() => {
    if (location.pathname.endsWith('/new')) {
      resetForm();
      setShowForm(true);
    }
  }, [location.pathname]);

  useEffect(() => {
    if (user?.id) {
      setForm(prev => ({ ...prev, owner: prev.owner || user.id }));
    }
  }, [user]);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await getObjectives({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const data = await getUsers({ organization_id: orgId });
      setUsers(normalizeList(data));
    } catch (error) {
      console.error('Error loading users:', error);
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
        owner: form.owner || null
      };
      if (editingId) {
        await updateObjective(editingId, payload);
      } else {
        await createObjective(payload);
      }
      resetForm();
      loadData();
      setShowForm(false);
      if (location.pathname.endsWith('/new')) {
        navigate(location.pathname.replace(/\/new$/, ''), { replace: true });
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
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
      budget: item.budget ?? ''
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar?')) return;
    try {
      await deleteObjective(id);
      loadData();
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const resetForm = () => {
    setForm({
      code: '',
      title: '',
      description: '',
      alignment: 'policy',
      metric: '',
      baseline: '',
      target: '',
      current_value: '',
      unit: '',
      owner: user?.id || '',
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
      budget: ''
    });
    setEditingId(null);
  };

  const openForm = () => {
    resetForm();
    setShowForm(true);
  };

  const closeForm = () => {
    resetForm();
    setShowForm(false);
    if (location.pathname.endsWith('/new')) {
      navigate(location.pathname.replace(/\/new$/, ''), { replace: true });
    }
  };

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-3xl font-bold text-white">Objetivos de Calidad</h1>
        <button
          type="button"
          onClick={openForm}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          Nuevo objetivo
        </button>
      </div>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Código</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Título</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Estado</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Meta</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">% Avance</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Responsable</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-gray-300">{i.code}</td>
                <td className="px-6 py-4 text-sm text-white">{i.title}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.status_display}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.target_date}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.progress_percentage}%</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.owner_name || '-'}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-400 hover:text-blue-300">Editar</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-400 hover:text-red-300">Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="text-center py-8 text-gray-400">No hay objetivos</div>}
      </div>

      <Modal
        title={editingId ? 'Editar objetivo' : 'Nuevo objetivo'}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Código *</label>
              <input type="text" value={form.code} onChange={(e) => setForm({...form, code: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Título *</label>
              <input type="text" value={form.title} onChange={(e) => setForm({...form, title: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Descripción</label>
              <textarea value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="3" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Alineación</label>
              <select value={form.alignment} onChange={(e) => setForm({...form, alignment: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="policy">Política de Calidad</option>
                <option value="strategic">Estrategia Organizacional</option>
                <option value="customer">Requisitos del Cliente</option>
                <option value="compliance">Cumplimiento Legal</option>
                <option value="improvement">Mejora Continua</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Métrica *</label>
              <input type="text" value={form.metric} onChange={(e) => setForm({...form, metric: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Unidad</label>
              <input type="text" value={form.unit} onChange={(e) => setForm({...form, unit: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Línea Base</label>
              <input type="number" value={form.baseline} onChange={(e) => setForm({...form, baseline: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Meta *</label>
              <input type="number" value={form.target} onChange={(e) => setForm({...form, target: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Valor Actual</label>
              <input type="number" value={form.current_value} onChange={(e) => setForm({...form, current_value: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Responsable</label>
              <select value={form.owner} onChange={(e) => setForm({...form, owner: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="">Sin asignar</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name || u.username || u.email}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Fecha Inicio *</label>
              <input type="date" value={form.start_date} onChange={(e) => setForm({...form, start_date: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Fecha Meta *</label>
              <input type="date" value={form.target_date} onChange={(e) => setForm({...form, target_date: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Estado</label>
              <select value={form.status} onChange={(e) => setForm({...form, status: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="draft">Borrador</option>
                <option value="approved">Aprobado</option>
                <option value="in_progress">En Progreso</option>
                <option value="achieved">Logrado</option>
                <option value="partially_achieved">Parcialmente Logrado</option>
                <option value="not_achieved">No Logrado</option>
                <option value="cancelled">Cancelado</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">% Avance</label>
              <input type="number" min="0" max="100" value={form.progress_percentage} onChange={(e) => setForm({...form, progress_percentage: parseInt(e.target.value || 0)})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Recursos Requeridos</label>
              <textarea value={form.required_resources} onChange={(e) => setForm({...form, required_resources: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Presupuesto</label>
              <input type="number" value={form.budget} onChange={(e) => setForm({...form, budget: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Criterios SMART</label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <label className="flex items-center space-x-2">
                  <input type="checkbox" checked={form.is_specific} onChange={(e) => setForm({...form, is_specific: e.target.checked})} className="rounded" />
                  <span className="text-sm text-gray-300">Específico</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input type="checkbox" checked={form.is_measurable} onChange={(e) => setForm({...form, is_measurable: e.target.checked})} className="rounded" />
                  <span className="text-sm text-gray-300">Medible</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input type="checkbox" checked={form.is_achievable} onChange={(e) => setForm({...form, is_achievable: e.target.checked})} className="rounded" />
                  <span className="text-sm text-gray-300">Alcanzable</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input type="checkbox" checked={form.is_relevant} onChange={(e) => setForm({...form, is_relevant: e.target.checked})} className="rounded" />
                  <span className="text-sm text-gray-300">Relevante</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input type="checkbox" checked={form.is_time_bound} onChange={(e) => setForm({...form, is_time_bound: e.target.checked})} className="rounded" />
                  <span className="text-sm text-gray-300">Temporal</span>
                </label>
              </div>
            </div>
          </div>
          <div className="flex space-x-3">
            <button type="submit" disabled={saving} className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
              {saving ? 'Guardando...' : editingId ? 'Actualizar' : 'Crear'}
            </button>
            {editingId && <button type="button" onClick={closeForm} className="px-6 py-2 bg-gray-600 text-white rounded-lg">Cancelar</button>}
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default QualityObjectivesPage;
