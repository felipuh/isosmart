import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import {
  getRACIMatrices,
  createRACIMatrix,
  updateRACIMatrix,
  deleteRACIMatrix
} from '../api/leadershipApi';

const normalizeList = (data) => (Array.isArray(data) ? data : data?.results || []);

const initialForm = {
  name: '',
  description: '',
  is_active: true
};

const RACIMatricesPage = () => {
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';

  const [matrices, setMatrices] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const loadMatrices = async () => {
    try {
      setLoading(true);
      const data = await getRACIMatrices();
      setMatrices(normalizeList(data));
    } catch (err) {
      setError('No se pudieron cargar las matrices.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMatrices();
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
    } catch (err) {
      setError('No se pudo guardar la matriz.');
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
    if (!window.confirm('Eliminar esta matriz?')) {
      return;
    }

    try {
      await deleteRACIMatrix(id);
      await loadMatrices();
    } catch (err) {
      setError('No se pudo eliminar la matriz.');
    }
  };

  return (
    <div className="space-y-6" style={{ fontFamily: '"Sora", "Work Sans", sans-serif' }}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">Matrices RACI</h1>
          <p className="text-sm text-slate-400">Define responsabilidades y autoridades.</p>
        </div>
        <button
          type="button"
          onClick={resetForm}
          className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:border-slate-500"
        >
          Nueva matriz
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
            <div className="py-10 text-center text-slate-400">Cargando matrices...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-200">
                <thead className="text-xs uppercase text-slate-400">
                  <tr>
                    <th className="px-3 py-2">Nombre</th>
                    <th className="px-3 py-2">Descripcion</th>
                    <th className="px-3 py-2">Activa</th>
                    <th className="px-3 py-2 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {matrices.map((matrix) => (
                    <tr key={matrix.id} className="hover:bg-slate-800/40">
                      <td className="px-3 py-2 font-medium text-slate-100">
                        <Link
                          to={`/leadership/raci/${matrix.id}`}
                          className="text-sky-300 hover:text-sky-200"
                        >
                          {matrix.name}
                        </Link>
                      </td>
                      <td className="px-3 py-2">{matrix.description || '-'}</td>
                      <td className="px-3 py-2">{matrix.is_active ? 'Si' : 'No'}</td>
                      <td className="px-3 py-2 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleEdit(matrix)}
                            className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-200"
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(matrix.id)}
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
              {editingId ? 'Editar matriz' : 'Nueva matriz'}
            </h2>
            <p className="text-xs text-slate-400">Organizacion: {orgName || 'Sin seleccionar'}</p>
          </div>

          <div className="grid gap-3">
            <label className="text-xs text-slate-400">
              Nombre
              <input
                type="text"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>

            <label className="text-xs text-slate-400">
              Descripcion
              <textarea
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
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
              Activa
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

export default RACIMatricesPage;
