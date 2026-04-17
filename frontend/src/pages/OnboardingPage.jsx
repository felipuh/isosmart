import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  CheckCircle2,
  Globe,
  Info,
  Loader2,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
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

const inputClassName = 'mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-400 focus:ring-4 focus:ring-cyan-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-cyan-500 dark:focus:ring-cyan-500/20';

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

const splitStandardLabel = (label) => {
  const [titlePart, ...descriptionParts] = String(label || '').split(' - ');
  return {
    title: titlePart?.trim() || label,
    description: descriptionParts.join(' - ').trim(),
  };
};

const normalizeAvailableStandards = (standards) => {
  const catalogCodes = new Set(STANDARD_OPTIONS.map((option) => option.code));
  const input = Array.isArray(standards) ? standards : [];
  const filtered = [];

  input.forEach((code) => {
    const normalizedCode = String(code || '').trim();
    if (!normalizedCode || !catalogCodes.has(normalizedCode) || filtered.includes(normalizedCode)) {
      return;
    }
    filtered.push(normalizedCode);
  });

  if (!filtered.includes('ISO9001_2015')) {
    filtered.unshift('ISO9001_2015');
  }

  return filtered;
};

const OnboardingPage = () => {
  const navigate = useNavigate();
  const { currentOrganization } = useAuth();
  const { language, setLanguage, t } = useI18n();

  const [enabledStandards, setEnabledStandards] = useState(['ISO9001_2015']);
  const [availableStandards, setAvailableStandards] = useState(['ISO9001_2015']);
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
  const [currentStep, setCurrentStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [creationStage, setCreationStage] = useState(-1);
  const [error, setError] = useState('');

  const organizationId = currentOrganization?.id;

  const standardOptions = useMemo(
    () => STANDARD_OPTIONS.filter((option) => availableStandards.includes(option.code)),
    [availableStandards],
  );

  const selectedStandards = useMemo(() => {
    if (!enabledStandards.includes('ISO9001_2015')) {
      return ['ISO9001_2015', ...enabledStandards];
    }
    return enabledStandards;
  }, [enabledStandards]);

  useEffect(() => {
    let mounted = true;

    const loadAvailableStandards = async () => {
      if (!organizationId) {
        if (mounted) {
          setAvailableStandards(['ISO9001_2015']);
          setEnabledStandards(['ISO9001_2015']);
        }
        return;
      }

      try {
        const standards = await settingsService.getCommerciallyAvailableStandards(organizationId);
        const normalized = normalizeAvailableStandards(standards);

        if (!mounted) return;

        setAvailableStandards(normalized);
        setEnabledStandards((previous) => {
          const allowed = new Set(normalized);
          const next = previous.filter((code) => allowed.has(code));
          if (!next.includes('ISO9001_2015')) {
            next.unshift('ISO9001_2015');
          }
          return Array.from(new Set(next));
        });
      } catch {
        if (!mounted) return;
        setAvailableStandards(['ISO9001_2015']);
        setEnabledStandards(['ISO9001_2015']);
      }
    };

    loadAvailableStandards();

    return () => {
      mounted = false;
    };
  }, [organizationId]);

  const stepDefinitions = [
    {
      key: 'foundation',
      title: t('onboarding.wizard.foundationTitle'),
      description: t('onboarding.wizard.foundationDesc'),
      icon: Building2,
    },
    {
      key: 'profile',
      title: t('onboarding.wizard.profileStepTitle'),
      description: t('onboarding.wizard.profileStepDesc'),
      icon: ShieldCheck,
    },
    {
      key: 'context',
      title: t('onboarding.wizard.contextStepTitle'),
      description: t('onboarding.wizard.contextStepDesc'),
      icon: Globe,
    },
    {
      key: 'experience',
      title: t('onboarding.wizard.experienceStepTitle'),
      description: t('onboarding.wizard.experienceStepDesc'),
      icon: Sparkles,
    },
  ];

  const creationSteps = [
    t('onboarding.wizard.creatingStandards'),
    t('onboarding.wizard.creatingPreferences'),
    t('onboarding.wizard.creatingWorkspace'),
    t('onboarding.wizard.creatingReady'),
  ];

  const progressPercent = `${((currentStep + 1) / stepDefinitions.length) * 100}%`;
  const creationPercent = creationStage >= 0
    ? `${((Math.min(creationStage, creationSteps.length - 1) + 1) / creationSteps.length) * 100}%`
    : '0%';
  const isLastStep = currentStep === stepDefinitions.length - 1;
  const activeStep = stepDefinitions[currentStep];
  const wizardCounterLabel = t('onboarding.wizard.stepCounter')
    .replace('{current}', String(currentStep + 1))
    .replace('{total}', String(stepDefinitions.length));

  const selectedExpertiseRoute = t(`onboarding.expertiseRoutes.${onboardingProfile.iso_expertise}`);

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

  const nextStep = () => {
    setError('');
    setCurrentStep((prev) => Math.min(prev + 1, stepDefinitions.length - 1));
  };

  const previousStep = () => {
    setError('');
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  };

  const handleFinish = async () => {
    if (!organizationId) {
      setError(t('onboarding.errorNoOrganization'));
      return;
    }
    setSaving(true);
    setCreationStage(0);
    setError('');

    try {
      await settingsService.initializeStandards(organizationId, selectedStandards);
      setCreationStage(1);

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

      setCreationStage(2);

      try {
        await settingsService.runOnboardingOrchestration(organizationId);
      } catch {
        // No bloquear el acceso al sistema si la orquestación falla
      }

      setCreationStage(3);
      await sleep(350);
      navigate('/', { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || t('onboarding.errorComplete'));
      setSaving(false);
      setCreationStage(-1);
    }
  };

  const renderFoundationStep = () => (
    <div className="grid gap-5 xl:grid-cols-3">
      <section className="rounded-3xl border border-slate-200 bg-slate-50/90 p-5 dark:border-slate-700 dark:bg-slate-900/70 xl:col-span-1">
        <div className="flex items-start gap-3">
          <div className="rounded-2xl bg-cyan-500/10 p-3 text-cyan-600 dark:text-cyan-300">
            <Building2 className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900 dark:text-white">{t('onboarding.step1Title')}</h3>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{t('onboarding.step1Desc')}</p>
          </div>
        </div>
        <div className="mt-5 rounded-2xl border border-slate-200 bg-white px-4 py-5 dark:border-slate-700 dark:bg-slate-950/80">
          <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-400 dark:text-slate-500">{t('onboarding.wizard.organizationLabel')}</p>
          <p className="mt-3 text-lg font-semibold text-slate-900 dark:text-white">{currentOrganization?.name || '-'}</p>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-slate-50/90 p-5 dark:border-slate-700 dark:bg-slate-900/70 xl:col-span-2">
        <div className="grid gap-6">
          <div className="max-w-md">
            <div className="flex items-start gap-3">
              <div className="rounded-2xl bg-cyan-500/10 p-3 text-cyan-600 dark:text-cyan-300">
                <Globe className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 dark:text-white">{t('onboarding.step2Title')}</h3>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{t('onboarding.step2Desc')}</p>
              </div>
            </div>
            <select
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
              className={inputClassName}
            >
              <option value="es-LATAM">{t('onboarding.languages.es-LATAM')}</option>
              <option value="en">{t('onboarding.languages.en')}</option>
              <option value="pt">{t('onboarding.languages.pt')}</option>
            </select>
          </div>

          <div>
            <div className="flex items-start gap-3">
              <div className="rounded-2xl bg-cyan-500/10 p-3 text-cyan-600 dark:text-cyan-300">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 dark:text-white">{t('onboarding.step3Title')}</h3>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{t('onboarding.step3Desc')}</p>
              </div>
            </div>

              <div className="mt-5 grid gap-3 lg:grid-cols-2">
                {standardOptions.map((standard) => {
                const checked = selectedStandards.includes(standard.code);
                const standardLabel = t(`onboarding.standards.${standard.code}`);
                const { title, description } = splitStandardLabel(standardLabel);

                return (
                  <label
                    key={standard.code}
                    className={`group relative flex min-h-[124px] cursor-pointer items-start gap-3 rounded-2xl border px-4 py-4 transition-all duration-200 ${checked
                      ? 'border-cyan-400 bg-gradient-to-br from-cyan-50/90 to-sky-50/70 shadow-[0_10px_28px_-22px_rgba(14,165,233,0.9)] dark:border-cyan-500/70 dark:from-cyan-500/12 dark:to-sky-500/8'
                      : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm dark:border-slate-700 dark:bg-slate-950/70 dark:hover:border-slate-600'}`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      disabled={Boolean(standard.required)}
                      onChange={() => toggleStandard(standard.code, standard.required)}
                      className="mt-1 h-4 w-4 shrink-0 accent-cyan-500"
                    />
                    <span className="min-w-0 flex-1 text-sm text-slate-700 dark:text-slate-200">
                      <span className="flex items-start justify-between gap-2">
                        <span className="block break-words text-sm font-semibold leading-5 text-slate-900 dark:text-white">{title}</span>
                        {description ? (
                          <span
                            title={description}
                            className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-slate-200 text-slate-400 dark:border-slate-600 dark:text-slate-400"
                          >
                            <Info className="h-3.5 w-3.5" />
                          </span>
                        ) : null}
                      </span>
                      <span className="mt-3 inline-flex rounded-full border border-slate-200 bg-slate-100 px-2.5 py-1 text-[11px] font-medium tracking-[0.04em] text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
                        {standard.code}
                      </span>
                    </span>
                    {checked ? (
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-cyan-600 dark:text-cyan-300" />
                    ) : null}
                  </label>
                );
              })}
            </div>

            <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">{t('onboarding.requiredStandard')}</p>
          </div>
        </div>
      </section>
    </div>
  );

  const renderProfileStep = () => (
    <div className="grid gap-4 md:grid-cols-2">
      <label className="block text-sm text-slate-700 dark:text-slate-200">
        {t('onboarding.primaryRole')}
        <select
          value={onboardingProfile.primary_role}
          onChange={(event) => updateProfileField('primary_role', event.target.value)}
          className={inputClassName}
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
          className={inputClassName}
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
          className={inputClassName}
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
          className={inputClassName}
        />
      </label>
    </div>
  );

  const renderContextStep = () => (
    <div className="grid gap-4 md:grid-cols-2">
      <label className="block text-sm text-slate-700 dark:text-slate-200">
        {t('onboarding.employeesCount')}
        <input
          type="number"
          min="1"
          value={onboardingProfile.employees_count}
          onChange={(event) => updateProfileField('employees_count', event.target.value)}
          className={inputClassName}
        />
      </label>

      <label className="block text-sm text-slate-700 dark:text-slate-200">
        {t('onboarding.sitesCount')}
        <input
          type="number"
          min="1"
          value={onboardingProfile.sites_count}
          onChange={(event) => updateProfileField('sites_count', event.target.value)}
          className={inputClassName}
        />
      </label>

      <label className="block text-sm text-slate-700 dark:text-slate-200 md:col-span-2">
        {t('onboarding.countries')}
        <input
          type="text"
          value={onboardingProfile.countries}
          onChange={(event) => updateProfileField('countries', event.target.value)}
          placeholder={t('onboarding.countriesPlaceholder')}
          className={inputClassName}
        />
      </label>

      <label className="block text-sm text-slate-700 dark:text-slate-200 md:col-span-2">
        {t('onboarding.certification')}
        <select
          value={onboardingProfile.certification_status}
          onChange={(event) => updateProfileField('certification_status', event.target.value)}
          className={inputClassName}
        >
          {CERTIFICATION_OPTIONS.map((option) => (
            <option key={option} value={option}>{t(`onboarding.certificationOptions.${option}`)}</option>
          ))}
        </select>
      </label>
    </div>
  );

  const renderExperienceStep = () => (
    <div className="space-y-6">
      <section>
        <h3 className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-400 dark:text-slate-500">{t('onboarding.toneTitle')}</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {TONE_OPTIONS.map((option) => (
            <label
              key={option}
              className={`flex cursor-pointer items-start gap-3 rounded-2xl border px-4 py-4 transition ${preferredTone === option
                ? 'border-cyan-400 bg-cyan-50/80 dark:border-cyan-500/70 dark:bg-cyan-500/10'
                : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-950/70 dark:hover:border-slate-600'}`}
            >
              <input
                type="radio"
                name="preferredTone"
                checked={preferredTone === option}
                onChange={() => setPreferredTone(option)}
                className="mt-1"
              />
              <span>
                <span className="block font-medium text-slate-900 dark:text-white">{t(`onboarding.tones.${option}.title`)}</span>
                <span className="mt-1 block text-xs text-slate-500 dark:text-slate-400">{t(`onboarding.tones.${option}.desc`)}</span>
              </span>
            </label>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-slate-50/90 p-5 dark:border-slate-700 dark:bg-slate-900/70">
        <h3 className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-400 dark:text-slate-500">{t('onboarding.aiReview.title')}</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <article className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950/80">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">{t('onboarding.aiReview.engines.engine1.label')}</p>
            <p className="mt-2 text-sm font-semibold text-slate-900 dark:text-white">{t('onboarding.aiReview.engines.engine1.title')}</p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{t('onboarding.aiReview.engines.engine1.desc')}</p>
          </article>
          <article className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950/80">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">{t('onboarding.aiReview.engines.engine2.label')}</p>
            <p className="mt-2 text-sm font-semibold text-slate-900 dark:text-white">{t('onboarding.aiReview.engines.engine2.title')}</p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{t('onboarding.aiReview.engines.engine2.desc')}</p>
          </article>
          <article className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950/80">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">{t('onboarding.aiReview.engines.engine3.label')}</p>
            <p className="mt-2 text-sm font-semibold text-slate-900 dark:text-white">{t('onboarding.aiReview.engines.engine3.title')}</p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{t('onboarding.aiReview.engines.engine3.desc')}</p>
          </article>
        </div>

        <div className="mt-4 rounded-2xl border border-cyan-200 bg-cyan-50/80 px-4 py-3 text-sm text-cyan-900 dark:border-cyan-700 dark:bg-cyan-900/20 dark:text-cyan-100">
          <p className="font-semibold">{t('onboarding.aiReview.suggestedRoute').replace('{route}', selectedExpertiseRoute)}</p>
          <p className="mt-1 text-xs text-cyan-700 dark:text-cyan-200">{t('onboarding.aiReview.selectedLevel').replace('{level}', t(`onboarding.expertiseLevels.${onboardingProfile.iso_expertise}`))}</p>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-slate-50/90 p-5 dark:border-slate-700 dark:bg-slate-900/70">
        <h3 className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-400 dark:text-slate-500">{t('onboarding.wizard.reviewTitle')}</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950/80">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">{t('onboarding.wizard.organizationLabel')}</p>
            <p className="mt-2 text-base font-semibold text-slate-900 dark:text-white">{currentOrganization?.name || '-'}</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950/80">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">{t('onboarding.wizard.languageLabel')}</p>
            <p className="mt-2 text-base font-semibold text-slate-900 dark:text-white">{t(`onboarding.languages.${language}`)}</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950/80 md:col-span-2">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">{t('onboarding.wizard.standardsLabel')}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {selectedStandards.map((standardCode) => (
                <span
                  key={standardCode}
                  className="rounded-full bg-slate-900 px-3 py-1.5 text-xs font-medium text-white dark:bg-cyan-500/15 dark:text-cyan-100"
                >
                  {t(`onboarding.standards.${standardCode}`)}
                </span>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950/80 md:col-span-2">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">{t('onboarding.wizard.toneLabel')}</p>
            <p className="mt-2 text-base font-semibold text-slate-900 dark:text-white">{t(`onboarding.tones.${preferredTone}.title`)}</p>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{t(`onboarding.tones.${preferredTone}.desc`)}</p>
          </div>
        </div>
      </section>
    </div>
  );

  const renderStepContent = () => {
    if (activeStep.key === 'foundation') return renderFoundationStep();
    if (activeStep.key === 'profile') return renderProfileStep();
    if (activeStep.key === 'context') return renderContextStep();
    return renderExperienceStep();
  };

  if (saving) {
    return (
      <div className="relative min-h-screen overflow-hidden bg-slate-950 text-white">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.22),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(56,189,248,0.18),_transparent_28%)]" />
        <div className="relative mx-auto flex min-h-screen max-w-3xl items-center justify-center p-6">
          <div className="w-full rounded-[32px] border border-white/10 bg-white/8 p-8 shadow-2xl shadow-cyan-950/30 backdrop-blur-xl sm:p-10">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-xs font-medium uppercase tracking-[0.24em] text-cyan-100">
              <Sparkles className="h-4 w-4" />
              {t('onboarding.wizard.badge')}
            </div>

            <h1 className="mt-6 text-3xl font-semibold tracking-tight text-white sm:text-4xl">{t('onboarding.wizard.creatingTitle')}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300 sm:text-base">{t('onboarding.wizard.creatingDesc')}</p>

            <div className="mt-8 h-2 overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-sky-400 to-emerald-400 transition-all duration-500"
                style={{ width: creationPercent }}
              />
            </div>

            <div className="mt-8 space-y-3">
              {creationSteps.map((label, index) => {
                const completed = creationStage > index;
                const active = creationStage === index;

                return (
                  <div
                    key={label}
                    className={`flex items-center gap-4 rounded-2xl border px-4 py-4 transition ${completed || active
                      ? 'border-cyan-400/40 bg-cyan-400/10'
                      : 'border-white/10 bg-white/5'}`}
                  >
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10">
                      {completed ? (
                        <CheckCircle2 className="h-5 w-5 text-emerald-300" />
                      ) : active ? (
                        <Loader2 className="h-5 w-5 animate-spin text-cyan-200" />
                      ) : (
                        <div className="h-2.5 w-2.5 rounded-full bg-slate-500" />
                      )}
                    </div>
                    <p className={`text-sm sm:text-base ${completed || active ? 'text-white' : 'text-slate-400'}`}>{label}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-[linear-gradient(135deg,#f8fafc_0%,#ecfeff_42%,#e0f2fe_100%)] dark:bg-[linear-gradient(135deg,#020617_0%,#082f49_48%,#0f172a_100%)]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.12),_transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(14,165,233,0.14),_transparent_28%)]" />

      <div className="relative mx-auto flex min-h-screen max-w-6xl items-center justify-center p-4 sm:p-6 lg:p-10">
        <div className="w-full overflow-hidden rounded-[32px] border border-slate-200/70 bg-white/92 shadow-[0_30px_90px_-40px_rgba(15,23,42,0.45)] backdrop-blur-xl dark:border-slate-700/70 dark:bg-slate-950/70">
          <div className="grid lg:grid-cols-[340px,1fr]">
            <aside className="bg-slate-950 px-6 py-8 text-white sm:px-8 lg:px-10 lg:py-10">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-xs font-medium uppercase tracking-[0.24em] text-cyan-100">
                <Sparkles className="h-4 w-4" />
                {t('onboarding.wizard.badge')}
              </div>

              <h1 className="mt-6 text-3xl font-semibold tracking-tight sm:text-4xl">{t('onboarding.title')}</h1>
              <p className="mt-3 text-sm leading-6 text-slate-300 sm:text-base">{t('onboarding.subtitle')}</p>

              <div className="mt-8 space-y-3">
                {stepDefinitions.map((step, index) => {
                  const StepIcon = step.icon;
                  const completed = index < currentStep;
                  const active = index === currentStep;

                  return (
                    <div
                      key={step.key}
                      className={`rounded-2xl border px-4 py-4 transition ${active
                        ? 'border-cyan-400/40 bg-cyan-400/12'
                        : completed
                          ? 'border-emerald-400/25 bg-emerald-400/10'
                          : 'border-white/10 bg-white/5'}`}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`rounded-2xl p-3 ${active ? 'bg-cyan-400/15 text-cyan-100' : completed ? 'bg-emerald-400/15 text-emerald-100' : 'bg-white/10 text-slate-300'}`}>
                          <StepIcon className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-white">{step.title}</p>
                          <p className="mt-1 text-xs leading-5 text-slate-300">{step.description}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-8 rounded-3xl border border-white/10 bg-white/5 p-5">
                <h2 className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-400">{t('onboarding.wizard.reviewTitle')}</h2>
                <div className="mt-4 space-y-4 text-sm">
                  <div>
                    <p className="text-slate-400">{t('onboarding.wizard.organizationLabel')}</p>
                    <p className="mt-1 font-medium text-white">{currentOrganization?.name || '-'}</p>
                  </div>
                  <div>
                    <p className="text-slate-400">{t('onboarding.wizard.languageLabel')}</p>
                    <p className="mt-1 font-medium text-white">{t(`onboarding.languages.${language}`)}</p>
                  </div>
                  <div>
                    <p className="text-slate-400">{t('onboarding.wizard.standardsLabel')}</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {selectedStandards.map((standardCode) => (
                        <span key={standardCode} className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs text-cyan-100">
                          {t(`onboarding.standards.${standardCode}`)}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </aside>

            <section className="px-6 py-8 sm:px-8 lg:px-10 lg:py-10">
              <div className="mb-8">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-400 dark:text-slate-500">{wizardCounterLabel}</p>
                    <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{activeStep.title}</h2>
                    <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300">{activeStep.description}</p>
                  </div>
                  <div className="hidden rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 sm:inline-flex">
                    {Math.round(((currentStep + 1) / stepDefinitions.length) * 100)}%
                  </div>
                </div>

                <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-sky-400 to-emerald-400 transition-all duration-500"
                    style={{ width: progressPercent }}
                  />
                </div>
              </div>

              <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-950/60 sm:p-6">
                {renderStepContent()}
              </div>

              {error && (
                <div className="mt-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300" role="alert" aria-live="assertive">
                  {error}
                </div>
              )}

              <div className="mt-8 flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
                <button
                  type="button"
                  onClick={previousStep}
                  disabled={currentStep === 0 || saving}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-700 dark:text-slate-200 dark:hover:border-slate-600 dark:hover:bg-slate-900"
                >
                  <ArrowLeft className="h-4 w-4" />
                  {t('onboarding.wizard.back')}
                </button>

                {isLastStep ? (
                  <button
                    type="button"
                    onClick={handleFinish}
                    disabled={saving || !organizationId}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl bg-slate-950 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-cyan-500 dark:text-slate-950 dark:hover:bg-cyan-400"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    {t('onboarding.wizard.create')}
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={nextStep}
                    disabled={!organizationId}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl bg-slate-950 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-cyan-500 dark:text-slate-950 dark:hover:bg-cyan-400"
                  >
                    {t('onboarding.wizard.next')}
                    <ArrowRight className="h-4 w-4" />
                  </button>
                )}
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingPage;