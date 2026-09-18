# Phase 20 — Effectiveness Operational Validation + Governed Learning Boundary Design Gate

**Date:** 2026-08-24

**PostgreSQL:** 18.6 official image, isolated ephemeral lifecycle

**Final run:** `20260824T224159Z_373ddf`
**Verdict:** **PROMOTED**

## 1. Entry state and scope

Phase 19 entered PROMOTED at 172/172 backend and 74/74 foundation tests. Phase
20 adds operational validation, a tenant-safe internal review read model, three
contract tests, a runbook addendum and non-normative
`governed-learning-policy/v1`. It adds no migration 0018, LearningSignal or
LearningProposal runtime, endpoint, deployment, external workflow, automatic
learning, compensation or second action. Migrations 0001–0017 remain frozen.

## 2. Operational Effectiveness validation

PostgreSQL proved two separate app connections racing from the same predecessor:
exactly one correction committed; the other received a stale/conflict failure.
The predecessor row lock plus one-to-one/unique predecessor rule yielded one leaf
and no fork. A retained `v1 -> v2 -> v3 -> v4` chain reconstructed every outcome,
actor snapshot, due time, execution chain and exact Evidence link.

Authority is evaluated at command time. Revoking access after a historical check
did not rewrite its actor/authority provenance; the same revoked authority was
denied a new correction before database mutation. UserProjection remains
identity provenance, never authority.

Later Evidence or MeasurementDefinition revisions do not alter frozen IDs,
revisions and hashes on historical checks. A valid change requires a new complete
correction. A stale predecessor cannot be retried blindly.

## 3. Due, overdue, unknown and inconclusive

The read model classifies a trusted plan with no check as `due` at `as_of ==
due_at` and `overdue` only when `as_of > due_at`. It performs no mutation, creates
no EffectivenessCheck, invents no SLA and triggers no workflow.

`unknown` records only an evidenced blocker that prevented reliable assessment.
It is not failed execution, ineffective, compensation, Recommendation or incident.
`inconclusive` records a completed assessment without reliable binary conclusion;
it remains distinct from all other outcomes. Both require policy-v1 reason and
explanation and produce no downstream action.

## 4. Review queue contract

Input is server-authorized `TrustedTenantIdentity`, exact Organization, trusted
`GovernedEffectivenessPlan` values and timezone-aware `as_of`; there is no body,
query or header tenant authority. Output is sanitized and ordered: category,
execution/Organization, due time, current check/revision, correction count, actor
reference and trace. Only the current leaf drives unknown/inconclusive attention;
superseded rows remain history. Queue membership confers no record/supersede
permission; the command independently resolves current AdminApps authority.

## 5. Learning source reconciliation

All ten sources were read directly, including DOCX XML and XLSX workbook content.

| Source | Learning concept | Field/relation | Semantics | Implement? | Rationale |
|---|---|---|---|---|---|
| Integrated DOCX | universal runtime step 12 | Effectiveness -> governed learning | learn from results with governed changes | design only | names boundary, not authority/schema |
| DOCX/XLSX/JSON | Learning Optimizer | transversal agent capability | not ISO 9001 clause 10.3 | no | catalog capability, no optimizer contract |
| Mermaid/Draw.io | Execute -> Effectiveness -> Memory | runtime nodes/edges | separates execution, measurement and memory | no | topology does not authorize mutation |
| DDL | EffectivenessCheck | subject/method/due/result/evidence | downstream effectiveness record | already Phase 19 | sketch lacks learning link |
| DDL/OpenAPI | LearningPath/QuizAttempt/ConceptMastery | onboarding learning | human ISO foundation education | no Phase 20 | unrelated to agent optimization |
| DOCX | feedback | ISO 10002 guidance | learn from customer feedback | no | QMS guidance, not automatic model feedback |
| DOCX/XLSX/JSON | Recommendation explainability | model/rule/prompt/evidence versions | provenance required | future reference | supports explainable proposal |
| DDL/DOCX | AgentDefinition/model policy | version/model/rule metadata | governed runtime ceiling/provenance | no mutation | no update authority specified |
| DOCX/LEEME/network | Knowledge Layers | versioned invisible guidance | explainable, non-certifiable unless pack | no mutation | global curation boundary |
| All sources | cross-tenant learning | none explicit | no anonymized aggregate contract | defer | inventing it would be unsafe |

The sources support governed learning as a future stage and exact provenance, but
do not define LearningSignal, LearningProposal, aggregation/scoring, approval
authority, automatic prompt/model changes or cross-tenant learning. Product Policy
therefore closes safety boundaries without presenting them as ISO requirements.

