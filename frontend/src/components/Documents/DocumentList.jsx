import React from 'react';
import { FileText, Download, Trash2, Calendar, User } from 'lucide-react';

const DocumentList = ({ documents, loading, onDelete, onDownload }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow">
        <div className="animate-pulse p-6">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          No hay documentos cargados
        </h3>
        <p className="text-gray-600">
          Sube tu primer documento para comenzar el análisis
        </p>
      </div>
    );
  }

  const getDocumentTypeLabel = (type) => {
    const types = {
      'policy': 'Política',
      'procedure': 'Procedimiento',
      'manual': 'Manual',
      'report': 'Reporte',
      'plan': 'Plan',
      'other': 'Otro'
    };
    return types[type] || type;
  };

  const getDocumentTypeColor = (type) => {
    const colors = {
      'policy': 'bg-purple-100 text-purple-700',
      'procedure': 'bg-blue-100 text-blue-700',
      'manual': 'bg-green-100 text-green-700',
      'report': 'bg-yellow-100 text-yellow-700',
      'plan': 'bg-orange-100 text-orange-700',
      'other': 'bg-gray-100 text-gray-700'
    };
    return colors[type] || colors['other'];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Documento
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tipo
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Subido por
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Fecha
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {documents.map((doc) => (
              <tr key={doc.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="flex items-center">
                    <FileText className="h-5 w-5 text-gray-400 mr-3" />
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {doc.title}
                      </div>
                      {doc.file_name && (
                        <div className="text-xs text-gray-500">
                          {doc.file_name}
                        </div>
                      )}
                      {doc.content && (
                        <div className="text-xs text-gray-500 mt-1 line-clamp-1">
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
                  <div className="flex items-center text-sm text-gray-500">
                    <User className="h-4 w-4 mr-1" />
                    {doc.source || 'Sistema'}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center text-sm text-gray-500">
                    <Calendar className="h-4 w-4 mr-1" />
                    {formatDate(doc.created_at)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    onClick={() => onDownload(doc)}
                    className="text-blue-600 hover:text-blue-900 mr-4"
                    title="Descargar"
                  >
                    <Download className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => onDelete(doc)}
                    className="text-red-600 hover:text-red-900"
                    title="Eliminar"
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