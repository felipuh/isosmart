import React, { useEffect, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import {
  getIndicators,
  createIndicator,
  updateIndicator,
  deleteIndicator
} from '../api/performanceApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const indicatorTypeLabels = {
  quality: 'Calidad',
  efficiency: 'Eficiencia',
  effectiveness: 'Efectividad',
  customer_satisfaction: 'Satisfaccion del Cliente',
  process: 'Desempeno de Procesos',
  financial: 'Financiero',
  operational: 'Operacional'
};

const frequencyLabels = {
  daily: 'Diario',
  weekly: 'Semanal',
  monthly: 'Mensual',
  quarterly: 'Trimestral',
  annually: 'Anual'
};

const statusLabels = {
  active: 'Activo',
  inactive: 'Inactivo',
  archived: 'Archivado'
};

const IndicatorsPage = () => {
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';

  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    code: '',
    name: '',
    description: '',
    indicator_type: 'quality',
    measurement_method: '',
    formula: '',
    target_value: '',
    unit_of_measure: '',
    frequency: 'monthly',
    status: 'active'
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (orgId) loadIndicators();
  }, [orgId]);

  const loadIndicators = async () => {
    try {
      setLoading(true);
      const data = await getIndicators({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error loading indicators:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      setSaving(true);
      const payload = {
        ...form,
        organization_id: orgId,
        organization_name: orgName,
        target_value: form.target_value === '' ? null : Number(form.target_value)
      };
      if (editingId) {
        await updateIndicator(editingId, payload);
      } else {
        await createIndicator(payload);
      }
      resetForm();
      loadIndicators();
    } catch (error) {
      console.error('Error saving indicator:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setForm({
      code: item.code || '',
      name: item.name || '',
      description: item.description || '',
      indicator_type: item.indicator_type || 'quality',
      measurement_method: item.measurement_method || '',
      formula: item.formula || '',
      target_value: item.target_value ?? '',
      unit_of_measure: item.unit_of_measure || '',
      frequency: item.frequency || 'monthly',
      status: item.status || 'active'
    });
    setEditingId(item.id);
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete indicator?')) return;
    try {
      await deleteIndicator(id);
      loadIndicators();
    } catch (error) {
      console.error('Error deleting indicator:', error);
    }
  };

  const resetForm = () => {
    setForm({
      code: '',
      name: '',
      description: '',
      indicator_type: 'quality',
      measurement_method: '',
      formula: '',
      target_value: '',
      unit_of_measure: '',
      frequency: 'monthly',
      status: 'active'
    });
    setEditingId(null);
  };

  if (loading) {
    return (
      <div className="flex justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Indicadores de Desempeno</h1>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">{editingId ? 'Editar' : 'Nuevo'} Indicador</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Codigo *</label>
              <input
                type="text"
                value={form.code}
                onChange={(event) => setForm({ ...form, code: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Nombre *</label>
              <input
                type="text"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Tipo *</label>
              <select
                value={form.indicator_type}
                onChange={(event) => setForm({ ...form, indicator_type: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              >
                {Object.entries(indicatorTypeLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Frecuencia *</label>
              <select
                value={form.frequency}
                onChange={(event) => setForm({ ...form, frequency: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              >
                {Object.entries(frequencyLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Valor Objetivo *</label>
              <input
                type="number"
                step="0.01"
                value={form.target_value}
                onChange={(event) => setForm({ ...form, target_value: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Unidad *</label>
              <input
                type="text"
                value={form.unit_of_measure}
                onChange={(event) => setForm({ ...form, unit_of_measure: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Estado</label>
              <select
                value={form.status}
                onChange={(event) => setForm({ ...form, status: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              >
                {Object.entries(statusLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Metodo de Medicion *</label>
              <textarea
                value={form.measurement_method}
                onChange={(event) => setForm({ ...form, measurement_method: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="2"
                required
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Formula</label>
              <textarea
                value={form.formula}
                onChange={(event) => setForm({ ...form, formula: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="2"
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Descripcion *</label>
              <textarea
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="3"
                required
              />
            </div>
          </div>
          <div className="flex space-x-3">
            <button type="submit" disabled={saving} className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
              {saving ? 'Guardando...' : editingId ? 'Actualizar' : 'Crear'}
            </button>
            {editingId && (
              <button type="button" onClick={resetForm} className="px-6 py-2 bg-gray-600 text-white rounded-lg">Cancelar</button>
            )}
          </div>
        </form>
      </div>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Codigo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Nombre</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Tipo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Frecuencia</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Estado</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-gray-300">{item.code}</td>
                <td className="px-6 py-4 text-sm text-white">{item.name}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{indicatorTypeLabels[item.indicator_type] || item.indicator_type}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{frequencyLabels[item.frequency] || item.frequency}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{statusLabels[item.status] || item.status}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-400 hover:text-blue-300">Editar</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-400 hover:text-red-300">Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="text-center py-8 text-gray-400">No hay indicadores</div>}
      </div>
    </div>
  );
};

export default IndicatorsPage;
