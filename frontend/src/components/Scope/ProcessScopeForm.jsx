import React, { useState, useEffect } from 'react';
import { X, Save, Plus } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';
import { showAlert } from '../../services/dialogs';

const ProcessScopeForm = ({ process, scopeId, onSave, onClose }) => {
  const { t } = useI18n();
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
    { value: 'strategic', label: t('processScopeForm.processTypes.strategic') },
    { value: 'operational', label: t('processScopeForm.processTypes.operational') },
    { value: 'support', label: t('processScopeForm.processTypes.support') }
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
      await showAlert(t('processScopeForm.messages.nameRequired'), { icon: 'warning' });
      return;
    }
    setSaving(true);
    try {
      await onSave(formData);
    } catch (error) {
      console.error('Error saving process scope:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-gray-900/75 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-all duration-300">
      <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-md rounded-lg shadow-2xl dark:shadow-slate-900/70 w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-white/20 dark:border-slate-700/30 transition-all duration-300">
        <div className="sticky top-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-md border-b border-slate-200/50 dark:border-slate-700/50 px-6 py-4 flex items-center justify-between transition-all duration-300">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            {process ? t('processScopeForm.titleEdit') : t('processScopeForm.titleCreate')}
          </h2>
          <button onClick={onClose} className="text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-300 transition-colors">
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Información Básica */}
          <div className="bg-gray-50/70 dark:bg-slate-700/70 backdrop-blur-md rounded-lg p-4 border border-gray-100/50 dark:border-slate-600/50 transition-all duration-300">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">{t('processScopeForm.sections.processInfo')}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  {t('processScopeForm.fields.processNameRequired')}
                </label>
                <input
                  type="text"
                  name="process_name"
                  value={formData.process_name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder={t('processScopeForm.placeholders.processName')}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  {t('processScopeForm.fields.processCode')}
                </label>
                <input
                  type="text"
                  name="process_code"
                  value={formData.process_code}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder={t('processScopeForm.placeholders.processCode')}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  {t('processScopeForm.fields.processTypeRequired')}
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
                  {t('processScopeForm.fields.owner')}
                </label>
                <input
                  type="text"
                  name="owner"
                  value={formData.owner}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder={t('processScopeForm.placeholders.owner')}
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  {t('processScopeForm.fields.description')}
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder={t('processScopeForm.placeholders.description')}
                />
              </div>
            </div>
          </div>

          {/* Entradas */}
          <div className="bg-blue-50/70 dark:bg-blue-900/20 backdrop-blur-md rounded-lg p-4 border border-blue-100/50 dark:border-blue-800/50 transition-all duration-300">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">{t('processScopeForm.sections.inputs')}</h3>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newInput}
                onChange={(e) => setNewInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddItem('inputs', newInput, setNewInput))}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white transition-colors"
                placeholder={t('processScopeForm.placeholders.addInput')}
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
          <div className="bg-green-50/70 dark:bg-green-900/20 backdrop-blur-md rounded-lg p-4 border border-green-100/50 dark:border-green-800/50 transition-all duration-300">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">{t('processScopeForm.sections.outputs')}</h3>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newOutput}
                onChange={(e) => setNewOutput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddItem('outputs', newOutput, setNewOutput))}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white transition-colors"
                placeholder={t('processScopeForm.placeholders.addOutput')}
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
          <div className="bg-purple-50/70 dark:bg-purple-900/20 backdrop-blur-md rounded-lg p-4 border border-purple-100/50 dark:border-purple-800/50 transition-all duration-300">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">{t('processScopeForm.sections.kpis')}</h3>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newKpi}
                onChange={(e) => setNewKpi(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddItem('kpis', newKpi, setNewKpi))}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white transition-colors"
                placeholder={t('processScopeForm.placeholders.addKpi')}
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
          <div className="bg-yellow-50/70 dark:bg-yellow-900/20 backdrop-blur-md rounded-lg p-4 border border-yellow-100/50 dark:border-yellow-800/50 transition-all duration-300">
            <div className="flex items-center mb-3">
              <input
                type="checkbox"
                name="is_included"
                checked={formData.is_included}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 dark:text-blue-500 border-gray-300 dark:border-slate-600 dark:bg-slate-700 rounded transition-colors"
              />
              <label className="ml-2 text-sm font-medium text-gray-700 dark:text-slate-300">
                {t('processScopeForm.fields.includedInScope')}
              </label>
            </div>
            {!formData.is_included && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  {t('processScopeForm.fields.exclusionReason')}
                </label>
                <textarea
                  name="exclusion_reason"
                  value={formData.exclusion_reason}
                  onChange={handleChange}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white transition-colors"
                  placeholder={t('processScopeForm.placeholders.exclusionReason')}
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
              {t('common.buttons.cancel')}
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 disabled:bg-blue-300 dark:disabled:bg-blue-900/30 transition-colors"
            >
              <Save className="mr-2 h-4 w-4" />
              {saving ? t('common.messages.saving') : t('common.buttons.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProcessScopeForm;