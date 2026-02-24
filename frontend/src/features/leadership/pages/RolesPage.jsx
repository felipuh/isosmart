import React, { useEffect, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import { getRoles, createRole, updateRole, deleteRole } from '../api/leadershipApi';

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

  const loadRoles = async () => {
    try {
      setLoading(true);
      const data = await getRoles();
      setRoles(normalizeList(data));
    } catch {
      setError('No se pudieron cargar los roles.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRoles();
  }, []);

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
      setError('No se pudo guardar el rol.');
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
    if (!window.confirm('Eliminar este rol?')) {
      return;
    }

    try {
      await deleteRole(id);
      await loadRoles();
    } catch {
      setError('No se pudo eliminar el rol.');
    }
  };

  return (
    <div className="space-y-6" style={{ fontFamily: '"Sora", "Work Sans", sans-serif' }}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">Roles organizacionales</h1>
          <p className="text-sm text-slate-400">Define responsabilidades y jerarquias.</p>
        </div>
        <button
          type="button"
          onClick={resetForm}
          className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:border-slate-500"
        >
          Nuevo rol
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
            <div className="py-10 text-center text-slate-400">Cargando roles...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-200">
                <thead className="text-xs uppercase text-slate-400">
                  <tr>
                    <th className="px-3 py-2">{t('common.forms.name')}</th>
                    <th className="px-3 py-2">Codigo</th>
                    <th className="px-3 py-2">Nivel</th>
                    <th className="px-3 py-2">{t('literals.Activo')}</th>
                    <th className="px-3 py-2 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {roles.map((role) => (
                    <tr key={role.id} className="hover:bg-slate-800/40">
                      <td className="px-3 py-2 font-medium text-slate-100">{role.name}</td>
                      <td className="px-3 py-2">{role.code}</td>
                      <td className="px-3 py-2">{role.level}</td>
                      <td className="px-3 py-2">{role.is_active ? 'Si' : 'No'}</td>
                      <td className="px-3 py-2 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleEdit(role)}
                            className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-200"
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(role.id)}
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
              {editingId ? 'Editar rol' : 'Nuevo rol'}
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
              Codigo
              <input
                type="text"
                value={form.code}
                onChange={(event) => setForm({ ...form, code: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>

            <label className="text-xs text-slate-400">
              Nivel
              <input
                type="number"
                min="1"
                max="10"
                value={form.level}
                onChange={(event) => setForm({ ...form, level: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>

            <label className="text-xs text-slate-400">
              Reporta a
              <select
                value={form.reports_to}
                onChange={(event) => setForm({ ...form, reports_to: event.target.value })}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              >
                <option value="">{t('literals.Sin dependencia')}</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-xs text-slate-400">
              Descripción
              <textarea
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                className="mt-1 h-20 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
            </label>

            <label className="text-xs text-slate-400">
              Responsabilidades (separadas por coma)
              <textarea
                value={form.responsibilities}
                onChange={(event) => setForm({ ...form, responsibilities: event.target.value })}
                className="mt-1 h-16 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
            </label>

            <label className="text-xs text-slate-400">
              Autoridades (separadas por coma)
              <textarea
                value={form.authorities}
                onChange={(event) => setForm({ ...form, authorities: event.target.value })}
                className="mt-1 h-16 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
            </label>

            <label className="text-xs text-slate-400">
              Competencias requeridas (separadas por coma)
              <textarea
                value={form.required_competencies}
                onChange={(event) => setForm({ ...form, required_competencies: event.target.value })}
                className="mt-1 h-16 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
            </label>

            <div className="flex items-center gap-4 text-xs text-slate-300">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.is_qms_role}
                  onChange={(event) => setForm({ ...form, is_qms_role: event.target.checked })}
                  className="h-4 w-4 rounded border-slate-600"
                />
                Rol SGC
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
                  className="h-4 w-4 rounded border-slate-600"
                />
                {t('literals.Activo')}
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

export default RolesPage;
