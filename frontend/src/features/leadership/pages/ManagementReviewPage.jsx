// features/leadership/pages/ManagementReviewPage.jsx
// ISO 9001:2015 – Cláusula 9.3 | Revisión por la Dirección
// IA genera briefs y sugiere decisiones → Alta Dirección aprueba

import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import {
  getManagementReviews,
  createManagementReview,
  updateManagementReview,
  deleteManagementReview,
  generateReviewBrief,
  approveReviewBrief,
  approveReviewMinutes,
  getReviewDecisions,
  createReviewDecision,
  approveReviewDecision,
} from '../api/leadershipApi';
import { showConfirm } from '../../../services/dialogs';

const normalizeList = (data) => (Array.isArray(data) ? data : data?.results || []);

const STATUS_COLORS = {
  planned: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  in_progress: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  cancelled: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400',
};

const initialForm = {
  title: '',
  review_type: 'scheduled',
  scheduled_date: '',
  agenda_items: [],
  minutes: '',
};

const ManagementReviewPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';

  const [reviews, setReviews] = useState([]);
  const [selected, setSelected] = useState(null);
  const [decisions, setDecisions] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [decisionForm, setDecisionForm] = useState({
    title: '', description: '', decision_type: 'strategic_decision', rationale: '', due_date: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [showDecisionForm, setShowDecisionForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [error, setError] = useState('');
  const [aiMessage, setAiMessage] = useState('');

  const loadReviews = useCallback(async () => {
    if (!orgId) { setLoading(false); return; }
    try {
      setLoading(true);
      const data = await getManagementReviews({ organization_id: orgId });
      setReviews(normalizeList(data));
    } catch {
      setError(t('modules.leadership.reviewPage.messages.loadError'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  useEffect(() => { loadReviews(); }, [loadReviews]);

  const loadDecisions = useCallback(async (reviewId) => {
    try {
      const data = await getReviewDecisions({ review: reviewId });
      setDecisions(normalizeList(data));
    } catch { /* non-critical */ }
  }, []);

  const handleSelectReview = (review) => {
    setSelected(review);
    loadDecisions(review.id);
    setShowDecisionForm(false);
  };

  const handleSaveReview = async (e) => {
    e.preventDefault();
    if (!orgId) return;
    const payload = { ...form, organization_id: orgId, organization_name: orgName };
    try {
      if (editingId) {
        await updateManagementReview(editingId, payload);
      } else {
        await createManagementReview(payload);
      }
      setShowForm(false);
      setForm(initialForm);
      setEditingId(null);
      await loadReviews();
    } catch (err) {
      const violations = err?.response?.data?.iso_violations;
      setError(violations ? violations.join(' | ') : t('modules.leadership.reviewPage.messages.saveError'));
    }
  };

  const handleDelete = async (id) => {
    if (!await showConfirm(t('modules.leadership.reviewPage.messages.confirmDelete'))) return;
    try {
      await deleteManagementReview(id);
      if (selected?.id === id) setSelected(null);
      await loadReviews();
    } catch { setError(t('modules.leadership.reviewPage.messages.deleteError')); }
  };

  const handleGenerateBrief = async () => {
    if (!selected) return;
    setAiLoading(true);
    setAiMessage('');
    try {
      const result = await generateReviewBrief(selected.id);
      setAiMessage(`✅ ${result.message}`);
      await loadReviews();
      const updated = reviews.find(r => r.id === selected.id) || selected;
      setSelected({ ...updated, ai_brief: result.brief_preview });
    } catch {
      setAiMessage('❌ ' + t('modules.leadership.reviewPage.messages.briefError'));
    } finally {
      setAiLoading(false);
    }
  };

  const handleApproveBrief = async () => {
    if (!selected) return;
    try {
      await approveReviewBrief(selected.id);
      setAiMessage('✅ ' + t('modules.leadership.reviewPage.messages.briefApproved'));
      await loadReviews();
    } catch { setAiMessage('❌ ' + t('modules.leadership.reviewPage.messages.briefApproveError')); }
  };

  const handleApproveMinutes = async () => {
    if (!selected) return;
    try {
      await approveReviewMinutes(selected.id);
      setAiMessage('✅ ' + t('modules.leadership.reviewPage.messages.minutesApproved'));
      await loadReviews();
    } catch { setAiMessage('❌ ' + t('modules.leadership.reviewPage.messages.minutesError')); }
  };

  const handleSaveDecision = async (e) => {
    e.preventDefault();
    if (!selected || !decisionForm.title) return;
    try {
      await createReviewDecision({ ...decisionForm, review: selected.id });
      setShowDecisionForm(false);
      setDecisionForm({ title: '', description: '', decision_type: 'strategic_decision', rationale: '', due_date: '' });
      await loadDecisions(selected.id);
    } catch (err) {
      const violations = err?.response?.data?.iso_violations;
      setError(violations ? violations.join(' | ') : t('modules.leadership.reviewPage.messages.decisionSaveError'));
    }
  };

  const handleApproveDecision = async (decisionId) => {
    try {
      await approveReviewDecision(decisionId);
      await loadDecisions(selected.id);
    } catch (err) {
      setError(err?.response?.data?.error || t('modules.leadership.reviewPage.messages.decisionApproveError'));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div className="p-6 bg-slate-50 dark:bg-slate-900 min-h-screen space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            {t('modules.leadership.reviewPage.title')}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t('modules.leadership.reviewPage.subtitle')}
          </p>
        </div>
        <button
          onClick={() => { setShowForm(true); setEditingId(null); setForm(initialForm); }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors"
        >
          + {t('modules.leadership.reviewPage.buttons.new')}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-red-700 dark:text-red-300 text-sm">
          {error}
          <button onClick={() => setError('')} className="ml-2 text-red-500 hover:text-red-700">✕</button>
        </div>
      )}

      {aiMessage && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3 text-blue-800 dark:text-blue-200 text-sm">
          {aiMessage}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lista de Revisiones */}
        <div className="lg:col-span-1 space-y-3">
          {reviews.length === 0 ? (
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6 text-center text-slate-500 dark:text-slate-400 text-sm">
              {t('modules.leadership.reviewPage.messages.empty')}
            </div>
          ) : (
            reviews.map(review => (
              <div
                key={review.id}
                onClick={() => handleSelectReview(review)}
                className={`cursor-pointer bg-white dark:bg-slate-800 rounded-lg border p-4 transition-all hover:shadow-md ${
                  selected?.id === review.id
                    ? 'border-blue-500 ring-1 ring-blue-500'
                    : 'border-slate-200 dark:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-slate-900 dark:text-white text-sm truncate">{review.title}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      {new Date(review.scheduled_date).toLocaleDateString()}
                    </p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium shrink-0 ${STATUS_COLORS[review.status] || ''}`}>
                    {review.status_display || review.status}
                  </span>
                </div>
                {review.minutes_approved_at && (
                  <p className="text-xs text-green-600 dark:text-green-400 mt-1">✓ Acta firmada</p>
                )}
                <div className="flex gap-2 mt-3 justify-end">
                  <button
                    onClick={(e) => { e.stopPropagation(); setEditingId(review.id); setForm({ title: review.title, review_type: review.review_type, scheduled_date: review.scheduled_date?.slice(0, 16), agenda_items: review.agenda_items || [], minutes: review.minutes || '' }); setShowForm(true); }}
                    className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    {t('common.buttons.edit')}
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(review.id); }}
                    className="text-xs text-red-500 hover:underline"
                  >
                    {t('common.buttons.delete')}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Panel Detalle */}
        <div className="lg:col-span-2">
          {selected ? (
            <div className="space-y-4">
              {/* Header detalle */}
              <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-5">
                <div className="flex items-start justify-between flex-wrap gap-3">
                  <div>
                    <h2 className="text-lg font-bold text-slate-900 dark:text-white">{selected.title}</h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      {new Date(selected.scheduled_date).toLocaleString()} — {selected.review_type_display || selected.review_type}
                    </p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_COLORS[selected.status] || ''}`}>
                    {selected.status_display || selected.status}
                  </span>
                </div>

                {/* Acciones IA */}
                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    onClick={handleGenerateBrief}
                    disabled={aiLoading}
                    className="px-3 py-1.5 bg-purple-600 text-white text-xs rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors flex items-center gap-1"
                  >
                    {aiLoading ? '⏳' : '🤖'} {t('modules.leadership.reviewPage.buttons.generateBrief')}
                  </button>
                  {selected.ai_brief && !selected.ai_brief_approved_at && (
                    <button
                      onClick={handleApproveBrief}
                      className="px-3 py-1.5 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700 transition-colors"
                    >
                      ✅ {t('modules.leadership.reviewPage.buttons.approveBrief')}
                    </button>
                  )}
                  {selected.minutes && !selected.minutes_approved_at && (
                    <button
                      onClick={handleApproveMinutes}
                      className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      📝 {t('modules.leadership.reviewPage.buttons.approveMinutes')}
                    </button>
                  )}
                </div>

                {/* Brief IA */}
                {selected.ai_brief && (
                  <div className="mt-4 p-3 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-700 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-semibold text-purple-700 dark:text-purple-300">
                        🤖 {t('modules.leadership.reviewPage.aiBriefLabel')}
                      </span>
                      {selected.ai_brief_approved_at ? (
                        <span className="text-xs text-green-600 dark:text-green-400">✓ Aprobado por {selected.ai_brief_approved_by_name}</span>
                      ) : (
                        <span className="text-xs text-yellow-600 dark:text-yellow-400">⚠️ Pendiente de aprobación</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-700 dark:text-slate-300 whitespace-pre-line line-clamp-6">
                      {selected.ai_brief}
                    </p>
                  </div>
                )}

                {/* Acta */}
                {selected.minutes && (
                  <div className="mt-4 p-3 bg-slate-50 dark:bg-slate-700/40 border border-slate-200 dark:border-slate-600 rounded-lg">
                    <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      📋 {t('modules.leadership.reviewPage.minutesLabel')}
                      {selected.minutes_approved_at && (
                        <span className="ml-2 text-green-600 dark:text-green-400">✓ Firmada</span>
                      )}
                    </p>
                    <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-4">{selected.minutes}</p>
                  </div>
                )}
              </div>

              {/* Decisiones */}
              <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-900 dark:text-white">
                    {t('modules.leadership.reviewPage.decisionsTitle')}
                  </h3>
                  <button
                    onClick={() => setShowDecisionForm(!showDecisionForm)}
                    className="text-xs px-3 py-1.5 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                  >
                    + {t('modules.leadership.reviewPage.buttons.newDecision')}
                  </button>
                </div>

                {showDecisionForm && (
                  <form onSubmit={handleSaveDecision} className="mb-4 p-4 bg-slate-50 dark:bg-slate-700/40 rounded-lg space-y-3">
                    <input
                      type="text"
                      placeholder={t('modules.leadership.reviewPage.decisionForm.title')}
                      value={decisionForm.title}
                      onChange={e => setDecisionForm(f => ({ ...f, title: e.target.value }))}
                      required
                      className="w-full px-3 py-2 text-sm rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                    <textarea
                      placeholder={t('modules.leadership.reviewPage.decisionForm.description')}
                      value={decisionForm.description}
                      onChange={e => setDecisionForm(f => ({ ...f, description: e.target.value }))}
                      rows={2}
                      className="w-full px-3 py-2 text-sm rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                    <textarea
                      placeholder={t('modules.leadership.reviewPage.decisionForm.rationale')}
                      value={decisionForm.rationale}
                      onChange={e => setDecisionForm(f => ({ ...f, rationale: e.target.value }))}
                      rows={2}
                      className="w-full px-3 py-2 text-sm rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                    <div className="flex gap-3 flex-wrap">
                      <select
                        value={decisionForm.decision_type}
                        onChange={e => setDecisionForm(f => ({ ...f, decision_type: e.target.value }))}
                        className="flex-1 px-3 py-2 text-sm rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                      >
                        {['policy_change','objective_change','resource_allocation','process_change','corrective_action','improvement_opportunity','strategic_decision'].map(v => (
                          <option key={v} value={v}>{v.replace(/_/g, ' ')}</option>
                        ))}
                      </select>
                      <input
                        type="date"
                        value={decisionForm.due_date}
                        onChange={e => setDecisionForm(f => ({ ...f, due_date: e.target.value }))}
                        className="px-3 py-2 text-sm rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                      />
                    </div>
                    <p className="text-xs text-amber-600 dark:text-amber-400">
                      ⚠️ {t('modules.leadership.reviewPage.decisionForm.responsibleNote')}
                    </p>
                    <div className="flex gap-2">
                      <button type="submit" className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                        {t('common.buttons.save')}
                      </button>
                      <button type="button" onClick={() => setShowDecisionForm(false)} className="px-4 py-2 bg-slate-200 dark:bg-slate-600 text-slate-700 dark:text-slate-200 text-sm rounded hover:bg-slate-300">
                        {t('common.buttons.cancel')}
                      </button>
                    </div>
                  </form>
                )}

                <div className="space-y-2">
                  {decisions.length === 0 ? (
                    <p className="text-sm text-slate-500 dark:text-slate-400">{t('modules.leadership.reviewPage.messages.noDecisions')}</p>
                  ) : decisions.map(d => (
                    <div key={d.id} className="flex items-start gap-3 p-3 bg-slate-50 dark:bg-slate-700/40 rounded-lg">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="font-medium text-sm text-slate-900 dark:text-white">{d.title}</p>
                          {d.ai_suggested && (
                            <span className="text-xs px-1.5 py-0.5 bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300 rounded">
                              🤖 IA
                            </span>
                          )}
                          <span className={`text-xs px-1.5 py-0.5 rounded ${
                            d.status === 'approved' || d.status === 'completed'
                              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                              : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
                          }`}>
                            {d.status_display || d.status}
                          </span>
                        </div>
                        {d.description && <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">{d.description}</p>}
                        {d.rationale && <p className="text-xs text-slate-400 dark:text-slate-500 italic mt-1">Por qué: {d.rationale}</p>}
                        {d.due_date && <p className="text-xs text-slate-400 mt-1">Vence: {d.due_date}</p>}
                      </div>
                      {d.status === 'proposed' && (
                        <button
                          onClick={() => handleApproveDecision(d.id)}
                          className="text-xs px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700 shrink-0"
                        >
                          ✓ Aprobar
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-8 text-center text-slate-500 dark:text-slate-400">
              <p className="text-3xl mb-3">📋</p>
              <p className="text-sm">{t('modules.leadership.reviewPage.messages.selectReview')}</p>
            </div>
          )}
        </div>
      </div>

      {/* Modal formulario */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                {editingId ? t('modules.leadership.reviewPage.form.editTitle') : t('modules.leadership.reviewPage.form.newTitle')}
              </h2>
              <form onSubmit={handleSaveReview} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    {t('modules.leadership.reviewPage.form.title')}
                  </label>
                  <input
                    type="text"
                    value={form.title}
                    onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                    required
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      {t('modules.leadership.reviewPage.form.type')}
                    </label>
                    <select
                      value={form.review_type}
                      onChange={e => setForm(f => ({ ...f, review_type: e.target.value }))}
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm"
                    >
                      <option value="scheduled">Programada</option>
                      <option value="extraordinary">Extraordinaria</option>
                      <option value="follow_up">Seguimiento</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      {t('modules.leadership.reviewPage.form.scheduledDate')}
                    </label>
                    <input
                      type="datetime-local"
                      value={form.scheduled_date}
                      onChange={e => setForm(f => ({ ...f, scheduled_date: e.target.value }))}
                      required
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    {t('modules.leadership.reviewPage.form.minutes')}
                  </label>
                  <textarea
                    value={form.minutes}
                    onChange={e => setForm(f => ({ ...f, minutes: e.target.value }))}
                    rows={4}
                    placeholder="Acta de la reunión..."
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm"
                  />
                </div>
                <div className="flex gap-3 pt-2">
                  <button type="submit" className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm">
                    {t('common.buttons.save')}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setShowForm(false); setEditingId(null); }}
                    className="flex-1 px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg hover:bg-slate-300 text-sm"
                  >
                    {t('common.buttons.cancel')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ManagementReviewPage;
