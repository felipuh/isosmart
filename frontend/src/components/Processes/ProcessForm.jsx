import React, { useState, useEffect } from 'react';
import { X, Save, Plus } from 'lucide-react';

const ProcessForm = ({ process, mapId, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    process_map: mapId,
    code: '',
    name: '',
    description: '',
    process_type: 'operational',
    objective: '',
    owner: '',
    inputs: [],
    outputs: [],
    resources: [],
    kpis: [],
    risks: [],
    controls: [],
    documented_in: '',
    is_active: true
  });

  const [newInput, setNewInput] = useState('');
  const [newOutput, setNewOutput] = useState('');
  const [newResource, setNewResource] = useState('');
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
        process_map: process.process_map || mapId,
        code: process.code || '',
        name: process.name || '',
        description: process.description || '',
        process_type: process.process_type || 'operational',
        objective: process.objective || '',
        owner: process.owner || '',
        inputs: process.inputs || [],
        outputs: process.outputs || [],
        resources: process.resources || [],
        kpis: process.kpis || [],
        risks: process.risks || [],
        controls: process.controls || [],
        documented_in: process.documented_in || '',
        is_active: process.is_active !== undefined ? process.is_active : true
      });
    }
  }, [process, mapId]);

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
    if (!formData.code.trim() || !formData.name.trim()) {
      alert('El código y nombre del proceso son requeridos');
      return;
    }
    if (!formData.owner.trim()) {
      alert('El responsable del proceso es requerido');
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

  const renderListSection = (title, field, value, setter, color) => {
    const colorMap = {
      'blue': 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-700 text-blue-900 dark:text-blue-300',
      'green': 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-700 text-green-900 dark:text-green-300',
      'purple': 'bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-700 text-purple-900 dark:text-purple-300',
      'yellow': 'bg-yellow-50 dark:bg-yellow-900/30 border-yellow-200 dark:border-yellow-700 text-yellow-900 dark:text-yellow-300'
    };
    const colorClass = colorMap[color] || colorMap['blue'];
    
    return (
    <div className={`${colorClass} rounded-lg p-4 transition-colors`}>
      <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-3">{title}</h3>
      <div className="flex gap-2 mb-3">
        <input
          type="text"
          value={value}
          onChange={(e) => setter(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddItem(field, value, setter))}
          className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg text-sm transition-colors"
          placeholder={`Agregar ${title.toLowerCase()}...`}
        />
        <button
          type="button"
          onClick={() => handleAddItem(field, value, setter)}
          className={`px-3 py-2 text-white rounded-lg transition-colors ${color === 'blue' ? 'bg-blue-500 hover:bg-blue-600 dark:bg-blue-600 dark:hover:bg-blue-700' : color === 'green' ? 'bg-green-500 hover:bg-green-600 dark:bg-green-600 dark:hover:bg-green-700' : color === 'purple' ? 'bg-purple-500 hover:bg-purple-600 dark:bg-purple-600 dark:hover:bg-purple-700' : 'bg-yellow-500 hover:bg-yellow-600 dark:bg-yellow-600 dark:hover:bg-yellow-700'}`}
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {formData[field].map((item, index) => (
          <span key={index} className="flex items-center bg-white dark:bg-slate-700 px-3 py-1 rounded-full border dark:border-slate-600 text-sm dark:text-slate-300 transition-colors">
            {item}
            <button type="button" onClick={() => handleRemoveItem(field, index)} className="ml-2 text-red-500 dark:text-red-400">
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
      </div>
    </div>
  );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl dark:shadow-slate-900/50 w-full max-w-3xl max-h-[90vh] overflow-y-auto transition-colors">
        <div className="sticky top-0 bg-white dark:bg-slate-800 border-b dark:border-slate-700 px-6 py-4 flex items-center justify-between transition-colors">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            {process ? 'Editar Proceso' : 'Nuevo Proceso'}
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
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1 transition-colors">Código *</label>
                <input
                  type="text"
                  name="code"
                  value={formData.code}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg transition-colors"
                  placeholder="Ej: OPE-001"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1 transition-colors">Tipo *</label>
                <select
                  name="process_type"
                  value={formData.process_type}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg transition-colors"
                >
                  {PROCESS_TYPES.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1 transition-colors">Nombre *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg transition-colors"
                  placeholder="Nombre del proceso"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1 transition-colors">Responsable *</label>
                <input
                  type="text"
                  name="owner"
                  value={formData.owner}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg transition-colors"
                  placeholder="Dueño del proceso"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1 transition-colors">Documentado en</label>
                <input
                  type="text"
                  name="documented_in"
                  value={formData.documented_in}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg transition-colors"
                  placeholder="Referencia del documento"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1 transition-colors">Objetivo</label>
                <textarea
                  name="objective"
                  value={formData.objective}
                  onChange={handleChange}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg transition-colors"
                  placeholder="Objetivo del proceso..."
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1 transition-colors">Descripción</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg transition-colors"
                  placeholder="Descripción del proceso..."
                />
              </div>
            </div>
          </div>

          {/* Entradas y Salidas */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {renderListSection('Entradas', 'inputs', newInput, setNewInput, 'blue')}
            {renderListSection('Salidas', 'outputs', newOutput, setNewOutput, 'green')}
          </div>

          {/* Recursos y KPIs */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {renderListSection('Recursos', 'resources', newResource, setNewResource, 'purple')}
            {renderListSection('KPIs', 'kpis', newKpi, setNewKpi, 'yellow')}
          </div>

          {/* Estado */}
          <div className="flex items-center">
            <input
              type="checkbox"
              name="is_active"
              checked={formData.is_active}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 border-gray-300 dark:border-slate-600 dark:bg-slate-700 rounded transition-colors"
            />
            <label className="ml-2 text-sm text-gray-700 dark:text-slate-300 transition-colors">Proceso Activo</label>
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
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 disabled:bg-blue-300 dark:disabled:bg-blue-900/30 transition-colors"
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

export default ProcessForm;
