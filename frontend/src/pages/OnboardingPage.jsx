import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, Globe, Building2, ShieldCheck, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import settingsService from '../services/settingsService';

const STANDARD_OPTIONS = [
  { code: 'ISO9001_2015', required: true },
  { code: 'ISO42001_2023' },
  { code: 'ISO27001_2022' },
  { code: 'ISO14001_2015' },
  { code: 'ISO45001_2018' },
];

const ROLE_OPTIONS = ['owner_founder', 'general_manager', 'operations_manager', 'quality_manager', 'external_consultant', 'other'];
const EXPERTISE_OPTIONS = ['none', 'beginner', 'intermediate', 'expert', 'ninja'];
const COMPANY_SIZE_OPTIONS = [
  { value: '10-50', labelKey: 'onboarding.companySizeRanges.range10to50' },
  { value: '51-200', labelKey: 'onboarding.companySizeRanges.range51to200' },
  { value: '201-500', labelKey: 'onboarding.companySizeRanges.range201to500' },
  { value: '501-2000', labelKey: 'onboarding.companySizeRanges.range501to2000' },
  { value: '2000+', labelKey: 'onboarding.companySizeRanges.range2000plus' },
];
const CERTIFICATION_OPTIONS = ['first_time', 'already_certified', 'in_transition'];
const TONE_OPTIONS = ['manager', 'technical'];

const OnboardingPage = () => {
  const navigate = useNavigate();
  const { currentOrganization } = useAuth();
  const { language, setLanguage, t } = useI18n();

  const [enabledStandards, setEnabledStandards] = useState(['ISO9001_2015']);
  const [onboardingProfile, setOnboardingProfile] = useState({
    primary_role: 'quality_manager',
    iso_expertise: 'intermediate',
    company_size_range: '10-50',
    industry_sector: '',
    employees_count: '',
    sites_count: '',
    countries: '',
    certification_status: 'first_time',
  });
  const [preferredTone, setPreferredTone] = useState('manager');
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

  const updateProfileField = (key, value) => {
    setOnboardingProfile((prev) => ({ ...prev, [key]: value }));
  };

  const parseOptionalInt = (value) => {
    if (value === '' || value === null || value === undefined) return null;
    const parsed = Number.parseInt(value, 10);
    return Number.isNaN(parsed) ? null : parsed;
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
        preferred_response_tone: preferredTone,
        onboarding_profile: {
          ...onboardingProfile,
          employees_count: parseOptionalInt(onboardingProfile.employees_count),
          sites_count: parseOptionalInt(onboardingProfile.sites_count),
          countries: onboardingProfile.countries
            .split(',')
            .map((item) => item.trim())
            .filter(Boolean),
        },
      });

      try {
        await settingsService.runOnboardingOrchestration(organizationId);
      } catch {
        // No bloquear el acceso al sistema si la orquestación falla
      }

      navigate('/', { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || t('onboarding.errorComplete'));
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
              <option value="es-LATAM">{t('onboarding.languages.es-LATAM')}</option>
              <option value="en">{t('onboarding.languages.en')}</option>
              <option value="pt">{t('onboarding.languages.pt')}</option>
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
                    <span>{t(`onboarding.standards.${standard.code}`)}</span>
                  </label>
                );
              })}
            </div>
            <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">{t('onboarding.requiredStandard')}</p>
          </section>
        </div>

        <div className="grid gap-6 md:grid-cols-2 mb-8">
          <section className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/80 dark:bg-slate-800/50">
            <h2 className="font-semibold text-slate-900 dark:text-slate-100 mb-3">{t('onboarding.profileTitle')}</h2>
            <div className="space-y-3">
              <label className="block text-sm text-slate-700 dark:text-slate-200">
                {t('onboarding.primaryRole')}
                <select
                  value={onboardingProfile.primary_role}
                  onChange={(event) => updateProfileField('primary_role', event.target.value)}
                  className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700"
                >
                  {ROLE_OPTIONS.map((option) => (
                    <option key={option} value={option}>{t(`onboarding.roles.${option}`)}</option>
                  ))}
                </select>
              </label>

              <label className="block text-sm text-slate-700 dark:text-slate-200">
                {t('onboarding.expertise')}
                <select
                  value={onboardingProfile.iso_expertise}
                  onChange={(event) => updateProfileField('iso_expertise', event.target.value)}
                  className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700"
                >
                  {EXPERTISE_OPTIONS.map((option) => (
                    <option key={option} value={option}>{t(`onboarding.expertiseLevels.${option}`)}</option>
                  ))}
                </select>
              </label>

              <label className="block text-sm text-slate-700 dark:text-slate-200">
                {t('onboarding.companySize')}
                <select
                  value={onboardingProfile.company_size_range}
                  onChange={(event) => updateProfileField('company_size_range', event.target.value)}
                  className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700"
                >
                  {COMPANY_SIZE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{t(option.labelKey)}</option>
                  ))}
                </select>
              </label>

              <label className="block text-sm text-slate-700 dark:text-slate-200">
                {t('onboarding.industry')}
                <input
                  type="text"
                  value={onboardingProfile.industry_sector}
                  onChange={(event) => updateProfileField('industry_sector', event.target.value)}
                  placeholder={t('onboarding.industryPlaceholder')}
                  className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700"
                />
              </label>
            </div>
          </section>

          <section className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/80 dark:bg-slate-800/50">
            <h2 className="font-semibold text-slate-900 dark:text-slate-100 mb-3">{t('onboarding.contextTitle')}</h2>
            <div className="space-y-3">
              <label className="block text-sm text-slate-700 dark:text-slate-200">
                {t('onboarding.employeesCount')}
                <input
                  type="number"
                  min="1"
                  value={onboardingProfile.employees_count}
                  onChange={(event) => updateProfileField('employees_count', event.target.value)}
                  className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700"
                />
              </label>

              <label className="block text-sm text-slate-700 dark:text-slate-200">
                {t('onboarding.sitesCount')}
                <input
                  type="number"
                  min="1"
                  value={onboardingProfile.sites_count}
                  onChange={(event) => updateProfileField('sites_count', event.target.value)}
                  className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700"
                />
              </label>

              <label className="block text-sm text-slate-700 dark:text-slate-200">
                {t('onboarding.countries')}
                <input
                  type="text"
                  value={onboardingProfile.countries}
                  onChange={(event) => updateProfileField('countries', event.target.value)}
                  placeholder={t('onboarding.countriesPlaceholder')}
                  className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700"
                />
              </label>

              <label className="block text-sm text-slate-700 dark:text-slate-200">
                {t('onboarding.certification')}
                <select
                  value={onboardingProfile.certification_status}
                  onChange={(event) => updateProfileField('certification_status', event.target.value)}
                  className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700"
                >
                  {CERTIFICATION_OPTIONS.map((option) => (
                    <option key={option} value={option}>{t(`onboarding.certificationOptions.${option}`)}</option>
                  ))}
                </select>
              </label>
            </div>
          </section>
        </div>

        <section className="mb-8 p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/80 dark:bg-slate-800/50">
          <h2 className="font-semibold text-slate-900 dark:text-slate-100 mb-3">{t('onboarding.toneTitle')}</h2>
          <div className="grid gap-2 md:grid-cols-2">
            {TONE_OPTIONS.map((option) => (
              <label key={option} className="flex items-start gap-2 text-sm text-slate-700 dark:text-slate-200 p-3 rounded-lg border border-slate-300 dark:border-slate-600">
                <input
                  type="radio"
                  name="preferredTone"
                  checked={preferredTone === option}
                  onChange={() => setPreferredTone(option)}
                />
                <span>
                  <span className="font-medium block">{t(`onboarding.tones.${option}.title`)}</span>
                  <span className="text-xs text-slate-500 dark:text-slate-400">{t(`onboarding.tones.${option}.desc`)}</span>
                </span>
              </label>
            ))}
          </div>
        </section>

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