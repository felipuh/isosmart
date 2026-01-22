import React, { useState, useEffect } from 'react';
import { X, Save, Plus, Trash2 } from 'lucide-react';

const ProcessScopeForm = ({ process, scopeId, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    scope_definition: scopeId,
    process_name: '',
    process_code: '',
    process_type: 'operational',
    description: '',
    owner: '',
    inputs: [],
    outputs: [],
    kpis: [],
    is_included: true,
    exclusion_reason: ''
  });

  const [newInput, setNewInput] = useState('');
  const [newOutput, setNewOutput] = useState('');
  const [newKpi, setNewKpi] = useState('');
  const [saving, setSaving] = useState(false);

  const PROCESS_TYPES = [
    { value: 'strategic', label: 'Estratégico' },
    { value: 'operational', label: 'Operativo' },
    { value: 'support', label: 'Apoyo' }
  ];

  useEffect(() => {
    if (process) {
      setFormData({
        scope_definition: process.scope_definition || scopeId,
        process_name: process.process_name || '',
        process_code: process.process_code || '',
        process_type: process.process_type || 'operational',
        description: process.description || '',
        owner: process.owner || '',
        inputs: process.inputs || [],
        outputs: process.outputs || [],
        kpis: process.kpis || [],
        is_included: process.is_included !== undefined ? process.is_included : true,
        exclusion_reason: process.exclusion_reason || ''
      });
    }
  }, [process, scopeId]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleAddItem = (field, value, setter) => {
    if (value.trim()) {
      setFormData(prev => ({
        ...prev,
        [field]: [...prev[field], value.trim()]
      }));
      setter('');
    }
  };

  const handleRemoveItem = (field, index) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.process_name.trim()) {
      alert('El nombre del proceso es requerido');
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
            {process ? 'Editar Proceso' : 'Nuevo Proceso en Alcance'}
          </h2>
          <button onClick={onClose} className="text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-300 transition-colors">
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Información Básica */}
          <div className="bg-gray-50 dark:bg-slate-700/50 rounded-lg p-4 transition-colors">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Información del Proceso</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Nombre del Proceso *
                </label>
                <input
                  type="text"
                  name="process_name"
                  value={formData.process_name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder="Ej: Gestión de Producción"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Código del Proceso
                </label>
                <input
                  type="text"
                  name="process_code"
                  value={formData.process_code}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder="Ej: PRO-001"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Tipo de Proceso *
                </label>
                <select
                  name="process_type"
                  value={formData.process_type}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                >
                  {PROCESS_TYPES.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Responsable
                </label>
                <input
                  type="text"
                  name="owner"
                  value={formData.owner}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder="Nombre del responsable"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Descripción
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder="Descripción del proceso..."
                />
              </div>
            </div>
          </div>

          {/* Entradas */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-100 dark:border-blue-800 transition-colors">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Entradas del Proceso</h3>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newInput}
                onChange={(e) => setNewInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddItem('inputs', newInput, setNewInput))}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white transition-colors"
                placeholder="Agregar entrada..."
              />
              <button
                type="button"
                onClick={() => handleAddItem('inputs', newInput, setNewInput)}
                className="px-3 py-2 bg-blue-500 dark:bg-blue-600 text-white rounded-lg hover:bg-blue-600 dark:hover:bg-blue-700 transition-colors"
              >
                <Plus className="h-5 w-5" />
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.inputs.map((item, index) => (
                <span key={index} className="flex items-center bg-white dark:bg-slate-700 px-3 py-1 rounded-full border dark:border-slate-600 text-sm dark:text-slate-300 transition-colors">
                  {item}
                  <button type="button" onClick={() => handleRemoveItem('inputs', index)} className="ml-2 text-red-500 dark:text-red-400 transition-colors">
                    <X className="h-4 w-4" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Salidas */}
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-100 dark:border-green-800 transition-colors">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Salidas del Proceso</h3>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newOutput}
                onChange={(e) => setNewOutput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddItem('outputs', newOutput, setNewOutput))}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white transition-colors"
                placeholder="Agregar salida..."
              />
              <button
                type="button"
                onClick={() => handleAddItem('outputs', newOutput, setNewOutput)}
                className="px-3 py-2 bg-green-500 dark:bg-green-600 text-white rounded-lg hover:bg-green-600 dark:hover:bg-green-700 transition-colors"
              >
                <Plus className="h-5 w-5" />
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.outputs.map((item, index) => (
                <span key={index} className="flex items-center bg-white dark:bg-slate-700 px-3 py-1 rounded-full border dark:border-slate-600 text-sm dark:text-slate-300 transition-colors">
                  {item}
                  <button type="button" onClick={() => handleRemoveItem('outputs', index)} className="ml-2 text-red-500 dark:text-red-400 transition-colors">
                    <X className="h-4 w-4" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* KPIs */}
          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-100 dark:border-purple-800 transition-colors">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Indicadores (KPIs)</h3>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newKpi}
                onChange={(e) => setNewKpi(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddItem('kpis', newKpi, setNewKpi))}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white transition-colors"
                placeholder="Agregar KPI..."
              />
              <button
                type="button"
                onClick={() => handleAddItem('kpis', newKpi, setNewKpi)}
                className="px-3 py-2 bg-purple-500 dark:bg-purple-600 text-white rounded-lg hover:bg-purple-600 dark:hover:bg-purple-700 transition-colors"
              >
                <Plus className="h-5 w-5" />
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.kpis.map((item, index) => (
                <span key={index} className="flex items-center bg-white dark:bg-slate-700 px-3 py-1 rounded-full border dark:border-slate-600 text-sm dark:text-slate-300 transition-colors">
                  {item}
                  <button type="button" onClick={() => handleRemoveItem('kpis', index)} className="ml-2 text-red-500 dark:text-red-400 transition-colors">
                    <X className="h-4 w-4" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Inclusión */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 border border-yellow-100 dark:border-yellow-800 transition-colors">
            <div className="flex items-center mb-3">
              <input
                type="checkbox"
                name="is_included"
                checked={formData.is_included}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 dark:text-blue-500 border-gray-300 dark:border-slate-600 dark:bg-slate-700 rounded transition-colors"
              />
              <label className="ml-2 text-sm font-medium text-gray-700 dark:text-slate-300">
                Incluido en el Alcance del SGC
              </label>
            </div>
            {!formData.is_included && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Razón de Exclusión
                </label>
                <textarea
                  name="exclusion_reason"
                  value={formData.exclusion_reason}
                  onChange={handleChange}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white transition-colors"
                  placeholder="Justifique la exclusión..."
                />
              </div>
            )}
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

export default ProcessScopeForm;
