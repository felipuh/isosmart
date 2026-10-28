import React, { useCallback, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { getActions, createAction, updateAction, deleteAction, getObjectives, getUsers } from '../api/planningApi';
import { showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const ObjectiveActionsPage = () => {
  const { t } = useI18n();
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [objectives, setObjectives] = useState([]);
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({
    objective: '',
    action_number: 1,
    description: '',
    what_will_be_done: '',
    how_will_be_done: '',
    responsible: user?.id || '',
    due_date: '',
    status: 'planned',
    progress_percentage: 0,
    resources_needed: '',
    estimated_cost: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const resetForm = useCallback(() => {
    setForm({
      objective: '',
      action_number: 1,
      description: '',
      what_will_be_done: '',
      how_will_be_done: '',
      responsible: user?.id || '',
      due_date: '',
      status: 'planned',
      progress_percentage: 0,
      resources_needed: '',
      estimated_cost: ''
    });
    setEditingId(null);
  }, [user?.id]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getActions({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error:', error);
      setError(t('common.messages.errorTryAgain'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  const loadObjectives = useCallback(async () => {
    try {
      const data = await getObjectives({ organization_id: orgId });
      setObjectives(normalizeList(data));
    } catch (error) {
      console.error('Error loading objectives:', error);
      setError(t('common.messages.errorTryAgain'));
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
      loadObjectives();
      loadUsers();
    }
  }, [orgId, loadData, loadObjectives, loadUsers]);

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
        responsible: form.responsible || null,
        estimated_cost: form.estimated_cost === '' ? null : Number(form.estimated_cost)
      };
      if (editingId) {
        await updateAction(editingId, payload);
      } else {
        await createAction(payload);
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
      objective: item.objective,
      action_number: item.action_number,
      description: item.description || '',
      what_will_be_done: item.what_will_be_done || '',
      how_will_be_done: item.how_will_be_done || '',
      responsible: item.responsible || '',
      due_date: item.due_date,
      status: item.status,
      progress_percentage: item.progress_percentage || 0,
      resources_needed: item.resources_needed || '',
      estimated_cost: item.estimated_cost ?? ''
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.planning.objectiveActionsPage.deleteConfirm'));
    if (!confirmed) return;
    try {
      await deleteAction(id);
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
        title={t('modules.planning.objectiveActionsPage.title')}
        actionLabel={t('modules.planning.objectiveActionsPage.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.objectiveActionsPage.table.objective')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.objectiveActionsPage.table.number')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.objectiveActionsPage.table.dueDate')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.objectiveActionsPage.table.progress')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.planning.objectiveActionsPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.objective}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.action_number}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.status_display}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.due_date}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.progress_percentage}%</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <CrudEmptyState message={t('modules.planning.objectiveActionsPage.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.planning.objectiveActionsPage.edit') : t('modules.planning.objectiveActionsPage.new')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.objectiveActionsPage.fields.objective')}</label>
              <select value={form.objective} onChange={(e) => setForm({...form, objective: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required>
                <option value="">{t('modules.planning.objectiveActionsPage.fields.select')}</option>
                {objectives.map(o => (
                  <option key={o.id} value={o.id}>{o.code} - {o.title}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.objectiveActionsPage.fields.number')}</label>
              <input type="number" min="1" value={form.action_number} onChange={(e) => setForm({...form, action_number: parseInt(e.target.value || 1)})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.objectiveActionsPage.fields.responsible')}</label>
              <select value={form.responsible} onChange={(e) => setForm({...form, responsible: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="">{t('modules.planning.objectiveActionsPage.fields.unassigned')}</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name || u.username || u.email}</option>
                ))}
              </select>
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.objectiveActionsPage.fields.description')}</label>
              <textarea value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.objectiveActionsPage.fields.whatWillBeDone')}</label>
              <textarea value={form.what_will_be_done} onChange={(e) => setForm({...form, what_will_be_done: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.objectiveActionsPage.fields.howWillBeDone')}</label>
              <textarea value={form.how_will_be_done} onChange={(e) => setForm({...form, how_will_be_done: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.objectiveActionsPage.fields.dueDate')}</label>
              <input type="date" value={form.due_date} onChange={(e) => setForm({...form, due_date: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('common.forms.status')}</label>
              <select value={form.status} onChange={(e) => setForm({...form, status: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="planned">{t('modules.planning.objectiveActionsPage.statuses.planned')}</option>
                <option value="in_progress">{t('modules.planning.objectiveActionsPage.statuses.inProgress')}</option>
                <option value="completed">{t('modules.planning.objectiveActionsPage.statuses.completed')}</option>
                <option value="cancelled">{t('modules.planning.objectiveActionsPage.statuses.cancelled')}</option>
                <option value="delayed">{t('modules.planning.objectiveActionsPage.statuses.delayed')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.objectiveActionsPage.fields.progress')}</label>
              <input type="number" min="0" max="100" value={form.progress_percentage} onChange={(e) => setForm({...form, progress_percentage: parseInt(e.target.value || 0)})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.objectiveActionsPage.fields.resourcesNeeded')}</label>
              <textarea value={form.resources_needed} onChange={(e) => setForm({...form, resources_needed: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.planning.objectiveActionsPage.fields.estimatedCost')}</label>
              <input type="number" value={form.estimated_cost} onChange={(e) => setForm({...form, estimated_cost: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
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

export default ObjectiveActionsPage;