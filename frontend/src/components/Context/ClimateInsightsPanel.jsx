import React from 'react';
import { Radar, Thermometer, Workflow, Shield } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const Bar = ({ label, value, max = 100, color = 'bg-blue-500' }) => {
  const width = Math.max(4, Math.min(100, Math.round((value / max) * 100)));
  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-slate-600 dark:text-slate-300">{label}</span>
        <span className="text-slate-700 dark:text-slate-200 font-medium">{value}</span>
      </div>
      <div className="h-2.5 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${width}%` }} />
      </div>
    </div>
  );
};

const ChipList = ({ title, items, icon, emptyLabel }) => (
  <div className="bg-slate-50 dark:bg-slate-900/60 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
    <div className="flex items-center gap-2 mb-3">
      {icon}
      <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100">{title}</h4>
    </div>
    <div className="flex flex-wrap gap-2">
      {(items || []).length === 0 ? (
        <span className="text-xs text-slate-500 dark:text-slate-400">{emptyLabel}</span>
      ) : (
        items.map((item, index) => (
          <span
            key={`${title}-${item}-${index}`}
            className="px-2.5 py-1 rounded-full text-xs bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
          >
            {item}
          </span>
        ))
      )}
    </div>
  </div>
);

const ClimateInsightsPanel = ({ contextData, dashboardData }) => {
  const { t } = useI18n();
  const climate = contextData?.climate_context || {};
  const envScope = contextData?.environmental_scope || [];
  const summary = dashboardData?.summary || {};

  const formatImpactLevel = (impactLevel) => {
    const normalized = String(impactLevel || '').toLowerCase();
    const impactMap = {
      alto: t('contextDashboard.alertsPanel.filters.high'),
      high: t('contextDashboard.alertsPanel.filters.high'),
      medio: t('contextDashboard.alertsPanel.filters.medium'),
      medium: t('contextDashboard.alertsPanel.filters.medium'),
      bajo: t('contextDashboard.alertsPanel.filters.low'),
      low: t('contextDashboard.alertsPanel.filters.low'),
      crítico: t('contextDashboard.alertsPanel.filters.critical'),
      critico: t('contextDashboard.alertsPanel.filters.critical'),
      critical: t('contextDashboard.alertsPanel.filters.critical'),
    };
    return impactMap[normalized] || impactLevel;
  };

  const radarMetrics = {
    regulatory: (climate.regulatory_trends || []).length * 15,
    supply: (climate.supply_chain_signals || []).length * 20,
    digital: (climate.digital_transformation_signals || []).length * 20,
    alerts: (summary.alerts_open || 0) * 10,
    critical: (summary.alerts_critical || 0) * 20,
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow dark:shadow-slate-900/50 p-5 border border-slate-200/60 dark:border-slate-700/60">
        <div className="flex items-center gap-2 mb-4">
          <Radar className="h-5 w-5 text-indigo-500" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{t('contextDashboard.climatePanel.title')}</h3>
        </div>

        <div className="space-y-4">
          <Bar label={t('contextDashboard.climatePanel.radar.regulatory')} value={radarMetrics.regulatory} max={100} color="bg-indigo-500" />
          <Bar label={t('contextDashboard.climatePanel.radar.supply')} value={radarMetrics.supply} max={100} color="bg-amber-500" />
          <Bar label={t('contextDashboard.climatePanel.radar.digital')} value={radarMetrics.digital} max={100} color="bg-blue-500" />
          <Bar label={t('contextDashboard.climatePanel.radar.alertsOpen')} value={radarMetrics.alerts} max={100} color="bg-red-500" />
          <Bar label={t('contextDashboard.climatePanel.radar.alertsCritical')} value={radarMetrics.critical} max={100} color="bg-fuchsia-500" />
        </div>
      </div>

      <div className="space-y-4">
        <ChipList
          title={t('contextDashboard.climatePanel.chips.regulatory')}
          items={climate.regulatory_trends}
          icon={<Thermometer className="h-4 w-4 text-red-500" />}
          emptyLabel={t('contextDashboard.climatePanel.emptySignals')}
        />
        <ChipList
          title={t('contextDashboard.climatePanel.chips.supply')}
          items={climate.supply_chain_signals}
          icon={<Workflow className="h-4 w-4 text-amber-500" />}
          emptyLabel={t('contextDashboard.climatePanel.emptySignals')}
        />
        <ChipList
          title={t('contextDashboard.climatePanel.chips.digital')}
          items={climate.digital_transformation_signals}
          icon={<Shield className="h-4 w-4 text-blue-500" />}
          emptyLabel={t('contextDashboard.climatePanel.emptySignals')}
        />

        <div className="bg-slate-50 dark:bg-slate-900/60 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
          <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-3">{t('contextDashboard.climatePanel.environmentalScope.title')}</h4>
          {(envScope || []).length === 0 ? (
            <p className="text-xs text-slate-500 dark:text-slate-400">{t('contextDashboard.climatePanel.environmentalScope.empty')}</p>
          ) : (
            <div className="space-y-2">
              {envScope.map((item, idx) => (
                <div key={`${item.area}-${idx}`} className="flex items-center justify-between">
                  <span className="text-sm text-slate-700 dark:text-slate-200">{item.area}</span>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    ['alto', 'high', 'critical', 'critico', 'crítico'].includes(String(item.impact_level || '').toLowerCase())
                      ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
                      : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
                  }`}>
                    {formatImpactLevel(item.impact_level)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClimateInsightsPanel;
