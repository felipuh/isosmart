import React, { useState, useRef, useEffect } from 'react';
import { 
  Building2, Upload, Save, Mail, Phone, MapPin, Globe, 
  FileText, Camera, Check, AlertCircle, Loader2
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import settingsService from '../../services/settingsService';

const OrganizationSettings = ({ organization: propOrganization, onUpdate }) => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const organization = propOrganization || currentOrganization;
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address: '',
    website: '',
    tax_id: '',
    legal_name: '',
  });
  
  useEffect(() => {
    if (organization) {
      setFormData({
        name: organization.name || '',
        email: organization.email || '',
        phone: organization.phone || '',
        address: organization.address || '',
        website: organization.website || '',
        tax_id: organization.tax_id || '',
        legal_name: organization.legal_name || '',
      });
    }
  }, [organization]);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);
  const [logoPreview, setLogoPreview] = useState(organization?.logo || null);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const fileInputRef = useRef(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setSuccess(false);
    setError(null);
  };

  const handleLogoChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validar tipo de archivo
    if (!file.type.startsWith('image/')) {
      setError(t('settings.organization.messages.invalidImage'));
      return;
    }

    // Preview
    const reader = new FileReader();
    reader.onload = (e) => setLogoPreview(e.target.result);
    reader.readAsDataURL(file);

    // Upload
    try {
      setUploadingLogo(true);
      const result = await settingsService.uploadLogo(organization.id, file);
      onUpdate({ logo: result.logo });
      setSuccess(true);
    } catch (err) {
      setError(t('settings.organization.messages.uploadError'));
      console.error(err);
    } finally {
      setUploadingLogo(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setSaving(true);
      setError(null);
      
      const result = await settingsService.updateOrganization(organization.id, formData);
      onUpdate(result);
      setSuccess(true);
      
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(t('settings.organization.messages.saveError'));
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <div className="p-3 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl shadow-lg shadow-blue-500/25">
          <Building2 className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-white">
            {t('settings.organization.headerTitle')}
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {t('settings.organization.headerSubtitle')}
          </p>
        </div>
      </div>

      {/* Alerts */}
      {success && (
        <div className="mb-6 p-4 bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-800 rounded-xl flex items-center gap-3 animate-fade-in">
          <Check className="w-5 h-5 text-emerald-500" />
          <span className="text-emerald-700 dark:text-emerald-300">{t('common.messages.success')}</span>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700 dark:text-red-300">{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Logo Section */}
        <div className="flex flex-col sm:flex-row items-start gap-6 p-6 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-700/30 dark:to-slate-800/30 rounded-2xl">
          <div className="relative group">
            {logoPreview ? (
              <img 
                src={logoPreview} 
                alt={t('settings.organization.logoAlt')}
                className="w-32 h-32 rounded-2xl object-cover border-4 border-white dark:border-slate-600 shadow-xl"
              />
            ) : (
              <div className="w-32 h-32 rounded-2xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center border-4 border-white dark:border-slate-600 shadow-xl">
                <Building2 className="w-12 h-12 text-white" />
              </div>
            )}
            
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadingLogo}
              className="absolute -bottom-2 -right-2 p-2 bg-white dark:bg-slate-700 rounded-full shadow-lg border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600 transition-colors"
            >
              {uploadingLogo ? (
                <Loader2 className="w-5 h-5 text-indigo-500 animate-spin" />
              ) : (
                <Camera className="w-5 h-5 text-indigo-500" />
              )}
            </button>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleLogoChange}
              className="hidden"
            />
          </div>
          
          <div className="flex-1">
            <h3 className="font-semibold text-slate-800 dark:text-white mb-2">{t('settings.organization.logoTitle')}</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
              {t('settings.organization.logoHelp')}
            </p>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-600 transition-colors flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              {t('settings.organization.changeLogo')}
            </button>
          </div>
        </div>

        {/* Basic Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              {t('settings.organization.fields.organizationNameRequired')}
            </label>
            <div className="relative">
              <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-slate-800 dark:text-white placeholder-slate-400"
                placeholder={t('settings.organization.placeholders.organizationName')}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              {t('settings.organization.fields.legalName')}
            </label>
            <div className="relative">
              <FileText className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                name="legal_name"
                value={formData.legal_name}
                onChange={handleChange}
                className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-slate-800 dark:text-white placeholder-slate-400"
                placeholder={t('settings.organization.placeholders.legalName')}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              {t('settings.organization.fields.taxId')}
            </label>
            <div className="relative">
              <FileText className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                name="tax_id"
                value={formData.tax_id}
                onChange={handleChange}
                className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-slate-800 dark:text-white placeholder-slate-400"
                placeholder={t('settings.organization.placeholders.taxId')}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              {t('settings.organization.fields.website')}
            </label>
            <div className="relative">
              <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="url"
                name="website"
                value={formData.website}
                onChange={handleChange}
                className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-slate-800 dark:text-white placeholder-slate-400"
                placeholder={t('settings.organization.placeholders.website')}
              />
            </div>
          </div>
        </div>

        {/* Contact Info */}
        <div>
          <h3 className="text-lg font-semibold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
            <Mail className="w-5 h-5 text-indigo-500" />
            {t('settings.organization.fields.contactInfo')}
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                {t('settings.organization.fields.contactEmail')}
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-slate-800 dark:text-white placeholder-slate-400"
                  placeholder={t('settings.organization.placeholders.contactEmail')}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                {t('settings.organization.fields.phone')}
              </label>
              <div className="relative">
                <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-slate-800 dark:text-white placeholder-slate-400"
                  placeholder={t('settings.organization.placeholders.phone')}
                />
              </div>
            </div>

            <div className="md:col-span-2 space-y-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                {t('settings.organization.fields.address')}
              </label>
              <div className="relative">
                <MapPin className="absolute left-4 top-4 w-5 h-5 text-slate-400" />
                <textarea
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  rows={3}
                  className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-slate-800 dark:text-white placeholder-slate-400 resize-none"
                  placeholder={t('settings.organization.placeholders.address')}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-end gap-4 pt-6 border-t border-slate-200 dark:border-slate-700">
          <button
            type="button"
            onClick={() => setFormData({
              name: organization?.name || '',
              email: organization?.email || '',
              phone: organization?.phone || '',
              address: organization?.address || '',
              website: organization?.website || '',
              tax_id: organization?.tax_id || '',
              legal_name: organization?.legal_name || '',
            })}
            className="px-6 py-3 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors font-medium"
          >
            {t('settings.organization.actions.cancel')}
          </button>
          
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white rounded-xl font-medium shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                {t('settings.organization.actions.saving')}
              </>
            ) : (
              <>
                <Save className="w-5 h-5" />
                {t('settings.organization.actions.saveChanges')}
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default OrganizationSettings;