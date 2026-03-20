import React from 'react';
import { Globe, TrendingUp, Users, Briefcase, Scale, Zap } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const ExternalFactors = ({ factors, loading }) => {
  const { t } = useI18n();
  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-3 gap-4">
            <div className="h-32 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-32 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-32 bg-slate-200 dark:bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const getIcon = (type) => {
    const normalizedType = (type || '').toLowerCase();
    switch (normalizedType) {
      case 'económico':
      case 'economico':
        return <TrendingUp className="h-6 w-6" />;
      case 'social':
        return <Users className="h-6 w-6" />;
      case 'político':
      case 'politico':
        return <Scale className="h-6 w-6" />;
      case 'tecnológico':
      case 'tecnologico':
        return <Zap className="h-6 w-6" />;
      case 'competitivo':
        return <Briefcase className="h-6 w-6" />;
      default:
        return <Globe className="h-6 w-6" />;
    }
  };

  const getColorClass = (impact) => {
    const normalizedImpact = (impact || '').toLowerCase();
    if (normalizedImpact === 'alto') return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-300 dark:border-red-700';
    if (normalizedImpact === 'medio') return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700';
    return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 border-blue-300 dark:border-blue-700';
  };

  const getText = (value) => {
    if (typeof value === 'string') return value;
    if (typeof value === 'object' && value !== null) {
      return value.texto || value.descripcion || JSON.stringify(value);
    }
    return String(value);
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
      <h3 className="text-xl font-semibold dark:text-white mb-6 flex items-center">
        <Globe className="mr-2 h-6 w-6 text-blue-500" />
        {t('externalFactors.title')}
      </h3>

      {!factors || factors.length === 0 ? (
        <p className="text-slate-500 dark:text-slate-400 text-center py-8">{t('externalFactors.empty')}</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 ">
          {factors.map((factor, idx) => (
            <div 
              key={idx}
              className={`border-l-4 rounded-lg p-4 ${getColorClass(factor.impacto)} transition-all hover:shadow-md`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center">
                  {getIcon(factor.tipo)}
                  <span className="ml-2 font-semibold dark:text-slate-100 capitalize">{getText(factor.tipo)}</span>
                </div>
                <span className="text-xs px-2 py-1 rounded dark:text-slate-100 capitalize">
                  {getText(factor.impacto)}
                </span>
              </div>
              <p className="text-sm text-gray-700 dark:text-slate-100">{getText(factor.descripcion)}</p>
              {factor.tendencia && (
                <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                  <p className="text-xs text-gray-600 dark:text-slate-400">
                    <span className="font-medium">{t('externalFactors.trend')}</span> {getText(factor.tendencia)}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ExternalFactors;