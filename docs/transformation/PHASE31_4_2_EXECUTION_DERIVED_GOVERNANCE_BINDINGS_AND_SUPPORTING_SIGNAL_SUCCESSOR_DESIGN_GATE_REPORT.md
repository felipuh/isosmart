# Phase 31.4.2 — Execution-derived governance bindings and supporting signal design gate

## 1. Verdict

`PHASE 31.4.2 — NOT PROMOTED`

P0=0; P1=4. This is a diagnostic design result, not an approved execution contract. No PostgreSQL creation or lifecycle retry is authorized. Model B is recommended on the inspected semantics, but an integrated successor has not been adopted. Missing producers, complete field bindings and retention edges cannot be replaced by passing necessary-condition tests.

The two companion additions are `backend/foundation/test_phase31_4_2_design_gate.py` and `docs/governance/evidence/PHASE31_4_2_SUCCESSOR_DESIGN_DIAGNOSTIC_V1.json`. The JSON explicitly records incomplete schemas, incomplete taxonomy coverage, incomplete semantic closure and false execution-authorization flags. Neither is a V2 operational fixture.

## 2. Entry B1–B4

Phase 31.4.1 ended NOT PROMOTED, P0=0/P1=4, without PostgreSQL or lifecycle execution.

| Blocker | Entry defect | Result here |
|---|---|---|
| B1 | Predicted root full-row hash lacks authentic timestamps | Exact derivation candidate documented; bootstrap and integrated admission contract incomplete |
| B2 | Compatibility ID/hash lacks canonical preimage | Proposed postpublication observation; complete producer and schema absent |
| B3 | Release ID/hash lacks canonical preimage | Proposed nonrecursive checkpoint ordering; exact membership and producer absent |
| B4 | Supporting signal/effectiveness and governance material incomplete | Required execution provenance expanded; full material, identities, replay and closure not closed |

These are four retained P1 blockers, not four new regressions. No additional P0 finding was established.

## 3. Initial Git state

The first repository inspection was `git status --short` from `/home/felipe/proyectos/isosmart`, followed by `git diff --check`. Exact status:

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

Initial diff check exited 2 solely for the preexisting trailing whitespace in `frontend/src/components/Layout/Sidebar.jsx:28`. Its exact output, including the trailing space, is retained in diagnostic `entry_diff_check`; the file was not normalized.

## 4. Frozen hash verification

The diagnostic retains 216 protected file hashes and 23 numbered migration hashes. The predecessor protection inventory was checked before additions. A broader entry inventory covers 14,352 preexisting tracked/nonignored regular files, excluding symlinks and Python bytecode/cache files; byte comparisons are preservation checks, not semantic review. Final integrity results are retained under `integrity_validation`.

No old report, ADR, policy, fixture, implementation, migration or historical evidence was overwritten. Migration 0024 remains absent. No reset, stash, clean, stage or commit was performed.

## 5. Reading completion

**Complete mandatory semantic reading is not claimed.** This is also an unmet gate requirement. Full-byte parsing and digest verification do not establish semantic reading.

Fully reviewed inputs include AGENTS.md; ADR-0013–0017; the Phase 31.3 Product Policy and source fixture; Phase 31.3 and Phase 31.4 reports; the registry and expected closure; migrations 0009, 0018, 0019, 0020, 0021 and 0023; governed learning, Application, Review/Decision/Authorization, Effectiveness, eventing, audit, canonical and learning-delta implementations; knowledge-rule release service; relevant LearningSignal/Proposal/Review/Decision/Authorization/Effectiveness model definitions; tenant context; and the Phase 28.3 retained-candidate helper. Phase 31.3.1 and Phase 31.4.1 report sections were reviewed through multiple reads, including recovered portions of truncated output, but are conservatively not certified completely reviewed here.

The lifecycle specification was parsed completely and its principal lifecycle/source/identity/operation sections reviewed; remaining policy and boundary sections were not all semantically exhausted. Both predecessor diagnostic JSON files were parsed and their findings, root vectors, inventories and validation material inspected, but not every retained member was semantically reviewed. Migration 0022 was inspected extensively, including native operation formulas and ACLs; a truncated combined read prevents claiming full coverage. Phase 26 harness lines 1–260, relevant initial Phase 28.3 harness lifecycle paths and retained-publication-evidence helper sections were reviewed, not their complete files. No harness was executed. RLS/least privilege was reviewed through ADRs, tenant context and inspected migration code; no live RLS validation occurred.

The continuation must finish these readings before claiming an approved successor. This report does not conceal the shortfall behind a hash check.

## 6. Execution-ready-v2 principle

Recommended principle: every future value is either exact prebound material or the unique result of a preapproved derivation over exact persisted/fresh inputs, with explicit provenance, freeze point and consumers. The producer, input selection and canonicalization cannot be left to the executor.

Authentic persisted timestamps make a precreation full-row numeric hash inappropriate. This does not make Model B architecturally impossible. It requires changing the governance sequencing and approving a complete successor. This diagnostic supplies only part of that contract and therefore does not adopt execution-ready-v2 as operational authority.

## 7. Prebound/execution-derived taxonomy

The candidate taxonomy is closed to four modes:

