# Phase 31.4.3 — Supporting fixture and governed admission gate

`PHASE 31.4.3 — NOT PROMOTED`

P0=0; P1=4. B1, B2, B3 and B4 remain open. This task adds source evidence,
an expanded dependency census, regression tests and a guarded offline runner.
It does **not** deliver the requested complete successor architecture. No
ADR-0018, successor Product Policy, lifecycle spec V2, registry V2, closure V2,
fixture producer or operational admission schema has been issued.

Work began on 2026-09-08 and resumed on 2026-09-09, America/Costa_Rica.
The initial inspection and the resumed inspection preserved the existing
unrelated work. This report and its companions are append-only additions;
Phase 31.4.2 and its continuation addendum remain unchanged.

## Evidence and validation

- `docs/governance/evidence/PHASE31_4_3_SUPPORTING_CONTRACT_AUDIT_V1.json`:
  diagnostic evidence, exact source excerpts, reading ledger, native identity
  vectors, source metadata census, protected hashes and validation results.
- `backend/foundation/test_phase31_4_3_supporting_contract_audit.py`:
  16 additional offline source/integrity tests.
- `backend/foundation/verify_phase31_4_3_offline.py`: bounded offline runner.
- `docs/transformation/PHASE31_4_3_OFFLINE_CONTINUATION_PROMPT.md`:
  the single continuation prompt for the remaining offline work.

The selected run passed **103 tests, zero failures, errors or skips**. Django
4.2.22 `check` and `makemigrations --check --dry-run` passed with in-memory
auth/contenttypes/Foundation settings and a dummy database. In-memory Python
compilation covered 355 files. Normal project settings and logging were not
loaded. No PostgreSQL harness was executed. Operational tests: `NOT EXECUTED`.

Command, from `/home/felipe/proyectos/isosmart`:

```text
backend/.venv/bin/python -B backend/foundation/verify_phase31_4_3_offline.py
```

The runner builds the selected suite without test database setup, blocks
database access, sockets, subprocesses, the protected lifecycle entry points
and RuntimeAdoption resolver invocation. It preserves signatures for source
contract checks. Observed counters in this guarded run:

```text
database_attempts=0
network_attempts=0
resolver_invocations=0
lifecycle_attempts=0
subprocess_attempts=0
```

The 87 predecessor tests remain selected, with the same exclusions for
resolver-invoking and lifecycle tests. The 16 new tests prove the source facts
below and reject altered source witnesses and incompatible identity
substitutions. They do not prove a complete supporting fixture, all lifecycle
fields, exact authority freshness, live RLS, SQL execution parity, or complete
V2 acceptance. Those positive acceptance tests cannot pass against a package
that has not been completed.

## Exact initial Git output

Before repository discovery, the task ran `git status --short`, then
`git diff --check` in the required workspace. Status output:

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

`git diff --check` exited 2. Its exact output, expressed as a JSON string to
preserve the final space without adding another whitespace defect, was:

```json
"frontend/src/components/Layout/Sidebar.jsx:28: trailing whitespace.\n+    { name: t('navigation.risks'), path: '/risks', icon: AlertTriangle, group: 'control' }, \n"
```

The resumed status added only the task's temporary `.phase31_4_3_entry.json`.
That temporary file is removed after preservation verification. No reset,
stash, clean, staging, commit or normalization was performed.

## Reading boundary

`mandatory_reading_complete=false`. The evidence contains a per-file ledger:
21 files were fully read in this task; 82 files are included in the conservative
reading inventory. The remaining files are explicitly not certified complete.
Hashing, JSON parsing, model metadata extraction and predecessor reading claims
are not substituted for semantic reading.

Completed sources include AGENTS.md, ADR-0017, the complete Phase 31.3 lifecycle
JSON, the complete Phase 31.4.2 report/addendum, migrations 0011, 0017 and 0022,
the complete Phase 26 harness, AgentRun/catalog, Recommendation, preparation
and execution authorization, AgentDecision/human approval, controlled
Opportunity, Effectiveness, Signal/Proposal, release/resolver source, audit,
canonicalization, tenant context, and the two Phase 31.4.2 test files.

