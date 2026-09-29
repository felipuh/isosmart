# Phase 31.4 V2.5 — Evidence Reconciliation Report

Date: 2026-09-22
State: `PHASE31_4_V2_5_EVIDENCE_RECONCILIATION`
Scope: documentary/static reconciliation only. No retry, pilot, production activity, or Phase 31.5 WS-A was executed.

## Verdict

**PROMOTION_PARTIALLY_RATIFIED**.

The historical Retry 16 `PROMOTED` record remains intact and is not rewritten. Its PostgreSQL environment, migration, limited AdminApps transport, synthetic domain-operation, and teardown-manifest claims have support. Its central live exact-comparison claim is not ratifiable from retained evidence.

The decisive contradiction is internal to the retained artifacts:

- `PHASE31_4_5C_V2_5_RESOLVED_GRAPH_V1.json` declares `resolution_mode: offline_regression_fixture`.
- Its canonical graph hash is `d6723f0fa64fce046d47ad9a64a01c60c33ac6205b26949131b675a4744dddc0`.
- `PHASE31_4_CLEAN_RETRY_16_LIVE_EXACT_COMPARISON.json` calls that same value `live_graph_sha256`.
- The offline capture file declares `native_execution_performed: false`; 562 of 565 capture values are `captured:*` placeholders and the other three are fixed example UUIDs.
- The resolved graph contains 670 `captured:*` occurrences representing 562 distinct placeholder strings.

Therefore the hash proves deterministic integrity of an offline graph, not provenance from Retry 16 PostgreSQL rows.

## Retry 16 live provenance

What is truly live:

- Two disposable PostgreSQL 18.6 environments were allocated for AdminApps and ISO Smart.
- AdminApps and ISO Smart migration logs report successful application of 61 and 92 migrations. Their current bytes match the hashes recorded in `PHASE31_4_CLEAN_RETRY_16_BOOTSTRAP_MIGRATIONS.json`.
- ISO Smart's server log records two accepted AdminApps tenant-event HTTP POSTs (`201`). AdminApps' server log records entitlement validation and user endpoint requests (`200`).
- Three bridge identifiers are retained: actor, TenantProjection, and Process.
- Nine phases invoked material services: Opportunity creation, synthetic catalog/agent creation, AgentRun start/completion, Recommendation, AgentDecision, ActionPlan preparation/dry run, approval/authorization, and controlled Opportunity transition. The report proves only that these callbacks returned without an exception.
- The resource manifest records containers, networks, and volumes as removed.

What is not retained:

- native operation outputs and persisted row snapshots;
- the generated IDs for AgentDefinition, AgentRun, Recommendation, AgentDecision, ActionPlan, dry run, Approval, Authorization, ActionExecution/receipt, and Opportunity successor;
- event, outbox, and audit rows;
- the five Stage EXT values as a complete value set;
- the 565 native capture/readback pairs;
- a live 118-member/1664-field graph.

Outcome: **`LIVE_GRAPH_NOT_RECOVERABLE`**. The databases and volumes were removed, the in-memory captures were not serialized, and the only complete graph is the offline fixture. Replacing placeholders with fixture values would not be legitimate recovery.

## Offline fixture contamination

The structural counts `118` members and `1664` fields are valid properties of the V2.5 contract. The following promotion claims are contaminated by offline fixture substitution:

- `LIVE_EXACT_COMPARISON.live_graph_sha256`;
- `native_captures_resolved: 565` and `upstream_captures_resolved: 5` as claims of retained live values;
- `resolved_members: 118`, `resolved_fields: 1664`, and zero mismatch claims as a live comparison;
- the corresponding exact-comparison, graph-count, and capture-count fields copied into `PROMOTION_CLOSURE`;
- the promoted-baseline live graph hash.

The Retry 16 SHA-256 manifest currently verifies every file it lists. This is byte-integrity assurance only. It does not prove that values came from PostgreSQL, that a query was executed, or that an artifact labeled live was generated from live captures. The server logs are not members of that manifest; the migration logs are indirectly bound through hashes in the bootstrap summary.

## 33 phase verifier audit

| Classification | Count |
|---|---:|
| `FULLY_VERIFIED` | 0 |
| `PARTIALLY_VERIFIED` | 9 |
| `STRUCTURAL_ONLY` | 0 |
| `NO_OP` | 12 |
| `OVERCLAIMED` | 12 |

All 33 retained phase statuses are `PASS`, but none of those PASS records alone logically proves its named guarantee:

- Twelve early phases have no native operation or direct service. `_NativePhaseExecutor` returns a PASS-shaped result by default.
- Nine phases execute relevant services, but the retained bridge drops the operation metadata, assertions, generated IDs, rows, and in-memory captures. These are partial.
- `EVENT_OUTBOX_ASSERTIONS` checks only that `authorization_id` exists; it performs no event/outbox/audit query.
- Eleven late phases—including `RESOLVED_GRAPH`, `EXACT_COMPARISON`, `SECURITY_EVIDENCE`, closure, and teardown verification—share a branch that only checks for `authorization_id` and returns PASS.
- `V25ExecutionSession.run_phase` ignores the returned `PhaseExecutionResult.status`; any callback that returns without exception is recorded as PASS.

Detailed phase-by-phase evidence is in `docs/governance/evidence/PHASE31_4_V2_5_PHASE_VERIFIER_AUDIT_V1.json`.

Required design correction:

1. Reject any phase without a valid operation and explicit assertions; remove all default-PASS branches.
2. Persist the returned status, executor identity, inputs hash, operation, output/readback IDs, assertion results, artifact paths, and hashes.
3. Materialize `RESOLVED_GRAPH` only from serialized live capture/readback pairs and reject `captured:*` and fixture identities.
4. Perform an independent exact comparison after capture, with full mismatch details.
5. Query actual event/outbox/audit rows.
6. Execute named positive and negative security/RLS/least-privilege probes.
7. Run teardown outside the business phase loop and verify absence afterward in a distinct step.

## AdminApps provenance

Real versus synthetic:

- AdminApps delivery is partially real: two HTTP tenant-event posts were accepted. The event envelopes, event IDs, AdminApps outbox rows, delivery receipts, signatures, and ISO Smart ingress receipts were not retained.
- `retry16_admin_create.py` creates/reads an AdminApps user through ORM and authenticates an in-process DRF test client with `force_authenticate`. This is not a real login/token journey.
- `user.updated` is constructed locally in `retry16_live.py` and passed directly to `ProjectionWriterService.apply`; UserProjection is therefore synthetic/local for this retry.
- `tenant.provisioned` has a local fallback branch. The two HTTP deliveries make upstream projection likely, but the retained report does not serialize which branch supplied the projection.
- QMS Organization and Process are ISO Smart-native local objects, not upstream captures.
- The actor ID originates in AdminApps, but its authoritative role is not propagated. The approval harness injects `authorized_roles=("quality_approver",)` literally.
- AdminApps harness roles were `is_staff`, `is_superuser`, and UserOrganization `superadmin`; ISO Smart used the unrelated literal `quality_approver`.

The bundle's blanket label `LIVE_UPSTREAM_NATIVE_CAPTURE` for all five values is overbroad. Only the AdminApps tenant identity is unambiguously upstream-native; TenantProjection is a local read model, UserProjection is locally synthesized, and Organization/Process are ISO Smart native outputs.

## Original requirements

The authoritative DOCX/JSON/XLSX contain 63 requirement cards. Current summary:

| Status | Count |
|---|---:|
| `IMPLEMENTED_AND_PROVEN` | 0 |
| `IMPLEMENTED_NOT_LIVE_PROVEN` | 0 |
| `PARTIAL` | 63 |
| `PLANNED` | 0 |
| `DEFERRED` | 0 |
| `DISCARDED_BY_GOVERNANCE` | 0 |
| `NOT_IMPLEMENTED` | 0 |

Every card has some related domain capability, model, view, engine, or foundation. None has a retained live acceptance chain from visible result to source requirement, Knowledge Layers, evidence, model/rule versions, and human decision where required. This is why the result is `PARTIAL`, not requirement coverage inferred from database machinery.

The complete 63-row matrix is in `docs/governance/evidence/PHASE31_4_V2_5_SOURCE_REQUIREMENT_TRACEABILITY_V1.json`.

## Onboarding

| Status | Count |
|---|---:|
| `PARTIAL` | 16 |
| `NOT_IMPLEMENTED` | 1 |

The non-implemented stage is the backend-authoritative adaptive `ISO 9000:2026 Foundation Gate`. The other stages have related pieces, but there is no proven 17-stage state machine or complete first-use journey. Retry 16 partially supports Tenant Provisioning transport/projection only; it is not onboarding acceptance.

## Product priorities

| Original objective | Status | Reconciliation |
|---|---|---|
| Onboarding | partial | Related features exist; no 17-stage authoritative flow. |
| Foundation Gate | unproven | Required adaptive learning gate not implemented as specified. |
| Evidence Graph | partial | Legacy UI and newer evidence foundations exist; not source-complete. |
| Recommendation Drawer | unproven | The source calls it the Normative Intelligence Drawer; no conformant component was located. |
| A0–A3 agents | partial | Governed foundations and a synthetic A3-shaped run exist; real product agents/authority are unproven. |
| Audit | partial | Audit/Finding domain exists; autonomous source acceptance is incomplete. |
| CAPA | partial | NC/CorrectiveAction/Effectiveness foundations exist; canonical closed loop is incomplete. |
| Risk | partial | Risk/Opportunity exists; source-specific governed experience is incomplete. |
| Value discovery | unproven | Three value engines and measurable outcome are not proven. |
| Tangible first-day value | unproven | No three savings opportunities, top risks, 3/6/12 roadmap, and next action experience is retained. |

Governance/runtime hardening is useful, but it cannot stand in for these product outcomes.

## Legitimate extensions

- AdminApps authority specialization — `LEGITIMATE_ARCHITECTURAL_SPECIALIZATION`.
- TenantProjection/UserProjection — `LEGITIMATE_ARCHITECTURAL_SPECIALIZATION`.
- Transactional Outbox — `GOVERNANCE_SUPPORTING_MECHANISM`.
- ActionPlan — `GOVERNANCE_SUPPORTING_MECHANISM`.
- Execution Authorization — `GOVERNANCE_SUPPORTING_MECHANISM`.
- Exact row-level contract — `POC_ONLY`.
- Phase 31.5 hardening — `GOVERNANCE_SUPPORTING_MECHANISM`, currently held.

These remain valid only when labeled accurately and when they serve, rather than replace, original product requirements.

## Scope drift

- The 118/1664 machinery is `POTENTIAL_SCOPE_DRIFT`: it became a promotion target without proving any of the 63 source acceptance cards or 17 onboarding stages.
- Treating an offline deterministic graph hash as live exact-comparison evidence is evidence-governance drift.
- Repeated runtime/governance hardening without measurable onboarding, drawer, value-discovery, or first-day-value progress risks roadmap displacement.
- Synthetic AdminApps projections and harness role literals must not be relabeled as authenticated upstream authority.

## Factual documentation correction

`ISO_SMART_AI_SOURCE_RECONCILIATION.md` says the source DDL lacks `EffectivenessCheck.tenant_id`. That is false: the original DDL defines `effectiveness_check.tenant_id uuid NOT NULL REFERENCES tenant`. The structured JSON/XLSX entity lists `check_id; subject_type; subject_id; method; due_at; result; evidence_id` and omits `tenant_id`.

Correct interpretation: the DDL includes the field; the structured maps omit it. Keeping direct tenant scope is a reasonable target specialization, but it must not be presented as a field common to all original representations. The historical derived document and source artifacts were not modified; this successor records the correction.

No second confirmed field-level contradiction was found in the checked neighboring cases. `ActionExecution` and `RecommendationBasis` do lack direct `tenant_id` in both structured map and DDL, so proposing direct tenant scope for them remains an architectural decision, not a source fact.

## Phase 31.5

Disposition: **`CONCEPTUALLY_ALIGNED / EXECUTION_HELD`**.

No Phase 31.5 artifact was deleted and WS-A was not executed. Its corrected gate model is:

1. documentary admission;
2. disposable environment authorization;
3. environment provisioning;
4. environment acceptance;
5. WS-A execution.

No earlier gate may require evidence that only a later gate can produce.

## Missing evidence

Exact missing set:

1. Complete six-identity Stage EXT capture/readback package: external tenant, actor, TenantProjection, UserProjection, QMS Organization, and Process.
2. All 565 native output/readback pairs with type, phase, service/operation, retry ID, and provenance; zero placeholders.
3. Live materialized graph with exactly 118 members and 1664 typed fields.
4. Independent exact-comparison mismatch output over that graph.
5. Row snapshots and IDs for Opportunity before/successor, AgentDefinition, AgentRun, Recommendation, AgentDecision, ActionPlan, dry run, Approval, Authorization, ActionExecution/receipt, and controlled revision.
6. DomainEvent, TransactionalOutbox, and ImmutableAuditLog rows linked by aggregate, trace, payload, and transaction.
7. AdminApps event/outbox envelopes, delivery receipts, and ISO Smart ingress receipts.
8. Real authenticated identity/entitlement evidence and source-backed actor/approver roles.
9. Positive and negative RLS, tenant-isolation, least-privilege, and authorization probes.
10. Transaction rollback/atomicity evidence and independent post-teardown absence checks.

The minimum future execution, after separately authorized verifier remediation, is one disposable evidence-only retry of the synthetic chain that serializes precisely this evidence. It must not start a pilot, production, or Phase 31.5 WS-A.

## Product code modified

None. This reconciliation adds successor documentation/evidence only. It does not modify V2.4, Retry 16 artifacts, source artifacts, product code, historical hashes, blockers, or promotion closure.

## Next authorized action

Authorize one separate **verifier-remediation change only**: remove default-PASS semantics and add retained per-phase capture/readback evidence. Review that change before separately authorizing any disposable rerun.

## Successor artifacts

- `docs/governance/evidence/PHASE31_4_V2_5_EVIDENCE_RECONCILIATION_V1.json`
- `docs/governance/evidence/PHASE31_4_V2_5_SOURCE_REQUIREMENT_TRACEABILITY_V1.json`
- `docs/governance/evidence/PHASE31_4_V2_5_PHASE_VERIFIER_AUDIT_V1.json`
- `docs/transformation/PHASE31_4_V2_5_EVIDENCE_RECONCILIATION_REPORT.md`
