import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import {
  getNonconformities, getNonconformityStats,
  getCorrectiveActions, getOverdueActions,
  getContinualImprovements, getActiveInitiatives
} from '../api/improvementApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const statColors = {
  red:    { card: 'from-red-500/10 to-red-600/5 border-red-500/20', value: 'text-red-400', shadow: 'shadow-red-500/10' },
  orange: { card: 'from-orange-500/10 to-orange-600/5 border-orange-500/20', value: 'text-orange-400', shadow: 'shadow-orange-500/10' },
  blue:   { card: 'from-blue-500/10 to-blue-600/5 border-blue-500/20', value: 'text-blue-400', shadow: 'shadow-blue-500/10' },
  green:  { card: 'from-green-500/10 to-green-600/5 border-green-500/20', value: 'text-green-400', shadow: 'shadow-green-500/10' },
};

const ImprovementDashboard = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    nonconformities: { total: 0, open: 0, closed: 0, critical: 0 },
    corrective_actions: { total: 0, overdue: 0, effective: 0 },
    improvements: { total: 0, active: 0, successful: 0 }
  });

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      const [ncsData, ncStats, actionsData, overdueData, improvementsData, activeData] = await Promise.all([
        getNonconformities({ organization_id: orgId }),
        getNonconformityStats(orgId).catch(() => null),
        getCorrectiveActions({ organization_id: orgId }),
        getOverdueActions(orgId).catch(() => []),
        getContinualImprovements({ organization_id: orgId }),
        getActiveInitiatives(orgId).catch(() => [])
      ]);

      const ncs = normalizeList(ncsData);
      const actions = normalizeList(actionsData);
      const overdue = normalizeList(overdueData);
      const improvements = normalizeList(improvementsData);
      const active = normalizeList(activeData);

      setStats({
        nonconformities: {
          total: ncStats?.total ?? ncs.length,
          open: ncStats?.open ?? ncs.filter(n => n.status === 'open').length,
          closed: ncStats?.closed ?? ncs.filter(n => n.status === 'closed').length,
          critical: ncStats?.critical ?? ncs.filter(n => n.severity === 'critical').length,
        },
        corrective_actions: {
          total: actions.length,
          overdue: overdue.length,
          effective: actions.filter(a => a.is_effective === true).length,
        },
        improvements: {
          total: improvements.length,
          active: active.length,
          successful: improvements.filter(i => i.status === 'successful').length,
        }
      });
    } catch (error) {
      console.error('Error loading improvement dashboard:', error);
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => { if (orgId) loadDashboard(); }, [orgId, loadDashboard]);

  const StatCard = ({ title, value, subtitle, icon, link, color = 'blue' }) => {
    const palette = statColors[color] || statColors.blue;
    return (
      <Link to={link} className="block">
        <div className={`bg-gradient-to-br ${palette.card} backdrop-blur-sm border rounded-lg p-6 hover:shadow-lg ${palette.shadow} transition-all duration-300`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-400">{title}</h3>
            <span className="text-2xl">{icon}</span>
          </div>
          <p className={`text-3xl font-bold ${palette.value}`}>{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-2">{subtitle}</p>}
        </div>
      </Link>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" style={{ fontFamily: '"Sora", "Work Sans", sans-serif' }}>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">{t('literals.Mejora')}</h1>
          <p className="text-gray-400 mt-1">{t('literals.ISO 9001:2015 - Cláusula 10')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="No Conformidades" value={stats.nonconformities.total}
          subtitle={`${stats.nonconformities.open} abiertas, ${stats.nonconformities.critical} críticas`}
          icon="🚨" link="/improvement/nonconformities" color="red" />
        <StatCard title="Acciones Correctivas" value={stats.corrective_actions.total}
          subtitle={`${stats.corrective_actions.overdue} vencidas, ${stats.corrective_actions.effective} efectivas`}
          icon="🔧" link="/improvement/corrective-actions" color="orange" />
        <StatCard title="Mejora Continua" value={stats.improvements.total}
          subtitle={`${stats.improvements.active} activas, ${stats.improvements.successful} exitosas`}
          icon="📈" link="/improvement/continual" color="green" />
        <StatCard title="Efectividad"
          value={stats.corrective_actions.total > 0 ? `${Math.round((stats.corrective_actions.effective / stats.corrective_actions.total) * 100)}%` : 'N/A'}
          subtitle="Tasa de acciones efectivas" icon="✅" link="/improvement/corrective-actions" color="blue" />
      </div>

      {stats.nonconformities.critical > 0 && (
        <div className="bg-gradient-to-br from-red-500/10 to-red-600/5 backdrop-blur-sm border border-red-500/20 rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">🚨</span>
            <h2 className="text-xl font-bold text-white">{t('literals.Atención requerida')}</h2>
          </div>
          <p className="text-gray-300">{t('literals.Hay {stats.nonconformities.critical} no conformidad(es) crítica(s) que requieren acción inmediata.')}</p>
          <Link to="/improvement/nonconformities" className="inline-block mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all">
            Ver no conformidades críticas
          </Link>
        </div>
      )}

      {stats.corrective_actions.overdue > 0 && (
        <div className="bg-gradient-to-br from-orange-500/10 to-orange-600/5 backdrop-blur-sm border border-orange-500/20 rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">⏰</span>
            <h2 className="text-xl font-bold text-white">{t('literals.Acciones Vencidas')}</h2>
          </div>
          <p className="text-gray-300">{t('literals.Hay {stats.corrective_actions.overdue} acción(es) correctiva(s) que han superado su fecha de cumplimiento.')}</p>
          <Link to="/improvement/corrective-actions" className="inline-block mt-4 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-all">
            Ver Acciones Vencidas
          </Link>
        </div>
      )}

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">{t('literals.Acciones rápidas')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link to="/improvement/nonconformities/new" className="flex items-center space-x-3 p-4 bg-red-500/10 border border-red-500/20 rounded-lg hover:bg-red-500/20 transition-all">
            <span className="text-2xl">🚨</span>
            <div><p className="font-medium text-white">{t('literals.Reportar NC')}</p><p className="text-xs text-gray-400">{t('literals.Registrar no conformidad')}</p></div>
          </Link>
          <Link to="/improvement/corrective-actions/new" className="flex items-center space-x-3 p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg hover:bg-orange-500/20 transition-all">
            <span className="text-2xl">🔧</span>
            <div><p className="font-medium text-white">{t('literals.Nueva acción correctiva')}</p><p className="text-xs text-gray-400">{t('literals.Crear plan de acción')}</p></div>
          </Link>
          <Link to="/improvement/continual/new" className="flex items-center space-x-3 p-4 bg-green-500/10 border border-green-500/20 rounded-lg hover:bg-green-500/20 transition-all">
            <span className="text-2xl">📈</span>
            <div><p className="font-medium text-white">{t('literals.Iniciativa de mejora')}</p><p className="text-xs text-gray-400">{t('literals.Proponer mejora continua')}</p></div>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link to="/improvement/nonconformities" className="p-6 bg-gradient-to-br from-red-500/10 to-red-600/5 border border-red-500/20 rounded-lg hover:shadow-lg transition-all">
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">📋</span>
            <h3 className="text-lg font-bold text-white">{t('literals.No Conformidades y Acciones Correctivas')}</h3>
          </div>
          <p className="text-sm text-gray-400">{t('literals.ISO 9001:2015 Cláusula 10.2 - Gestión de no conformidades, análisis de causa raíz y acciones correctivas')}</p>
        </Link>
        <Link to="/improvement/continual" className="p-6 bg-gradient-to-br from-green-500/10 to-green-600/5 border border-green-500/20 rounded-lg hover:shadow-lg transition-all">
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">🚀</span>
            <h3 className="text-lg font-bold text-white">{t('literals.Mejora Continua')}</h3>
          </div>
          <p className="text-sm text-gray-400">{t('literals.ISO 9001:2015 Cláusula 10.3 - Iniciativas de mejora, análisis de ROI y seguimiento de resultados')}</p>
        </Link>
      </div>
    </div>
  );
};

export default ImprovementDashboard;