Mandatory unresolved reading includes the other historical reports and
diagnostic material, ADR-0013–0016, the remaining migrations, full models and
relevant Phase 28.3 paths, plus the other evidence/security/producer sources
listed in the ledger. The RuntimeAdoption resolver was read, never invoked.

## Additional B4 support dependencies

The predecessor non-null ORM traversal reached 23 model classes and 77 edges.
Adding source-established reverse/semantic roots and audit/event roots yields
**37 model classes, 105 non-null relations and 485 concrete columns**. The
evidence retains each column's declared type, nullability, table and relation
target. This is a source census, not a field taxonomy, a count of future rows,
an exact minimum graph, or a fixed-point live schema closure.

The 14 additional classes are AgentCatalogCurationAudit, AgentRunInput,
AgentRunRecommendation, Clause, DomainEvent, ImmutableAuditLog, KnowledgeLayer,
KnowledgeLayerRule, NormativeCurationAudit, RecommendationBasis,
RequirementControl, Standard, StandardEdition and TransactionalOutbox.

Concrete obligations exposed by the source:

1. `qms.foundation_0011_validate_run` requires both the exact AgentDefinition
   and ModelPolicy to be **published**. Merely creating draft catalog rows
   cannot produce a legal AgentRun. Their exact fixture-only creation and
   publication boundary must be addressed explicitly; an ID exception cannot
   bypass this constraint.
2. AgentRun requires at least one frozen AgentRunInput, enforced by a deferred
   SQL trigger. The input requires a running run, published StandardEdition,
   published KnowledgeLayerRule, exact RequirementControl and exact Evidence.
   The normative support catalog cannot be omitted from the graph.
3. AgentRun completion needs a separate AgentRunRecommendation row. The SQL
   link validator compares both directions of the input/basis set difference.
   A Recommendation FK alone does not establish exact provenance.
4. `prepare_action_plan` loads AgentDecision before creating the ActionPlan.
   The chain needs an AgentDecision **before** plan/dry run; the subsequent
   human Approval is a separate row/operation. The abbreviated requested
   sequence must not be implemented by creating its first AgentDecision only
   after the dry run.
5. The new inaccessible producer owner needs explicit table privileges **and**
   applicable tenant RLS policies. Migration 0011 policies name specific
   existing roles; grants alone do not establish access for a new NOINHERIT,
   NOBYPASSRLS owner. The full table-by-table security contract remains absent.
6. `trusted_tenant_context` rejects an existing outer transaction. An outer
   transaction around unmodified support service calls is not a general
   precommit insertion point. The separately authorized fixture producer must
   specify transaction composition and equivalent validation for each exact
   operation, without modifying protected services.

The existing AgentRun implementation explicitly records synthetic provenance
without provider/tool calls. That supports investigating the distinction
between isolated fixture creation and operational runtime changes. It does
not itself authorize exact synthetic catalog publication, define its material,
or satisfy the requested no-promotion boundary. No categorical impossibility
of a separately governed fixture is claimed.

## Audit types and identity exceptions

The supporting catalog creates `governance.curation_audit` through
AgentCatalogCurationAudit. It is distinct from both `normative.curation_audit`
and `audit.immutable_audit_log`. Catalog create/publish methods call the catalog
curation writer; they do not create DomainEvent/TransactionalOutbox rows.
The successor must record this native absence explicitly, and separately
authorize any additional outer event/audit rather than inventing native rows.
Publication/Activation additionally use their dedicated 0022 governance Audit.

The generic immutable Audit writer calls SQL `audit.append_immutable_audit`,
which allocates its identity with `uuidv7()`. A fixture identity replacement
must preserve tenant checks, metadata restrictions, advisory stream lock,
sequence, predecessor hash, exact timestamp rendering and entry hash. It
cannot be implemented by a new `audit_id` argument to the existing Python
writer, which has none. Every actual operation needs its own audit identity;
one blanket exception for all support rows remains insufficient.

No such producer or exception was implemented or authorized here. ADR-0017
remains byte-identical and limited to its seven Application output positions.

## Native release identity tension

Section 26 of the submitted request says to create UUIDv5 identity for every
deterministic nonfresh future row. Frozen 0022 instead computes child IDs from
MD5 of `artifact_uuid + ':' + suffix`, forcing the version nibble to 4 and the
variant nibble to 8. It does not use UUIDv5. These exact historical values
were independently recomputed offline:

