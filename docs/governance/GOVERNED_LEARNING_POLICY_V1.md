# Governed Learning Policy v1

- Policy ID: `governed-learning-policy/v1`
- Status: **APPROVED FOR DESIGN/IMPLEMENTATION GATE**
- Nature: ISO Smart Product Policy, non-normative
- Date: 2026-08-24

## 1. Invariant and scope

An EffectivenessCheck is governed evidence about the business effectiveness of
one executed action. It may become input to future learning; it is not a learning
decision or model update. No runtime path may map an outcome directly to a
confidence, prompt, rule, model, policy, Knowledge Layer, Recommendation,
authorization, autonomy or QMS action change.

The governed chain is:

`EffectivenessCheck revision -> LearningSignal -> LearningProposal -> separate human/governance review -> approved new target version`.

This policy designs that boundary only. It authorizes no table, migration, event,
optimizer, training job, proposal application or external effect.

## 2. Prohibited shortcuts

It is forbidden to treat `effective` as increased confidence/autonomy, treat
`ineffective` as reduced confidence or an automatic prompt change, or treat any
count/threshold as authority. An agent/optimizer cannot approve its own change,
and a runtime agent cannot edit the ModelPolicy that governs it. A3/A4 changes
always require explicit, separate governance.

No outcome automatically creates an incident, Recommendation, compensation or
second QMS action. Operational-integrity incidents remain distinct from business
effectiveness.

## 3. Conceptual LearningSignal

A future LearningSignal is a tenant- and Organization-scoped, immutable,
redacted reference set derived under a separately authorized process. It is not a
score, label, target mutation or approval. Where applicable it identifies exact:

- current EffectivenessCheck leaf and full correction lineage;
- ActionExecution, receipt, ActionPlan/hash and authorization;
- Recommendation, RecommendationBasis, AgentRun, AgentDefinition version and
  ModelPolicy version;
- RequirementControl, KnowledgeLayerRule and exact Evidence revisions;
- tenant, Organization, policy, trace and derivation rule/version.

It references canonical immutable artifacts and hashes/trust metadata; it does
not copy document bodies, raw prompts, secrets or tokens.

## 4. Conceptual LearningProposal and authority

A future LearningProposal is an explainable, immutable proposal, not an applied
change. It identifies supporting signals/samples, exact evidence, target and
tenant scope, current target version, proposed new version/change, rationale,
expected effect, risks, provenance, proposer and required governance domains.

QMS effectiveness-review authority does not imply proposal authority. Future
authority must be resolved separately from applicable QMS, AI governance,
security and platform systems of record. This policy invents no local roles/RBAC.

## 5. Correction-aware aggregation

Default analysis uses only the current leaf of each EffectivenessCheck lineage.
Superseded revisions remain available for explicit correction-history analysis
but are never counted as independent final outcomes. Aggregates preserve sample
IDs, lineage, tenant/Organization, Evidence quality and outcome semantics;
categorical outcomes are not averaged.

`unknown` means an evidenced blocker prevented reliable assessment;
`inconclusive` means assessment occurred without a reliable binary conclusion.
Neither is a negative example, failure label or numeric zero by default.

## 6. Tenant and global boundary

Default is no cross-tenant learning. Tenant A data cannot influence Tenant B
behavior automatically or implicitly. The ten authoritative sources specify no
anonymized/aggregated cross-tenant effectiveness-learning contract, so it is
deferred. A future global proposal requires separate policy, privacy/security
review, minimization proof, provenance and explicit global governance.

## 7. Target taxonomy and versioning

| Target | Scope | Nature | Security | Human approval |
|---|---|---|---|---|
| Prompt version | global or explicitly tenant-scoped | guidance/runtime | high | AI governance + security |
| Rule bundle | global or explicitly tenant-scoped | guidance/runtime | high | AI governance + domain owner |
| ModelPolicy | global | governance/policy | critical | AI governance + security/platform |
| AgentDefinition | global | runtime governance | critical | AI governance + platform |
| KnowledgeLayerRule | global | non-certifiable guidance | high | normative curation + AI governance |
| Recommendation heuristics | global or tenant-scoped | guidance/runtime | high | QMS/domain + AI governance |
| Retrieval strategy | global or tenant-scoped | runtime | high | AI governance + security |

Approved changes create a new version. Published targets are never changed in
place.

## 8. Normative safety

Learning never creates, edits, supersedes or reinterprets RequirementControl,
StandardEdition, Clause or certifiable normative content. KnowledgeLayerRule is
governed global curation, not automatic learning. Certifiability and normative
coverage cannot be inferred from effectiveness outcomes.

## 9. Conceptual event and audit boundary

`effectiveness_check.recorded` remains the only implemented event. Future names
`learning_signal.created`, `learning_proposal.created` and
`learning_proposal.approved` are design terminology only. If later approved,
audit must reconstruct Evidence -> check leaf -> signal -> proposal -> authority
decision -> new target version. No opaque optimizer mutation is acceptable.

## 10. Threat controls

| Threat | Required boundary |
|---|---|
| Effectiveness poisoning / malicious Evidence | exact revisions, trust/provenance validation, independent review |
| Cross-tenant influence / global contamination | tenant default-deny; separate global policy/review |
| Self-reinforcing recommendations | no direct loop; correction-aware samples/challenger review |
| Autonomy escalation / policy self-edit | separation of duties; explicit A3/A4/policy governance |
| Reviewer collusion | attributable samples, independent approval, anomaly review |
| Stale/superseded or duplicate samples | current-leaf default and lineage uniqueness |
| Unknown treated as failure | closed semantics; no default scoring |
| Proposal spoofing | trusted authority, immutable provenance, target-version binding |
| Raw-data/prompt leakage | canonical references, redaction and minimization |

## 11. Change control

Automatic application, cross-tenant aggregation, numeric scoring, a new target,
authority model or event contract requires a later policy version and separate
implementation/security gate. This v1 is immutable once referenced.
