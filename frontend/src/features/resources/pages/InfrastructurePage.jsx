import React, { useCallback, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import { getInfrastructure, createInfrastructure, updateInfrastructure, deleteInfrastructure } from '../api/resourcesApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const InfrastructurePage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    infrastructure_type: 'building',
    name: '',
    code: '',
    description: '',
    location: '',
    status: 'operational'
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getInfrastructure({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    if (orgId) {
      loadData();
    } else {
      setLoading(false);
    }
  }, [orgId, loadData]);

  useEffect(() => {
    if (location.pathname.endsWith('/new')) {
      resetForm();
      setShowForm(true);
    }
  }, [location.pathname]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!orgId) {
      alert(t('modules.resources.infrastructurePage.messages.selectOrganization'));
      return;
    }
    try {
      setSaving(true);
      const payload = { ...form, organization_id: orgId, organization_name: orgName };
      if (editingId) {
        await updateInfrastructure(editingId, payload);
      } else {
        await createInfrastructure(payload);
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
      infrastructure_type: item.infrastructure_type,
      name: item.name,
      code: item.code,
      description: item.description || '',
      location: item.location || '',
      status: item.status
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm(t('modules.resources.infrastructurePage.messages.confirmDelete'))) return;
    try {
      await deleteInfrastructure(id);
      await loadData();
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const resetForm = () => {
    setForm({
      infrastructure_type: 'building',
      name: '',
      code: '',
      description: '',
      location: '',
      status: 'operational'
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
        <h1 className="text-3xl font-bold text-white">{t('modules.resources.infrastructurePage.title')}</h1>
        <button
          type="button"
          onClick={openForm}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          {t('modules.resources.infrastructurePage.buttons.new')}
        </button>
      </div>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.resources.infrastructurePage.table.code')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('common.forms.name')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.resources.infrastructurePage.table.type')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.resources.infrastructurePage.table.location')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.resources.infrastructurePage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-gray-300">{i.code}</td>
                <td className="px-6 py-4 text-sm text-white">{i.name}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.infrastructure_type_display}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.location}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-400 hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-400 hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="text-center py-8 text-gray-400">{t('modules.resources.infrastructurePage.messages.empty')}</div>}
      </div>

      <Modal
        title={editingId ? t('modules.resources.infrastructurePage.modal.editTitle') : t('modules.resources.infrastructurePage.modal.newTitle')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('modules.resources.infrastructurePage.form.type')}</label>
              <select value={form.infrastructure_type} onChange={(e) => setForm({...form, infrastructure_type: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required>
                <option value="building">{t('modules.resources.infrastructurePage.options.type.building')}</option>
                <option value="equipment">{t('modules.resources.infrastructurePage.options.type.equipment')}</option>
                <option value="software">{t('modules.resources.infrastructurePage.options.type.software')}</option>
                <option value="transport">{t('modules.resources.infrastructurePage.options.type.transport')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('modules.resources.infrastructurePage.form.nameRequired')}</label>
              <input type="text" value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('modules.resources.infrastructurePage.form.codeRequired')}</label>
              <input type="text" value={form.code} onChange={(e) => setForm({...form, code: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('modules.resources.infrastructurePage.form.location')}</label>
              <input type="text" value={form.location} onChange={(e) => setForm({...form, location: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('common.forms.description')}</label>
              <textarea value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="3" />
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

export default InfrastructurePage;