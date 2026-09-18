# First Retained Synthetic KnowledgeLayerRule Publication Candidate Policy v1

- Policy ID: `first-retained-synthetic-klr-publication-candidate-policy/v1`
- Policy artifact ID: `704f2135-9ec7-505f-8444-bb131b1afc07`
- Version: `v1`
- Date: 2026-09-03 (`America/Costa_Rica`)
- Status: **APPROVED FOR RETAINED SYNTHETIC CANDIDATE CREATION AND FUTURE EPHEMERAL PUBLICATION POC AUTHORIZATION GATE ONLY**
- Nature: ISO Smart Product Policy; non-normative; test-only; non-production
- Frozen policy-material SHA-256: `29281e4db12bf54d1eccc523fbbf889720d2cd9178d18d55d9c19c87ba93acf2`

## 1. Exact authorization

Product Governance recognizes the completed creation and retention of exactly
one candidate classified
`NEW_DETERMINISTIC_SYNTHETIC_PUBLICATION_POC_LINEAGE` and authorizes only its
eligibility for a later, separately controlled, ephemeral publication POC.
This policy does not authorize publication itself.

The only governed operation is
`learning.knowledge_layer_rule.source_reference.correct/v1`. No other target,
operation, lineage or candidate is covered.

## 2. Exact retained identity

| Material | Exact value |
|---|---|
| Run | `6fb6fdd0-9b03-5f54-9041-9e80bc90d0d5` |
| KnowledgeLayer | `43329c0b-5aaf-5bee-b944-41746fcededb` |
| Lineage/root/predecessor | `da72872a-3f3c-5fcd-86f7-0ed33e453522` |
| Root version | `sN` |
| Candidate | `01a0682b-dfc8-7b49-a601-f9bda29a70a5` |
| Candidate version | `sN+1` |
| Root full-material hash | `bd9824852e26a1fc4858df2410f29952aad97e220912813591109f8e05fd77ec` |
| Candidate full-material hash | `caa24592b509334af4cd60fd7d3f3c43989d864d3f1c6e6d0d3bf83a81871f81` |
| Phase 26-compatible semantic fingerprint | `8465956c1daf27a9838bc1bfb468af3f518ae255b4662b2df40e7b8648516192` |
| Phase 27.2 lifecycle hash | `0adfd8075cc720140c6e1f0393d286799edac8f352efd9f1969816be83c51e52` |
| Application Receipt | `01a0682b-dfa3-779c-89cd-1814e9209527` |
| Created manifest hash | `9ab80f4b0208e7dac971a0759df0bdb5c28392aa423ae11cbc0d483abb739a75` |
| Disposition hash | `964b632537323764de35f9132bf7e63966df29dc89d70c1166e432d4e6436b5c` |

The immutable creation manifest and append-only disposition record under
`docs/governance/evidence/` are the authoritative retained evidence. Summary
text never substitutes for them.

## 3. Source truthfulness

The only source is deterministic source ID
`6ec35e4a-bb8a-592b-bc6a-420691f4e8e3`, manifest material hash
`cf92c267439f94f302e67888665dbf99392592341a808f5fc00f4c32ef23dc24`
and source-material hash
`efe61114215914ac486011e4efd9977b4fa2f1c34fa6fad67012a46ced85ab4f`.
It is non-official, non-authoritative, non-normative, non-licensed, test-only
and non-production. It contains no ISO clause text and makes no licensing or
normative claim.

The exact correction changes only `fixture/element/A` to
`fixture/element/B` within
`iso-smart-synthetic-poc-source-ref-v1`. Source identity and bytes hash remain
unchanged.

## 4. Governance chain and Receipt

Eligibility is bound to the exact manifest-retained LearningSignal, Proposal,
CanonicalDelta, selected Review, Decision, ApplicationAuthorization, Receipt,
application DomainEvent, transactional Outbox record, application audit and
policy materials. Each reference carries its complete sanitized database
material and independently recomputable hash. Missing or mismatched material
fails closed.

The Receipt proves success with `external_effects=false`,
`runtime_effect_changed=false`, `result_published=false` and result status
`draft`. The retained leaf set is exactly the singleton candidate ID above.

## 5. No Phase 26 continuity

This lineage is new and independent. It is not `RECOVERED_PHASE26`, does not
reuse or infer any destroyed Phase 26 identity, and does not change the
`PERMANENTLY_UNAVAILABLE` classification of the historical Phase 26 candidate.

## 6. Separation of duties

The retained manifest binds nine pairwise-distinct server-resolved synthetic
AdminApps identities: proposer, reviewer, proposal approver, application
authorizer, application executor, curator, future publisher, activator and
adopter. The future publisher differs from every earlier actor, curator differs
from executor, and activator differs from adopter. Client claims are not
authority.

The retained future-publisher record is
`PUBLICATION_POC_ELIGIBILITY_AUTHORITY`; it is evidence of a tested
precondition only. Phase 29 must obtain a fresh AdminApps authority decision.
The Phase 28.3 authority must never be invoked as live publication privilege.

## 7. Publication preconditions

A later ephemeral POC may proceed only after re-verifying the immutable source
manifest, creation manifest, disposition, this exact policy material, current
leaf proof, all three rule hashes, full governance graph and Receipt, curator
evidence, fresh independent publisher authority, capability fence,
idempotency, concurrency, TOCTOU and expected-state token. Any mismatch,
missing evidence or reconstruction attempt makes the candidate ineligible.

## 8. Explicit prohibitions

This policy does not authorize:

- publication during Phase 28.3 or outside a separately authorized ephemeral POC;
- Activation, RuntimeAdoption, runtime wiring, cutover or deployment;
- production, staging or any shared database;
- another target, candidate, lineage, source namespace or operation;
- automatic learning, cross-tenant learning or tenant promotion;
- normative mutation, official-source classification or licensed content;
- mutation of ModelPolicy, AgentDefinition, Recommendation or AgentRun;
- reconstruction, regeneration or inference of missing retained evidence.

Publication, activation, RuntimeAdoption, runtime, normative, automatic-learning
and external-business effects in Phase 28.3 are exactly zero.

## 9. Revocation and change control

This policy is immutable once referenced. Correction or withdrawal requires a
successor policy and append-only evidence. A failed retained-evidence check,
changed candidate state, authority failure, SOD failure, unexpected successor,
or hash mismatch revokes later-gate eligibility without mutating history.

