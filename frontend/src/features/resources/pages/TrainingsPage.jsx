import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import Modal from '../../../components/Common/Modal';
import { getTrainings, createTraining, updateTraining, deleteTraining } from '../api/resourcesApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const TrainingsPage = () => {
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    title: '',
    code: '',
    description: '',
    training_type: 'internal',
    start_date: '',
    end_date: '',
    duration_hours: 1
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    if (orgId) {
      loadData();
    } else {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    if (location.pathname.endsWith('/new')) {
      resetForm();
      setShowForm(true);
    }
  }, [location.pathname]);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await getTrainings({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!orgId) {
      alert('Selecciona una organizacion antes de crear registros.');
      return;
    }
    try {
      setSaving(true);
      const payload = { ...form, organization_id: orgId, organization_name: orgName, status: 'planned' };
      if (editingId) {
        await updateTraining(editingId, payload);
      } else {
        await createTraining(payload);
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
      title: item.title,
      code: item.code,
      description: item.description || '',
      training_type: item.training_type,
      start_date: item.start_date,
      end_date: item.end_date,
      duration_hours: item.duration_hours
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar?')) return;
    try {
      await deleteTraining(id);
      loadData();
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const resetForm = () => {
    setForm({
      title: '',
      code: '',
      description: '',
      training_type: 'internal',
      start_date: '',
      end_date: '',
      duration_hours: 1
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
        <h1 className="text-3xl font-bold text-white">Capacitaciones</h1>
        <button
          type="button"
          onClick={openForm}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          Nueva capacitación
        </button>
      </div>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Código</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Título</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Inicio</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Fin</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-gray-300">{i.code}</td>
                <td className="px-6 py-4 text-sm text-white">{i.title}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.start_date}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.end_date}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-400 hover:text-blue-300">Editar</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-400 hover:text-red-300">Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="text-center py-8 text-gray-400">No hay capacitaciones</div>}
      </div>

      <Modal
        title={editingId ? 'Editar capacitación' : 'Nueva capacitación'}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Título *</label>
              <input type="text" value={form.title} onChange={(e) => setForm({...form, title: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Código *</label>
              <input type="text" value={form.code} onChange={(e) => setForm({...form, code: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Tipo</label>
              <select value={form.training_type} onChange={(e) => setForm({...form, training_type: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="internal">Interno</option>
                <option value="external">Externo</option>
                <option value="online">En Línea</option>
                <option value="on_the_job">En el Puesto</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Fecha Inicio *</label>
              <input type="date" value={form.start_date} onChange={(e) => setForm({...form, start_date: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Fecha Fin *</label>
              <input type="date" value={form.end_date} onChange={(e) => setForm({...form, end_date: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Descripción</label>
              <textarea value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="3" required />
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

export default TrainingsPage;
