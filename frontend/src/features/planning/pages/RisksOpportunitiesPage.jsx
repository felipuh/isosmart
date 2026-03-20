// features/planning/pages/RisksOpportunitiesPage.jsx
import React, { useCallback, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { getRisksOpportunities, createRiskOpportunity, updateRiskOpportunity, deleteRiskOpportunity } from '../api/planningApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const RisksOpportunitiesPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const toNumberOrNull = (value) => {
    if (value === '' || value === null || value === undefined) return null;
    const parsed = Number(value);
    return Number.isNaN(parsed) ? null : parsed;
  };

  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    item_type: 'risk',
    code: '',
    title: '',
    description: '',
    category: 'operational',
    context: 'internal',
    probability: 3,
    impact: 3,
    feasibility: 3,
    benefit: 3,
    treatment: 'mitigate',
    treatment_description: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [filterType, setFilterType] = useState('all');
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getRisksOpportunities({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error:', error);
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  useEffect(() => {
    if (orgId) loadData();
  }, [orgId, loadData]);

  useEffect(() => {
    if (location.pathname.endsWith('/new')) {
      resetForm();
      setShowForm(true);
    }
  }, [location.pathname]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError('');
      const payload = {
        ...form,
        organization_id: orgId,
        organization_name: orgName,
        probability: form.item_type === 'risk' ? toNumberOrNull(form.probability) : null,
        impact: form.item_type === 'risk' ? toNumberOrNull(form.impact) : null,
        feasibility: form.item_type === 'opportunity' ? toNumberOrNull(form.feasibility) : null,
        benefit: form.item_type === 'opportunity' ? toNumberOrNull(form.benefit) : null
      };
      if (editingId) {
        await updateRiskOpportunity(editingId, payload);
      } else {
        await createRiskOpportunity(payload);
      }
      resetForm();
      await loadData();
      setShowForm(false);
      if (location.pathname.endsWith('/new')) {
        navigate(location.pathname.replace(/\/new$/, ''), { replace: true });
      }
    } catch (error) {
      console.error('Error:', error);
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setForm({
      item_type: item.item_type,
      code: item.code,
      title: item.title,
      description: item.description || '',
      category: item.category,
      context: item.context,
      probability: item.probability || 3,
      impact: item.impact || 3,
      feasibility: item.feasibility || 3,
      benefit: item.benefit || 3,
      treatment: item.treatment || 'mitigate',
      treatment_description: item.treatment_description || ''
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm(t('modules.planning.risksOpportunitiesPage.deleteConfirm'))) return;
    try {
      await deleteRiskOpportunity(id);
      await loadData();
    } catch (error) {
      console.error('Error:', error);
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const resetForm = () => {
    setForm({
      item_type: 'risk',
      code: '',
      title: '',
      description: '',
      category: 'operational',
      context: 'internal',
      probability: 3,
      impact: 3,
      feasibility: 3,
      benefit: 3,
      treatment: 'mitigate',
      treatment_description: ''
    });
    setEditingId(null);
  };

  const openForm = () => {
    resetForm();
    setShowForm(true);
  };

  const closeForm = () => {
    resetForm();
    setShowForm(false);
    if (location.pathname.endsWith('/new')) {
      navigate(location.pathname.replace(/\/new$/, ''), { replace: true });
    }
  };

  const filteredItems = filterType === 'all' 
    ? items 
    : items.filter(i => i.item_type === filterType);

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="space-y-6">
      <CrudPageHeader
        title={t('modules.planning.risksOpportunitiesPage.title')}
        actionLabel={t('modules.planning.risksOpportunitiesPage.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="flex space-x-2">
        {['all', 'risk', 'opportunity'].map(type => (
          <button
            key={type}
            onClick={() => setFilterType(type)}
            className={`px-4 py-2 rounded-lg ${filterType === type ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700 hover:bg-slate-300 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600'}`}
          >
            {type === 'all'
              ? t('modules.planning.risksOpportunitiesPage.filters.all')
              : type === 'risk'
                ? t('modules.planning.risksOpportunitiesPage.filters.risks')
                : t('modules.planning.risksOpportunitiesPage.filters.opportunities')}
          </button>
        ))}
      </div>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.risksOpportunitiesPage.table.code')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.risksOpportunitiesPage.table.title')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.risksOpportunitiesPage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.risksOpportunitiesPage.table.category')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.risksOpportunitiesPage.table.level')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.risksOpportunitiesPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {filteredItems.map(item => (
              <tr key={item.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.code}</td>
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{item.title}</td>
                <td className="px-6 py-4 text-sm">
                  <span className={`badge-base ${item.item_type === 'risk' ? 'badge-danger' : 'badge-success'}`}>
                    {item.item_type_display}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.category_display}</td>
                <td className="px-6 py-4 text-sm">
                  {item.item_type === 'risk' ? (
                    <span className={`badge-base ${
                      item.risk_level >= 15 ? 'badge-danger' :
                      item.risk_level >= 10 ? 'badge-warning' :
                      'badge-success'
                    }`}>
                      {item.risk_level}
                    </span>
                  ) : (
                    <span className="badge-base badge-info">
                      {item.opportunity_score}
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredItems.length === 0 && <CrudEmptyState message={t('modules.planning.risksOpportunitiesPage.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.planning.risksOpportunitiesPage.edit') : t('modules.planning.risksOpportunitiesPage.new')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.type')}</label>
              <select value={form.item_type} onChange={(e) => setForm({...form, item_type: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required>
                <option value="risk">{t('modules.planning.risksOpportunitiesPage.types.risk')}</option>
                <option value="opportunity">{t('modules.planning.risksOpportunitiesPage.types.opportunity')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.code')}</label>
              <input type="text" value={form.code} onChange={(e) => setForm({...form, code: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.category')}</label>
              <select value={form.category} onChange={(e) => setForm({...form, category: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="strategic">{t('modules.planning.risksOpportunitiesPage.categories.strategic')}</option>
                <option value="operational">{t('modules.planning.risksOpportunitiesPage.categories.operational')}</option>
                <option value="financial">{t('modules.planning.risksOpportunitiesPage.categories.financial')}</option>
                <option value="compliance">{t('modules.planning.risksOpportunitiesPage.categories.compliance')}</option>
                <option value="reputation">{t('modules.planning.risksOpportunitiesPage.categories.reputation')}</option>
                <option value="technology">{t('modules.planning.risksOpportunitiesPage.categories.technology')}</option>
                <option value="market">{t('modules.planning.risksOpportunitiesPage.categories.market')}</option>
                <option value="other">{t('modules.planning.risksOpportunitiesPage.categories.other')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.context')}</label>
              <select value={form.context} onChange={(e) => setForm({...form, context: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="internal">{t('modules.planning.risksOpportunitiesPage.context.internal')}</option>
                <option value="external">{t('modules.planning.risksOpportunitiesPage.context.external')}</option>
                <option value="both">{t('modules.planning.risksOpportunitiesPage.context.both')}</option>
              </select>
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.title')}</label>
              <input type="text" value={form.title} onChange={(e) => setForm({...form, title: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('common.forms.description')}</label>
              <textarea value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="3" required />
            </div>
            {form.item_type === 'risk' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.probability')}</label>
                  <input type="number" min="1" max="5" value={form.probability} onChange={(e) => setForm({...form, probability: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.impact')}</label>
                  <input type="number" min="1" max="5" value={form.impact} onChange={(e) => setForm({...form, impact: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
                </div>
              </>
            )}
            {form.item_type === 'opportunity' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.feasibility')}</label>
                  <input type="number" min="1" max="5" value={form.feasibility} onChange={(e) => setForm({...form, feasibility: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.benefit')}</label>
                  <input type="number" min="1" max="5" value={form.benefit} onChange={(e) => setForm({...form, benefit: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
                </div>
              </>
            )}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.treatment')}</label>
              <select value={form.treatment} onChange={(e) => setForm({...form, treatment: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="avoid">{t('modules.planning.risksOpportunitiesPage.treatments.avoid')}</option>
                <option value="mitigate">{t('modules.planning.risksOpportunitiesPage.treatments.mitigate')}</option>
                <option value="transfer">{t('modules.planning.risksOpportunitiesPage.treatments.transfer')}</option>
                <option value="accept">{t('modules.planning.risksOpportunitiesPage.treatments.accept')}</option>
                <option value="exploit">{t('modules.planning.risksOpportunitiesPage.treatments.exploit')}</option>
                <option value="enhance">{t('modules.planning.risksOpportunitiesPage.treatments.enhance')}</option>
              </select>
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.risksOpportunitiesPage.fields.treatmentDescription')}</label>
              <textarea value={form.treatment_description} onChange={(e) => setForm({...form, treatment_description: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" />
            </div>
          </div>
          <div className="flex space-x-3">
            <button type="submit" disabled={saving} className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
              {saving ? t('common.messages.saving') : editingId ? t('common.buttons.update') : t('common.buttons.create')}
            </button>
            {editingId && <button type="button" onClick={closeForm} className="px-6 py-2 bg-slate-500 hover:bg-slate-600 dark:bg-slate-600 dark:hover:bg-slate-500 text-white rounded-lg">{t('common.buttons.cancel')}</button>}
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default RisksOpportunitiesPage;