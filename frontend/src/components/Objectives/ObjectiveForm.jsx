import React, { useState, useEffect } from 'react';

const ObjectiveForm = ({ objective, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    objective_description: '',
    indicator_name: '',
    measurement_unit: '',
    baseline_value: '',
    target_value: '',
    current_value: '',
    measurement_frequency: 'mensual',
    responsible: '',
    deadline: '',
    status: 'active',
    iso_clause: '6.2',
    process_id: '',
    source_module: 'MANUAL',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const frequencyOptions = [
    { value: 'diario', label: 'Diario' },
    { value: 'semanal', label: 'Semanal' },
    { value: 'quincenal', label: 'Quincenal' },
    { value: 'mensual', label: 'Mensual' },
    { value: 'bimestral', label: 'Bimestral' },
    { value: 'trimestral', label: 'Trimestral' },
    { value: 'semestral', label: 'Semestral' },
    { value: 'anual', label: 'Anual' },
  ];

  const statusOptions = [
    { value: 'active', label: 'Activo' },
    { value: 'in_progress', label: 'En Progreso' },
    { value: 'achieved', label: 'Logrado' },
    { value: 'delayed', label: 'Retrasado' },
    { value: 'cancelled', label: 'Cancelado' },
  ];

  const unitSuggestions = ['%', 'unidades', 'horas', 'días', 'puntos', 'USD', 'clientes', 'productos', 'defectos'];

  useEffect(() => {
    if (objective) {
      setFormData({
        objective_description: objective.objective_description || '',
        indicator_name: objective.indicator_name || '',
        measurement_unit: objective.measurement_unit || '',
        baseline_value: objective.baseline_value || '',
        target_value: objective.target_value || '',
        current_value: objective.current_value || '',
        measurement_frequency: objective.measurement_frequency || 'mensual',
        responsible: objective.responsible || '',
        deadline: objective.deadline ? objective.deadline.split('T')[0] : '',
        status: objective.status || 'active',
        iso_clause: objective.iso_clause || '6.2',
        process_id: objective.process_id || '',
        source_module: objective.source_module || 'MANUAL',
      });
    }
  }, [objective]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: null }));
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.indicator_name.trim()) newErrors.indicator_name = 'El nombre del indicador es requerido';
    if (!formData.objective_description.trim()) newErrors.objective_description = 'La descripción es requerida';
    if (!formData.measurement_unit.trim()) newErrors.measurement_unit = 'La unidad de medida es requerida';
    if (formData.baseline_value === '') newErrors.baseline_value = 'El valor base es requerido';
    if (formData.target_value === '') newErrors.target_value = 'El valor meta es requerido';
    if (!formData.responsible.trim()) newErrors.responsible = 'El responsable es requerido';
    if (!formData.deadline) newErrors.deadline = 'La fecha límite es requerida';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    
    setLoading(true);
    try {
      const dataToSend = {
        ...formData,
        baseline_value: parseFloat(formData.baseline_value),
        target_value: parseFloat(formData.target_value),
        current_value: formData.current_value ? parseFloat(formData.current_value) : null,
      };
      await onSubmit(dataToSend);
    } catch (err) {
      setErrors({ submit: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-gray-900/75 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-all duration-300">
      <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-md rounded-xl shadow-2xl dark:shadow-slate-900/70 max-w-3xl w-full max-h-[90vh] overflow-hidden border border-white/20 dark:border-slate-700/30 transition-all duration-300">
        <div className="px-6 py-4 border-b border-slate-200/50 dark:border-slate-700/50 flex justify-between items-center bg-white/80 dark:bg-slate-800/80 backdrop-blur-md transition-all duration-300">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {objective ? 'Editar Objetivo' : 'Nuevo Objetivo de Calidad'}
          </h2>
          <button onClick={onCancel} className="text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-400 transition-colors">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="px-6 py-4 space-y-6">
            {errors.submit && (
              <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg transition-colors">{errors.submit}</div>
            )}

            {/* Indicator Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                Nombre del Indicador <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="indicator_name"
                value={formData.indicator_name}
                onChange={handleChange}
                className={`w-full rounded-lg shadow-sm dark:bg-slate-700 dark:text-white dark:focus:ring-blue-400 focus:ring-blue-500 focus:border-blue-500 transition-colors ${errors.indicator_name ? 'border-red-300 dark:border-red-800' : 'border-gray-300 dark:border-slate-600'}`}
                placeholder="Ej: Índice de Satisfacción del Cliente"
              />
              {errors.indicator_name && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.indicator_name}</p>}
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                Descripción del Objetivo <span className="text-red-500">*</span>
              </label>
              <textarea
                name="objective_description"
                value={formData.objective_description}
                onChange={handleChange}
                rows={3}
                className={`w-full rounded-lg shadow-sm dark:bg-slate-700 dark:text-white dark:focus:ring-blue-400 focus:ring-blue-500 focus:border-blue-500 transition-colors ${errors.objective_description ? 'border-red-300 dark:border-red-800' : 'border-gray-300 dark:border-slate-600'}`}
                placeholder="Describa el objetivo de calidad..."
              />
              {errors.objective_description && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.objective_description}</p>}
            </div>

            {/* Measurement Values */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Línea Base <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  name="baseline_value"
                  value={formData.baseline_value}
                  onChange={handleChange}
                  className={`w-full rounded-lg shadow-sm dark:bg-slate-700 dark:text-white dark:focus:ring-blue-400 focus:ring-blue-500 focus:border-blue-500 transition-colors ${errors.baseline_value ? 'border-red-300 dark:border-red-800' : 'border-gray-300 dark:border-slate-600'}`}
                  placeholder="0"
                />
                {errors.baseline_value && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.baseline_value}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Meta <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  name="target_value"
                  value={formData.target_value}
                  onChange={handleChange}
                  className={`w-full rounded-lg shadow-sm dark:bg-slate-700 dark:text-white dark:focus:ring-blue-400 focus:ring-blue-500 focus:border-blue-500 transition-colors ${errors.target_value ? 'border-red-300 dark:border-red-800' : 'border-gray-300 dark:border-slate-600'}`}
                  placeholder="100"
                />
                {errors.target_value && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.target_value}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">Valor Actual</label>
                <input
                  type="number"
                  step="0.01"
                  name="current_value"
                  value={formData.current_value}
                  onChange={handleChange}
                  className="w-full rounded-lg border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white shadow-sm dark:focus:ring-blue-400 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Unidad <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="measurement_unit"
                  value={formData.measurement_unit}
                  onChange={handleChange}
                  list="unit-suggestions"
                  className={`w-full rounded-lg shadow-sm dark:bg-slate-700 dark:text-white dark:focus:ring-blue-400 focus:ring-blue-500 focus:border-blue-500 transition-colors ${errors.measurement_unit ? 'border-red-300 dark:border-red-800' : 'border-gray-300 dark:border-slate-600'}`}
                  placeholder="%"
                />
                <datalist id="unit-suggestions">
                  {unitSuggestions.map(unit => <option key={unit} value={unit} />)}
                </datalist>
                {errors.measurement_unit && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.measurement_unit}</p>}
              </div>
            </div>

            {/* Frequency and Responsible */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">Frecuencia de Medición</label>
                <select
                  name="measurement_frequency"
                  value={formData.measurement_frequency}
                  onChange={handleChange}
                  className="w-full rounded-lg border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white shadow-sm dark:focus:ring-blue-400 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                >
                  {frequencyOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Responsable <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="responsible"
                  value={formData.responsible}
                  onChange={handleChange}
                  className={`w-full rounded-lg shadow-sm dark:bg-slate-700 dark:text-white dark:focus:ring-blue-400 focus:ring-blue-500 focus:border-blue-500 transition-colors ${errors.responsible ? 'border-red-300 dark:border-red-800' : 'border-gray-300 dark:border-slate-600'}`}
                  placeholder="Nombre del responsable"
                />
                {errors.responsible && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.responsible}</p>}
              </div>
            </div>

            {/* Deadline and Status */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Fecha Límite <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  name="deadline"
                  value={formData.deadline}
                  onChange={handleChange}
                  className={`w-full rounded-lg shadow-sm dark:bg-slate-700 dark:text-white dark:focus:ring-blue-400 focus:ring-blue-500 focus:border-blue-500 transition-colors ${errors.deadline ? 'border-red-300 dark:border-red-800' : 'border-gray-300 dark:border-slate-600'}`}
                />
                {errors.deadline && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.deadline}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">Estado</label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  className="w-full rounded-lg border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white shadow-sm dark:focus:ring-blue-400 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                >
                  {statusOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                </select>
              </div>
            </div>

            {/* Process ID */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">ID de Proceso (opcional)</label>
              <input
                type="text"
                name="process_id"
                value={formData.process_id}
                onChange={handleChange}
                className="w-full rounded-lg border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white shadow-sm dark:focus:ring-blue-400 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                placeholder="Ej: PROC-001"
              />
            </div>
          </div>

          <div className="px-6 py-4 border-t border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-700/50 flex justify-end gap-3 transition-colors">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-600 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 dark:bg-blue-700 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Guardando...' : (objective ? 'Actualizar' : 'Crear')} Objetivo
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ObjectiveForm;
