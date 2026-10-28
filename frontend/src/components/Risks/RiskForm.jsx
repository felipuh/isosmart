import React, { useState, useEffect } from 'react';
import { useI18n } from '../../context/I18nContext';

const probabilityOptions = [
  { value: 'muy_baja', score: 1 },
  { value: 'baja', score: 2 },
  { value: 'media', score: 3 },
  { value: 'alta', score: 4 },
  { value: 'muy_alta', score: 5 },
];

const impactOptions = [
  { value: 'muy_bajo', score: 1 },
  { value: 'bajo', score: 2 },
  { value: 'medio', score: 3 },
  { value: 'alto', score: 4 },
  { value: 'muy_alto', score: 5 },
];

const RiskForm = ({ risk, onSubmit, onCancel }) => {
  const { t } = useI18n();
  const [formData, setFormData] = useState({
    risk_description: '',
    risk_category: '',
    probability: 'media',
    impact: 'medio',
    risk_level: 'medio',
    mitigation_actions: '',
    responsible: '',
    iso_clause: '6.1',
    status: 'identified',
    deadline: '',
    process_id: '',
    source_module: 'MANUAL',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const statusOptions = ['identified', 'under_analysis', 'mitigated', 'accepted', 'closed'];

  const categoryOptions = [
    'Operacional', 'Financiero', 'Legal/Regulatorio', 'Tecnológico',
    'Recursos Humanos', 'Reputacional', 'Ambiental', 'Seguridad', 'Calidad', 'Estratégico', 'Otro',
  ];

  const categoryLabelKeys = {
    Operacional: 'operational',
    Financiero: 'financial',
    'Legal/Regulatorio': 'legalRegulatory',
    Tecnológico: 'technological',
    'Recursos Humanos': 'humanResources',
    Reputacional: 'reputational',
    Ambiental: 'environmental',
    Seguridad: 'security',
    Calidad: 'quality',
    Estratégico: 'strategic',
    Otro: 'other',
  };

  const isoClauseOptions = [
    '4.1', '4.2', '4.3', '4.4', '5.1', '5.2', '5.3',
    '6.1', '6.2', '6.3', '7.1', '7.2', '7.3', '7.4', '7.5',
    '8.1', '8.2', '8.3', '8.4', '8.5', '8.6', '8.7',
    '9.1', '9.2', '9.3', '10.1', '10.2', '10.3',
  ];

  useEffect(() => {
    if (risk) {
      setFormData({
        risk_description: risk.risk_description || '',
        risk_category: risk.risk_category || '',
        probability: risk.probability || 'media',
        impact: risk.impact || 'medio',
        risk_level: risk.risk_level || 'medio',
        mitigation_actions: risk.mitigation_actions || '',
        responsible: risk.responsible || '',
        iso_clause: risk.iso_clause || '6.1',
        status: risk.status || 'identified',
        deadline: risk.deadline ? risk.deadline.split('T')[0] : '',
        process_id: risk.process_id || '',
        source_module: risk.source_module || 'MANUAL',
      });
    }
  }, [risk]);

  useEffect(() => {
    const probScore = probabilityOptions.find(p => p.value === formData.probability)?.score || 3;
    const impactScore = impactOptions.find(i => i.value === formData.impact)?.score || 3;
    const totalScore = probScore + impactScore;

    let level = 'bajo';
    if (totalScore >= 8) level = 'critico';
    else if (totalScore >= 6) level = 'alto';
    else if (totalScore >= 4) level = 'medio';

    setFormData(prev => ({ ...prev, risk_level: level }));
  }, [formData.probability, formData.impact]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: null }));
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.risk_description.trim()) newErrors.risk_description = t('riskManagement.form.errors.descriptionRequired');
    if (!formData.risk_category) newErrors.risk_category = t('riskManagement.form.errors.categoryRequired');
    if (!formData.responsible.trim()) newErrors.responsible = t('riskManagement.form.errors.responsibleRequired');
    if (!formData.mitigation_actions.trim()) newErrors.mitigation_actions = t('riskManagement.form.errors.mitigationRequired');
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      await onSubmit(formData);
    } catch (err) {
      setErrors({ submit: err.message });
    } finally {
      setLoading(false);
    }
  };

  const getLevelColor = (level) => {
    const colors = {
      critico: 'bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-300 border-red-300 dark:border-red-700',
      alto: 'bg-orange-100 dark:bg-orange-900/40 text-orange-800 dark:text-orange-300 border-orange-300 dark:border-orange-700',
      medio: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700',
      bajo: 'bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-300 border-green-300 dark:border-green-700',
    };
    return colors[level] || colors.medio;
  };

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-gray-900/75 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-all duration-300">
      <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-md rounded-lg shadow-2xl dark:shadow-slate-900/70 max-w-3xl w-full max-h-[90vh] overflow-hidden border border-white/20 dark:border-slate-700/30 transition-all duration-300">
        <div className="px-6 py-4 border-b border-slate-200/50 dark:border-slate-700/50 flex justify-between items-center bg-white/80 dark:bg-slate-800/80 backdrop-blur-md transition-all duration-300">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{risk ? t('riskManagement.form.titleEdit') : t('riskManagement.form.titleCreate')}</h2>
          <button onClick={onCancel} className="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-400 transition-colors">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="px-6 py-4 space-y-6">
            {errors.submit && <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded transition-colors">{errors.submit}</div>}

            <div className="bg-gray-50/70 dark:bg-slate-700/70 backdrop-blur-md rounded-lg p-4 border border-gray-100/50 dark:border-slate-600/50 transition-all duration-300">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{t('riskManagement.form.calculatedLevel')}:</span>
                <span className={`px-4 py-2 text-sm font-bold rounded-lg border ${getLevelColor(formData.risk_level)}`}>
                  {t(`riskManagement.levels.${formData.risk_level}`)}
                </span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 transition-colors">{t('riskManagement.form.fields.description')} <span className="text-red-500">*</span></label>
              <textarea name="risk_description" value={formData.risk_description} onChange={handleChange} rows={3}
                className={`w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-slate-700 dark:text-white dark:border-slate-600 transition-colors ${errors.risk_description ? 'border-red-300' : 'border-gray-300'}`}
                placeholder={t('riskManagement.form.placeholders.description')} />
              {errors.risk_description && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.risk_description}</p>}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 transition-colors">{t('riskManagement.form.fields.category')} <span className="text-red-500">*</span></label>
                <select name="risk_category" value={formData.risk_category} onChange={handleChange}
                  className={`w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-slate-700 dark:text-white dark:border-slate-600 transition-colors ${errors.risk_category ? 'border-red-300' : 'border-gray-300'}`}>
                  <option value="">{t('riskManagement.form.selectCategory')}</option>
                  {categoryOptions.map(cat => <option key={cat} value={cat}>{t(`riskManagement.form.categories.${categoryLabelKeys[cat] || 'other'}`)}</option>)}
                </select>
                {errors.risk_category && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.risk_category}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 transition-colors">{t('riskManagement.form.fields.isoClause')}</label>
                <select name="iso_clause" value={formData.iso_clause} onChange={handleChange} className="w-full border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 transition-colors">
                  {isoClauseOptions.map((clause) => (
                    <option key={clause} value={clause}>
                      {t('riskManagement.form.isoClauseOption').replace('{clause}', clause)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 transition-colors">{t('riskManagement.form.fields.probability')}</label>
                <select name="probability" value={formData.probability} onChange={handleChange} className="w-full border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 transition-colors">
                  {probabilityOptions.map(opt => <option key={opt.value} value={opt.value}>{t(`riskManagement.matrix.probability.${opt.value}`)}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 transition-colors">{t('riskManagement.form.fields.impact')}</label>
                <select name="impact" value={formData.impact} onChange={handleChange} className="w-full border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 transition-colors">
                  {impactOptions.map(opt => <option key={opt.value} value={opt.value}>{t(`riskManagement.matrix.impact.${opt.value}`)}</option>)}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 transition-colors">{t('riskManagement.form.fields.responsible')} <span className="text-red-500">*</span></label>
                <input type="text" name="responsible" value={formData.responsible} onChange={handleChange}
                  className={`w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-slate-700 dark:text-white dark:border-slate-600 transition-colors ${errors.responsible ? 'border-red-300' : 'border-gray-300'}`}
                  placeholder={t('riskManagement.form.placeholders.responsible')} />
                {errors.responsible && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.responsible}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 transition-colors">{t('common.forms.status')}</label>
                <select name="status" value={formData.status} onChange={handleChange} className="w-full border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 transition-colors">
                  {statusOptions.map(status => <option key={status} value={status}>{t(`riskManagement.statuses.${status}`)}</option>)}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 transition-colors">{t('riskManagement.form.fields.deadline')}</label>
                <input type="date" name="deadline" value={formData.deadline} onChange={handleChange} className="w-full border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 transition-colors" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 transition-colors">{t('riskManagement.form.fields.processIdOptional')}</label>
                <input type="text" name="process_id" value={formData.process_id} onChange={handleChange} className="w-full border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 transition-colors" placeholder={t('riskManagement.form.placeholders.processId')} />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 transition-colors">{t('riskManagement.form.fields.mitigationActions')} <span className="text-red-500">*</span></label>
              <textarea name="mitigation_actions" value={formData.mitigation_actions} onChange={handleChange} rows={4}
                className={`w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-slate-700 dark:text-white dark:border-slate-600 transition-colors ${errors.mitigation_actions ? 'border-red-300' : 'border-gray-300'}`}
                placeholder={t('riskManagement.form.placeholders.mitigationActions')} />
              {errors.mitigation_actions && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.mitigation_actions}</p>}
            </div>
          </div>

          <div className="px-6 py-4 border-t border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-700/50 flex justify-end gap-3 transition-colors">
            <button type="button" onClick={onCancel} className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors">{t('common.buttons.cancel')}</button>
            <button type="submit" disabled={loading} className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 dark:bg-blue-700 border border-transparent rounded-md shadow-sm hover:bg-blue-700 dark:hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
              {loading ? t('common.messages.saving') : (risk ? t('riskManagement.form.buttons.updateRisk') : t('riskManagement.form.buttons.createRisk'))}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RiskForm;