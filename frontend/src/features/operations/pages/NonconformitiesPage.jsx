import React, { useCallback, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { showConfirm } from '../../../services/dialogs';
import { getNonconformities, createNonconformity, updateNonconformity, deleteNonconformity, getUsers } from '../api/operationsApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const NonconformitiesPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({
    nc_number: '',
    title: '',
    description: '',
    nc_type: 'product',
    severity: 'minor',
    detection_date: '',
    detection_stage: 'production',
    detected_by: '',
    affected_product_service: '',
    batch_lot_number: '',
    quantity_affected: '',
    affects_customer: false,
    customer_name: '',
    customer_notified: false,
    notification_date: '',
    responsible: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const loadUsers = useCallback(async () => {
    try {
      const data = await getUsers({ organization_id: orgId });
      setUsers(normalizeList(data));
    } catch (error) {
      console.error('Error loading users:', error);
      setError(t('common.messages.errorTryAgain'));
    }
  }, [orgId, t]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getNonconformities({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error:', error);
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setLoading(false);
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
        status: 'identified',
        detected_by: form.detected_by || null,
        responsible: form.responsible || null,
        quantity_affected: form.quantity_affected === '' ? null : Number(form.quantity_affected)
      };
      if (editingId) {
        await updateNonconformity(editingId, payload);
      } else {
        await createNonconformity(payload);
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
      nc_number: item.nc_number,
      title: item.title,
      description: item.description || '',
      nc_type: item.nc_type,
      severity: item.severity,
      detection_date: item.detection_date,
      detection_stage: item.detection_stage,
      detected_by: item.detected_by || '',
      affected_product_service: item.affected_product_service,
      batch_lot_number: item.batch_lot_number || '',
      quantity_affected: item.quantity_affected ?? '',
      affects_customer: item.affects_customer,
      customer_name: item.customer_name || '',
      customer_notified: item.customer_notified || false,
      notification_date: item.notification_date || '',
      responsible: item.responsible || ''
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.operations.nonconformitiesOpsPage.deleteConfirm'));
    if (!confirmed) return;
    try {
      await deleteNonconformity(id);
      await loadData();
    } catch (error) {
      console.error('Error:', error);
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const resetForm = () => {
    setForm({
      nc_number: '',
      title: '',
      description: '',
      nc_type: 'product',
      severity: 'minor',
      detection_date: '',
      detection_stage: 'production',
      detected_by: '',
      affected_product_service: '',
      batch_lot_number: '',
      quantity_affected: '',
      affects_customer: false,
      customer_name: '',
      customer_notified: false,
      notification_date: '',
      responsible: ''
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
        title={t('modules.operations.nonconformitiesOpsPage.title')}
        actionLabel={t('modules.operations.nonconformitiesOpsPage.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.nonconformitiesOpsPage.table.number')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.nonconformitiesOpsPage.table.title')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.nonconformitiesOpsPage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.nonconformitiesOpsPage.table.severity')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.nonconformitiesOpsPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.map(item => (
              <tr key={item.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.nc_number}</td>
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{item.title}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.nc_type_display}</td>
                <td className="px-6 py-4">
                  <span className={`badge-base ${
                    item.severity === 'critical' ? 'badge-danger' :
                    item.severity === 'major' ? 'badge-caution' :
                    'badge-warning'
                  }`}>
                    {item.severity_display}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{item.status_display}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <CrudEmptyState message={t('modules.operations.nonconformitiesOpsPage.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.operations.nonconformitiesOpsPage.edit') : t('modules.operations.nonconformitiesOpsPage.new')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.nonconformitiesOpsPage.fields.ncNumber')}</label>
              <input type="text" value={form.nc_number} onChange={(e) => setForm({...form, nc_number: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.nonconformitiesOpsPage.fields.type')}</label>
              <select value={form.nc_type} onChange={(e) => setForm({...form, nc_type: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="product">{t('modules.operations.nonconformitiesOpsPage.types.product')}</option>
                <option value="service">{t('modules.operations.nonconformitiesOpsPage.types.service')}</option>
                <option value="process">{t('modules.operations.nonconformitiesOpsPage.types.process')}</option>
                <option value="documentation">{t('modules.operations.nonconformitiesOpsPage.types.documentation')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.nonconformitiesOpsPage.fields.severity')}</label>
              <select value={form.severity} onChange={(e) => setForm({...form, severity: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="minor">{t('modules.operations.nonconformitiesOpsPage.severities.minor')}</option>
                <option value="major">{t('modules.operations.nonconformitiesOpsPage.severities.major')}</option>
                <option value="critical">{t('modules.operations.nonconformitiesOpsPage.severities.critical')}</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.nonconformitiesOpsPage.fields.title')}</label>
              <input type="text" value={form.title} onChange={(e) => setForm({...form, title: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.nonconformitiesOpsPage.fields.detectionDate')}</label>
              <input type="date" value={form.detection_date} onChange={(e) => setForm({...form, detection_date: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.nonconformitiesOpsPage.fields.detectionStage')}</label>
              <select value={form.detection_stage} onChange={(e) => setForm({...form, detection_stage: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="production">{t('modules.operations.nonconformitiesOpsPage.detectionStages.production')}</option>
                <option value="pre_delivery">{t('modules.operations.nonconformitiesOpsPage.detectionStages.preDelivery')}</option>
                <option value="post_delivery">{t('modules.operations.nonconformitiesOpsPage.detectionStages.postDelivery')}</option>
                <option value="in_use">{t('modules.operations.nonconformitiesOpsPage.detectionStages.inUse')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.nonconformitiesOpsPage.fields.detectedBy')}</label>
              <select value={form.detected_by} onChange={(e) => setForm({...form, detected_by: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="">{t('modules.operations.nonconformitiesOpsPage.fields.unassigned')}</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name || u.username || u.email}</option>
                ))}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.nonconformitiesOpsPage.fields.affectedProductService')}</label>
              <input type="text" value={form.affected_product_service} onChange={(e) => setForm({...form, affected_product_service: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.nonconformitiesOpsPage.fields.batchLot')}</label>
              <input type="text" value={form.batch_lot_number} onChange={(e) => setForm({...form, batch_lot_number: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.nonconformitiesOpsPage.fields.quantityAffected')}</label>
              <input type="number" value={form.quantity_affected} onChange={(e) => setForm({...form, quantity_affected: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div className="flex items-center">
              <label className="flex items-center space-x-2">
                <input type="checkbox" checked={form.affects_customer} onChange={(e) => setForm({...form, affects_customer: e.target.checked})} className="rounded" />
                <span className="text-sm text-slate-700 dark:text-slate-300">{t('modules.operations.nonconformitiesOpsPage.fields.affectsCustomer')}</span>
              </label>
            </div>
            {form.affects_customer && (
              <>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.nonconformitiesOpsPage.fields.customer')}</label>
                  <input type="text" value={form.customer_name} onChange={(e) => setForm({...form, customer_name: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
                </div>
                <div className="flex items-center">
                  <label className="flex items-center space-x-2">
                    <input type="checkbox" checked={form.customer_notified} onChange={(e) => setForm({...form, customer_notified: e.target.checked})} className="rounded" />
                    <span className="text-sm text-slate-700 dark:text-slate-300">{t('modules.operations.nonconformitiesOpsPage.fields.customerNotified')}</span>
                  </label>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.nonconformitiesOpsPage.fields.notificationDate')}</label>
                  <input type="date" value={form.notification_date} onChange={(e) => setForm({...form, notification_date: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
                </div>
              </>
            )}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.nonconformitiesOpsPage.fields.responsible')}</label>
              <select value={form.responsible} onChange={(e) => setForm({...form, responsible: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="">{t('modules.operations.nonconformitiesOpsPage.fields.unassigned')}</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name || u.username || u.email}</option>
                ))}
              </select>
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

export default NonconformitiesPage;