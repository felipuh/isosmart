import React, { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getRACIEntries, createRACIEntry, updateRACIEntry, deleteRACIEntry, getRoles } from '../api/leadershipApi';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import { showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => (Array.isArray(data) ? data : data?.results || []);

const initialForm = {
  activity: '',
  description: '',
  order: 0,
  responsible_roles: [],
  accountable_roles: [],
  consulted_roles: [],
  informed_roles: []
};

const toggleItem = (list, value) => {
  if (list.includes(value)) {
    return list.filter((item) => item !== value);
  }
  return [...list, value];
};

const RACIEntriesPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const { matrixId } = useParams();
  const [entries, setEntries] = useState([]);
  const [roles, setRoles] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [entriesData, rolesData] = await Promise.all([
        getRACIEntries({ matrix: matrixId }),
        getRoles(orgId ? { organization_id: orgId } : {})
      ]);
      setEntries(normalizeList(entriesData));
      setRoles(normalizeList(rolesData));
    } catch {
      setError(t('modules.leadership.raciEntriesPage.messages.loadError'));
    } finally {
      setLoading(false);
    }
  }, [matrixId, orgId, t]);

  useEffect(() => {
    loadData();
  }, [loadData]);

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
        matrix: matrixId,
        activity: form.activity,
        description: form.description,
        order: Number(form.order || 0),
        responsible_roles: form.responsible_roles,
        accountable_roles: form.accountable_roles,
        consulted_roles: form.consulted_roles,
        informed_roles: form.informed_roles
      };

      if (editingId) {
        await updateRACIEntry(editingId, payload);
      } else {
        await createRACIEntry(payload);
      }

      resetForm();
      await loadData();
    } catch {
      setError(t('modules.leadership.raciEntriesPage.messages.saveError'));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (entry) => {
    setEditingId(entry.id);
    setForm({
      activity: entry.activity || '',
      description: entry.description || '',
      order: entry.order || 0,
      responsible_roles: entry.responsible_roles || [],
      accountable_roles: entry.accountable_roles || [],
      consulted_roles: entry.consulted_roles || [],
      informed_roles: entry.informed_roles || []
    });
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.leadership.raciEntriesPage.messages.confirmDelete'));
    if (!confirmed) {
      return;
    }

    try {
      await deleteRACIEntry(id);
      await loadData();
    } catch {
      setError(t('modules.leadership.raciEntriesPage.messages.deleteError'));
    }
  };

  const renderRoleChecklist = (label, valueKey) => (
    <div className="space-y-2">
      <p className="text-xs uppercase text-slate-600 dark:text-slate-400">{label}</p>
      <div className="grid gap-2 sm:grid-cols-2">
        {roles.map((role) => (
          <label key={`${valueKey}-${role.id}`} className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300">
            <input
              type="checkbox"
              checked={form[valueKey].includes(role.id)}
              onChange={() => setForm({
                ...form,
                [valueKey]: toggleItem(form[valueKey], role.id)
              })}
              className="h-4 w-4 rounded border-slate-600"
            />
            {role.name}
          </label>
        ))}
      </div>
    </div>
  );

  return (
    <div className="space-y-6" style={{ fontFamily: '"Sora", "Work Sans", sans-serif' }}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">{t('modules.leadership.raciEntriesPage.title')}</h1>
          <p className="muted-text">{t('modules.leadership.raciEntriesPage.subtitle')}: {matrixId}</p>
        </div>
        <Link
          to="/leadership/raci"
          className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:border-slate-500"
        >
          {t('modules.leadership.raciEntriesPage.buttons.backToMatrices')}
        </Link>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
          {loading ? (
            <div className="py-10 text-center muted-text">{t('modules.leadership.raciEntriesPage.messages.loading')}</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-200">
                <thead className="table-head-muted">
                  <tr>
                    <th className="px-3 py-2">{t('modules.leadership.raciEntriesPage.table.order')}</th>
                    <th className="px-3 py-2">{t('modules.leadership.raciEntriesPage.table.activity')}</th>
                    <th className="px-3 py-2 text-right">{t('modules.leadership.raciEntriesPage.table.actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {entries.map((entry) => (
                    <tr key={entry.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/40">
                      <td className="px-3 py-2">{entry.order}</td>
                      <td className="px-3 py-2 font-medium text-slate-100">{entry.activity}</td>
                      <td className="px-3 py-2 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleEdit(entry)}
                            className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-200"
                          >
                            {t('common.buttons.edit')}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(entry.id)}
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
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
              {editingId ? t('modules.leadership.raciEntriesPage.form.editTitle') : t('modules.leadership.raciEntriesPage.form.newTitle')}
            </h2>
          </div>

          <div className="grid gap-3">
            <label className="form-label-muted">
              {t('modules.leadership.raciEntriesPage.form.activity')}
              <input
                type="text"
                value={form.activity}
                onChange={(event) => setForm({ ...form, activity: event.target.value })}
                className="field-control"
                required
              />
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
              {t('modules.leadership.raciEntriesPage.form.order')}
              <input
                type="number"
                value={form.order}
                onChange={(event) => setForm({ ...form, order: event.target.value })}
                className="field-control"
              />
            </label>

            {renderRoleChecklist(t('modules.leadership.raciEntriesPage.form.responsible'), 'responsible_roles')}
            {renderRoleChecklist(t('modules.leadership.raciEntriesPage.form.accountable'), 'accountable_roles')}
            {renderRoleChecklist(t('modules.leadership.raciEntriesPage.form.consulted'), 'consulted_roles')}
            {renderRoleChecklist(t('modules.leadership.raciEntriesPage.form.informed'), 'informed_roles')}
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="submit"
              disabled={saving}
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

export default RACIEntriesPage;