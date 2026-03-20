import React from 'react';
import { Target, TrendingUp, Calendar, User } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const QualityObjectives = ({ objectives }) => {
  const { t } = useI18n();
  if (!objectives || objectives.length === 0) {
    return (
      <div className="card">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <Target className="w-6 h-6 text-green-600" />
          {t('dashboard.qualityObjectives.title')}
        </h2>
        <div className="text-center py-12 text-gray-500">
          <Target className="w-12 h-12 mx-auto mb-3 text-gray-400" />
          <p>{t('dashboard.qualityObjectives.empty')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
        <Target className="w-6 h-6 text-green-600" />
        {t('dashboard.qualityObjectives.title')}
      </h2>

      <div className="space-y-4">
        {objectives.map((obj, index) => {
          const progress = obj.progress || 0;
          const progressColor = 
            progress >= 80 ? 'bg-green-500' :
            progress >= 50 ? 'bg-yellow-500' : 'bg-red-500';
          
          const badgeColor = 
            progress >= 80 ? 'bg-green-100 text-green-800' :
            progress >= 50 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800';

          return (
            <div 
              key={index} 
              className="p-4 bg-gradient-to-br from-slate-50 dark:from-slate-800 to-white dark:to-slate-800 rounded-lg border-2 border-slate-200 dark:border-slate-700 hover:border-blue-400 dark:hover:border-blue-500 transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-bold text-slate-900 dark:text-white flex-1">{obj.indicator_name}</h3>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${badgeColor}`}>
                  {Math.round(progress)}%
                </span>
              </div>

              {/* Métricas */}
              <div className="grid grid-cols-3 gap-3 mb-4 text-sm">
                <div className="text-center p-2 bg-blue-50 rounded">
                  <p className="text-xs text-slate-600 dark:text-slate-400">{t('dashboard.qualityObjectives.baseline')}</p>
                  <p className="font-bold text-blue-900 dark:text-blue-300">{obj.baseline}</p>
                </div>
                <div className="text-center p-2 bg-purple-50 dark:bg-purple-900/30 rounded">
                  <p className="text-xs text-slate-600 dark:text-slate-400">{t('dashboard.qualityObjectives.current')}</p>
                  <p className="font-bold text-purple-900 dark:text-purple-300">{obj.current || '-'}</p>
                </div>
                <div className="text-center p-2 bg-green-50 dark:bg-green-900/30 rounded">
                  <p className="text-xs text-slate-600 dark:text-slate-400">{t('dashboard.qualityObjectives.target')}</p>
                  <p className="font-bold text-green-900">{obj.target}</p>
                </div>
              </div>

              {/* Barra de progreso */}
              <div className="mb-3">
                <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${progressColor}`}
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400">
                <span className="flex items-center gap-1">
                  <User className="w-3 h-3" />
                  {obj.responsible}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {obj.deadline || t('dashboard.qualityObjectives.noDate')}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default QualityObjectives;