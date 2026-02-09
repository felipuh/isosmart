import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { getResources, createResource, updateResource, deleteResource } from '../api/resourcesApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const ResourcesPage = () => {
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';

  const [resources, setResources] = useState([]);
  const [form, setForm] = useState({
    resource_type: 'human',
    name: '',
    code: '',
    description: '',
    quantity: 1,
    unit: '',
    location: '',
    status: 'available'
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (orgId) loadResources();
  }, [orgId]);

  const loadResources = async () => {
    try {
      setLoading(true);
      const data = await getResources({ organization_id: orgId });
      setResources(normalizeList(data));
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
      const payload = { ...form, organization_id: orgId, organization_name: orgName };
      if (editingId) {
        await updateResource(editingId, payload);
      } else {
        await createResource(payload);
      }
      resetForm();
      loadResources();
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (resource) => {
    setForm({
      resource_type: resource.resource_type,
      name: resource.name,
      code: resource.code,
      description: resource.description || '',
      quantity: resource.quantity,
      unit: resource.unit || '',
      location: resource.location || '',
      status: resource.status
    });
    setEditingId(resource.id);
  };

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar?')) return;
    try {
      await deleteResource(id);
      loadResources();
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const resetForm = () => {
    setForm({
      resource_type: 'human',
      name: '',
      code: '',
      description: '',
      quantity: 1,
      unit: '',
      location: '',
      status: 'available'
    });
    setEditingId(null);
  };

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Recursos</h1>
      
      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">{editingId ? 'Editar' : 'Nuevo'} Recurso</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Tipo</label>
              <select value={form.resource_type} onChange={(e) => setForm({...form, resource_type: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required>
                <option value="human">Recurso Humano</option>
                <option value="infrastructure">Infraestructura</option>
                <option value="technology">Tecnología</option>
                <option value="material">Material</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Nombre *</label>
              <input type="text" value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Código *</label>
              <input type="text" value={form.code} onChange={(e) => setForm({...form, code: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
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
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {resources.map(r => (
              <tr key={r.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-gray-300">{r.code}</td>
                <td className="px-6 py-4 text-sm text-white">{r.name}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{r.resource_type_display}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(r)} className="text-blue-400 hover:text-blue-300">Editar</button>
                  <button onClick={() => handleDelete(r.id)} className="text-red-400 hover:text-red-300">Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {resources.length === 0 && <div className="text-center py-8 text-gray-400">No hay recursos</div>}
      </div>
    </div>
  );
};

export default ResourcesPage;
