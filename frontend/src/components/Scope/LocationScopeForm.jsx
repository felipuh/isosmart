import React, { useState, useEffect } from 'react';
import { X, Save, Plus } from 'lucide-react';

const LocationScopeForm = ({ location, scopeId, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    scope_definition: scopeId,
    location_name: '',
    address: '',
    location_type: 'office',
    country: 'Costa Rica',
    city: '',
    activities: [],
    employee_count: 0,
    is_included: true
  });

  const [newActivity, setNewActivity] = useState('');
  const [saving, setSaving] = useState(false);

  const LOCATION_TYPES = [
    { value: 'headquarters', label: 'Sede Principal' },
    { value: 'branch', label: 'Sucursal' },
    { value: 'warehouse', label: 'Almacén/Bodega' },
    { value: 'plant', label: 'Planta de Producción' },
    { value: 'office', label: 'Oficina' },
    { value: 'remote', label: 'Trabajo Remoto' }
  ];

  useEffect(() => {
    if (location) {
      setFormData({
        scope_definition: location.scope_definition || scopeId,
        location_name: location.location_name || '',
        address: location.address || '',
        location_type: location.location_type || 'office',
        country: location.country || 'Costa Rica',
        city: location.city || '',
        activities: location.activities || [],
        employee_count: location.employee_count || 0,
        is_included: location.is_included !== undefined ? location.is_included : true
      });
    }
  }, [location, scopeId]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : type === 'number' ? parseInt(value) || 0 : value
    }));
  };

  const handleAddActivity = () => {
    if (newActivity.trim()) {
      setFormData(prev => ({
        ...prev,
        activities: [...prev.activities, newActivity.trim()]
      }));
      setNewActivity('');
    }
  };

  const handleRemoveActivity = (index) => {
    setFormData(prev => ({
      ...prev,
      activities: prev.activities.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.location_name.trim()) {
      alert('El nombre de la ubicación es requerido');
      return;
    }
    if (!formData.city.trim()) {
      alert('La ciudad es requerida');
      return;
    }
    setSaving(true);
    try {
      await onSave(formData);
    } catch (error) {
      console.error('Error guardando:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black dark:bg-gray-900 bg-opacity-50 dark:bg-opacity-75 flex items-center justify-center z-50 p-4 transition-colors">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl dark:shadow-slate-900/50 w-full max-w-2xl max-h-[90vh] overflow-y-auto transition-colors">
        <div className="sticky top-0 bg-white dark:bg-slate-800 border-b dark:border-slate-700 px-6 py-4 flex items-center justify-between transition-colors">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            {location ? 'Editar Ubicación' : 'Nueva Ubicación en Alcance'}
          </h2>
          <button onClick={onClose} className="text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-300 transition-colors">
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Información Básica */}
          <div className="bg-gray-50 dark:bg-slate-700/50 rounded-lg p-4 transition-colors">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Información de la Ubicación</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Nombre de la Ubicación *
                </label>
                <input
                  type="text"
                  name="location_name"
                  value={formData.location_name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder="Ej: Oficina Central San José"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Tipo de Ubicación *
                </label>
                <select
                  name="location_type"
                  value={formData.location_type}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                >
                  {LOCATION_TYPES.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Número de Empleados
                </label>
                <input
                  type="number"
                  name="employee_count"
                  value={formData.employee_count}
                  onChange={handleChange}
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  País *
                </label>
                <input
                  type="text"
                  name="country"
                  value={formData.country}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder="Costa Rica"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Ciudad *
                </label>
                <input
                  type="text"
                  name="city"
                  value={formData.city}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder="San José"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Dirección Completa
                </label>
                <textarea
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder="Dirección física de la ubicación..."
                />
              </div>
            </div>
          </div>

          {/* Actividades */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-100 dark:border-blue-800 transition-colors">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Actividades Realizadas</h3>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newActivity}
                onChange={(e) => setNewActivity(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddActivity())}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white transition-colors"
                placeholder="Agregar actividad..."
              />
              <button
                type="button"
                onClick={handleAddActivity}
                className="px-3 py-2 bg-blue-500 dark:bg-blue-600 text-white rounded-lg hover:bg-blue-600 dark:hover:bg-blue-700 transition-colors"
              >
                <Plus className="h-5 w-5" />
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.activities.map((activity, index) => (
                <span key={index} className="flex items-center bg-white dark:bg-slate-700 px-3 py-1 rounded-full border dark:border-slate-600 text-sm dark:text-slate-300 transition-colors">
                  {activity}
                  <button type="button" onClick={() => handleRemoveActivity(index)} className="ml-2 text-red-500 dark:text-red-400 transition-colors">
                    <X className="h-4 w-4" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Inclusión */}
          <div className="flex items-center">
            <input
              type="checkbox"
              name="is_included"
              checked={formData.is_included}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 dark:text-blue-500 border-gray-300 dark:border-slate-600 dark:bg-slate-700 rounded transition-colors"
            />
            <label className="ml-2 text-sm text-gray-700 dark:text-slate-300">
              Incluida en el Alcance del SGC
            </label>
          </div>

          {/* Botones */}
          <div className="flex justify-end gap-3 pt-4 border-t dark:border-slate-700 transition-colors">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 dark:text-slate-300 bg-gray-100 dark:bg-slate-700 rounded-lg hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 disabled:bg-blue-300 dark:disabled:bg-blue-900/30 transition-colors"
            >
              <Save className="mr-2 h-4 w-4" />
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LocationScopeForm;