## 6. Conceptual LearningSignal

`LearningSignal` is design terminology for immutable, tenant/Organization-scoped,
redacted evidence derived from the current EffectivenessCheck leaf. It references
the exact check lineage, ActionExecution/Receipt/Plan/Authorization,
Recommendation/Basis, AgentRun, AgentDefinition/ModelPolicy versions,
RequirementControl, KnowledgeLayerRule, Evidence revisions, policy/derivation
version and trace where relevant. It is not a score, model update or approval and
copies no Evidence body, prompt, token or secret.

## 7. Conceptual LearningProposal and governance

`LearningProposal` is an explainable immutable proposal containing samples,
Evidence, exact current target/version, proposed new version/change, rationale,
expected effect, risks, scope and provenance. It cannot apply itself. Effectiveness
review authority is not reused; future approval must separately resolve applicable
QMS, AI-governance, security and platform authority without inventing local RBAC.

Approved changes create new versions. Published prompt/rule artifacts,
AgentDefinition, ModelPolicy and KnowledgeLayerRule are never edited in place.
The governed runtime cannot edit its own policy, and an agent/optimizer cannot
propose and approve its own autonomy increase. A3/A4 always requires explicit
governance.

## 8. Target taxonomy, tenant and normative boundaries

| Target | Scope | Classification | Required boundary |
|---|---|---|---|
| prompt/rule bundle | global or explicit tenant | guidance, security-sensitive | AI governance/security; new version |
| ModelPolicy | global | governance, critical | separation of duties; new version |
| AgentDefinition | global | runtime governance, critical | AI governance/platform; new version |
| KnowledgeLayerRule | global | non-certifiable guidance, high | normative curation; new version |
| Recommendation heuristic | global or tenant | guidance/runtime, high | QMS/domain + AI governance |
| retrieval strategy | global or tenant | runtime/security, high | AI governance/security |

Default is no cross-tenant learning. Tenant A data cannot affect Tenant B or a
global target automatically. Anonymized/aggregated cross-tenant effectiveness
learning is not explicit in the sources and is deferred. Learning never modifies
RequirementControl, StandardEdition, Clause, certifiable content or normative
coverage. KnowledgeLayerRule remains governed global curation.

## 9. Aggregation and correction semantics

Default analysis takes one current leaf per Effectiveness lineage. Superseded
revisions are used only when the analytical purpose explicitly studies correction
history; they are not independent final samples. Aggregation preserves tenant,
Organization, sample/lineage IDs, exact Evidence and trust metadata, outcome
semantics and derivation version. Categorical outcomes are never simply averaged.
Unknown/inconclusive are not negative examples or zero scores by default.

## 10. Threat and minimization matrix

| Threat | Control/design boundary |
|---|---|
| effectiveness poisoning / malicious Evidence | exact immutable Evidence, hashes/trust, independent review |
| cross-tenant influence / global contamination | tenant default-deny; separate global policy/review |
| self-reinforcing bad recommendations | no direct loop; challenger and correction-aware review |
| autonomy escalation / policy self-modification | separation of duties; explicit A3/A4/policy governance |
| reviewer collusion | attributable samples and independent proposal approval |
| stale/superseded assessment / duplicate counting | one current leaf; unique predecessor; lineage-aware input |
| unknown treated as failure | closed semantics; no automatic scoring |
| proposal spoofing | trusted authority, immutable provenance, target-version binding |
| raw Evidence/prompt leakage | canonical references and redaction; no copied bodies/secrets |

Conceptual alerts cover overdue review, repeated inconclusive outcomes, missing
Evidence, authority failure and lineage conflict. No monitoring dependency was
installed. Business ineffectiveness/inconclusive alone never creates an incident.

## 11. Policy, runbook and eventing

`GOVERNED_LEARNING_POLICY_V1.md` is APPROVED FOR DESIGN/IMPLEMENTATION GATE and
states no self-modification, no direct mutation, no automatic autonomy/normative
or cross-tenant learning, human approval, versioning, provenance and
correction/uncertainty rules. The operational runbook now covers due/overdue,
unknown/inconclusive, stale correction, authority loss and Evidence/
MeasurementDefinition evolution without raw SQL repair.

Only `effectiveness_check.recorded` is implemented. Future
`learning_signal.created`, `learning_proposal.created` and
`learning_proposal.approved` names are conceptual and require a later gate.

## 12. Verification results

