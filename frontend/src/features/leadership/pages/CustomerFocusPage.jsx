import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import { getCustomerFocus, createCustomerFocus, updateCustomerFocus, deleteCustomerFocus } from '../api/leadershipApi';
import { showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => (Array.isArray(data) ? data : data?.results || []);

const focusTypes = [
  { value: 'requirements', labelKey: 'modules.leadership.customerFocusPage.options.focusType.requirements' },
  { value: 'risks', labelKey: 'modules.leadership.customerFocusPage.options.focusType.risks' },
  { value: 'satisfaction', labelKey: 'modules.leadership.customerFocusPage.options.focusType.satisfaction' },
  { value: 'compliance', labelKey: 'modules.leadership.customerFocusPage.options.focusType.compliance' }
];

const initialForm = {
  focus_type: 'requirements',
  title: '',
  description: '',
  action_taken: '',
  results: '',
  action_date: ''
};

const CustomerFocusPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';

  const [items, setItems] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [evidenceFile, setEvidenceFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const loadItems = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getCustomerFocus(orgId ? { organization_id: orgId } : {});
      setItems(normalizeList(data));
    } catch {
      setError(t('modules.leadership.customerFocusPage.messages.loadError'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  const resetForm = () => {
    setForm(initialForm);
    setEditingId(null);
    setEvidenceFile(null);
  };

  const buildPayload = () => {
    const payload = {
      organization_id: orgId,
      organization_name: orgName,
      focus_type: form.focus_type,
      title: form.title,
      description: form.description,
      action_taken: form.action_taken,
      results: form.results,
      action_date: form.action_date
    };

    if (!evidenceFile) {
      return payload;
    }

    const formData = new FormData();
    Object.entries(payload).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        formData.append(key, value);
      }
    });
    formData.append('evidence_file', evidenceFile);
    return formData;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSaving(true);

    try {
      const payload = buildPayload();
      if (editingId) {
        await updateCustomerFocus(editingId, payload);
      } else {
        await createCustomerFocus(payload);
      }
      resetForm();
      await loadItems();
    } catch {
      setError(t('modules.leadership.customerFocusPage.messages.saveError'));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setEditingId(item.id);
    setForm({
      focus_type: item.focus_type || 'requirements',
      title: item.title || '',
      description: item.description || '',
      action_taken: item.action_taken || '',
      results: item.results || '',
      action_date: item.action_date || ''
    });
    setEvidenceFile(null);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.leadership.customerFocusPage.messages.confirmDelete'));
    if (!confirmed) {
      return;
    }

    try {
      await deleteCustomerFocus(id);
      await loadItems();
    } catch {
      setError(t('modules.leadership.customerFocusPage.messages.deleteError'));
    }
  };

  return (
    <div className="space-y-6" style={{ fontFamily: '"Sora", "Work Sans", sans-serif' }}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">{t('modules.leadership.customerFocusPage.title')}</h1>
          <p className="muted-text">{t('modules.leadership.customerFocusPage.subtitle')}</p>
        </div>
        <button
          type="button"
          onClick={resetForm}
          className="rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/40"
        >
          {t('modules.leadership.customerFocusPage.buttons.new')}
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
            <div className="py-10 text-center muted-text">{t('modules.leadership.customerFocusPage.messages.loading')}</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-700 dark:text-slate-200">
                <thead className="table-head-muted border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="px-3 py-3">{t('modules.leadership.customerFocusPage.table.title')}</th>
                    <th className="px-3 py-3">{t('modules.leadership.customerFocusPage.table.type')}</th>
                    <th className="px-3 py-3">{t('common.forms.date')}</th>
                    <th className="px-3 py-3 text-right">{t('modules.leadership.customerFocusPage.table.actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                  {items.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/40">
                      <td className="px-3 py-3 font-medium text-slate-900 dark:text-slate-100">{item.title}</td>
                      <td className="px-3 py-3">{item.focus_type_display || item.focus_type}</td>
                      <td className="px-3 py-3">{item.action_date}</td>
                      <td className="px-3 py-3 text-right">
                        <div className="flex flex-wrap justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleEdit(item)}
                            className="rounded-md border border-slate-300 dark:border-slate-700 px-2 py-1 text-xs text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700/60"
                          >
                            {t('common.buttons.edit')}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(item.id)}
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
              {editingId ? t('modules.leadership.customerFocusPage.form.editTitle') : t('modules.leadership.customerFocusPage.form.newTitle')}
            </h2>
            <p className="form-label-muted">{t('modules.leadership.customerFocusPage.form.organization')}: {orgName || t('modules.leadership.customerFocusPage.form.unselected')}</p>
          </div>

          <div className="grid gap-4">
            <label className="form-label-muted">
              {t('modules.leadership.customerFocusPage.form.type')}
              <select
                value={form.focus_type}
                onChange={(event) => setForm({ ...form, focus_type: event.target.value })}
                className="field-control"
              >
                {focusTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {t(type.labelKey)}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.customerFocusPage.form.title')}
              <input
                type="text"
                value={form.title}
                onChange={(event) => setForm({ ...form, title: event.target.value })}
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
                required
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.customerFocusPage.form.actionTaken')}
              <textarea
                value={form.action_taken}
                onChange={(event) => setForm({ ...form, action_taken: event.target.value })}
                className="field-control h-20"
                required
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.customerFocusPage.form.results')}
              <textarea
                value={form.results}
                onChange={(event) => setForm({ ...form, results: event.target.value })}
                className="field-control h-16"
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.customerFocusPage.form.actionDate')}
              <input
                type="date"
                value={form.action_date}
                onChange={(event) => setForm({ ...form, action_date: event.target.value })}
                className="field-control"
                required
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.customerFocusPage.form.evidence')}
              <input
                type="file"
                onChange={(event) => setEvidenceFile(event.target.files?.[0] || null)}
                className="mt-1 w-full text-xs text-slate-600 dark:text-slate-300"
              />
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

export default CustomerFocusPage;