import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import { getCommitments, createCommitment, updateCommitment, deleteCommitment } from '../api/leadershipApi';
import { showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => (Array.isArray(data) ? data : data?.results || []);

const commitmentTypes = [
  { value: 'responsibility', labelKey: 'modules.leadership.commitmentsPage.options.commitmentType.responsibility' },
  { value: 'policy', labelKey: 'modules.leadership.commitmentsPage.options.commitmentType.policy' },
  { value: 'integration', labelKey: 'modules.leadership.commitmentsPage.options.commitmentType.integration' },
  { value: 'resources', labelKey: 'modules.leadership.commitmentsPage.options.commitmentType.resources' },
  { value: 'importance', labelKey: 'modules.leadership.commitmentsPage.options.commitmentType.importance' },
  { value: 'results', labelKey: 'modules.leadership.commitmentsPage.options.commitmentType.results' },
  { value: 'engagement', labelKey: 'modules.leadership.commitmentsPage.options.commitmentType.engagement' },
  { value: 'improvement', labelKey: 'modules.leadership.commitmentsPage.options.commitmentType.improvement' },
  { value: 'management', labelKey: 'modules.leadership.commitmentsPage.options.commitmentType.management' }
];

const evidenceTypes = [
  { value: 'meeting', labelKey: 'modules.leadership.commitmentsPage.options.evidenceType.meeting' },
  { value: 'communication', labelKey: 'modules.leadership.commitmentsPage.options.evidenceType.communication' },
  { value: 'decision', labelKey: 'modules.leadership.commitmentsPage.options.evidenceType.decision' },
  { value: 'resource_allocation', labelKey: 'modules.leadership.commitmentsPage.options.evidenceType.resourceAllocation' },
  { value: 'review', labelKey: 'modules.leadership.commitmentsPage.options.evidenceType.review' },
  { value: 'policy_update', labelKey: 'modules.leadership.commitmentsPage.options.evidenceType.policyUpdate' },
  { value: 'other', labelKey: 'modules.leadership.commitmentsPage.options.evidenceType.other' }
];

const statusOptions = [
  { value: 'planned', labelKey: 'modules.leadership.commitmentsPage.options.status.planned' },
  { value: 'in_progress', labelKey: 'modules.leadership.commitmentsPage.options.status.inProgress' },
  { value: 'completed', labelKey: 'modules.leadership.commitmentsPage.options.status.completed' },
  { value: 'verified', labelKey: 'modules.leadership.commitmentsPage.options.status.verified' }
];

const initialForm = {
  commitment_type: 'responsibility',
  title: '',
  description: '',
  evidence_type: 'meeting',
  evidence_url: '',
  commitment_date: '',
  status: 'planned'
};

const CommitmentsPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';

  const [commitments, setCommitments] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [documentFile, setDocumentFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const loadCommitments = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getCommitments(orgId ? { organization_id: orgId } : {});
      setCommitments(normalizeList(data));
    } catch {
      setError(t('modules.leadership.commitmentsPage.messages.loadError'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  useEffect(() => {
    loadCommitments();
  }, [loadCommitments]);

  const resetForm = () => {
    setForm(initialForm);
    setEditingId(null);
    setDocumentFile(null);
  };

  const buildPayload = () => {
    const payload = {
      organization_id: orgId,
      organization_name: orgName,
      commitment_type: form.commitment_type,
      title: form.title,
      description: form.description,
      evidence_type: form.evidence_type,
      evidence_url: form.evidence_url,
      commitment_date: form.commitment_date,
      status: form.status
    };

    if (!documentFile) {
      return payload;
    }

    const formData = new FormData();
    Object.entries(payload).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        formData.append(key, value);
      }
    });
    formData.append('evidence_document', documentFile);
    return formData;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSaving(true);

    try {
      const payload = buildPayload();
      if (editingId) {
        await updateCommitment(editingId, payload);
      } else {
        await createCommitment(payload);
      }
      resetForm();
      await loadCommitments();
    } catch {
      setError(t('modules.leadership.commitmentsPage.messages.saveError'));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (commitment) => {
    setEditingId(commitment.id);
    setForm({
      commitment_type: commitment.commitment_type || 'responsibility',
      title: commitment.title || '',
      description: commitment.description || '',
      evidence_type: commitment.evidence_type || 'meeting',
      evidence_url: commitment.evidence_url || '',
      commitment_date: commitment.commitment_date || '',
      status: commitment.status || 'planned'
    });
    setDocumentFile(null);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.leadership.commitmentsPage.messages.confirmDelete'));
    if (!confirmed) {
      return;
    }

    try {
      await deleteCommitment(id);
      await loadCommitments();
    } catch {
      setError(t('modules.leadership.commitmentsPage.messages.deleteError'));
    }
  };

  return (
    <div className="space-y-6" style={{ fontFamily: '"Sora", "Work Sans", sans-serif' }}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">{t('modules.leadership.commitmentsPage.title')}</h1>
          <p className="muted-text">{t('modules.leadership.commitmentsPage.subtitle')}</p>
        </div>
        <button
          type="button"
          onClick={resetForm}
          className="rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/40"
        >
          {t('modules.leadership.commitmentsPage.buttons.new')}
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
            <div className="py-10 text-center muted-text">{t('modules.leadership.commitmentsPage.messages.loading')}</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-700 dark:text-slate-200">
                <thead className="table-head-muted border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="px-3 py-3">{t('modules.leadership.commitmentsPage.table.title')}</th>
                    <th className="px-3 py-3">{t('modules.leadership.commitmentsPage.table.type')}</th>
                    <th className="px-3 py-3">{t('common.forms.date')}</th>
                    <th className="px-3 py-3">{t('common.forms.status')}</th>
                    <th className="px-3 py-3 text-right">{t('modules.leadership.commitmentsPage.table.actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                  {commitments.map((commitment) => (
                    <tr key={commitment.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/40">
                      <td className="px-3 py-3 font-medium text-slate-900 dark:text-slate-100">{commitment.title}</td>
                      <td className="px-3 py-3">{commitment.commitment_type_display || commitment.commitment_type}</td>
                      <td className="px-3 py-3">{commitment.commitment_date}</td>
                      <td className="px-3 py-3">{commitment.status_display || commitment.status}</td>
                      <td className="px-3 py-3 text-right">
                        <div className="flex flex-wrap justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleEdit(commitment)}
                            className="rounded-md border border-slate-300 dark:border-slate-700 px-2 py-1 text-xs text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700/60"
                          >
                            {t('common.buttons.edit')}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(commitment.id)}
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
              {editingId ? t('modules.leadership.commitmentsPage.form.editTitle') : t('modules.leadership.commitmentsPage.form.newTitle')}
            </h2>
            <p className="form-label-muted">{t('modules.leadership.commitmentsPage.form.organization')}: {orgName || t('modules.leadership.commitmentsPage.form.unselected')}</p>
          </div>

          <div className="grid gap-4">
            <label className="form-label-muted">
              {t('modules.leadership.commitmentsPage.form.commitmentType')}
              <select
                value={form.commitment_type}
                onChange={(event) => setForm({ ...form, commitment_type: event.target.value })}
                className="field-control"
              >
                {commitmentTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {t(type.labelKey)}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.commitmentsPage.form.title')}
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
                className="field-control h-24"
                required
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.commitmentsPage.form.evidenceType')}
              <select
                value={form.evidence_type}
                onChange={(event) => setForm({ ...form, evidence_type: event.target.value })}
                className="field-control"
              >
                {evidenceTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {t(type.labelKey)}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.commitmentsPage.form.evidenceUrl')}
              <input
                type="url"
                value={form.evidence_url}
                onChange={(event) => setForm({ ...form, evidence_url: event.target.value })}
                className="field-control"
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.commitmentsPage.form.evidenceDocument')}
              <input
                type="file"
                onChange={(event) => setDocumentFile(event.target.files?.[0] || null)}
                className="mt-1 w-full text-xs text-slate-600 dark:text-slate-300"
              />
            </label>

            <label className="form-label-muted">
              {t('common.forms.date')}
              <input
                type="date"
                value={form.commitment_date}
                onChange={(event) => setForm({ ...form, commitment_date: event.target.value })}
                className="field-control"
                required
              />
            </label>

            <label className="form-label-muted">
              {t('common.forms.status')}
              <select
                value={form.status}
                onChange={(event) => setForm({ ...form, status: event.target.value })}
                className="field-control"
              >
                {statusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {t(option.labelKey)}
                  </option>
                ))}
              </select>
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

export default CommitmentsPage;