import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useI18n } from '../../context/I18nContext';

const getQuadrantColor = (quadrant) => {
  switch (quadrant) {
    case 'manageClosely': return '#ef4444';
    case 'keepSatisfied': return '#f59e0b';
    case 'keepInformed': return '#3b82f6';
    case 'monitor': return '#10b981';
    default: return '#6b7280';
  }
};

const getQuadrantLabel = (quadrant, t) => {
  switch (quadrant) {
    case 'manageClosely':
      return t('stakeholdersInsights.matrix.quadrants.manageClosely');
    case 'keepSatisfied':
      return t('stakeholdersInsights.matrix.quadrants.keepSatisfied');
    case 'keepInformed':
      return t('stakeholdersInsights.matrix.quadrants.keepInformed');
    case 'monitor':
      return t('stakeholdersInsights.matrix.quadrants.monitor');
    default:
      return quadrant;
  }
};

const PowerInterestTooltip = ({ active, payload, t }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white dark:bg-slate-800 p-3 rounded-lg shadow-lg border border-slate-200 dark:border-slate-600 transition-colors">
        <p className="font-semibold dark:text-white">{data.name}</p>
        <p className="text-sm dark:text-slate-400 capitalize">{t('stakeholdersInsights.matrix.tooltip.type')}: {data.type}</p>
        <p className="text-sm dark:text-slate-400">{t('stakeholdersInsights.matrix.tooltip.influence')}: {(data.influence * 100).toFixed(0)}%</p>
        <p className="text-sm dark:text-slate-400">{t('stakeholdersInsights.matrix.tooltip.satisfaction')}: {data.satisfaction?.toFixed(1)}/10</p>
        <p className="text-sm font-medium mt-1" style={{ color: getQuadrantColor(data.quadrant) }}>
          {getQuadrantLabel(data.quadrant, t)}
        </p>
      </div>
    );
  }
  return null;
};

const PowerInterestMatrix = ({ matrixData, loading }) => {
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

  // Convertir datos de matriz a formato para scatter plot
  const scatterData = [];
  
  if (matrixData) {
    const addToScatter = (items, quadrant) => {
      items.forEach(item => {
        const powerValue = item.power === 'alto' ? 3 : item.power === 'medio' ? 2 : 1;
        const interestValue = item.interest === 'alto' ? 3 : item.interest === 'medio' ? 2 : 1;
        
        scatterData.push({
          x: interestValue,
          y: powerValue,
          name: item.name,
          type: item.type,
          influence: item.influence_score,
          quadrant: quadrant,
          satisfaction: item.satisfaction_score
        });
      });
    };

    addToScatter(matrixData.manage_closely || [], 'manageClosely');
    addToScatter(matrixData.keep_satisfied || [], 'keepSatisfied');
    addToScatter(matrixData.keep_informed || [], 'keepInformed');
    addToScatter(matrixData.monitor || [], 'monitor');
  }

  const getColor = getQuadrantColor;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
      <h3 className="text-lg font-semibold dark:text-white mb-4">{t('stakeholdersInsights.matrix.title')}</h3>
      
      {scatterData.length === 0 ? (
        <p className="text-slate-500 dark:text-slate-400 text-center py-8">{t('stakeholdersInsights.noData')}</p>
      ) : (
        <ResponsiveContainer width="100%" height={400}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
            <XAxis
              type="number"
              dataKey="x"
              name={t('stakeholdersInsights.matrix.axes.interest')}
              domain={[0.5, 3.5]}
              ticks={[1, 2, 3]}
              tickFormatter={(value) => {
                if (value === 1) return t('stakeholdersInsights.matrix.levels.low');
                if (value === 2) return t('stakeholdersInsights.matrix.levels.medium');
                if (value === 3) return t('stakeholdersInsights.matrix.levels.high');
                return '';
              }}
              stroke="#9ca3af"
            />
            <YAxis
              type="number"
              dataKey="y"
              name={t('stakeholdersInsights.matrix.axes.power')}
              domain={[0.5, 3.5]}
              ticks={[1, 2, 3]}
              tickFormatter={(value) => {
                if (value === 1) return t('stakeholdersInsights.matrix.levels.low');
                if (value === 2) return t('stakeholdersInsights.matrix.levels.medium');
                if (value === 3) return t('stakeholdersInsights.matrix.levels.high');
                return '';
              }}
            />
            <Tooltip content={<PowerInterestTooltip t={t} />} />
            <Scatter data={scatterData} fill="#8884d8">
              {scatterData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getColor(entry.quadrant)} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      )}

      {/* Leyenda de cuadrantes */}
      <div className="grid grid-cols-2 gap-4 mt-6">
        <div className="flex items-center">
          <div className="w-4 h-4 bg-red-500 rounded mr-2"></div>
          <span className="text-sm">{t('stakeholdersInsights.matrix.legend.manageClosely')}</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 bg-orange-500 rounded mr-2"></div>
          <span className="text-sm">{t('stakeholdersInsights.matrix.legend.keepSatisfied')}</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 bg-blue-500 rounded mr-2"></div>
          <span className="text-sm">{t('stakeholdersInsights.matrix.legend.keepInformed')}</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 bg-green-500 rounded mr-2"></div>
          <span className="text-sm">{t('stakeholdersInsights.matrix.legend.monitor')}</span>
        </div>
      </div>
    </div>
  );
};

export default PowerInterestMatrix;