import React, { useCallback, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import CrudErrorBanner from '../../../components/Common/CrudErrorBanner';
import CrudPageHeader from '../../../components/Common/CrudPageHeader';
import CrudEmptyState from '../../../components/Common/CrudEmptyState';
import { showConfirm } from '../../../services/dialogs';
import { getDesignProjects, createDesignProject, updateDesignProject, deleteDesignProject, getUsers } from '../api/operationsApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const DesignProjectsPage = () => {
  const { t } = useI18n();
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({
    project_code: '',
    project_name: '',
    description: '',
    project_type: 'product',
    current_stage: 'planning',
    status: 'active',
    design_inputs: '',
    design_outputs: '',
    design_controls: '',
    verification_method: '',
    is_verified: false,
    validation_method: '',
    is_validated: false,
    project_leader: user?.id || '',
    start_date: '',
    target_completion_date: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const resetForm = useCallback(() => {
    setForm({
      project_code: '',
      project_name: '',
      description: '',
      project_type: 'product',
      current_stage: 'planning',
      status: 'active',
      design_inputs: '',
      design_outputs: '',
      design_controls: '',
      verification_method: '',
      is_verified: false,
      validation_method: '',
      is_validated: false,
      project_leader: user?.id || '',
      start_date: '',
      target_completion_date: ''
    });
    setEditingId(null);
  }, [user?.id]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getDesignProjects({ organization_id: orgId });
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
      setForm(prev => ({ ...prev, project_leader: prev.project_leader || user.id }));
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
        project_leader: form.project_leader || null
      };
      if (editingId) {
        await updateDesignProject(editingId, payload);
      } else {
        await createDesignProject(payload);
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
      project_code: item.project_code,
      project_name: item.project_name,
      description: item.description || '',
      project_type: item.project_type,
      current_stage: item.current_stage,
      status: item.status,
      design_inputs: item.design_inputs || '',
      design_outputs: item.design_outputs || '',
      design_controls: item.design_controls || '',
      verification_method: item.verification_method || '',
      is_verified: item.is_verified || false,
      validation_method: item.validation_method || '',
      is_validated: item.is_validated || false,
      project_leader: item.project_leader || '',
      start_date: item.start_date,
      target_completion_date: item.target_completion_date
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.operations.designProjectsPage.deleteConfirm'));
    if (!confirmed) return;
    try {
      await deleteDesignProject(id);
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
        title={t('modules.operations.designProjectsPage.title')}
        actionLabel={t('modules.operations.designProjectsPage.new')}
        onAction={openForm}
      />

      <CrudErrorBanner message={error} onClose={() => setError('')} />

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100 dark:bg-slate-800/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.designProjectsPage.table.code')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.name')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.designProjectsPage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.designProjectsPage.table.stage')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-300 uppercase">{t('modules.operations.designProjectsPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.project_code}</td>
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{i.project_name}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.project_type_display}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.current_stage_display}</td>
                <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{i.status_display}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <CrudEmptyState message={t('modules.operations.designProjectsPage.empty')} />}
      </div>

      <Modal
        title={editingId ? t('modules.operations.designProjectsPage.edit') : t('modules.operations.designProjectsPage.new')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.designProjectsPage.fields.code')}</label>
              <input type="text" value={form.project_code} onChange={(e) => setForm({...form, project_code: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.designProjectsPage.fields.name')}</label>
              <input type="text" value={form.project_name} onChange={(e) => setForm({...form, project_name: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.designProjectsPage.fields.type')}</label>
              <select value={form.project_type} onChange={(e) => setForm({...form, project_type: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="product">{t('modules.operations.designProjectsPage.types.product')}</option>
                <option value="service">{t('modules.operations.designProjectsPage.types.service')}</option>
                <option value="process">{t('modules.operations.designProjectsPage.types.process')}</option>
                <option value="system">{t('modules.operations.designProjectsPage.types.system')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.designProjectsPage.fields.stage')}</label>
              <select value={form.current_stage} onChange={(e) => setForm({...form, current_stage: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="planning">{t('modules.operations.designProjectsPage.stages.planning')}</option>
                <option value="inputs">{t('modules.operations.designProjectsPage.stages.inputs')}</option>
                <option value="controls">{t('modules.operations.designProjectsPage.stages.controls')}</option>
                <option value="outputs">{t('modules.operations.designProjectsPage.stages.outputs')}</option>
                <option value="verification">{t('modules.operations.designProjectsPage.stages.verification')}</option>
                <option value="validation">{t('modules.operations.designProjectsPage.stages.validation')}</option>
                <option value="changes">{t('modules.operations.designProjectsPage.stages.changes')}</option>
                <option value="completed">{t('modules.operations.designProjectsPage.stages.completed')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('common.forms.status')}</label>
              <select value={form.status} onChange={(e) => setForm({...form, status: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="active">{t('modules.operations.designProjectsPage.statuses.active')}</option>
                <option value="on_hold">{t('modules.operations.designProjectsPage.statuses.onHold')}</option>
                <option value="completed">{t('modules.operations.designProjectsPage.statuses.completed')}</option>
                <option value="cancelled">{t('modules.operations.designProjectsPage.statuses.cancelled')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.designProjectsPage.fields.projectLeader')}</label>
              <select value={form.project_leader} onChange={(e) => setForm({...form, project_leader: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white">
                <option value="">{t('modules.operations.designProjectsPage.fields.unassigned')}</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name || u.username || u.email}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.designProjectsPage.fields.startDate')}</label>
              <input type="date" value={form.start_date} onChange={(e) => setForm({...form, start_date: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.designProjectsPage.fields.targetDate')}</label>
              <input type="date" value={form.target_completion_date} onChange={(e) => setForm({...form, target_completion_date: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('common.forms.description')}</label>
              <textarea value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="3" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.designProjectsPage.fields.designInputs')}</label>
              <textarea value={form.design_inputs} onChange={(e) => setForm({...form, design_inputs: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.designProjectsPage.fields.designOutputs')}</label>
              <textarea value={form.design_outputs} onChange={(e) => setForm({...form, design_outputs: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.designProjectsPage.fields.designControls')}</label>
              <textarea value={form.design_controls} onChange={(e) => setForm({...form, design_controls: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" rows="2" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.designProjectsPage.fields.verificationMethod')}</label>
              <input type="text" value={form.verification_method} onChange={(e) => setForm({...form, verification_method: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div className="flex items-center">
              <label className="flex items-center space-x-2">
                <input type="checkbox" checked={form.is_verified} onChange={(e) => setForm({...form, is_verified: e.target.checked})} className="rounded" />
                <span className="text-sm text-slate-700 dark:text-slate-300">{t('modules.operations.designProjectsPage.fields.verified')}</span>
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('modules.operations.designProjectsPage.fields.validationMethod')}</label>
              <input type="text" value={form.validation_method} onChange={(e) => setForm({...form, validation_method: e.target.value})} className="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white" />
            </div>
            <div className="flex items-center">
              <label className="flex items-center space-x-2">
                <input type="checkbox" checked={form.is_validated} onChange={(e) => setForm({...form, is_validated: e.target.checked})} className="rounded" />
                <span className="text-sm text-slate-700 dark:text-slate-300">{t('modules.operations.designProjectsPage.fields.validated')}</span>
              </label>
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

export default DesignProjectsPage;