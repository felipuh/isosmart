import React from 'react';
import { TrendingUp, AlertTriangle, Target, Users, Activity } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const MetricCard = ({ title, value, subtitle, icon, trend, color, borderColor }) => {
  return (
    <div className={`metric-card ${borderColor}`}>
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 ${color} rounded-lg shadow-md`}>
          {React.createElement(icon, { className: 'w-6 h-6 text-white' })}
        </div>
        {trend && (
          <span className={`flex items-center text-sm font-semibold ${
            trend > 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            <TrendingUp className={`w-4 h-4 mr-1 ${trend < 0 ? 'rotate-180' : ''}`} />
            {Math.abs(trend)}%
          </span>
        )}
      </div>
      
      <h3 className="text-slate-600 dark:text-slate-400 text-sm font-medium mb-2">{title}</h3>
      <p className="text-3xl font-bold text-slate-900 dark:text-white mb-1">{value}</p>
      {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
    </div>
  );
};

const MetricsGrid = ({ data, loading }) => {
  const { t } = useI18n();

  if (loading || !data) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="metric-card border-l-gray-300 h-32">
            <div className="animate-pulse space-y-3">
              <div className="h-12 w-12 bg-slate-200 dark:bg-slate-700 rounded"></div>
              <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4"></div>
              <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-1/2"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  const metrics = [
    {
      title: t('dashboard.metricsGrid.risksIdentified.title'),
      value: data.total_risks || 0,
      subtitle: t('dashboard.metricsGrid.risksIdentified.subtitle').replace(
        '{count}',
        String(data.risks_by_level?.critical || 0)
      ),
      icon: AlertTriangle,
      color: 'bg-gradient-to-br from-red-500 to-red-600',
      borderColor: 'border-l-red-500',
      trend: -12,
    },
    {
      title: t('dashboard.metricsGrid.qualityObjectives.title'),
      value: data.total_objectives || 0,
      subtitle: t('dashboard.metricsGrid.qualityObjectives.subtitle').replace(
        '{percentage}',
        String(Math.round(data.objectives_progress || 0))
      ),
      icon: Target,
      color: 'bg-gradient-to-br from-green-500 to-green-600',
      borderColor: 'border-l-green-500',
      trend: 8,
    },
    {
      title: t('dashboard.metricsGrid.stakeholders.title'),
      value: data.total_stakeholders || 0,
      subtitle: t('dashboard.metricsGrid.stakeholders.subtitle').replace(
        '{count}',
        String(data.high_influence_stakeholders || 0)
      ),
      icon: Users,
      color: 'bg-gradient-to-br from-blue-500 to-blue-600',
      borderColor: 'border-l-blue-500',
    },
    {
      title: t('dashboard.metricsGrid.processCoverage.title'),
      value: `${Math.round(data.process_coverage || 0)}%`,
      subtitle: t('dashboard.metricsGrid.processCoverage.subtitle').replace(
        '{count}',
        String(data.total_processes || 0)
      ),
      icon: Activity,
      color: 'bg-gradient-to-br from-purple-500 to-purple-600',
      borderColor: 'border-l-purple-500',
      trend: 5,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {metrics.map((metric, index) => (
        <MetricCard key={index} {...metric} />
      ))}
    </div>
  );
};

export default MetricsGrid;