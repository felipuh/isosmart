import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { AlertTriangle, AlertCircle, Info, TrendingUp, Filter } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import contextService from '../../services/contextService';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';

const RiskBadge = ({ level }) => {
  const { t } = useI18n();
  const styles = {
    critico: 'bg-red-100 text-red-800 border border-red-300',
    alto: 'bg-orange-100 text-orange-800 border border-orange-300',
    medio: 'bg-yellow-100 text-yellow-800 border border-yellow-300',
    bajo: 'bg-green-100 text-green-800 border border-green-300',
  };

  const icons = {
    critico: AlertTriangle,
    alto: AlertCircle,
    medio: Info,
    bajo: TrendingUp,
  };

  const Icon = icons[level] || Info;

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${styles[level]}`}>
      <Icon className="w-3 h-3 mr-1" />
      {t(`dashboard.riskMatrix.levels.${level}`)}
    </span>
  );
};

const ModuleBadge = ({ module }) => {
  const styles = {
    SCA: 'bg-blue-100 text-blue-800',
    SIE: 'bg-green-100 text-green-800',
    SPM: 'bg-purple-100 text-purple-800',
    ASB: 'bg-orange-100 text-orange-800',
    MANUAL: 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200',
  };

  return (
    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-semibold ${styles[module] || styles.MANUAL}`}>
      {module}
    </span>
  );
};

const RiskMatrix = () => {
  const { t, language } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const [risks, setRisks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const locale = useMemo(() => {
    if (language === 'en') return 'en-US';
    if (language === 'pt') return 'pt-BR';
    return 'es-ES';
  }, [language]);

  const loadRisks = useCallback(async () => {
    try {
      setLoading(true);
      const response = await contextService.getRiskMatrix(orgId);
      const normalized = Array.isArray(response) ? response : response?.results || [];
      setRisks(normalized);
    } catch (error) {
      console.error('Error loading risks:', error);
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    void loadRisks();
  }, [loadRisks]);

  // Datos para el gráfico
  const chartData = [
    {
      module: 'SCA',
      critico: risks.filter(r => r.source_module === 'SCA' && r.risk_level === 'critico').length,
      alto: risks.filter(r => r.source_module === 'SCA' && r.risk_level === 'alto').length,
      medio: risks.filter(r => r.source_module === 'SCA' && r.risk_level === 'medio').length,
    },
    {
      module: 'SIE',
      critico: risks.filter(r => r.source_module === 'SIE' && r.risk_level === 'critico').length,
      alto: risks.filter(r => r.source_module === 'SIE' && r.risk_level === 'alto').length,
      medio: risks.filter(r => r.source_module === 'SIE' && r.risk_level === 'medio').length,
    },
    {
      module: 'SPM',
      critico: risks.filter(r => r.source_module === 'SPM' && r.risk_level === 'critico').length,
      alto: risks.filter(r => r.source_module === 'SPM' && r.risk_level === 'alto').length,
      medio: risks.filter(r => r.source_module === 'SPM' && r.risk_level === 'medio').length,
    },
  ];

  const filteredRisks = filter === 'all' 
    ? risks 
    : risks.filter(r => r.risk_level === filter);

  const levelLabels = {
    critico: t('dashboard.riskMatrix.levels.critico'),
    alto: t('dashboard.riskMatrix.levels.alto'),
    medio: t('dashboard.riskMatrix.levels.medio'),
    bajo: t('dashboard.riskMatrix.levels.bajo'),
  };

  if (loading) {
    return (
      <div className="card">
        <div className="h-8 w-48 bg-slate-200 dark:bg-slate-700 rounded animate-pulse mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-slate-100 dark:bg-slate-800 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Gráfico de barras */}
      <div className="card">
        <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
          <BarChart className="w-5 h-5 text-blue-600" />
          {t('dashboard.riskMatrix.risksByModule')}
        </h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="module" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="critico" fill="#ef4444" name={t('dashboard.riskMatrix.criticals')} />
            <Bar dataKey="alto" fill="#f97316" name={t('dashboard.riskMatrix.highs')} />
            <Bar dataKey="medio" fill="#eab308" name={t('dashboard.riskMatrix.mediums')} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Lista de riesgos */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-red-600" />
            {t('dashboard.riskMatrix.consolidatedTitle')}
          </h2>
          
          {/* Filtros */}
          <div className="flex gap-2 items-center">
            <Filter className="w-4 h-4 text-gray-500" />
            {['all', 'critico', 'alto', 'medio', 'bajo'].map((level) => (
              <button
                key={level}
                onClick={() => setFilter(level)}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                  filter === level
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
                }`}
              >
                {level === 'all' ? t('dashboard.riskMatrix.all') : levelLabels[level]}
              </button>
            ))}
          </div>
        </div>

        {/* Lista de riesgos */}
        <div className="space-y-4">
          {filteredRisks.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <AlertCircle className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p>{t('dashboard.riskMatrix.noRisks')}</p>
            </div>
          ) : (
            filteredRisks.slice(0, 10).map((risk) => (
              <div
                key={risk.id}
                className="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-lg border-l-4 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                style={{
                  borderLeftColor: 
                    risk.risk_level === 'critico' ? '#ef4444' :
                    risk.risk_level === 'alto' ? '#f97316' :
                    risk.risk_level === 'medio' ? '#eab308' : '#22c55e'
                }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <ModuleBadge module={risk.source_module} />
                      <RiskBadge level={risk.risk_level} />
                      <span className="text-xs text-gray-500">
                        {risk.detection_date ? new Date(risk.detection_date).toLocaleDateString(locale) : '-'}
                      </span>
                    </div>
                    <p className="text-slate-900 dark:text-slate-100 font-medium mb-2">
                      {risk.description}
                    </p>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500 dark:text-slate-400">{t('dashboard.riskMatrix.probability')}:</span>
                        <span className="ml-2 font-semibold">{risk.probability}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 dark:text-slate-400">{t('dashboard.riskMatrix.impact')}:</span>
                        <span className="ml-2 font-semibold">{risk.impact}</span>
                      </div>
                      <div className="col-span-2">
                        <span className="text-slate-500 dark:text-slate-400">{t('dashboard.riskMatrix.responsible')}:</span>
                        <span className="ml-2 font-semibold">{risk.responsible}</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Acciones de mitigación */}
                <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                  <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">{t('dashboard.riskMatrix.mitigationActions')}:</p>
                  <p className="text-sm text-slate-700 dark:text-slate-300">{risk.mitigation_actions}</p>
                </div>
              </div>
            ))
          )}
        </div>

        {filteredRisks.length > 10 && (
          <div className="mt-6 text-center">
            <button className="px-6 py-2 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg font-semibold border-2 border-slate-300 dark:border-slate-600 hover:border-blue-500 hover:text-blue-600 transition-all">
              {t('dashboard.riskMatrix.viewAllRisks')} ({filteredRisks.length})
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default RiskMatrix;