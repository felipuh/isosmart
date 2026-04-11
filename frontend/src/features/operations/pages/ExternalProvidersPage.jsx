import React, { useCallback, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { showConfirm } from '../../../services/dialogs';
import { getExternalProviders, createExternalProvider, updateExternalProvider, deleteExternalProvider, getUsers } from '../api/operationsApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const ExternalProvidersPage = () => {
  const { t } = useI18n();
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({
    provider_code: '',
    provider_name: '',
    contact_person: '',
    email: '',
    phone: '',
    address: '',
    provision_type: 'product',
    products_services: '',
    evaluation_criteria: '',
    last_evaluation_date: '',
    evaluation_score: '',
    evaluation_notes: '',
    classification: 'conditional',
    performance_rating: '',
    controls_applied: '',
    responsible: user?.id || ''
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const resetForm = useCallback(() => {
    setForm({
      provider_code: '',
      provider_name: '',
      contact_person: '',
      email: '',
      phone: '',
      address: '',
      provision_type: 'product',
      products_services: '',
      evaluation_criteria: '',
      last_evaluation_date: '',
      evaluation_score: '',
      evaluation_notes: '',
      classification: 'conditional',
      performance_rating: '',
      controls_applied: '',
      responsible: user?.id || ''
    });
    setEditingId(null);
  }, [user?.id]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getExternalProviders({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error:', error);
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  const loadUsers = useCallback(async () => {
    try {
      const data = await getUsers({ organization_id: orgId });
      setUsers(normalizeList(data));
    } catch (error) {
      console.error('Error loading users:', error);
      setError(t('common.messages.errorTryAgain'));
    }
  }, [orgId, t]);

  useEffect(() => {
    if (orgId) {
      loadData();
      loadUsers();
    }
  }, [orgId, loadData, loadUsers]);

  useEffect(() => {
    if (location.pathname.endsWith('/new')) {
      resetForm();
      setShowForm(true);
    }
  }, [location.pathname, resetForm]);

  useEffect(() => {
    if (user?.id) {
      setForm(prev => ({ ...prev, responsible: prev.responsible || user.id }));
    }
  }, [user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError('');
      const payload = {
        ...form,
        organization_id: orgId,
        organization_name: orgName,
        evaluation_score: form.evaluation_score === '' ? null : Number(form.evaluation_score),
        performance_rating: form.performance_rating === '' ? null : Number(form.performance_rating),
        responsible: form.responsible || null
      };
      if (editingId) {
        await updateExternalProvider(editingId, payload);
      } else {
        await createExternalProvider(payload);
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
      provider_code: item.provider_code,
      provider_name: item.provider_name,
      contact_person: item.contact_person || '',
      email: item.email || '',
      phone: item.phone || '',
      address: item.address || '',
      provision_type: item.provision_type,
      products_services: item.products_services || '',
      evaluation_criteria: item.evaluation_criteria || '',
      last_evaluation_date: item.last_evaluation_date || '',
      evaluation_score: item.evaluation_score ?? '',
      evaluation_notes: item.evaluation_notes || '',
      classification: item.classification,
      performance_rating: item.performance_rating ?? '',
      controls_applied: item.controls_applied || '',
      responsible: item.responsible || ''
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.operations.externalProvidersPage.messages.confirmDelete'));
    if (!confirmed) return;
    try {
      await deleteExternalProvider(id);
      await loadData();
    } catch (error) {
      console.error('Error:', error);
      setError(t('common.messages.errorTryAgain'));
    }
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
        title={t('modules.operations.externalProvidersPage.title')}
        actionLabel={t('modules.operations.externalProvidersPage.buttons.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.externalProvidersPage.table.code')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.name')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.externalProvidersPage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.externalProvidersPage.table.classification')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.externalProvidersPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.provider_code}</td>
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{i.provider_name}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.provision_type_display}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.classification_display}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <CrudEmptyState message={t('modules.operations.externalProvidersPage.messages.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.operations.externalProvidersPage.modal.editTitle') : t('modules.operations.externalProvidersPage.modal.newTitle')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.externalProvidersPage.form.codeRequired')}</label>
              <input type="text" value={form.provider_code} onChange={(e) => setForm({...form, provider_code: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.externalProvidersPage.form.nameRequired')}</label>
              <input type="text" value={form.provider_name} onChange={(e) => setForm({...form, provider_name: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.externalProvidersPage.form.contact')}</label>
              <input type="text" value={form.contact_person} onChange={(e) => setForm({...form, contact_person: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('common.forms.email')}</label>
              <input type="email" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.externalProvidersPage.form.phone')}</label>
              <input type="text" value={form.phone} onChange={(e) => setForm({...form, phone: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.externalProvidersPage.form.address')}</label>
              <textarea value={form.address} onChange={(e) => setForm({...form, address: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.externalProvidersPage.form.provisionType')}</label>
              <select value={form.provision_type} onChange={(e) => setForm({...form, provision_type: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="product">{t('modules.operations.externalProvidersPage.options.provisionType.product')}</option>
                <option value="service">{t('modules.operations.externalProvidersPage.options.provisionType.service')}</option>
                <option value="process">{t('modules.operations.externalProvidersPage.options.provisionType.process')}</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.externalProvidersPage.form.productsServicesRequired')}</label>
              <input type="text" value={form.products_services} onChange={(e) => setForm({...form, products_services: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.externalProvidersPage.form.evaluationCriteriaRequired')}</label>
              <textarea value={form.evaluation_criteria} onChange={(e) => setForm({...form, evaluation_criteria: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.externalProvidersPage.form.lastEvaluation')}</label>
              <input type="date" value={form.last_evaluation_date} onChange={(e) => setForm({...form, last_evaluation_date: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.externalProvidersPage.form.score')}</label>
              <input type="number" min="0" max="100" value={form.evaluation_score} onChange={(e) => setForm({...form, evaluation_score: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.externalProvidersPage.form.classification')}</label>
              <select value={form.classification} onChange={(e) => setForm({...form, classification: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="approved">{t('modules.operations.externalProvidersPage.options.classification.approved')}</option>
                <option value="conditional">{t('modules.operations.externalProvidersPage.options.classification.conditional')}</option>
                <option value="not_approved">{t('modules.operations.externalProvidersPage.options.classification.notApproved')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.externalProvidersPage.form.performance')}</label>
              <input type="number" min="1" max="5" value={form.performance_rating} onChange={(e) => setForm({...form, performance_rating: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.externalProvidersPage.form.controlsApplied')}</label>
              <textarea value={form.controls_applied} onChange={(e) => setForm({...form, controls_applied: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.externalProvidersPage.form.responsible')}</label>
              <select value={form.responsible} onChange={(e) => setForm({...form, responsible: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="">{t('modules.operations.externalProvidersPage.form.unassigned')}</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name || u.username || u.email}</option>
                ))}
              </select>
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

export default ExternalProvidersPage;