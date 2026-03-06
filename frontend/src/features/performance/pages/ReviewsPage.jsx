import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import Modal from '../../../components/Common/Modal';
import {
  getReviews,
  createReview,
  updateReview,
  deleteReview
} from '../api/performanceApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const ReviewsPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';

  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    review_code: '',
    title: '',
    scheduled_date: '',
    performance_results: '',
    customer_feedback: '',
    status: 'scheduled'
  });
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const statusLabels = useMemo(() => ({
    scheduled: t('modules.performance.reviewsPage.statuses.scheduled'),
    in_progress: t('modules.performance.reviewsPage.statuses.inProgress'),
    completed: t('modules.performance.reviewsPage.statuses.completed'),
    cancelled: t('modules.performance.reviewsPage.statuses.cancelled'),
  }), [t]);

  const loadReviews = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getReviews({ organization_id: orgId });
      setItems(normalizeList(data));
    } catch (error) {
      console.error('Error loading reviews:', error);
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    if (orgId) {
      loadReviews();
    }
  }, [orgId, loadReviews]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      setSaving(true);
      const payload = { ...form, organization_id: orgId, organization_name: orgName };
      if (editingId) {
        await updateReview(editingId, payload);
      } else {
        await createReview(payload);
      }
      resetForm();
      await loadReviews();
      setShowForm(false);
    } catch (error) {
      console.error('Error saving review:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setForm({
      review_code: item.review_code || '',
      title: item.title || '',
      scheduled_date: item.scheduled_date || '',
      performance_results: item.performance_results || '',
      customer_feedback: item.customer_feedback || '',
      status: item.status || 'scheduled'
    });
    setEditingId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm(t('modules.performance.reviewsPage.deleteConfirm'))) return;
    try {
      await deleteReview(id);
      await loadReviews();
    } catch (error) {
      console.error('Error deleting review:', error);
    }
  };

  const resetForm = () => {
    setForm({
      review_code: '',
      title: '',
      scheduled_date: '',
      performance_results: '',
      customer_feedback: '',
      status: 'scheduled'
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
  };

  if (loading) {
    return (
      <div className="flex justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-3xl font-bold text-white">{t('modules.performance.reviewsPage.title')}</h1>
        <button
          type="button"
          onClick={openForm}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          {t('modules.performance.reviewsPage.new')}
        </button>
      </div>

      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.performance.reviewsPage.table.code')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.performance.reviewsPage.table.title')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.performance.reviewsPage.table.scheduled')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('common.forms.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">{t('modules.performance.reviewsPage.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-gray-700/30">
                <td className="px-6 py-4 text-sm text-gray-300">{item.review_code}</td>
                <td className="px-6 py-4 text-sm text-white">{item.title}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{item.scheduled_date}</td>
                <td className="px-6 py-4 text-sm text-gray-300">{statusLabels[item.status] || item.status}</td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-400 hover:text-blue-300">{t('common.buttons.edit')}</button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-400 hover:text-red-300">{t('common.buttons.delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="text-center py-8 text-gray-400">{t('modules.performance.reviewsPage.empty')}</div>}
      </div>

      <Modal
        title={editingId ? t('modules.performance.reviewsPage.edit') : t('modules.performance.reviewsPage.new')}
        isOpen={showForm}
        onClose={closeForm}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('modules.performance.reviewsPage.fields.reviewCode')}</label>
              <input
                type="text"
                value={form.review_code}
                onChange={(event) => setForm({ ...form, review_code: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('modules.performance.reviewsPage.fields.title')}</label>
              <input
                type="text"
                value={form.title}
                onChange={(event) => setForm({ ...form, title: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('modules.performance.reviewsPage.fields.scheduledDate')}</label>
              <input
                type="date"
                value={form.scheduled_date}
                onChange={(event) => setForm({ ...form, scheduled_date: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('common.forms.status')}</label>
              <select
                value={form.status}
                onChange={(event) => setForm({ ...form, status: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              >
                {Object.entries(statusLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('modules.performance.reviewsPage.fields.performanceResults')}</label>
              <textarea
                value={form.performance_results}
                onChange={(event) => setForm({ ...form, performance_results: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="2"
                required
              />
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('modules.performance.reviewsPage.fields.customerFeedback')}</label>
              <textarea
                value={form.customer_feedback}
                onChange={(event) => setForm({ ...form, customer_feedback: event.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="2"
              />
            </div>
          </div>
          <div className="flex space-x-3">
            <button type="submit" disabled={saving} className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
              {saving ? t('common.messages.saving') : editingId ? t('common.buttons.update') : t('common.buttons.create')}
            </button>
            <button type="button" onClick={closeForm} className="px-6 py-2 bg-gray-600 text-white rounded-lg">{t('common.buttons.cancel')}</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ReviewsPage;