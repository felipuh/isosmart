import React, { useState, useEffect, useCallback } from 'react';
import { 
  FileCheck, Check, X, Edit2, Save, Loader2, AlertCircle,
  ChevronDown, ChevronRight, Info, RefreshCw, Shield
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import settingsService from '../../services/settingsService';

const ISOClausesSettings = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const organizationId = currentOrganization?.id;
  const [selectedStandard, setSelectedStandard] = useState('ISO9001_2015');
  const [availableStandards, setAvailableStandards] = useState(['ISO9001_2015']);
  const [clauses, setClauses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editingClause, setEditingClause] = useState(null);
  const [expandedSections, setExpandedSections] = useState(['4', '5', '6']);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);

  // Agrupar cláusulas por sección principal
  const groupedClauses = clauses.reduce((acc, clause) => {
    const section = clause.clause_number.split('.')[0];
    if (!acc[section]) {
      acc[section] = [];
    }
    acc[section].push(clause);
    return acc;
  }, {});

  const sectionNames = {
    '4': t('settings.iso.sectionNames.4'),
    '5': t('settings.iso.sectionNames.5'),
    '6': t('settings.iso.sectionNames.6'),
    '7': t('settings.iso.sectionNames.7'),
    '8': t('settings.iso.sectionNames.8'),
    '9': t('settings.iso.sectionNames.9'),
    '10': t('settings.iso.sectionNames.10'),
  };

  useEffect(() => {
    let mounted = true;

    const loadAvailableStandards = async () => {
      if (!organizationId) {
        if (mounted) {
          setAvailableStandards(['ISO9001_2015']);
          setSelectedStandard('ISO9001_2015');
        }
        return;
      }

      try {
        const standards = await settingsService.getCommerciallyAvailableStandards(organizationId);
        const normalized = Array.isArray(standards) && standards.length > 0
          ? Array.from(new Set(standards.map((code) => String(code || '').trim()).filter(Boolean)))
          : ['ISO9001_2015'];

        if (!normalized.includes('ISO9001_2015')) {
          normalized.unshift('ISO9001_2015');
        }

        if (!mounted) return;

        setAvailableStandards(normalized);
        setSelectedStandard((previous) => (
          normalized.includes(previous) ? previous : normalized[0]
        ));
      } catch {
        if (!mounted) return;
        setAvailableStandards(['ISO9001_2015']);
        setSelectedStandard('ISO9001_2015');
      }
    };

    loadAvailableStandards();

    return () => {
      mounted = false;
    };
  }, [organizationId]);

  const loadClauses = useCallback(async () => {
    try {
      if (!organizationId) {
        setClauses([]);
        setLoading(false);
        return;
      }
      setLoading(true);
      const data = await settingsService.getISOClauses(organizationId, selectedStandard);
      setClauses(data);
    } catch (err) {
      console.error('Error loading clauses:', err);
      setError(t('settings.iso.messages.errorLoadingClauses'));
    } finally {
      setLoading(false);
    }
  }, [organizationId, selectedStandard, t]);

  useEffect(() => {
    loadClauses();
  }, [loadClauses]);

  const handleInitialize = async () => {
    try {
      setSaving(true);
      setError(null);
      await settingsService.initializeStandards(organizationId, [selectedStandard]);
      
      // Guardar el estándar en la configuración de la organización
      await settingsService.updateStandards(organizationId, [selectedStandard]);
      
      await loadClauses();
      const standardName = t(`settings.iso.standards.${selectedStandard}`);
      setSuccess(t('settings.iso.messages.initializedSuccess').replace('{standard}', standardName));
      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      console.error('Error initializing clauses:', error);
      setError(t('settings.iso.messages.errorInitializingClauses'));
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateClause = async (clauseId, updates) => {
    try {
      setSaving(true);
      await settingsService.updateISOClause(clauseId, updates);
      setClauses(prev => prev.map(c => c.id === clauseId ? { ...c, ...updates } : c));
      setEditingClause(null);
      setSuccess(t('settings.iso.messages.clauseUpdated'));
      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      console.error('Error updating clause:', error);
      setError(t('settings.iso.messages.errorUpdatingClause'));
    } finally {
      setSaving(false);
    }
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => 
      prev.includes(section) 
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  };

  const applicableCount = clauses.filter(c => c.is_applicable).length;
  const excludedCount = clauses.filter(c => !c.is_applicable).length;
  const selectedStandardLabel = t(`settings.iso.standards.${selectedStandard}`);

  if (loading) {
    return (
      <div className="p-6 lg:p-8 flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 mb-8">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gradient-to-br from-teal-500 to-cyan-500 rounded-xl shadow-lg shadow-teal-500/25">
            <FileCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-800 dark:text-white">
              {t('settings.iso.title')}
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {t('settings.iso.clausesSubtitle')}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedStandard}
            onChange={(event) => setSelectedStandard(event.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100"
          >
            {availableStandards.map((standardCode) => (
              <option key={standardCode} value={standardCode}>
                {t(`settings.iso.standards.${standardCode}`)}
              </option>
            ))}
          </select>
        
          {clauses.length === 0 && (
            <button
              onClick={handleInitialize}
              disabled={saving}
              className="px-4 py-2 bg-teal-500 hover:bg-teal-600 text-white rounded-lg font-medium flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              {saving ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              {t('settings.iso.initialize')}
            </button>
          )}
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

      {clauses.length > 0 ? (
        <>
          {/* Summary */}
          <div className="mb-8 grid grid-cols-3 gap-4">
            <div className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl border border-blue-100 dark:border-blue-800/50">
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{clauses.length}</p>
              <p className="text-sm text-blue-600/70 dark:text-blue-400/70">{t('settings.iso.stats.totalClauses')}</p>
            </div>
            <div className="p-4 bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 rounded-xl border border-emerald-100 dark:border-emerald-800/50">
              <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{applicableCount}</p>
              <p className="text-sm text-emerald-600/70 dark:text-emerald-400/70">{t('settings.iso.stats.applicable')}</p>
            </div>
            <div className="p-4 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl border border-amber-100 dark:border-amber-800/50">
              <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">{excludedCount}</p>
              <p className="text-sm text-amber-600/70 dark:text-amber-400/70">{t('settings.iso.stats.excluded')}</p>
            </div>
          </div>

          {/* Clauses by Section */}
          <div className="space-y-4">
            {Object.entries(groupedClauses).sort(([a], [b]) => parseInt(a) - parseInt(b)).map(([section, sectionClauses]) => (
              <div key={section} className="bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
                {/* Section Header */}
                <button
                  onClick={() => toggleSection(section)}
                  className="w-full p-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-teal-100 dark:bg-teal-900/30 rounded-lg">
                      <Shield className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-bold text-slate-800 dark:text-white">
                        {t('settings.iso.sectionTitle')
                          .replace('{section}', section)
                          .replace('{name}', sectionNames[section])}
                      </h3>
                      <p className="text-sm text-slate-500 dark:text-slate-400">
                        {t('settings.iso.sectionApplicableCount')
                          .replace('{applicable}', sectionClauses.filter(c => c.is_applicable).length)
                          .replace('{total}', sectionClauses.length)}
                      </p>
                    </div>
                  </div>
                  {expandedSections.includes(section) ? (
                    <ChevronDown className="w-5 h-5 text-slate-400" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-slate-400" />
                  )}
                </button>

                {/* Section Content */}
                {expandedSections.includes(section) && (
                  <div className="border-t border-slate-200 dark:border-slate-700">
                    {sectionClauses.sort((a, b) => a.clause_number.localeCompare(b.clause_number)).map((clause) => (
                      <ClauseRow 
                        key={clause.id}
                        clause={clause}
                        isEditing={editingClause === clause.id}
                        onEdit={() => setEditingClause(clause.id)}
                        onSave={(updates) => handleUpdateClause(clause.id, updates)}
                        onCancel={() => setEditingClause(null)}
                      />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="text-center py-12">
          <FileCheck className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-800 dark:text-white mb-2">
            {t('settings.iso.noClausesConfigured')}
          </h3>
          <p className="text-slate-500 dark:text-slate-400 mb-6">
            {t('settings.iso.noClausesDescription').replace('{standard}', selectedStandardLabel)}
          </p>
          <button
            onClick={handleInitialize}
            disabled={saving}
            className="px-6 py-3 bg-gradient-to-r from-teal-500 to-cyan-500 text-white rounded-xl font-medium shadow-lg shadow-teal-500/25 flex items-center gap-2 mx-auto disabled:opacity-50"
          >
            {saving ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <RefreshCw className="w-5 h-5" />
            )}
            {t('settings.iso.initializeSelected').replace('{standard}', selectedStandardLabel)}
          </button>
        </div>
      )}

      {/* Info Box */}
      <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-700 dark:text-blue-300">
          <p className="font-medium mb-1">{t('settings.iso.aboutExclusions')}</p>
          <p>{t('settings.iso.infoDescription')}</p>
        </div>
      </div>
    </div>
  );
};

// Componente de fila de cláusula
const ClauseRow = ({ clause, isEditing, onEdit, onSave, onCancel }) => {
  const { t } = useI18n();
  const [formData, setFormData] = useState({
    is_applicable: clause.is_applicable,
    exclusion_justification: clause.exclusion_justification || '',
    responsible: clause.responsible || '',
  });

  const handleSave = () => {
    onSave(formData);
  };

  if (isEditing) {
    return (
      <div className="p-4 bg-slate-50 dark:bg-slate-700/30 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-start gap-4 mb-4">
          <div className="min-w-[60px]">
            <span className="px-2 py-1 bg-teal-100 dark:bg-teal-900/50 text-teal-700 dark:text-teal-300 rounded text-sm font-mono font-medium">
              {clause.clause_number}
            </span>
          </div>
          <div className="flex-1">
            <p className="font-medium text-slate-800 dark:text-white">{clause.clause_name}</p>
          </div>
        </div>
        
        <div className="ml-16 space-y-4">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_applicable}
                onChange={(e) => setFormData(prev => ({ ...prev, is_applicable: e.target.checked }))}
                className="w-5 h-5 rounded border-slate-300 text-teal-500 focus:ring-teal-500"
              />
              <span className="text-sm text-slate-700 dark:text-slate-300">{t('settings.iso.applicableLabel')}</span>
            </label>
          </div>
          
          {!formData.is_applicable && (
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t('settings.iso.exclusionJustificationLabel')}
              </label>
              <textarea
                value={formData.exclusion_justification}
                onChange={(e) => setFormData(prev => ({ ...prev, exclusion_justification: e.target.value }))}
                rows={2}
                className="w-full px-4 py-2 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-lg text-slate-800 dark:text-white resize-none"
                placeholder={t('settings.iso.exclusionJustificationPlaceholder')}
              />
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              {t('settings.iso.responsibleLabel')}
            </label>
            <input
              type="text"
              value={formData.responsible}
              onChange={(e) => setFormData(prev => ({ ...prev, responsible: e.target.value }))}
              className="w-full px-4 py-2 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-lg text-slate-800 dark:text-white"
              placeholder={t('settings.iso.responsiblePlaceholder')}
            />
          </div>
          
          <div className="flex justify-end gap-2">
            <button
              onClick={onCancel}
              className="px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-lg"
            >
              {t('common.buttons.cancel')}
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-teal-500 hover:bg-teal-600 text-white rounded-lg flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              {t('common.buttons.save')}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 flex items-center gap-4 border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
      <div className="min-w-[60px]">
        <span className="px-2 py-1 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded text-sm font-mono font-medium">
          {clause.clause_number}
        </span>
      </div>
      
      <div className="flex-1">
        <p className="font-medium text-slate-800 dark:text-white">{clause.clause_name}</p>
        {clause.responsible && (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {t('settings.iso.responsiblePrefix').replace('{name}', clause.responsible)}
          </p>
        )}
      </div>
      
      <div className="flex items-center gap-3">
        {clause.is_applicable ? (
          <span className="flex items-center gap-1.5 px-3 py-1 bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 rounded-full text-sm font-medium">
            <Check className="w-4 h-4" />
            {t('settings.iso.applicableStatus')}
          </span>
        ) : (
          <span className="flex items-center gap-1.5 px-3 py-1 bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300 rounded-full text-sm font-medium">
            <X className="w-4 h-4" />
            {t('settings.iso.excludedStatus')}
          </span>
        )}
        
        <button
          onClick={onEdit}
          className="p-2 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-lg transition-colors"
        >
          <Edit2 className="w-4 h-4 text-slate-400" />
        </button>
      </div>
    </div>
  );
};

export default ISOClausesSettings;