import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { getExternalProviders, createExternalProvider, updateExternalProvider, deleteExternalProvider, getUsers } from '../api/operationsApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const ExternalProvidersPage = () => {
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';

  const [items, setItems] = useState([]);
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({
    provider_code: '',
    provider_name: '',
    contact_person: '',
    email: '',
    phone: '',
    address: '',
    provision_type: 'product',
    products_services: '',
    evaluation_criteria: '',
    last_evaluation_date: '',
    evaluation_score: '',
    evaluation_notes: '',
    classification: 'conditional',
    performance_rating: '',
    controls_applied: '',
    responsible: user?.id || ''
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (orgId) {
      loadData();
      loadUsers();
    }
  }, [orgId]);

  useEffect(() => {
    if (user?.id) {
      setForm(prev => ({ ...prev, responsible: prev.responsible || user.id }));
    }
  }, [user]);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await getExternalProviders({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const data = await getUsers({ organization_id: orgId });
      setUsers(normalizeList(data));
    } catch (error) {
      console.error('Error loading users:', error);
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
        evaluation_score: form.evaluation_score === '' ? null : Number(form.evaluation_score),
        performance_rating: form.performance_rating === '' ? null : Number(form.performance_rating),
        responsible: form.responsible || null
      };
      if (editingId) {
        await updateExternalProvider(editingId, payload);
      } else {
        await createExternalProvider(payload);
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
      provider_code: item.provider_code,
      provider_name: item.provider_name,
      contact_person: item.contact_person || '',
      email: item.email || '',
      phone: item.phone || '',
      address: item.address || '',
      provision_type: item.provision_type,
      products_services: item.products_services || '',
      evaluation_criteria: item.evaluation_criteria || '',
      last_evaluation_date: item.last_evaluation_date || '',
      evaluation_score: item.evaluation_score ?? '',
      evaluation_notes: item.evaluation_notes || '',
      classification: item.classification,
      performance_rating: item.performance_rating ?? '',
      controls_applied: item.controls_applied || '',
      responsible: item.responsible || ''
    });
    setEditingId(item.id);
  };

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar?')) return;
    try {
      await deleteExternalProvider(id);
      loadData();
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const resetForm = () => {
    setForm({
      provider_code: '',
      provider_name: '',
      contact_person: '',
      email: '',
      phone: '',
      address: '',
      provision_type: 'product',
      products_services: '',
      evaluation_criteria: '',
      last_evaluation_date: '',
      evaluation_score: '',
      evaluation_notes: '',
      classification: 'conditional',
      performance_rating: '',
      controls_applied: '',
      responsible: user?.id || ''
    });
    setEditingId(null);
  };

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Proveedores Externos</h1>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">{editingId ? 'Editar' : 'Nuevo'} Proveedor</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Código *</label>
              <input type="text" value={form.provider_code} onChange={(e) => setForm({...form, provider_code: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Nombre *</label>
              <input type="text" value={form.provider_name} onChange={(e) => setForm({...form, provider_name: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Contacto</label>
              <input type="text" value={form.contact_person} onChange={(e) => setForm({...form, contact_person: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Teléfono</label>
              <input type="text" value={form.phone} onChange={(e) => setForm({...form, phone: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Dirección</label>
              <textarea value={form.address} onChange={(e) => setForm({...form, address: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Tipo de Provisión</label>
              <select value={form.provision_type} onChange={(e) => setForm({...form, provision_type: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="product">Producto</option>
                <option value="service">Servicio</option>
                <option value="process">Proceso Subcontratado</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Productos/Servicios *</label>
              <input type="text" value={form.products_services} onChange={(e) => setForm({...form, products_services: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Criterios de Evaluación *</label>
              <textarea value={form.evaluation_criteria} onChange={(e) => setForm({...form, evaluation_criteria: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Última Evaluación</label>
              <input type="date" value={form.last_evaluation_date} onChange={(e) => setForm({...form, last_evaluation_date: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Puntuación (0-100)</label>
              <input type="number" min="0" max="100" value={form.evaluation_score} onChange={(e) => setForm({...form, evaluation_score: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Clasificación</label>
              <select value={form.classification} onChange={(e) => setForm({...form, classification: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="approved">Aprobado</option>
                <option value="conditional">Condicional</option>
                <option value="not_approved">No Aprobado</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Desempeño (1-5)</label>
              <input type="number" min="1" max="5" value={form.performance_rating} onChange={(e) => setForm({...form, performance_rating: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Controles Aplicados</label>
              <textarea value={form.controls_applied} onChange={(e) => setForm({...form, controls_applied: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Responsable</label>
              <select value={form.responsible} onChange={(e) => setForm({...form, responsible: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="">Sin asignar</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name || u.username || u.email}</option>
                ))}
              </select>
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
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Nombre</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Tipo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Clasificación</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-gray-300">{i.provider_code}</td>
                <td className="px-6 py-4 text-sm text-white">{i.provider_name}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.provision_type_display}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.classification_display}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-400 hover:text-blue-300">Editar</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-400 hover:text-red-300">Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="text-center py-8 text-gray-400">No hay proveedores</div>}
      </div>
    </div>
  );
};

export default ExternalProvidersPage;
