import React, { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import {
  getAudits,
  getFindings,
  createFinding,
  updateFinding,
  deleteFinding
} from '../api/performanceApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const findingTypeLabels = {
  nc_major: 'Major Nonconformity',
  nc_minor: 'Minor Nonconformity',
  observation: 'Observation',
  opportunity: 'Opportunity',
  conformity: 'Conformity'
};

const statusLabels = {
  open: 'Open',
  in_progress: 'In Progress',
  resolved: 'Resolved',
  verified: 'Verified',
  closed: 'Closed'
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
      loadData();
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

  if (loading) {
    return (
      <div className="flex justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Audit Findings</h1>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">{editingId ? 'Edit' : 'New'} Finding</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Audit *</label>
              <select
                value={form.audit}
                onChange={(event) => setForm({ ...form, audit: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              >
                <option value="">Select audit</option>
                {audits.map((audit) => (
                  <option key={audit.id} value={audit.id}>
                    {audit.audit_code} - {audit.title}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Finding Number *</label>
              <input
                type="text"
                value={form.finding_number}
                onChange={(event) => setForm({ ...form, finding_number: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Type *</label>
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
              <label className="block text-sm font-medium text-gray-300 mb-2">Clause Reference *</label>
              <input
                type="text"
                value={form.clause_reference}
                onChange={(event) => setForm({ ...form, clause_reference: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Due Date</label>
              <input
                type="date"
                value={form.due_date}
                onChange={(event) => setForm({ ...form, due_date: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Status</label>
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
              <label className="block text-sm font-medium text-gray-300 mb-2">Description *</label>
              <textarea
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="2"
                required
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Evidence *</label>
              <textarea
                value={form.evidence}
                onChange={(event) => setForm({ ...form, evidence: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="2"
                required
              />
            </div>
          </div>
          <div className="flex space-x-3">
            <button type="submit" disabled={saving} className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
              {saving ? 'Saving...' : editingId ? 'Update' : 'Create'}
            </button>
            {editingId && (
              <button type="button" onClick={resetForm} className="px-6 py-2 bg-gray-600 text-white rounded-lg">Cancel</button>
            )}
          </div>
        </form>
      </div>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Finding</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Audit</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Actions</th>
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
                  <button onClick={() => handleEdit(item)} className="text-blue-400 hover:text-blue-300">Edit</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-400 hover:text-red-300">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="text-center py-8 text-gray-400">No findings yet</div>}
      </div>
    </div>
  );
};

export default FindingsPage;