| Mode | Material | Earliest availability and retention |
|---|---|---|
| PREBOUND_STATIC | Exact source, meaningful IDs, non-time business inputs, schemas, policies and formulas | Freeze 0; retain exact preimages/source provenance |
| EXECUTION_DERIVED_PERSISTED | Full rows, target/Delta/governance hashes, observations, checkpoint manifests | After designated persistence/read; retain complete canonical inputs and output |
| EXECUTION_DERIVED_EXTERNAL_AUTHORITY | Fresh server-resolved authority decision/reference | At authorized operation boundary; retain frozen external/test provenance |
| OUTPUT_ID_MAPPED_BY_ADR0017 | Seven Application output identity positions only | Identity comparison under ADR-0017; retain original and mapped comparison material |

Three candidate descriptors explicitly state source, derivation, canonicalization, policy status, availability, deadline, consumers and disposition. No predicted numeric digest occurs in these derived descriptors. A candidate type list is not a classification of every lifecycle field: `taxonomy_covers_every_lifecycle_field=false`. Exact exhaustive field coverage remains required.

## 8. B1 resolution status

Model B is recommended, not approved as a complete successor. Root ID and lineage remain `bc5f4f17-294d-5abd-b27b-2d296921ffdf`, version `s0`. The diagnostic retains all eleven non-time root values, including published state, null predecessor, layer, source locator and JSON fields. The complete row has thirteen columns, including `created_at` and `published_at`.

The old target `dbaa2e4eff3c980522a916d0cf2f10127e39f0af8dbfdacb469ac3015d8d87db` is classified in the proposed successor analysis as `SUPERSEDED_PREEXECUTION_EXPECTATION — NEVER EXECUTED`, with execution authority false. Its historical source is unchanged. No replacement numeric target is supplied.

The hash candidate preserves 0021 exactly: SHA-256 of UTF-8 bytes of `{"canonicalization":"iso-smart-canonical-json-v1","value":` followed by `qms.foundation_0020_canonical_json_value(to_jsonb(r))` followed by `}`. The eleven-field input is not substituted for the full row. This derivation does not by itself close the bootstrap identity/authority/retention admission requirements.

## 9. Root persistence/freeze sequencing

Freeze identity and non-time material; create a synthetic draft; publish through an approved bootstrap transition; commit; open a new REPEATABLE READ READ ONLY transaction; select exactly the root by ID; require one published row, null predecessor and no successor. Obtain raw PostgreSQL JSONB and canonical text. Repeat in an independent read-only transaction and require identical canonical bytes. Only then freeze the full target artifact and admit Proposal/Delta.

Retain both read observations, schema/migration binding, rendering settings, exact canonical bytes, hash, bootstrap evidence and full curation audit. Root times are authentic persisted values, never guesses, fixture constants or omitted fields. ORM auto_now_add and SQL statement_timestamp are different producers; the final bootstrap must explicitly select the producer and privileges. That full recipe remains absent.

## 10. PostgreSQL rendering profile

Proposed future profile: PostgreSQL 18.6 (`server_version_num=180006`), server/client UTF8, TimeZone UTC, libc locale provider, LC_COLLATE=C, LC_CTYPE=C, DateStyle `ISO, YMD`, IntervalStyle `iso_8601`, extra_float_digits=3 and standard_conforming_strings=on. Future execution must verify actual server/database/session values before writes and in hash reads; these are requirements, not observations from this phase.

0020 sorts JSON object keys using ORDER BY and renders scalar JSONB text. Collation therefore matters. PostgreSQL-rendered timestamp strings remain authoritative; Python datetime normalization to six-digit Z strings must not replace them. No RFC8785 compatibility is claimed. No helper replacement or migration change is proposed.

## 11. B2 compatibility evidence

Preserve intended identity `37d3d0bc-4387-581a-a627-f02a011250d1`. No authentic preimage was found for old hash `43c72090f30e90a4f3896b3d194aa264f421189f0589978453136464e270dbc9`; it receives the same superseded/non-executable classification in this analysis.

The proposed meaning is a bounded synthetic compatibility observation after native Publication: exact candidate and Publication, same substantive fingerprint/source edition/source bytes, locator-only correction, retained Application parity, and observed absence of RuntimeAdoption/runtime effects. The diagnostic enumerates required material fields, intended Activation cross-link, producer/version, transaction observation, input retention and synthetic/non-normative flags.

It is EXECUTION_DERIVED_PERSISTED, available within Freeze 7 and required before Freeze 8. Complete field types, allowed values, assertion evaluation rules and a governed producer are not supplied; `schema_complete=false`. A required-field list is not a schema or preimage. B2 remains open.

## 12. B3 release evidence

Preserve intended identity `981e1753-dcd1-5f8d-8b10-49bfaed5eafb`. Old hash `5583dd2939abe5e1e2d602cef33077685df8efb48f0c664812eaee138723d15a` has no authenticated preimage in the inspected package and is classified superseded/non-executable here.

Proposed meaning: native Publication has been recorded and independently exported, while Activation remains separately gated and RuntimeAdoption absent. Required fields include exact candidate/Publication graph, source, compatibility observation, producer/read provenance and a preceding Publication graph checkpoint.

Release cannot hash a final closure that includes release itself. Use an explicitly defined earlier checkpoint excluding itself/final manifest, then include release and compatibility in the final Publication closure. This ordering is a design candidate; exact checkpoint membership and complete producer/schema remain missing. B3 stays open. No release digest is prebound.

## 13. B4 Effectiveness graph

`effectiveness-check-policy/v1` does not accept a standalone invented check. The inspected path requires a succeeded `controlled_opportunity` execution of `opportunity.defer_evaluation`, an `opportunity_deferred` receipt, exact under_evaluation/deferred Opportunity revisions, plan, authorization, decision and recommendation. The receipt must not claim effectiveness. Evidence must bind at least one exact eligible Evidence revision in the same tenant/organization.

