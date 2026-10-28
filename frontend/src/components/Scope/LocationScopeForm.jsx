import React, { useState, useEffect } from 'react';
import { X, Save, Plus } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';
import { showAlert } from '../../services/dialogs';

const LocationScopeForm = ({ location, scopeId, onSave, onClose }) => {
  const { t } = useI18n();
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
    { value: 'headquarters', label: t('locationScopeForm.locationTypes.headquarters') },
    { value: 'branch', label: t('locationScopeForm.locationTypes.branch') },
    { value: 'warehouse', label: t('locationScopeForm.locationTypes.warehouse') },
    { value: 'plant', label: t('locationScopeForm.locationTypes.plant') },
    { value: 'office', label: t('locationScopeForm.locationTypes.office') },
    { value: 'remote', label: t('locationScopeForm.locationTypes.remote') }
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
      await showAlert(t('locationScopeForm.messages.locationNameRequired'), { icon: 'warning' });
      return;
    }
    if (!formData.city.trim()) {
      await showAlert(t('locationScopeForm.messages.cityRequired'), { icon: 'warning' });
      return;
    }
    setSaving(true);
    try {
      await onSave(formData);
    } catch (error) {
      console.error('Error saving location scope:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-gray-900/75 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-all duration-300">
      <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-md rounded-lg shadow-2xl dark:shadow-slate-900/70 w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-white/20 dark:border-slate-700/30 transition-all duration-300">
        <div className="sticky top-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-md border-b border-slate-200/50 dark:border-slate-700/50 px-6 py-4 flex items-center justify-between transition-all duration-300">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            {location ? t('locationScopeForm.titleEdit') : t('locationScopeForm.titleCreate')}
          </h2>
          <button onClick={onClose} className="text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-300 transition-colors">
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Información Básica */}
          <div className="bg-gray-50/70 dark:bg-slate-700/70 backdrop-blur-md rounded-lg p-4 border border-gray-100/50 dark:border-slate-600/50 transition-all duration-300">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">{t('locationScopeForm.sections.locationInfo')}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  {t('locationScopeForm.fields.locationNameRequired')}
                </label>
                <input
                  type="text"
                  name="location_name"
                  value={formData.location_name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder={t('locationScopeForm.placeholders.locationName')}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  {t('locationScopeForm.fields.locationTypeRequired')}
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
                  {t('locationScopeForm.fields.employeeCount')}
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
                  {t('locationScopeForm.fields.countryRequired')}
                </label>
                <input
                  type="text"
                  name="country"
                  value={formData.country}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder={t('locationScopeForm.placeholders.country')}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  {t('locationScopeForm.fields.cityRequired')}
                </label>
                <input
                  type="text"
                  name="city"
                  value={formData.city}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder={t('locationScopeForm.placeholders.city')}
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  {t('locationScopeForm.fields.fullAddress')}
                </label>
                <textarea
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder={t('locationScopeForm.placeholders.address')}
                />
              </div>
            </div>
          </div>

          {/* Actividades */}
          <div className="bg-blue-50/70 dark:bg-blue-900/20 backdrop-blur-md rounded-lg p-4 border border-blue-100/50 dark:border-blue-800/50 transition-all duration-300">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">{t('locationScopeForm.sections.activitiesPerformed')}</h3>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newActivity}
                onChange={(e) => setNewActivity(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddActivity())}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-white transition-colors"
                placeholder={t('locationScopeForm.placeholders.addActivity')}
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
              {t('locationScopeForm.fields.includedInScope')}
            </label>
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

export default LocationScopeForm;