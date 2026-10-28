import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import {
  getPolicies,
  createPolicy,
  updatePolicy,
  deletePolicy,
  approvePolicy,
  publishPolicy,
  makeObsoletePolicy
} from '../api/leadershipApi';
import { showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => (Array.isArray(data) ? data : data?.results || []);

const initialForm = {
  version: '',
  title: '',
  content: '',
  customer_focus: '',
  framework_for_objectives: '',
  commitment_requirements: '',
  commitment_improvement: '',
  status: 'draft',
  effective_date: '',
  review_date: '',
  approval_comments: ''
};

const PoliciesPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';

  const [policies, setPolicies] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [pdfFile, setPdfFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const loadPolicies = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getPolicies(orgId ? { organization_id: orgId } : {});
      setPolicies(normalizeList(data));
    } catch {
      setError(t('modules.leadership.policiesPage.messages.loadError'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  useEffect(() => {
    loadPolicies();
  }, [loadPolicies]);

  const resetForm = () => {
    setForm(initialForm);
    setEditingId(null);
    setPdfFile(null);
  };

  const buildPayload = () => {
    const payload = {
      ...form,
      organization_id: orgId,
      organization_name: orgName
    };

    if (!pdfFile) {
      return payload;
    }

    const formData = new FormData();
    Object.entries(payload).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        formData.append(key, value);
      }
    });
    formData.append('pdf_file', pdfFile);
    return formData;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSaving(true);

    try {
      const payload = buildPayload();
      if (editingId) {
        await updatePolicy(editingId, payload);
      } else {
        await createPolicy(payload);
      }
      resetForm();
      await loadPolicies();
    } catch {
      setError(t('modules.leadership.policiesPage.messages.saveError'));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (policy) => {
    setEditingId(policy.id);
    setForm({
      version: policy.version || '',
      title: policy.title || t('modules.leadership.policiesPage.form.defaultTitle'),
      content: policy.content || '',
      customer_focus: policy.customer_focus || '',
      framework_for_objectives: policy.framework_for_objectives || '',
      commitment_requirements: policy.commitment_requirements || '',
      commitment_improvement: policy.commitment_improvement || '',
      status: policy.status || 'draft',
      effective_date: policy.effective_date || '',
      review_date: policy.review_date || '',
      approval_comments: policy.approval_comments || ''
    });
    setPdfFile(null);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(t('modules.leadership.policiesPage.messages.confirmDelete'));
    if (!confirmed) {
      return;
    }

    try {
      await deletePolicy(id);
      await loadPolicies();
    } catch {
      setError(t('modules.leadership.policiesPage.messages.deleteError'));
    }
  };

  const handleStatusAction = async (id, action) => {
    try {
      if (action === 'approve') {
        await approvePolicy(id);
      }
      if (action === 'publish') {
        await publishPolicy(id);
      }
      if (action === 'obsolete') {
        await makeObsoletePolicy(id);
      }
      await loadPolicies();
    } catch {
      setError(t('modules.leadership.policiesPage.messages.statusError'));
    }
  };

  return (
    <div className="space-y-6" style={{ fontFamily: '"Sora", "Work Sans", sans-serif' }}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">{t('modules.leadership.policiesPage.title')}</h1>
          <p className="muted-text">{t('modules.leadership.policiesPage.subtitle')}</p>
        </div>
        <button
          type="button"
          onClick={resetForm}
          className="rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/40"
        >
          {t('modules.leadership.policiesPage.buttons.new')}
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
            <div className="py-10 text-center muted-text">{t('modules.leadership.policiesPage.messages.loading')}</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-700 dark:text-slate-200">
                <thead className="table-head-muted border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="px-3 py-3">{t('modules.leadership.policiesPage.table.version')}</th>
                    <th className="px-3 py-3">{t('modules.leadership.policiesPage.table.title')}</th>
                    <th className="px-3 py-3">{t('common.forms.status')}</th>
                    <th className="px-3 py-3">{t('modules.leadership.policiesPage.table.effectiveDate')}</th>
                    <th className="px-3 py-3 text-right">{t('modules.leadership.policiesPage.table.actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                  {policies.map((policy) => (
                    <tr key={policy.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/40">
                      <td className="px-3 py-3 font-medium text-slate-900 dark:text-slate-100">{policy.version}</td>
                      <td className="px-3 py-3">{policy.title}</td>
                      <td className="px-3 py-3 capitalize">{policy.status}</td>
                      <td className="px-3 py-3">{policy.effective_date || '-'}</td>
                      <td className="px-3 py-3 text-right">
                        <div className="flex flex-wrap justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleEdit(policy)}
                            className="rounded-md border border-slate-300 dark:border-slate-700 px-2 py-1 text-xs text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700/60"
                          >
                            {t('common.buttons.edit')}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleStatusAction(policy.id, 'approve')}
                            className="rounded-md border border-emerald-300 dark:border-emerald-500/50 px-2 py-1 text-xs text-emerald-700 dark:text-emerald-200 hover:bg-emerald-50 dark:hover:bg-emerald-500/10"
                          >
                            {t('common.buttons.approve')}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleStatusAction(policy.id, 'publish')}
                            className="rounded-md border border-sky-300 dark:border-sky-500/50 px-2 py-1 text-xs text-sky-700 dark:text-sky-200 hover:bg-sky-50 dark:hover:bg-sky-500/10"
                          >
                            {t('common.buttons.publish')}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleStatusAction(policy.id, 'obsolete')}
                            className="rounded-md border border-amber-300 dark:border-amber-500/50 px-2 py-1 text-xs text-amber-700 dark:text-amber-200 hover:bg-amber-50 dark:hover:bg-amber-500/10"
                          >
                            {t('modules.leadership.policiesPage.options.status.obsolete')}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(policy.id)}
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
              {editingId ? t('modules.leadership.policiesPage.form.editTitle') : t('modules.leadership.policiesPage.form.newTitle')}
            </h2>
            <p className="form-label-muted">{t('modules.leadership.policiesPage.form.organization')}: {orgName || t('modules.leadership.policiesPage.form.unselected')}</p>
          </div>

          <div className="grid gap-4">
            <label className="form-label-muted">
              {t('modules.leadership.policiesPage.form.version')}
              <input
                type="text"
                value={form.version}
                onChange={(event) => setForm({ ...form, version: event.target.value })}
                className="field-control"
                required
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.policiesPage.form.title')}
              <input
                type="text"
                value={form.title}
                onChange={(event) => setForm({ ...form, title: event.target.value })}
                className="field-control"
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.policiesPage.form.content')}
              <textarea
                value={form.content}
                onChange={(event) => setForm({ ...form, content: event.target.value })}
                className="field-control h-24"
                required
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.policiesPage.form.customerFocus')}
              <textarea
                value={form.customer_focus}
                onChange={(event) => setForm({ ...form, customer_focus: event.target.value })}
                className="field-control h-16"
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.policiesPage.form.frameworkForObjectives')}
              <textarea
                value={form.framework_for_objectives}
                onChange={(event) => setForm({ ...form, framework_for_objectives: event.target.value })}
                className="field-control h-16"
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.policiesPage.form.commitmentRequirements')}
              <textarea
                value={form.commitment_requirements}
                onChange={(event) => setForm({ ...form, commitment_requirements: event.target.value })}
                className="field-control h-16"
              />
            </label>

            <label className="form-label-muted">
              {t('modules.leadership.policiesPage.form.commitmentImprovement')}
              <textarea
                value={form.commitment_improvement}
                onChange={(event) => setForm({ ...form, commitment_improvement: event.target.value })}
                className="field-control h-16"
              />
            </label>

            <div className="grid gap-3 sm:grid-cols-2">
              <label className="form-label-muted">
                {t('common.forms.status')}
                <select
                  value={form.status}
                  onChange={(event) => setForm({ ...form, status: event.target.value })}
                  className="field-control"
                >
                  <option value="draft">{t('modules.leadership.policiesPage.options.status.draft')}</option>
                  <option value="review">{t('modules.leadership.policiesPage.options.status.review')}</option>
                  <option value="approved">{t('modules.leadership.policiesPage.options.status.approved')}</option>
                  <option value="active">{t('modules.leadership.policiesPage.options.status.active')}</option>
                  <option value="obsolete">{t('modules.leadership.policiesPage.options.status.obsolete')}</option>
                </select>
              </label>

              <label className="form-label-muted">
                {t('modules.leadership.policiesPage.form.effectiveDate')}
                <input
                  type="date"
                  value={form.effective_date}
                  onChange={(event) => setForm({ ...form, effective_date: event.target.value })}
                  className="field-control"
                />
              </label>

              <label className="form-label-muted">
                {t('modules.leadership.policiesPage.form.reviewDate')}
                <input
                  type="date"
                  value={form.review_date}
                  onChange={(event) => setForm({ ...form, review_date: event.target.value })}
                  className="field-control"
                />
              </label>

              <label className="form-label-muted">
                {t('modules.leadership.policiesPage.form.approvalComments')}
                <input
                  type="text"
                  value={form.approval_comments}
                  onChange={(event) => setForm({ ...form, approval_comments: event.target.value })}
                  className="field-control"
                />
              </label>
            </div>

            <label className="form-label-muted">
              {t('modules.leadership.policiesPage.form.signedPdf')}
              <input
                type="file"
                onChange={(event) => setPdfFile(event.target.files?.[0] || null)}
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

export default PoliciesPage;