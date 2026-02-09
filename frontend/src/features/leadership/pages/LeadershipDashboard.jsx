// features/leadership/pages/LeadershipDashboard.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getPolicies, getRoles, getCommitments } from '../api/leadershipApi';

const LeadershipDashboard = () => {
  const [stats, setStats] = useState({
    policies: { total: 0, active: 0, draft: 0 },
    roles: { total: 0, assigned: 0 },
    commitments: { total: 0, completed: 0, pending: 0 }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Cargar políticas
      const policiesData = await getPolicies();
      const policies = Array.isArray(policiesData) ? policiesData : policiesData.results || [];
      
      // Cargar roles
      const rolesData = await getRoles();
      const roles = Array.isArray(rolesData) ? rolesData : rolesData.results || [];
      
      // Cargar compromisos
      const commitmentsData = await getCommitments();
      const commitments = Array.isArray(commitmentsData) ? commitmentsData : commitmentsData.results || [];
      
      setStats({
        policies: {
          total: policies.length,
          active: policies.filter(p => p.status === 'active').length,
          draft: policies.filter(p => p.status === 'draft').length
        },
        roles: {
          total: roles.length,
          assigned: roles.filter(r => r.is_active).length
        },
        commitments: {
          total: commitments.length,
          completed: commitments.filter(c => c.status === 'completed').length,
          pending: commitments.filter(c => c.status === 'planned' || c.status === 'in_progress').length
        }
      });
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const colorMap = {
    blue: {
      gradient: 'from-blue-500/10 to-blue-600/5',
      border: 'border-blue-500/20',
      text: 'text-blue-400',
      shadow: 'hover:shadow-blue-500/20'
    },
    purple: {
      gradient: 'from-purple-500/10 to-purple-600/5',
      border: 'border-purple-500/20',
      text: 'text-purple-400',
      shadow: 'hover:shadow-purple-500/20'
    },
    green: {
      gradient: 'from-green-500/10 to-green-600/5',
      border: 'border-green-500/20',
      text: 'text-green-400',
      shadow: 'hover:shadow-green-500/20'
    },
    orange: {
      gradient: 'from-orange-500/10 to-orange-600/5',
      border: 'border-orange-500/20',
      text: 'text-orange-400',
      shadow: 'hover:shadow-orange-500/20'
    }
  };

  const StatCard = ({ title, value, subtitle, icon, link, color = 'blue' }) => {
    const palette = colorMap[color] || colorMap.blue;

    return (
    <Link to={link} className="block">
      <div className={`bg-gradient-to-br ${palette.gradient} backdrop-blur-sm border ${palette.border} rounded-lg p-6 hover:shadow-lg ${palette.shadow} transition-all duration-300`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-400">{title}</h3>
          <span className="text-2xl">{icon}</span>
        </div>
        <div className="flex items-baseline">
          <p className={`text-3xl font-bold ${palette.text}`}>{value}</p>
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
    <div className="space-y-6" style={{ fontFamily: '"Sora", "Work Sans", sans-serif' }}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Liderazgo y Compromiso</h1>
          <p className="text-gray-400 mt-1">ISO 9001:2015 - Cláusula 5</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Políticas Totales"
          value={stats.policies.total}
          subtitle={`${stats.policies.active} activas, ${stats.policies.draft} borradores`}
          icon="📋"
          link="/leadership/policies"
          color="blue"
        />
        
        <StatCard
          title="Roles Organizacionales"
          value={stats.roles.total}
          subtitle={`${stats.roles.assigned} asignados`}
          icon="👥"
          link="/leadership/roles"
          color="purple"
        />
        
        <StatCard
          title="Compromisos"
          value={stats.commitments.total}
          subtitle={`${stats.commitments.completed} completados, ${stats.commitments.pending} pendientes`}
          icon="✅"
          link="/leadership/commitments"
          color="green"
        />
        
        <StatCard
          title="Matrices RACI"
          value="Ver todas"
          subtitle="Responsabilidades y autoridades"
          icon="📊"
          link="/leadership/raci"
          color="orange"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Acciones Rápidas</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/leadership/policies/new"
            className="flex items-center space-x-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg hover:bg-blue-500/20 transition-all"
          >
            <span className="text-2xl">📝</span>
            <div>
              <p className="font-medium text-white">Nueva Política</p>
              <p className="text-xs text-gray-400">Crear política de calidad</p>
            </div>
          </Link>
          
          <Link
            to="/leadership/roles/new"
            className="flex items-center space-x-3 p-4 bg-purple-500/10 border border-purple-500/20 rounded-lg hover:bg-purple-500/20 transition-all"
          >
            <span className="text-2xl">👤</span>
            <div>
              <p className="font-medium text-white">Nuevo Rol</p>
              <p className="text-xs text-gray-400">Definir rol organizacional</p>
            </div>
          </Link>
          
          <Link
            to="/leadership/raci/new"
            className="flex items-center space-x-3 p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg hover:bg-orange-500/20 transition-all"
          >
            <span className="text-2xl">📋</span>
            <div>
              <p className="font-medium text-white">Nueva Matriz RACI</p>
              <p className="text-xs text-gray-400">Crear matriz de responsabilidades</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Actividad Reciente</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
            <div className="flex items-center space-x-3">
              <span className="text-blue-400">📋</span>
              <div>
                <p className="text-sm font-medium text-white">Política de Calidad v1.0</p>
                <p className="text-xs text-gray-400">Creada hace 2 horas</p>
              </div>
            </div>
            <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs rounded">Borrador</span>
          </div>
          
          <div className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
            <div className="flex items-center space-x-3">
              <span className="text-purple-400">👥</span>
              <div>
                <p className="text-sm font-medium text-white">Director de Calidad</p>
                <p className="text-xs text-gray-400">Rol creado hace 1 día</p>
              </div>
            </div>
            <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded">Activo</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeadershipDashboard;
