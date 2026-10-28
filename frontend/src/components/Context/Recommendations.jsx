import React from 'react';
import { Lightbulb, ArrowRight, CheckCircle2 } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const Recommendations = ({ recomendaciones, loading }) => {
  const { t } = useI18n();
  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const getPriorityColor = (prioridad) => {
    switch (prioridad?.toLowerCase()) {
      case 'alta':
        return 'border-l-red-500 bg-red-50 dark:bg-red-900/30';
      case 'media':
        return 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900/30';
      case 'baja':
        return 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/30';
      default:
        return 'border-l-slate-500 bg-slate-50 dark:bg-slate-700';
    }
  };

  const getPriorityBadge = (prioridad) => {
    switch (prioridad?.toLowerCase()) {
      case 'alta':
        return 'bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-300 border-red-300 dark:border-red-700';
      case 'media':
        return 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700';
      case 'baja':
        return 'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 border-blue-300 dark:border-blue-700';
      default:
        return 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-300 border-slate-300 dark:border-slate-600';
    }
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
      <h3 className="text-xl font-semibold mb-6 flex items-center dark:text-white">
        <Lightbulb className="mr-2 h-6 w-6 text-yellow-500" />
        {t('contextRecommendations.title').replace('{count}', recomendaciones?.length || 0)}
      </h3>

      {!recomendaciones || recomendaciones.length === 0 ? (
        <div className="text-center py-8">
          <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <p className="text-slate-500 dark:text-slate-400">{t('contextRecommendations.empty.noPending')}</p>
          <p className="text-sm text-slate-400 dark:text-slate-500 mt-2">{t('contextRecommendations.empty.allGood')}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {recomendaciones.map((rec, idx) => (
            <div 
              key={idx}
              className={`border-l-4 rounded-lg p-4 ${getPriorityColor(rec.prioridad)} transition-all hover:shadow-md`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <Lightbulb className="h-4 w-4 text-yellow-600 mr-2" />
                    <span className={`text-xs px-2 py-1 rounded border font-semibold ${getPriorityBadge(rec.prioridad)}`}>
                      {rec.prioridad?.toUpperCase() || t('contextRecommendations.defaultPriority')}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">
                    {rec.texto || rec.recomendacion}
                  </p>
                  {rec.descripcion && (
                    <p className="text-sm text-slate-600 dark:text-slate-400">{rec.descripcion}</p>
                  )}
                </div>
              </div>

              {rec.acciones && rec.acciones.length > 0 && (
                <div className="mt-3 pt-3 border-t dark:border-slate-700">
                  <p className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-2">{t('contextRecommendations.actionsSuggested')}</p>
                  <ul className="space-y-1">
                    {rec.acciones.map((acción, actionIdx) => (
                      <li key={actionIdx} className="flex items-start text-sm text-slate-700 dark:text-slate-300">
                        <ArrowRight className="h-4 w-4 text-slate-400 dark:text-slate-600 mr-2 mt-0.5 flex-shrink-0" />
                        <span>{acción}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {rec.beneficio && (
                <div className="mt-3 pt-3 border-t dark:border-slate-700">
                  <p className="text-xs text-slate-600 dark:text-slate-400">
                    <span className="font-medium">{t('contextRecommendations.expectedBenefit')}</span> {rec.beneficio}
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

export default Recommendations;