Required timing is deferred revision created_at < due_at <= assessed_at. Human review requires an authorized human projection. MeasurementDefinition can be absent only for human_review criteria that are not measurement-derived. Revision 1 with null predecessor needs no correction history; later corrections require the full linear lineage. These are constraint findings, not fabricated successful outcomes.

Recursive non-null ORM FK inspection from the five supporting graph roots reaches 23 model classes and 77 edges. These include ActionPlanDryRun, AgentRun, AgentDefinition and ModelPolicy. The machine evidence retains all edges and their columns. This is a lower bound: SQL-only, conditional nullable and semantic dependencies still need expansion, including RecommendationBasis, AgentRunInput and operation event/outbox/audit provenance.

The old spec lists LearningSignal, ModelPolicy and AgentDefinition among zero unauthorized deltas and protects AgentRun/Recommendation state. A successor must explicitly distinguish a new isolated NON-OFFICIAL TEST FIXTURE bootstrap from changes to protected runtime state. It cannot borrow old harness objects or execute a model to fill the gap. This conflict needs an exact approved fixture recipe; it is not proof that such a recipe is impossible.

## 14. B4 LearningSignal

The supporting signal is tenant/organization-scoped even when its Proposal targets a global rule. It must select an eligible current EffectivenessCheck leaf, retain its complete lineage snapshot and exact evidence links, and derive no earlier than the check's created_at. The Proposal must retain at least one eligible signal via LearningProposalSignal; 0018's deferred requirement is not bypassable.

Signal type/findings/rationale/target indication and synthetic flags are not columns on LearningSignal. Any extra annotations need a versioned retained envelope, not invented model fields. Required boundary: synthetic=true, automatic_learning=false, normative=false, production=false, NON-OFFICIAL TEST FIXTURE. No real QMS result or autonomous improvement claim is established.

Exact signal/check business material, per-operation event/outbox/audit rows and producer contracts remain incomplete. The diagnostic identity slots are not permission to insert fake minimal rows.

## 15. Proposal V2

Proposal may follow only the exact persisted root artifact and eligible retained signal. It must bind the old truthful target identity, live target tuple, exact signal IDs, intended locator correction, proposer, policy, rationale, expected effect, risks, domains and revision/predecessor semantics. Proposal and exact Delta use their existing coupled transaction/deferred bindings.

The native create_proposal method generates UUIDs internally and has no proposal_id output argument. A deterministic fixture contract therefore needs an explicit governed producer. ADR-0017 does not supply it. Full nonfresh values and producer/replay rules are not complete here; no Proposal V2 has been authorized.

## 16. Delta V2

Preserve operation `learning.knowledge_layer_rule.source_reference.correct/v1`, schema `learning-knowledge-layer-rule-source-reference-correction-delta-v1`, canonicalization `iso-smart-learning-delta-canonical-v1`, exact locators, source and successor semantics. The ten-key document binds target identity, lineage, version, type, hash, operation pair, schema, canonicalization and payload.

After the root artifact exists, substitute its exact hash into the unchanged operation document, validate against the exact target/source, canonicalize with learning_delta.py and compute SHA-256. Persist with Proposal; retain canonical bytes; never mutate later. Old Delta `06f75de72e2a2ded515c223a1c62df6ab3780ebfe1ed0ccca71a22a222071c9e` is reproducible historical material whose target admission is defective. Recomputability does not make it valid execution authority.

## 17. Review V2

Review follows exact Proposal/Delta, target reread and signal support. Native outcome is `review_recorded`, not approval. Findings require summary, domains and booleans for autonomy change, normative change, policy relaxation and cross-tenant effect. For the proposed locator-only correction these booleans should be false, but validity/staleness must be checked against actual inputs rather than predeclared success.

Retain the full Review, target tuple, Proposal material hash, Delta binding, findings, policy, reviewer and fresh authority provenance. The exact narrative findings and deterministic output producer remain unbound. Passing structural findings checks does not close Review V2.

## 18. Decision V2

The native Review-set hash is canonical_hash of sorted Review UUID strings, not hashes of complete Review rows. Full selected Reviews must therefore be retained separately. Decision material binds proposal_id, proposal_material_hash, review_set_hash, outcome, rationale, approver and policy_id through the implementation's canonical_hash.

Fresh authority permits recording a decision; it is not the business decision itself. Exact successful outcome cannot be asserted before eligible Reviews exist. Deterministic identity production and complete nonfresh rationale/policy binding remain incomplete in this diagnostic.

## 19. Authorization V2

Authorization follows exact target, Delta, Proposal, Reviews and Decision. Its idempotency material includes tenant/organization, Proposal identity/revision/material, Decision, target tuple, capability ID/version, caller key, authorizer, authority context/reference and exact Delta tuple. Because fresh authority participates, the resulting hash is execution-derived.

The native service generates the Authorization identity. This phase did not add an output-ID parameter or freeze a future authority outcome. A complete V2 authorization/capability/provenance and replay contract is still required.

## 20. Authority separation

Governed business material is distinct from the fresh authority decision permitting its recording. External authority is retained as `EXTERNAL_AUTHORITY_REFERENCE_WITH_FROZEN_PROVENANCE` or an explicitly approved test-equivalent provenance contract. No real AdminApps interaction occurred.

Compatibility/release observations are evidence only. They are neither authority, capability, approval, adoption nor certification. They can constrain future admission but cannot execute an operation. Database context must come from trusted server-resolved identity; request-controlled tenant inputs are not a substitute. No local fallback was enabled.

## 21. Idempotency V2

