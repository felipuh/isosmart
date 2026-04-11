import React, { useCallback, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { getCompetences, createCompetence, updateCompetence, deleteCompetence, getUsers } from '../api/resourcesApi';
import { showAlert, showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const CompetencesPage = () => {
  const { t } = useI18n();
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({
    user: user?.id || '',
    competence_name: '',
    position: '',
    description: '',
    required_level: 'intermediate',
    current_level: 'basic',
    acquisition_method: 'training'
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const resetForm = useCallback(() => {
    setForm({
      user: user?.id || '',
      competence_name: '',
      position: '',
      description: '',
      required_level: 'intermediate',
      current_level: 'basic',
      acquisition_method: 'training'
    });
    setEditingId(null);
  }, [user?.id]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getCompetences({ organization_id: orgId });
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
    } else {
      setLoading(false);
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
      setForm(prev => ({ ...prev, user: prev.user || user.id }));
    }
  }, [user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!orgId) {
      await showAlert(t('modules.resources.competencesPage.messages.selectOrganization'));
      return;
    }
    try {
      setSaving(true);
      setError('');
      const payload = { ...form, organization_id: orgId, organization_name: orgName };
      if (editingId) {
        await updateCompetence(editingId, payload);
      } else {
        await createCompetence(payload);
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
      user: item.user,
      competence_name: item.competence_name,
      position: item.position,
      description: item.description || '',
      required_level: item.required_level,
      current_level: item.current_level,
      acquisition_method: item.acquisition_method
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.resources.competencesPage.messages.confirmDelete'));
    if (!confirmed) return;
    try {
      await deleteCompetence(id);
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
        title={t('modules.resources.competencesPage.title')}
        actionLabel={t('modules.resources.competencesPage.buttons.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.competencesPage.table.user')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.competencesPage.table.competence')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.competencesPage.table.position')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.competencesPage.table.required')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.competencesPage.table.current')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.resources.competencesPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.user_name || i.user}</td>
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{i.competence_name}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.position}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.required_level_display}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.current_level_display}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <CrudEmptyState message={t('modules.resources.competencesPage.messages.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.resources.competencesPage.modal.editTitle') : t('modules.resources.competencesPage.modal.newTitle')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.competencesPage.form.userRequired')}</label>
              <select value={form.user} onChange={(e) => setForm({...form, user: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required>
                <option value="">{t('modules.resources.competencesPage.form.selectOption')}</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name || u.username || u.email}</option>
                ))}
                {users.length === 0 && user?.id && (
                  <option value={user.id}>{user.full_name || user.username || user.email}</option>
                )}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.competencesPage.form.competenceRequired')}</label>
              <input type="text" value={form.competence_name} onChange={(e) => setForm({...form, competence_name: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.competencesPage.form.positionRequired')}</label>
              <input type="text" value={form.position} onChange={(e) => setForm({...form, position: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.competencesPage.form.requiredLevel')}</label>
              <select value={form.required_level} onChange={(e) => setForm({...form, required_level: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="basic">{t('modules.resources.competencesPage.options.level.basic')}</option>
                <option value="intermediate">{t('modules.resources.competencesPage.options.level.intermediate')}</option>
                <option value="advanced">{t('modules.resources.competencesPage.options.level.advanced')}</option>
                <option value="expert">{t('modules.resources.competencesPage.options.level.expert')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.competencesPage.form.currentLevel')}</label>
              <select value={form.current_level} onChange={(e) => setForm({...form, current_level: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="basic">{t('modules.resources.competencesPage.options.level.basic')}</option>
                <option value="intermediate">{t('modules.resources.competencesPage.options.level.intermediate')}</option>
                <option value="advanced">{t('modules.resources.competencesPage.options.level.advanced')}</option>
                <option value="expert">{t('modules.resources.competencesPage.options.level.expert')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.resources.competencesPage.form.acquisitionMethod')}</label>
              <select value={form.acquisition_method} onChange={(e) => setForm({...form, acquisition_method: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="education">{t('modules.resources.competencesPage.options.acquisition.education')}</option>
                <option value="training">{t('modules.resources.competencesPage.options.acquisition.training')}</option>
                <option value="experience">{t('modules.resources.competencesPage.options.acquisition.experience')}</option>
                <option value="certification">{t('modules.resources.competencesPage.options.acquisition.certification')}</option>
              </select>
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

export default CompetencesPage;