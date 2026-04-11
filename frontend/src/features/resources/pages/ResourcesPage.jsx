import React, { useCallback, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { getResources, createResource, updateResource, deleteResource } from '../api/resourcesApi';
import { showAlert, showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const ResourcesPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [resources, setResources] = useState([]);
  const [form, setForm] = useState({
    resource_type: 'human',
    name: '',
    code: '',
    description: '',
    quantity: 1,
    unit: '',
    location: '',
    status: 'available'
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const loadResources = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getResources({ organization_id: orgId });
      setResources(normalizeList(data));
    } catch (error) {
      console.error('Error:', error);
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  useEffect(() => {
    if (orgId) {
      loadResources();
    } else {
      setLoading(false);
    }
  }, [orgId, loadResources]);

  useEffect(() => {
    if (location.pathname.endsWith('/new')) {
      resetForm();
      setShowForm(true);
    }
  }, [location.pathname]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!orgId) {
      await showAlert(t('modules.resources.resourcesPage.messages.selectOrganization'));
      return;
    }
    try {
      setSaving(true);
      setError('');
      const payload = { ...form, organization_id: orgId, organization_name: orgName };
      if (editingId) {
        await updateResource(editingId, payload);
      } else {
        await createResource(payload);
      }
      resetForm();
      await loadResources();
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

  const handleEdit = (resource) => {
    setForm({
      resource_type: resource.resource_type,
      name: resource.name,
      code: resource.code,
      description: resource.description || '',
      quantity: resource.quantity,
      unit: resource.unit || '',
      location: resource.location || '',
      status: resource.status
    });
    setEditingId(resource.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.resources.resourcesPage.messages.confirmDelete'));
    if (!confirmed) return;
    try {
      await deleteResource(id);
      await loadResources();
    } catch (error) {
      console.error('Error:', error);
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const resetForm = () => {
    setForm({
      resource_type: 'human',
      name: '',
      code: '',
      description: '',
      quantity: 1,
      unit: '',
      location: '',
      status: 'available'
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
        title={t('modules.resources.resourcesPage.title')}
        actionLabel={t('modules.resources.resourcesPage.buttons.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.resourcesPage.table.code')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.name')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.resourcesPage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.resourcesPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {resources.map(r => (
              <tr key={r.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{r.code}</td>
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{r.name}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{r.resource_type_display}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(r)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(r.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {resources.length === 0 && <CrudEmptyState message={t('modules.resources.resourcesPage.messages.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.resources.resourcesPage.modal.editTitle') : t('modules.resources.resourcesPage.modal.newTitle')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.resourcesPage.form.type')}</label>
              <select value={form.resource_type} onChange={(e) => setForm({...form, resource_type: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required>
                <option value="human">{t('modules.resources.resourcesPage.options.type.human')}</option>
                <option value="infrastructure">{t('modules.resources.resourcesPage.options.type.infrastructure')}</option>
                <option value="technology">{t('modules.resources.resourcesPage.options.type.technology')}</option>
                <option value="material">{t('modules.resources.resourcesPage.options.type.material')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.resourcesPage.form.nameRequired')}</label>
              <input type="text" value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.resourcesPage.form.codeRequired')}</label>
              <input type="text" value={form.code} onChange={(e) => setForm({...form, code: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
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

export default ResourcesPage;