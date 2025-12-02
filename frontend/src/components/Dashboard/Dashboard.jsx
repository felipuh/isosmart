import React from 'react';
import { Link } from 'react-router-dom';
import { Network, TrendingUp, FileText, Target, CheckCircle, AlertCircle } from 'lucide-react';

const Dashboard = () => {
  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Dashboard Principal
      </h1>
      <p className="text-gray-600 mb-8">
        Sistema Inteligente de Gobierno de Calidad ISO 9001:2015
      </p>

      {/* Módulos Principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        
        {/* SCA - Contexto */}
        <div className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <TrendingUp className="h-10 w-10 text-blue-500" />
            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">
              ACTIVO
            </span>
          </div>
          <h3 className="text-lg font-semibold mb-2">Análisis de Contexto</h3>
          <p className="text-sm text-gray-600 mb-4">ISO 4.1 - Módulo SCA</p>
          <div className="flex items-center text-sm text-gray-500 mb-4">
            <CheckCircle className="h-4 w-4 mr-1 text-green-500" />
            Smart Context Analyzer
          </div>
          <Link 
            to="/context" 
            className="block w-full text-center px-4 py-2 bg-blue-50 text-blue-600 rounded hover:bg-blue-100 transition-colors font-medium"
          >
            Ver Dashboard
          </Link>
        </div>

        {/* SIE - Stakeholders */}
        <div className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <Network className="h-10 w-10 text-green-500" />
            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">
              ACTIVO
            </span>
          </div>
          <h3 className="text-lg font-semibold mb-2">Stakeholders</h3>
          <p className="text-sm text-gray-600 mb-4">ISO 4.2 - Módulo SIE</p>
          <div className="flex items-center text-sm text-gray-500 mb-4">
            <CheckCircle className="h-4 w-4 mr-1 text-green-500" />
            Stakeholder Intelligence Engine
          </div>
          <Link 
            to="/stakeholders" 
            className="block w-full text-center px-4 py-2 bg-green-50 text-green-600 rounded hover:bg-green-100 transition-colors font-medium"
          >
            Ver Dashboard
          </Link>
        </div>

        {/* ASB - Alcance */}
        <div className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 opacity-75">
          <div className="flex items-center justify-between mb-4">
            <Target className="h-10 w-10 text-purple-400" />
            <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-semibold">
              PRÓXIMO
            </span>
          </div>
          <h3 className="text-lg font-semibold mb-2">Alcance SGC</h3>
          <p className="text-sm text-gray-600 mb-4">ISO 4.3 - Módulo ASB</p>
          <div className="flex items-center text-sm text-gray-500 mb-4">
            <AlertCircle className="h-4 w-4 mr-1" />
            AI Scope Builder
          </div>
          <button 
            disabled
            className="block w-full text-center px-4 py-2 bg-gray-100 text-gray-400 rounded cursor-not-allowed font-medium"
          >
            En desarrollo
          </button>
        </div>

        {/* SPM - Procesos */}
        <div className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 opacity-75">
          <div className="flex items-center justify-between mb-4">
            <FileText className="h-10 w-10 text-orange-400" />
            <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-semibold">
              PRÓXIMO
            </span>
          </div>
          <h3 className="text-lg font-semibold mb-2">Mapeo de Procesos</h3>
          <p className="text-sm text-gray-600 mb-4">ISO 4.4 - Módulo SPM</p>
          <div className="flex items-center text-sm text-gray-500 mb-4">
            <AlertCircle className="h-4 w-4 mr-1" />
            Smart Process Mapper
          </div>
          <button 
            disabled
            className="block w-full text-center px-4 py-2 bg-gray-100 text-gray-400 rounded cursor-not-allowed font-medium"
          >
            En desarrollo
          </button>
        </div>
      </div>

      {/* Resumen de Estado */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-6">Estado del Sistema</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-4xl font-bold text-blue-600 mb-2">2/4</div>
            <div className="text-sm text-gray-600">Módulos Activos</div>
          </div>

          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-4xl font-bold text-green-600 mb-2">50%</div>
            <div className="text-sm text-gray-600">Cláusula 4 Completada</div>
          </div>

          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-4xl font-bold text-purple-600 mb-2">AI</div>
            <div className="text-sm text-gray-600">Análisis Automatizado</div>
          </div>

          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <div className="text-4xl font-bold text-orange-600 mb-2">100%</div>
            <div className="text-sm text-gray-600">ISO 9001:2015</div>
          </div>
        </div>
      </div>

      {/* Acciones Rápidas */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg shadow-lg p-8 text-white">
        <h2 className="text-2xl font-semibold mb-6">Acciones Rápidas</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          
          <Link 
            to="/stakeholders"
            className="bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg p-5 transition-all flex items-center"
          >
            <Network className="h-8 w-8 mr-4" />
            <div>
              <div className="font-semibold text-lg">Analizar Stakeholders</div>
              <div className="text-sm text-blue-100">Ejecutar IA para identificar stakeholders críticos</div>
            </div>
          </Link>

          <Link 
            to="/context"
            className="bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg p-5 transition-all flex items-center"
          >
            <TrendingUp className="h-8 w-8 mr-4" />
            <div>
              <div className="font-semibold text-lg">Análisis de Contexto</div>
              <div className="text-sm text-blue-100">Revisar factores internos y externos</div>
            </div>
          </Link>
        </div>
      </div>

      {/* Footer Info */}
      <div className="mt-8 text-center text-gray-500 text-sm">
        <p>Sistema desarrollado bajo ISO 9001:2015 e ISO/IEC 42001:2023</p>
        <p className="mt-1">Módulos de IA: SCA ✓ | SIE ✓ | ASB (próximo) | SPM (próximo)</p>
      </div>
    </div>
  );
};

export default Dashboard;