import React, { useEffect, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import {
  getAnalyses,
  createAnalysis,
  updateAnalysis,
  deleteAnalysis
} from '../api/performanceApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const analysisTypeLabels = {
  trend: 'Trend',
  comparative: 'Comparative',
  root_cause: 'Root Cause',
  predictive: 'Predictive',
  statistical: 'Statistical'
};

const statusLabels = {
  draft: 'Draft',
  in_review: 'In Review',
  completed: 'Completed',
  archived: 'Archived'
};

const AnalysesPage = () => {
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;

  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    title: '',
    analysis_type: 'trend',
    period_start: '',
    period_end: '',
    objectives: '',
    methodology: '',
    findings: '',
    conclusions: '',
    recommendations: '',
    status: 'draft'
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (orgId) loadAnalyses();
  }, [orgId]);

  const loadAnalyses = async () => {
    try {
      setLoading(true);
      const data = await getAnalyses({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error loading analyses:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      setSaving(true);
      const payload = { ...form, organization_id: orgId };
      if (editingId) {
        await updateAnalysis(editingId, payload);
      } else {
        await createAnalysis(payload);
      }
      resetForm();
      loadAnalyses();
    } catch (error) {
      console.error('Error saving analysis:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setForm({
      title: item.title || '',
      analysis_type: item.analysis_type || 'trend',
      period_start: item.period_start || '',
      period_end: item.period_end || '',
      objectives: item.objectives || '',
      methodology: item.methodology || '',
      findings: item.findings || '',
      conclusions: item.conclusions || '',
      recommendations: item.recommendations || '',
      status: item.status || 'draft'
    });
    setEditingId(item.id);
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete analysis?')) return;
    try {
      await deleteAnalysis(id);
      loadAnalyses();
    } catch (error) {
      console.error('Error deleting analysis:', error);
    }
  };

  const resetForm = () => {
    setForm({
      title: '',
      analysis_type: 'trend',
      period_start: '',
      period_end: '',
      objectives: '',
      methodology: '',
      findings: '',
      conclusions: '',
      recommendations: '',
      status: 'draft'
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
      <h1 className="text-3xl font-bold text-white">Data Analyses</h1>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">{editingId ? 'Edit' : 'New'} Analysis</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Title *</label>
              <input
                type="text"
                value={form.title}
                onChange={(event) => setForm({ ...form, title: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Type *</label>
              <select
                value={form.analysis_type}
                onChange={(event) => setForm({ ...form, analysis_type: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              >
                {Object.entries(analysisTypeLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Period Start *</label>
              <input
                type="date"
                value={form.period_start}
                onChange={(event) => setForm({ ...form, period_start: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Period End *</label>
              <input
                type="date"
                value={form.period_end}
                onChange={(event) => setForm({ ...form, period_end: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
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
              <label className="block text-sm font-medium text-gray-300 mb-2">Objectives *</label>
              <textarea
                value={form.objectives}
                onChange={(event) => setForm({ ...form, objectives: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="2"
                required
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Methodology *</label>
              <textarea
                value={form.methodology}
                onChange={(event) => setForm({ ...form, methodology: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="2"
                required
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Findings *</label>
              <textarea
                value={form.findings}
                onChange={(event) => setForm({ ...form, findings: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="2"
                required
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Conclusions *</label>
              <textarea
                value={form.conclusions}
                onChange={(event) => setForm({ ...form, conclusions: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="2"
                required
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Recommendations *</label>
              <textarea
                value={form.recommendations}
                onChange={(event) => setForm({ ...form, recommendations: event.target.value })}
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
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Title</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Period</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-white">{item.title}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{analysisTypeLabels[item.analysis_type] || item.analysis_type}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{item.period_start} - {item.period_end}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{statusLabels[item.status] || item.status}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-400 hover:text-blue-300">Edit</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-400 hover:text-red-300">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="text-center py-8 text-gray-400">No analyses yet</div>}
      </div>
    </div>
  );
};

export default AnalysesPage;