| Operation | Inspected native behavior; unresolved successor boundary |
|---|---|
| Proposal/Delta | No caller idempotency-key parameter; exact coupled material and generated identities. Do not invent native replay support. |
| Review | No caller idempotency-key parameter; new immutable Review identity. Complete fixture replay recipe absent. |
| Decision | Natural Proposal decision uniqueness and canonical decision identity material; changed material is not an exact replay. |
| Authorization | Caller key differs from canonical idempotency hash including fresh authority. A changed authority reference can cause a conflict. |
| Application | Native application identity and claim formulas below; outer experiment key is distinct. |
| Publication | SHA-256 UTF8(candidate UUID + ':' + expected selected rule hash + ':' + reason). |
| Activation | SHA-256 UTF8(Publication UUID + ':' + selected rule hash + ':' + predecessor UUID or ROOT + ':' + compatibility hash + ':' + reason). |

The Publication/Activation formulas are narrow native 0022 material hashes, not complete authority/policy/evidence envelope hashes. The final successor must specify any outer admission envelope separately without changing native SQL formulas. Three historical caller-key hashes were independently recomputed; this does not verify live canonical operation hashes. There is no complete idempotency V2 contract yet.

## 22. Claim formulas

0021 application identity is SHA-256 over UTF8 of concat_ws('|', Proposal ID, Decision ID, Authorization ID, operation ID, operation version, Delta hash, target ID, target version, target hash, coalesce(forward receipt ID, '')). A forward Application therefore retains the trailing separator.

Claim material is SHA-256 over UTF8 of concat_ws('|', application identity, Decision.review_ids_snapshot::text, Authorization.idempotency_hash, executor UUID). Preserve PostgreSQL JSONB array text, including its separators; a compact Python list rendering is not interchangeable. Compute only after all inputs exist. No numerical claim hash was predicted.

## 23. Receipt/Event/Audit derivation

Expected identity and full persisted row material are different commitments. Receipt, event, outbox and audit material containing timestamps, authority or outputs is obtained from committed rows and retained with its canonicalization and provenance. Never compare only UUIDs.

Application's candidate after-hash captures the draft row at Application. Publication later changes candidate status/timestamp. Retain each historical state required by the lifecycle; a current published row cannot replace the earlier draft snapshot in Receipt verification. Application curation payload uses a full-row after-hash, whereas native Publication curation payload uses selected rule material. Preserve both algorithms and complete audits.

## 24. Freeze points

| Freeze | Candidate sequencing obligation |
|---|---|
| 0 | Before DB: source, identities, complete schemas/graphs, policies and derivation/producer rules |
| 1 | Persisted published root independently reread; full target artifact frozen |
| Before 2 | Complete governed synthetic execution, Effectiveness and eligible signal support retained |
| 2 | Coupled Proposal/Delta exact material persisted and verified |
| 3 | Review material and fresh authority retained |
| 4 | Decision and selected Review set retained |
| 5 | Authorization/capability and authority provenance retained |
| 6 | Application outputs and historical candidate state retained |
| 7 | Native Publication, nonrecursive evidence checkpoints, compatibility/release, final Publication closure exported and independently verified |
| 8 | Separately authorized Activation and complete result graph |
| 9 | Full fixed-point retained export, independent verification and teardown gate |

The diagnostic validates necessary ordering and rejects cycles. It does not prove every field has a freeze binding. No consumer may rely on a value before its designated verified freeze.

## 25. ID stability

Same intended experiment identity `a3f8fd64-af24-5b31-977a-bcaf8146c563`; intended new execution-contract version; no lifecycle execution under predecessor contract. Namespace remains `05611a8a-f662-5b7f-ad24-c4df48d573ec`, derived by UUIDv5 URL namespace from `https://iso-smart.local/phase31.3/complete-retained-synthetic-lifecycle/v1`.

Existing truthful root/candidate/Publication/Activation identities remain unchanged. The diagnostic includes 28 proposed UUIDv5 label slots for support and observations, with explicit labels and an empty collision list against the enumerated historical files. This is not a complete per-row graph inventory: one event type slot cannot identify every operation's event. The subsequent 23-class FK finding also exceeds parts of the original candidate slot inventory. `candidate_support_ids_operationally_frozen=false` is intentional. No fresh authority decision was frozen as a persisted approved outcome.

## 26. ADR-0017 compatibility

ADR-0017 remains byte-identical and valid for its one exception: preallocated Application output identities for candidate, claim, Receipt, event, outbox, curation audit and Application audit. Both reference 0021 and the adapter must consume the same exact derived target/Delta/Authorization inputs. Original timestamps, authority and validation results cannot be removed to manufacture parity.

The native Signal, Effectiveness, Proposal, Review, Decision and Authorization services generate UUIDs internally and lack corresponding output-ID parameters. AST probes verify that finding. AuditWriter likewise does not expose an arbitrary audit-ID parameter. This does not authorize expanding the Application adapter or bypassing guards. An explicit narrowly governed supporting fixture producer remains a design requirement. No parity run occurred.

## 27. ADR-0018

Not created. An accepted ADR cannot merely rename unresolved fields or bless an incomplete graph. Model B and execution-ready-v2 remain recommendations recorded in this diagnostic report. A successor ADR must explain the full bootstrap/producer/identity boundary, B2/B3 evidence, complete B4 graph and exhaustive freeze semantics before adoption.

## 28. Product Policy successor

Not created because B1–B4 are not all closed. The old policy remains immutable historical evidence. A future successor may authorize clean Phase 31.4 retry eligibility only; this phase never authorizes lifecycle execution. No implicit policy exception has been inferred from the new diagnostic.

