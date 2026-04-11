import React, { useCallback, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { getAwareness, createAwareness, updateAwareness, deleteAwareness } from '../api/resourcesApi';
import { showAlert, showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const AwarenessPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    activity_name: '',
    description: '',
    awareness_type: 'policy',
    method: 'meeting',
    date: '',
    target_audience: ''
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
      const data = await getAwareness({ organization_id: orgId });
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
    } else {
      setLoading(false);
    }
  }, [orgId, loadData]);

  useEffect(() => {
    if (location.pathname.endsWith('/new')) {
      resetForm();
      setShowForm(true);
    }
  }, [location.pathname]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!orgId) {
      await showAlert(t('modules.resources.awarenessPage.messages.selectOrganization'));
      return;
    }
    try {
      setSaving(true);
      setError('');
      const payload = { ...form, organization_id: orgId, organization_name: orgName };
      if (editingId) {
        await updateAwareness(editingId, payload);
      } else {
        await createAwareness(payload);
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
      activity_name: item.activity_name,
      description: item.description || '',
      awareness_type: item.awareness_type,
      method: item.method,
      date: item.date,
      target_audience: item.target_audience || ''
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.resources.awarenessPage.messages.confirmDelete'));
    if (!confirmed) return;
    try {
      await deleteAwareness(id);
      await loadData();
    } catch (error) {
      console.error('Error:', error);
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const resetForm = () => {
    setForm({
      activity_name: '',
      description: '',
      awareness_type: 'policy',
      method: 'meeting',
      date: '',
      target_audience: ''
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
        title={t('modules.resources.awarenessPage.title')}
        actionLabel={t('modules.resources.awarenessPage.buttons.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.awarenessPage.table.activity')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.date')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.awarenessPage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.awarenessPage.table.method')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.awarenessPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{i.activity_name}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.date}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.awareness_type_display}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.method_display}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <CrudEmptyState message={t('modules.resources.awarenessPage.messages.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.resources.awarenessPage.modal.editTitle') : t('modules.resources.awarenessPage.modal.newTitle')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.awarenessPage.form.activityRequired')}</label>
              <input type="text" value={form.activity_name} onChange={(e) => setForm({...form, activity_name: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.awarenessPage.form.dateRequired')}</label>
              <input type="date" value={form.date} onChange={(e) => setForm({...form, date: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.awarenessPage.form.type')}</label>
              <select value={form.awareness_type} onChange={(e) => setForm({...form, awareness_type: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="policy">{t('modules.resources.awarenessPage.options.type.policy')}</option>
                <option value="objectives">{t('modules.resources.awarenessPage.options.type.objectives')}</option>
                <option value="contribution">{t('modules.resources.awarenessPage.options.type.contribution')}</option>
                <option value="improvement">{t('modules.resources.awarenessPage.options.type.improvement')}</option>
                <option value="nonconformity">{t('modules.resources.awarenessPage.options.type.nonconformity')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.awarenessPage.form.method')}</label>
              <select value={form.method} onChange={(e) => setForm({...form, method: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="meeting">{t('modules.resources.awarenessPage.options.method.meeting')}</option>
                <option value="training">{t('modules.resources.awarenessPage.options.method.training')}</option>
                <option value="email">{t('modules.resources.awarenessPage.options.method.email')}</option>
                <option value="poster">{t('modules.resources.awarenessPage.options.method.poster')}</option>
                <option value="intranet">{t('modules.resources.awarenessPage.options.method.intranet')}</option>
                <option value="video">{t('modules.resources.awarenessPage.options.method.video')}</option>
                <option value="other">{t('modules.resources.awarenessPage.options.method.other')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.awarenessPage.form.targetAudienceRequired')}</label>
              <input type="text" value={form.target_audience} onChange={(e) => setForm({...form, target_audience: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-2">
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

export default AwarenessPage;