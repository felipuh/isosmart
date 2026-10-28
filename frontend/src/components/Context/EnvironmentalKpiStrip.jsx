import React from 'react';
import { Globe, Siren, BellRing, ShieldAlert, ShieldCheck } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const KpiCard = ({ label, value, accent = 'blue', icon }) => {
  const accentMap = {
    blue: 'text-blue-600 bg-blue-50 dark:bg-blue-900/30 dark:text-blue-300',
    amber: 'text-amber-600 bg-amber-50 dark:bg-amber-900/30 dark:text-amber-300',
    red: 'text-red-600 bg-red-50 dark:bg-red-900/30 dark:text-red-300',
    emerald: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-900/30 dark:text-emerald-300',
    violet: 'text-violet-600 bg-violet-50 dark:bg-violet-900/30 dark:text-violet-300',
  };

  return (
    <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-md rounded-xl shadow-sm dark:shadow-slate-900/50 border border-white/20 dark:border-slate-700/50 p-5 transition-all duration-300 hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm text-slate-600 dark:text-slate-400">{label}</p>
          <p className="text-3xl font-bold text-slate-900 dark:text-white mt-1">{value}</p>
        </div>
        <div className={`p-2.5 rounded-lg ${accentMap[accent] || accentMap.blue}`}>
          {icon}
        </div>
      </div>
    </div>
  );
};

const EnvironmentalKpiStrip = ({ summary, contextData }) => {
  const { t } = useI18n();
  const climateContext = contextData?.climate_context || {};

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
      <KpiCard
        label={t('contextDashboard.kpis.signalsExternal')}
        value={summary?.signals_total || 0}
        accent="blue"
        icon={<Globe className="h-5 w-5" />}
      />
      <KpiCard
        label={t('contextDashboard.kpis.signalsHighCritical')}
        value={summary?.signals_high_critical || 0}
        accent="amber"
        icon={<Siren className="h-5 w-5" />}
      />
      <KpiCard
        label={t('contextDashboard.kpis.alertsOpen')}
        value={summary?.alerts_open || 0}
        accent="red"
        icon={<BellRing className="h-5 w-5" />}
      />
      <KpiCard
        label={t('contextDashboard.kpis.alertsCritical')}
        value={summary?.alerts_critical || 0}
        accent="violet"
        icon={<ShieldAlert className="h-5 w-5" />}
      />
      <KpiCard
        label={t('contextDashboard.kpis.signalsClimateContext')}
        value={climateContext?.external_signals_count || 0}
        accent="emerald"
        icon={<ShieldCheck className="h-5 w-5" />}
      />
    </div>
  );
};

export default EnvironmentalKpiStrip;
