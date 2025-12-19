import React, { useState, useEffect } from 'react';
import { RefreshCw, Download, PlayCircle, FileText } from 'lucide-react';
import scopeService from '../../services/scopeService';
import ScopeStatement from './ScopeStatement';
import OrganizationalBoundaries from './OrganizationalBoundaries';
import ISORequirements from './ISORequirements';
import CoverageAnalysis from './CoverageAnalysis';

const ScopeDashboard = () => {
  const [scopeData, setScopeData] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [analysisConfig, setAnalysisConfig] = useState({
    products_services: [''],
    has_design: false
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [latestResponse, statsResponse] = await Promise.all([
        scopeService.getLatest(),
        scopeService.getStats()
      ]);

      if (latestResponse.status === 'success') {
        setScopeData(latestResponse.data);
      }
      setStats(statsResponse);
    } catch (error) {
      console.error('Error cargando datos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    // Limpiar campos vacíos
    const cleanProducts = analysisConfig.products_services.filter(p => p.trim() !== '');
    
    if (cleanProducts.length === 0) {
      alert('⚠️ Debes agregar al menos un producto o servicio');
      return;
    }

    setAnalyzing(true);
    try {
      const result = await scopeService.runAnalysis({
        products_services: cleanProducts,
        has_design: analysisConfig.has_design
      });

      console.log('Análisis completado:', result);

      if (result.status === 'success') {
        await loadData();
        setShowConfig(false);
        
        alert(`✅ Análisis de alcance completado!\n\n` +
              `Productos/Servicios: ${result.products_count}\n` +
              `Exclusiones: ${result.exclusions_count}\n` +
              `Cobertura: ${result.coverage_score?.toFixed(1)}%`);
      } else {
        alert(`⚠️ ${result.message}`);
      }
    } catch (error) {
      console.error('Error ejecutando análisis:', error);
      alert('❌ Error al ejecutar el análisis de alcance');
    } finally {
      setAnalyzing(false);
    }
  };

  const addProductField = () => {
    setAnalysisConfig(prev => ({
      ...prev,
      products_services: [...prev.products_services, '']
    }));
  };

  const updateProduct = (index, value) => {
    setAnalysisConfig(prev => ({
      ...prev,
      products_services: prev.products_services.map((p, i) => i === index ? value : p)
    }));
  };

  const removeProduct = (index) => {
    setAnalysisConfig(prev => ({
      ...prev,
      products_services: prev.products_services.filter((_, i) => i !== index)
    }));
  };

  const formatDate = (date) => {
    if (!date) return 'No disponible';
    return new Intl.DateTimeFormat('es-ES', {
      day: '2-digit',
      month: 'long',
      year: 'numeric'
    }).format(new Date(date));
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Definición del Alcance del SGC
        </h1>
        <p className="text-gray-600">
          ISO 4.3 - Determinación del alcance del sistema de gestión de calidad
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Alcances Definidos</p>
              <p className="text-3xl font-bold text-blue-600">
                {stats?.total_definitions || 0}
              </p>
            </div>
            <FileText className="h-10 w-10 text-blue-400" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Productos/Servicios</p>
              <p className="text-3xl font-bold text-green-600">
                {scopeData?.total_products_count || 0}
              </p>
            </div>
            <PlayCircle className="h-10 w-10 text-green-400" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Exclusiones</p>
              <p className="text-3xl font-bold text-orange-600">
                {scopeData?.total_exclusions_count || 0}
              </p>
            </div>
            <FileText className="h-10 w-10 text-orange-400" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Cobertura</p>
              <p className="text-3xl font-bold text-purple-600">
                {scopeData?.coverage_percentage?.toFixed(0) || 0}%
              </p>
            </div>
            <RefreshCw className="h-10 w-10 text-purple-400" />
          </div>
        </div>
      </div>

      {/* Actions Bar */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowConfig(!showConfig)}
              disabled={analyzing}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
            >
              <PlayCircle className={`mr-2 h-4 w-4 ${analyzing ? 'animate-spin' : ''}`} />
              {analyzing ? 'Analizando...' : 'Definir Alcance con IA'}
            </button>

            <button
              onClick={loadData}
              className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Actualizar
            </button>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">
              Última actualización: {formatDate(scopeData?.updated_at)}
            </span>
            <button className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
              <Download className="mr-2 h-4 w-4" />
              Exportar
            </button>
          </div>
        </div>
      </div>

      {/* Configuration Panel */}
      {showConfig && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Configuración del Análisis</h3>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Productos y Servicios
            </label>
            {analysisConfig.products_services.map((product, index) => (
              <div key={index} className="flex items-center space-x-2 mb-2">
                <input
                  type="text"
                  value={product}
                  onChange={(e) => updateProduct(index, e.target.value)}
                  placeholder="Ej: Consultoría en gestión de calidad"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {analysisConfig.products_services.length > 1 && (
                  <button
                    onClick={() => removeProduct(index)}
                    className="px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
            <button
              onClick={addProductField}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              + Agregar producto/servicio
            </button>
          </div>

          <div className="mb-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={analysisConfig.has_design}
                onChange={(e) => setAnalysisConfig(prev => ({ ...prev, has_design: e.target.checked }))}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">
                La organización realiza actividades de diseño y desarrollo
              </span>
            </label>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleRunAnalysis}
              disabled={analyzing}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300"
            >
              {analyzing ? 'Procesando...' : 'Ejecutar Análisis'}
            </button>
            <button
              onClick={() => setShowConfig(false)}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="space-y-6">
        {/* Declaración de Alcance */}
        <ScopeStatement scopeData={scopeData} loading={loading} />

        {/* Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Límites Organizacionales */}
          <OrganizationalBoundaries 
            boundaries={scopeData?.organizational_boundaries} 
            loading={loading}
          />

          {/* Análisis de Cobertura */}
          <CoverageAnalysis 
            coverageData={scopeData?.coverage_analysis} 
            loading={loading}
          />
        </div>

        {/* Requisitos ISO */}
        <ISORequirements 
          requirements={scopeData?.applicable_requirements} 
          loading={loading}
        />
      </div>
    </div>
  );
};

export default ScopeDashboard;