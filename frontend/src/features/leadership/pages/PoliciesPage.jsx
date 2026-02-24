import React, { useEffect, useState } from 'react';
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

const normalizeList = (data) => (Array.isArray(data) ? data : data?.results || []);

const initialForm = {
  version: '',
  title: 'Politica de Calidad',
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

  const loadPolicies = async () => {
    try {
      setLoading(true);
      const data = await getPolicies();
      setPolicies(normalizeList(data));
    } catch {
      setError('No se pudieron cargar las políticas.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, []);

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
      setError('No se pudo guardar la política.');
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (policy) => {
    setEditingId(policy.id);
    setForm({
      version: policy.version || '',
      title: policy.title || 'Politica de Calidad',
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
    if (!window.confirm('Eliminar esta política?')) {
      return;
    }

    try {
      await deletePolicy(id);
      await loadPolicies();
    } catch {
      setError('No se pudo eliminar la política.');
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
      setError('No se pudo actualizar el estado.');
    }
  };

  return (
    <div className="space-y-6" style={{ fontFamily: '"Sora", "Work Sans", sans-serif' }}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">Politicas de Calidad</h1>
          <p className="text-sm text-slate-400">Gestion y aprobación de políticas ISO 9001.</p>
        </div>
        <button
          type="button"
          onClick={resetForm}
          className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:border-slate-500"
        >
          Nueva política
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
            <div className="py-10 text-center text-slate-400">Cargando políticas...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-200">
                <thead className="text-xs uppercase text-slate-400">
                  <tr>
                    <th className="px-3 py-2">Version</th>
                    <th className="px-3 py-2">Título</th>
                    <th className="px-3 py-2">{t('common.forms.status')}</th>
                    <th className="px-3 py-2">Vigencia</th>
                    <th className="px-3 py-2 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {policies.map((policy) => (
                    <tr key={policy.id} className="hover:bg-slate-800/40">
                      <td className="px-3 py-2 font-medium text-slate-100">{policy.version}</td>
                      <td className="px-3 py-2">{policy.title}</td>
                      <td className="px-3 py-2 capitalize">{policy.status}</td>
                      <td className="px-3 py-2">{policy.effective_date || '-'}</td>
                      <td className="px-3 py-2 text-right">
                        <div className="flex flex-wrap justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleEdit(policy)}
                            className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-200"
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            onClick={() => handleStatusAction(policy.id, 'approve')}
                            className="rounded-md border border-emerald-500/50 px-2 py-1 text-xs text-emerald-200"
                          >
                            Aprobar
                          </button>
                          <button
                            type="button"
                            onClick={() => handleStatusAction(policy.id, 'publish')}
                            className="rounded-md border border-sky-500/50 px-2 py-1 text-xs text-sky-200"
                          >
                            Publicar
                          </button>
                          <button
                            type="button"
                            onClick={() => handleStatusAction(policy.id, 'obsolete')}
                            className="rounded-md border border-amber-500/50 px-2 py-1 text-xs text-amber-200"
                          >
                            {t('literals.Obsoleta')}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(policy.id)}
                            className="rounded-md border border-red-500/50 px-2 py-1 text-xs text-red-200"
                          >
                            Eliminar
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
              {editingId ? 'Editar política' : 'Nueva política'}
            </h2>
            <p className="text-xs text-slate-400">Organizacion: {orgName || 'Sin seleccionar'}</p>
          </div>

          <div className="grid gap-3">
            <label className="text-xs text-slate-400">
              Version
              <input
                type="text"
                value={form.version}
                onChange={(event) => setForm({ ...form, version: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>

            <label className="text-xs text-slate-400">
              Título
              <input
                type="text"
                value={form.title}
                onChange={(event) => setForm({ ...form, title: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
            </label>

            <label className="text-xs text-slate-400">
              Contenido
              <textarea
                value={form.content}
                onChange={(event) => setForm({ ...form, content: event.target.value })}
                className="mt-1 h-24 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>

            <label className="text-xs text-slate-400">
              Enfoque al cliente
              <textarea
                value={form.customer_focus}
                onChange={(event) => setForm({ ...form, customer_focus: event.target.value })}
                className="mt-1 h-16 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
            </label>

            <label className="text-xs text-slate-400">
              Marco para objetivos
              <textarea
                value={form.framework_for_objectives}
                onChange={(event) => setForm({ ...form, framework_for_objectives: event.target.value })}
                className="mt-1 h-16 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
            </label>

            <label className="text-xs text-slate-400">
              Compromiso con requisitos
              <textarea
                value={form.commitment_requirements}
                onChange={(event) => setForm({ ...form, commitment_requirements: event.target.value })}
                className="mt-1 h-16 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
            </label>

            <label className="text-xs text-slate-400">
              Compromiso con mejora
              <textarea
                value={form.commitment_improvement}
                onChange={(event) => setForm({ ...form, commitment_improvement: event.target.value })}
                className="mt-1 h-16 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
            </label>

            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-xs text-slate-400">
                Estado
                <select
                  value={form.status}
                  onChange={(event) => setForm({ ...form, status: event.target.value })}
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                >
                  <option value="draft">{t('literals.Borrador')}</option>
                  <option value="review">{t('literals.Revision')}</option>
                  <option value="approved">{t('literals.Aprobada')}</option>
                  <option value="active">{t('literals.Activa')}</option>
                  <option value="obsolete">{t('literals.Obsoleta')}</option>
                </select>
              </label>

              <label className="text-xs text-slate-400">
                Fecha de vigencia
                <input
                  type="date"
                  value={form.effective_date}
                  onChange={(event) => setForm({ ...form, effective_date: event.target.value })}
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                />
              </label>

              <label className="text-xs text-slate-400">
                Fecha de revision
                <input
                  type="date"
                  value={form.review_date}
                  onChange={(event) => setForm({ ...form, review_date: event.target.value })}
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                />
              </label>

              <label className="text-xs text-slate-400">
                Comentarios de aprobación
                <input
                  type="text"
                  value={form.approval_comments}
                  onChange={(event) => setForm({ ...form, approval_comments: event.target.value })}
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                />
              </label>
            </div>

            <label className="text-xs text-slate-400">
              PDF firmado
              <input
                type="file"
                onChange={(event) => setPdfFile(event.target.files?.[0] || null)}
                className="mt-1 w-full text-xs text-slate-300"
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
              className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-200"
            >
              Limpiar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PoliciesPage;
