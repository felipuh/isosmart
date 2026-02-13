// features/performance/pages/PerformanceDashboard.jsx
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import {
  getIndicators,
  getMeasurements,
  getMeasurementStats,
  getAudits,
  getFindings,
  getReviews
} from '../api/performanceApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const PerformanceDashboard = () => {
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;

  const statColors = {
    blue: {
      card: 'from-blue-500/10 to-blue-600/5 border-blue-500/20 hover:shadow-blue-500/20',
      value: 'text-blue-400'
    },
    green: {
      card: 'from-green-500/10 to-green-600/5 border-green-500/20 hover:shadow-green-500/20',
      value: 'text-green-400'
    },
    orange: {
      card: 'from-orange-500/10 to-orange-600/5 border-orange-500/20 hover:shadow-orange-500/20',
      value: 'text-orange-400'
    },
    red: {
      card: 'from-red-500/10 to-red-600/5 border-red-500/20 hover:shadow-red-500/20',
      value: 'text-red-400'
    }
  };

  const [stats, setStats] = useState({
    indicators: { total: 0, active: 0 },
    measurements: { total: 0, on_target: 0, needs_attention: 0 },
    audits: { total: 0, planned: 0 },
    findings: { total: 0, open: 0 },
    reviews: { total: 0, scheduled: 0 }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (orgId) loadDashboardData();
  }, [orgId]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [
        indicatorsData,
        measurementsData,
        auditsData,
        findingsData,
        reviewsData,
        measurementStats
      ] = await Promise.all([
        getIndicators({ organization_id: orgId }),
        getMeasurements({ organization_id: orgId }),
        getAudits({ organization_id: orgId }),
        getFindings({ organization_id: orgId }),
        getReviews({ organization_id: orgId }),
        getMeasurementStats(orgId)
      ]);

      const indicators = normalizeList(indicatorsData);
      const measurements = normalizeList(measurementsData);
      const audits = normalizeList(auditsData);
      const findings = normalizeList(findingsData);
      const reviews = normalizeList(reviewsData);

      setStats({
        indicators: {
          total: indicators.length,
          active: indicators.filter(i => i.status === 'active').length
        },
        measurements: {
          total: measurements.length,
          on_target: measurementStats?.on_target ?? measurements.filter(m => m.status === 'on_target').length,
          needs_attention: measurementStats?.needs_attention ?? measurements.filter(m => m.status === 'needs_attention').length
        },
        audits: {
          total: audits.length,
          planned: audits.filter(a => a.status === 'planned').length
        },
        findings: {
          total: findings.length,
          open: findings.filter(f => f.status === 'open').length
        },
        reviews: {
          total: reviews.length,
          scheduled: reviews.filter(r => r.status === 'scheduled').length
        }
      });
    } catch (error) {
      console.error('Error loading performance dashboard:', error);
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
          <h1 className="text-3xl font-bold text-white">Evaluacion del Desempeno</h1>
          <p className="text-gray-400 mt-1">ISO 9001:2015 - Clausula 9</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Indicadores"
          value={stats.indicators.total}
          subtitle={`${stats.indicators.active} activos`}
          icon="🎯"
          link="/performance/indicators"
          color="blue"
        />

        <StatCard
          title="Mediciones"
          value={stats.measurements.total}
          subtitle={`${stats.measurements.on_target} en objetivo, ${stats.measurements.needs_attention} requieren atencion`}
          icon="📈"
          link="/performance/measurements"
          color="green"
        />

        <StatCard
          title="Auditorias"
          value={stats.audits.total}
          subtitle={`${stats.audits.planned} planificadas`}
          icon="🧾"
          link="/performance/audits"
          color="orange"
        />

        <StatCard
          title="Hallazgos"
          value={stats.findings.total}
          subtitle={`${stats.findings.open} abiertos`}
          icon="🔎"
          link="/performance/findings"
          color="red"
        />
      </div>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Acciones Rapidas</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/performance/indicators"
            className="flex items-center space-x-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg hover:bg-blue-500/20 transition-all"
          >
            <span className="text-2xl">🎯</span>
            <div>
              <p className="font-medium text-white">Nuevo Indicador</p>
              <p className="text-xs text-gray-400">Define KPI y objetivos</p>
            </div>
          </Link>

          <Link
            to="/performance/measurements"
            className="flex items-center space-x-3 p-4 bg-green-500/10 border border-green-500/20 rounded-lg hover:bg-green-500/20 transition-all"
          >
            <span className="text-2xl">📈</span>
            <div>
              <p className="font-medium text-white">Registrar Medicion</p>
              <p className="text-xs text-gray-400">Capturar resultados</p>
            </div>
          </Link>

          <Link
            to="/performance/audits"
            className="flex items-center space-x-3 p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg hover:bg-orange-500/20 transition-all"
          >
            <span className="text-2xl">🧾</span>
            <div>
              <p className="font-medium text-white">Planificar Auditoria</p>
              <p className="text-xs text-gray-400">Programar y dar seguimiento</p>
            </div>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Link
          to="/performance/analyses"
          className="p-6 bg-gradient-to-br from-indigo-500/10 to-indigo-600/5 border border-indigo-500/20 rounded-lg hover:shadow-lg transition-all"
        >
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">🧠</span>
            <h3 className="text-lg font-bold text-white">Analisis</h3>
          </div>
          <p className="text-sm text-gray-400">Tendencias y causas raiz</p>
        </Link>

        <Link
          to="/performance/reviews"
          className="p-6 bg-gradient-to-br from-teal-500/10 to-teal-600/5 border border-teal-500/20 rounded-lg hover:shadow-lg transition-all"
        >
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">📋</span>
            <h3 className="text-lg font-bold text-white">Revision por la Direccion</h3>
          </div>
          <p className="text-sm text-gray-400">Reuniones de revision gerencial</p>
        </Link>

        <Link
          to="/performance/findings"
          className="p-6 bg-gradient-to-br from-rose-500/10 to-rose-600/5 border border-rose-500/20 rounded-lg hover:shadow-lg transition-all"
        >
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">🔎</span>
            <h3 className="text-lg font-bold text-white">Hallazgos de Auditoria</h3>
          </div>
          <p className="text-sm text-gray-400">Seguimiento de hallazgos</p>
        </Link>
      </div>
    </div>
  );
};

export default PerformanceDashboard;
