import React, { useCallback, useEffect, useState } from 'react';
import riskService from '../../services/riskService';
import { useI18n } from '../../context/I18nContext';
import { useAuth } from '../../context/AuthContext';

const RiskMatrixVisual = ({ onRiskClick }) => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const [matrixData, setMatrixData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCell, setSelectedCell] = useState(null);

  const probabilityLabels = {
    muy_alta: t('riskManagement.matrix.probability.muy_alta'),
    alta: t('riskManagement.matrix.probability.alta'),
    media: t('riskManagement.matrix.probability.media'),
    baja: t('riskManagement.matrix.probability.baja'),
    muy_baja: t('riskManagement.matrix.probability.muy_baja')
  };

  const impactLabels = {
    muy_bajo: t('riskManagement.matrix.impact.muy_bajo'),
    bajo: t('riskManagement.matrix.impact.bajo'),
    medio: t('riskManagement.matrix.impact.medio'),
    alto: t('riskManagement.matrix.impact.alto'),
    muy_alto: t('riskManagement.matrix.impact.muy_alto')
  };

  const probOrder = ['muy_alta', 'alta', 'media', 'baja', 'muy_baja'];
  const impactOrder = ['muy_bajo', 'bajo', 'medio', 'alto', 'muy_alto'];

  const getCellColor = (prob, impact) => {
    const probIndex = probOrder.indexOf(prob);
    const impactIndex = impactOrder.indexOf(impact);
    const riskScore = (4 - probIndex) + impactIndex;

    if (riskScore >= 6) return 'bg-red-500 hover:bg-red-600';
    if (riskScore >= 4) return 'bg-orange-500 hover:bg-orange-600';
    if (riskScore >= 2) return 'bg-yellow-400 hover:bg-yellow-500';
    return 'bg-green-500 hover:bg-green-600';
  };

  const getRiskLevelLabel = (prob, impact) => {
    const probIndex = probOrder.indexOf(prob);
    const impactIndex = impactOrder.indexOf(impact);
    const riskScore = (4 - probIndex) + impactIndex;

    if (riskScore >= 6) return t('riskManagement.levels.critico');
    if (riskScore >= 4) return t('riskManagement.levels.alto');
    if (riskScore >= 2) return t('riskManagement.levels.medio');
    return t('riskManagement.levels.bajo');
  };

  const loadMatrixData = useCallback(async () => {
    setLoading(true);
    try {
      const data = await riskService.getMatrixData(currentOrganization?.id || null);
      setMatrixData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [currentOrganization?.id]);

  useEffect(() => {
    loadMatrixData();
  }, [loadMatrixData]);

  const handleCellClick = (prob, impact) => {
    if (matrixData?.matrix?.[prob]?.[impact]?.count > 0) {
      setSelectedCell({ prob, impact });
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-4 text-center transition-colors">
        <p className="text-red-600 dark:text-red-400">{error}</p>
        <button onClick={loadMatrixData} className="mt-2 text-sm text-red-700 dark:text-red-300 underline hover:no-underline transition-colors">{t('common.buttons.retry')}</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-4 transition-colors">
        <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">{t('riskManagement.matrix.legendTitle')}</h3>
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center"><div className="w-4 h-4 bg-red-500 rounded mr-2"></div><span className="text-sm text-slate-600 dark:text-slate-400">{t('riskManagement.levels.critico')}</span></div>
          <div className="flex items-center"><div className="w-4 h-4 bg-orange-500 rounded mr-2"></div><span className="text-sm text-slate-600 dark:text-slate-400">{t('riskManagement.levels.alto')}</span></div>
          <div className="flex items-center"><div className="w-4 h-4 bg-yellow-400 rounded mr-2"></div><span className="text-sm text-slate-600 dark:text-slate-400">{t('riskManagement.levels.medio')}</span></div>
          <div className="flex items-center"><div className="w-4 h-4 bg-green-500 rounded mr-2"></div><span className="text-sm text-slate-600 dark:text-slate-400">{t('riskManagement.levels.bajo')}</span></div>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 overflow-x-auto transition-colors">
        <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-6 text-center">{t('riskManagement.matrix.title')}</h3>
        
        <div className="min-w-[600px]">
          <div className="flex">
            <div className="w-28 flex-shrink-0"></div>
            <div className="flex-1 grid grid-cols-5 gap-1 mb-1">
              {impactOrder.map((impact) => (
                <div key={impact} className="text-center text-xs font-medium text-slate-600 dark:text-slate-400 py-2">{impactLabels[impact]}</div>
              ))}
            </div>
          </div>

          <div className="flex">
            <div className="w-28 flex-shrink-0 flex flex-col gap-1">
              {probOrder.map((prob) => (
                <div key={prob} className="h-16 flex items-center justify-end pr-3 text-xs font-medium text-slate-600 dark:text-slate-400">{probabilityLabels[prob]}</div>
              ))}
            </div>

            <div className="flex-1">
              {probOrder.map((prob) => (
                <div key={prob} className="grid grid-cols-5 gap-1 mb-1">
                  {impactOrder.map((impact) => {
                    const cellData = matrixData?.matrix?.[prob]?.[impact];
                    const count = cellData?.count || 0;
                    const isSelected = selectedCell?.prob === prob && selectedCell?.impact === impact;

                    return (
                      <div
                        key={`${prob}-${impact}`}
                        onClick={() => handleCellClick(prob, impact)}
                        className={`h-16 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${getCellColor(prob, impact)} ${count > 0 ? 'hover:scale-105' : 'opacity-70'} ${isSelected ? 'ring-4 ring-blue-600 dark:ring-blue-400' : ''}`}
                      >
                        <span className="text-xl font-bold text-white">{count}</span>
                        <span className="text-xs text-white opacity-80">{count === 1 ? t('riskManagement.matrix.riskSingular') : t('riskManagement.matrix.riskPlural')}</span>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-center mt-4">
            <span className="text-sm font-medium text-slate-600 dark:text-slate-400">{t('riskManagement.matrix.impactAxis')}</span>
          </div>
        </div>
      </div>

      {selectedCell && matrixData?.matrix?.[selectedCell.prob]?.[selectedCell.impact]?.count > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-lg font-medium text-slate-900 dark:text-white">
                {t('riskManagement.matrix.selectedTitlePrefix')}: {probabilityLabels[selectedCell.prob]} {t('riskManagement.matrix.selectedProbabilitySuffix')}, {impactLabels[selectedCell.impact]} {t('riskManagement.matrix.selectedImpactSuffix')}
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">{t('riskManagement.matrix.levelLabel')}: <span className="font-medium text-slate-700 dark:text-slate-300">{getRiskLevelLabel(selectedCell.prob, selectedCell.impact)}</span></p>
            </div>
            <button onClick={() => setSelectedCell(null)} className="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="space-y-3">
            {matrixData.matrix[selectedCell.prob][selectedCell.impact].risks.map((risk) => (
              <div key={risk.id} onClick={() => onRiskClick && onRiskClick(risk)} className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 cursor-pointer transition-colors">
                <span className="text-sm font-medium text-slate-900 dark:text-white">#{risk.id}</span>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{risk.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskMatrixVisual;