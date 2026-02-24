import React, { useCallback, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import { getProductReleases, createProductRelease, updateProductRelease, deleteProductRelease, getUsers } from '../api/operationsApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const ProductReleasesPage = () => {
  const { t } = useI18n();
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({
    release_code: '',
    product_service_name: '',
    batch_lot_number: '',
    release_date: '',
    quantity_released: '',
    unit: '',
    verification_performed: false,
    verification_results: '',
    acceptance_criteria_met: false,
    criteria_details: '',
    authorized_by: user?.id || '',
    status: 'pending',
    customer_name: '',
    delivery_date: '',
    notes: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const resetForm = useCallback(() => {
    setForm({
      release_code: '',
      product_service_name: '',
      batch_lot_number: '',
      release_date: '',
      quantity_released: '',
      unit: '',
      verification_performed: false,
      verification_results: '',
      acceptance_criteria_met: false,
      criteria_details: '',
      authorized_by: user?.id || '',
      status: 'pending',
      customer_name: '',
      delivery_date: '',
      notes: ''
    });
    setEditingId(null);
  }, [user?.id]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getProductReleases({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  const loadUsers = useCallback(async () => {
    try {
      const data = await getUsers({ organization_id: orgId });
      setUsers(normalizeList(data));
    } catch (error) {
      console.error('Error loading users:', error);
    }
  }, [orgId]);

  useEffect(() => {
    if (orgId) {
      loadData();
      loadUsers();
    }
  }, [orgId, loadData, loadUsers]);

  useEffect(() => {
    if (location.pathname.endsWith('/new')) {
      resetForm();
      setShowForm(true);
    }
  }, [location.pathname, resetForm]);

  useEffect(() => {
    if (user?.id) {
      setForm(prev => ({ ...prev, authorized_by: prev.authorized_by || user.id }));
    }
  }, [user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = {
        ...form,
        organization_id: orgId,
        organization_name: orgName,
        quantity_released: form.quantity_released === '' ? null : Number(form.quantity_released),
        authorized_by: form.authorized_by || null
      };
      if (editingId) {
        await updateProductRelease(editingId, payload);
      } else {
        await createProductRelease(payload);
      }
      resetForm();
      await loadData();
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
      release_code: item.release_code,
      product_service_name: item.product_service_name,
      batch_lot_number: item.batch_lot_number || '',
      release_date: item.release_date,
      quantity_released: item.quantity_released ?? '',
      unit: item.unit || '',
      verification_performed: item.verification_performed || false,
      verification_results: item.verification_results || '',
      acceptance_criteria_met: item.acceptance_criteria_met || false,
      criteria_details: item.criteria_details || '',
      authorized_by: item.authorized_by || '',
      status: item.status,
      customer_name: item.customer_name || '',
      delivery_date: item.delivery_date || '',
      notes: item.notes || ''
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar?')) return;
    try {
      await deleteProductRelease(id);
      await loadData();
    } catch (error) {
      console.error('Error:', error);
    }
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
        <h1 className="text-3xl font-bold text-white">Liberación de Productos</h1>
        <button
          type="button"
          onClick={openForm}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          Nueva liberación
        </button>
      </div>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Código</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Producto/Servicio</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('common.forms.date')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-gray-300">{i.release_code}</td>
                <td className="px-6 py-4 text-sm text-white">{i.product_service_name}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.release_date}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.status_display}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-400 hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-400 hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="text-center py-8 text-gray-400">No hay liberaciones</div>}
      </div>

      <Modal
        title={editingId ? 'Editar liberación' : 'Nueva liberación'}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Código *</label>
              <input type="text" value={form.release_code} onChange={(e) => setForm({...form, release_code: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Producto/Servicio *</label>
              <input type="text" value={form.product_service_name} onChange={(e) => setForm({...form, product_service_name: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Lote/Batch</label>
              <input type="text" value={form.batch_lot_number} onChange={(e) => setForm({...form, batch_lot_number: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Fecha *</label>
              <input type="date" value={form.release_date} onChange={(e) => setForm({...form, release_date: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Cantidad *</label>
              <input type="number" value={form.quantity_released} onChange={(e) => setForm({...form, quantity_released: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Unidad</label>
              <input type="text" value={form.unit} onChange={(e) => setForm({...form, unit: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div className="flex items-center">
              <label className="flex items-center space-x-2">
                <input type="checkbox" checked={form.verification_performed} onChange={(e) => setForm({...form, verification_performed: e.target.checked})} className="rounded" />
                <span className="text-sm text-gray-300">Verificación Realizada</span>
              </label>
            </div>
            <div className="flex items-center">
              <label className="flex items-center space-x-2">
                <input type="checkbox" checked={form.acceptance_criteria_met} onChange={(e) => setForm({...form, acceptance_criteria_met: e.target.checked})} className="rounded" />
                <span className="text-sm text-gray-300">Criterios Cumplidos</span>
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Autorizado por</label>
              <select value={form.authorized_by} onChange={(e) => setForm({...form, authorized_by: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="">{t('literals.Sin asignar')}</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name || u.username || u.email}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('common.forms.status')}</label>
              <select value={form.status} onChange={(e) => setForm({...form, status: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="pending">{t('literals.Pendiente')}</option>
                <option value="approved">{t('literals.Aprobado')}</option>
                <option value="released">{t('literals.Liberado')}</option>
                <option value="rejected">{t('literals.Rechazado')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Cliente</label>
              <input type="text" value={form.customer_name} onChange={(e) => setForm({...form, customer_name: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Fecha de Entrega</label>
              <input type="date" value={form.delivery_date} onChange={(e) => setForm({...form, delivery_date: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Resultados de Verificación</label>
              <textarea value={form.verification_results} onChange={(e) => setForm({...form, verification_results: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Detalles de Criterios</label>
              <textarea value={form.criteria_details} onChange={(e) => setForm({...form, criteria_details: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Notas</label>
              <textarea value={form.notes} onChange={(e) => setForm({...form, notes: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" />
            </div>
          </div>
          <div className="flex space-x-3">
            <button type="submit" disabled={saving} className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
              {saving ? t('common.messages.saving') : editingId ? t('common.buttons.update') : t('common.buttons.create')}
            </button>
            {editingId && <button type="button" onClick={closeForm} className="px-6 py-2 bg-gray-600 text-white rounded-lg">{t('common.buttons.cancel')}</button>}
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ProductReleasesPage;
