import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import {
  getRACIMatrices,
  createRACIMatrix,
  updateRACIMatrix,
  deleteRACIMatrix
} from '../api/leadershipApi';
import { showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => (Array.isArray(data) ? data : data?.results || []);

const initialForm = {
  name: '',
  description: '',
  is_active: true
};

const RACIMatricesPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';

  const [matrices, setMatrices] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const loadMatrices = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getRACIMatrices(orgId ? { organization_id: orgId } : {});
      setMatrices(normalizeList(data));
    } catch {
      setError(t('modules.leadership.raciMatricesPage.messages.loadError'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  useEffect(() => {
    loadMatrices();
  }, [loadMatrices]);

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
        organization_name: orgName,
        name: form.name,
        description: form.description,
        is_active: !!form.is_active
      };

      if (editingId) {
        await updateRACIMatrix(editingId, payload);
      } else {
        await createRACIMatrix(payload);
      }

      resetForm();
      await loadMatrices();
    } catch {
      setError(t('modules.leadership.raciMatricesPage.messages.saveError'));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (matrix) => {
    setEditingId(matrix.id);
    setForm({
      name: matrix.name || '',
      description: matrix.description || '',
      is_active: !!matrix.is_active
    });
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.leadership.raciMatricesPage.messages.confirmDelete'));
    if (!confirmed) {
      return;
    }

    try {
      await deleteRACIMatrix(id);
      await loadMatrices();
    } catch {
      setError(t('modules.leadership.raciMatricesPage.messages.deleteError'));
    }
  };

  return (
    <div className="space-y-6" style={{ fontFamily: '"Sora", "Work Sans", sans-serif' }}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">{t('modules.leadership.raciMatricesPage.title')}</h1>
          <p className="muted-text">{t('modules.leadership.raciMatricesPage.subtitle')}</p>
        </div>
        <button
          type="button"
          onClick={resetForm}
          className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:border-slate-500"
        >
          {t('modules.leadership.raciMatricesPage.buttons.new')}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
          {loading ? (
            <div className="py-10 text-center muted-text">{t('modules.leadership.raciMatricesPage.messages.loading')}</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-200">
                <thead className="table-head-muted">
                  <tr>
                    <th className="px-3 py-2">{t('common.forms.name')}</th>
                    <th className="px-3 py-2">{t('common.forms.description')}</th>
                    <th className="px-3 py-2">{t('modules.leadership.raciMatricesPage.table.active')}</th>
                    <th className="px-3 py-2 text-right">{t('modules.leadership.raciMatricesPage.table.actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {matrices.map((matrix) => (
                    <tr key={matrix.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/40">
                      <td className="px-3 py-2 font-medium text-slate-100">
                        <Link
                          to={`/leadership/raci/${matrix.id}`}
                          className="text-sky-300 hover:text-sky-200"
                        >
                          {matrix.name}
                        </Link>
                      </td>
                      <td className="px-3 py-2">{matrix.description || '-'}</td>
                      <td className="px-3 py-2">{matrix.is_active ? t('modules.leadership.raciMatricesPage.options.yes') : t('modules.leadership.raciMatricesPage.options.no')}</td>
                      <td className="px-3 py-2 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleEdit(matrix)}
                            className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-200"
                          >
                            {t('common.buttons.edit')}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(matrix.id)}
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
              {editingId ? t('modules.leadership.raciMatricesPage.form.editTitle') : t('modules.leadership.raciMatricesPage.form.newTitle')}
            </h2>
            <p className="form-label-muted">{t('modules.leadership.raciMatricesPage.form.organization')}: {orgName || t('modules.leadership.raciMatricesPage.form.unselected')}</p>
          </div>

          <div className="grid gap-3">
            <label className="form-label-muted">
              {t('modules.leadership.raciMatricesPage.form.name')}
              <input
                type="text"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
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

            <label className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
                className="h-4 w-4 rounded border-slate-600"
              />
              {t('modules.leadership.raciMatricesPage.form.active')}
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

export default RACIMatricesPage;