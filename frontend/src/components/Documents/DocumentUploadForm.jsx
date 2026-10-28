import React, { useState } from 'react';
import { Upload, X, File, AlertCircle } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const DocumentUploadForm = ({ onUpload, onCancel, uploading }) => {
  const { t } = useI18n();
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    document_type: 'otro',
    source: ''
  });
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validar tamaño (10MB)
      if (file.size > 10 * 1024 * 1024) {
        setError(t('documentsManager.upload.errors.fileTooLarge').replace('{size}', '10MB'));
        return;
      }

      // Validar extensión
      const validExtensions = ['pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls'];
      const extension = file.name.split('.').pop().toLowerCase();
      if (!validExtensions.includes(extension)) {
        setError(
          t('documentsManager.upload.errors.invalidType').replace('{extensions}', validExtensions.join(', '))
        );
        return;
      }

      setSelectedFile(file);
      setError('');
      
      // Auto-llenar título si está vacío
      if (!formData.title) {
        setFormData(prev => ({
          ...prev,
          title: file.name.replace(/\.[^/.]+$/, '')
        }));
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!selectedFile) {
      setError(t('documentsManager.upload.errors.fileRequired'));
      return;
    }

    if (!formData.title.trim()) {
      setError(t('documentsManager.upload.errors.titleRequired'));
      return;
    }

    const uploadData = new FormData();
    uploadData.append('file', selectedFile);
    uploadData.append('title', formData.title);
    uploadData.append('content', formData.content);
    uploadData.append('document_type', formData.document_type);
    uploadData.append('source', formData.source || t('documentsManager.upload.defaults.source'));

    onUpload(uploadData);
  };

  return (
    <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-md rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-all duration-300 border border-white/20 dark:border-slate-700/50 hover:shadow-md dark:hover:shadow-slate-900/70">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-slate-900 dark:text-white">{t('documentsManager.upload.title')}</h3>
        {onCancel && (
          <button
            onClick={onCancel}
            className="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-400 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Selector de archivo */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 transition-colors">
            {t('documentsManager.upload.fields.fileRequired')}
          </label>
          <div className="flex items-center justify-center w-full">
            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 dark:border-slate-600 border-dashed rounded-lg cursor-pointer bg-gray-50 dark:bg-slate-700/50 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                {selectedFile ? (
                  <>
                    <File className="h-10 w-10 text-blue-500 mb-2" />
                    <p className="text-sm text-slate-700 dark:text-white font-medium">{selectedFile.name}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {(selectedFile.size / 1024).toFixed(2)} KB
                    </p>
                  </>
                ) : (
                  <>
                    <Upload className="h-10 w-10 text-gray-400 dark:text-slate-500 mb-2" />
                    <p className="text-sm text-gray-500 dark:text-slate-400">
                      <span className="font-semibold">{t('documentsManager.upload.clickToUpload')}</span> {t('documentsManager.upload.orDrag')}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-slate-500">
                      {t('documentsManager.upload.supportedFormats').replace('{size}', '10MB')}
                    </p>
                  </>
                )}
              </div>
              <input
                type="file"
                className="hidden"
                onChange={handleFileChange}
                accept=".pdf,.docx,.doc,.txt,.xlsx,.xls"
              />
            </label>
          </div>
        </div>

        {/* Título */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 transition-colors">
            {t('documentsManager.upload.fields.titleRequired')}
          </label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            placeholder={t('documentsManager.upload.placeholders.title')}
            required
          />
        </div>

        {/* Descripción */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 transition-colors">
            {t('documentsManager.upload.fields.content')}
          </label>
          <textarea
            value={formData.content}
            onChange={(e) => setFormData({ ...formData, content: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            rows="3"
            placeholder={t('documentsManager.upload.placeholders.content')}
          />
        </div>

        {/* Tipo de documento */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 transition-colors">
            {t('documentsManager.upload.fields.documentTypeRequired')}
          </label>
          <select
            value={formData.document_type}
            onChange={(e) => setFormData({ ...formData, document_type: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            required
          >
            <option value="acta">{t('documentsManager.types.minute')}</option>
            <option value="reporte">{t('documentsManager.types.report')}</option>
            <option value="política">{t('documentsManager.types.policy')}</option>
            <option value="procedimiento">{t('documentsManager.types.procedure')}</option>
            <option value="otro">{t('documentsManager.types.other')}</option>
          </select>
        </div>

        {/* Fuente/Origen */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 transition-colors">
            {t('documentsManager.upload.fields.source')}
          </label>
          <input
            type="text"
            value={formData.source}
            onChange={(e) => setFormData({ ...formData, source: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            placeholder={t('documentsManager.upload.placeholders.source')}
          />
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg transition-colors">
            <AlertCircle className="h-5 w-5 text-red-500 dark:text-red-400 mr-2" />
            <span className="text-sm text-red-700 dark:text-red-200">{error}</span>
          </div>
        )}

        {/* Botones */}
        <div className="flex items-center justify-end space-x-3 pt-4">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors"
            >
              {t('common.buttons.cancel')}
            </button>
          )}
          <button
            type="submit"
            disabled={uploading || !selectedFile}
            className="px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 disabled:bg-blue-300 dark:disabled:bg-blue-900/30 disabled:cursor-not-allowed flex items-center transition-colors"
          >
            {uploading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                {t('documentsManager.upload.actions.uploading')}
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                {t('documentsManager.upload.actions.uploadDocument')}
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default DocumentUploadForm;