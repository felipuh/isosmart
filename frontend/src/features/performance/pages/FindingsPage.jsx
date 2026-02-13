import React, { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import Modal from '../../../components/Common/Modal';
import {
  getAudits,
  getFindings,
  createFinding,
  updateFinding,
  deleteFinding
} from '../api/performanceApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const findingTypeLabels = {
  nc_major: 'No Conformidad Mayor',
  nc_minor: 'No Conformidad Menor',
  observation: 'Observacion',
  opportunity: 'Oportunidad',
  conformity: 'Conformidad'
};

const statusLabels = {
  open: 'Abierto',
  in_progress: 'En Proceso',
  resolved: 'Resuelto',
  verified: 'Verificado',
  closed: 'Cerrado'
};

const FindingsPage = () => {
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;

  const [audits, setAudits] = useState([]);
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    audit: '',
    finding_number: '',
    finding_type: 'nc_minor',
    clause_reference: '',
    description: '',
    evidence: '',
    status: 'open',
    due_date: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const auditMap = useMemo(() => {
    return audits.reduce((acc, audit) => {
      acc[audit.id] = audit;
      return acc;
    }, {});
  }, [audits]);

  useEffect(() => {
    if (orgId) loadData();
  }, [orgId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [auditsData, findingsData] = await Promise.all([
        getAudits({ organization_id: orgId }),
        getFindings({ organization_id: orgId })
      ]);
      setAudits(normalizeList(auditsData));
      setItems(normalizeList(findingsData));
    } catch (error) {
      console.error('Error loading findings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      setSaving(true);
      const payload = {
        ...form,
        organization_id: orgId,
        audit: Number(form.audit) || null
      };
      if (editingId) {
        await updateFinding(editingId, payload);
      } else {
        await createFinding(payload);
      }
      resetForm();
      await loadData();
      setShowForm(false);
    } catch (error) {
      console.error('Error saving finding:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setForm({
      audit: item.audit,
      finding_number: item.finding_number || '',
      finding_type: item.finding_type || 'nc_minor',
      clause_reference: item.clause_reference || '',
      description: item.description || '',
      evidence: item.evidence || '',
      status: item.status || 'open',
      due_date: item.due_date || ''
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete finding?')) return;
    try {
      await deleteFinding(id);
      loadData();
    } catch (error) {
      console.error('Error deleting finding:', error);
    }
  };

  const resetForm = () => {
    setForm({
      audit: '',
      finding_number: '',
      finding_type: 'nc_minor',
      clause_reference: '',
      description: '',
      evidence: '',
      status: 'open',
      due_date: ''
    });
    setEditingId(null);
  };

  const openForm = () => {
    resetForm();
    setShowForm(true);
  };

  const closeForm = () => {
    resetForm();
    setShowForm(false);
  };

  if (loading) {
    return (
      <div className="flex justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-3xl font-bold text-white">Hallazgos de Auditoria</h1>
        <button
          type="button"
          onClick={openForm}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          Nuevo hallazgo
        </button>
      </div>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Hallazgo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Auditoria</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Tipo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Estado</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-gray-300">{item.finding_number}</td>
                <td className="px-6 py-4 text-sm text-white">
                  {auditMap[item.audit]?.audit_code || item.audit}
                </td>
                <td className="px-6 py-4 text-sm text-gray-300">{findingTypeLabels[item.finding_type] || item.finding_type}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{statusLabels[item.status] || item.status}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-400 hover:text-blue-300">Editar</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-400 hover:text-red-300">Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="text-center py-8 text-gray-400">No hay hallazgos</div>}
      </div>

      <Modal
        title={editingId ? 'Editar hallazgo' : 'Nuevo hallazgo'}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Auditoria *</label>
              <select
                value={form.audit}
                onChange={(event) => setForm({ ...form, audit: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              >
                <option value="">Selecciona auditoria</option>
                {audits.map((audit) => (
                  <option key={audit.id} value={audit.id}>
                    {audit.audit_code} - {audit.title}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Numero de Hallazgo *</label>
              <input
                type="text"
                value={form.finding_number}
                onChange={(event) => setForm({ ...form, finding_number: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Tipo *</label>
              <select
                value={form.finding_type}
                onChange={(event) => setForm({ ...form, finding_type: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              >
                {Object.entries(findingTypeLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Referencia de Clausula *</label>
              <input
                type="text"
                value={form.clause_reference}
                onChange={(event) => setForm({ ...form, clause_reference: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Fecha Compromiso</label>
              <input
                type="date"
                value={form.due_date}
                onChange={(event) => setForm({ ...form, due_date: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Estado</label>
              <select
                value={form.status}
                onChange={(event) => setForm({ ...form, status: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              >
                {Object.entries(statusLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Descripcion *</label>
              <textarea
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="3"
                required
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Evidencia</label>
              <textarea
                value={form.evidence}
                onChange={(event) => setForm({ ...form, evidence: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="2"
              />
            </div>
          </div>
          <div className="flex space-x-3">
            <button type="submit" disabled={saving} className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
              {saving ? 'Guardando...' : editingId ? 'Actualizar' : 'Crear'}
            </button>
            <button type="button" onClick={closeForm} className="px-6 py-2 bg-gray-600 text-white rounded-lg">Cancelar</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default FindingsPage;
