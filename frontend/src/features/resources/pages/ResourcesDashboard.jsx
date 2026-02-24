// features/resources/pages/ResourcesDashboard.jsx
import React, { useCallback, useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import {
  getResources,
  getInfrastructure,
  getCompetences,
  getTrainings,
  getUpcomingTrainings,
  getCompetenceGaps
} from '../api/resourcesApi';

const ResourcesDashboard = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;

  const statColors = {
    blue: {
      card: 'from-blue-500/10 to-blue-600/5 border-blue-500/20 hover:shadow-blue-500/20',
      value: 'text-blue-400'
    },
    purple: {
      card: 'from-purple-500/10 to-purple-600/5 border-purple-500/20 hover:shadow-purple-500/20',
      value: 'text-purple-400'
    },
    green: {
      card: 'from-green-500/10 to-green-600/5 border-green-500/20 hover:shadow-green-500/20',
      value: 'text-green-400'
    },
    orange: {
      card: 'from-orange-500/10 to-orange-600/5 border-orange-500/20 hover:shadow-orange-500/20',
      value: 'text-orange-400'
    }
  };

  const [stats, setStats] = useState({
    resources: { total: 0, available: 0, in_use: 0 },
    infrastructure: { total: 0, operational: 0, maintenance: 0 },
    competences: { total: 0, gaps: 0 },
    trainings: { upcoming: 0, in_progress: 0 }
  });
  const [loading, setLoading] = useState(true);

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);

      const [resourcesData, infraData, compData, trainData, upcomingData, gapsData] = await Promise.all([
        getResources({ organization_id: orgId }),
        getInfrastructure({ organization_id: orgId }),
        getCompetences({ organization_id: orgId }),
        getTrainings({ organization_id: orgId }),
        getUpcomingTrainings(orgId),
        getCompetenceGaps(orgId)
      ]);

      const resources = Array.isArray(resourcesData) ? resourcesData : resourcesData.results || [];
      const infrastructure = Array.isArray(infraData) ? infraData : infraData.results || [];
      const competences = Array.isArray(compData) ? compData : compData.results || [];
      const trainings = Array.isArray(trainData) ? trainData : trainData.results || [];
      const upcoming = Array.isArray(upcomingData) ? upcomingData : [];
      const gaps = Array.isArray(gapsData) ? gapsData : [];

      setStats({
        resources: {
          total: resources.length,
          available: resources.filter(r => r.status === 'available').length,
          in_use: resources.filter(r => r.status === 'in_use').length
        },
        infrastructure: {
          total: infrastructure.length,
          operational: infrastructure.filter(i => i.status === 'operational').length,
          maintenance: infrastructure.filter(i => i.status === 'maintenance').length
        },
        competences: {
          total: competences.length,
          gaps: gaps.length
        },
        trainings: {
          upcoming: upcoming.length,
          in_progress: trainings.filter(t => t.status === 'in_progress').length
        }
      });
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    if (orgId) {
      loadDashboardData();
    } else {
      setLoading(false);
    }
  }, [orgId, loadDashboardData]);

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
        {subtitle && (
          <p className="text-xs text-gray-500 mt-2">{subtitle}</p>
        )}
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">{t('literals.Recursos y Apoyo')}</h1>
          <p className="text-gray-400 mt-1">{t('literals.ISO 9001:2015 - Cláusula 7')}</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Recursos Totales"
          value={stats.resources.total}
          subtitle={`${stats.resources.available} disponibles, ${stats.resources.in_use} en uso`}
          icon="📦"
          link="/resources/resources"
          color="blue"
        />

        <StatCard
          title="Infraestructura"
          value={stats.infrastructure.total}
          subtitle={`${stats.infrastructure.operational} operativa, ${stats.infrastructure.maintenance} en mantenimiento`}
          icon="🏗️"
          link="/resources/infrastructure"
          color="purple"
        />

        <StatCard
          title="Competencias"
          value={stats.competences.total}
          subtitle={`${stats.competences.gaps} brechas identificadas`}
          icon="🎓"
          link="/resources/competences"
          color="green"
        />

        <StatCard
          title="Capacitaciones"
          value={stats.trainings.upcoming}
          subtitle={`${stats.trainings.in_progress} en progreso`}
          icon="📚"
          link="/resources/trainings"
          color="orange"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">{t('literals.Acciones Rápidas')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/resources/resources/new"
            className="flex items-center space-x-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg hover:bg-blue-500/20 transition-all"
          >
            <span className="text-2xl">📦</span>
            <div>
              <p className="font-medium text-white">{t('literals.Nuevo Recurso')}</p>
              <p className="text-xs text-gray-400">{t('literals.Registrar recurso')}</p>
            </div>
          </Link>

          <Link
            to="/resources/trainings/new"
            className="flex items-center space-x-3 p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg hover:bg-orange-500/20 transition-all"
          >
            <span className="text-2xl">📚</span>
            <div>
              <p className="font-medium text-white">{t('literals.Nueva Capacitación')}</p>
              <p className="text-xs text-gray-400">{t('literals.Planificar capacitación')}</p>
            </div>
          </Link>

          <Link
            to="/resources/competences/new"
            className="flex items-center space-x-3 p-4 bg-green-500/10 border border-green-500/20 rounded-lg hover:bg-green-500/20 transition-all"
          >
            <span className="text-2xl">🎓</span>
            <div>
              <p className="font-medium text-white">{t('literals.Nueva Competencia')}</p>
              <p className="text-xs text-gray-400">{t('literals.Registrar competencia')}</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Module Links */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Link
          to="/resources/work-environment"
          className="p-6 bg-gradient-to-br from-cyan-500/10 to-cyan-600/5 border border-cyan-500/20 rounded-lg hover:shadow-lg transition-all"
        >
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">🏢</span>
            <h3 className="text-lg font-bold text-white">{t('literals.Ambiente de Trabajo')}</h3>
          </div>
          <p className="text-sm text-gray-400">{t('literals.Gestión de ambientes laborales')}</p>
        </Link>

        <Link
          to="/resources/awareness"
          className="p-6 bg-gradient-to-br from-yellow-500/10 to-yellow-600/5 border border-yellow-500/20 rounded-lg hover:shadow-lg transition-all"
        >
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">💡</span>
            <h3 className="text-lg font-bold text-white">{t('literals.Toma de Conciencia')}</h3>
          </div>
          <p className="text-sm text-gray-400">{t('literals.Actividades de sensibilización')}</p>
        </Link>

        <Link
          to="/resources/communications"
          className="p-6 bg-gradient-to-br from-pink-500/10 to-pink-600/5 border border-pink-500/20 rounded-lg hover:shadow-lg transition-all"
        >
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">📢</span>
            <h3 className="text-lg font-bold text-white">{t('literals.Comunicaciones')}</h3>
          </div>
          <p className="text-sm text-gray-400">{t('literals.Plan de comunicación')}</p>
        </Link>
      </div>
    </div>
  );
};

export default ResourcesDashboard;