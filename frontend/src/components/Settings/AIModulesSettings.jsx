import React, { useState } from 'react';
import { 
  Brain, Sparkles, Users, Target, GitBranch, Zap, 
  Clock, Save, Loader2, Check, AlertCircle, Info,
  ToggleLeft, ToggleRight, Settings2
} from 'lucide-react';
import settingsService from '../../services/settingsService';
import { useI18n } from '../../context/I18nContext';

const AIModulesSettings = ({ settings, onUpdate, organizationId }) => {
  const { t } = useI18n();
  const [formData, setFormData] = useState({
    ai_sca_enabled: settings?.ai_sca_enabled ?? true,
    ai_sie_enabled: settings?.ai_sie_enabled ?? true,
    ai_asb_enabled: settings?.ai_asb_enabled ?? true,
    ai_spm_enabled: settings?.ai_spm_enabled ?? true,
    ai_auto_analysis: settings?.ai_auto_analysis ?? false,
    ai_analysis_frequency: settings?.ai_analysis_frequency ?? 'weekly',
  });
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const modules = [
    {
      key: 'ai_sca_enabled',
      name: t('settings.aiModules.modules.sca.name'),
      description: t('settings.aiModules.modules.sca.description'),
      icon: Sparkles,
      color: 'from-blue-500 to-cyan-500',
      features: [
        t('settings.aiModules.modules.sca.features.swot'),
        t('settings.aiModules.modules.sca.features.risks'),
        t('settings.aiModules.modules.sca.features.trends'),
      ],
      clause: '4.1'
    },
    {
      key: 'ai_sie_enabled',
      name: t('settings.aiModules.modules.sie.name'),
      description: t('settings.aiModules.modules.sie.description'),
      icon: Users,
      color: 'from-violet-500 to-purple-500',
      features: [
        t('settings.aiModules.modules.sie.features.matrix'),
        t('settings.aiModules.modules.sie.features.expectations'),
        t('settings.aiModules.modules.sie.features.alerts'),
      ],
      clause: '4.2'
    },
    {
      key: 'ai_asb_enabled',
      name: t('settings.aiModules.modules.asb.name'),
      description: t('settings.aiModules.modules.asb.description'),
      icon: Target,
      color: 'from-emerald-500 to-teal-500',
      features: [
        t('settings.aiModules.modules.asb.features.scope'),
        t('settings.aiModules.modules.asb.features.requirements'),
        t('settings.aiModules.modules.asb.features.exclusions'),
      ],
      clause: '4.3'
    },
    {
      key: 'ai_spm_enabled',
      name: t('settings.aiModules.modules.spm.name'),
      description: t('settings.aiModules.modules.spm.description'),
      icon: GitBranch,
      color: 'from-amber-500 to-orange-500',
      features: [
        t('settings.aiModules.modules.spm.features.mapping'),
        t('settings.aiModules.modules.spm.features.kpis'),
        t('settings.aiModules.modules.spm.features.interactions'),
      ],
      clause: '4.4'
    },
  ];

  const frequencyOptions = [
    {
      value: 'daily',
      label: t('settings.aiModules.frequency.daily.label'),
      description: t('settings.aiModules.frequency.daily.description'),
    },
    {
      value: 'weekly',
      label: t('settings.aiModules.frequency.weekly.label'),
      description: t('settings.aiModules.frequency.weekly.description'),
    },
    {
      value: 'monthly',
      label: t('settings.aiModules.frequency.monthly.label'),
      description: t('settings.aiModules.frequency.monthly.description'),
    },
    {
      value: 'manual',
      label: t('settings.aiModules.frequency.manual.label'),
      description: t('settings.aiModules.frequency.manual.description'),
    },
  ];

  const handleToggle = (key) => {
    setFormData(prev => ({ ...prev, [key]: !prev[key] }));
    setSuccess(false);
  };

  const handleSubmit = async () => {
    try {
      setSaving(true);
      setError(null);
      
      const result = await settingsService.updateAIModules(formData, organizationId);
      onUpdate(result);
      setSuccess(true);
      
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(t('settings.aiModules.messages.errorSaving'));
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const enabledCount = [
    formData.ai_sca_enabled,
    formData.ai_sie_enabled,
    formData.ai_asb_enabled,
    formData.ai_spm_enabled
  ].filter(Boolean).length;

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/25">
          <Brain className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-white">
            {t('settings.aiModules.title')}
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {t('settings.aiModules.subtitle')}
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

      {/* Status Banner */}
      <div className="mb-8 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-xl border border-indigo-100 dark:border-indigo-800/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm">
              <Zap className="w-5 h-5 text-indigo-500" />
            </div>
            <div>
              <p className="font-semibold text-slate-800 dark:text-white">
                {t('settings.aiModules.banner.activeModules').replace('{count}', enabledCount)}
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {t('settings.aiModules.banner.clauseCoverage').replace('{percentage}', Math.round((enabledCount / 4) * 100))}
              </p>
            </div>
          </div>
          <div className="flex gap-1">
            {modules.map((m, i) => (
              <div 
                key={i}
                className={`w-3 h-3 rounded-full ${formData[m.key] ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'}`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* AI Modules */}
      <div className="space-y-4 mb-8">
        {modules.map((module) => {
          const Icon = module.icon;
          const isEnabled = formData[module.key];
          
          return (
            <div 
              key={module.key}
              className={`
                p-5 rounded-2xl border-2 transition-all duration-300
                ${isEnabled 
                  ? 'bg-gradient-to-br from-slate-50 to-white dark:from-slate-700/50 dark:to-slate-800/50 border-indigo-200 dark:border-indigo-700 shadow-lg' 
                  : 'bg-slate-50 dark:bg-slate-800/30 border-slate-200 dark:border-slate-700 opacity-75'
                }
              `}
            >
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-xl bg-gradient-to-br ${module.color} shadow-lg`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-slate-800 dark:text-white">
                          {module.name}
                        </h3>
                        <span className="px-2 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-xs font-medium text-slate-600 dark:text-slate-300">
                          ISO {module.clause}
                        </span>
                      </div>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                        {module.description}
                      </p>
                    </div>
                    
                    <button
                      onClick={() => handleToggle(module.key)}
                      className="flex-shrink-0 ml-4"
                    >
                      {isEnabled ? (
                        <ToggleRight className="w-12 h-7 text-indigo-500" />
                      ) : (
                        <ToggleLeft className="w-12 h-7 text-slate-400" />
                      )}
                    </button>
                  </div>
                  
                  {isEnabled && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {module.features.map((feature, i) => (
                        <span 
                          key={i}
                          className="px-3 py-1 bg-white dark:bg-slate-700 rounded-full text-xs font-medium text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-600"
                        >
                          {feature}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Automation Settings */}
      <div className="p-6 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-700/30 dark:to-slate-800/30 rounded-2xl border border-slate-200 dark:border-slate-700 mb-8">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <Settings2 className="w-5 h-5 text-indigo-500" />
          {t('settings.aiModules.automation.title')}
        </h3>
        
        {/* Auto Analysis Toggle */}
        <div className="flex items-center justify-between p-4 bg-white dark:bg-slate-800/50 rounded-xl mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
              <Zap className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <p className="font-semibold text-slate-800 dark:text-white">{t('settings.aiModules.autoAnalysis')}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {t('settings.aiModules.automation.autoAnalysisDescription')}
              </p>
            </div>
          </div>
          <button onClick={() => handleToggle('ai_auto_analysis')}>
            {formData.ai_auto_analysis ? (
              <ToggleRight className="w-12 h-7 text-indigo-500" />
            ) : (
              <ToggleLeft className="w-12 h-7 text-slate-400" />
            )}
          </button>
        </div>
        
        {/* Frequency Selection */}
        {formData.ai_auto_analysis && (
          <div className="mt-4">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              {t('settings.aiModules.automation.frequencyLabel')}
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {frequencyOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setFormData(prev => ({ ...prev, ai_analysis_frequency: option.value }))}
                  className={`
                    p-4 rounded-xl border-2 transition-all text-left
                    ${formData.ai_analysis_frequency === option.value
                      ? 'bg-indigo-50 dark:bg-indigo-900/30 border-indigo-400 dark:border-indigo-500'
                      : 'bg-white dark:bg-slate-800/50 border-slate-200 dark:border-slate-600 hover:border-slate-300 dark:hover:border-slate-500'
                    }
                  `}
                >
                  <p className={`font-semibold ${formData.ai_analysis_frequency === option.value ? 'text-indigo-700 dark:text-indigo-300' : 'text-slate-700 dark:text-slate-200'}`}>
                    {option.label}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    {option.description}
                  </p>
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* Info Box */}
        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-blue-700 dark:text-blue-300">
            {t('settings.aiModules.automation.infoDescription')}
          </p>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={saving}
          className="px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white rounded-xl font-medium shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              {t('common.messages.saving')}
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              {t('settings.aiModules.actions.saveConfiguration')}
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default AIModulesSettings;