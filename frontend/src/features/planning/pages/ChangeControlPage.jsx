import React, { useCallback, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { getChanges, createChange, updateChange, deleteChange } from '../api/planningApi';
import { showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const ChangeControlPage = () => {
  const { t } = useI18n();
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    change_number: '',
    title: '',
    description: '',
    change_type: 'process',
    reason: 'improvement',
    justification: '',
    urgency: 'medium',
    planned_date: '',
    affected_areas: '',
    impact_assessment: '',
    potential_risks: '',
    mitigation_plan: '',
    status: 'draft'
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getChanges({ organization_id: orgId });
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
        requested_by: user?.id || null
      };
      if (editingId) {
        await updateChange(editingId, payload);
      } else {
        await createChange(payload);
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
      change_number: item.change_number,
      title: item.title,
      description: item.description || '',
      change_type: item.change_type,
      reason: item.reason,
      justification: item.justification || '',
      urgency: item.urgency,
      planned_date: item.planned_date,
      affected_areas: item.affected_areas || '',
      impact_assessment: item.impact_assessment || '',
      potential_risks: item.potential_risks || '',
      mitigation_plan: item.mitigation_plan || '',
      status: item.status
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.planning.changeControlPage.deleteConfirm'));
    if (!confirmed) return;
    try {
      await deleteChange(id);
      await loadData();
    } catch (error) {
      console.error('Error:', error);
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const resetForm = () => {
    setForm({
      change_number: '',
      title: '',
      description: '',
      change_type: 'process',
      reason: 'improvement',
      justification: '',
      urgency: 'medium',
      planned_date: '',
      affected_areas: '',
      impact_assessment: '',
      potential_risks: '',
      mitigation_plan: '',
      status: 'draft'
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

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="space-y-6">
      <CrudPageHeader
        title={t('modules.planning.changeControlPage.title')}
        actionLabel={t('modules.planning.changeControlPage.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.changeControlPage.table.number')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.changeControlPage.table.title')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.changeControlPage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.changeControlPage.table.urgency')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.changeControlPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.change_number}</td>
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{i.title}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.change_type_display}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.urgency_display}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.status_display}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <CrudEmptyState message={t('modules.planning.changeControlPage.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.planning.changeControlPage.edit') : t('modules.planning.changeControlPage.new')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.number')}</label>
              <input type="text" value={form.change_number} onChange={(e) => setForm({...form, change_number: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.title')}</label>
              <input type="text" value={form.title} onChange={(e) => setForm({...form, title: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('common.forms.description')}</label>
              <textarea value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.type')}</label>
              <select value={form.change_type} onChange={(e) => setForm({...form, change_type: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="process">{t('modules.planning.changeControlPage.types.process')}</option>
                <option value="procedure">{t('modules.planning.changeControlPage.types.procedure')}</option>
                <option value="resource">{t('modules.planning.changeControlPage.types.resource')}</option>
                <option value="technology">{t('modules.planning.changeControlPage.types.technology')}</option>
                <option value="structure">{t('modules.planning.changeControlPage.types.structure')}</option>
                <option value="scope">{t('modules.planning.changeControlPage.types.scope')}</option>
                <option value="policy">{t('modules.planning.changeControlPage.types.policy')}</option>
                <option value="other">{t('modules.planning.changeControlPage.types.other')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.reason')}</label>
              <select value={form.reason} onChange={(e) => setForm({...form, reason: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="improvement">{t('modules.planning.changeControlPage.reasons.improvement')}</option>
                <option value="correction">{t('modules.planning.changeControlPage.reasons.correction')}</option>
                <option value="compliance">{t('modules.planning.changeControlPage.reasons.compliance')}</option>
                <option value="risk_mitigation">{t('modules.planning.changeControlPage.reasons.riskMitigation')}</option>
                <option value="opportunity">{t('modules.planning.changeControlPage.reasons.opportunity')}</option>
                <option value="external_requirement">{t('modules.planning.changeControlPage.reasons.externalRequirement')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.urgency')}</label>
              <select value={form.urgency} onChange={(e) => setForm({...form, urgency: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="low">{t('modules.planning.changeControlPage.urgency.low')}</option>
                <option value="medium">{t('modules.planning.changeControlPage.urgency.medium')}</option>
                <option value="high">{t('modules.planning.changeControlPage.urgency.high')}</option>
                <option value="critical">{t('modules.planning.changeControlPage.urgency.critical')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.plannedDate')}</label>
              <input type="date" value={form.planned_date} onChange={(e) => setForm({...form, planned_date: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('common.forms.status')}</label>
              <select value={form.status} onChange={(e) => setForm({...form, status: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="draft">{t('modules.planning.changeControlPage.statuses.draft')}</option>
                <option value="submitted">{t('modules.planning.changeControlPage.statuses.submitted')}</option>
                <option value="under_review">{t('modules.planning.changeControlPage.statuses.underReview')}</option>
                <option value="approved">{t('modules.planning.changeControlPage.statuses.approved')}</option>
                <option value="rejected">{t('modules.planning.changeControlPage.statuses.rejected')}</option>
                <option value="in_implementation">{t('modules.planning.changeControlPage.statuses.inImplementation')}</option>
                <option value="implemented">{t('modules.planning.changeControlPage.statuses.implemented')}</option>
                <option value="verified">{t('modules.planning.changeControlPage.statuses.verified')}</option>
                <option value="closed">{t('modules.planning.changeControlPage.statuses.closed')}</option>
              </select>
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.justification')}</label>
              <textarea value={form.justification} onChange={(e) => setForm({...form, justification: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.affectedAreas')}</label>
              <textarea value={form.affected_areas} onChange={(e) => setForm({...form, affected_areas: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.impactAssessment')}</label>
              <textarea value={form.impact_assessment} onChange={(e) => setForm({...form, impact_assessment: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.potentialRisks')}</label>
              <textarea value={form.potential_risks} onChange={(e) => setForm({...form, potential_risks: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.changeControlPage.fields.mitigationPlan')}</label>
              <textarea value={form.mitigation_plan} onChange={(e) => setForm({...form, mitigation_plan: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" />
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

export default ChangeControlPage;