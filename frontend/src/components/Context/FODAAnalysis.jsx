import React from 'react';
import { TrendingUp, TrendingDown, Shield, AlertTriangle } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const FODAAnalysis = ({ fortalezas, oportunidades, debilidades, amenazas, loading }) => {
  const { t } = useI18n();
  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-40 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-40 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-40 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-40 bg-slate-200 dark:bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  // Función para extraer texto de un item (puede ser string u objeto)
  const getItemText = (item) => {
    if (typeof item === 'string') return item;
    if (typeof item === 'object' && item !== null) {
      return item.texto || item.descripcion || JSON.stringify(item);
    }
    return String(item);
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
      <h3 className="text-xl font-semibold mb-6 dark:text-white">{t('contextSwot.title')}</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Fortalezas */}
        <div className="bg-green-50 dark:bg-green-900/30 border-2 border-green-200 dark:border-green-700 rounded-lg p-5 transition-colors">
          <div className="flex items-center mb-4">
            <div className="bg-green-500 rounded-full p-2 mr-3">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <h4 className="text-lg font-semibold text-green-900 dark:text-green-300">{t('contextSwot.strengths')}</h4>
          </div>
          <ul className="space-y-2">
            {fortalezas && fortalezas.length > 0 ? (
              fortalezas.map((item, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-green-600 dark:text-green-400 mr-2">•</span>
                  <span className="text-sm text-slate-700 dark:text-slate-300">{getItemText(item)}</span>
                </li>
              ))
            ) : (
              <li className="text-sm text-slate-500 dark:text-slate-400 italic">{t('contextSwot.empty.strengths')}</li>
            )}
          </ul>
        </div>

        {/* Oportunidades */}
        <div className="bg-blue-50 dark:bg-blue-900/30 border-2 border-blue-200 dark:border-blue-700 rounded-lg p-5 transition-colors">
          <div className="flex items-center mb-4">
            <div className="bg-blue-500 rounded-full p-2 mr-3">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
            <h4 className="text-lg font-semibold text-blue-900 dark:text-blue-300">{t('contextSwot.opportunities')}</h4>
          </div>
          <ul className="space-y-2">
            {oportunidades && oportunidades.length > 0 ? (
              oportunidades.map((item, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-blue-600 dark:text-blue-400 mr-2">•</span>
                  <span className="text-sm text-slate-700 dark:text-slate-300">{getItemText(item)}</span>
                </li>
              ))
            ) : (
              <li className="text-sm text-slate-500 dark:text-slate-400 italic">{t('contextSwot.empty.opportunities')}</li>
            )}
          </ul>
        </div>

        {/* Debilidades */}
        <div className="bg-yellow-50 dark:bg-yellow-900/30 border-2 border-yellow-200 dark:border-yellow-700 rounded-lg p-5 transition-colors">
          <div className="flex items-center mb-4">
            <div className="bg-yellow-500 rounded-full p-2 mr-3">
              <TrendingDown className="h-5 w-5 text-white" />
            </div>
            <h4 className="text-lg font-semibold text-yellow-900 dark:text-yellow-300">{t('contextSwot.weaknesses')}</h4>
          </div>
          <ul className="space-y-2">
            {debilidades && debilidades.length > 0 ? (
              debilidades.map((item, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-yellow-600 dark:text-yellow-400 mr-2">•</span>
                  <span className="text-sm text-slate-700 dark:text-slate-300">{getItemText(item)}</span>
                </li>
              ))
            ) : (
              <li className="text-sm text-slate-500 dark:text-slate-400 italic">{t('contextSwot.empty.weaknesses')}</li>
            )}
          </ul>
        </div>

        {/* Amenazas */}
        <div className="bg-red-50 dark:bg-red-900/30 border-2 border-red-200 dark:border-red-700 rounded-lg p-5 transition-colors">
          <div className="flex items-center mb-4">
            <div className="bg-red-500 rounded-full p-2 mr-3">
              <AlertTriangle className="h-5 w-5 text-white" />
            </div>
            <h4 className="text-lg font-semibold text-red-900 dark:text-red-300">{t('contextSwot.threats')}</h4>
          </div>
          <ul className="space-y-2">
            {amenazas && amenazas.length > 0 ? (
              amenazas.map((item, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-red-600 dark:text-red-400 mr-2">•</span>
                  <span className="text-sm text-slate-700 dark:text-slate-300">{getItemText(item)}</span>
                </li>
              ))
            ) : (
              <li className="text-sm text-slate-500 dark:text-slate-400 italic">{t('contextSwot.empty.threats')}</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default FODAAnalysis;