import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Network, 
  TrendingUp, 
  Target, 
  Workflow, 
  CheckCircle2, 
  ArrowRight,
  Award,
  Activity,
  FileText,
  BarChart3
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

const Dashboard = () => {
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const [stats, setStats] = useState({
    modulesActive: 0,
    totalModules: 7,
    clause4Progress: 0,
    iso9001Progress: 0,
    totalProcesses: 0,
    totalStakeholders: 0,
    lastUpdate: new Date().toISOString(),
  });
  const [clauseProgress, setClauseProgress] = useState([]);

  const normalizeCount = (data) => {
    if (Array.isArray(data)) return data.length;
    if (Array.isArray(data?.results)) return data.results.length;
    if (typeof data?.count === 'number') return data.count;
    return 0;
  };

  const fetchCount = useCallback(async (endpoint) => {
    try {
      const response = await api.get(endpoint, { params: { organization_id: orgId } });
      return normalizeCount(response.data);
    } catch {
      return 0;
    }
  }, [orgId]);

  const loadDashboardStats = useCallback(async () => {
    if (!orgId) return;

    const clauseChecks = [
      { id: '4', label: '4. Contexto de la Organización', checks: ['/context/history/', '/stakeholders/stakeholders/', '/scope/scopes/', '/processes/maps/'] },
      { id: '5', label: '5. Liderazgo', checks: ['/leadership/policies/', '/leadership/commitments/', '/leadership/roles/'] },
      { id: '6', label: '6. Planificación', checks: ['/planning/risks-opportunities/', '/planning/objectives/', '/planning/actions/'] },
      { id: '7', label: '7. Apoyo', checks: ['/resources/resources/', '/resources/competences/', '/resources/trainings/'] },
      { id: '8', label: '8. Operación', checks: ['/operations/requirements/', '/operations/providers/', '/operations/nonconformities/'] },
      { id: '9', label: '9. Evaluación del Desempeño', checks: ['/performance/measurements/', '/performance/findings/', '/performance/reviews/'] },
      { id: '10', label: '10. Mejora', checks: ['/improvement/nonconformities/', '/improvement/corrective-actions/', '/improvement/continual-improvements/'] },
    ];

    const [processCount, stakeholderCount, clauseResults] = await Promise.all([
      fetchCount('/processes/maps/'),
      fetchCount('/stakeholders/stakeholders/'),
      Promise.all(
        clauseChecks.map(async (clause) => {
          const values = await Promise.all(clause.checks.map((endpoint) => fetchCount(endpoint)));
          const completed = values.filter((value) => value > 0).length;
          const progress = Math.round((completed / clause.checks.length) * 100);
          return { ...clause, progress };
        })
      ),
    ]);

    const iso9001Progress = clauseResults.length
      ? Math.round(clauseResults.reduce((acc, clause) => acc + clause.progress, 0) / clauseResults.length)
      : 0;

    setClauseProgress(clauseResults);
    setStats({
      modulesActive: clauseResults.filter((clause) => clause.progress > 0).length,
      totalModules: clauseResults.length,
      clause4Progress: clauseResults.find((clause) => clause.id === '4')?.progress || 0,
      iso9001Progress,
      totalProcesses: processCount,
      totalStakeholders: stakeholderCount,
      lastUpdate: new Date().toISOString(),
    });
  }, [fetchCount, orgId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadDashboardStats();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadDashboardStats]);

  const modules = [
    {
      id: 'sca',
      name: 'Smart Context Analyzer',
      code: 'SCA',
      iso: 'ISO 4.1',
      description: 'Análisis automático del contexto organizacional',
      icon: TrendingUp,
      color: 'bg-blue-500',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-700',
      route: '/context',
      status: 'active',
      features: ['Análisis FODA', 'Factores internos/externos', 'Riesgos identificados']
    },
    {
      id: 'sie',
      name: 'Stakeholder Intelligence Engine',
      code: 'SIE',
      iso: 'ISO 4.2',
      description: 'Gestión inteligente de partes interesadas',
      icon: Network,
      color: 'bg-green-500',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      textColor: 'text-green-700',
      route: '/stakeholders',
      status: 'active',
      features: ['Análisis de red', 'Matriz poder/interés', 'Stakeholders críticos']
    },
    {
      id: 'asb',
      name: 'AI Scope Builder',
      code: 'ASB',
      iso: 'ISO 4.3',
      description: 'Definición automática del alcance del SGC',
      icon: Target,
      color: 'bg-purple-500',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
      textColor: 'text-purple-700',
      route: '/scope',
      status: 'active',
      features: ['Alcance del SGC', 'Requisitos aplicables', 'Exclusiones justificadas']
    },
    {
      id: 'spm',
      name: 'Smart Process Mapper',
      code: 'SPM',
      iso: 'ISO 4.4',
      description: 'Mapeo inteligente de procesos organizacionales',
      icon: Workflow,
      color: 'bg-orange-500',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200',
      textColor: 'text-orange-700',
      route: '/processes',
      status: 'active',
      features: ['Mapa de procesos', 'Interacciones', 'Análisis de criticidad']
    }
  ];

  const quickActions = [
    {
      title: 'Analizar Contexto',
      description: 'Ejecutar análisis de contexto organizacional',
      icon: TrendingUp,
      route: '/context',
      color: 'bg-blue-500'
    },
    {
      title: 'Gestionar Stakeholders',
      description: 'Ver y analizar partes interesadas',
      icon: Network,
      route: '/stakeholders',
      color: 'bg-green-500'
    },
    {
      title: 'Definir Alcance',
      description: 'Revisar alcance del SGC',
      icon: Target,
      route: '/scope',
      color: 'bg-purple-500'
    },
    {
      title: 'Mapear Procesos',
      description: 'Ver mapa de procesos',
      icon: Workflow,
      route: '/processes',
      color: 'bg-orange-500'
    }
  ];

  return (
    <div className="p-6 bg-slate-50 dark:bg-slate-900 min-h-screen transition-colors duration-300">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
            Sistema Inteligente de Gestión de Calidad
          </h1>
          {user && (
            <div className="text-right">
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                {user.first_name} {user.last_name}
              </p>
              <p className="text-xs text-slate-500">
                Último acceso: {new Date().toLocaleDateString('es-ES')}
              </p>
            </div>
          )}
        </div>
        <p className="text-slate-600 dark:text-slate-400">
          {currentOrganization?.name || 'Cargando organización...'} | ISO 9001:2015 | ISO/IEC 42001:2023
        </p>
      </div>

      <div className="mb-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center mb-2">
              <Award className="h-8 w-8 mr-3" />
              <h2 className="text-2xl font-bold">Estado global de cumplimiento ISO 9001</h2>
            </div>
            <p className="text-blue-100">
              Progreso dinámico por cláusula según datos reales de cada módulo.
            </p>
          </div>
          <div className="text-right">
            <div className="text-6xl font-bold">{stats.iso9001Progress}%</div>
            <div className="text-sm text-blue-100">Promedio cláusulas 4-10</div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Cláusulas con avance</p>
              <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                {stats.modulesActive}/{stats.totalModules}
              </p>
            </div>
            <CheckCircle2 className="h-12 w-12 text-green-400" />
          </div>
          <div className="mt-4">
            <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
              <div
                className="bg-green-500 dark:bg-green-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${stats.totalModules ? Math.round((stats.modulesActive / stats.totalModules) * 100) : 0}%` }}
              />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Cláusula 4 ISO</p>
              <p className="text-3xl font-bold text-blue-600">{stats.clause4Progress}%</p>
            </div>
            <Target className="h-12 w-12 text-blue-400" />
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${stats.clause4Progress}%` }}
              />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Procesos Mapeados</p>
              <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">{stats.totalProcesses}</p>
            </div>
            <Workflow className="h-12 w-12 text-purple-400" />
          </div>
          <div className="mt-2">
            <p className="text-xs text-gray-500">3 Estratégicos • 3 Operativos • 5 Apoyo</p>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-slate-400 mb-1">Partes Interesadas</p>
              <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">{stats.totalStakeholders}</p>
            </div>
            <Activity className="h-12 w-12 text-orange-400" />
          </div>
          <div className="mt-2">
            <p className="text-xs text-gray-500">Registros activos de stakeholders</p>
          </div>
        </div>
      </div>

      {/* Módulos Grid */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">Módulos del Sistema</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {modules.map((module) => {
            const Icon = module.icon;
            return (
              <Link
                key={module.id}
                to={module.route}
                className={`${module.bgColor} dark:bg-slate-800 ${module.borderColor} dark:border-slate-700 border-2 rounded-lg p-6 hover:shadow-lg dark:hover:shadow-slate-900/50 transition-all duration-200 hover:scale-105`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className={`${module.color} p-3 rounded-lg mr-4`}>
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-slate-900 dark:text-white">{module.name}</h3>
                      <p className="text-sm text-slate-600 dark:text-slate-400">{module.code} • {module.iso}</p>
                    </div>
                  </div>
                  <span className="flex items-center text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 px-2 py-1 rounded-full font-semibold">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    ACTIVO
                  </span>
                </div>
                
                <p className="text-sm text-slate-700 dark:text-slate-300 mb-4">{module.description}</p>
                
                <div className="space-y-2">
                  {module.features.map((feature, idx) => (
                    <div key={idx} className="flex items-center text-sm text-slate-600 dark:text-slate-400">
                      <CheckCircle2 className="h-4 w-4 text-green-500 dark:text-green-400 mr-2" />
                      {feature}
                    </div>
                  ))}
                </div>

                <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between">
                  <span className={`text-sm font-semibold ${module.textColor}`}>
                    Ver Dashboard
                  </span>
                  <ArrowRight className={`h-5 w-5 ${module.textColor}`} />
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Acciones Rápidas</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 dark:text-white gap-4">
          {quickActions.map((action, idx) => {
            const Icon = action.icon;
            return (
              <Link
                key={idx}
                to={action.route}
                className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-4 hover:shadow-lg transition-shadow"
              >
                <div className={`${action.color} w-10 h-10 rounded-lg flex items-center justify-center mb-3`}>
                  <Icon className="h-5 w-5 text-white" />
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">{action.title}</h3>
                <p className="text-sm text-gray-600 dark:text-slate-400">{action.description}</p>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Progress Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center">
            <BarChart3 className="h-5 w-5 mr-2 text-blue-500" />
            Progreso por Cláusula ISO 9001:2015
          </h3>
          <div className="space-y-4">
            {clauseProgress.map((clause) => (
              <div key={clause.id}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{clause.label}</span>
                  <span className="text-sm font-bold text-blue-600 dark:text-blue-400">{clause.progress}%</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3">
                  <div className="bg-blue-500 dark:bg-blue-600 h-3 rounded-full" style={{ width: `${clause.progress}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center">
            <FileText className="h-5 w-5 mr-2 text-purple-500" />
            Resumen del Sistema
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-700">
              <span className="text-sm text-slate-600 dark:text-slate-400">Módulos de IA Activos</span>
              <span className="text-sm font-bold text-gray-900 dark:text-slate-500">{stats.modulesActive}/{stats.totalModules}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600 dark:text-slate-400">Requisitos ISO Cubiertos</span>
              <span className="text-sm font-bold text-gray-900 dark:text-slate-500">4 - 10 (progreso dinámico)</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600 dark:text-slate-400">Procesos Mapeados</span>
              <span className="text-sm font-bold text-gray-900 dark:text-slate-500">{stats.totalProcesses} procesos</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600 dark:text-slate-400">Cumplimiento ISO 9001</span>
              <span className="text-sm font-bold text-gray-900 dark:text-slate-500">{stats.iso9001Progress}%</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-gray-600 dark:text-slate-400">Estado del Sistema</span>
              <span className="text-sm font-bold text-green-600">✓ Operacional</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-1">ISO Smart v1.0</h3>
            <p className="text-sm text-gray-600 dark:text-slate-400">
              Sistema Inteligente de Gestión de Calidad con IA
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600 dark:text-slate-400">Última actualización</p>
            <p className="text-sm font-medium text-gray-900 dark:text-slate-500">
              {new Date(stats.lastUpdate).toLocaleDateString('es-ES', {
                day: '2-digit',
                month: 'long',
                year: 'numeric'
              })}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;