| Operation child | Native identity |
|---|---|
| Publication Event | `0ff9868e-a847-4624-862c-d93ddb9c11e2` |
| Publication Outbox | `37816380-7022-43b2-8d4a-c57346e5f7f6` |
| Publication governance Audit | `5f33e3ba-abba-4b0e-8a43-bb60cc67a5cc` |
| Publication curation Audit | `5fa5038d-3042-481f-8162-e1144eebc815` |
| Activation Event | `237fd48c-59bd-4b25-8521-4876fe9fc1a1` |
| Activation Outbox | `68df6cc0-e04a-4693-80ab-07182c81bec1` |
| Activation governance Audit | `b51984ce-3391-4597-8592-6539737b2ee9` |

The old lifecycle JSON already distinguishes `release_child_id` from UUIDv5
allocation. Preserving this native rule as an explicit exception is the
proposed resolution; it has not been treated as an answer to the pending
clarification. Preserving native behavior takes precedence over silently
rewriting 0022. This finding is included in B4's complete identity/producer
integration blocker, not counted as an extra P1.

Also, native Claim and Publication/Activation are separate rows whose UUIDs
are intentionally equal. A row inventory needs `(qualified_table, primary_key)`
identity and explicit native cross-table reuse. A flat UUID uniqueness check
would reject the native graph incorrectly. Historical repeated references to
the same row must likewise be distinguished from actual identity collisions.

These seven vectors are source-derived historical identity observations, not
new operational row allocations. No exhaustive future UUID collision pass is
claimed, since the complete future row set is still missing.

## Effectiveness and Signal

Migration 0017 binds the succeeded `controlled_opportunity` execution, exact
`opportunity_deferred` Receipt, plan, authorization, AgentDecision,
Recommendation and Opportunity revisions. `due_at` must be strictly after
the resulting revision's `created_at`; `assessed_at >= due_at`. The Receipt
must explicitly deny claiming effectiveness.

Human-review assessment requires no MeasurementDefinition; measurement-derived
assessment requires one. Revision 1 requires null predecessor and correction
reason. A correction needs a predecessor, revision increment, reason, supersede
permission and exact same execution provenance. At least one exact Evidence
revision/link is required by deferred SQL validation. These source rules do
not establish exact fixture criteria, findings, evidence content, due-time
derivation or a successful outcome evaluation.

LearningSignal must select an eligible current leaf with its complete linear
Effectiveness history and derivation timestamp no earlier than the selected
row's creation. Synthetic/normative/production/automatic-learning flags,
findings and rationale are **not** LearningSignal model columns. They belong
in a separately retained semantic envelope. No such fields were added to the
model, and no successful business result was predeclared.

## Native material versus governed admission

The native formulas remain:

```text
Publication = SHA256(UTF8(rule_uuid + ':' + expected_selected_hash + ':' + reason))
Activation = SHA256(UTF8(publication_uuid + ':' + expected_selected_hash + ':'
             + (predecessor_uuid or 'ROOT') + ':' + compatibility_hash + ':' + reason))
```

They do not bind the full actor, authority, policy, trace, caller key, release
or closure envelope. Native same-material replay cannot prove that envelope
matches. A new attempt's fresh authority to retrieve/reconcile a prior response
must be retained separately from the immutable original operation provenance.
The separate admission/precommit producer, canonical schemas, atomic retention
and replay comparison are still incomplete; no source test is a replacement.

Root bootstrap also needs a distinct admission contract. Requiring its own
future Application Receipt as a root-publication prerequisite would create
a root → Application → root causal cycle. The candidate Publication envelope's
Receipt/parity requirements cannot be copied indiscriminately onto bootstrap.

B2 and B3 remain postpublication observations. The required future order is:

```text
native Publication -> Publication graph checkpoint -> compatibility evidence
-> release evidence -> final Publication closure -> Activation
```

The checkpoint must exclude B2/B3, final closure and its own digest. Release
must not use RuntimeAdoption configuration fields. No exact checkpoint member
set, complete compatibility/release schema, or integrated producer is approved.

## Residual blockers and requested gates

