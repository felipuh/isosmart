import React, { useState } from 'react';
import { 
  Palette, Sun, Moon, Monitor, Check, Sparkles,
  Eye, Type, Layout, Globe, Loader2, AlertCircle
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useI18n } from '../../context/I18nContext';
import { useAuth } from '../../context/AuthContext';
import settingsService from '../../services/settingsService';

const ThemeSettings = () => {
  const { theme, setTheme, isDark } = useTheme();
  const { language, setLanguage, t } = useI18n();
  const { currentOrganization } = useAuth();
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);

  const themeOptions = [
    {
      id: 'light',
      nameKey: 'settings.theme.lightMode',
      descriptionKey: 'settings.theme.optionDescriptions.light',
      icon: Sun,
      preview: {
        bg: 'bg-white',
        card: 'bg-slate-100',
        text: 'text-slate-800',
        accent: 'bg-indigo-500'
      }
    },
    {
      id: 'dark',
      nameKey: 'settings.theme.darkMode',
      descriptionKey: 'settings.theme.optionDescriptions.dark',
      icon: Moon,
      preview: {
        bg: 'bg-slate-900',
        card: 'bg-slate-800',
        text: 'text-slate-200',
        accent: 'bg-indigo-500'
      }
    },
    {
      id: 'system',
      nameKey: 'settings.theme.systemMode',
      descriptionKey: 'settings.theme.optionDescriptions.system',
      icon: Monitor,
      preview: {
        bg: 'bg-gradient-to-r from-white to-slate-900',
        card: 'bg-gradient-to-r from-slate-100 to-slate-800',
        text: 'text-slate-600',
        accent: 'bg-indigo-500'
      }
    },
  ];

  const handleThemeChange = (newTheme) => {
    if (newTheme === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setTheme(prefersDark ? 'dark' : 'light');
      localStorage.setItem('isosmart-theme', 'system');
    } else {
      setTheme(newTheme);
    }
  };

  const currentThemeSetting = localStorage.getItem('isosmart-theme') || theme;

  const languageOptions = [
    { code: 'es-LATAM', name: t('settings.theme.languageOptions.esLatam'), flag: '🇪🇸' },
    { code: 'en', name: t('settings.theme.languageOptions.en'), flag: '🇺🇸' },
    { code: 'pt', name: t('settings.theme.languageOptions.pt'), flag: '🇧🇷' },
  ];

  const paletteItems = [
    { color: 'bg-indigo-500', name: t('settings.theme.palette.primary') },
    { color: 'bg-purple-500', name: t('settings.theme.palette.secondary') },
    { color: 'bg-emerald-500', name: t('settings.theme.palette.success') },
    { color: 'bg-amber-500', name: t('settings.theme.palette.warning') },
    { color: 'bg-red-500', name: t('settings.theme.palette.error') },
    { color: 'bg-blue-500', name: t('settings.theme.palette.info') },
    { color: 'bg-teal-500', name: t('settings.theme.palette.accent') },
    { color: 'bg-pink-500', name: t('settings.theme.palette.pink') },
    { color: 'bg-slate-500', name: t('settings.theme.palette.neutral') },
    { color: 'bg-violet-500', name: t('settings.theme.palette.violet') },
  ];

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <div className="p-3 bg-gradient-to-br from-pink-500 to-rose-500 rounded-xl shadow-lg shadow-pink-500/25">
          <Palette className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-white">
            {t('settings.theme.title')}
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {t('settings.theme.subtitle')}
          </p>
        </div>
      </div>

      {/* Theme Selection */}
      <div className="mb-8">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <Eye className="w-5 h-5 text-pink-500" />
          {t('settings.theme.colorThemeTitle')}
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {themeOptions.map((option) => {
            const Icon = option.icon;
            const isSelected = currentThemeSetting === option.id || 
              (option.id !== 'system' && currentThemeSetting !== 'system' && theme === option.id);
            
            return (
              <button
                key={option.id}
                onClick={() => handleThemeChange(option.id)}
                className={`
                  relative p-4 rounded-2xl border-2 transition-all duration-300 text-left
                  ${isSelected 
                    ? 'border-pink-400 dark:border-pink-500 shadow-lg shadow-pink-500/20' 
                    : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                  }
                `}
              >
                {/* Selection indicator */}
                {isSelected && (
                  <div className="absolute top-3 right-3 p-1 bg-pink-500 rounded-full">
                    <Check className="w-3 h-3 text-white" />
                  </div>
                )}
                
                {/* Preview */}
                <div className={`${option.preview.bg} rounded-xl p-3 mb-4 h-24 flex flex-col justify-between overflow-hidden`}>
                  <div className="flex gap-2">
                    <div className={`w-8 h-2 ${option.preview.accent} rounded`}></div>
                    <div className={`w-12 h-2 ${option.preview.card} rounded`}></div>
                  </div>
                  <div className="flex gap-2">
                    <div className={`flex-1 h-8 ${option.preview.card} rounded`}></div>
                    <div className={`w-8 h-8 ${option.preview.card} rounded`}></div>
                  </div>
                </div>
                
                {/* Info */}
                <div className="flex items-center gap-3 mb-2">
                  <div className={`p-2 rounded-lg ${isSelected ? 'bg-pink-100 dark:bg-pink-900/30' : 'bg-slate-100 dark:bg-slate-700'}`}>
                    <Icon className={`w-5 h-5 ${isSelected ? 'text-pink-500' : 'text-slate-500 dark:text-slate-400'}`} />
                  </div>
                  <h4 className="font-semibold text-slate-800 dark:text-white">
                    {t(option.nameKey)}
                  </h4>
                </div>
                
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {t(option.descriptionKey)}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Current Theme Info */}
      <div className="mb-8 p-6 bg-gradient-to-br from-pink-50 to-rose-50 dark:from-pink-900/20 dark:to-rose-900/20 rounded-2xl border border-pink-100 dark:border-pink-800/50">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-white dark:bg-slate-800 rounded-xl shadow-sm">
            {isDark ? (
              <Moon className="w-6 h-6 text-indigo-500" />
            ) : (
              <Sun className="w-6 h-6 text-amber-500" />
            )}
          </div>
          <div>
            <p className="font-semibold text-slate-800 dark:text-white">
              {t('settings.theme.currentThemeLabel').replace('{theme}', isDark ? t('settings.theme.darkMode') : t('settings.theme.lightMode'))}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {currentThemeSetting === 'system' 
                ? t('settings.theme.systemFollowing')
                : t('settings.theme.manualConfiguration')
              }
            </p>
          </div>
        </div>
      </div>

      {/* Additional Options */}
      <div className="space-y-4 mb-8">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
          <Globe className="w-5 h-5 text-blue-500" />
          {t('settings.theme.language')}
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {languageOptions.map((lang) => (
            <button
              key={lang.code}
              onClick={async () => {
                try {
                  setSaving(true);
                  setError(null);
                  await settingsService.updateLanguage(currentOrganization?.id, lang.code);
                  setLanguage(lang.code);
                  setSuccess(t('settings.theme.messages.languageChanged').replace('{language}', lang.name));
                  setTimeout(() => setSuccess(null), 3000);
                } catch (err) {
                  console.error('Error changing language:', err);
                  setError(t('settings.theme.messages.languageChangeError'));
                } finally {
                  setSaving(false);
                }
              }}
              disabled={saving}
              className={`
                relative p-4 rounded-xl border-2 transition-all duration-300 text-center
                ${language === lang.code
                  ? 'border-blue-400 dark:border-blue-500 shadow-lg shadow-blue-500/20 bg-blue-50 dark:bg-blue-900/10'
                  : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                }
              `}
            >
              {language === lang.code && (
                <div className="absolute top-2 right-2 p-1 bg-blue-500 rounded-full">
                  <Check className="w-3 h-3 text-white" />
                </div>
              )}
              <div className="text-3xl mb-2">{lang.flag}</div>
              <p className="font-semibold text-slate-800 dark:text-white">{lang.name}</p>
              {saving && language === lang.code && (
                <div className="mt-2 flex items-center justify-center">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts */}
      {success && (
        <div className="mb-6 p-4 bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-800 rounded-xl flex items-center gap-3">
          <Check className="w-5 h-5 text-emerald-500" />
          <span className="text-emerald-700 dark:text-emerald-300">{success}</span>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700 dark:text-red-300">{error}</span>
        </div>
      )}

      {/* Features */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-pink-500" />
          {t('settings.theme.visualFeaturesTitle')}
        </h3>
        
        <div className="p-4 bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
                <Layout className="w-5 h-5 text-indigo-500" />
              </div>
              <div>
                <p className="font-semibold text-slate-800 dark:text-white">{t('settings.theme.features.glassmorphism')}</p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {t('settings.theme.features.glassmorphismDescription')}
                </p>
              </div>
            </div>
            <span className="px-3 py-1 bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 rounded-full text-sm font-medium">
              {t('common.labels.active')}
            </span>
          </div>
        </div>
        
        <div className="p-4 bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-violet-100 dark:bg-violet-900/30 rounded-lg">
                <Sparkles className="w-5 h-5 text-violet-500" />
              </div>
              <div>
                <p className="font-semibold text-slate-800 dark:text-white">{t('settings.theme.features.animations')}</p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {t('settings.theme.features.animationsDescription')}
                </p>
              </div>
            </div>
            <span className="px-3 py-1 bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 rounded-full text-sm font-medium">
              {t('common.labels.active')}
            </span>
          </div>
        </div>
        
        <div className="p-4 bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
                <Type className="w-5 h-5 text-amber-500" />
              </div>
              <div>
                <p className="font-semibold text-slate-800 dark:text-white">{t('settings.theme.features.typography')}</p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {t('settings.theme.features.typographyDescription')}
                </p>
              </div>
            </div>
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {t('settings.theme.defaultLabel')}
            </span>
          </div>
        </div>
      </div>

      {/* Color Palette Preview */}
      <div className="mt-8">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4">
          {t('settings.theme.paletteTitle')}
        </h3>
        
        <div className="grid grid-cols-5 md:grid-cols-10 gap-2">
          {paletteItems.map((item, i) => (
            <div key={i} className="text-center">
              <div className={`w-full aspect-square ${item.color} rounded-lg shadow-md mb-1`}></div>
              <span className="text-xs text-slate-500 dark:text-slate-400">{item.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ThemeSettings;