import React, { useState, useEffect } from 'react';
import { RefreshCw, Download, PlayCircle, FileText } from 'lucide-react';
import scopeService from '../../services/scopeService';
import ScopeStatement from './ScopeStatement';
import OrganizationalBoundaries from './OrganizationalBoundaries';
import ISORequirements from './ISORequirements';
import CoverageAnalysis from './CoverageAnalysis';
import ScopeProcessList from './ScopeProcessList';
import ProcessScopeForm from './ProcessScopeForm';
import LocationScopeForm from './LocationScopeForm';

const ScopeDashboard = () => {
  const [scopeData, setScopeData] = useState(null);
  const [stats, setStats] = useState(null);
  const [processes, setProcesses] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [showProcessForm, setShowProcessForm] = useState(false);
  const [showLocationForm, setShowLocationForm] = useState(false);
  const [editingProcess, setEditingProcess] = useState(null);
  const [editingLocation, setEditingLocation] = useState(null);
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
        // Cargar procesos y ubicaciones si hay un scope activo
        if (latestResponse.data?.id) {
          const [procs, locs] = await Promise.all([
            scopeService.getProcesses(latestResponse.data.id),
            scopeService.getLocations(latestResponse.data.id)
          ]);
          setProcesses(Array.isArray(procs) ? procs : procs.results || []);
          setLocations(Array.isArray(locs) ? locs : locs.results || []);
        }
      }
      setStats(statsResponse);
    } catch (error) {
      console.error('Error cargando datos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    const cleanProducts = analysisConfig.products_services.filter(p => p.trim() !== '');
    
    if (cleanProducts.length === 0) {
      alert('Debes agregar al menos un producto o servicio');
      return;
    }

    setAnalyzing(true);
    try {
      const result = await scopeService.runAnalysis({
        products_services: cleanProducts,
        has_design: analysisConfig.has_design
      });

      if (result.status === 'success') {
        await loadData();
        setShowConfig(false);
        alert('Análisis de alcance completado!\n\n' +
              'Productos/Servicios: ' + result.products_count + '\n' +
              'Exclusiones: ' + result.exclusions_count + '\n' +
              'Cobertura: ' + (result.coverage_score?.toFixed(1) || 0) + '%');
      } else {
        alert(result.message);
      }
    } catch (error) {
      console.error('Error ejecutando análisis:', error);
      alert('Error al ejecutar el análisis de alcance');
    } finally {
      setAnalyzing(false);
    }
  };

  // Handlers para Procesos
  const handleAddProcess = () => {
    setEditingProcess(null);
    setShowProcessForm(true);
  };

  const handleEditProcess = (process) => {
    setEditingProcess(process);
    setShowProcessForm(true);
  };

  const handleSaveProcess = async (formData) => {
    try {
      if (editingProcess) {
        await scopeService.updateProcess(editingProcess.id, formData);
        alert('Proceso actualizado exitosamente');
      } else {
        await scopeService.createProcess(formData);
        alert('Proceso creado exitosamente');
      }
      setShowProcessForm(false);
      setEditingProcess(null);
      await loadData();
    } catch (error) {
      console.error('Error guardando proceso:', error);
      alert('Error al guardar el proceso');
      throw error;
    }
  };

  const handleDeleteProcess = async (process) => {
    if (!window.confirm('¿Estás seguro de eliminar el proceso "' + process.process_name + '"?')) {
      return;
    }
    try {
      await scopeService.deleteProcess(process.id);
      alert('Proceso eliminado exitosamente');
      await loadData();
    } catch (error) {
      console.error('Error eliminando proceso:', error);
      alert('Error al eliminar el proceso');
    }
  };

  // Handlers para Ubicaciones
  const handleAddLocation = () => {
    setEditingLocation(null);
    setShowLocationForm(true);
  };

  const handleEditLocation = (location) => {
    setEditingLocation(location);
    setShowLocationForm(true);
  };

  const handleSaveLocation = async (formData) => {
    try {
      if (editingLocation) {
        await scopeService.updateLocation(editingLocation.id, formData);
        alert('Ubicación actualizada exitosamente');
      } else {
        await scopeService.createLocation(formData);
        alert('Ubicación creada exitosamente');
      }
      setShowLocationForm(false);
      setEditingLocation(null);
      await loadData();
    } catch (error) {
      console.error('Error guardando ubicación:', error);
      alert('Error al guardar la ubicación');
      throw error;
    }
  };

  const handleDeleteLocation = async (location) => {
    if (!window.confirm('¿Estás seguro de eliminar la ubicación "' + location.location_name + '"?')) {
      return;
    }
    try {
      await scopeService.deleteLocation(location.id);
      alert('Ubicación eliminada exitosamente');
      await loadData();
    } catch (error) {
      console.error('Error eliminando ubicación:', error);
      alert('Error al eliminar la ubicación');
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
    <div className="p-6 bg-slate-50 dark:bg-slate-900 min-h-screen transition-colors duration-300">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
          Definición del Alcance del SGC
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          ISO 4.3 - Determinación del alcance del sistema de gestión de calidad
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-md dark:backdrop-blur-md rounded-lg shadow dark:shadow-slate-900/50 border border-white/20 dark:border-slate-700/50 p-6 transition-all duration-300 hover:shadow-md dark:hover:shadow-slate-900/70">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Alcances Definidos</p>
              <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {stats?.total_definitions || 0}
              </p>
            </div>
            <FileText className="h-10 w-10 text-blue-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Procesos</p>
              <p className="text-3xl font-bold text-green-600">
                {processes.length}
              </p>
            </div>
            <PlayCircle className="h-10 w-10 text-green-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Ubicaciones</p>
              <p className="text-3xl font-bold text-orange-600">
                {locations.length}
              </p>
            </div>
            <FileText className="h-10 w-10 text-orange-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Cobertura</p>
              <p className="text-3xl font-bold text-purple-600">
                {scopeData?.coverage_percentage?.toFixed(0) || 0}%
              </p>
            </div>
            <RefreshCw className="h-10 w-10 text-purple-400" />
          </div>
        </div>
      </div>

      {/* Actions Bar */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-4 mb-6 transition-colors">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowConfig(!showConfig)}
              disabled={analyzing}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
            >
              <PlayCircle className={'mr-2 h-4 w-4 ' + (analyzing ? 'animate-spin' : '')} />
              {analyzing ? 'Analizando...' : 'Definir Alcance con IA'}
            </button>

            <button
              onClick={loadData}
              className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Actualizar
            </button>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-sm text-slate-600 dark:text-slate-400">
              Última actualización: {formatDate(scopeData?.updated_at)}
            </span>
            <button className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors">
              <Download className="mr-2 h-4 w-4" />
              Exportar
            </button>
          </div>
        </div>
      </div>

      {/* Configuration Panel */}
      {showConfig && (
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 mb-6 transition-colors">
          <h3 className="text-lg font-semibold mb-4 dark:text-white">Configuración del Análisis</h3>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Productos y Servicios
            </label>
            {analysisConfig.products_services.map((product, index) => (
              <div key={index} className="flex items-center space-x-2 mb-2">
                <input
                  type="text"
                  value={product}
                  onChange={(e) => updateProduct(index, e.target.value)}
                  placeholder="Ej: Consultoría en gestión de calidad"
                  className="flex-1 px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                />
                {analysisConfig.products_services.length > 1 && (
                  <button
                    onClick={() => removeProduct(index)}
                    className="px-3 py-2 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
            <button
              onClick={addProductField}
              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
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
                className="mr-2 accent-blue-600"
              />
              <span className="text-sm text-slate-700 dark:text-slate-300">
                La organización realiza actividades de diseño y desarrollo
              </span>
            </label>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleRunAnalysis}
              disabled={analyzing}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
            >
              {analyzing ? 'Procesando...' : 'Ejecutar Análisis'}
            </button>
            <button
              onClick={() => setShowConfig(false)}
              className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
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

        {/* Procesos y Ubicaciones */}
        <ScopeProcessList
          processes={processes}
          locations={locations}
          loading={loading}
          onAddProcess={handleAddProcess}
          onEditProcess={handleEditProcess}
          onDeleteProcess={handleDeleteProcess}
          onAddLocation={handleAddLocation}
          onEditLocation={handleEditLocation}
          onDeleteLocation={handleDeleteLocation}
        />

        {/* Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <OrganizationalBoundaries 
            boundaries={scopeData?.organizational_boundaries} 
            loading={loading}
          />
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

      {/* Modales */}
      {showProcessForm && (
        <ProcessScopeForm
          process={editingProcess}
          scopeId={scopeData?.id}
          onSave={handleSaveProcess}
          onClose={() => { setShowProcessForm(false); setEditingProcess(null); }}
        />
      )}

      {showLocationForm && (
        <LocationScopeForm
          location={editingLocation}
          scopeId={scopeData?.id}
          onSave={handleSaveLocation}
          onClose={() => { setShowLocationForm(false); setEditingLocation(null); }}
        />
      )}
    </div>
  );
};

export default ScopeDashboard;