| Blocker | Exact remaining work |
|---|---|
| B1 | Complete governed root draft/publication producer; exact privileges, actor/authority/capability, per-row events/audits; eleven frozen non-time values; authentic PostgreSQL timestamp/render profile; two independent committed rereads and target artifact integrated with every consumer. No predicted target hash. |
| B2 | Complete typed compatibility schema and independent read-only producer for evidence `37d3d0bc-4387-581a-a627-f02a011250d1`, exact observations/assertions and Freeze 7c retention. |
| B3 | Exact Publication checkpoint membership; typed release schema and producer for `981e1753-dcd1-5f8d-8b10-49bfaed5eafb`; nonrecursive final Publication closure and export/live comparison before Activation. |
| B4 | Complete supporting graph and business material; catalog/bootstrap and input/output links above; exact per-row identity exceptions and RLS grants/policies; native-ID wording resolution; event/audit inventory; criteria and outcome rule; Proposal/Delta/Review/Decision/Authorization material; original/replay authority separation; full field taxonomy, producer matrix, semantic registry and fixed-point closure. |

Mandatory reading and complete downstream governed envelopes are additional
cross-cutting conditions within these unresolved gate obligations. The new
findings refine the four retained P1 groups; they do not close any group.

```text
mandatory_reading_complete=false
B1_closed=false
B2_closed=false
B3_closed=false
B4_closed=false
execution_ready_v2_adopted=false
model_b_adopted=false
native_governed_contract_separation_complete=false
publication_governed_admission_complete=false
activation_governed_admission_complete=false
replay_provenance_contract_complete=false
root_bootstrap_complete=false
root_target_artifact_complete=false
supporting_graph_complete=false
supporting_fixture_producer_complete=false
compatibility_schema_complete=false
compatibility_producer_complete=false
release_schema_complete=false
release_producer_complete=false
publication_checkpoint_complete=false
taxonomy_covers_every_lifecycle_field=false
producer_matrix_covers_every_created_row=false
ADR0017_preserved=true
ADR0018_created=false
successor_policy_created=false
lifecycle_spec_v2_complete=false
registry_v2_complete=false
closure_v2_complete=false
migration_0024_absent=true
RuntimeAdoption=false
database_created=false
P0=0
P1=4
```

`unknown_binding_count` is not measured over a complete lifecycle universe;
the diagnostic records null with a reason, not a fabricated zero. V2 cycle
detection, exhaustive row production, closure reachability and a complete
V2 fixed-hash audit are not established. Every fixed digest in this diagnostic
is classified as a source-bytes hash and checked against the corresponding
existing file; that narrower result does not certify future V2 digests.

## Preservation and zero effects

The captured baseline contains 14,357 preexisting regular files. All are
byte-compared after the work; 223 protected source/governance files have
individual retained hashes. All 23 numbered Foundation migrations remain
byte-identical, and migration 0024 is absent. Source artifacts, ADR-0013–0017,
Phase 29 evidence, historical Phase 31 reports/diagnostics, and the Phase 31.3
five-artifact package are preserved. New files are separately checked for
whitespace because ordinary `git diff` omits untracked additions. Exact final
Git output and preservation results are retained in the diagnostic JSON.

Phase 29 remains `HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE` /
`RETENTION_CLOSURE_BREACH`. Publication
`e97576de-d4ef-520d-8592-d376ed401221` and missing audit
`12d811ab-c3b4-4615-8972-75008a36e327` were not used operationally or reconstructed.
Old B1/B2/B3 numeric expectations remain historical, superseded execution
inputs; no new live target, Delta, authority, compatibility or release digest
was numerically prebound.

```text
database effects=0
PostgreSQL effects=0
support fixture execution effects=0
Opportunity execution effects=0
Effectiveness effects=0
LearningSignal effects=0
Proposal effects=0
Application effects=0
Publication effects=0
Activation effects=0
RuntimeAdoption effects=0
resolver invocation=0
runtime effects=0
production effects=0
staging effects=0
shared DB effects=0
real AdminApps effects=0
external API effects=0
normative effects=0
automatic learning effects=0
external business effects=0
Phase29 reconstruction effects=0
```

`PHASE 31.4.3 — NOT PROMOTED`

Only the linked offline continuation is supplied. No PostgreSQL retry or
Phase 32 authorization follows from this report.
