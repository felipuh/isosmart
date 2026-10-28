import React, { useCallback, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { getCommunications, createCommunication, updateCommunication, deleteCommunication } from '../api/resourcesApi';
import { showAlert, showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const CommunicationsPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    title: '',
    description: '',
    communication_type: 'internal',
    method: 'email',
    frequency: 'one_time',
    content_summary: '',
    scheduled_date: '',
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
      const data = await getCommunications({ organization_id: orgId });
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
      await showAlert(t('modules.resources.communicationsPage.messages.selectOrganization'));
      return;
    }
    try {
      setSaving(true);
      setError('');
      const payload = { ...form, organization_id: orgId, organization_name: orgName };
      if (editingId) {
        await updateCommunication(editingId, payload);
      } else {
        await createCommunication(payload);
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
      title: item.title,
      description: item.description || '',
      communication_type: item.communication_type,
      method: item.method,
      frequency: item.frequency,
      content_summary: item.content_summary || '',
      scheduled_date: item.scheduled_date || '',
      target_audience: item.target_audience || ''
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.resources.communicationsPage.messages.confirmDelete'));
    if (!confirmed) return;
    try {
      await deleteCommunication(id);
      await loadData();
    } catch (error) {
      console.error('Error:', error);
      setError(t('common.messages.errorTryAgain'));
    }
  };

  const resetForm = () => {
    setForm({
      title: '',
      description: '',
      communication_type: 'internal',
      method: 'email',
      frequency: 'one_time',
      content_summary: '',
      scheduled_date: '',
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
        title={t('modules.resources.communicationsPage.title')}
        actionLabel={t('modules.resources.communicationsPage.buttons.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.communicationsPage.table.title')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.communicationsPage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.communicationsPage.table.method')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.date')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.communicationsPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{i.title}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.communication_type_display}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.method_display}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.scheduled_date || t('modules.resources.communicationsPage.table.noDate')}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.status_display}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <CrudEmptyState message={t('modules.resources.communicationsPage.messages.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.resources.communicationsPage.modal.editTitle') : t('modules.resources.communicationsPage.modal.newTitle')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.communicationsPage.form.titleRequired')}</label>
              <input type="text" value={form.title} onChange={(e) => setForm({...form, title: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.communicationsPage.form.type')}</label>
              <select value={form.communication_type} onChange={(e) => setForm({...form, communication_type: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="internal">{t('modules.resources.communicationsPage.options.type.internal')}</option>
                <option value="external">{t('modules.resources.communicationsPage.options.type.external')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.communicationsPage.form.method')}</label>
              <select value={form.method} onChange={(e) => setForm({...form, method: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="email">{t('modules.resources.communicationsPage.options.method.email')}</option>
                <option value="meeting">{t('modules.resources.communicationsPage.options.method.meeting')}</option>
                <option value="memo">{t('modules.resources.communicationsPage.options.method.memo')}</option>
                <option value="report">{t('modules.resources.communicationsPage.options.method.report')}</option>
                <option value="presentation">{t('modules.resources.communicationsPage.options.method.presentation')}</option>
                <option value="intranet">{t('modules.resources.communicationsPage.options.method.intranet')}</option>
                <option value="notice_board">{t('modules.resources.communicationsPage.options.method.noticeBoard')}</option>
                <option value="other">{t('modules.resources.communicationsPage.options.method.other')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.communicationsPage.form.frequency')}</label>
              <select value={form.frequency} onChange={(e) => setForm({...form, frequency: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="one_time">{t('modules.resources.communicationsPage.options.frequency.oneTime')}</option>
                <option value="daily">{t('modules.resources.communicationsPage.options.frequency.daily')}</option>
                <option value="weekly">{t('modules.resources.communicationsPage.options.frequency.weekly')}</option>
                <option value="monthly">{t('modules.resources.communicationsPage.options.frequency.monthly')}</option>
                <option value="quarterly">{t('modules.resources.communicationsPage.options.frequency.quarterly')}</option>
                <option value="annual">{t('modules.resources.communicationsPage.options.frequency.annual')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.communicationsPage.form.scheduledDate')}</label>
              <input type="date" value={form.scheduled_date} onChange={(e) => setForm({...form, scheduled_date: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.communicationsPage.form.targetAudienceRequired')}</label>
              <input type="text" value={form.target_audience} onChange={(e) => setForm({...form, target_audience: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.communicationsPage.form.contentSummary')}</label>
              <textarea value={form.content_summary} onChange={(e) => setForm({...form, content_summary: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="3" required />
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

export default CommunicationsPage;