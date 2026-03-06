import React from 'react';
import { Lightbulb, CheckCircle2, AlertTriangle, Info } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const ProcessRecommendations = ({ recommendations, loading }) => {
  const { t } = useI18n();
  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <h3 className="text-xl font-semibold mb-4 dark:text-white">{t('processRecommendations.title')}</h3>
        <div className="flex items-center justify-center py-8 text-green-600 dark:text-green-400">
          <CheckCircle2 className="h-12 w-12 mr-3" />
          <p className="text-lg">{t('processRecommendations.empty')}</p>
        </div>
      </div>
    );
  }

  const getRecommendationIcon = (text) => {
    if (text.includes('⚠️') || text.includes('URGENTE')) {
      return <AlertTriangle className="h-5 w-5" />;
    } else if (text.includes('✅')) {
      return <CheckCircle2 className="h-5 w-5" />;
    } else if (text.includes('💡') || text.includes('🎯')) {
      return <Lightbulb className="h-5 w-5" />;
    }
    return <Info className="h-5 w-5" />;
  };

  const getRecommendationColor = (text) => {
    if (text.includes('⚠️') || text.includes('URGENTE')) {
      return 'bg-red-50 dark:bg-red-900/30 border-red-400 dark:border-red-600 text-red-800 dark:text-red-300';
    } else if (text.includes('✅')) {
      return 'bg-green-50 dark:bg-green-900/30 border-green-400 dark:border-green-600 text-green-800 dark:text-green-300';
    } else if (text.includes('🔗') || text.includes('📊')) {
      return 'bg-yellow-50 dark:bg-yellow-900/30 border-yellow-400 dark:border-yellow-600 text-yellow-800 dark:text-yellow-300';
    }
    return 'bg-blue-50 dark:bg-blue-900/30 border-blue-400 dark:border-blue-600 text-blue-800 dark:text-blue-300';
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
      <div className="flex items-center mb-4">
        <Lightbulb className="h-6 w-6 text-yellow-500 mr-2" />
        <h3 className="text-xl font-semibold dark:text-white">{t('processRecommendations.systemTitle')}</h3>
      </div>

      <div className="space-y-3">
        {recommendations.map((recommendation, index) => (
          <div
            key={index}
            className={`border-l-4 rounded-lg p-4 flex items-start transition-colors ${getRecommendationColor(recommendation)}`}
          >
            <div className="mr-3 mt-0.5">
              {getRecommendationIcon(recommendation)}
            </div>
            <p className="text-sm flex-1">{recommendation}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProcessRecommendations;