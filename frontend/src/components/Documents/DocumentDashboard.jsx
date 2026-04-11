import React, { useCallback, useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, RefreshCw, FileText, Upload as UploadIcon, Folder } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import documentService from '../../services/documentService';
import { showAlert, showConfirm } from '../../services/dialogs';
import DocumentList from './DocumentList';
import DocumentUploadForm from './DocumentUploadForm';

const DocumentDashboard = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [filterType, setFilterType] = useState('all');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params = filterType !== 'all' ? { type: filterType } : {};
      const [docsResponse, statsResponse] = await Promise.all([
        documentService.getAll(currentOrganization.id, params),
        documentService.getStats(currentOrganization.id)
      ]);

      setDocuments(docsResponse);
      setStats(statsResponse);
    } catch (error) {
      console.error('Error cargando documentos:', error);
      await showAlert(t('documentsManager.messages.errorLoading'), { icon: 'error' });
    } finally {
      setLoading(false);
    }
  }, [currentOrganization?.id, filterType, t]);

  useEffect(() => {
    if (currentOrganization?.id) {
      loadData();
    }
  }, [currentOrganization?.id, filterType, loadData]);

  const handleUpload = async (formData) => {
    setUploading(true);
    try {
      await documentService.upload(formData);

      await showAlert(t('documentsManager.messages.uploadSuccess'), { icon: 'success' });

      setShowUploadForm(false);
      await loadData();
    } catch (error) {
      console.error('Error subiendo documento:', error);
      await showAlert(t('documentsManager.messages.uploadError'), { icon: 'error' });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (doc) => {
    const confirmed = await showConfirm(t('documentsManager.messages.confirmDelete').replace('{title}', doc.title));
    if (!confirmed) {
      return;
    }

    try {
      await documentService.delete(doc.id);

      await showAlert(t('documentsManager.messages.deleteSuccess'), { icon: 'success' });

      await loadData();
    } catch (error) {
      console.error('Error eliminando documento:', error);
      await showAlert(t('documentsManager.messages.deleteError'), { icon: 'error' });
    }
  };

  const handleDownload = async (doc) => {
    try {
      const blob = await documentService.download(doc.id);

      // Crear URL para el blob
      const url = window.URL.createObjectURL(blob);

      // Crear elemento de descarga temporal
      const link = document.createElement('a');
      link.href = url;
      link.download = doc.file_name || doc.title;
      document.body.appendChild(link);
      link.click();

      // Limpiar
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error descargando documento:', error);
      await showAlert(t('documentsManager.messages.downloadError'), { icon: 'error' });
    }
  };

  const documentTypes = [
    { value: 'all', label: t('documentsManager.types.all') },
    { value: 'acta', label: t('documentsManager.types.minutePlural') },
    { value: 'reporte', label: t('documentsManager.types.reportPlural') },
    { value: 'política', label: t('documentsManager.types.policyPlural') },
    { value: 'procedimiento', label: t('documentsManager.types.procedurePlural') },
    { value: 'otro', label: t('documentsManager.types.otherPlural') }
  ];

  return (
    <div className="p-6 bg-slate-50 dark:bg-slate-900 min-h-screen transition-colors duration-300">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
          {t('documentsManager.dashboard.title')}
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          {t('documentsManager.dashboard.subtitle')}
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-md dark:backdrop-blur-md rounded-lg shadow dark:shadow-slate-900/50 border border-white/20 dark:border-slate-700/50 p-6 transition-all duration-300 hover:shadow-md dark:hover:shadow-slate-900/70">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">{t('documentsManager.dashboard.stats.total')}</p>
              <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {stats?.total_documents || 0}
              </p>
            </div>
            <FileText className="h-10 w-10 text-blue-400 dark:text-blue-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">{t('documentsManager.dashboard.stats.policies')}</p>
              <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                {stats?.by_type?.política || 0}
              </p>
            </div>
            <Folder className="h-10 w-10 text-purple-400 dark:text-purple-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">{t('documentsManager.dashboard.stats.procedures')}</p>
              <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                {stats?.by_type?.procedimiento || 0}
              </p>
            </div>
            <Folder className="h-10 w-10 text-green-400 dark:text-green-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">{t('documentsManager.dashboard.stats.reports')}</p>
              <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                {stats?.by_type?.reporte || 0}
              </p>
            </div>
            <UploadIcon className="h-10 w-10 text-orange-400 dark:text-orange-500" />
          </div>
        </div>
      </div>

      {/* Actions Bar */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-4 mb-6 transition-colors">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowUploadForm(!showUploadForm)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 transition-colors"
            >
              <Plus className="mr-2 h-4 w-4" />
              {showUploadForm ? t('common.buttons.cancel') : t('documentsManager.dashboard.actions.upload')}
            </button>

            <button
              onClick={loadData}
              className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              {t('documentsManager.dashboard.actions.refresh')}
            </button>
          </div>

          <div className="flex items-center space-x-3">
            <label className="text-sm text-slate-600 dark:text-slate-400 transition-colors">{t('documentsManager.dashboard.filterByType')}</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
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
        <div className="mt-6 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-4 transition-colors">
          <div className="flex items-start">
            <FileText className="h-5 w-5 text-blue-500 dark:text-blue-400 mr-3 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-1">
                {t('documentsManager.info.title')}
              </h4>
              <p className="text-sm text-blue-700 dark:text-blue-200">
                {t('documentsManager.info.description')}
              </p>
              <Link to="/context"
                className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium mt-2 inline-block transition-colors">
                {t('documentsManager.info.goToContext')}
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentDashboard;