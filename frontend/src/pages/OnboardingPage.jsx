import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, Globe, Building2, ShieldCheck, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import settingsService from '../services/settingsService';

const STANDARD_OPTIONS = [
  { code: 'ISO9001_2015', label: 'ISO 9001:2015', required: true },
  { code: 'ISO42001_2023', label: 'ISO/IEC 42001:2023' },
  { code: 'ISO27001_2022', label: 'ISO 27001:2022' },
  { code: 'ISO14001_2015', label: 'ISO 14001:2015' },
  { code: 'ISO45001_2018', label: 'ISO 45001:2018' },
];

const OnboardingPage = () => {
  const navigate = useNavigate();
  const { currentOrganization } = useAuth();
  const { language, setLanguage, t } = useI18n();

  const [enabledStandards, setEnabledStandards] = useState(['ISO9001_2015']);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const organizationId = currentOrganization?.id;

  const selectedStandards = useMemo(() => {
    if (!enabledStandards.includes('ISO9001_2015')) {
      return ['ISO9001_2015', ...enabledStandards];
    }
    return enabledStandards;
  }, [enabledStandards]);

  const toggleStandard = (code, required) => {
    if (required) return;
    setEnabledStandards((prev) => {
      if (prev.includes(code)) {
        return prev.filter((value) => value !== code);
      }
      return [...prev, code];
    });
  };

  const handleFinish = async () => {
    if (!organizationId) return;
    setSaving(true);
    setError('');

    try {
      await settingsService.initializeStandards(organizationId, selectedStandards);
      await settingsService.completeOnboarding(organizationId, {
        enabled_standards: selectedStandards,
        preferred_language: language,
      });
      navigate('/', { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || 'No fue posible completar el onboarding');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50 to-blue-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 p-6">
      <div className="max-w-4xl mx-auto bg-white/90 dark:bg-slate-800/90 backdrop-blur border border-slate-200 dark:border-slate-700 rounded-2xl shadow-xl p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{t('onboarding.title')}</h1>
          <p className="text-slate-600 dark:text-slate-300">{t('onboarding.subtitle')}</p>
        </div>

        <div className="grid gap-6 md:grid-cols-3 mb-8">
          <section className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/80 dark:bg-slate-800/50">
            <div className="flex items-center gap-2 mb-3 text-indigo-600 dark:text-indigo-400">
              <Building2 className="w-5 h-5" />
              <h2 className="font-semibold">{t('onboarding.step1Title')}</h2>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-300">{t('onboarding.step1Desc')}</p>
            <p className="mt-3 text-sm font-medium text-slate-800 dark:text-slate-200">{currentOrganization?.name}</p>
          </section>

          <section className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/80 dark:bg-slate-800/50">
            <div className="flex items-center gap-2 mb-3 text-indigo-600 dark:text-indigo-400">
              <Globe className="w-5 h-5" />
              <h2 className="font-semibold">{t('onboarding.step2Title')}</h2>
            </div>
            <select
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100"
            >
              <option value="es-LATAM">{t('literals.Español (LATAM)')}</option>
              <option value="en">{t('literals.English')}</option>
              <option value="pt">{t('literals.Português')}</option>
            </select>
          </section>

          <section className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/80 dark:bg-slate-800/50">
            <div className="flex items-center gap-2 mb-3 text-indigo-600 dark:text-indigo-400">
              <ShieldCheck className="w-5 h-5" />
              <h2 className="font-semibold">{t('onboarding.step3Title')}</h2>
            </div>
            <div className="space-y-2">
              {STANDARD_OPTIONS.map((standard) => {
                const checked = selectedStandards.includes(standard.code);
                return (
                  <label key={standard.code} className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-200">
                    <input
                      type="checkbox"
                      checked={checked}
                      disabled={Boolean(standard.required)}
                      onChange={() => toggleStandard(standard.code, standard.required)}
                    />
                    <span>{standard.label}</span>
                  </label>
                );
              })}
            </div>
            <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">{t('onboarding.requiredStandard')}</p>
          </section>
        </div>

        {error && (
          <div className="mb-4 px-4 py-3 rounded-lg border border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300">
            {error}
          </div>
        )}

        <div className="flex justify-end">
          <button
            onClick={handleFinish}
            disabled={saving || !organizationId}
            className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium disabled:opacity-50 inline-flex items-center gap-2"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
            {saving ? t('onboarding.saving') : t('onboarding.complete')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default OnboardingPage;