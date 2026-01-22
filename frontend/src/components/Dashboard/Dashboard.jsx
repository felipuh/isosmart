import React, { useState, useEffect } from 'react';
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

const Dashboard = () => {
  const [stats, setStats] = useState({
    modulesActive: 4,
    totalModules: 4,
    clause4Progress: 100,
    iso9001Progress: 100,
    totalProcesses: 0,
    totalStakeholders: 0,
    lastUpdate: new Date().toISOString()
  });

  useEffect(() => {
    // Aquí podrías cargar stats reales desde la API
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      // Por ahora usamos datos estáticos
      // Podrías hacer llamadas a las APIs de cada módulo
      setStats({
        modulesActive: 4,
        totalModules: 4,
        clause4Progress: 100,
        iso9001Progress: 100,
        totalProcesses: 11,
        totalStakeholders: 0,
        lastUpdate: new Date().toISOString()
      });
    } catch (error) {
      console.error('Error cargando estadísticas:', error);
    }
  };

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
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
          Sistema Inteligente de Gestión de Calidad
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          ISO 9001:2015 | ISO/IEC 42001:2023
        </p>
      </div>

      {/* Celebración 100% */}
      <div className="mb-8 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center mb-2">
              <Award className="h-8 w-8 mr-3" />
              <h2 className="text-2xl font-bold">¡Cláusula 4 Completada al 100%!</h2>
            </div>
            <p className="text-green-100">
              Los 4 módulos de IA están activos y funcionando. Sistema de gestión base completo.
            </p>
          </div>
          <div className="text-right">
            <div className="text-6xl font-bold">100%</div>
            <div className="text-sm text-green-100">Contexto de la Organización</div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Módulos Activos</p>
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
                style={{ width: '100%' }}
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
              <p className="text-sm text-gray-600 dark:text-slate-400 mb-1">Análisis Ejecutados</p>
              <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">4</p>
            </div>
            <Activity className="h-12 w-12 text-orange-400" />
          </div>
          <div className="mt-2">
            <p className="text-xs text-gray-500">Todos los módulos inicializados</p>
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
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">4. Contexto de la Organización</span>
                <span className="text-sm font-bold text-green-600 dark:text-green-400">100%</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3">
                <div className="bg-green-500 dark:bg-green-600 h-3 rounded-full" style={{ width: '100%' }} />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">5. Liderazgo</span>
                <span className="text-sm font-bold text-slate-400 dark:text-slate-500">0%</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3">
                <div className="bg-slate-300 dark:bg-slate-600 h-3 rounded-full" style={{ width: '0%' }} />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">6. Planificación</span>
                <span className="text-sm font-bold text-slate-400 dark:text-slate-500">0%</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3">
                <div className="bg-slate-300 dark:bg-slate-600 h-3 rounded-full" style={{ width: '0%' }} />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">7-10. Otras Cláusulas</span>
                <span className="text-sm font-bold text-slate-400 dark:text-slate-500">0%</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3">
                <div className="bg-slate-300 dark:bg-slate-600 h-3 rounded-full" style={{ width: '0%' }} />
              </div>
            </div>
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
              <span className="text-sm font-bold text-gray-900 dark:text-slate-500">4/4</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600 dark:text-slate-400">Requisitos ISO Cubiertos</span>
              <span className="text-sm font-bold text-gray-900 dark:text-slate-500">4.1 - 4.4</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600 dark:text-slate-400">Procesos Mapeados</span>
              <span className="text-sm font-bold text-gray-900 dark:text-slate-500">11 procesos</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600 dark:text-slate-400">Dashboards Disponibles</span>
              <span className="text-sm font-bold text-gray-900 dark:text-slate-500">4 dashboards</span>
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