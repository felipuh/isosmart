import React from 'react';
import { FileText, CheckCircle, XCircle } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const ScopeStatement = ({ scopeData, loading }) => {
  const { t } = useI18n();
  const statusLabels = {
    active: t('scopeInsights.statement.status.active'),
    approved: t('scopeInsights.statement.status.approved'),
    under_review: t('scopeInsights.statement.status.underReview'),
    draft: t('scopeInsights.statement.status.draft'),
  };
  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!scopeData) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <h3 className="text-xl font-semibold mb-4 dark:text-white">{t('scopeInsights.statement.title')}</h3>
        <p className="text-slate-500 dark:text-slate-400 text-center py-8">{t('scopeInsights.statement.empty')}</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <FileText className="h-6 w-6 text-blue-500 mr-2" />
          <h3 className="text-xl font-semibold dark:text-white">{t('scopeInsights.statement.title')}</h3>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
          scopeData.status === 'active' ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300' :
          scopeData.status === 'approved' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300' :
          scopeData.status === 'under_review' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300' :
          'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-300'
        }`}>
          {statusLabels[scopeData.status] || statusLabels.draft}
        </span>
      </div>

      {/* Info del alcance */}
      <div className="grid grid-cols-3 gap-4 mb-6 pb-6 border-b dark:border-slate-700">
        <div>
          <p className="text-sm text-slate-600 dark:text-slate-400">{t('scopeInsights.statement.version')}</p>
          <p className="text-lg font-semibold dark:text-white">{scopeData.version}</p>
        </div>
        <div>
          <p className="text-sm text-slate-600 dark:text-slate-400">{t('scopeInsights.statement.effectiveDate')}</p>
          <p className="text-lg font-semibold dark:text-white">
            {scopeData.effective_date ? new Date(scopeData.effective_date).toLocaleDateString(undefined) : t('scopeInsights.statement.notAvailable')}
          </p>
        </div>
        <div>
          <p className="text-sm text-slate-600 dark:text-slate-400">{t('scopeInsights.statement.coverage')}</p>
          <p className="text-lg font-semibold text-blue-600">
            {scopeData.coverage_percentage?.toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Declaración */}
      <div className="mb-6">
        <h4 className="font-semibold text-slate-900 dark:text-white mb-3">{t('scopeInsights.statement.formalDeclaration')}</h4>
        <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4 border-l-4 border-blue-500 transition-colors">
          <p className="text-slate-700 dark:text-slate-300 whitespace-pre-line leading-relaxed">
            {scopeData.scope_statement}
          </p>
        </div>
      </div>

      {/* Productos y Servicios */}
      {scopeData.products_services && scopeData.products_services.length > 0 && (
        <div className="mb-6">
          <h4 className="font-semibold text-slate-900 dark:text-white mb-3 flex items-center">
            <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
            {t('scopeInsights.statement.productsServicesTitle').replace('{count}', scopeData.products_services.length)}
          </h4>
          <ul className="space-y-2">
            {scopeData.products_services.map((product, idx) => (
              <li key={idx} className="flex items-start">
                <span className="text-green-600 dark:text-green-400 mr-2">✓</span>
                <span className="text-slate-700 dark:text-slate-300">{product}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Exclusiones */}
      {scopeData.exclusions && scopeData.exclusions.length > 0 && (
        <div>
          <h4 className="font-semibold text-slate-900 dark:text-white mb-3 flex items-center">
            <XCircle className="h-5 w-5 text-orange-500 mr-2" />
            {t('scopeInsights.statement.permittedExclusionsTitle').replace('{count}', scopeData.exclusions.length)}
          </h4>
          <div className="space-y-3">
            {scopeData.exclusions.map((exclusion, idx) => (
              <div key={idx} className="bg-orange-50 dark:bg-orange-900/30 border-l-4 border-orange-400 dark:border-orange-600 p-3 rounded transition-colors">
                <p className="font-medium text-orange-900 dark:text-orange-300">
                  {t('scopeInsights.statement.clauseLabel').replace('{clause}', exclusion.clause).replace('{title}', exclusion.title)}
                </p>
                <p className="text-sm text-orange-700 dark:text-orange-400 mt-1">
                  <span className="font-medium">{t('scopeInsights.statement.reason')}:</span> {exclusion.reason}
                </p>
                {exclusion.impact && (
                  <p className="text-xs text-orange-600 dark:text-orange-400 mt-1">
                    <span className="font-medium">{t('scopeInsights.statement.impact')}:</span> {exclusion.impact}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ScopeStatement;