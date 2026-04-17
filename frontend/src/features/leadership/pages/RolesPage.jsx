import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import { getRoles, createRole, updateRole, deleteRole } from '../api/leadershipApi';
import { showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => (Array.isArray(data) ? data : data?.results || []);
const listToText = (value) => (Array.isArray(value) ? value.join(', ') : '');
const textToList = (value) =>
  value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

const initialForm = {
  name: '',
  code: '',
  level: 1,
  description: '',
  reports_to: '',
  responsibilities: '',
  authorities: '',
  required_competencies: '',
  is_qms_role: true,
  is_active: true
};

const RolesPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';

  const [roles, setRoles] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const loadRoles = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getRoles(orgId ? { organization_id: orgId } : {});
      setRoles(normalizeList(data));
    } catch {
      setError(t('modules.leadership.rolesPage.messages.loadError'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  useEffect(() => {
    loadRoles();
  }, [loadRoles]);

  const resetForm = () => {
    setForm(initialForm);
    setEditingId(null);
  };

  const buildPayload = () => ({
    organization_id: orgId,
    organization_name: orgName,
    name: form.name,
    code: form.code,
    level: Number(form.level || 1),
    description: form.description,
    reports_to: form.reports_to || null,
    responsibilities: textToList(form.responsibilities),
    authorities: textToList(form.authorities),
    required_competencies: textToList(form.required_competencies),
    is_qms_role: !!form.is_qms_role,
    is_active: !!form.is_active
  });

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSaving(true);

    try {
      const payload = buildPayload();
      if (editingId) {
        await updateRole(editingId, payload);
      } else {
        await createRole(payload);
      }
      resetForm();
      await loadRoles();
    } catch {
      setError(t('modules.leadership.rolesPage.messages.saveError'));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (role) => {
    setEditingId(role.id);
    setForm({
      name: role.name || '',
      code: role.code || '',
      level: role.level || 1,
      description: role.description || '',
      reports_to: role.reports_to || '',
      responsibilities: listToText(role.responsibilities),
      authorities: listToText(role.authorities),
      required_competencies: listToText(role.required_competencies),
      is_qms_role: !!role.is_qms_role,
      is_active: !!role.is_active
    });
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.leadership.rolesPage.messages.confirmDelete'));
    if (!confirmed) {
      return;
    }

    try {
      await deleteRole(id);
      await loadRoles();
    } catch {
      setError(t('modules.leadership.rolesPage.messages.deleteError'));
    }
  };

  return (
    <div className="space-y-6" style={{ fontFamily: '"Sora", "Work Sans", sans-serif' }}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">{t('modules.leadership.rolesPage.title')}</h1>
          <p className="muted-text">{t('modules.leadership.rolesPage.subtitle')}</p>
        </div>
        <button
          type="button"
          onClick={resetForm}
          className="rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/40"
        >
          {t('modules.leadership.rolesPage.buttons.new')}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-300 dark:border-red-500/40 bg-red-50 dark:bg-red-500/10 px-4 py-3 text-sm text-red-700 dark:text-red-200">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div className="card p-5 lg:p-6">
          {loading ? (
            <div className="py-10 text-center muted-text">{t('modules.leadership.rolesPage.messages.loading')}</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-700 dark:text-slate-200">
                <thead className="table-head-muted border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="px-3 py-3">{t('common.forms.name')}</th>
                    <th className="px-3 py-3">{t('modules.leadership.rolesPage.table.code')}</th>
                    <th className="px-3 py-3">{t('modules.leadership.rolesPage.table.level')}</th>
                    <th className="px-3 py-3">{t('modules.leadership.rolesPage.table.active')}</th>
                    <th className="px-3 py-3 text-right">{t('modules.leadership.rolesPage.table.actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                  {roles.map((role) => (
                    <tr key={role.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/40">
                      <td className="px-3 py-3 font-medium text-slate-900 dark:text-slate-100">{role.name}</td>
                      <td className="px-3 py-3">{role.code}</td>
                      <td className="px-3 py-3">{role.level}</td>
                      <td className="px-3 py-3">{role.is_active ? t('modules.leadership.rolesPage.options.yes') : t('modules.leadership.rolesPage.options.no')}</td>
                      <td className="px-3 py-3 text-right">
                        <div className="flex flex-wrap justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleEdit(role)}
                            className="rounded-md border border-slate-300 dark:border-slate-700 px-2 py-1 text-xs text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700/60"
                          >
                            {t('common.buttons.edit')}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(role.id)}
                            className="rounded-md border border-red-300 dark:border-red-500/50 px-2 py-1 text-xs text-red-700 dark:text-red-200 hover:bg-red-50 dark:hover:bg-red-500/10"
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

        <form onSubmit={handleSubmit} className="card p-5 lg:p-6 space-y-5 lg:max-h-[calc(100vh-11rem)] lg:overflow-y-auto">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
              {editingId ? t('modules.leadership.rolesPage.form.editTitle') : t('modules.leadership.rolesPage.form.newTitle')}
            </h2>
            <p className="form-label-muted">{t('modules.leadership.rolesPage.form.organization')}: {orgName || t('modules.leadership.rolesPage.form.unselected')}</p>
          </div>

          <div className="grid gap-4">
            <label className="form-label-muted">
              {t('modules.leadership.rolesPage.form.name')}
              <input
                type="text"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                className="field-control"
                required
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.rolesPage.form.code')}
              <input
                type="text"
                value={form.code}
                onChange={(event) => setForm({ ...form, code: event.target.value })}
                className="field-control"
                required
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.rolesPage.form.level')}
              <input
                type="number"
                min="1"
                max="10"
                value={form.level}
                onChange={(event) => setForm({ ...form, level: event.target.value })}
                className="field-control"
                required
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.rolesPage.form.reportsTo')}
              <select
                value={form.reports_to}
                onChange={(event) => setForm({ ...form, reports_to: event.target.value })}
                className="field-control"
              >
                <option value="">{t('modules.leadership.rolesPage.form.noDependency')}</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-label-muted">
              {t('common.forms.description')}
              <textarea
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                className="field-control h-20"
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.rolesPage.form.responsibilities')}
              <textarea
                value={form.responsibilities}
                onChange={(event) => setForm({ ...form, responsibilities: event.target.value })}
                className="field-control h-16"
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.rolesPage.form.authorities')}
              <textarea
                value={form.authorities}
                onChange={(event) => setForm({ ...form, authorities: event.target.value })}
                className="field-control h-16"
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.rolesPage.form.requiredCompetencies')}
              <textarea
                value={form.required_competencies}
                onChange={(event) => setForm({ ...form, required_competencies: event.target.value })}
                className="field-control h-16"
              />
            </label>

            <div className="flex items-center gap-4 text-xs text-slate-600 dark:text-slate-300">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.is_qms_role}
                  onChange={(event) => setForm({ ...form, is_qms_role: event.target.checked })}
                  className="h-4 w-4 rounded border-slate-600"
                />
                {t('modules.leadership.rolesPage.form.qmsRole')}
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
                  className="h-4 w-4 rounded border-slate-600"
                />
                {t('common.labels.active')}
              </label>
            </div>
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
              className="rounded-lg border border-slate-300 dark:border-slate-700 px-4 py-2 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/40"
            >
              {t('common.buttons.clear')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RolesPage;