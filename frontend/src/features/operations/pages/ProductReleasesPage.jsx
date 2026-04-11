import React, { useCallback, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { showConfirm } from '../../../services/dialogs';
import { getProductReleases, createProductRelease, updateProductRelease, deleteProductRelease, getUsers } from '../api/operationsApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const ProductReleasesPage = () => {
  const { t } = useI18n();
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({
    release_code: '',
    product_service_name: '',
    batch_lot_number: '',
    release_date: '',
    quantity_released: '',
    unit: '',
    verification_performed: false,
    verification_results: '',
    acceptance_criteria_met: false,
    criteria_details: '',
    authorized_by: user?.id || '',
    status: 'pending',
    customer_name: '',
    delivery_date: '',
    notes: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const resetForm = useCallback(() => {
    setForm({
      release_code: '',
      product_service_name: '',
      batch_lot_number: '',
      release_date: '',
      quantity_released: '',
      unit: '',
      verification_performed: false,
      verification_results: '',
      acceptance_criteria_met: false,
      criteria_details: '',
      authorized_by: user?.id || '',
      status: 'pending',
      customer_name: '',
      delivery_date: '',
      notes: ''
    });
    setEditingId(null);
  }, [user?.id]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getProductReleases({ organization_id: orgId });
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
      setForm(prev => ({ ...prev, authorized_by: prev.authorized_by || user.id }));
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
        quantity_released: form.quantity_released === '' ? null : Number(form.quantity_released),
        authorized_by: form.authorized_by || null
      };
      if (editingId) {
        await updateProductRelease(editingId, payload);
      } else {
        await createProductRelease(payload);
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
      release_code: item.release_code,
      product_service_name: item.product_service_name,
      batch_lot_number: item.batch_lot_number || '',
      release_date: item.release_date,
      quantity_released: item.quantity_released ?? '',
      unit: item.unit || '',
      verification_performed: item.verification_performed || false,
      verification_results: item.verification_results || '',
      acceptance_criteria_met: item.acceptance_criteria_met || false,
      criteria_details: item.criteria_details || '',
      authorized_by: item.authorized_by || '',
      status: item.status,
      customer_name: item.customer_name || '',
      delivery_date: item.delivery_date || '',
      notes: item.notes || ''
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.operations.productReleasesPage.messages.confirmDelete'));
    if (!confirmed) return;
    try {
      await deleteProductRelease(id);
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
        title={t('modules.operations.productReleasesPage.title')}
        actionLabel={t('modules.operations.productReleasesPage.buttons.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.productReleasesPage.table.code')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.productReleasesPage.table.productService')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.date')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.productReleasesPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.release_code}</td>
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{i.product_service_name}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.release_date}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.status_display}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <CrudEmptyState message={t('modules.operations.productReleasesPage.messages.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.operations.productReleasesPage.modal.editTitle') : t('modules.operations.productReleasesPage.modal.newTitle')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.productReleasesPage.form.codeRequired')}</label>
              <input type="text" value={form.release_code} onChange={(e) => setForm({...form, release_code: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.productReleasesPage.form.productServiceRequired')}</label>
              <input type="text" value={form.product_service_name} onChange={(e) => setForm({...form, product_service_name: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.productReleasesPage.form.batchLot')}</label>
              <input type="text" value={form.batch_lot_number} onChange={(e) => setForm({...form, batch_lot_number: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.productReleasesPage.form.dateRequired')}</label>
              <input type="date" value={form.release_date} onChange={(e) => setForm({...form, release_date: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.productReleasesPage.form.quantityRequired')}</label>
              <input type="number" value={form.quantity_released} onChange={(e) => setForm({...form, quantity_released: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.productReleasesPage.form.unit')}</label>
              <input type="text" value={form.unit} onChange={(e) => setForm({...form, unit: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div className="flex items-center">
              <label className="flex items-center space-x-2">
                <input type="checkbox" checked={form.verification_performed} onChange={(e) => setForm({...form, verification_performed: e.target.checked})} className="rounded" />
                <span className="text-sm text-slate-700 dark:text-slate-300">{t('modules.operations.productReleasesPage.form.verificationPerformed')}</span>
              </label>
            </div>
            <div className="flex items-center">
              <label className="flex items-center space-x-2">
                <input type="checkbox" checked={form.acceptance_criteria_met} onChange={(e) => setForm({...form, acceptance_criteria_met: e.target.checked})} className="rounded" />
                <span className="text-sm text-slate-700 dark:text-slate-300">{t('modules.operations.productReleasesPage.form.criteriaMet')}</span>
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.productReleasesPage.form.authorizedBy')}</label>
              <select value={form.authorized_by} onChange={(e) => setForm({...form, authorized_by: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="">{t('modules.operations.productReleasesPage.form.unassigned')}</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name || u.username || u.email}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('common.forms.status')}</label>
              <select value={form.status} onChange={(e) => setForm({...form, status: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="pending">{t('modules.operations.productReleasesPage.options.status.pending')}</option>
                <option value="approved">{t('modules.operations.productReleasesPage.options.status.approved')}</option>
                <option value="released">{t('modules.operations.productReleasesPage.options.status.released')}</option>
                <option value="rejected">{t('modules.operations.productReleasesPage.options.status.rejected')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.productReleasesPage.form.customer')}</label>
              <input type="text" value={form.customer_name} onChange={(e) => setForm({...form, customer_name: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.productReleasesPage.form.deliveryDate')}</label>
              <input type="date" value={form.delivery_date} onChange={(e) => setForm({...form, delivery_date: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.productReleasesPage.form.verificationResults')}</label>
              <textarea value={form.verification_results} onChange={(e) => setForm({...form, verification_results: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.productReleasesPage.form.criteriaDetails')}</label>
              <textarea value={form.criteria_details} onChange={(e) => setForm({...form, criteria_details: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.productReleasesPage.form.notes')}</label>
              <textarea value={form.notes} onChange={(e) => setForm({...form, notes: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" />
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

export default ProductReleasesPage;