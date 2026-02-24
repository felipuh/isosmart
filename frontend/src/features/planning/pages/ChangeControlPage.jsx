import React, { useCallback, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import { getChanges, createChange, updateChange, deleteChange } from '../api/planningApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const ChangeControlPage = () => {
  const { t } = useI18n();
  const { currentOrganization, user } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';
  const location = useLocation();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    change_number: '',
    title: '',
    description: '',
    change_type: 'process',
    reason: 'improvement',
    justification: '',
    urgency: 'medium',
    planned_date: '',
    affected_areas: '',
    impact_assessment: '',
    potential_risks: '',
    mitigation_plan: '',
    status: 'draft'
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getChanges({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    if (orgId) loadData();
  }, [orgId, loadData]);

  useEffect(() => {
    if (location.pathname.endsWith('/new')) {
      resetForm();
      setShowForm(true);
    }
  }, [location.pathname]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = {
        ...form,
        organization_id: orgId,
        organization_name: orgName,
        requested_by: user?.id || null
      };
      if (editingId) {
        await updateChange(editingId, payload);
      } else {
        await createChange(payload);
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
      change_number: item.change_number,
      title: item.title,
      description: item.description || '',
      change_type: item.change_type,
      reason: item.reason,
      justification: item.justification || '',
      urgency: item.urgency,
      planned_date: item.planned_date,
      affected_areas: item.affected_areas || '',
      impact_assessment: item.impact_assessment || '',
      potential_risks: item.potential_risks || '',
      mitigation_plan: item.mitigation_plan || '',
      status: item.status
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar?')) return;
    try {
      await deleteChange(id);
      await loadData();
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const resetForm = () => {
    setForm({
      change_number: '',
      title: '',
      description: '',
      change_type: 'process',
      reason: 'improvement',
      justification: '',
      urgency: 'medium',
      planned_date: '',
      affected_areas: '',
      impact_assessment: '',
      potential_risks: '',
      mitigation_plan: '',
      status: 'draft'
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
        <h1 className="text-3xl font-bold text-white">{t('literals.Control de Cambios')}</h1>
        <button
          type="button"
          onClick={openForm}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          Nuevo cambio
        </button>
      </div>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Número</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Título</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Tipo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Urgencia</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {items.map(i => (
              <tr key={i.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-gray-300">{i.change_number}</td>
                <td className="px-6 py-4 text-sm text-white">{i.title}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.change_type_display}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.urgency_display}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{i.status_display}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(i)} className="text-blue-400 hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(i.id)} className="text-red-400 hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="text-center py-8 text-gray-400">No hay cambios</div>}
      </div>

      <Modal
        title={editingId ? 'Editar cambio' : 'Nuevo cambio'}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Número *</label>
              <input type="text" value={form.change_number} onChange={(e) => setForm({...form, change_number: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Título *</label>
              <input type="text" value={form.title} onChange={(e) => setForm({...form, title: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('common.forms.description')}</label>
              <textarea value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Tipo</label>
              <select value={form.change_type} onChange={(e) => setForm({...form, change_type: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="process">{t('literals.Proceso')}</option>
                <option value="procedure">{t('literals.Procedimiento')}</option>
                <option value="resource">{t('literals.Recurso')}</option>
                <option value="technology">{t('literals.Tecnología')}</option>
                <option value="structure">{t('literals.Estructura Organizacional')}</option>
                <option value="scope">{t('literals.Alcance del SGC')}</option>
                <option value="policy">{t('literals.Política')}</option>
                <option value="other">{t('literals.Otro')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Razón</label>
              <select value={form.reason} onChange={(e) => setForm({...form, reason: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="improvement">{t('literals.Mejora')}</option>
                <option value="correction">{t('literals.Corrección')}</option>
                <option value="compliance">{t('literals.Cumplimiento')}</option>
                <option value="risk_mitigation">{t('literals.Mitigación de Riesgo')}</option>
                <option value="opportunity">{t('literals.Oportunidad')}</option>
                <option value="external_requirement">{t('literals.Requisito Externo')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Urgencia</label>
              <select value={form.urgency} onChange={(e) => setForm({...form, urgency: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="low">{t('literals.Baja')}</option>
                <option value="medium">{t('literals.Media')}</option>
                <option value="high">{t('literals.Alta')}</option>
                <option value="critical">{t('literals.Crítica')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Fecha Planificada *</label>
              <input type="date" value={form.planned_date} onChange={(e) => setForm({...form, planned_date: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('common.forms.status')}</label>
              <select value={form.status} onChange={(e) => setForm({...form, status: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                <option value="draft">{t('literals.Borrador')}</option>
                <option value="submitted">{t('literals.Enviado')}</option>
                <option value="under_review">{t('literals.En Revisión')}</option>
                <option value="approved">{t('literals.Aprobado')}</option>
                <option value="rejected">{t('literals.Rechazado')}</option>
                <option value="in_implementation">{t('literals.En Implementación')}</option>
                <option value="implemented">{t('literals.Implementado')}</option>
                <option value="verified">{t('literals.Verificado')}</option>
                <option value="closed">{t('literals.Cerrado')}</option>
              </select>
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Justificación *</label>
              <textarea value={form.justification} onChange={(e) => setForm({...form, justification: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Áreas Afectadas *</label>
              <textarea value={form.affected_areas} onChange={(e) => setForm({...form, affected_areas: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Evaluación de Impacto *</label>
              <textarea value={form.impact_assessment} onChange={(e) => setForm({...form, impact_assessment: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" required />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Riesgos Potenciales</label>
              <textarea value={form.potential_risks} onChange={(e) => setForm({...form, potential_risks: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">Plan de Mitigación</label>
              <textarea value={form.mitigation_plan} onChange={(e) => setForm({...form, mitigation_plan: e.target.value})} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" rows="2" />
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

export default ChangeControlPage;