## 29. Lifecycle spec V2

Not issued. No complete machine-readable operational successor exists. The diagnostic JSON is canonicalizable and independently hashable, but explicitly incomplete. Fake zeros, TBD, null or arbitrary hashes are not used to make its three execution-derived candidate descriptors appear exact.

## 30. Registry V2

New semantic edges will be necessary for root-target provenance, supporting Effectiveness/Evidence/Signal, Proposal linkage, compatibility and release. Each needs cardinality, target, disposition, canonicalization and verification rule. The old registry's 56 edges passed a structural check only. No V2 registry or complete edge set is claimed.

## 31. Closure V2

Not issued. The future closure must combine a live schema/FK snapshot with a complete successor semantic registry to a fixed point. Every mandatory local row requires `RETAIN_FULL_CANONICAL_MATERIAL`; fresh external authority requires its frozen provenance disposition. The 23-class/77-edge ORM traversal is explicitly not this live fixed point. Conditional lineage, semantic inputs and event/audit graphs still need expansion.

Historical expected closure checkpoint/migration references passed structural checks. No Publication, Activation or live retained closure was produced or validated.

## 32. Curation-audit retention

Every mandatory normative.curation_audit must retain all eight fields: id, action, entity_type, entity_id, actor_id, trace_id, payload_hash and occurred_at. This includes root and Application/Publication audits and any support operation whose actual promoted path requires one. A UUID-only edge fails. Do not add invented curation audits to operations that instead require immutable governance audits; follow the exact operation semantics and retain those rows too.

Phase 29 remains `HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE`, incident `RETENTION_CLOSURE_BREACH`. Publication `e97576de-d4ef-520d-8592-d376ed401221` and missing audit `12d811ab-c3b4-4615-8972-75008a36e327` are historical-only. Neither may enter the new operational graph. No reconstruction or reuse occurred.

## 33. Publication closure checkpoint

Publication closure must be computed, exported, independently reread and verified before Activation. A successful native Publication commit is insufficient.

The old spec's `canonical_operation_contracts.publication.required_fields` includes `compatibility_release_evidence_hashes`. If those evidence documents assert persisted Publication facts, moving only their hash availability creates Publication admission → evidence → Publication → admission. The candidate resolution separates prepublication eligibility from postpublication observations, then final Publication closure. Release's earlier checkpoint excludes its own/final-manifest digest to prevent another cycle. Exact new edges, membership and admission schema still need approval. The diagnostic negative test rejects a reintroduced dependency cycle.

## 34. Prebound hash audit

All literal 64-hex values in the diagnostic, including embedded locators and protection inventories, must occur in `digest_provenance` with a nonempty source classification. The source/manifest, old Delta, selected root/candidate, substantive/lifecycle hashes, two locators and three caller keys have twelve retained independent recomputations. Old B1/B2/B3 values are historical references, not authenticated future material.

This is a diagnostic hash-provenance audit, not the requested complete successor-spec audit: no successor exists. A provenance label alone is not a proof of arbitrary semantic correctness or a complete preimage contract. Fixed-hash defects are not declared prospectively closed.

## 35. Offline contract tests

Validation used only backend/.venv, Django 4.2.22 and Python bytecode-disabled/in-memory compilation. In-memory settings installed auth, contenttypes and Foundation with a dummy database; normal project settings/logging were not loaded. Database connection, socket events and resolver calls were guarded to raise. Tests ran through DiscoverRunner.build_suite and unittest.TextTestRunner without database setup.

Final selected run: **78 tests, 0 failures, 0 errors, 0 skips**. It includes 23 new diagnostic tests and 55 selected predecessor/Foundation tests. `check` reported no issues; `makemigrations --check --dry-run` reported no changes. In-memory compilation covered 352 backend Python files. No migration was executed. Database/network/resolver attempt counters were all zero.

Exact labels and raw output are retained in diagnostic `offline_validation`. The selected groups are Phase3ContractTests, Phase9KnowledgeLayerContractTests, Phase21BlockingHardeningTests, Phase23LearningProposalGovernanceTests, Phase26KnowledgeRuleApplicationContractTests, test_learning_delta, two inert release signature tests, test_phase31_4_1_root_binding and test_phase31_4_2_design_gate. The resolver-invoking test, Publication-service revocation test, historical evidence execution suites, all PostgreSQL harnesses and remaining unrelated Foundation tests were excluded.

One earlier 77-test attempt failed because the test-only resolver denial guard changed the inspected method signature; the guard was corrected to preserve `self, *, runtime_adoption_id`. A later rerun setup stopped on a mistaken resolver class import before checks/tests; it was corrected to InertRuntimeAdoptionResolver. Neither required protected implementation changes or invoked the resolver. These attempts are retained; they are not concealed as first-pass success.

## 36. Negative tests

The diagnostic probes reject predicted target hashes, derived-value placeholders, missing derivation/freeze, unknown taxonomy, static approved external authority, static digest/preimage mismatch, Proposal before root/signal, missing Effectiveness predecessor, Authorization before Decision, missing closure disposition, Phase 29 operational identities, RuntimeAdoption members and the Publication/evidence cycle. They verify the limited ADR-0017 mapping and native generated-ID findings.

They test necessary conditions and explicit incompleteness, not a complete operational schema. In particular, a hand-supplied required-member list cannot prove transitive closure, and descriptor presence cannot prove executable producers. No positive full supporting graph or complete V2 package passed acceptance here.

## 37. Migration/source/governance/runtime hashes

| Historical artifact | SHA-256 |
|---|---|
| Exact source bytes | e458cd0bb7eb11f96ce8723b0ab4dea97e4ca60b0e47a6f7e1fb1f38cef66d6b |
| Phase 31.3 lifecycle spec | 683f7c83ff3e3e16733d63288d317f8b3a14fe9e5bfaf2e86b0cf2e86b6ab6ca |
| Phase 31.3 Product Policy | 44535b47bda30a4319903d8b9f10be04890b4d9085c8955d57916f3616d9588d |
| Phase 31.3 registry | d5e1960801772af74d491c9c6f69a877b79f1e26b937701cf1a239114b37bf1c |
| Phase 31.3 expected closure | d3455bc64957ef1aab5f618e552d9276bd6fd60e0b1ce2e7a8068e5c14c8917a |
| ADR-0017 | 82501ef34edc6d7e76e0971d3d2607c58f229a1dd4dd26696dd227fb7e994edb |
| Migration set 0001–0023 | cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc |

Migration-set formula: sorted repository-relative path + NUL + file SHA-256 hex + LF for each numbered migration, then SHA-256 of the resulting bytes. It is not a JSON-object digest. Exact per-file protected governance/runtime/historical hashes are retained in the diagnostic, avoiding a duplicate full inventory. The source remains synthetic/non-normative with no licensed content added.

## 38. Git hygiene

Only the three new files named in this report are durable additions. Entry files remain byte-identical against the captured inventory; all 216 protected entries and 23 migration entries match. The final complete diff check preserves the same preexisting Sidebar warning; scoped `git diff --check -- . ':(exclude)frontend/src/components/Layout/Sidebar.jsx'` passes. New untracked additions are separately checked for whitespace because ordinary git diff omits them. Final status is retained in diagnostic `final_git_status_exact`; directory-collapsed status alone is not the preservation proof.

Temporary entry/validation files created by this task are removed after their results are retained. No unrelated file is staged, normalized or deleted. No sibling repository was inspected.

## 39. Zero effects

```text
database effects=0
PostgreSQL effects=0
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

No database/container/role was created, no adapter installed and no lifecycle service executed. Operational tests: `NOT EXECUTED`. Reading resolver code/signature is not invoking it.

## 40. P0/P1

P0=0; P1=4. B1_closed=false, B2_closed=false, B3_closed=false, B4_closed=false. Missing complete reading and integrated contracts are explicitly disclosed within the unresolved gate, not asserted away. No RuntimeAdoption or migration authorization follows from the offline checks.

## 41. Residual blockers

B1 needs an exact governed root bootstrap and full integration of derived material with all consumers. B2 needs complete typed compatibility material and producer/admission rules. B3 needs complete typed release material and a nonrecursive, precisely enumerated checkpoint. B4 needs every supporting row and semantic edge, legitimate synthetic execution provenance, exact nonfresh governance findings/rationales/policies, deterministic ID production, authority boundary, operation replay rules and fixed-point retention.

These are concrete design tasks that can be continued offline. The absence of native output-ID parameters does not prove no approved fixture design is possible. Neither additional numeric guesses nor an ADR with unresolved slots would close them.

## 42. Final verdict

`PHASE 31.4.2 — NOT PROMOTED`

No accepted ADR-0018, successor Product Policy, lifecycle spec V2, registry V2 or closure V2 was issued. The architectural closure objective remains incomplete. The diagnostic result preserves useful derivation and dependency findings for one blocker-specific continuation; it does not advance to Phase 32 or authorize PostgreSQL.

### Offline continuation audit — 2026-09-08

The report and its original diagnostic/tests already existed at this run's entry.
Sections 3–38 above describe that earlier run; this addendum records the current
work separately. The initial `git status --short` and `git diff --check` outputs
were identical to the recorded entry outputs. Existing unrelated changes were
preserved. No complete mandatory semantic reading is claimed for this run.

New retained evidence:
`docs/governance/evidence/PHASE31_4_2_NATIVE_BINDING_AUDIT_V1.json` and
`backend/foundation/test_phase31_4_2_native_binding_audit.py`. These are diagnostic
additions, not a lifecycle spec V2 or an accepted successor architecture. Migration
0022 was now read completely in three non-truncated ranges; Effectiveness,
Signal/Proposal, release implementation and ADR-0017 were read completely. Other
required inputs were inspected only in part or through prior diagnostic results;
the complete-reading admission requirement remains unmet.

The additional source audit makes the missing downstream governance binding
concrete. Frozen 0022 computes the native Publication operation hash as SHA-256
over UTF-8 `rule_id + ':' + expected_hash + ':' + reason`. Activation uses
`publication_id + ':' + expected_hash + ':' + (predecessor_id or 'ROOT') + ':' +
compatibility_hash + ':' + reason`. Neither is the predecessor specification's
broader canonical governance-operation envelope. Neither hash includes actor,
fresh authority reference, policy, trace or caller idempotency key. Their replay
branches compare native operation material without comparing those original
provenance fields. This is static source evidence; successful SQL replay with
changed authority was **not** executed or established.

Publication has no compatibility/release input. Activation stores and hashes
compatibility, but has no release-evidence or Publication-closure-digest input.
The new evidence retains exact historical-input preimages and nine tests that
demonstrate these distinctions without executing SQL. Changing fields outside
the native hash projection leaves its hash unchanged; changing compatibility
changes Activation's hash. Therefore native hash equality cannot substitute for
the complete successor governance/evidence comparison. These findings refine
the existing B1–B4 integration and idempotency blockers; they do not establish a
new accepted outer contract or an inherent impossibility.

The future successor must specify separate native-operation and governed-admission
material, the producer and retention of the latter, and exact admission/replay/
precommit enforcement. It must distinguish the original business action's
immutable provenance from a newly authorized replay attempt. Release evidence
must not be routed through RuntimeAdoption's release-configuration fields.
Compatibility and the Publication closure must still become exact before
Activation. ADR-0017's Application output-ID exception cannot implement or
silently authorize these additional governance semantics.

Current validation: **87 tests passed, 0 failures, 0 errors, 0 skips**, including
the earlier 78 selected tests and nine new native-binding tests. Django 4.2.22
system check and `makemigrations --check --dry-run` passed under in-memory
auth/contenttypes/Foundation settings with a dummy database. This is not a check
of normal project settings or a PostgreSQL execution. In-memory compilation
covered 353 backend Python files. Database, network, lifecycle and resolver
attempt counters were all zero. All operational tests remain `NOT EXECUTED`.
Raw validation, current hash/integrity checks and exact Git output are retained
in the new audit evidence. The old diagnostic JSON and tests remain unchanged.

Verdict remains **PHASE 31.4.2 — NOT PROMOTED**, P0=0/P1=4. B1–B4 are still open;
all zero-effect declarations in §39 remain true. No ADR-0018, successor policy,
operational V2 package, database or future PostgreSQL authorization was issued.
The requested complete successor remains unfinished.

## 43. NEXT_CODEX_PROMPT

```text
# ISO SMART AI — PHASE 31.4.2 CONTINUATION
# CLOSE THE SUPPORTING FIXTURE PRODUCER AND EXECUTION-DERIVED CONTRACTS
# OFFLINE ONLY — NO POSTGRESQL — NO PHASE 32

Work exclusively in /home/felipe/proyectos/isosmart. Before any discovery or
repository reading, run git status --short there and record exact output, then
git diff --check. Do not inspect sibling repositories. Preserve every existing
file byte-for-byte, including Sidebar.jsx:28 whitespace, migrations 0001–0023,
all Phase 29/31 evidence and the three Phase 31.4.2 diagnostic additions. Keep
0024 absent. Do not reset, stash, clean, stage, commit or reformat unrelated work.
Use only backend/.venv with Django 4.2.22, never .venv312.

Entry: Phase 31.4.2 NOT PROMOTED, P0=0/P1=4. Its report is
docs/transformation/PHASE31_4_2_EXECUTION_DERIVED_GOVERNANCE_BINDINGS_AND_SUPPORTING_SIGNAL_SUCCESSOR_DESIGN_GATE_REPORT.md.
Read its companion diagnostic JSON at
docs/governance/evidence/PHASE31_4_2_SUCCESSOR_DESIGN_DIAGNOSTIC_V1.json
and backend/foundation/test_phase31_4_2_design_gate.py. They are incomplete
diagnostics, never operational authority. Their 78 selected passing tests prove
necessary conditions only. Finish all mandatory semantic reading; do not equate
digest checks, parsed JSON or truncated output with complete reading.

Also read the 2026-09-08 continuation addendum, the new diagnostic
docs/governance/evidence/PHASE31_4_2_NATIVE_BINDING_AUDIT_V1.json and
backend/foundation/test_phase31_4_2_native_binding_audit.py. Preserve them as
historical diagnostics. The current selected suite has 87 passing offline tests,
not an approved V2 package. In particular, native 0022 Publication/Activation
operation hashes and replay checks do not bind all actor/authority/policy/trace,
caller-key, release-evidence and closure material required by the successor.
Define exact separate governed admission material and its producer, replay and
precommit enforcement. Preserve native SQL formulas. Do not claim native hash
equality proves the broader contract, or place release evidence into a prohibited
RuntimeAdoption operation. Retain original-action and fresh-replay authority
provenance distinctly without freezing a future approved authority outcome.

Read AGENTS.md; reports Phase 31.3,31.3.1,31.4,31.4.1,31.4.2; predecessor blocker
and diagnostic JSONs; ADR-0013–0017; Phase 31.3 Product Policy, exact source,
lifecycle spec, registry and expected closure; migrations 0009,0018–0023;
Application, Signal/Proposal, Review/Decision/Authorization, Effectiveness,
eventing, audit, canonical/delta/release/evidence implementations; relevant
models; full Phase 26 harness and Phase 28.3 relevant lifecycle paths; RLS and
least privilege architecture. Inspect additional controlled Opportunity,
execution, recommendation and agent-input constraints needed by B4, without
executing them. Preserve authoritative implementations.

Resolve all four blockers as one complete append-only successor design:

B1: Model B remains recommended, not adopted. Freeze exact root identity and
eleven non-time values from the diagnostic, approve its exact draft/publish
bootstrap producer/privileges/audits, then authentic persisted timestamps,
commit and independent full-row rereads before Proposal/Delta. Preserve 0021
to_jsonb(r) hashing with the iso-smart-canonical-json-v1 envelope and unchanged
0020 canonical function. Pin and later verify PostgreSQL 18.6, UTF8, UTC,
libc C collation/ctype and exact rendering settings. No Python datetime
substitution, omitted timestamps, guessed times or precreation numerical hash.

