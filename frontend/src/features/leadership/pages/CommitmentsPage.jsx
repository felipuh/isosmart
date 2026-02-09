import React, { useEffect, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { getCommitments, createCommitment, updateCommitment, deleteCommitment } from '../api/leadershipApi';

const normalizeList = (data) => (Array.isArray(data) ? data : data?.results || []);

const commitmentTypes = [
  { value: 'responsibility', label: 'Responsabilidad por SGC' },
  { value: 'policy', label: 'Politica y objetivos' },
  { value: 'integration', label: 'Integracion en procesos' },
  { value: 'resources', label: 'Disponibilidad de recursos' },
  { value: 'importance', label: 'Comunicacion de importancia' },
  { value: 'results', label: 'Logro de resultados' },
  { value: 'engagement', label: 'Participacion de personal' },
  { value: 'improvement', label: 'Promocion de mejora' },
  { value: 'management', label: 'Apoyo a gestion' }
];

const evidenceTypes = [
  { value: 'meeting', label: 'Acta de reunion' },
  { value: 'communication', label: 'Comunicacion' },
  { value: 'decision', label: 'Decision documentada' },
  { value: 'resource_allocation', label: 'Asignacion de recursos' },
  { value: 'review', label: 'Revision por la direccion' },
  { value: 'policy_update', label: 'Actualizacion de politica' },
  { value: 'other', label: 'Otro' }
];

const statusOptions = [
  { value: 'planned', label: 'Planificado' },
  { value: 'in_progress', label: 'En progreso' },
  { value: 'completed', label: 'Completado' },
  { value: 'verified', label: 'Verificado' }
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

  const loadCommitments = async () => {
    try {
      setLoading(true);
      const data = await getCommitments();
      setCommitments(normalizeList(data));
    } catch (err) {
      setError('No se pudieron cargar los compromisos.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCommitments();
  }, []);

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
    } catch (err) {
      setError('No se pudo guardar el compromiso.');
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
    if (!window.confirm('Eliminar este compromiso?')) {
      return;
    }

    try {
      await deleteCommitment(id);
      await loadCommitments();
    } catch (err) {
      setError('No se pudo eliminar el compromiso.');
    }
  };

  return (
    <div className="space-y-6" style={{ fontFamily: '"Sora", "Work Sans", sans-serif' }}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">Compromisos de liderazgo</h1>
          <p className="text-sm text-slate-400">Evidencias de liderazgo ISO 9001.</p>
        </div>
        <button
          type="button"
          onClick={resetForm}
          className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:border-slate-500"
        >
          Nuevo compromiso
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
            <div className="py-10 text-center text-slate-400">Cargando compromisos...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-200">
                <thead className="text-xs uppercase text-slate-400">
                  <tr>
                    <th className="px-3 py-2">Titulo</th>
                    <th className="px-3 py-2">Tipo</th>
                    <th className="px-3 py-2">Fecha</th>
                    <th className="px-3 py-2">Estado</th>
                    <th className="px-3 py-2 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {commitments.map((commitment) => (
                    <tr key={commitment.id} className="hover:bg-slate-800/40">
                      <td className="px-3 py-2 font-medium text-slate-100">{commitment.title}</td>
                      <td className="px-3 py-2">{commitment.commitment_type_display || commitment.commitment_type}</td>
                      <td className="px-3 py-2">{commitment.commitment_date}</td>
                      <td className="px-3 py-2">{commitment.status_display || commitment.status}</td>
                      <td className="px-3 py-2 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleEdit(commitment)}
                            className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-200"
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(commitment.id)}
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
              {editingId ? 'Editar compromiso' : 'Nuevo compromiso'}
            </h2>
            <p className="text-xs text-slate-400">Organizacion: {orgName || 'Sin seleccionar'}</p>
          </div>

          <div className="grid gap-3">
            <label className="text-xs text-slate-400">
              Tipo de compromiso
              <select
                value={form.commitment_type}
                onChange={(event) => setForm({ ...form, commitment_type: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              >
                {commitmentTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-xs text-slate-400">
              Titulo
              <input
                type="text"
                value={form.title}
                onChange={(event) => setForm({ ...form, title: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>

            <label className="text-xs text-slate-400">
              Descripcion
              <textarea
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                className="mt-1 h-24 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>

            <label className="text-xs text-slate-400">
              Tipo de evidencia
              <select
                value={form.evidence_type}
                onChange={(event) => setForm({ ...form, evidence_type: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              >
                {evidenceTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-xs text-slate-400">
              URL evidencia
              <input
                type="url"
                value={form.evidence_url}
                onChange={(event) => setForm({ ...form, evidence_url: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
            </label>

            <label className="text-xs text-slate-400">
              Documento evidencia
              <input
                type="file"
                onChange={(event) => setDocumentFile(event.target.files?.[0] || null)}
                className="mt-1 w-full text-xs text-slate-300"
              />
            </label>

            <label className="text-xs text-slate-400">
              Fecha
              <input
                type="date"
                value={form.commitment_date}
                onChange={(event) => setForm({ ...form, commitment_date: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>

            <label className="text-xs text-slate-400">
              Estado
              <select
                value={form.status}
                onChange={(event) => setForm({ ...form, status: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              >
                {statusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
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
              {saving ? 'Guardando...' : editingId ? 'Actualizar' : 'Crear'}
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

export default CommitmentsPage;
