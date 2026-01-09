import React, { useState, useEffect } from 'react';
import { Plus, RefreshCw, FileText, Upload as UploadIcon, Folder } from 'lucide-react';
import documentService from '../../services/documentService';
import DocumentList from './DocumentList';
import DocumentUploadForm from './DocumentUploadForm';

const DocumentDashboard = () => {
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [filterType, setFilterType] = useState('all');

  useEffect(() => {
    loadData();
  }, [filterType]);

  const loadData = async () => {
    setLoading(true);
    try {
      const params = filterType !== 'all' ? { type: filterType } : {};
      const [docsResponse, statsResponse] = await Promise.all([
        documentService.getAll(params),
        documentService.getStats()
      ]);

      setDocuments(docsResponse);
      setStats(statsResponse);
    } catch (error) {
      console.error('Error cargando documentos:', error);
      alert('Error al cargar los documentos');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (formData) => {
    setUploading(true);
    try {
      await documentService.upload(formData);
      
      alert('✅ Documento subido exitosamente');
      
      setShowUploadForm(false);
      await loadData();
    } catch (error) {
      console.error('Error subiendo documento:', error);
      alert('❌ Error al subir el documento. Por favor intenta nuevamente.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (document) => {
    if (!window.confirm(`¿Estás seguro de eliminar "${document.title}"?`)) {
      return;
    }

    try {
      await documentService.delete(document.id);
      
      alert('✅ Documento eliminado exitosamente');
      
      await loadData();
    } catch (error) {
      console.error('Error eliminando documento:', error);
      alert('❌ Error al eliminar el documento');
    }
  };

  const handleDownload = async (document) => {
    try {
      const blob = await documentService.download(document.id);
      
      // Crear URL para el blob
      const url = window.URL.createObjectURL(blob);
      
      // Crear elemento de descarga temporal
      const link = document.createElement('a');
      link.href = url;
      link.download = document.file_name || document.title;
      document.body.appendChild(link);
      link.click();
      
      // Limpiar
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error descargando documento:', error);
      alert('❌ Error al descargar el documento');
    }
  };

  const documentTypes = [
    { value: 'all', label: 'Todos' },
    { value: 'acta', label: 'Actas' },
    { value: 'reporte', label: 'Reportes' },
    { value: 'politica', label: 'Políticas' },
    { value: 'procedimiento', label: 'Procedimientos' },
    { value: 'otro', label: 'Otros' }
  ];

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Gestión de Documentos
        </h1>
        <p className="text-gray-600">
          Administra los documentos organizacionales para análisis del SGC
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Documentos</p>
              <p className="text-3xl font-bold text-blue-600">
                {stats?.total_documents || 0}
              </p>
            </div>
            <FileText className="h-10 w-10 text-blue-400" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Políticas</p>
              <p className="text-3xl font-bold text-purple-600">
                {stats?.by_type?.politica || 0}
              </p>
            </div>
            <Folder className="h-10 w-10 text-purple-400" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Procedimientos</p>
              <p className="text-3xl font-bold text-green-600">
                {stats?.by_type?.procedimiento || 0}
              </p>
            </div>
            <Folder className="h-10 w-10 text-green-400" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Reportes</p>
              <p className="text-3xl font-bold text-orange-600">
                {stats?.by_type?.reporte || 0}
              </p>
            </div>
            <UploadIcon className="h-10 w-10 text-orange-400" />
          </div>
        </div>
      </div>

      {/* Actions Bar */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowUploadForm(!showUploadForm)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="mr-2 h-4 w-4" />
              {showUploadForm ? 'Cancelar' : 'Subir Documento'}
            </button>

            <button
              onClick={loadData}
              className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Actualizar
            </button>
          </div>

          <div className="flex items-center space-x-3">
            <label className="text-sm text-gray-600">Filtrar por tipo:</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {documentTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Upload Form */}
      {showUploadForm && (
        <div className="mb-6">
          <DocumentUploadForm
            onUpload={handleUpload}
            onCancel={() => setShowUploadForm(false)}
            uploading={uploading}
          />
        </div>
      )}

      {/* Documents List */}
      <DocumentList
        documents={documents}
        loading={loading}
        onDelete={handleDelete}
        onDownload={handleDownload}
      />

      {/* Info Box */}
      {documents.length > 0 && (
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start">
            <FileText className="h-5 w-5 text-blue-500 mr-3 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-blue-900 mb-1">
                Análisis Automático con IA
              </h4>
              <p className="text-sm text-blue-700">
                Los documentos subidos pueden ser analizados automáticamente por el módulo SCA 
                (Smart Context Analyzer) para identificar fortalezas, debilidades, oportunidades 
                y amenazas de tu organización.
              </p>
              <a href="/context"
                className="text-sm text-blue-600 hover:text-blue-800 font-medium mt-2 inline-block">
                Ir a Análisis de Contexto →
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentDashboard;