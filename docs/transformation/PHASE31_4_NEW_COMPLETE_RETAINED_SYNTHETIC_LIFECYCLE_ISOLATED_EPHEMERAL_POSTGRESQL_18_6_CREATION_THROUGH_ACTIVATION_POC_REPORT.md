# ISO SMART AI — Phase 31.4 creation-through-Activation POC entry report

- Verdict: **PHASE 31.4 — NOT PROMOTED**
- Report schema: `phase31.4-precreation-blocker-report/v1`.
- Date: 2026-09-04; workspace: `/home/felipe/proyectos/isosmart`.
- Provenance: fresh offline inspection, byte/hash verification and restricted regression execution during this task.
- Execution boundary reached: precreation input validation. No PostgreSQL database was created.

## Blocking finding B1 — exact full-row target hash lacks timestamp bindings

The frozen package passes byte-integrity verification but does not supply a
reproducible complete root-row preimage for its mandatory Application target
hash. This is an execution-readiness **P1**, not a checksum mismatch or an
observed PostgreSQL rejection.

The lifecycle specification fixes root `bc5f4f17-294d-5abd-b27b-2d296921ffdf`
and `foundation_0021_target_hash`:

```text
dbaa2e4eff3c980522a916d0cf2f10127e39f0af8dbfdacb469ac3015d8d87db
```

The same value is inside the immutable canonical Delta, whose fixed hash is
`06f75de72e2a2ded515c223a1c62df6ab3780ebfe1ed0ccca71a22a222071c9e`.
However, `lineage.root` and `support_graph.root_creation` contain neither a
complete root-row snapshot nor exact `created_at` / `published_at` values.
The package's fresh-slot policy permits fresh transaction timestamps, but
does not define a binding that makes those values produce the preallocated
full-row hash.

The unchanged implementation makes those omitted values material:

1. Migration 0009, lines 34–61, includes both timestamp columns;
   `created_at` is non-null with `statement_timestamp()` as its default, and a
   published root requires non-null `published_at`.
2. Migration 0021, lines 293–299, hashes the canonical envelope of
   **`to_jsonb(r)`**, including the entire persisted row and both timestamps.
3. Migration 0021, lines 449–452, recomputes that hash and compares it with
   the authorized target hash, also comparing the full Proposal snapshot.
4. Migration 0023 replaces only two source grammar checks. It does not change
   the row hash or timestamp semantics.

The distinct selected-material root hash
`3421457f44586a28cf4b6a242cb2f25929e3eae8689de214292639fcb89be3af`
was independently recomputed successfully. It excludes the timestamps and
cannot substitute for the 0021 full-row hash. Candidate material, substantive
fingerprint, lifecycle, source, Delta and idempotency hashes likewise match;
none supplies the missing root-row preimage.

No missing dates were guessed, no hash was silently replaced, and no adapter
was installed to bypass that comparison. ADR-0017 permits only the bounded
Application output-ID difference; it does not authorize a different target
hash algorithm, Delta or timestamp contract. Product Policy's Change Control
requires an append-only successor gate for corrections.

This finding stops the operational path before environment creation. It does
not prove a live rejection, claim that SHA-256 has no possible preimage, or
claim Application parity. All such PostgreSQL observations remain **NOT EXECUTED**.

## Entry authorization, frozen inputs and source

Both required promoted verdict strings were found. The finalized reports are
frozen as execution inputs with these observed file-byte hashes:

| Report | SHA-256 |
|---|---|
| Phase 31.3 | `fc5f16abab801570aefd313b87cae1805f3e5067e73d01acebebce9519724a8f` |
| Phase 31.3.1 | `5df6ba154a49d3aede4938bdcf17ff11d524e4d75526ba96b969df9ac6a3b6da` |

| Frozen input | Expected = observed SHA-256 |
|---|---|
| Product Policy | `44535b47bda30a4319903d8b9f10be04890b4d9085c8955d57916f3616d9588d` |
| Exact source bytes | `e458cd0bb7eb11f96ce8723b0ab4dea97e4ca60b0e47a6f7e1fb1f38cef66d6b` |
| Lifecycle specification | `683f7c83ff3e3e16733d63288d317f8b3a14fe9e5bfaf2e86b0cf2e86b6ab6ca` |
| Semantic registry | `d5e1960801772af74d491c9c6f69a877b79f1e26b937701cf1a239114b37bf1c` |
| Expected closure | `d3455bc64957ef1aab5f618e552d9276bd6fd60e0b1ce2e7a8068e5c14c8917a` |
| ADR-0017 | `82501ef34edc6d7e76e0971d3d2607c58f229a1dd4dd26696dd227fb7e994edb` |
| Sorted migrations 0001–0023 | `cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc` |

All 23 migration files remain unchanged; 0024 is absent. The migration digest
uses sorted repository-relative path + NUL + file-byte SHA-256 + LF.
The evidence JSON retains every individual migration hash.

The source was read as exact bytes and not rewritten. Its frozen classification
remains synthetic=true, authoritative=false, normative=false, licensed=false,
test_only=true, production_allowed=false, certifiable=false and
phase29_continuity_claim=false.

## Input-package review and limits

Read `AGENTS.md`, ADR-0013–0017 and ADR-0003, the Product Policy, exact source,
and the machine-readable lifecycle/registry/closure contracts. Reviewed the
relevant Phase 31.3/31.3.1 report sections, Application service, 0021 target
hash/validation/evidence paths, complete 0023 grammar replacement, 0009 row
schema, 0022 hash definitions, Phase 28.3 creation/identity path and retained
evidence canonicalization helpers. Source excerpts and hashes are retained.

**Complete mandatory semantic reading: NOT COMPLETED.** The task stopped at
the discovered precreation blocker before finishing all historical report
sections, the complete 0021/0022 files, Phase 26 and Phase 28.3 harnesses, full
release/evidence/eventing/immutable-audit/models/security implementation and
resolver implementation. Full-byte inventories, imports, compilation and
tests do not substitute for that reading. A later execution attempt must
complete the entire mandatory package before creating PostgreSQL.

## Initial repository hygiene and procedural deviation

The first repository command after processing the attachment was
`git status --short`, before opening `AGENTS.md` or editing repository content.
Exact output:

```text
 M backend/backend/settings.py
 M backend/integration/assistant_memory_views.py
 M backend/integration/serializers.py
 M backend/integration/tests.py
 M backend/integration/views.py
 M backend/leadership/serializers.py
 M backend/leadership/views.py
 M backend/test_default.sqlite3
 M frontend/src/components/Assistant/VirtualAssistantPanel.jsx
 M frontend/src/components/Auth/OnboardingGuard.jsx
 M frontend/src/components/Common/CrudEmptyState.jsx
 M frontend/src/components/Common/CrudErrorBanner.jsx
 M frontend/src/components/Common/CrudPageHeader.jsx
 M frontend/src/components/Layout/Header.jsx
 M frontend/src/components/Layout/Layout.jsx
 M frontend/src/components/Layout/Sidebar.jsx
 M frontend/src/context/I18nContext.jsx
 M frontend/src/features/improvement/pages/ImprovementCorrectiveActionsPage.jsx
 M frontend/src/features/improvement/pages/ImprovementNonconformitiesPage.jsx
 M frontend/src/features/operations/pages/CustomerRequirementsPage.jsx
 M frontend/src/index.css
 M frontend/src/pages/ForgotPasswordPage.jsx
 M frontend/tests/e2e/assistant-runtime.spec.js
 M frontend/vite.config.js
?? AGENTS.md
?? backend/foundation/
?? backend/leadership/tests.py
?? backend/logs/
?? docs/adr/
?? docs/governance/
?? docs/operations/
?? docs/transformation/
?? frontend/tests/e2e/onboarding-guard-runtime.spec.js
```

Before the attachment result was processed, the initial tool batch also ran
a path-only discovery from `/home/felipe/proyectos`. That enumerated filenames
in sibling repositories, contrary to the exclusive-workspace instruction and
before the required repository status. This procedural deviation is explicitly
recorded; passing tests do not erase it. No sibling file content was opened,
modified, executed or used as implementation input. All subsequent work used
the exclusive `isosmart` workspace. The broader consumer-inspection guideline
in `AGENTS.md` did not override the user's explicit sibling prohibition.

The initial targeted diff check over docs/governance, docs/transformation and
backend passed with empty output. Final full `git diff --check` exits 2 solely
for the known pre-existing Sidebar line 28 trailing whitespace; the exclusion
check passes. That file and all other existing work are byte-preserved.
An inventory captured after read-only preflight and before deliverable edits
contains 14,349 existing regular tracked/nonignored files, excluding Python
caches. Every inventoried file matched at final verification. Ignored files
were not part of that inventory. No reset, stash, clean, stage, commit or
unrelated formatting occurred.

## Environment and exact experiment

Local tooling observation: Podman 5.8.2 and cached
`docker.io/library/postgres:18.6`, image ID
`a6638641707cdf047e5d5c2781f437e2e809323cab22c70b280be8389fbb7878`.
Only version/image metadata commands ran; no pull or server startup occurred.
A cached tag is not a live server-version attestation.

Container ID/name, temporary port, database name, roles, volume, live server
version, creation/destruction commands, credentials and sockets: **NOT CREATED /
NOT EXECUTED**. No host/shared/DEV/QA/production/staging PostgreSQL was used.
No migration was applied and no live catalog, ACL or RLS state was inspected.

The authorized experiment remains
`a3f8fd64-af24-5b31-977a-bcaf8146c563`, namespace
`05611a8a-f662-5b7f-ad24-c4df48d573ec`; source
`72d038c3-4ee5-5d40-a75b-398133dbed00`; root/lineage
`bc5f4f17-294d-5abd-b27b-2d296921ffdf`; candidate
`a55716fa-63c7-54eb-bda2-9c9666613b1a`; Receipt
`b35d11e1-6848-50b2-b760-dd09d38f0acb`; Publication
`cf4db0d2-a312-5a44-91cf-6e14f5cd600e`; Activation
`676ad5e4-e167-5336-93ae-5a9f1d4388d3`. These are frozen input references,
not evidence of created rows. No retained lifecycle identity was invented.

Phase 29 remains historical-only:
Publication `e97576de-d4ef-520d-8592-d376ed401221`, candidate
`01a0682b-dfc8-7b49-a601-f9bda29a70a5`, missing audit
`12d811ab-c3b4-4615-8972-75008a36e327`, classification
`HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE`, incident
`RETENTION_CLOSURE_BREACH`. No graph was imported, reconstructed, rerun or repaired.
Existing offline evidence regressions do not execute that historical lifecycle.

## Fresh checks and their boundaries

| Category | Fresh result | Limit |
|---|---|---|
| Required artifact byte hashes | 6/6 MATCH | Integrity only |
| Migration inventory | 23/23 unchanged; 0024 absent | No live migration state |
| Canonical recomputations | 12/12 MATCH | Excludes unbound root full-row hash |
| Foundation permitted offline subset | 135 executed, 0 failures, 0 errors, 0 skips | 136 discovered; one excluded before execution |
| Entire Foundation suite | NOT EXECUTED | Resolver prohibition prevents running one test |
| Django check | 4.2.22; zero issues | auth/contenttypes/Foundation only; dummy DB |
| makemigrations --check --dry-run | PASS; no changes | Same restricted installed-app scope |
| Python compilation | 350 backend source files PASS | In-memory compile; excludes hidden/vendor paths |
| Full backend regression | NOT EXECUTED | No permitted migrated DB established |
| PostgreSQL/adapter/rollback/concurrency/hostile/ACL/reconciliation | NOT EXECUTED | B1 prevents operational entry |
| Live closure/export/re-read/offline lifecycle verifier | NOT EXECUTED | No graph or export exists |
| Eleven closure tamper-negative cases | NOT EXECUTED | No retained live lifecycle package exists |

The twelve recomputations cover source bytes, source manifest, Delta, candidate
full material, substantive fingerprint, lifecycle, root selected material,
both locators and three idempotency keys. Counts are separate categories and
are not added into a grand total.

The excluded test is
`foundation.test_knowledge_rule_release.InertKnowledgeRuleReleaseContractTests.test_resolver_rejects_selector_and_fallback_tokens_before_database_access`.
It calls the RuntimeAdoption resolver even though it expects invalid-selector
denials. User section 46 forbids resolver invocation; it was therefore omitted,
not mocked into a passing result. Other existing signature/source checks ran.
No complete operational selector or hostile matrix is claimed.

Validation used `backend/.venv` with in-memory Django settings, a dummy database
backend, normal file logging disabled and network connection attempts denied.
It did not load normal backend settings or connect to the existing SQLite
files. `.venv312` was not used. Raw test output is retained in the evidence JSON.

## Lifecycle, retention, teardown and zero effects

```text
CREATED=false
APPLICATION_GOVERNED=false
PUBLISHED=false
ACTIVATED=false
RUNTIME_ADOPTED=false
RUNTIME_EFFECTIVE=false
database_reconstructed=false
retention_closure_complete=false
export_matches_live_graph=NOT EXECUTED
reconstruction_required=NOT EVALUATED
adapter_installed=false
adapter_removed=NOT APPLICABLE
normal_teardown_authorized=false
normal_teardown_executed=false
```

These describe this task's absence of lifecycle execution. They are not a
database query or an ambiguous-COMMIT reconciliation result. No environment
exists to preserve or tear down; no dual-control override was invoked. Temporary
offline validation files were removed after verification; that cleanup is not
database teardown and does not destroy lifecycle evidence.

Complete lifecycle/Publication/Activation manifests, pre-teardown disposition,
teardown proof, post-teardown verification and adapter-equivalence observations
were **NOT CREATED**, because their live prerequisites never occurred. The
precreation evidence document is explicitly not any of those artifacts.

Application curation audit `ff75b1d0-a2ea-5eae-9064-b9114496047a`, Publication
curation audit `5fa5038d-3042-481f-8162-e1144eebc815`, and root curation audit
`805875c2-6505-5b82-ad41-40c2519293d2` remain mandatory future full eight-field
rows. No UUID-only placeholder was accepted as live evidence.

This task produced zero production, staging, shared database, real AdminApps,
MedSupplier operational, external API, deployment, RuntimeAdoption, runtime
cutover, normative, automatic-learning and external business effects. No
adoption authority or resolver was invoked. RuntimeAdoption row/event/Outbox/
Audit writes are zero by non-execution, not live count observations. Protected
runtime, recommendation, release/resolver, settings, governance and migration
files have matching before/after hashes in the evidence inventory. No runtime
configuration, selector, ModelPolicy, AgentDefinition or autonomy was changed.

## Evidence artifacts and reproduction

New deliverables are this report, the diagnostic evidence JSON, and a detached
SHA-256 ledger. No runtime implementation, adapter or migration was added.

- Evidence: `docs/governance/evidence/PHASE31_4_PRECREATION_BLOCKER_EVIDENCE_V1.json`.
  File-byte SHA-256: `b8490b2bb2cd059b015be7a97731dad009b45018fa822278b61daabb886fbf70`.
- Ledger: `docs/governance/evidence/PHASE31_4_PREFLIGHT_ARTIFACTS_V1.sha256`.
  It records the finalized report and evidence file hashes; its own hash is
  emitted by final verification, avoiding recursive self-hashing.
- Evidence canonical hash: recompute SHA-256 of sorted compact UTF-8 JSON after
  removing only `canonical_material_sha256`, then compare that field.

The JSON retains the original promoted hash-function source, missing bindings,
exact input/report/migration/protected-file hashes, initial status, raw offline
test output, execution limits and zero-effect declarations. Expected fixture
values remain explicitly labeled offline input observations.

To reproduce B1 without any database: load the frozen lifecycle JSON; inspect
`lineage.root` and `support_graph.root_creation` for exact timestamps/full-row
material; compare with migration 0009's non-null timestamp/publication contract,
0021's complete `to_jsonb(r)` hash and exact target revalidation, and 0023's
grammar-only change. Do not generate dates, replace the target hash or convert
this source inspection into a claimed PostgreSQL test.

## P0/P1, residual limits and verdict

Identified operational P0 violations: 0. Identified execution-readiness P1
blockers: 1 (B1). The separately recorded initial workspace-discovery deviation
remains part of this task's audit trail. All unexecuted operational acceptance
gates remain unproved; their absence is not a pass or a warning downgraded from
a blocker. Further issues may be found when the full mandatory review is
completed. This report changes no frozen architecture or historical verdict.

**PHASE 31.4 — NOT PROMOTED**. No roadmap advancement or Phase 32 authorization.

## Exactly one blocker-specific continuation

```text
NEXT_CODEX_PROMPT

ISO SMART AI — PHASE 31.4 BLOCKER-SPECIFIC CONTINUATION — ROOT FULL-ROW HASH AND FRESH TIMESTAMP CONTRACT — DESIGN/DIAGNOSTIC ONLY

Work exclusively in /home/felipe/proyectos/isosmart. Run git status --short before repository discovery or reading, record exact output, then targeted git diff --check. Do not enumerate, inspect, modify or execute against sibling repositories. Preserve all unrelated work, including frontend/src/components/Layout/Sidebar.jsx:28. No reset, stash, clean, stage or commit.

Read the Phase 31.4 report and PHASE31_4_PRECREATION_BLOCKER_EVIDENCE_V1.json, verify their detached SHA-256 ledger and the evidence's canonical hash, then complete the entire mandatory input-package reading from the Phase 31.4 request. Preserve promoted Phase 31.3/31.3.1 reports, ADR-0017, policy, source, lifecycle JSON, semantic registry and closure specification unchanged. Verify the six frozen hashes recorded in the Phase 31.4 report, Phase 31.3.1 report hash 5df6ba154a49d3aede4938bdcf17ff11d524e4d75526ba96b969df9ac6a3b6da, migration-set hash cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc, and migration 0024 absence.

Resolve B1 only through evidence and an explicit append-only design/authorization correction if required. The frozen root bc5f4f17-294d-5abd-b27b-2d296921ffdf must be published at Application; migration 0021 hashes its complete row including created_at and published_at. Its fixed target hash dbaa2e4eff3c980522a916d0cf2f10127e39f0af8dbfdacb469ac3015d8d87db is embedded in the frozen Delta, yet no exact timestamp preimage or complete root-row material is supplied. Determine whether any already-approved input supplies the missing binding; do not guess timestamps, brute-force a preimage, replace the target hash with the 0022 selected-material hash, change the Delta silently or weaken the promoted comparison. If a correction is needed, document a proposed successor contract with exact canonical full-row/timestamp semantics, freshness rules, dependent hash/Delta/authorization impacts and test vectors; create a successor ADR only if the decision is architectural. Do not overwrite old artifacts or claim a proposed successor is operationally approved.

Keep the exact experiment and all lifecycle IDs unchanged unless a separately approved successor gate explicitly authorizes a replacement; this diagnostic task grants no replacement authority. Review remaining required identity/material bindings as part of input completeness, without inventing retained rows or claiming PostgreSQL parity. Preserve the sole ADR-0017 output-ID exception. Record the initial path-discovery deviation and prevent recurrence by setting the exact repository working directory before all discovery.

Do not create PostgreSQL, install an adapter, execute Application/Publication/Activation, apply migrations, invoke RuntimeAdoption or its resolver, contact real AdminApps or external services, deploy, change runtime or reconstruct Phase 29. Phase 29 remains HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE with RETENTION_CLOSURE_BREACH. Run only safe offline checks with backend/.venv Django 4.2.22; explicitly exclude resolver-invoking tests and report every unexecuted criterion. Return an append-only blocker-resolution/design report, exact hashes, remaining P0/P1 and exactly one continuation prompt. Do not advance to Phase 32. A future operational Phase 31.4 attempt requires explicit accepted input bindings and every original Application parity, lifecycle, retention, teardown and zero-effect gate.
```

| Component/test | State | Evidence | Risk/next action |
|---|---|---|---|
| 1–5 Verdict, entry, initial status, hashes, input review | NOT PROMOTED; byte hashes MATCH; reading incomplete | Report and diagnostic JSON | Resolve B1 and finish mandatory review |
| 6–7 PostgreSQL environment and migration state | NOT EXECUTED | Image metadata only; 23 frozen files | No live server or catalog attestation |
| 8–10 Exact experiment, source and support/root creation | Source verified; creation NOT EXECUTED | Frozen IDs/bytes; missing root timestamps | No material substitution |
| 11–18 Adapter, owner/ACL, SECURITY DEFINER, reference/adapter trials, raw parity, bijection, equivalence | NOT EXECUTED | No installed functions or parity output | Publication blocked |
| 19–25 Application authority/SOD/transaction/rollback/concurrency/TOCTOU/exact candidate | NOT EXECUTED | 13 rollback points unexecuted; candidate absent | All gates still required |
| 26–34 Publication authority/curation audit/transaction/event/Outbox/Audit/rollback/concurrency/reconciliation/closure/export comparison | NOT EXECUTED | No Publication graph or full audit row | Activation blocked |
| 35–43 Activation authority/SOD/null predecessor/transaction/event/Outbox/Audit/rollback/concurrency/TOCTOU/ambiguous commit | NOT EXECUTED | 12 rollback points unexecuted; no Activation | No commit inference |
| 44–45 Repair restrictions and hostile tests | No repair; tests NOT EXECUTED | No lifecycle execution | No automatic repair or claim theft |
| 46–53 Full closure/schema snapshot/registry/canonical members/curation Audits/fixed point/re-read/export comparison | NOT EXECUTED; registry bytes MATCH | Diagnostic evidence is not closure evidence | Do not fabricate manifests |
| 54–57 RuntimeAdoption, runtime, learning and normative invariance | Zero task effects; protected bytes unchanged | Before/after inventory | No live-count proof claimed |
| 58–62 Pre-teardown state/authorization/teardown/adapter removal/post-teardown verification | NOT EXECUTED / NOT APPLICABLE | Environment never created | No teardown override |
| 63 Tamper-negative closure tests | NOT EXECUTED | No retained live package | Do not substitute input hash checks |
| 64 Evidence artifact hashes | PASS | Detached SHA-256 ledger and canonical field | Preserve finalized artifacts |
| 65–66 Regressions and Django | 135 permitted tests PASS; 350 files compile; Django 4.2.22 checks PASS | Raw results in JSON | Full Foundation/backend explicitly not passed |
| 67–69 Migration/source/governance/runtime hashes and Git hygiene | Frozen files unchanged; known whitespace preserved | 14,349-file comparison; final status matches entry after temporary cleanup | Initial scope deviation recorded |
| 70 External effects | Zero operational effects | No DB/API/deployment operations | Sibling filename discovery separately disclosed |
| 71–73 P0/P1, residual risks and final verdict | P1 B1 remains; NOT PROMOTED | Missing exact root-row hash bindings | No Phase 32 advancement |
| 74 Continuation | One prompt supplied | Blocker-specific design/diagnostic prompt above | No operational authorization inferred |
