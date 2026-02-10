import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { getCustomerRequirements, createCustomerRequirement, updateCustomerRequirement, deleteCustomerRequirement } from '../api/operationsApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const CustomerRequirementsPage = () => {
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';

  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    customer_name: '',
    customer_code: '',
    contact_person: '',
    requirement_code: '',
    requirement_title: '',
    description: '',
    requirement_type: 'product',
    communication_date: '',
    communication_method: '',
    can_meet_requirement: true
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (orgId) loadData();
  }, [orgId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await getCustomerRequirements({ organization_id: orgId });
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
      const payload = { ...form, organization_id: orgId, organization_name: orgName, status: 'identified' };
      if (editingId) {
        await updateCustomerRequirement(editingId, payload);
      } else {
        await createCustomerRequirement(payload);
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
      customer_name: item.customer_name,
      customer_code: item.customer_code || '',
      contact_person: item.contact_person || '',
      requirement_code: item.requirement_code,
      requirement_title: item.requirement_title,
      description: item.description || '',
      requirement_type: item.requirement_type,
      communication_date: item.communication_date,
      communication_method: item.communication_method || '',
      can_meet_requirement: item.can_meet_requirement
    });
    setEditingId(item.id);
  };

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar?')) return;
    try {
      await deleteCustomerRequirement(id);
      loadData();
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const resetForm = () => {
    setForm({
      customer_name: '',
      customer_code: '',
      contact_person: '',
      requirement_code: '',
      requirement_title: '',
      description: '',
      requirement_type: 'product',
      communication_date: '',
      communication_method: '',
      can_meet_requirement: true
    });
    setEditingId(null);
  };

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Requisitos del Cliente</h1>
      
      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">{editingId ? 'Editar' : 'Nuevo'} Requisito</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Cliente *</label>
              <input type="text" value={form.customer_name} onChange={(e) => setForm({...form, customer_name: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Código Cliente</label>
              <input type="text" value={form.customer_code} onChange={(e) => setForm({...form, customer_code: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Contacto</label>
              <input type="text" value={form.contact_person} onChange={(e) => setForm({...form, contact_person: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Código *</label>
              <input type="text" value={form.requirement_code} onChange={(e) => setForm({...form, requirement_code: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Tipo</label>
              <select value={form.requirement_type} onChange={(e) => setForm({...form, requirement_type: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="product">Producto</option>
                <option value="service">Servicio</option>
                <option value="delivery">Entrega</option>
                <option value="quality">Calidad</option>
                <option value="regulatory">Regulatorio</option>
                <option value="other">Otro</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Título *</label>
              <input type="text" value={form.requirement_title} onChange={(e) => setForm({...form, requirement_title: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Fecha Comunicación *</label>
              <input type="date" value={form.communication_date} onChange={(e) => setForm({...form, communication_date: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Método</label>
              <input type="text" value={form.communication_method} onChange={(e) => setForm({...form, communication_method: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" placeholder="Email, Reunión, Contrato" />
            </div>
            <div className="flex items-center">
              <label className="flex items-center space-x-2">
                <input type="checkbox" checked={form.can_meet_requirement} onChange={(e) => setForm({...form, can_meet_requirement: e.target.checked})} className="rounded" />
                <span className="text-sm text-gray-300">Podemos cumplir</span>
              </label>
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Descripción</label>
              <textarea value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="3" required />
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

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Código</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Cliente</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Título</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Tipo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Estado</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {items.map(item => (
              <tr key={item.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-gray-300">{item.requirement_code}</td>
                <td className="px-6 py-4 text-sm text-white">{item.customer_name}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{item.requirement_title}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{item.requirement_type_display}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs rounded ${
                    item.status === 'fulfilled' ? 'bg-green-500/20 text-green-400' :
                    item.status === 'in_progress' ? 'bg-blue-500/20 text-blue-400' :
                    'bg-yellow-500/20 text-yellow-400'
                  }`}>
                    {item.status_display}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-400 hover:text-blue-300">Editar</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-400 hover:text-red-300">Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="text-center py-8 text-gray-400">No hay requisitos</div>}
      </div>
    </div>
  );
};

export default CustomerRequirementsPage;
