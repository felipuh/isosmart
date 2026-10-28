import React, { useCallback, useEffect, useState } from 'react';
import { useI18n } from '../../../context/I18nContext';
import qmsService, { qmsErrorMessage } from '../../../services/qmsService';

const field = 'w-full rounded border border-slate-300 px-2 py-1 text-sm';
const btn = 'rounded bg-blue-700 px-3 py-1 text-sm text-white disabled:opacity-50';
const todayPlus = (days) => new Date(Date.now() + days * 86400000).toISOString().slice(0, 10);

function Section({ title, testId, children }) {
  return (
    <section data-testid={testId} className="rounded border border-slate-200 bg-white p-4 space-y-3">
      <h2 className="text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function Label({ text, children }) {
  return (
    <label className="block text-sm">
      <span className="text-slate-700">{text}</span>
      {children}
    </label>
  );
}

function ActionForm({ submitLabel, disabled, onSubmit, initial, children, testId, hidden }) {
  const [values, setValues] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const set = (name) => (event) => setValues((prev) => ({ ...prev, [name]: event.target.value }));
  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      await onSubmit(values);
      setValues(initial);
    } catch (err) {
      setError(qmsErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };
  if (hidden) return null;
  return (
    <form onSubmit={submit} data-testid={testId} className="grid gap-2 md:grid-cols-2">
      {children(values, set)}
      <div className="md:col-span-2 flex items-center gap-3">
        <button type="submit" className={btn} disabled={disabled || busy}>
          {busy ? '…' : submitLabel}
        </button>
        {error && <span role="alert" className="text-sm text-red-700">{error}</span>}
      </div>
    </form>
  );
}

const QmsCapaPage = () => {
  const { t } = useI18n();
  const [state, setState] = useState({
    loading: true, error: '', forbidden: false, organizations: [], requirements: [],
    evidence: [], audits: [], findings: [], ncs: [], capas: [], owners: [],
    caps: { can_write: false, write_policy_configured: false, capa_create_enabled: false },
  });
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    try {
      const caps = await qmsService.capabilities();
      const [organizations, requirements, evidence, audits, findings, ncs, capas, owners] = await Promise.all([
        qmsService.organizations(), qmsService.requirements(), qmsService.evidence(), qmsService.audits(),
        qmsService.findings(), qmsService.nonconformities(), qmsService.correctiveActions(),
        caps.can_write ? qmsService.owners() : Promise.resolve([]),
      ]);
      setState({ loading: false, error: '', forbidden: false, organizations, requirements, evidence, audits, findings, ncs, capas, owners, caps });
    } catch (err) {
      setState((prev) => ({
        ...prev, loading: false, forbidden: err?.response?.status === 403, error: qmsErrorMessage(err),
      }));
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const act = (call, message) => async (values) => {
    await call(values);
    setNotice(message);
    await load();
  };

  const { loading, error, forbidden, organizations, requirements, evidence, audits, findings, ncs, capas, owners, caps } = state;
  const ro = forbidden || !caps.can_write;
  const firstOrg = organizations[0]?.id || '';
  const ncByFinding = Object.fromEntries(ncs.filter((n) => n.source_type === 'finding').map((n) => [n.source_id, n]));

  if (loading) return <div role="status">{t('qmsCapa.loading', 'Loading QMS audit and corrective action data…')}</div>;

  return (
    <div className="space-y-4 p-4" data-testid="qms-capa-page">
      <h1 className="text-2xl font-bold">{t('qmsCapa.title', 'Audits, Findings, Nonconformities and Corrective Actions')}</h1>
      {error && <div role="alert" className="rounded border border-red-300 bg-red-50 p-2 text-sm text-red-800">{error}</div>}
      {forbidden && <div className="text-sm">{t('qmsCapa.forbidden', 'You do not have permission to use this workspace.')}</div>}
      {!forbidden && !caps.can_write && (
        <div role="status" data-testid="qms-readonly" className="rounded border border-amber-300 bg-amber-50 p-2 text-sm text-amber-900">
          {caps.write_policy_configured
            ? t('qmsCapa.readOnlyRole', 'Your role is not authorized to create QMS records. Showing read-only data.')
            : t('qmsCapa.readOnlyPolicy', 'QMS record creation is disabled until a write-role policy is configured. Showing read-only data.')}
        </div>
      )}
      {notice && <div role="status" className="rounded border border-green-300 bg-green-50 p-2 text-sm text-green-800">{notice}</div>}
      {!error && organizations.length === 0 && (
        <div className="text-sm">{t('qmsCapa.noOrganization', 'Complete onboarding to create an organization before registering audits.')}</div>
      )}

      <Section title={t('qmsCapa.evidence', 'Evidence references')} testId="qms-evidence">
        <ul className="text-sm list-disc pl-5">
          {evidence.map((e) => <li key={e.id}>{e.source_type} — {e.source_uri || e.id}</li>)}
          {evidence.length === 0 && <li className="list-none text-slate-500">{t('qmsCapa.empty', 'No records yet.')}</li>}
        </ul>
        <ActionForm hidden={ro} testId="evidence-form" submitLabel={t('qmsCapa.addEvidence', 'Add evidence')} disabled={ro || !firstOrg}
          initial={{ source_type: 'audit_record', source_uri: '', content_hash: '' }}
          onSubmit={act((v) => qmsService.createEvidence({
            organization_id: firstOrg, source_type: v.source_type, source_uri: v.source_uri || undefined,
            content_hash: v.content_hash.trim().toLowerCase(), captured_at: new Date().toISOString(),
          }), t('qmsCapa.evidenceSaved', 'Evidence saved.'))}>
          {(v, set) => (<>
            <Label text={t('qmsCapa.sourceType', 'Source type')}><input className={field} required maxLength={80} value={v.source_type} onChange={set('source_type')} /></Label>
            <Label text={t('qmsCapa.sourceUri', 'Source URI')}><input className={field} value={v.source_uri} onChange={set('source_uri')} /></Label>
            <Label text={t('qmsCapa.contentHash', 'SHA-256 content hash (64 hex)')}><input className={field} required pattern="[0-9a-fA-F]{64}" value={v.content_hash} onChange={set('content_hash')} /></Label>
          </>)}
        </ActionForm>
      </Section>

      <Section title={t('qmsCapa.audits', 'Audits')} testId="qms-audits">
        <ul className="text-sm list-disc pl-5">
          {audits.map((a) => <li key={a.id}>{a.scope} — {a.criteria} ({a.status}, {a.lead_auditor})</li>)}
          {audits.length === 0 && <li className="list-none text-slate-500">{t('qmsCapa.empty', 'No records yet.')}</li>}
        </ul>
        <ActionForm hidden={ro} testId="audit-form" submitLabel={t('qmsCapa.addAudit', 'Register audit')} disabled={ro || !firstOrg}
          initial={{ organization_id: '', scope: '', criteria: '', status: '', lead_auditor: '' }}
          onSubmit={act((v) => qmsService.createAudit({ ...v, organization_id: v.organization_id || firstOrg }), t('qmsCapa.auditSaved', 'Audit registered.'))}>
          {(v, set) => (<>
            <Label text={t('qmsCapa.organization', 'Organization')}>
              <select className={field} value={v.organization_id || firstOrg} onChange={set('organization_id')}>
                {organizations.map((o) => <option key={o.id} value={o.id}>{o.display_name}</option>)}
              </select>
            </Label>
            <Label text={t('qmsCapa.scope', 'Scope')}><input className={field} required value={v.scope} onChange={set('scope')} /></Label>
            <Label text={t('qmsCapa.criteria', 'Criteria')}><input className={field} required value={v.criteria} onChange={set('criteria')} /></Label>
            <Label text={t('qmsCapa.status', 'Status')}><input className={field} required maxLength={80} value={v.status} onChange={set('status')} /></Label>
            <Label text={t('qmsCapa.leadAuditor', 'Lead auditor')}><input className={field} required value={v.lead_auditor} onChange={set('lead_auditor')} /></Label>
          </>)}
        </ActionForm>
      </Section>

      <Section title={t('qmsCapa.findings', 'Findings')} testId="qms-findings">
        <ul className="text-sm space-y-2">
          {findings.map((f) => {
            const nc = ncByFinding[f.id];
            return (
              <li key={f.id} className="border-b pb-2">
                <div>[{f.type}] {f.statement}</div>
                {nc ? <div className="text-slate-600">{t('qmsCapa.ncCreated', 'Nonconformity registered')}: {nc.description} ({nc.severity}, {nc.status})</div> : (
                  <ActionForm hidden={ro} testId={`nc-form-${f.id}`} submitLabel={t('qmsCapa.addNc', 'Register nonconformity')} disabled={ro}
                    initial={{ description: '', severity: '', status: '' }}
                    onSubmit={act((v) => qmsService.createNonconformity(f.id, v), t('qmsCapa.ncSaved', 'Nonconformity registered.'))}>
                    {(v, set) => (<>
                      <Label text={t('qmsCapa.description', 'Description')}><input className={field} required value={v.description} onChange={set('description')} /></Label>
                      <Label text={t('qmsCapa.severity', 'Severity')}><input className={field} required maxLength={80} value={v.severity} onChange={set('severity')} /></Label>
                      <Label text={t('qmsCapa.status', 'Status')}><input className={field} required maxLength={80} value={v.status} onChange={set('status')} /></Label>
                    </>)}
                  </ActionForm>
                )}
              </li>
            );
          })}
          {findings.length === 0 && <li className="text-slate-500">{t('qmsCapa.empty', 'No records yet.')}</li>}
        </ul>
        <ActionForm hidden={ro} testId="finding-form" submitLabel={t('qmsCapa.addFinding', 'Register finding')} disabled={ro || !audits.length || !evidence.length}
          initial={{ audit_id: '', requirement_id: '', evidence_id: '', type: '', statement: '' }}
          onSubmit={act((v) => qmsService.createFinding({
            ...v, audit_id: v.audit_id || audits[0].id, requirement_id: v.requirement_id || requirements[0]?.id,
            evidence_id: v.evidence_id || evidence[0].id,
          }), t('qmsCapa.findingSaved', 'Finding registered.'))}>
          {(v, set) => (<>
            <Label text={t('qmsCapa.audit', 'Audit')}>
              <select className={field} value={v.audit_id || audits[0]?.id || ''} onChange={set('audit_id')}>
                {audits.map((a) => <option key={a.id} value={a.id}>{a.scope}</option>)}
              </select>
            </Label>
            <Label text={t('qmsCapa.requirement', 'Requirement')}>
              <select className={field} value={v.requirement_id || requirements[0]?.id || ''} onChange={set('requirement_id')}>
                {requirements.map((r) => <option key={r.id} value={r.id}>{r.clause} — {r.paraphrase.slice(0, 60)}</option>)}
              </select>
            </Label>
            <Label text={t('qmsCapa.evidenceItem', 'Evidence')}>
              <select className={field} value={v.evidence_id || evidence[0]?.id || ''} onChange={set('evidence_id')}>
                {evidence.map((e) => <option key={e.id} value={e.id}>{e.source_type} — {e.source_uri || e.id.slice(0, 8)}</option>)}
              </select>
            </Label>
            <Label text={t('qmsCapa.type', 'Type')}><input className={field} required maxLength={80} value={v.type} onChange={set('type')} /></Label>
            <Label text={t('qmsCapa.statement', 'Statement')}><input className={field} required value={v.statement} onChange={set('statement')} /></Label>
          </>)}
        </ActionForm>
      </Section>

      <Section title={t('qmsCapa.corrective', 'Corrective actions')} testId="qms-capa">
        <ul className="text-sm list-disc pl-5">
          {capas.map((c) => <li key={c.id}>{c.action} — {t('qmsCapa.due', 'due')} {c.due_date}</li>)}
          {capas.length === 0 && <li className="list-none text-slate-500">{t('qmsCapa.empty', 'No records yet.')}</li>}
        </ul>
        {!ro && !caps.capa_create_enabled && (
          <div role="status" data-testid="capa-blocked" className="text-sm text-amber-900">
            {t('qmsCapa.capaBlocked', 'Corrective action creation is blocked: the source defines no Cause contract for cause_id.')}
          </div>
        )}
        <ActionForm hidden={ro || !caps.capa_create_enabled} testId="capa-form" submitLabel={t('qmsCapa.addCapa', 'Register corrective action')} disabled={ro || !ncs.length}
          initial={{ nc_id: '', cause_id: '', action: '', owner_id: '', due_date: todayPlus(30) }}
          onSubmit={act((v) => qmsService.createCorrectiveAction(v.nc_id || ncs[0].id, {
            cause_id: v.cause_id.trim(), action: v.action, owner_id: v.owner_id.trim(), due_date: v.due_date,
          }), t('qmsCapa.capaSaved', 'Corrective action registered.'))}>
          {(v, set) => (<>
            <Label text={t('qmsCapa.nonconformity', 'Nonconformity')}>
              <select className={field} value={v.nc_id || ncs[0]?.id || ''} onChange={set('nc_id')}>
                {ncs.map((n) => <option key={n.id} value={n.id}>{n.description}</option>)}
              </select>
            </Label>
            <Label text={t('qmsCapa.causeId', 'Externally supplied cause reference (UUID)')}><input className={field} required value={v.cause_id} onChange={set('cause_id')} /></Label>
            <Label text={t('qmsCapa.action', 'Action')}><input className={field} required value={v.action} onChange={set('action')} /></Label>
            <Label text={t('qmsCapa.owner', 'Owner')}>
              <select className={field} required value={v.owner_id} onChange={set('owner_id')}>
                <option value="">{t('qmsCapa.selectOwner', 'Select owner')}</option>
                {owners.map((o) => <option key={o.id} value={o.id}>{o.email || o.id}</option>)}
              </select>
            </Label>
            <Label text={t('qmsCapa.dueDate', 'Due date')}><input type="date" className={field} required value={v.due_date} onChange={set('due_date')} /></Label>
          </>)}
        </ActionForm>
      </Section>
    </div>
  );
};

export default QmsCapaPage;
