import React, { useState } from 'react';
import { useI18n } from '../../context/I18nContext';

const RiskList = ({ risks, onEdit, onDelete, onStatusChange }) => {
  const { t } = useI18n();
  const [expandedRisk, setExpandedRisk] = useState(null);

  const statusLabels = {
    identified: t('riskManagement.statuses.identified'),
    under_analysis: t('riskManagement.statuses.under_analysis'),
    mitigated: t('riskManagement.statuses.mitigated'),
    accepted: t('riskManagement.statuses.accepted'),
    closed: t('riskManagement.statuses.closed'),
  };

  const statusColors = {
    identified: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
    under_analysis: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300',
    mitigated: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300',
    accepted: 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300',
    closed: 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300',
  };

  const levelColors = {
    critico: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300',
    alto: 'bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300',
    medio: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300',
    bajo: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300',
  };

  const sourceIcons = {
    SCA: { icon: '🔍', label: t('riskManagement.stats.modules.sca') },
    SIE: { icon: '👥', label: t('riskManagement.stats.modules.sie') },
    SPM: { icon: '⚙️', label: t('riskManagement.stats.modules.spm') },
    MANUAL: { icon: '✏️', label: t('riskManagement.stats.modules.manualShort') },
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString(undefined, {
      day: 'numeric',
      month: 'short', 
      year: 'numeric' 
    });
  };

  if (risks.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm dark:shadow-slate-900/50 border border-gray-100 dark:border-slate-700 p-12 text-center transition-colors">
        <div className="w-16 h-16 bg-gray-100 dark:bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-slate-400 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-1">{t('riskManagement.list.emptyTitle')}</h3>
        <p className="text-slate-500 dark:text-slate-400">{t('riskManagement.list.emptySubtitle')}</p>
      </div>
    );
  }

  return (
    <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-md rounded-xl shadow-sm dark:shadow-slate-900/50 border border-white/20 dark:border-slate-700/50 overflow-hidden transition-all duration-300 hover:shadow-md dark:hover:shadow-slate-900/70">
      {/* Table Header */}
      <div className="grid grid-cols-12 gap-4 px-6 py-3 bg-gray-50 dark:bg-slate-700/50 border-b border-gray-200 dark:border-slate-700 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider transition-colors">
        <div className="col-span-4">{t('riskManagement.list.columns.risk')}</div>
        <div className="col-span-2">{t('riskManagement.list.columns.level')}</div>
        <div className="col-span-2">{t('riskManagement.list.columns.source')}</div>
        <div className="col-span-2">{t('common.forms.date')}</div>
        <div className="col-span-2 text-right">{t('riskManagement.list.columns.actions')}</div>
      </div>

      {/* Table Body */}
      <div className="divide-y divide-gray-100 dark:divide-slate-700 transition-colors">
        {risks.map((risk) => (
          <div key={risk.id} className="hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors">
            {/* Main Row */}
            <div 
              className="grid grid-cols-12 gap-4 px-6 py-4 items-center cursor-pointer"
              onClick={() => setExpandedRisk(expandedRisk === risk.id ? null : risk.id)}
            >
              {/* Risk Info */}
              <div className="col-span-4">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-10 h-10 bg-gray-100 dark:bg-slate-700 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-slate-500 dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                      {risk.risk_description?.substring(0, 60)}{risk.risk_description?.length > 60 ? '...' : ''}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                      {risk.risk_category || t('riskManagement.list.uncategorized')} • ISO {risk.iso_clause || '6.1'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Level */}
              <div className="col-span-2">
                <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${levelColors[risk.risk_level] || 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300'}`}>
                  {risk.risk_level ? t(`riskManagement.levels.${risk.risk_level}`) : t('riskManagement.list.details.notAvailable')}
                </span>
              </div>

              {/* Source */}
              <div className="col-span-2">
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{sourceIcons[risk.source_module]?.icon || '📋'}</span>
                  <span className="text-sm text-slate-600 dark:text-slate-400">{sourceIcons[risk.source_module]?.label || risk.source_module}</span>
                </div>
              </div>

              {/* Date */}
              <div className="col-span-2">
                <div className="flex items-center text-sm text-slate-500 dark:text-slate-400">
                  <svg className="w-4 h-4 mr-1.5 text-gray-400 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  {formatDate(risk.detection_date)}
                </div>
              </div>

              {/* Actions */}
              <div className="col-span-2 flex items-center justify-end space-x-2">
                <button
                  onClick={(e) => { e.stopPropagation(); onEdit(risk); }}
                  className="p-2 text-slate-400 dark:text-slate-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-colors"
                  title={t('common.buttons.edit')}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); onDelete(risk.id); }}
                  className="p-2 text-slate-400 dark:text-slate-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                  title={t('common.buttons.delete')}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Expanded Details */}
            {expandedRisk === risk.id && (
              <div className="px-6 pb-4 bg-slate-50 dark:bg-slate-700/50 border-t border-gray-100 dark:border-slate-700 transition-colors">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-600 transition-colors">
                    <h4 className="text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase mb-2">{t('riskManagement.list.details.evaluation')}</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-500 dark:text-slate-400">{t('riskManagement.list.details.probability')}:</span>
                        <span className="font-medium text-slate-900 dark:text-white">{risk.probability || t('riskManagement.list.details.notAvailable')}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500 dark:text-slate-400">{t('riskManagement.list.details.impact')}:</span>
                        <span className="font-medium text-slate-900 dark:text-white">{risk.impact || t('riskManagement.list.details.notAvailable')}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500 dark:text-slate-400">{t('riskManagement.list.details.responsible')}:</span>
                        <span className="font-medium text-slate-900 dark:text-white">{risk.responsible || t('riskManagement.list.details.unassigned')}</span>
                      </div>
                    </div>
                  </div>
                  <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-600 transition-colors">
                    <h4 className="text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase mb-2">{t('common.forms.status')}</h4>
                    <div className="space-y-3">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusColors[risk.status]}`}>
                        {statusLabels[risk.status] || risk.status}
                      </span>
                      <select
                        value=""
                        onChange={(e) => { if (e.target.value) onStatusChange(risk.id, e.target.value); }}
                        className="w-full mt-2 px-3 py-2 text-sm border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 transition-colors"
                      >
                        <option value="">{t('riskManagement.list.changeStatus')}</option>
                        {Object.entries(statusLabels).filter(([key]) => key !== risk.status).map(([key, label]) => (
                          <option key={key} value={key}>{label}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-600 transition-colors">
                    <h4 className="text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase mb-2">{t('riskManagement.list.details.mitigation')}</h4>
                    <p className="text-sm text-slate-600 dark:text-slate-300">
                      {risk.mitigation_actions || t('riskManagement.list.details.noMitigation')}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default RiskList;