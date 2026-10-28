import React from 'react';
import { Target, TrendingUp, Users, ShieldCheck } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const CoverageAnalysis = ({ coverageData, loading }) => {
  const { t } = useI18n();
  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-4 gap-4">
            <div className="h-24 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-24 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-24 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-24 bg-slate-200 dark:bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!coverageData) {
    return null;
  }

  const overallScore = coverageData.overall_score || 0;
  const gaps = coverageData.gaps || [];
  const recommendations = coverageData.recommendations || [];

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-blue-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score) => {
    if (score >= 90) return 'bg-green-50 dark:bg-green-900/30';
    if (score >= 70) return 'bg-blue-50 dark:bg-blue-900/30';
    if (score >= 50) return 'bg-yellow-50 dark:bg-yellow-900/30';
    return 'bg-red-50 dark:bg-red-900/30';
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
      <h3 className="text-xl font-semibold mb-6 dark:text-white">{t('scopeInsights.coverage.title')}</h3>

      {/* Score General */}
      <div className={`${getScoreBg(overallScore)} rounded-lg p-6 mb-6 text-center transition-colors`}>
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">{t('scopeInsights.coverage.overallCoverage')}</p>
        <p className={`text-5xl font-bold ${getScoreColor(overallScore)}`}>
          {overallScore.toFixed(1)}%
        </p>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
          {overallScore >= 90 ? t('scopeInsights.coverage.levels.excellent') :
           overallScore >= 70 ? t('scopeInsights.coverage.levels.good') :
           overallScore >= 50 ? t('scopeInsights.coverage.levels.acceptable') : t('scopeInsights.coverage.levels.needsImprovement')}
        </p>
      </div>

      {/* Desglose por categoría */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-4 transition-colors">
          <div className="flex items-center justify-between mb-2">
            <Target className="h-6 w-6 text-blue-500" />
            <span className="text-sm font-semibold text-blue-800 dark:text-blue-300">
              {coverageData.products_coverage?.score?.toFixed(0) || 0}%
            </span>
          </div>
          <p className="text-xs text-slate-700 dark:text-slate-400">{t('scopeInsights.coverage.categories.productsServices')}</p>
        </div>

        <div className="bg-green-50 dark:bg-green-900/30 rounded-lg p-4 transition-colors">
          <div className="flex items-center justify-between mb-2">
            <Users className="h-6 w-6 text-green-500" />
            <span className="text-sm font-semibold text-green-800 dark:text-green-300">
              {coverageData.stakeholder_coverage?.score?.toFixed(0) || 0}%
            </span>
          </div>
          <p className="text-xs text-slate-700 dark:text-slate-400">{t('scopeInsights.coverage.categories.stakeholders')}</p>
        </div>

        <div className="bg-purple-50 dark:bg-purple-900/30 rounded-lg p-4 transition-colors">
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className="h-6 w-6 text-purple-500" />
            <span className="text-sm font-semibold text-purple-800 dark:text-purple-300">
              {coverageData.process_coverage?.score?.toFixed(0) || 0}%
            </span>
          </div>
          <p className="text-xs text-slate-700 dark:text-slate-400">{t('scopeInsights.coverage.categories.processes')}</p>
        </div>

        <div className="bg-orange-50 dark:bg-orange-900/30 rounded-lg p-4 transition-colors">
          <div className="flex items-center justify-between mb-2">
            <ShieldCheck className="h-6 w-6 text-orange-500" />
            <span className="text-sm font-semibold text-orange-800 dark:text-orange-300">
              {coverageData.risk_coverage?.score?.toFixed(0) || 0}%
            </span>
          </div>
          <p className="text-xs text-slate-700 dark:text-slate-400">{t('scopeInsights.coverage.categories.risks')}</p>
        </div>
      </div>

      {/* Gaps identificados */}
      {gaps.length > 0 && (
        <div className="mb-6">
          <h4 className="font-semibold text-slate-900 dark:text-white mb-3">{t('scopeInsights.coverage.gapsTitle')}</h4>
          <div className="space-y-2">
            {gaps.map((gap, idx) => (
              <div key={idx} className="flex items-start bg-red-50 dark:bg-red-900/30 border-l-4 border-red-400 dark:border-red-600 p-3 rounded transition-colors">
                <span className="text-red-600 dark:text-red-400 mr-2">⚠</span>
                <span className="text-sm text-red-800 dark:text-red-300">{gap}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recomendaciones */}
      {recommendations.length > 0 && (
        <div>
          <h4 className="font-semibold text-slate-900 dark:text-white mb-3">{t('scopeInsights.coverage.recommendationsTitle')}</h4>
          <div className="space-y-2">
            {recommendations.map((rec, idx) => (
              <div key={idx} className="flex items-start bg-blue-50 dark:bg-blue-900/30 border-l-4 border-blue-400 dark:border-blue-600 p-3 rounded transition-colors">
                <span className="text-blue-600 dark:text-blue-400 mr-2">💡</span>
                <span className="text-sm text-blue-800 dark:text-blue-300">{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CoverageAnalysis;