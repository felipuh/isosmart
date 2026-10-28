// features/leadership/pages/AuditorPackPage.jsx
// Paquete para Auditor — ISO 9001:2015 §9.2/9.3
// Genera un snapshot verificable con firmas digitales (SHA-256)

import React, { useState } from 'react';
import { useI18n } from '../../../context/I18nContext';
import { generateAuditorPack, verifyApprovalSignature } from '../api/leadershipApi';

const Section = ({ icon, title, count, children, defaultOpen = false }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between p-4 text-left"
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">{icon}</span>
          <span className="font-semibold text-slate-900 dark:text-white text-sm">{title}</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">{count}</span>
        </div>
        <span className="text-slate-400 text-xs">{open ? '▲' : '▼'}</span>
      </button>
      {open && <div className="px-4 pb-4">{children}</div>}
    </div>
  );
};

const Badge = ({ value, positive }) => (
  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
    positive ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
              : 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
  }`}>
    {value}
  </span>
);

const AuditorPackPage = () => {
  const { t } = useI18n();
  const [pack, setPack] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [generatedAt, setGeneratedAt] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    setPack(null);
    setVerifyResult(null);
    try {
      const data = await generateAuditorPack();
      setPack(data);
      setGeneratedAt(new Date().toLocaleString());
    } catch (err) {
      setError(err?.response?.data?.error || t('modules.leadership.auditorPack.messages.generateError'));
    } finally {
      setLoading(false);
    }
  };

  const handleVerifySignature = async (recordId) => {
    setVerifying(true);
    setVerifyResult(null);
    try {
      const r = await verifyApprovalSignature(recordId);
      setVerifyResult({ id: recordId, ...r });
    } catch {
      setVerifyResult({ id: recordId, valid: false, error: 'Error al verificar' });
    } finally {
      setVerifying(false);
    }
  };

  const handleDownloadJSON = () => {
    if (!pack) return;
    const blob = new Blob([JSON.stringify(pack, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `auditor_pack_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 bg-slate-50 dark:bg-slate-900 min-h-screen space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            {t('modules.leadership.auditorPack.title')}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t('modules.leadership.auditorPack.subtitle')}
          </p>
        </div>
        <div className="flex gap-3">
          {pack && (
            <button onClick={handleDownloadJSON} className="px-4 py-2 bg-slate-600 text-white rounded-lg text-sm hover:bg-slate-700 flex items-center gap-2">
              ⬇ JSON
            </button>
          )}
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? (
              <><div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" /> Generando...</>
            ) : (
              <>📦 {t('modules.leadership.auditorPack.buttons.generate')}</>
            )}
          </button>
        </div>
      </div>

      {/* Nota auditoría */}
      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg p-4 flex gap-3">
        <span className="text-2xl">⚠️</span>
        <div>
          <p className="text-sm font-semibold text-amber-800 dark:text-amber-200">
            {t('modules.leadership.auditorPack.noteTitle')}
          </p>
          <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
            {t('modules.leadership.auditorPack.noteDesc')}
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-red-700 dark:text-red-300 text-sm">
          {error}
        </div>
      )}

      {!pack && !loading && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
          <p className="text-5xl mb-4">📋</p>
          <p className="text-slate-500 dark:text-slate-400 text-sm mb-4">
            {t('modules.leadership.auditorPack.messages.empty')}
          </p>
          <button onClick={handleGenerate} className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
            {t('modules.leadership.auditorPack.buttons.generate')}
          </button>
        </div>
      )}

      {pack && (
        <div className="space-y-4">
          {/* Meta */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4 flex items-center justify-between flex-wrap gap-3">
            <div>
              <p className="text-xs text-blue-700 dark:text-blue-300 font-medium">{t('modules.leadership.auditorPack.generatedAt')}: <strong>{generatedAt}</strong></p>
              {pack.organization && <p className="text-xs text-blue-600 dark:text-blue-400 mt-0.5">{pack.organization}</p>}
              {pack.ai_disclaimer && <p className="text-xs text-blue-500 dark:text-blue-400 mt-0.5 italic">{pack.ai_disclaimer}</p>}
            </div>
            <div className="flex gap-2">
              <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded-full">ISO 9001:2015</span>
              <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded-full">§5 + §9.3</span>
            </div>
          </div>

          {/* Verify result */}
          {verifyResult && (
            <div className={`rounded-lg p-3 text-sm ${verifyResult.valid ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 border border-green-200' : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200'}`}>
              {verifyResult.valid
                ? `✅ Firma verificada — Registro #${verifyResult.id}`
                : `❌ ${verifyResult.error || 'Firma inválida'} — Registro #${verifyResult.id}`
              }
            </div>
          )}

          {/* Políticas */}
          {pack.policies && (
            <Section icon="📄" title="Políticas de Calidad" count={pack.policies.length} defaultOpen>
              <div className="space-y-2 mt-2">
                {pack.policies.length === 0 ? (
                  <p className="text-xs text-slate-400">Sin políticas</p>
                ) : pack.policies.map((p, idx) => (
                  <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-700 last:border-0">
                    <div>
                      <p className="text-sm text-slate-800 dark:text-slate-200">{p.title}</p>
                      <p className="text-xs text-slate-400">v{p.version} · {p.status}</p>
                    </div>
                    <Badge value={p.status} positive={p.status === 'published'} />
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Revisiones de gestión */}
          {pack.management_reviews && (
            <Section icon="📋" title="Revisiones de Gestión" count={pack.management_reviews.length}>
              <div className="space-y-2 mt-2">
                {pack.management_reviews.length === 0 ? <p className="text-xs text-slate-400">Sin revisiones</p> : pack.management_reviews.map((r, idx) => (
                  <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-700 last:border-0">
                    <div>
                      <p className="text-sm text-slate-800 dark:text-slate-200">{r.title}</p>
                      <p className="text-xs text-slate-400">{r.actual_date || r.scheduled_date}</p>
                    </div>
                    <Badge value={r.status} positive={r.status === 'completed'} />
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Decisiones */}
          {pack.review_decisions && (
            <Section icon="🎯" title="Decisiones de Revisión" count={pack.review_decisions.length}>
              <div className="space-y-2 mt-2">
                {pack.review_decisions.length === 0 ? <p className="text-xs text-slate-400">Sin decisiones</p> : pack.review_decisions.map((d, idx) => (
                  <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-700 last:border-0">
                    <div>
                      <p className="text-sm text-slate-800 dark:text-slate-200">{d.title}</p>
                      <p className="text-xs text-slate-400">{d.decision_type} · {d.status} · {d.responsible || 'Sin responsable'}</p>
                    </div>
                    {d.ai_suggested && <span className="text-xs bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-full">IA sugerida</span>}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Registros de aprobación */}
          {pack.approval_records && (
            <Section icon="🔐" title="Registros de Aprobación (SHA-256)" count={pack.approval_records.length}>
              <div className="space-y-2 mt-2">
                {pack.approval_records.length === 0 ? <p className="text-xs text-slate-400">Sin registros</p> : pack.approval_records.map((ar, idx) => (
                  <div key={idx} className="py-2 border-b border-slate-100 dark:border-slate-700 last:border-0">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">{ar.digital_signature?.slice(0, 16)}...</p>
                        <p className="text-xs text-slate-400">{ar.approved_by} · {ar.approved_at}</p>
                      </div>
                      <button
                        onClick={() => handleVerifySignature(ar.id)}
                        disabled={verifying}
                        className="text-xs text-blue-600 hover:underline disabled:opacity-50"
                      >
                        Verificar firma
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Nodos de evidencia */}
          {pack.evidence_nodes && (
            <Section icon="🕸" title="Nodos de Evidencia" count={pack.evidence_nodes.length}>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2">
                {pack.evidence_nodes.length === 0 ? <p className="text-xs text-slate-400">Sin nodos</p> : pack.evidence_nodes.map((n, idx) => (
                  <div key={idx} className="p-2 bg-slate-50 dark:bg-slate-700/40 rounded text-xs">
                    <p className="font-medium text-slate-700 dark:text-slate-300">{n.title}</p>
                    <p className="text-slate-400">{n.node_type}</p>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Roles */}
          {pack.roles && (
            <Section icon="👥" title="Roles Organizacionales" count={pack.roles.length}>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2">
                {pack.roles.length === 0 ? <p className="text-xs text-slate-400">Sin roles</p> : pack.roles.map((r, idx) => (
                  <div key={idx} className="p-2 bg-slate-50 dark:bg-slate-700/40 rounded text-xs">
                    <p className="font-medium text-slate-700 dark:text-slate-300">{r.title}</p>
                    <p className="text-slate-400">{r.role_type}</p>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* RACI */}
          {pack.raci_matrices && (
            <Section icon="📊" title="Matrices RACI" count={pack.raci_matrices.length}>
              <div className="space-y-1 mt-2">
                {pack.raci_matrices.length === 0 ? <p className="text-xs text-slate-400">Sin matrices</p> : pack.raci_matrices.map((m, idx) => (
                  <p key={idx} className="text-xs text-slate-600 dark:text-slate-300">• {m.title} ({m.entry_count || 0} actividades)</p>
                ))}
              </div>
            </Section>
          )}
        </div>
      )}
    </div>
  );
};

export default AuditorPackPage;
