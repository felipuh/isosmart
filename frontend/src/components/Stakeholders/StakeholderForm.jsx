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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">
            {stakeholder ? 'Editar Stakeholder' : 'Nuevo Stakeholder'}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Información Básica */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Información Básica</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Nombre del stakeholder"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Stakeholder *
                </label>
                <select
                  name="stakeholder_type"
                  value={formData.stakeholder_type}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {STAKEHOLDER_TYPES.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Organización
                </label>
                <input
                  type="text"
                  name="organization"
                  value={formData.organization}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Empresa u organización"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Persona de Contacto
                </label>
                <input
                  type="text"
                  name="contact_person"
                  value={formData.contact_person}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Nombre del contacto"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="correo@ejemplo.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Teléfono
                </label>
                <input
                  type="text"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="+506 8888-8888"
                />
              </div>
            </div>
          </div>

          {/* Análisis de Poder e Interés */}
          <div className="bg-blue-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Análisis de Poder e Interés</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nivel de Poder
                </label>
                <select
                  name="power"
                  value={formData.power}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {POWER_LEVELS.map(level => (
                    <option key={level.value} value={level.value}>{level.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nivel de Interés
                </label>
                <select
                  name="interest"
                  value={formData.interest}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {INTEREST_LEVELS.map(level => (
                    <option key={level.value} value={level.value}>{level.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Comunicación */}
          <div className="bg-green-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Estrategia de Comunicación</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Frecuencia de Comunicación
                </label>
                <select
                  name="communication_frequency"
                  value={formData.communication_frequency}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {COMMUNICATION_FREQUENCY.map(freq => (
                    <option key={freq.value} value={freq.value}>{freq.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Canal Preferido
                </label>
                <input
                  type="text"
                  name="preferred_channel"
                  value={formData.preferred_channel}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Email, Teléfono, Reunión, etc."
                />
              </div>
            </div>
          </div>

          {/* Expectativas */}
          <div className="bg-yellow-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Expectativas</h3>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newExpectation}
                onChange={(e) => setNewExpectation(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddExpectation())}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Agregar expectativa..."
              />
              <button
                type="button"
                onClick={handleAddExpectation}
                className="px-3 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600"
              >
                <Plus className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-2">
              {formData.expectations.map((exp, index) => (
                <div key={index} className="flex items-center justify-between bg-white p-2 rounded border">
                  <span className="text-sm">{exp}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveExpectation(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Requisitos */}
          <div className="bg-purple-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Requisitos</h3>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newRequirement}
                onChange={(e) => setNewRequirement(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddRequirement())}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Agregar requisito..."
              />
              <button
                type="button"
                onClick={handleAddRequirement}
                className="px-3 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
              >
                <Plus className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-2">
              {formData.requirements.map((req, index) => (
                <div key={index} className="flex items-center justify-between bg-white p-2 rounded border">
                  <span className="text-sm">{req}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveRequirement(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Notas */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notas Adicionales
            </label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label className="ml-2 text-sm text-gray-700">
              Stakeholder Activo
            </label>
          </div>

          {/* Botones */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300"
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
