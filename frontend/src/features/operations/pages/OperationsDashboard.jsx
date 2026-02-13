// features/operations/pages/OperationsDashboard.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import {
  getCustomerRequirements,
  getDesignProjects,
  getExternalProviders,
  getNonconformities,
  getProductReleases,
  getPendingReviewRequirements,
  getOpenNonconformities,
  getCriticalNonconformities
} from '../api/operationsApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const OperationsDashboard = () => {
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
    red: {
      card: 'from-red-500/10 to-red-600/5 border-red-500/20 hover:shadow-red-500/20',
      value: 'text-red-400'
    }
  };

  const [stats, setStats] = useState({
    requirements: { total: 0, pending_review: 0 },
    design_projects: { total: 0, active: 0 },
    providers: { total: 0, approved: 0 },
    releases: { total: 0, pending: 0 },
    nonconformities: { total: 0, open: 0, critical: 0 }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (orgId) loadDashboardData();
  }, [orgId]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      const [
        requirementsData,
        designData,
        providersData,
        releasesData,
        ncsData,
        pendingReqs,
        openNCs,
        criticalNCs
      ] = await Promise.all([
        getCustomerRequirements({ organization_id: orgId }),
        getDesignProjects({ organization_id: orgId }),
        getExternalProviders({ organization_id: orgId }),
        getProductReleases({ organization_id: orgId }),
        getNonconformities({ organization_id: orgId }),
        getPendingReviewRequirements(orgId),
        getOpenNonconformities(orgId),
        getCriticalNonconformities(orgId)
      ]);

      const requirements = normalizeList(requirementsData);
      const design = normalizeList(designData);
      const providers = normalizeList(providersData);
      const releases = normalizeList(releasesData);
      const ncs = normalizeList(ncsData);

      setStats({
        requirements: {
          total: requirements.length,
          pending_review: normalizeList(pendingReqs).length
        },
        design_projects: {
          total: design.length,
          active: design.filter(p => p.status === 'active').length
        },
        providers: {
          total: providers.length,
          approved: providers.filter(p => p.classification === 'approved').length
        },
        releases: {
          total: releases.length,
          pending: releases.filter(r => r.status === 'pending').length
        },
        nonconformities: {
          total: ncs.length,
          open: normalizeList(openNCs).length,
          critical: normalizeList(criticalNCs).length
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
          <h1 className="text-3xl font-bold text-white">Operación</h1>
          <p className="text-gray-400 mt-1">ISO 9001:2015 - Cláusula 8</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Requisitos del Cliente"
          value={stats.requirements.total}
          subtitle={`${stats.requirements.pending_review} pendientes de revisión`}
          icon="📋"
          link="/operations/requirements"
          color="blue"
        />

        <StatCard
          title="Proyectos de Diseño"
          value={stats.design_projects.total}
          subtitle={`${stats.design_projects.active} activos`}
          icon="🎨"
          link="/operations/design-projects"
          color="purple"
        />

        <StatCard
          title="Proveedores Externos"
          value={stats.providers.total}
          subtitle={`${stats.providers.approved} aprobados`}
          icon="🏢"
          link="/operations/providers"
          color="green"
        />

        <StatCard
          title="No Conformidades"
          value={stats.nonconformities.total}
          subtitle={`${stats.nonconformities.open} abiertas, ${stats.nonconformities.critical} críticas`}
          icon="⚠️"
          link="/operations/nonconformities"
          color="red"
        />
      </div>

      {/* Alerts Section */}
      {stats.nonconformities.critical > 0 && (
        <div className="bg-gradient-to-br from-red-500/10 to-red-600/5 backdrop-blur-sm border border-red-500/20 rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">🚨</span>
            <h2 className="text-xl font-bold text-white">Atención Requerida</h2>
          </div>
          <p className="text-gray-300">
            Hay {stats.nonconformities.critical} no conformidad(es) crítica(s) que requieren atención inmediata.
          </p>
          <Link
            to="/operations/nonconformities"
            className="inline-block mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all"
          >
            Ver No Conformidades Críticas
          </Link>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Acciones Rápidas</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/operations/requirements/new"
            className="flex items-center space-x-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg hover:bg-blue-500/20 transition-all"
          >
            <span className="text-2xl">📋</span>
            <div>
              <p className="font-medium text-white">Nuevo Requisito</p>
              <p className="text-xs text-gray-400">Registrar requisito del cliente</p>
            </div>
          </Link>

          <Link
            to="/operations/nonconformities/new"
            className="flex items-center space-x-3 p-4 bg-red-500/10 border border-red-500/20 rounded-lg hover:bg-red-500/20 transition-all"
          >
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="font-medium text-white">Reportar NC</p>
              <p className="text-xs text-gray-400">Registrar no conformidad</p>
            </div>
          </Link>

          <Link
            to="/operations/releases/new"
            className="flex items-center space-x-3 p-4 bg-green-500/10 border border-green-500/20 rounded-lg hover:bg-green-500/20 transition-all"
          >
            <span className="text-2xl">✅</span>
            <div>
              <p className="font-medium text-white">Liberar Producto</p>
              <p className="text-xs text-gray-400">Autorizar liberación</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Module Links */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link
          to="/operations/releases"
          className="p-6 bg-gradient-to-br from-green-500/10 to-green-600/5 border border-green-500/20 rounded-lg hover:shadow-lg transition-all"
        >
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">📦</span>
            <h3 className="text-lg font-bold text-white">Liberación de Productos</h3>
          </div>
          <p className="text-sm text-gray-400">
            {stats.releases.pending} liberaciones pendientes de aprobación
          </p>
        </Link>

        <Link
          to="/operations/production"
          className="p-6 bg-gradient-to-br from-orange-500/10 to-orange-600/5 border border-orange-500/20 rounded-lg hover:shadow-lg transition-all"
        >
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">⚙️</span>
            <h3 className="text-lg font-bold text-white">Control de Producción</h3>
          </div>
          <p className="text-sm text-gray-400">Controles operacionales de producción</p>
        </Link>
      </div>
    </div>
  );
};

export default OperationsDashboard;