| Gate | Result | Evidence/delta |
|---|---|---|
| Concurrent correction | PASS | one winner, one stale conflict, no fork |
| Authority-time | PASS | historical snapshot retained; revoked writer denied |
| Review queue | PASS | due/overdue/inconclusive current leaf; tenant/Org scope |
| Retained history | PASS | v1 -> v2 -> v3 -> v4 reconstructible |
| Unknown/inconclusive inertness | PASS | protected row byte-state unchanged |
| Phase 19 matrix | PASS | atomic unit, 9/9 rollback, RLS/raw SQL/retention |
| Phase 16/17 matrices | PASS | full inherited controlled execution/recovery matrices |
| Backend | **175 PASS / 0 FAIL / 0 SKIP** | +3 Phase 20 tests from 172 |
| Foundation | **77 PASS / 0 FAIL / 0 SKIP** | +3 from 74 |
| Django check | PASS | zero issues |
| Migration drift | PASS | no changes detected |
| Python compilation | PASS | foundation/backend |
| PostgreSQL | PASS | official 18.6, real principals, run `20260824T224159Z_373ddf` |
| Migration hashes | PASS | 17/17 exact promoted SHA-256 |
| Source hashes | PASS | 10/10 exact manifest SHA-256 |
| Migration 0018 | ABSENT | no persistent Phase 20 state justified |
| Second action | ABSENT | forward defer only; resume remains separate compensation |
| Scoped diff hygiene | PASS | pre-existing Sidebar whitespace untouched |
| External business effects | ZERO | no deployment/provider/AdminApps/MedSupplier/notification write |
| Teardown | PASS | database/11 roles/container/volume/temp absent |

The legacy suite again attempted pre-existing Chroma/PostHog DNS telemetry and
failed closed; Phase 20 code itself imports/calls no HTTP, provider, shell,
subprocess, tool or notification path.

Migration SHA-256 values match Phase 19 exactly, including 0017
`580f16d1cdb10c30bae8f3e3c1667c3c4d2552b895fc9dea053d2c9b6adfaa38`.
The ten source hashes match the manifest (`8308bde9…`, `e0a59c91…`,
`11c2b461…`, `952d8ac9…`, `ecaecd25…`, `30e3c052…`, `de1b4899…`,
`29ac5c2d…`, `c41e847e…`, `eb42315c…`).

## 13. Residual blockers and verdict

There are 0 P0 and 0 P1 defects blocking the next design/implementation gate.
Product Policy v1 approval remains the prerequisite for Phase 21 implementation;
live AdminApps integration, production release, cross-tenant/global learning,
automatic proposal application and numeric aggregation remain out of scope.

**PHASE 20 — EFFECTIVENESS OPERATIONAL VALIDATION + GOVERNED LEARNING BOUNDARY DESIGN GATE: PROMOTED**

| Component/gate | State | Evidence | Risk/next action |
|---|---|---|---|
| Operational Effectiveness | PASS | concurrency, authority-time, queue, v1-v4 | retain PostgreSQL matrix |
| Governed learning boundary | PASS | Product Policy v1 + source matrix | approve policy before Phase 21 |
| Tenant/normative safety | PASS | no cross-tenant/default; no normative mutation | later global policy if ever needed |
| Runtime/schema | PASS | no 0018 or learning models/events | implement only under approved Phase 21 |
| Regression/integrity | PASS | 175/175; 77/77; Django/hash gates | preserve frozen baseline |
| External effects/teardown | PASS | zero business effects; resources absent | no deployment |

## NEXT_CODEX_PROMPT

Execute PHASE 21 — GOVERNED LEARNING SIGNAL + LEARNING PROPOSAL FOUNDATION IMPLEMENTATION exclusively in `/home/felipe/proyectos/isosmart` only after `governed-learning-policy/v1` receives the required Product Policy approval. Preserve migrations 0001–0017 and all promoted artifacts byte-for-byte; use additive migration 0018+ only for tenant-isolated, immutable LearningSignal, exact current-leaf Effectiveness links and explainable LearningProposal provenance. Implement separate trusted human/governance authority, global-versus-tenant target controls, versioned/append-only proposal history, DomainEvent/TransactionalOutbox/ImmutableAuditLog atomicity, ENABLE+FORCE RLS, correction-aware sample selection and data minimization. Do not automatically apply proposals; do not update prompts, ModelPolicy, AgentDefinition, KnowledgeLayerRule, Recommendation logic, retrieval, autonomy or normative content; do not enable cross-tenant learning, create another QMS action, deploy or touch production/staging/shared databases. Validate with official ephemeral PostgreSQL 18.6, real principals, rollback/retention/concurrency/security matrices, complete Phase 16/17/19/20 regressions, Django integrity, frozen hashes, zero external business effects and mandatory teardown; emit PROMOTED only with zero P0/P1 blockers.
