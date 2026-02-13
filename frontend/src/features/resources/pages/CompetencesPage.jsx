import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import Modal from '../../../components/Common/Modal';
import { getCompetences, createCompetence, updateCompetence, deleteCompetence, getUsers } from '../api/resourcesApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const CompetencesPage = () => {
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({
    user: user?.id || '',
    competence_name: '',
    position: '',
    description: '',
    required_level: 'intermediate',
    current_level: 'basic',
    acquisition_method: 'training'
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    if (orgId) {
      loadData();
      loadUsers();
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

  useEffect(() => {
    if (user?.id) {
      setForm(prev => ({ ...prev, user: prev.user || user.id }));
    }
  }, [user]);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await getCompetences({ organization_id: orgId });
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
    if (!orgId) {
      alert('Selecciona una organizacion antes de crear registros.');
      return;
    }
    try {
      setSaving(true);
      const payload = { ...form, organization_id: orgId, organization_name: orgName };
      if (editingId) {
        await updateCompetence(editingId, payload);
      } else {
        await createCompetence(payload);
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
      user: item.user,
      competence_name: item.competence_name,
      position: item.position,
      description: item.description || '',
      required_level: item.required_level,
      current_level: item.current_level,
      acquisition_method: item.acquisition_method
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar?')) return;
    try {
      await deleteCompetence(id);
      loadData();
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const resetForm = () => {
    setForm({
      user: user?.id || '',
      competence_name: '',
      position: '',
      description: '',
      required_level: 'intermediate',
      current_level: 'basic',
      acquisition_method: 'training'
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
        <h1 className="text-3xl font-bold text-white">Competencias</h1>
        <button
          type="button"
          onClick={openForm}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          Nueva competencia
        </button>
      </div>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Usuario</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Competencia</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Puesto</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Requerido</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Actual</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-gray-300">{i.user_name || i.user}</td>
                <td className="px-6 py-4 text-sm text-white">{i.competence_name}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.position}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.required_level_display}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.current_level_display}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-400 hover:text-blue-300">Editar</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-400 hover:text-red-300">Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="text-center py-8 text-gray-400">No hay competencias</div>}
      </div>

      <Modal
        title={editingId ? 'Editar competencia' : 'Nueva competencia'}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Usuario *</label>
              <select value={form.user} onChange={(e) => setForm({...form, user: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required>
                <option value="">Seleccionar</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name || u.username || u.email}</option>
                ))}
                {users.length === 0 && user?.id && (
                  <option value={user.id}>{user.full_name || user.username || user.email}</option>
                )}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Competencia *</label>
              <input type="text" value={form.competence_name} onChange={(e) => setForm({...form, competence_name: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Puesto *</label>
              <input type="text" value={form.position} onChange={(e) => setForm({...form, position: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Nivel Requerido</label>
              <select value={form.required_level} onChange={(e) => setForm({...form, required_level: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="basic">Básico</option>
                <option value="intermediate">Intermedio</option>
                <option value="advanced">Avanzado</option>
                <option value="expert">Experto</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Nivel Actual</label>
              <select value={form.current_level} onChange={(e) => setForm({...form, current_level: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="basic">Básico</option>
                <option value="intermediate">Intermedio</option>
                <option value="advanced">Avanzado</option>
                <option value="expert">Experto</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Método de Adquisición</label>
              <select value={form.acquisition_method} onChange={(e) => setForm({...form, acquisition_method: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="education">Educación Formal</option>
                <option value="training">Capacitación</option>
                <option value="experience">Experiencia Laboral</option>
                <option value="certification">Certificación</option>
              </select>
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

export default CompetencesPage;