B4 first: non-null ORM traversal already reaches 23 classes/77 edges including
ActionPlanDryRun, AgentRun, AgentDefinition and ModelPolicy; this is not complete
closure. Expand SQL-only, nullable conditional and semantic edges, including
RecommendationBasis/AgentRunInput and every event/outbox/audit. Specify a new
NON-OFFICIAL TEST FIXTURE controlled Opportunity defer execution, exact plan,
dry run, approval, authorization, execution/receipt, Opportunity revisions,
Evidence, human Effectiveness review and eligible Signal. No fake minimal rows,
old harness objects, Phase29 reuse, model execution, automatic learning or
protected runtime change. Resolve the old invariance list explicitly through
the successor policy. Define all rows, values, times, actors and authority
provenance; conditional measurement/correction branches must be explicit.

Native Effectiveness, Signal, Proposal, Review, Decision and Authorization
services generate UUIDs internally without output-ID parameters, and AuditWriter
does not expose arbitrary audit IDs. Design an explicit narrow governed fixture
producer satisfying all frozen constraints and deterministic identity requirements.
Do not pretend missing parameters exist, monkeypatch random/time to bypass
semantics, disable triggers, alter protected code or expand ADR-0017's Application
exception. If constraints cannot be reconciled, document exact residual blockers.
Complete every nonfresh Proposal/Review/Decision/Authorization value and rationale;
preserve actual Review outcome, Review-set hashing, fresh authority participation
and native idempotency limitations. A missing producer is a design problem, not
proof of inherent impossibility.

B2/B3: define exact typed schemas, producer, every field, source, candidate,
Publication, intended Activation links, assertions, timestamps, canonical bytes,
hash formula, provenance and retention. Preserve intended evidence IDs. They are
evidence only, never authority/capability/approval/adoption/certification. Separate
prepublication eligibility from postpublication observations: old Publication
required compatibility_release_evidence_hashes cannot create a causal cycle.
Define a preceding Publication graph checkpoint excluding release/final closure,
then release/compatibility and final Publication closure. Export and independently
verify that complete closure BEFORE Activation. Never self-hash the final manifest.

Preserve same experiment a3f8fd64-af24-5b31-977a-bcaf8146c563 and namespace
05611a8a-f662-5b7f-ad24-c4df48d573ec. Preserve truthful existing root/candidate/
Publication/Activation IDs. Complete UUIDv5 labels for every new row, not one slot
per type; check uniqueness and collisions against all Phase28.3/29/31 evidence.
No static future approved authority outcome. Source bytes must remain SHA256
e458cd0bb7eb11f96ce8723b0ab4dea97e4ca60b0e47a6f7e1fb1f38cef66d6b.

Old root target dbaa2e4eff3c980522a916d0cf2f10127e39f0af8dbfdacb469ac3015d8d87db,
compatibility 43c72090f30e90a4f3896b3d194aa264f421189f0589978453136464e270dbc9 and
release 5583dd2939abe5e1e2d602cef33077685df8efb48f0c664812eaee138723d15a remain
SUPERSEDED_PREEXECUTION_EXPECTATION — NEVER EXECUTED in the successor analysis;
preserve historical bytes. Recomputable old Delta is not valid execution authority.

Formalize execution-ready-v2: every future value is prebound or uniquely derived
under a preapproved exact rule over persisted/fresh inputs with zero executor
architectural discretion. Classify EVERY field exactly once as PREBOUND_STATIC,
EXECUTION_DERIVED_PERSISTED, EXECUTION_DERIVED_EXTERNAL_AUTHORITY or the seven
OUTPUT_ID_MAPPED_BY_ADR0017 positions. Supply derivation, source, canonicalization,
policy, provenance, consumers and freezes 0–9. Separate caller keys from native
operation hashes; preserve 0021 claim and 0022 operation formulas. No UNKNOWN,
TBD, zeros, null or invented hash preimages. Full eight-field curation audit
retention and fixed-point schema+semantic closure remain mandatory.

Phase29 stays HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE / RETENTION_CLOSURE_BREACH.
Publication e97576de-d4ef-520d-8592-d376ed401221 and missing audit
12d811ab-c3b4-4615-8972-75008a36e327 are never operational dependencies.

Only if B1–B4 fully close, create next sequential ADR (0018 if still available),
successor Product Policy, complete lifecycle spec V2, semantic registry V2,
expected closure V2, append-only continuation report and real offline acceptance
tests. Do not overwrite this diagnostic report or create an approved-looking
partial package. Preserve ADR0017's sole seven-output-ID Application exception.
Promotion authorizes future clean Phase31.4 retry eligibility, not execution now.

Validate offline: complete schema and field coverage, hash/preimage audit, UUIDs,
all positive/negative ordering/support/retention cases, native formulas, relevant
Foundation tests excluding resolver calls, JSON canonical recomputations,
in-memory Python compilation, Django check and makemigrations --check --dry-run
under dummy settings with DB/socket/resolver denial guards. Verify every protected
hash, migration0024 absence, source, new-file whitespace, git diff --check and
final git status. Report exact scopes, failures and omissions. Do not invoke any
PostgreSQL harness, create DB/container/roles, execute migrations, install adapter,
execute lifecycle services, call resolver or real AdminApps/external APIs.

Return one append-only detailed gate report covering all original 43 report
sections, explicit B1–B4 booleans, P0/P1 and all 17 zero-effect counters. Promote
only with complete artifacts, no unknown binding/unexplained hash and P0=0/P1=0.
Otherwise NOT PROMOTED and exactly one self-contained blocker continuation prompt.
If promoted, supply exactly one self-contained future clean Phase31.4 retry 2
prompt consuming V2, preserving parity, Publication closure before Activation,
live reread, export, teardown gates and zero RuntimeAdoption. Do not advance Phase32.
```
