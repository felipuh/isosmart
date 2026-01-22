import React, { useState, useEffect } from 'react';
import { X, Save, Plus, Trash2 } from 'lucide-react';

const StakeholderForm = ({ stakeholder, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    name: '',
    stakeholder_type: 'cliente',
    organization: '',
    contact_person: '',
    email: '',
    phone: '',
    power: 'medio',
    interest: 'medio',
    satisfaction_score: 5.0,
    communication_frequency: 'mensual',
    preferred_channel: '',
    expectations: [],
    requirements: [],
    notes: '',
    is_active: true
  });

  const [newExpectation, setNewExpectation] = useState('');
  const [newRequirement, setNewRequirement] = useState('');
  const [saving, setSaving] = useState(false);

  const STAKEHOLDER_TYPES = [
    { value: 'cliente', label: 'Cliente' },
    { value: 'proveedor', label: 'Proveedor' },
    { value: 'empleado', label: 'Empleado' },
    { value: 'accionista', label: 'Accionista' },
    { value: 'regulador', label: 'Entidad Reguladora' },
    { value: 'comunidad', label: 'Comunidad Local' },
    { value: 'socio', label: 'Socio Estratégico' },
    { value: 'competidor', label: 'Competidor' },
    { value: 'otro', label: 'Otro' }
  ];

  const POWER_LEVELS = [
    { value: 'bajo', label: 'Bajo' },
    { value: 'medio', label: 'Medio' },
    { value: 'alto', label: 'Alto' }
  ];

  const INTEREST_LEVELS = [
    { value: 'bajo', label: 'Bajo' },
    { value: 'medio', label: 'Medio' },
    { value: 'alto', label: 'Alto' }
  ];

  const COMMUNICATION_FREQUENCY = [
    { value: 'diaria', label: 'Diaria' },
    { value: 'semanal', label: 'Semanal' },
    { value: 'quincenal', label: 'Quincenal' },
    { value: 'mensual', label: 'Mensual' },
    { value: 'trimestral', label: 'Trimestral' },
    { value: 'semestral', label: 'Semestral' },
    { value: 'anual', label: 'Anual' }
  ];

  useEffect(() => {
    if (stakeholder) {
      setFormData({
        name: stakeholder.name || '',
        stakeholder_type: stakeholder.stakeholder_type || 'cliente',
        organization: stakeholder.organization || '',
        contact_person: stakeholder.contact_person || '',
        email: stakeholder.email || '',
        phone: stakeholder.phone || '',
        power: stakeholder.power || 'medio',
        interest: stakeholder.interest || 'medio',
        satisfaction_score: stakeholder.satisfaction_score || 5.0,
        communication_frequency: stakeholder.communication_frequency || 'mensual',
        preferred_channel: stakeholder.preferred_channel || '',
        expectations: stakeholder.expectations || [],
        requirements: stakeholder.requirements || [],
        notes: stakeholder.notes || '',
        is_active: stakeholder.is_active !== undefined ? stakeholder.is_active : true
      });
    }
  }, [stakeholder]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleAddExpectation = () => {
    if (newExpectation.trim()) {
      setFormData(prev => ({
        ...prev,
        expectations: [...prev.expectations, newExpectation.trim()]
      }));
      setNewExpectation('');
    }
  };

  const handleRemoveExpectation = (index) => {
    setFormData(prev => ({
      ...prev,
      expectations: prev.expectations.filter((_, i) => i !== index)
    }));
  };

  const handleAddRequirement = () => {
    if (newRequirement.trim()) {
      setFormData(prev => ({
        ...prev,
        requirements: [...prev.requirements, newRequirement.trim()]
      }));
      setNewRequirement('');
    }
  };

  const handleRemoveRequirement = (index) => {
    setFormData(prev => ({
      ...prev,
      requirements: prev.requirements.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      alert('El nombre es requerido');
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
    <div className="fixed inset-0 bg-black/50 dark:bg-gray-900/75 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-all duration-300">
      <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-md rounded-lg shadow-2xl dark:shadow-slate-900/70 w-full max-w-3xl max-h-[90vh] overflow-hidden border border-white/20 dark:border-slate-700/30 transition-all duration-300">
        <div className="sticky top-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-md border-b border-slate-200/50 dark:border-slate-700/50 px-6 py-4 flex items-center justify-between transition-all duration-300">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            {stakeholder ? 'Editar Stakeholder' : 'Nuevo Stakeholder'}
          </h2>
          <button onClick={onClose} className="text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-300 transition-colors">
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Información Básica */}
          <div className="bg-gray-50/70 dark:bg-slate-700/70 backdrop-blur-md rounded-lg p-4 border border-gray-100/50 dark:border-slate-600/50 transition-all duration-300">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Información Básica</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Nombre *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-colors"
                  placeholder="Nombre del stakeholder"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Tipo de Stakeholder *
                </label>
                <select
                  name="stakeholder_type"
                  value={formData.stakeholder_type}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-colors"
                >
                  {STAKEHOLDER_TYPES.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Organización
                </label>
                <input
                  type="text"
                  name="organization"
                  value={formData.organization}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-colors"
                  placeholder="Empresa u organización"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Persona de Contacto
                </label>
                <input
                  type="text"
                  name="contact_person"
                  value={formData.contact_person}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-colors"
                  placeholder="Nombre del contacto"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-colors"
                  placeholder="correo@ejemplo.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Teléfono
                </label>
                <input
                  type="text"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-colors"
                  placeholder="+506 8888-8888"
                />
              </div>
            </div>
          </div>

          {/* Análisis de Poder e Interés */}
          <div className="bg-blue-50/70 dark:bg-blue-900/20 backdrop-blur-md rounded-lg p-4 border border-blue-100/50 dark:border-blue-800/50 transition-all duration-300">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Análisis de Poder e Interés</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Nivel de Poder
                </label>
                <select
                  name="power"
                  value={formData.power}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-colors"
                >
                  {POWER_LEVELS.map(level => (
                    <option key={level.value} value={level.value}>{level.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Nivel de Interés
                </label>
                <select
                  name="interest"
                  value={formData.interest}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-colors"
                >
                  {INTEREST_LEVELS.map(level => (
                    <option key={level.value} value={level.value}>{level.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Satisfacción (0-10)
                </label>
                <input
                  type="number"
                  name="satisfaction_score"
                  value={formData.satisfaction_score}
                  onChange={handleChange}
                  min="0"
                  max="10"
                  step="0.5"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-colors"
                />
              </div>
            </div>
          </div>

          {/* Comunicación */}
          <div className="bg-green-50/70 dark:bg-green-900/20 backdrop-blur-md rounded-lg p-4 border border-green-100/50 dark:border-green-800/50 transition-all duration-300">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Estrategia de Comunicación</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Frecuencia de Comunicación
                </label>
                <select
                  name="communication_frequency"
                  value={formData.communication_frequency}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-colors"
                >
                  {COMMUNICATION_FREQUENCY.map(freq => (
                    <option key={freq.value} value={freq.value}>{freq.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Canal Preferido
                </label>
                <input
                  type="text"
                  name="preferred_channel"
                  value={formData.preferred_channel}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-colors"
                  placeholder="Email, Teléfono, Reunión, etc."
                />
              </div>
            </div>
          </div>

          {/* Expectativas */}
          <div className="bg-yellow-50/70 dark:bg-yellow-900/20 backdrop-blur-md rounded-lg p-4 border border-yellow-100/50 dark:border-yellow-800/50 transition-all duration-300">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Expectativas</h3>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newExpectation}
                onChange={(e) => setNewExpectation(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddExpectation())}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-colors"
                placeholder="Agregar expectativa..."
              />
              <button
                type="button"
                onClick={handleAddExpectation}
                className="px-3 py-2 bg-yellow-500 dark:bg-yellow-600 text-white rounded-lg hover:bg-yellow-600 dark:hover:bg-yellow-700 transition-colors"
              >
                <Plus className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-2">
              {formData.expectations.map((exp, index) => (
                <div key={index} className="flex items-center justify-between bg-white dark:bg-slate-700 p-2 rounded border border-gray-200 dark:border-slate-600 transition-colors">
                  <span className="text-sm text-gray-900 dark:text-white">{exp}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveExpectation(index)}
                    className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Requisitos */}
          <div className="bg-purple-50/70 dark:bg-purple-900/20 backdrop-blur-md rounded-lg p-4 border border-purple-100/50 dark:border-purple-800/50 transition-all duration-300">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Requisitos</h3>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newRequirement}
                onChange={(e) => setNewRequirement(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddRequirement())}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-colors"
                placeholder="Agregar requisito..."
              />
              <button
                type="button"
                onClick={handleAddRequirement}
                className="px-3 py-2 bg-purple-500 dark:bg-purple-600 text-white rounded-lg hover:bg-purple-600 dark:hover:bg-purple-700 transition-colors"
              >
                <Plus className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-2">
              {formData.requirements.map((req, index) => (
                <div key={index} className="flex items-center justify-between bg-white dark:bg-slate-700 p-2 rounded border border-gray-200 dark:border-slate-600 transition-colors">
                  <span className="text-sm text-gray-900 dark:text-white">{req}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveRequirement(index)}
                    className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Notas */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
              Notas Adicionales
            </label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-colors"
              placeholder="Observaciones o notas relevantes..."
            />
          </div>

          {/* Estado Activo */}
          <div className="flex items-center">
            <input
              type="checkbox"
              name="is_active"
              checked={formData.is_active}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 dark:text-blue-500 border-gray-300 dark:border-slate-600 rounded dark:bg-slate-700 focus:ring-blue-500 dark:focus:ring-blue-400"
            />
            <label className="ml-2 text-sm text-gray-700 dark:text-slate-300">
              Stakeholder Activo
            </label>
          </div>

          {/* Botones */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-slate-700 transition-colors">
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
              className="flex items-center px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 disabled:bg-blue-300 dark:disabled:bg-blue-900 transition-colors"
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

export default StakeholderForm;
