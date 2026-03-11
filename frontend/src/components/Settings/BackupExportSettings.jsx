import React, { useEffect, useState } from 'react';
import { 
  Database, Download, Upload, HardDrive, Clock, 
  FileJson, FileSpreadsheet, Calendar, Save, Loader2, 
  Check, AlertCircle, Info, ToggleLeft, ToggleRight,
  RefreshCw, Shield, Archive
} from 'lucide-react';
import settingsService from '../../services/settingsService';
import { useI18n } from '../../context/I18nContext';

const BackupExportSettings = ({ settings, onUpdate, organizationId }) => {
  const { t, language } = useI18n();
  const [autoBackup, setAutoBackup] = useState(settings?.auto_backup_enabled ?? false);
  const [backupFrequency, setBackupFrequency] = useState(settings?.backup_frequency ?? 'weekly');
  const [exporting, setExporting] = useState(null);
  const [backingUp, setBackingUp] = useState(false);
  const [backupHistory, setBackupHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);

  const exportOptions = [
    {
      id: 'all',
      title: t('settings.backup.exportOptions.all.title'),
      description: t('settings.backup.exportOptions.all.description'),
      icon: Archive,
      color: 'from-indigo-500 to-purple-500'
    },
    {
      id: 'risks',
      title: t('settings.backup.exportOptions.risks.title'),
      description: t('settings.backup.exportOptions.risks.description'),
      icon: Shield,
      color: 'from-red-500 to-rose-500'
    },
    {
      id: 'objectives',
      title: t('settings.backup.exportOptions.objectives.title'),
      description: t('settings.backup.exportOptions.objectives.description'),
      icon: FileJson,
      color: 'from-emerald-500 to-teal-500'
    },
    {
      id: 'stakeholders',
      title: t('settings.backup.exportOptions.stakeholders.title'),
      description: t('settings.backup.exportOptions.stakeholders.description'),
      icon: FileSpreadsheet,
      color: 'from-violet-500 to-purple-500'
    },
    {
      id: 'processes',
      title: t('settings.backup.exportOptions.processes.title'),
      description: t('settings.backup.exportOptions.processes.description'),
      icon: FileJson,
      color: 'from-amber-500 to-orange-500'
    },
  ];

  const frequencyOptions = [
    { value: 'daily', label: t('settings.backup.frequencyOptions.daily') },
    { value: 'weekly', label: t('settings.backup.frequencyOptions.weekly') },
    { value: 'monthly', label: t('settings.backup.frequencyOptions.monthly') },
  ];

  useEffect(() => {
    let cancelled = false;

    const loadBackupHistory = async () => {
      if (!organizationId) return;

      try {
        setHistoryLoading(true);
        const response = await settingsService.getBackupHistory(organizationId, 5);
        if (!cancelled) {
          setBackupHistory(response.results || []);
        }
      } catch (err) {
        if (!cancelled) {
          setError(t('settings.backup.messages.historyError'));
        }
        console.error(err);
      } finally {
        if (!cancelled) {
          setHistoryLoading(false);
        }
      }
    };

    loadBackupHistory();

    return () => {
      cancelled = true;
    };
  }, [organizationId, t]);

  const handleExport = async (type) => {
    try {
      setExporting(type);
      setError(null);
      
      await settingsService.downloadExport(type, organizationId);
      
      const selectedType = t(`settings.backup.exportOptions.${type}.title`);
      setSuccess(t('settings.backup.messages.exportSuccess').replace('{type}', selectedType));
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(t('settings.backup.messages.exportError'));
      console.error(err);
    } finally {
      setExporting(null);
    }
  };

  const handleBackup = async () => {
    try {
      setBackingUp(true);
      setError(null);
      
      const result = await settingsService.triggerBackup(organizationId);
      onUpdate({ last_backup_at: result.last_backup_at });
      if (result.history_entry) {
        setBackupHistory((prev) => [result.history_entry, ...prev.filter((entry) => entry.id !== result.history_entry.id)].slice(0, 5));
      }
      
      setSuccess(t('settings.backup.messages.backupSuccess'));
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(t('settings.backup.messages.backupError'));
      console.error(err);
    } finally {
      setBackingUp(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return t('settings.backup.never');
    const locale = language === 'es-LATAM' ? 'es-ES' : language;
    return new Date(dateString).toLocaleString(locale, {
      dateStyle: 'medium',
      timeStyle: 'short'
    });
  };

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <div className="p-3 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-xl shadow-lg shadow-emerald-500/25">
          <Database className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-white">
            {t('settings.backup.title')}
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {t('settings.backup.subtitle')}
          </p>
        </div>
      </div>

      {/* Alerts */}
      {success && (
        <div className="mb-6 p-4 bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-800 rounded-xl flex items-center gap-3">
          <Check className="w-5 h-5 text-emerald-500" />
          <span className="text-emerald-700 dark:text-emerald-300">{success}</span>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700 dark:text-red-300">{error}</span>
        </div>
      )}

      {/* Backup Section */}
      <div className="mb-8 p-6 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-700/30 dark:to-slate-800/30 rounded-2xl border border-slate-200 dark:border-slate-700">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <HardDrive className="w-5 h-5 text-emerald-500" />
          {t('settings.backup.backupConfigTitle')}
        </h3>
        
        {/* Last Backup Info */}
        <div className="flex items-center justify-between p-4 bg-white dark:bg-slate-800/50 rounded-xl mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
              <Clock className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <p className="font-semibold text-slate-800 dark:text-white">{t('settings.backup.lastBackup')}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {formatDate(settings?.last_backup_at)}
              </p>
            </div>
          </div>
          <button
            onClick={handleBackup}
            disabled={backingUp}
            data-testid="settings-backup-now"
            className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            {backingUp ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                {t('settings.backup.actions.backingUp')}
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                {t('settings.backup.actions.backupNow')}
              </>
            )}
          </button>
        </div>

        {/* Auto Backup Toggle */}
        <div className="flex items-center justify-between p-4 bg-white dark:bg-slate-800/50 rounded-xl mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Calendar className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="font-semibold text-slate-800 dark:text-white">{t('settings.backup.autoBackup')}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {t('settings.backup.autoBackupDescription')}
              </p>
            </div>
          </div>
          <button onClick={() => setAutoBackup(!autoBackup)}>
            {autoBackup ? (
              <ToggleRight className="w-12 h-7 text-emerald-500" />
            ) : (
              <ToggleLeft className="w-12 h-7 text-slate-400" />
            )}
          </button>
        </div>

        {/* Frequency Selection */}
        {autoBackup && (
          <div className="mt-4">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
              {t('settings.backup.backupFrequency')}
            </label>
            <div className="flex gap-3">
              {frequencyOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setBackupFrequency(option.value)}
                  className={`
                    px-4 py-2 rounded-lg border-2 transition-all
                    ${backupFrequency === option.value
                      ? 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-400 dark:border-emerald-500 text-emerald-700 dark:text-emerald-300'
                      : 'bg-white dark:bg-slate-800/50 border-slate-200 dark:border-slate-600 text-slate-700 dark:text-slate-200 hover:border-slate-300'
                    }
                  `}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="mb-8">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-blue-500" />
          {t('settings.backup.historyTitle')}
        </h3>

        <div className="p-4 bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700">
          {historyLoading ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {t('settings.backup.loadingHistory')}
            </p>
          ) : backupHistory.length === 0 ? (
            <div>
              <p className="font-medium text-slate-700 dark:text-slate-200">
                {t('settings.backup.historyEmpty')}
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                {t('settings.backup.historyEmptyDescription')}
              </p>
            </div>
          ) : (
            <ul className="space-y-3" data-testid="settings-backup-history">
              {backupHistory.map((entry) => (
                <li
                  key={entry.id}
                  className="flex items-start justify-between gap-4 border-b border-slate-100 dark:border-slate-700/60 pb-3 last:border-b-0 last:pb-0"
                >
                  <div>
                    <p className="font-medium text-slate-800 dark:text-white">
                      {entry.description}
                    </p>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                      {entry.user_name || 'Sistema'}
                    </p>
                  </div>
                  <span className="text-sm text-slate-500 dark:text-slate-400 whitespace-nowrap">
                    {formatDate(entry.created_at)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Export Section */}
      <div className="mb-8">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <Download className="w-5 h-5 text-indigo-500" />
          {t('settings.backup.exportData')}
        </h3>
        
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
          {t('settings.backup.exportDescription')}
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {exportOptions.map((option) => {
            const Icon = option.icon;
            const isExporting = exporting === option.id;
            
            return (
              <div 
                key={option.id}
                className="p-4 bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 transition-all"
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2.5 rounded-xl bg-gradient-to-br ${option.color} shadow-lg`}>
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-slate-800 dark:text-white">
                      {option.title}
                    </h4>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-3">
                      {option.description}
                    </p>
                    <button
                      onClick={() => handleExport(option.id)}
                      disabled={isExporting}
                      data-testid={`settings-export-${option.id}`}
                      className="px-3 py-1.5 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors disabled:opacity-50"
                    >
                      {isExporting ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          {t('settings.backup.actions.exporting')}
                        </>
                      ) : (
                        <>
                          <Download className="w-4 h-4" />
                          {t('settings.backup.actions.downloadJson')}
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Info Box */}
      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-700 dark:text-blue-300">
          <p className="font-medium mb-1">{t('settings.backup.aboutBackups')}</p>
          <p>
            {t('settings.backup.infoDescription')}
          </p>
        </div>
      </div>
    </div>
  );
};

export default BackupExportSettings;