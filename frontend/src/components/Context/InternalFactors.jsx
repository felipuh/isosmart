import React from 'react';
import { Building, CheckCircle, AlertCircle } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const InternalFactors = ({ fortalezas, debilidades, loading }) => {
  const { t } = useI18n();
  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-20 bg-slate-200 dark:bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  // Función para extraer texto
  const getItemText = (item) => {
    if (typeof item === 'string') return item;
    if (typeof item === 'object' && item !== null) {
      return item.texto || item.descripcion || JSON.stringify(item);
    }
    return String(item);
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
      <h3 className="text-xl font-semibold dark:text-white mb-6 flex items-center">
        <Building className="mr-2 h-6 w-6 text-purple-500" />
        {t('internalFactors.title')}
      </h3>

      <div className="space-y-6">
        
        {/* Fortalezas */}
        <div>
          <div className="flex items-center mb-4">
            <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
            <h4 className="text-lg font-semibold dark:text-white text-slate-900">
              {t('internalFactors.strengthsTitle').replace('{count}', fortalezas?.length || 0)}
            </h4>
          </div>
          
          {!fortalezas || fortalezas.length === 0 ? (
            <p className="text-slate-500 dark:text-slate-400 text-sm ml-7">{t('internalFactors.emptyStrengths')}</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 ml-7">
              {fortalezas.map((item, idx) => (
                <div 
                  key={idx}
                  className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 rounded-lg p-3 flex items-start transition-colors"
                >
                  <span className="text-green-600 dark:text-green-400 mr-2 mt-0.5">✓</span>
                  <span className="text-sm dark:text-slate-300">{getItemText(item)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Debilidades */}
        <div>
          <div className="flex items-center mb-4">
            <AlertCircle className="h-5 w-5 text-orange-500 mr-2" />
            <h4 className="text-lg font-semibold dark:text-white text-slate-900">
              {t('internalFactors.weaknessesTitle').replace('{count}', debilidades?.length || 0)}
            </h4>
          </div>
          
          {!debilidades || debilidades.length === 0 ? (
            <p className="text-slate-500 dark:text-slate-400 text-sm ml-7">{t('internalFactors.emptyWeaknesses')}</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 ml-7">
              {debilidades.map((item, idx) => (
                <div 
                  key={idx}
                  className="bg-orange-50 dark:bg-orange-900/30 border border-orange-200 dark:border-orange-700 rounded-lg p-3 flex items-start transition-colors"
                >
                  <span className="text-orange-600 mr-2 mt-0.5">!</span>
                  <span className="text-sm text-gray-700 dark:text-slate-100">{getItemText(item)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InternalFactors;