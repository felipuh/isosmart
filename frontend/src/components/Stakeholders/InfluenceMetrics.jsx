import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { TrendingUp, Users, Network } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const InfluenceTooltip = ({ active, payload, t }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white dark:bg-slate-800 p-3 rounded-lg shadow-lg border border-slate-200 dark:border-slate-600 transition-colors">
        <p className="font-semibold dark:text-white">{data.fullName}</p>
        <p className="text-sm dark:text-slate-400 capitalize">{t('stakeholdersInsights.metrics.tooltip.type')}: {data.type}</p>
        <p className="text-sm dark:text-slate-400">{t('stakeholdersInsights.metrics.tooltip.influence')}: {data.influence}%</p>
        <p className="text-sm dark:text-slate-400 capitalize">{t('stakeholdersInsights.metrics.tooltip.power')}: {data.power}</p>
        <p className="text-sm dark:text-slate-400 capitalize">{t('stakeholdersInsights.metrics.tooltip.interest')}: {data.interest}</p>
      </div>
    );
  }
  return null;
};

const InfluenceMetrics = ({ stakeholders, loading }) => {
  const { t } = useI18n();

  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="h-80 bg-slate-200 dark:bg-slate-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (!stakeholders || stakeholders.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <h3 className="text-lg font-semibold dark:text-white mb-4">{t('stakeholdersInsights.metrics.title')}</h3>
        <p className="text-slate-500 dark:text-slate-400 text-center py-8">{t('stakeholdersInsights.noData')}</p>
      </div>
    );
  }

  // Preparar datos para el gráfico (top 10 por influencia)
  const chartData = [...stakeholders]
    .sort((a, b) => b.influence_score - a.influence_score)
    .slice(0, 10)
    .map(sh => ({
      name: sh.name.length > 20 ? sh.name.substring(0, 20) + '...' : sh.name,
      fullName: sh.name,
      influence: (sh.influence_score * 100).toFixed(0),
      type: sh.stakeholder_type,
      power: sh.power,
      interest: sh.interest
    }));

  const getBarColor = (value) => {
    if (value >= 70) return '#ef4444'; // Rojo - Alto
    if (value >= 50) return '#f59e0b'; // Naranja - Medio
    return '#3b82f6'; // Azul - Bajo
  };

  // Calcular estadísticas generales
  const stats = {
    total: stakeholders.length,
    avgInfluence: (stakeholders.reduce((sum, sh) => sum + sh.influence_score, 0) / stakeholders.length * 100).toFixed(1),
    highInfluence: stakeholders.filter(sh => sh.influence_score >= 0.7).length,
    criticalCount: stakeholders.filter(sh => sh.is_critical).length
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
      <h3 className="text-lg font-semibold dark:text-white mb-4 flex items-center">
        <TrendingUp className="mr-2 h-5 w-5 text-blue-500" />
        {t('stakeholdersInsights.metrics.title')}
      </h3>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-4 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm dark:text-blue-300">{t('stakeholdersInsights.metrics.cards.total')}</p>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.total}</p>
            </div>
            <Users className="h-8 w-8 text-blue-400 dark:text-blue-300" />
          </div>
        </div>

        <div className="bg-green-50 dark:bg-green-900/30 rounded-lg p-4 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm dark:text-green-300">{t('stakeholdersInsights.metrics.cards.average')}</p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.avgInfluence}%</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-400 dark:text-green-300" />
          </div>
        </div>

        <div className="bg-orange-50 dark:bg-orange-900/30 rounded-lg p-4 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">{t('stakeholdersInsights.metrics.cards.highInfluence')}</p>
              <p className="text-2xl font-bold text-orange-600">{stats.highInfluence}</p>
            </div>
            <Network className="h-8 w-8 text-orange-400" />
          </div>
        </div>

        <div className="bg-red-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm dark:text-red-300">{t('stakeholdersInsights.metrics.cards.critical')}</p>
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">{stats.criticalCount}</p>
            </div>
            <Network className="h-8 w-8 text-red-400 dark:text-red-300" />
          </div>
        </div>
      </div>

      {/* Bar Chart */}
      <div className="mt-6">
        <h4 className="text-sm font-medium dark:text-slate-300 mb-3">{t('stakeholdersInsights.metrics.top10')}</h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 120, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
            <XAxis type="number" domain={[0, 100]} tick={{ fill: '#9ca3af' }} />
            <YAxis type="category" dataKey="name" width={100} tick={{ fill: '#9ca3af', fontSize: 12 }} />
            <Tooltip content={<InfluenceTooltip t={t} />} />
            <Bar dataKey="influence" radius={[0, 8, 8, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.influence)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default InfluenceMetrics;