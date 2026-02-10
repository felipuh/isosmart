// features/planning/pages/RisksOpportunitiesPage.jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { getRisksOpportunities, createRiskOpportunity, updateRiskOpportunity, deleteRiskOpportunity } from '../api/planningApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const RisksOpportunitiesPage = () => {
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';

  const toNumberOrNull = (value) => {
    if (value === '' || value === null || value === undefined) return null;
    const parsed = Number(value);
    return Number.isNaN(parsed) ? null : parsed;
  };

  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    item_type: 'risk',
    code: '',
    title: '',
    description: '',
    category: 'operational',
    context: 'internal',
    probability: 3,
    impact: 3,
    feasibility: 3,
    benefit: 3,
    treatment: 'mitigate',
    treatment_description: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [filterType, setFilterType] = useState('all');

  useEffect(() => {
    if (orgId) loadData();
  }, [orgId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await getRisksOpportunities({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = {
        ...form,
        organization_id: orgId,
        organization_name: orgName,
        probability: form.item_type === 'risk' ? toNumberOrNull(form.probability) : null,
        impact: form.item_type === 'risk' ? toNumberOrNull(form.impact) : null,
        feasibility: form.item_type === 'opportunity' ? toNumberOrNull(form.feasibility) : null,
        benefit: form.item_type === 'opportunity' ? toNumberOrNull(form.benefit) : null
      };
      if (editingId) {
        await updateRiskOpportunity(editingId, payload);
      } else {
        await createRiskOpportunity(payload);
      }
      resetForm();
      loadData();
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setForm({
      item_type: item.item_type,
      code: item.code,
      title: item.title,
      description: item.description || '',
      category: item.category,
      context: item.context,
      probability: item.probability || 3,
      impact: item.impact || 3,
      feasibility: item.feasibility || 3,
      benefit: item.benefit || 3,
      treatment: item.treatment || 'mitigate',
      treatment_description: item.treatment_description || ''
    });
    setEditingId(item.id);
  };

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar?')) return;
    try {
      await deleteRiskOpportunity(id);
      loadData();
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const resetForm = () => {
    setForm({
      item_type: 'risk',
      code: '',
      title: '',
      description: '',
      category: 'operational',
      context: 'internal',
      probability: 3,
      impact: 3,
      feasibility: 3,
      benefit: 3,
      treatment: 'mitigate',
      treatment_description: ''
    });
    setEditingId(null);
  };

  const filteredItems = filterType === 'all' 
    ? items 
    : items.filter(i => i.item_type === filterType);

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Riesgos y Oportunidades</h1>
      
      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">{editingId ? 'Editar' : 'Nuevo'}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Tipo *</label>
              <select value={form.item_type} onChange={(e) => setForm({...form, item_type: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required>
                <option value="risk">Riesgo</option>
                <option value="opportunity">Oportunidad</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Código *</label>
              <input type="text" value={form.code} onChange={(e) => setForm({...form, code: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Categoría</label>
              <select value={form.category} onChange={(e) => setForm({...form, category: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="strategic">Estratégico</option>
                <option value="operational">Operacional</option>
                <option value="financial">Financiero</option>
                <option value="compliance">Cumplimiento</option>
                <option value="reputation">Reputacional</option>
                <option value="technology">Tecnológico</option>
                <option value="market">Mercado</option>
                <option value="other">Otro</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Contexto</label>
              <select value={form.context} onChange={(e) => setForm({...form, context: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="internal">Interno</option>
                <option value="external">Externo</option>
                <option value="both">Interno y Externo</option>
              </select>
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Título *</label>
              <input type="text" value={form.title} onChange={(e) => setForm({...form, title: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Descripción</label>
              <textarea value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="3" required />
            </div>
            {form.item_type === 'risk' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Probabilidad (1-5)</label>
                  <input type="number" min="1" max="5" value={form.probability} onChange={(e) => setForm({...form, probability: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Impacto (1-5)</label>
                  <input type="number" min="1" max="5" value={form.impact} onChange={(e) => setForm({...form, impact: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
                </div>
              </>
            )}
            {form.item_type === 'opportunity' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Factibilidad (1-5)</label>
                  <input type="number" min="1" max="5" value={form.feasibility} onChange={(e) => setForm({...form, feasibility: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Beneficio (1-5)</label>
                  <input type="number" min="1" max="5" value={form.benefit} onChange={(e) => setForm({...form, benefit: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
                </div>
              </>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Tratamiento</label>
              <select value={form.treatment} onChange={(e) => setForm({...form, treatment: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="avoid">Evitar</option>
                <option value="mitigate">Mitigar</option>
                <option value="transfer">Transferir</option>
                <option value="accept">Aceptar</option>
                <option value="exploit">Explotar (Oportunidad)</option>
                <option value="enhance">Mejorar (Oportunidad)</option>
              </select>
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Descripción del Tratamiento</label>
              <textarea value={form.treatment_description} onChange={(e) => setForm({...form, treatment_description: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" />
            </div>
          </div>
          <div className="flex space-x-3">
            <button type="submit" disabled={saving} className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
              {saving ? 'Guardando...' : editingId ? 'Actualizar' : 'Crear'}
            </button>
            {editingId && <button type="button" onClick={resetForm} className="px-6 py-2 bg-gray-600 text-white rounded-lg">Cancelar</button>}
          </div>
        </form>
      </div>

      <div className="flex space-x-2">
        {['all', 'risk', 'opportunity'].map(type => (
          <button
            key={type}
            onClick={() => setFilterType(type)}
            className={`px-4 py-2 rounded-lg ${filterType === type ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}
          >
            {type === 'all' ? 'Todos' : type === 'risk' ? 'Riesgos' : 'Oportunidades'}
          </button>
        ))}
      </div>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Código</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Título</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Tipo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Categoría</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Nivel</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {filteredItems.map(item => (
              <tr key={item.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-gray-300">{item.code}</td>
                <td className="px-6 py-4 text-sm text-white">{item.title}</td>
                <td className="px-6 py-4 text-sm">
                  <span className={`px-2 py-1 text-xs rounded ${item.item_type === 'risk' ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
                    {item.item_type_display}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-300">{item.category_display}</td>
                <td className="px-6 py-4 text-sm">
                  {item.item_type === 'risk' ? (
                    <span className={`px-2 py-1 text-xs rounded ${
                      item.risk_level >= 15 ? 'bg-red-500/20 text-red-400' :
                      item.risk_level >= 10 ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {item.risk_level}
                    </span>
                  ) : (
                    <span className="px-2 py-1 text-xs rounded bg-blue-500/20 text-blue-400">
                      {item.opportunity_score}
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-400 hover:text-blue-300">Editar</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-400 hover:text-red-300">Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredItems.length === 0 && <div className="text-center py-8 text-gray-400">No hay elementos</div>}
      </div>
    </div>
  );
};

export default RisksOpportunitiesPage;
