import React, { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import {
  getIndicators,
  getMeasurements,
  createMeasurement,
  updateMeasurement,
  deleteMeasurement
} from '../api/performanceApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const statusLabels = {
  on_target: 'En Objetivo',
  below_target: 'Bajo Objetivo',
  above_target: 'Sobre Objetivo',
  needs_attention: 'Requiere Atencion'
};

const MeasurementsPage = () => {
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;

  const [indicators, setIndicators] = useState([]);
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    indicator: '',
    measurement_date: '',
    actual_value: '',
    target_value: '',
    status: 'on_target',
    comments: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const indicatorMap = useMemo(() => {
    return indicators.reduce((acc, indicator) => {
      acc[indicator.id] = indicator;
      return acc;
    }, {});
  }, [indicators]);

  useEffect(() => {
    if (orgId) loadData();
  }, [orgId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [indicatorsData, measurementsData] = await Promise.all([
        getIndicators({ organization_id: orgId }),
        getMeasurements({ organization_id: orgId })
      ]);
      setIndicators(normalizeList(indicatorsData));
      setItems(normalizeList(measurementsData));
    } catch (error) {
      console.error('Error loading measurements:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleIndicatorChange = (value) => {
    const selected = indicatorMap[value];
    setForm((prev) => ({
      ...prev,
      indicator: value,
      target_value: selected?.target_value ?? prev.target_value
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      setSaving(true);
      const payload = {
        ...form,
        organization_id: orgId,
        indicator: Number(form.indicator),
        actual_value: form.actual_value === '' ? null : Number(form.actual_value),
        target_value: form.target_value === '' ? null : Number(form.target_value)
      };
      if (editingId) {
        await updateMeasurement(editingId, payload);
      } else {
        await createMeasurement(payload);
      }
      resetForm();
      loadData();
    } catch (error) {
      console.error('Error saving measurement:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setForm({
      indicator: item.indicator,
      measurement_date: item.measurement_date || '',
      actual_value: item.actual_value ?? '',
      target_value: item.target_value ?? '',
      status: item.status || 'on_target',
      comments: item.comments || ''
    });
    setEditingId(item.id);
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete measurement?')) return;
    try {
      await deleteMeasurement(id);
      loadData();
    } catch (error) {
      console.error('Error deleting measurement:', error);
    }
  };

  const resetForm = () => {
    setForm({
      indicator: '',
      measurement_date: '',
      actual_value: '',
      target_value: '',
      status: 'on_target',
      comments: ''
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
      <h1 className="text-3xl font-bold text-white">Mediciones</h1>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">{editingId ? 'Editar' : 'Nueva'} Medicion</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Indicador *</label>
              <select
                value={form.indicator}
                onChange={(event) => handleIndicatorChange(event.target.value)}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              >
                <option value="">Selecciona indicador</option>
                {indicators.map((indicator) => (
                  <option key={indicator.id} value={indicator.id}>
                    {indicator.code} - {indicator.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Fecha de Medicion *</label>
              <input
                type="date"
                value={form.measurement_date}
                onChange={(event) => setForm({ ...form, measurement_date: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Estado *</label>
              <select
                value={form.status}
                onChange={(event) => setForm({ ...form, status: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              >
                {Object.entries(statusLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Valor Real *</label>
              <input
                type="number"
                step="0.01"
                value={form.actual_value}
                onChange={(event) => setForm({ ...form, actual_value: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              />
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
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Comentarios</label>
              <textarea
                value={form.comments}
                onChange={(event) => setForm({ ...form, comments: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="3"
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
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Fecha</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Indicador</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Real</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Objetivo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Estado</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-gray-300">{item.measurement_date}</td>
                <td className="px-6 py-4 text-sm text-white">
                  {item.indicator_detail?.code || indicatorMap[item.indicator]?.code}
                </td>
                <td className="px-6 py-4 text-sm text-gray-300">{item.actual_value}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{item.target_value}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{statusLabels[item.status] || item.status}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-400 hover:text-blue-300">Editar</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-400 hover:text-red-300">Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="text-center py-8 text-gray-400">No hay mediciones</div>}
      </div>
    </div>
  );
};

export default MeasurementsPage;
