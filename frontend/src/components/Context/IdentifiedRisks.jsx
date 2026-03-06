import React from 'react';
import { AlertTriangle, Shield, TrendingUp } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const IdentifiedRisks = ({ riesgos, loading }) => {
  const { t } = useI18n();
  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-24 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-24 bg-slate-200 dark:bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const getSeverityColor = (severidad) => {
    switch (severidad?.toLowerCase()) {
      case 'crítico':
      case 'alto':
        return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-300 dark:border-red-700';
      case 'medio':
        return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700';
      case 'bajo':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 border-blue-300 dark:border-blue-700';
      default:
        return 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-300 border-slate-300 dark:border-slate-600';
    }
  };

  const getSeverityIcon = (severidad) => {
    switch (severidad?.toLowerCase()) {
      case 'crítico':
      case 'alto':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'medio':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      default:
        return <Shield className="h-5 w-5 text-blue-500" />;
    }
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
      <h3 className="text-xl font-semibold dark:text-white mb-6 flex items-center">
        <AlertTriangle className="mr-2 h-6 w-6 text-red-500" />
        {t('identifiedRisks.title').replace('{count}', riesgos?.length || 0)}
      </h3>

      {!riesgos || riesgos.length === 0 ? (
        <div className="text-center py-8">
          <Shield className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <p className="text-slate-500 dark:text-slate-400">{t('identifiedRisks.empty')}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {riesgos.map((riesgo, idx) => (
            <div 
              key={idx}
              className={`border-l-4 rounded-lg p-4 ${getSeverityColor(riesgo.severidad)} transition-all hover:shadow-md`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center flex-1">
                  {getSeverityIcon(riesgo.severidad)}
                  <h4 className="ml-2 font-semibold dark:text-slate-100">{riesgo.texto}</h4>
                </div>
                <span className={`text-xs px-3 py-1 rounded-full font-semibold ${getSeverityColor(riesgo.severidad)}`}>
                  {riesgo.severidad?.toUpperCase()}
                </span>
              </div>

              {riesgo.descripcion && (
                <p className="text-sm dark:text-slate-300 mb-3 ml-7">{riesgo.descripcion}</p>
              )}

              {riesgo.mitigacion && (
                <div className="ml-7 mt-3 pt-3 border-t dark:border-slate-700">
                  <div className="flex items-start">
                    <TrendingUp className="h-4 w-4 text-green-600 mr-2 mt-0.5" />
                    <div>
                      <p className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">{t('identifiedRisks.mitigationPlan')}</p>
                      <p className="text-sm text-slate-700 dark:text-slate-300">{riesgo.mitigacion}</p>
                    </div>
                  </div>
                </div>
              )}

              {riesgo.categoria && (
                <div className="mt-3 ml-7">
                  <span className="text-xs bg-white dark:bg-slate-700 bg-opacity-50 px-2 py-1 rounded dark:text-slate-300">
                    {t('identifiedRisks.categoryPrefix').replace('{category}', riesgo.categoria)}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default IdentifiedRisks;