import React from 'react';
import { useI18n } from '../../context/I18nContext';

const Modal = ({ title, isOpen, onClose, children, maxWidth = 'max-w-4xl' }) => {
  const { t } = useI18n();
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 dark:bg-slate-950/70 backdrop-blur-sm p-4 transition-colors duration-300">
      <div className={`w-full ${maxWidth} rounded-xl border border-slate-200 dark:border-slate-700/50 bg-white/95 dark:bg-slate-900/95 shadow-2xl transition-colors duration-300`}>
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-700/50 px-6 py-4">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-500 dark:text-slate-300 hover:text-slate-700 dark:hover:text-white transition-colors"
            aria-label={t('common.buttons.close')}
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="max-h-[85vh] overflow-y-auto px-6 py-4 text-slate-800 dark:text-slate-100">
          {children}
        </div>
      </div>
    </div>
  );
};

export default Modal;