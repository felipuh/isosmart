import React from 'react';
import { AlertCircle, X } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const CrudErrorBanner = ({ message, onClose }) => {
  const { t } = useI18n();

  if (!message) return null;

  return (
    <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-red-200" role="alert">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <p className="text-sm">{message}</p>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="text-red-300 transition-colors hover:text-red-100"
            aria-label={t('common.buttons.dismissError')}
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default CrudErrorBanner;
