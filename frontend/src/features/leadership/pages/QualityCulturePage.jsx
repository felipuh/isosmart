// features/leadership/pages/QualityCulturePage.jsx
// Cultura de Calidad y Ética — ISO 9001:2026
// Micro-encuestas anónimas | Solo resultados agregados | Privacidad por diseño

import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import {
  getCultureSurveys,
  createCultureSurvey,
  submitSurveyResponse,
  getSurveyAggregateResults,
} from '../api/leadershipApi';

const normalizeList = (data) => (Array.isArray(data) ? data : data?.results || []);

const STATUS_COLORS = {
  draft: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
  active: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  closed: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  archived: 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400',
};

const QualityCulturePage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const orgName = currentOrganization?.name || '';

  const [surveys, setSurveys] = useState([]);
  const [selected, setSelected] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showRespondForm, setShowRespondForm] = useState(false);
  const [responseAnswers, setResponseAnswers] = useState({});
  const [submitMessage, setSubmitMessage] = useState('');

  const [surveyForm, setSurveyForm] = useState({
    title: '',
    description: '',
    start_date: '',
    end_date: '',
    min_responses_for_analysis: 5,
    questions: [{ id: '1', text: '', type: 'scale', options: [] }],
  });

  const loadSurveys = useCallback(async () => {
    if (!orgId) { setLoading(false); return; }
    try {
      setLoading(true);
      const data = await getCultureSurveys({ organization_id: orgId });
      setSurveys(normalizeList(data));
    } catch {
      setError(t('modules.leadership.culturePage.messages.loadError'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  useEffect(() => { loadSurveys(); }, [loadSurveys]);

  const handleSelectSurvey = async (survey) => {
    setSelected(survey);
    setResults(null);
    setShowRespondForm(false);
    setSubmitMessage('');
    if (survey.has_enough_responses || survey.response_count >= survey.min_responses_for_analysis) {
      try {
        const r = await getSurveyAggregateResults(survey.id);
        setResults(r);
      } catch { /* no results yet */ }
    }
  };

  const handleCreateSurvey = async (e) => {
    e.preventDefault();
    if (!orgId) return;
    try {
      await createCultureSurvey({
        ...surveyForm,
        organization_id: orgId,
        organization_name: orgName,
      });
      setShowCreateForm(false);
      setSurveyForm({ title: '', description: '', start_date: '', end_date: '', min_responses_for_analysis: 5, questions: [{ id: '1', text: '', type: 'scale', options: [] }] });
      await loadSurveys();
    } catch { setError(t('modules.leadership.culturePage.messages.createError')); }
  };

  const addQuestion = () => {
    setSurveyForm(f => ({
      ...f,
      questions: [...f.questions, { id: String(f.questions.length + 1), text: '', type: 'scale', options: [] }]
    }));
  };

  const updateQuestion = (idx, field, value) => {
    setSurveyForm(f => {
      const qs = [...f.questions];
      qs[idx] = { ...qs[idx], [field]: value };
      return { ...f, questions: qs };
    });
  };

  const handleSubmitResponse = async (e) => {
    e.preventDefault();
    if (!selected) return;
    try {
      await submitSurveyResponse({
        survey: selected.id,
        responses: responseAnswers,
      });
      setSubmitMessage(t('modules.leadership.culturePage.messages.responseSubmitted'));
      setShowRespondForm(false);
      setResponseAnswers({});
      await loadSurveys();
    } catch (err) {
      setError(err?.response?.data?.error || t('modules.leadership.culturePage.messages.responseError'));
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
    </div>
  );

  return (
    <div className="p-6 bg-slate-50 dark:bg-slate-900 min-h-screen space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            {t('modules.leadership.culturePage.title')}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t('modules.leadership.culturePage.subtitle')}
          </p>
        </div>
        <button onClick={() => setShowCreateForm(true)} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
          + {t('modules.leadership.culturePage.buttons.newSurvey')}
        </button>
      </div>

      {/* Aviso privacidad */}
      <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-700 rounded-lg p-4 flex gap-3">
        <span className="text-2xl">🔒</span>
        <div>
          <p className="text-sm font-semibold text-purple-800 dark:text-purple-200">
            {t('modules.leadership.culturePage.privacyTitle')}
          </p>
          <p className="text-xs text-purple-700 dark:text-purple-300 mt-1">
            {t('modules.leadership.culturePage.privacyDesc')}
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-red-700 dark:text-red-300 text-sm">
          {error} <button onClick={() => setError('')} className="ml-2">✕</button>
        </div>
      )}

      {submitMessage && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-3 text-green-700 dark:text-green-300 text-sm">
          {submitMessage}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lista encuestas */}
        <div className="lg:col-span-1 space-y-3">
          {surveys.length === 0 ? (
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6 text-center text-slate-500 dark:text-slate-400 text-sm">
              {t('modules.leadership.culturePage.messages.empty')}
            </div>
          ) : surveys.map(survey => (
            <div
              key={survey.id}
              onClick={() => handleSelectSurvey(survey)}
              className={`cursor-pointer bg-white dark:bg-slate-800 rounded-lg border p-4 transition-all hover:shadow-md ${
                selected?.id === survey.id
                  ? 'border-blue-500 ring-1 ring-blue-500'
                  : 'border-slate-200 dark:border-slate-700'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="font-medium text-sm text-slate-900 dark:text-white">{survey.title}</p>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[survey.status] || ''}`}>
                  {survey.status_display || survey.status}
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                {survey.start_date} — {survey.end_date}
              </p>
              <div className="flex items-center gap-2 mt-2">
                <div className="flex-1 bg-slate-100 dark:bg-slate-700 rounded-full h-1.5">
                  <div
                    className="bg-blue-500 h-1.5 rounded-full"
                    style={{ width: `${Math.min(100, (survey.response_count / (survey.min_responses_for_analysis || 5)) * 100)}%` }}
                  />
                </div>
                <span className="text-xs text-slate-400 shrink-0">
                  {survey.response_count}/{survey.min_responses_for_analysis}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Panel detalle */}
        <div className="lg:col-span-2">
          {selected ? (
            <div className="space-y-4">
              <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-5">
                <div className="flex items-start justify-between flex-wrap gap-3 mb-4">
                  <div>
                    <h2 className="text-lg font-bold text-slate-900 dark:text-white">{selected.title}</h2>
                    {selected.description && <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{selected.description}</p>}
                  </div>
                  {selected.status === 'active' && (
                    <button
                      onClick={() => setShowRespondForm(!showRespondForm)}
                      className="px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700"
                    >
                      📝 {t('modules.leadership.culturePage.buttons.respond')}
                    </button>
                  )}
                </div>

                {/* Formulario de respuesta anónima */}
                {showRespondForm && (
                  <form onSubmit={handleSubmitResponse} className="space-y-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg mb-4">
                    <p className="text-xs text-green-700 dark:text-green-300 font-medium">
                      🔒 {t('modules.leadership.culturePage.responseAnonymousNote')}
                    </p>
                    {(selected.questions || []).map(q => (
                      <div key={q.id}>
                        <label className="block text-sm text-slate-700 dark:text-slate-300 mb-1">{q.text}</label>
                        {q.type === 'scale' ? (
                          <div className="flex gap-2">
                            {[1,2,3,4,5].map(v => (
                              <button
                                key={v}
                                type="button"
                                onClick={() => setResponseAnswers(r => ({ ...r, [q.id]: v }))}
                                className={`w-9 h-9 rounded-full text-sm font-medium transition-colors ${
                                  responseAnswers[q.id] === v
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-slate-200 dark:bg-slate-600 text-slate-700 dark:text-slate-200'
                                }`}
                              >
                                {v}
                              </button>
                            ))}
                          </div>
                        ) : q.type === 'choice' ? (
                          <select
                            value={responseAnswers[q.id] || ''}
                            onChange={e => setResponseAnswers(r => ({ ...r, [q.id]: e.target.value }))}
                            className="w-full px-3 py-2 text-sm rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800"
                          >
                            <option value="">Seleccionar...</option>
                            {(q.options || []).map(opt => <option key={opt} value={opt}>{opt}</option>)}
                          </select>
                        ) : (
                          <textarea
                            value={responseAnswers[q.id] || ''}
                            onChange={e => setResponseAnswers(r => ({ ...r, [q.id]: e.target.value }))}
                            rows={2}
                            className="w-full px-3 py-2 text-sm rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800"
                          />
                        )}
                      </div>
                    ))}
                    <div className="flex gap-3">
                      <button type="submit" className="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700">
                        {t('common.buttons.submit')}
                      </button>
                      <button type="button" onClick={() => setShowRespondForm(false)} className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-sm rounded-lg">
                        {t('common.buttons.cancel')}
                      </button>
                    </div>
                  </form>
                )}

                {/* Resultados agregados */}
                {results ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                        📊 {t('modules.leadership.culturePage.aggregatedResults')}
                      </span>
                      <span className="text-xs text-slate-500">({results.total_responses} respuestas)</span>
                    </div>
                    {Object.entries(results.aggregated_results || {}).map(([qid, agg]) => (
                      <div key={qid} className="p-3 bg-slate-50 dark:bg-slate-700/40 rounded-lg">
                        <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{agg.question}</p>
                        {agg.type === 'scale' ? (
                          <div className="flex items-center gap-3">
                            <div className="flex-1 bg-slate-200 dark:bg-slate-600 rounded-full h-3">
                              <div
                                className="bg-blue-500 h-3 rounded-full transition-all"
                                style={{ width: `${(agg.avg / 5) * 100}%` }}
                              />
                            </div>
                            <span className="text-sm font-bold text-blue-600 dark:text-blue-400 w-10">{agg.avg}/5</span>
                            <span className="text-xs text-slate-400">{agg.count} resp.</span>
                          </div>
                        ) : (
                          <div className="space-y-1">
                            {Object.entries(agg.distribution || {}).map(([opt, count]) => (
                              <div key={opt} className="flex items-center gap-2">
                                <span className="text-xs text-slate-500 w-20 truncate">{opt}</span>
                                <div className="flex-1 bg-slate-200 dark:bg-slate-600 rounded-full h-2">
                                  <div className="bg-green-500 h-2 rounded-full" style={{ width: `${(count / agg.count) * 100}%` }} />
                                </div>
                                <span className="text-xs text-slate-400 w-6">{count}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6 text-slate-500 dark:text-slate-400">
                    <p className="text-3xl mb-2">🔒</p>
                    <p className="text-sm">
                      {selected.response_count < selected.min_responses_for_analysis
                        ? `${t('modules.leadership.culturePage.messages.notEnoughResponses')} (${selected.response_count}/${selected.min_responses_for_analysis})`
                        : t('modules.leadership.culturePage.messages.noResults')
                      }
                    </p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-8 text-center text-slate-500 dark:text-slate-400">
              <p className="text-3xl mb-3">📝</p>
              <p className="text-sm">{t('modules.leadership.culturePage.messages.selectSurvey')}</p>
            </div>
          )}
        </div>
      </div>

      {/* Modal crear encuesta */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                {t('modules.leadership.culturePage.form.title')}
              </h2>
              <form onSubmit={handleCreateSurvey} className="space-y-4">
                <input
                  type="text"
                  placeholder={t('modules.leadership.culturePage.form.surveyTitle')}
                  value={surveyForm.title}
                  onChange={e => setSurveyForm(f => ({ ...f, title: e.target.value }))}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm"
                />
                <textarea
                  placeholder={t('modules.leadership.culturePage.form.description')}
                  value={surveyForm.description}
                  onChange={e => setSurveyForm(f => ({ ...f, description: e.target.value }))}
                  rows={2}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm"
                />
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs text-slate-500 dark:text-slate-400 mb-1">{t('modules.leadership.culturePage.form.startDate')}</label>
                    <input type="date" value={surveyForm.start_date} onChange={e => setSurveyForm(f => ({ ...f, start_date: e.target.value }))} required className="w-full px-2 py-1.5 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm" />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 dark:text-slate-400 mb-1">{t('modules.leadership.culturePage.form.endDate')}</label>
                    <input type="date" value={surveyForm.end_date} onChange={e => setSurveyForm(f => ({ ...f, end_date: e.target.value }))} required className="w-full px-2 py-1.5 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm" />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 dark:text-slate-400 mb-1">{t('modules.leadership.culturePage.form.minResponses')}</label>
                    <input type="number" min="3" max="100" value={surveyForm.min_responses_for_analysis} onChange={e => setSurveyForm(f => ({ ...f, min_responses_for_analysis: parseInt(e.target.value) }))} className="w-full px-2 py-1.5 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm" />
                  </div>
                </div>

                {/* Preguntas */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-slate-700 dark:text-slate-300">{t('modules.leadership.culturePage.form.questions')}</label>
                    <button type="button" onClick={addQuestion} className="text-xs text-blue-600 hover:underline">+ Agregar</button>
                  </div>
                  {surveyForm.questions.map((q, idx) => (
                    <div key={idx} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        placeholder={`Pregunta ${idx + 1}`}
                        value={q.text}
                        onChange={e => updateQuestion(idx, 'text', e.target.value)}
                        className="flex-1 px-2 py-1.5 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-xs"
                      />
                      <select value={q.type} onChange={e => updateQuestion(idx, 'type', e.target.value)} className="px-2 py-1.5 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-xs">
                        <option value="scale">Escala 1-5</option>
                        <option value="choice">Opción</option>
                        <option value="text">Texto</option>
                      </select>
                    </div>
                  ))}
                </div>

                <div className="flex gap-3 pt-2">
                  <button type="submit" className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                    {t('common.buttons.save')}
                  </button>
                  <button type="button" onClick={() => setShowCreateForm(false)} className="flex-1 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-sm">
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

export default QualityCulturePage;
