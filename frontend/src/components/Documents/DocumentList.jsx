import React from 'react';
import { FileText, Download, Trash2, Calendar, User } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const DocumentList = ({ documents, loading, onDelete, onDownload }) => {
  const { t, language } = useI18n();
  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 transition-colors">
        <div className="animate-pulse p-6">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-12 text-center transition-colors">
        <FileText className="h-16 w-16 text-slate-400 dark:text-slate-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
          {t('documentsManager.list.emptyTitle')}
        </h3>
        <p className="text-slate-600 dark:text-slate-400">
          {t('documentsManager.list.emptySubtitle')}
        </p>
      </div>
    );
  }

  const getDocumentTypeLabel = (type) => {
    const types = {
      policy: t('documentsManager.types.policy'),
      politica: t('documentsManager.types.policy'),
      'política': t('documentsManager.types.policy'),
      procedure: t('documentsManager.types.procedure'),
      procedimiento: t('documentsManager.types.procedure'),
      manual: t('documentsManager.list.types.manual'),
      report: t('documentsManager.types.report'),
      reporte: t('documentsManager.types.report'),
      plan: t('documentsManager.list.types.plan'),
      other: t('documentsManager.types.other'),
      otro: t('documentsManager.types.other'),
      minute: t('documentsManager.types.minute'),
      acta: t('documentsManager.types.minute'),
    };
    return types[type] || type;
  };

  const getDocumentTypeColor = (type) => {
    const colors = {
      policy: 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300',
      politica: 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300',
      'política': 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300',
      procedure: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
      procedimiento: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
      manual: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300',
      report: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300',
      reporte: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300',
      plan: 'bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300',
      other: 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300',
      otro: 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300',
      minute: 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300',
      acta: 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300',
    };
    return colors[type] || colors.other;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const locale = language === 'es-LATAM' ? 'es-ES' : language;
    return new Date(dateString).toLocaleDateString(locale, {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 overflow-hidden transition-colors">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-slate-700">
          <thead className="bg-gray-50 dark:bg-slate-700/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                {t('documentsManager.list.columns.document')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                {t('documentsManager.list.columns.type')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                {t('documentsManager.list.columns.uploadedBy')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                {t('documentsManager.list.columns.date')}
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                {t('documentsManager.list.columns.actions')}
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-slate-800 divide-y divide-gray-200 dark:divide-slate-700 transition-colors">
            {documents.map((doc) => (
              <tr key={doc.id} className="hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center">
                    <FileText className="h-5 w-5 text-gray-400 dark:text-slate-500 mr-3" />
                    <div>
                      <div className="text-sm font-medium text-slate-900 dark:text-white">
                        {doc.title}
                      </div>
                      {doc.file_name && (
                        <div className="text-xs text-slate-500 dark:text-slate-400">
                          {doc.file_name}
                        </div>
                      )}
                      {doc.content && (
                        <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-1">
                          {doc.content}
                        </div>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getDocumentTypeColor(doc.document_type)}`}>
                    {getDocumentTypeLabel(doc.document_type)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center text-sm text-slate-500 dark:text-slate-400">
                    <User className="h-4 w-4 mr-1" />
                    {doc.source || t('documentsManager.list.defaultSource')}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center text-sm text-slate-500 dark:text-slate-400">
                    <Calendar className="h-4 w-4 mr-1" />
                    {formatDate(doc.created_at)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    onClick={() => onDownload(doc)}
                    className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 mr-4 transition-colors"
                    title={t('documentsManager.list.actions.download')}
                  >
                    <Download className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => onDelete(doc)}
                    className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 transition-colors"
                    title={t('common.buttons.delete')}
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DocumentList;