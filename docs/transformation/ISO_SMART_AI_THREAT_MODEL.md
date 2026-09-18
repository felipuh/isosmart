# ISO Smart AI — threat model de Enterprise Data foundation

Escala cualitativa: likelihood e impact `Low/Medium/High/Critical`. Residual risk es el esperado después de controles diseñados, pero antes de evidencia productiva; ningún control RLS se declara implementado en esta fase.

| Threat | Likelihood | Impact | Control | Test | Residual risk |
|---|---|---|---|---|---|
| Tenant spoofing por body/header/query | High | Critical | Tenant sólo de identity→projection; fields read-only; SET LOCAL server-side | forged tenant IDs en CRUD/API/raw | Low una vez RLS probada |
| TenantProjection drift | Medium | Critical | source version/event, reconcile states, fail-closed, immutable external ID | stale/out-of-order/conflicting events | Medium: dependencia AdminApps |
| Stale entitlement/revocation | High | Critical | max-staleness por operación, directed invalidation, fresh check para high impact | revoke during cached session/outage | Medium |
| RLS bypass por role/config | Medium | Critical | ENABLE+FORCE, no owner/BYPASS, catalog assertions | role introspection + A/B/none | Low |
| Application owner bypass | Medium | Critical | non-login owner; separate migrator/app roles | connect as app, inspect ownership/rolbypassrls | Low |
| Worker tenant bleed | High | Critical | event tenant validation, one atomic/SET LOCAL per task, quarantine missing | sequential A/B/error/retry tasks | Low |
| Pool/transaction tenant bleed | High | Critical | transaction-scoped GUC, atomic all tenant queries, rollback | reuse A→none→B; exception reuse | Low |
| Event replay | High | High | signed ingress, nonce/time, Inbox unique, explicit audited replay | resend same external/internal event | Low |
| Event duplication | High (expected) | High | at-least-once + ConsumerReceipt/business idempotency | publish/ack crash and duplicate delivery | Low |
| Event forgery/payload substitution | Medium | Critical | signature/source allow-list, schema validation, payload hash, no generic event POST | invalid key/schema/hash/event type | Low/Medium key custody |
| Poison event/retry storm | Medium | High | bounded retry+jitter, permanent classification, PostgreSQL dead-letter, alerts | deterministic handler failure | Low |
| Audit mutation/deletion | Medium | Critical | no runtime DML, append function, hash chain, external manifests/WORM | UPDATE/DELETE/TRUNCATE + tamper verify | Medium: privileged DB admin remains |
| Broken provenance | High | Critical | frozen RecommendationBasis, hashes, versions, trace/causation | omit rule/evidence/model/approval | Low for gated material outputs |
| Normativa histórica sobrescrita | Medium | Critical | published append-only, N+1 release, restrictive grants, frozen coverage | mutate N after publish; N+1 delta | Low |
| Cross-tenant object graph | High | Critical | direct tenant IDs, composite FKs, bilateral edge checks, RLS | every A/B endpoint combination + traversal | Low |
| Import/backfill contamination | High | Critical | tenant batches, no default tenant, mappings/checkpoints/reconcile/quarantine | mixed tenant fixtures, missing external ID, resume | Medium until migration complete |
| Tenant reassignment through CRUD/admin | Medium | Critical | immutable tenant IDs, DB trigger/service, no PATCH, special transfer protocol | direct/bulk/admin update tenant_id | Low |
| Global catalog malicious write | Low/Medium | Critical | runtime read-only grants, curator release, signed/source-hashed artifacts | app write/delete; unlicensed/unapproved release | Low/Medium curator compromise |
| SQL injection/search_path hijack | Medium | Critical | parameterized SQL, fixed search_path, no CREATE runtime, security-definer review | hostile identifiers/GUC/function shadowing | Low |
| Raw SQL bypass assumption | Medium | Critical | RLS applies to raw SQL; repositories allow-listed; no owner role | exact raw A/B/none queries | Low |
| Bulk operation bypass/partial mix | Medium | Critical | inject tenant, composite FK, atomic batch, policies | mixed tenant bulk_create/upsert/update | Low |
| Admin/support overreach | Medium | Critical | staff ≠ cross-tenant, scoped support grants, export/job paths, audit | admin without context, forged staff flag | Medium human/process |
| Break-glass abuse | Low | Critical | vaulted MFA, dual control, TTL/scope, session/external log, reconcile | tabletop + expired credential | Medium privileged threat |
| Privacy deletion breaks audit chain | Medium | High | minimization, pseudonymous tombstone, approved chain segment exception | erasure workflow + verifier/export | Medium legal variance |
| Object storage/DB evidence mismatch | Medium | Critical | content hash, version ID, consistent restore manifest | replace/missing object, point-in-time restore | Medium external storage |
| Malicious/incorrect normative import | Medium | Critical | licensed controlled source, edition hash, review/release, no direct source mutation | wrong hash/edition/schema, unsigned import | Medium until source obtained |
| Public arbitrary event injection | Medium | Critical | remove/disable generic `/v1/events`; typed commands/webhooks only | unauthorized event POST/event type | Low after contract change |
| Availability failure weaponized as allow | Medium | Critical | 503 fail-closed for required authority; no production fallback | AdminApps timeout/malformed/DNS/cache expired | Low security; Medium availability |

## Trust boundaries

1. Browser/client → ISO Smart API: untrusted tenant/object IDs and payloads.
2. AdminApps/IdP → projection/inbox: authoritative only after cryptographic/contract validation.
3. Web/worker → PostgreSQL: runtime roles constrained by grants + RLS; pool is not trusted to retain correct session state.
4. Curator/migrator/break-glass → global/audit data: privileged, separately authenticated and externally audited.
5. Object store/model/retrieval/event transports: external effects and data require tenant namespace, hashes, redaction and provenance.

## Gate

Unresolved P0 for implementation is any absent 10/10 intake, undefined AdminApps ownership, app superuser/owner/BYPASSRLS, missing `ENABLE+FORCE` catalog proof, context surviving commit or rollback, request-controlled tenant reaching `set_config`, mutable `tenant_id` without an independent DB trigger, missing default-deny policy/test, cross-tenant FK possibility, mutable published normativa/audit, non-atomic outbox or rollback without evidence. Current design resolves these on paper; behavioral and catalog proof on PostgreSQL 18.6 plus the AdminApps contract remain implementation restrictions.
