// features/planning/pages/PlanningDashboard.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import {
  getRisksOpportunities,
  getObjectives,
  getActions,
  getChanges,
  getHighPriorityRisks,
  getAtRiskObjectives,
  getOverdueActions,
  getPendingChanges
} from '../api/planningApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const PlanningDashboard = () => {
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;

  const statColors = {
    red: {
      card: 'from-red-500/10 to-red-600/5 border-red-500/20 hover:shadow-red-500/20',
      value: 'text-red-400'
    },
    green: {
      card: 'from-green-500/10 to-green-600/5 border-green-500/20 hover:shadow-green-500/20',
      value: 'text-green-400'
    },
    blue: {
      card: 'from-blue-500/10 to-blue-600/5 border-blue-500/20 hover:shadow-blue-500/20',
      value: 'text-blue-400'
    },
    purple: {
      card: 'from-purple-500/10 to-purple-600/5 border-purple-500/20 hover:shadow-purple-500/20',
      value: 'text-purple-400'
    }
  };

  const [stats, setStats] = useState({
    risks: { total: 0, high: 0 },
    opportunities: { total: 0 },
    objectives: { total: 0, active: 0, at_risk: 0 },
    actions: { total: 0, overdue: 0 },
    changes: { total: 0, pending: 0 }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (orgId) loadDashboardData();
  }, [orgId]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      const [
        risksData,
        objectivesData,
        actionsData,
        changesData,
        highRisks,
        atRiskObjs,
        overdueActs,
        pendingChgs
      ] = await Promise.all([
        getRisksOpportunities({ organization_id: orgId }),
        getObjectives({ organization_id: orgId }),
        getActions({ organization_id: orgId }),
        getChanges({ organization_id: orgId }),
        getHighPriorityRisks(orgId),
        getAtRiskObjectives(orgId),
        getOverdueActions(orgId),
        getPendingChanges(orgId)
      ]);

      const risks = normalizeList(risksData);
      const objectives = normalizeList(objectivesData);
      const actions = normalizeList(actionsData);
      const changes = normalizeList(changesData);

      setStats({
        risks: {
          total: risks.filter(r => r.item_type === 'risk').length,
          high: normalizeList(highRisks).length
        },
        opportunities: {
          total: risks.filter(r => r.item_type === 'opportunity').length
        },
        objectives: {
          total: objectives.length,
          active: objectives.filter(o => o.status === 'in_progress').length,
          at_risk: normalizeList(atRiskObjs).length
        },
        actions: {
          total: actions.length,
          overdue: normalizeList(overdueActs).length
        },
        changes: {
          total: changes.length,
          pending: normalizeList(pendingChgs).length
        }
      });
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, subtitle, icon, link, color = 'blue' }) => {
    const palette = statColors[color] || statColors.blue;
    return (
      <Link to={link} className="block">
        <div className={`bg-gradient-to-br ${palette.card} backdrop-blur-sm border rounded-lg p-6 hover:shadow-lg transition-all duration-300`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-400">{title}</h3>
            <span className="text-2xl">{icon}</span>
          </div>
          <div className="flex items-baseline">
            <p className={`text-3xl font-bold ${palette.value}`}>{value}</p>
          </div>
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Planificación</h1>
          <p className="text-gray-400 mt-1">ISO 9001:2015 - Cláusula 6</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Riesgos"
          value={stats.risks.total}
          subtitle={`${stats.risks.high} de alta prioridad`}
          icon="⚠️"
          link="/planning/risks-opportunities"
          color="red"
        />

        <StatCard
          title="Oportunidades"
          value={stats.opportunities.total}
          subtitle="Identificadas y en seguimiento"
          icon="🎯"
          link="/planning/risks-opportunities"
          color="green"
        />

        <StatCard
          title="Objetivos de Calidad"
          value={stats.objectives.total}
          subtitle={`${stats.objectives.active} activos, ${stats.objectives.at_risk} en riesgo`}
          icon="🎪"
          link="/planning/objectives"
          color="blue"
        />

        <StatCard
          title="Acciones"
          value={stats.actions.total}
          subtitle={`${stats.actions.overdue} vencidas`}
          icon="✅"
          link="/planning/actions"
          color="purple"
        />
      </div>

      {/* Change Control */}
      <div className="bg-gradient-to-br from-orange-500/10 to-orange-600/5 backdrop-blur-sm border border-orange-500/20 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-white">Control de Cambios</h2>
            <p className="text-sm text-gray-400">Gestión de cambios al SGC</p>
          </div>
          <Link
            to="/planning/changes"
            className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-all"
          >
            Ver Todos
          </Link>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-800/30 rounded-lg p-4">
            <p className="text-2xl font-bold text-orange-400">{stats.changes.total}</p>
            <p className="text-sm text-gray-400">Total de cambios</p>
          </div>
          <div className="bg-gray-800/30 rounded-lg p-4">
            <p className="text-2xl font-bold text-yellow-400">{stats.changes.pending}</p>
            <p className="text-sm text-gray-400">Pendientes de aprobación</p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Acciones Rápidas</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/planning/risks-opportunities"
            className="flex items-center space-x-3 p-4 bg-red-500/10 border border-red-500/20 rounded-lg hover:bg-red-500/20 transition-all"
          >
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="font-medium text-white">Nuevo Riesgo/Oportunidad</p>
              <p className="text-xs text-gray-400">Identificar y evaluar</p>
            </div>
          </Link>

          <Link
            to="/planning/objectives"
            className="flex items-center space-x-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg hover:bg-blue-500/20 transition-all"
          >
            <span className="text-2xl">🎯</span>
            <div>
              <p className="font-medium text-white">Nuevo Objetivo</p>
              <p className="text-xs text-gray-400">Crear objetivo SMART</p>
            </div>
          </Link>

          <Link
            to="/planning/changes"
            className="flex items-center space-x-3 p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg hover:bg-orange-500/20 transition-all"
          >
            <span className="text-2xl">🔄</span>
            <div>
              <p className="font-medium text-white">Solicitar Cambio</p>
              <p className="text-xs text-gray-400">Control de cambios SGC</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default PlanningDashboard;
