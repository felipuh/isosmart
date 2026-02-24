import React, { useEffect, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import { getCustomerFocus, createCustomerFocus, updateCustomerFocus, deleteCustomerFocus } from '../api/leadershipApi';

const normalizeList = (data) => (Array.isArray(data) ? data : data?.results || []);

const focusTypes = [
  { value: 'requirements', label: 'Determinacion de requisitos' },
  { value: 'risks', label: 'Determinacion de riesgos' },
  { value: 'satisfaction', label: 'Enfoque en satisfacción' },
  { value: 'compliance', label: 'Cumplimiento legal' }
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

  const loadItems = async () => {
    try {
      setLoading(true);
      const data = await getCustomerFocus();
      setItems(normalizeList(data));
    } catch {
      setError('No se pudieron cargar las evidencias.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadItems();
  }, []);

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
      setError('No se pudo guardar la evidencia.');
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
    if (!window.confirm('Eliminar esta evidencia?')) {
      return;
    }

    try {
      await deleteCustomerFocus(id);
      await loadItems();
    } catch {
      setError('No se pudo eliminar la evidencia.');
    }
  };

  return (
    <div className="space-y-6" style={{ fontFamily: '"Sora", "Work Sans", sans-serif' }}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">Enfoque al cliente</h1>
          <p className="text-sm text-slate-400">Evidencias y acciones enfocadas en el cliente.</p>
        </div>
        <button
          type="button"
          onClick={resetForm}
          className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:border-slate-500"
        >
          Nueva evidencia
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
            <div className="py-10 text-center text-slate-400">Cargando evidencias...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-200">
                <thead className="text-xs uppercase text-slate-400">
                  <tr>
                    <th className="px-3 py-2">Título</th>
                    <th className="px-3 py-2">Tipo</th>
                    <th className="px-3 py-2">{t('common.forms.date')}</th>
                    <th className="px-3 py-2 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {items.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/40">
                      <td className="px-3 py-2 font-medium text-slate-100">{item.title}</td>
                      <td className="px-3 py-2">{item.focus_type_display || item.focus_type}</td>
                      <td className="px-3 py-2">{item.action_date}</td>
                      <td className="px-3 py-2 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleEdit(item)}
                            className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-200"
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(item.id)}
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
              {editingId ? 'Editar evidencia' : 'Nueva evidencia'}
            </h2>
            <p className="text-xs text-slate-400">Organizacion: {orgName || 'Sin seleccionar'}</p>
          </div>

          <div className="grid gap-3">
            <label className="text-xs text-slate-400">
              Tipo
              <select
                value={form.focus_type}
                onChange={(event) => setForm({ ...form, focus_type: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              >
                {focusTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-xs text-slate-400">
              Título
              <input
                type="text"
                value={form.title}
                onChange={(event) => setForm({ ...form, title: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>

            <label className="text-xs text-slate-400">
              Descripción
              <textarea
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>

            <label className="text-xs text-slate-400">
              Acción tomada
              <textarea
                value={form.action_taken}
                onChange={(event) => setForm({ ...form, action_taken: event.target.value })}
                className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>

            <label className="text-xs text-slate-400">
              {t('literals.Resultados')}
              <textarea
                value={form.results}
                onChange={(event) => setForm({ ...form, results: event.target.value })}
                className="mt-1 h-16 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
            </label>

            <label className="text-xs text-slate-400">
              Fecha de acción
              <input
                type="date"
                value={form.action_date}
                onChange={(event) => setForm({ ...form, action_date: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>

            <label className="text-xs text-slate-400">
              Evidencia
              <input
                type="file"
                onChange={(event) => setEvidenceFile(event.target.files?.[0] || null)}
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

export default CustomerFocusPage;
