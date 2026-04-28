import React from 'react';
const CrudPageHeader = ({ title, subtitle, actionLabel, onAction, actionDisabled = false }) => {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{title}</h1>
        {subtitle ? <p className="mt-1 text-slate-600 dark:text-slate-400">{subtitle}</p> : null}
      </div>
      {actionLabel && onAction ? (
        <button
          type="button"
          onClick={onAction}
          disabled={actionDisabled}
          className="rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
};

export default CrudPageHeader;
