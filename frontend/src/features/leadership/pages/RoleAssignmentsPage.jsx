import React, { useEffect, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import {
  getRoleAssignments,
  createRoleAssignment,
  updateRoleAssignment,
  deleteRoleAssignment,
  getRoles,
  getUsers
} from '../api/leadershipApi';

const normalizeList = (data) => (Array.isArray(data) ? data : data?.results || []);

const initialForm = {
  role: '',
  user: '',
  start_date: '',
  end_date: '',
  assignment_type: 'permanent',
  notes: '',
  is_active: true
};

const RoleAssignmentsPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;

  const [assignments, setAssignments] = useState([]);
  const [roles, setRoles] = useState([]);
  const [users, setUsers] = useState([]);
  const [userError, setUserError] = useState('');
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      const [assignmentsData, rolesData] = await Promise.all([
        getRoleAssignments(),
        getRoles()
      ]);
      setAssignments(normalizeList(assignmentsData));
      setRoles(normalizeList(rolesData));
    } catch {
      setError(t('modules.leadership.roleAssignmentsPage.messages.loadError'));
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const data = await getUsers();
      setUsers(normalizeList(data));
      setUserError('');
    } catch {
      setUserError(t('modules.leadership.roleAssignmentsPage.messages.usersLoadError'));
    }
  };

  useEffect(() => {
    loadData();
    loadUsers();
  }, []);

  const resetForm = () => {
    setForm(initialForm);
    setEditingId(null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSaving(true);

    try {
      const payload = {
        organization_id: orgId,
        role: form.role,
        user: form.user,
        start_date: form.start_date,
        end_date: form.end_date || null,
        assignment_type: form.assignment_type,
        notes: form.notes,
        is_active: !!form.is_active
      };

      if (editingId) {
        await updateRoleAssignment(editingId, payload);
      } else {
        await createRoleAssignment(payload);
      }

      resetForm();
      await loadData();
    } catch {
      setError(t('modules.leadership.roleAssignmentsPage.messages.saveError'));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (assignment) => {
    setEditingId(assignment.id);
    setForm({
      role: assignment.role || '',
      user: assignment.user || '',
      start_date: assignment.start_date || '',
      end_date: assignment.end_date || '',
      assignment_type: assignment.assignment_type || 'permanent',
      notes: assignment.notes || '',
      is_active: !!assignment.is_active
    });
  };

  const handleDelete = async (id) => {
    if (!window.confirm(t('modules.leadership.roleAssignmentsPage.messages.confirmDelete'))) {
      return;
    }

    try {
      await deleteRoleAssignment(id);
      await loadData();
    } catch {
      setError(t('modules.leadership.roleAssignmentsPage.messages.deleteError'));
    }
  };

  return (
    <div className="space-y-6" style={{ fontFamily: '"Sora", "Work Sans", sans-serif' }}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">{t('modules.leadership.roleAssignmentsPage.title')}</h1>
          <p className="text-sm text-slate-400">{t('modules.leadership.roleAssignmentsPage.subtitle')}</p>
        </div>
        <button
          type="button"
          onClick={resetForm}
          className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:border-slate-500"
        >
          {t('modules.leadership.roleAssignmentsPage.buttons.new')}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {userError && (
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          {userError}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
          {loading ? (
            <div className="py-10 text-center text-slate-400">{t('modules.leadership.roleAssignmentsPage.messages.loading')}</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-200">
                <thead className="text-xs uppercase text-slate-400">
                  <tr>
                    <th className="px-3 py-2">{t('modules.leadership.roleAssignmentsPage.table.role')}</th>
                    <th className="px-3 py-2">{t('modules.leadership.roleAssignmentsPage.table.user')}</th>
                    <th className="px-3 py-2">{t('modules.leadership.roleAssignmentsPage.table.startDate')}</th>
                    <th className="px-3 py-2">{t('modules.leadership.roleAssignmentsPage.table.type')}</th>
                    <th className="px-3 py-2 text-right">{t('modules.leadership.roleAssignmentsPage.table.actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {assignments.map((assignment) => (
                    <tr key={assignment.id} className="hover:bg-slate-800/40">
                      <td className="px-3 py-2 font-medium text-slate-100">{assignment.role_name || assignment.role}</td>
                      <td className="px-3 py-2">{assignment.user_name || assignment.user_email || assignment.user}</td>
                      <td className="px-3 py-2">{assignment.start_date}</td>
                      <td className="px-3 py-2 capitalize">{assignment.assignment_type}</td>
                      <td className="px-3 py-2 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleEdit(assignment)}
                            className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-200"
                          >
                            {t('common.buttons.edit')}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(assignment.id)}
                            className="rounded-md border border-red-500/50 px-2 py-1 text-xs text-red-200"
                          >
                            {t('common.buttons.delete')}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-white">
              {editingId ? t('modules.leadership.roleAssignmentsPage.form.editTitle') : t('modules.leadership.roleAssignmentsPage.form.newTitle')}
            </h2>
            <p className="text-xs text-slate-400">{t('modules.leadership.roleAssignmentsPage.form.activeOrganization')}: {currentOrganization?.name || t('modules.leadership.roleAssignmentsPage.form.unselected')}</p>
          </div>

          <div className="grid gap-3">
            <label className="text-xs text-slate-400">
              {t('modules.leadership.roleAssignmentsPage.form.role')}
              <select
                value={form.role}
                onChange={(event) => setForm({ ...form, role: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              >
                <option value="">{t('modules.leadership.roleAssignmentsPage.form.selectRole')}</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-xs text-slate-400">
              {t('modules.leadership.roleAssignmentsPage.form.user')}
              {users.length > 0 ? (
                <select
                  value={form.user}
                  onChange={(event) => setForm({ ...form, user: event.target.value })}
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                  required
                >
                  <option value="">{t('modules.leadership.roleAssignmentsPage.form.selectUser')}</option>
                  {users.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.full_name || user.email}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="number"
                  value={form.user}
                  onChange={(event) => setForm({ ...form, user: event.target.value })}
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                  placeholder={t('modules.leadership.roleAssignmentsPage.form.userIdPlaceholder')}
                  required
                />
              )}
            </label>

            <label className="text-xs text-slate-400">
              {t('modules.leadership.roleAssignmentsPage.form.startDate')}
              <input
                type="date"
                value={form.start_date}
                onChange={(event) => setForm({ ...form, start_date: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>

            <label className="text-xs text-slate-400">
              {t('modules.leadership.roleAssignmentsPage.form.endDate')}
              <input
                type="date"
                value={form.end_date}
                onChange={(event) => setForm({ ...form, end_date: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
            </label>

            <label className="text-xs text-slate-400">
              {t('modules.leadership.roleAssignmentsPage.form.type')}
              <select
                value={form.assignment_type}
                onChange={(event) => setForm({ ...form, assignment_type: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              >
                <option value="permanent">{t('modules.leadership.roleAssignmentsPage.options.type.permanent')}</option>
                <option value="temporary">{t('modules.leadership.roleAssignmentsPage.options.type.temporary')}</option>
                <option value="acting">{t('modules.leadership.roleAssignmentsPage.options.type.acting')}</option>
              </select>
            </label>

            <label className="text-xs text-slate-400">
              {t('modules.leadership.roleAssignmentsPage.form.notes')}
              <textarea
                value={form.notes}
                onChange={(event) => setForm({ ...form, notes: event.target.value })}
                className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
            </label>

            <label className="flex items-center gap-2 text-xs text-slate-300">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
                className="h-4 w-4 rounded border-slate-600"
              />
              {t('common.labels.active')}
            </label>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="submit"
              disabled={saving || !orgId}
              className="rounded-lg bg-emerald-500/80 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
            >
              {saving ? t('common.messages.saving') : editingId ? t('common.buttons.update') : t('common.buttons.create')}
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-200"
            >
              {t('common.buttons.clear')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RoleAssignmentsPage;