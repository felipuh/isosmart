import React, { useCallback, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { showConfirm } from '../../../services/dialogs';
import { getCustomerRequirements, createCustomerRequirement, updateCustomerRequirement, deleteCustomerRequirement } from '../api/operationsApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const CustomerRequirementsPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    customer_name: '',
    customer_code: '',
    contact_person: '',
    requirement_code: '',
    requirement_title: '',
    description: '',
    requirement_type: 'product',
    communication_date: '',
    communication_method: '',
    can_meet_requirement: true
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
      const data = await getCustomerRequirements({ organization_id: orgId });
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
      const payload = { ...form, organization_id: orgId, organization_name: orgName, status: 'identified' };
      if (editingId) {
        await updateCustomerRequirement(editingId, payload);
      } else {
        await createCustomerRequirement(payload);
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
      customer_name: item.customer_name,
      customer_code: item.customer_code || '',
      contact_person: item.contact_person || '',
      requirement_code: item.requirement_code,
      requirement_title: item.requirement_title,
      description: item.description || '',
      requirement_type: item.requirement_type,
      communication_date: item.communication_date,
      communication_method: item.communication_method || '',
      can_meet_requirement: item.can_meet_requirement
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.operations.customerRequirementsPage.messages.confirmDelete'));
    if (!confirmed) return;
    try {
      await deleteCustomerRequirement(id);
      await loadData();
    } catch (error) {
      console.error('Error:', error);
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const resetForm = () => {
    setForm({
      customer_name: '',
      customer_code: '',
      contact_person: '',
      requirement_code: '',
      requirement_title: '',
      description: '',
      requirement_type: 'product',
      communication_date: '',
      communication_method: '',
      can_meet_requirement: true
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
        title={t('modules.operations.customerRequirementsPage.title')}
        actionLabel={t('modules.operations.customerRequirementsPage.buttons.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.customerRequirementsPage.table.code')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.customerRequirementsPage.table.customer')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.customerRequirementsPage.table.title')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.customerRequirementsPage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.customerRequirementsPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.map(item => (
              <tr key={item.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.requirement_code}</td>
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{item.customer_name}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.requirement_title}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.requirement_type_display}</td>
                <td className="px-6 py-4">
                  <span className={`badge-base ${
                    item.status === 'fulfilled' ? 'badge-success' :
                    item.status === 'in_progress' ? 'badge-info' :
                    'badge-warning'
                  }`}>
                    {item.status_display}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <CrudEmptyState message={t('modules.operations.customerRequirementsPage.messages.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.operations.customerRequirementsPage.modal.editTitle') : t('modules.operations.customerRequirementsPage.modal.newTitle')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.customerRequirementsPage.form.customerRequired')}</label>
              <input type="text" value={form.customer_name} onChange={(e) => setForm({...form, customer_name: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.customerRequirementsPage.form.customerCode')}</label>
              <input type="text" value={form.customer_code} onChange={(e) => setForm({...form, customer_code: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.customerRequirementsPage.form.contact')}</label>
              <input type="text" value={form.contact_person} onChange={(e) => setForm({...form, contact_person: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.customerRequirementsPage.form.codeRequired')}</label>
              <input type="text" value={form.requirement_code} onChange={(e) => setForm({...form, requirement_code: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.customerRequirementsPage.form.type')}</label>
              <select value={form.requirement_type} onChange={(e) => setForm({...form, requirement_type: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="product">{t('modules.operations.customerRequirementsPage.options.type.product')}</option>
                <option value="service">{t('modules.operations.customerRequirementsPage.options.type.service')}</option>
                <option value="delivery">{t('modules.operations.customerRequirementsPage.options.type.delivery')}</option>
                <option value="quality">{t('modules.operations.customerRequirementsPage.options.type.quality')}</option>
                <option value="regulatory">{t('modules.operations.customerRequirementsPage.options.type.regulatory')}</option>
                <option value="other">{t('modules.operations.customerRequirementsPage.options.type.other')}</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.customerRequirementsPage.form.titleRequired')}</label>
              <input type="text" value={form.requirement_title} onChange={(e) => setForm({...form, requirement_title: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.customerRequirementsPage.form.communicationDateRequired')}</label>
              <input type="date" value={form.communication_date} onChange={(e) => setForm({...form, communication_date: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.customerRequirementsPage.form.method')}</label>
              <input type="text" value={form.communication_method} onChange={(e) => setForm({...form, communication_method: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" placeholder={t('modules.operations.customerRequirementsPage.form.methodPlaceholder')} />
            </div>
            <div className="flex items-center">
              <label className="flex items-center space-x-2">
                <input type="checkbox" checked={form.can_meet_requirement} onChange={(e) => setForm({...form, can_meet_requirement: e.target.checked})} className="rounded" />
                <span className="text-sm text-slate-700 dark:text-slate-300">{t('modules.operations.customerRequirementsPage.form.canMeetRequirement')}</span>
              </label>
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('common.forms.description')}</label>
              <textarea value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="3" required />
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

export default CustomerRequirementsPage;