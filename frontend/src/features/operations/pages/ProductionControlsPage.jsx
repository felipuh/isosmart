import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import Modal from '../../../components/Common/Modal';
import { getProductionControls, createProductionControl, updateProductionControl, deleteProductionControl, getUsers } from '../api/operationsApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const ProductionControlsPage = () => {
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({
    control_code: '',
    product_service_name: '',
    description: '',
    control_type: 'production',
    control_method: '',
    requires_traceability: false,
    traceability_method: '',
    handles_customer_property: false,
    customer_property_controls: '',
    preservation_requirements: '',
    post_delivery_activities: '',
    change_control_process: '',
    responsible: user?.id || ''
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    if (orgId) {
      loadData();
      loadUsers();
    }
  }, [orgId]);

  useEffect(() => {
    if (location.pathname.endsWith('/new')) {
      resetForm();
      setShowForm(true);
    }
  }, [location.pathname]);

  useEffect(() => {
    if (user?.id) {
      setForm(prev => ({ ...prev, responsible: prev.responsible || user.id }));
    }
  }, [user]);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await getProductionControls({ organization_id: orgId });
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
        responsible: form.responsible || null
      };
      if (editingId) {
        await updateProductionControl(editingId, payload);
      } else {
        await createProductionControl(payload);
      }
      resetForm();
      loadData();
      setShowForm(false);
      if (location.pathname.endsWith('/new')) {
        navigate(location.pathname.replace(/\/new$/, ''), { replace: true });
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setForm({
      control_code: item.control_code,
      product_service_name: item.product_service_name,
      description: item.description || '',
      control_type: item.control_type,
      control_method: item.control_method || '',
      requires_traceability: item.requires_traceability || false,
      traceability_method: item.traceability_method || '',
      handles_customer_property: item.handles_customer_property || false,
      customer_property_controls: item.customer_property_controls || '',
      preservation_requirements: item.preservation_requirements || '',
      post_delivery_activities: item.post_delivery_activities || '',
      change_control_process: item.change_control_process || '',
      responsible: item.responsible || ''
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar?')) return;
    try {
      await deleteProductionControl(id);
      loadData();
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const resetForm = () => {
    setForm({
      control_code: '',
      product_service_name: '',
      description: '',
      control_type: 'production',
      control_method: '',
      requires_traceability: false,
      traceability_method: '',
      handles_customer_property: false,
      customer_property_controls: '',
      preservation_requirements: '',
      post_delivery_activities: '',
      change_control_process: '',
      responsible: user?.id || ''
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
    if (location.pathname.endsWith('/new')) {
      navigate(location.pathname.replace(/\/new$/, ''), { replace: true });
    }
  };

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-3xl font-bold text-white">Control de Producción</h1>
        <button
          type="button"
          onClick={openForm}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          Nuevo control
        </button>
      </div>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Código</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Producto/Servicio</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Tipo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-gray-300">{i.control_code}</td>
                <td className="px-6 py-4 text-sm text-white">{i.product_service_name}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.control_type_display}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-400 hover:text-blue-300">Editar</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-400 hover:text-red-300">Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="text-center py-8 text-gray-400">No hay controles</div>}
      </div>

      <Modal
        title={editingId ? 'Editar control' : 'Nuevo control'}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Código *</label>
              <input type="text" value={form.control_code} onChange={(e) => setForm({...form, control_code: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Producto/Servicio *</label>
              <input type="text" value={form.product_service_name} onChange={(e) => setForm({...form, product_service_name: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Tipo</label>
              <select value={form.control_type} onChange={(e) => setForm({...form, control_type: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="production">Producción</option>
                <option value="service_delivery">Prestación de Servicio</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Método de Control *</label>
              <input type="text" value={form.control_method} onChange={(e) => setForm({...form, control_method: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Descripción</label>
              <textarea value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" required />
            </div>
            <div className="flex items-center">
              <label className="flex items-center space-x-2">
                <input type="checkbox" checked={form.requires_traceability} onChange={(e) => setForm({...form, requires_traceability: e.target.checked})} className="rounded" />
                <span className="text-sm text-gray-300">Requiere Trazabilidad</span>
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Método de Trazabilidad</label>
              <input type="text" value={form.traceability_method} onChange={(e) => setForm({...form, traceability_method: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div className="flex items-center">
              <label className="flex items-center space-x-2">
                <input type="checkbox" checked={form.handles_customer_property} onChange={(e) => setForm({...form, handles_customer_property: e.target.checked})} className="rounded" />
                <span className="text-sm text-gray-300">Maneja Propiedad del Cliente</span>
              </label>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Controles de Propiedad</label>
              <input type="text" value={form.customer_property_controls} onChange={(e) => setForm({...form, customer_property_controls: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Requisitos de Preservación</label>
              <textarea value={form.preservation_requirements} onChange={(e) => setForm({...form, preservation_requirements: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Actividades Post-Entrega</label>
              <textarea value={form.post_delivery_activities} onChange={(e) => setForm({...form, post_delivery_activities: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Control de Cambios</label>
              <textarea value={form.change_control_process} onChange={(e) => setForm({...form, change_control_process: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" />
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
            {editingId && <button type="button" onClick={closeForm} className="px-6 py-2 bg-gray-600 text-white rounded-lg">Cancelar</button>}
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ProductionControlsPage;
