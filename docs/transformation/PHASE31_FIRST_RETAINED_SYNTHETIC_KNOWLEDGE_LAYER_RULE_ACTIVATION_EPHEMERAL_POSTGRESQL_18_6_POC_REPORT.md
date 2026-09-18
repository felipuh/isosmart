# ISO SMART AI — Phase 31 first retained synthetic KnowledgeLayerRule Activation ephemeral PostgreSQL 18.6 POC

Assessment date: 2026-09-04. Exclusive workspace: `/home/felipe/proyectos/isosmart`.
This is a pre-database failure report, not evidence of an executed Activation POC.

## 1. Verdict

NOT PROMOTED. The pre-database evidence gate found one concrete import blocker: exact Publication `e97576de-d4ef-520d-8592-d376ed401221` requires historical `normative.curation_audit` row `12d811ab-c3b4-4615-8972-75008a36e327`, but the approved retained inputs contain only its foreign-key reference, not its row material. No PostgreSQL environment or Activation was created.

## 2. Entry baseline

The existing Phase 29 repository-only verifier passes and returns:

```text
CREATED=true
APPLICATION_GOVERNED=true
PUBLISHED=true
ACTIVATED=false
RUNTIME_ADOPTED=false
RUNTIME_EFFECTIVE=false
database_reconstructed=false
```

The retained five-member Publication export remains hash-valid. Verifying its release-state summary is not the same as proving that all mandatory relational import dependencies survived teardown. This finding does not erase the historical fact of Publication.

## 3. Initial git status

Captured before edits; this work was pre-existing and preserved:

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

The initial whitespace check reported only Sidebar line 28. No staging, commit or cleanup was performed.

## 4. Frozen hashes

206 existing files across Foundation, backend configuration, governance, ADRs, transformation reports/source artifacts, AGENTS.md and Sidebar were hashed before edits. Repeated comparison: **206/206 unchanged**. Migrations match Phase 30: 23/23; authoritative sources: 10/10.

Review coverage is not overstated: the request, AGENTS.md, Phase 30 policy/report, retained inputs, Phase 29 verifier/exporter/service, ADR-0015 and relevant frozen schema were inspected for this blocker. The full mandatory architectural/source-content reading program was not completed before this fail-closed stop. Hashing sources does not constitute semantic reading/reconciliation. No operational promotion relies on that unfinished review.

## 5. Pre-database offline verification

Executed from the workspace root without PostgreSQL:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend backend/.venv/bin/python -m foundation.verify_phase29_post_teardown
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend backend/.venv/bin/python -m foundation.phase31_activation_preflight
```

The first exits 0. The second intentionally exits 1:

```text
blocker=MISSING_RETAINED_PUBLICATION_CURATION_AUDIT
required_relation=normative.curation_audit
required_row_id=12d811ab-c3b4-4615-8972-75008a36e327
complete_retained_row_occurrences=0
dependency_material_present=false
database_creation_authorized=false
database_created=false
database_reconstructed=false
activation_invoked=false
runtime_adoption_invoked=false
full_activation_preflight_completed=false
diagnostic_material_hash=19da1de4de8d401b702dab8eecf3fa065ba18865fefa00210cc0ef8ac9884b3e
```

Concrete evidence:

- Phase 29 manifest `live_graph.artifact.material.curation_audit_id` names the missing row.
- Migration 0022 line 74 requires `NOT NULL UNIQUE REFERENCES normative.curation_audit(id) ON DELETE RESTRICT`.
- Migration 0008 lines 79–91 requires actual action/entity/actor/trace/payload-hash/timestamp material.
- The Phase 29 harness inserts this curation audit but exports only claim, Publication, governance event, Outbox and governance Audit. It does not export that curation audit row.
- Before adding Phase 31 files, an exact-ID repository-wide search, including hidden files and excluding Git internals/dependency environments, returned only the manifest FK reference.
- Traversal of the five fixed approved retained JSON inputs found zero complete rows with this ID.

The existing verifier does not check this dependency; its success cannot authorize reconstruction.

## 6. Exact candidate

Only candidate `01a0682b-dfc8-7b49-a601-f9bda29a70a5`; lineage/rule predecessor `da72872a-3f3c-5fcd-86f7-0ed33e453522`; version `sN+1`.

```text
full_material_hash=caa24592b509334af4cd60fd7d3f3c43989d864d3f1c6e6d0d3bf83a81871f81
semantic_fingerprint=8465956c1daf27a9838bc1bfb468af3f518ae255b4662b2df40e7b8648516192
lifecycle_hash=0adfd8075cc720140c6e1f0393d286799edac8f352efd9f1969816be83c51e52
```

The retained candidate verifier was executed transitively. No candidate was created or changed.

## 7. Exact Publication

Publication/claim `e97576de-d4ef-520d-8592-d376ed401221`; event `b19e4861-219d-4a07-8faf-656e02dbf9b4`; Outbox `4e78cfe6-8afa-400b-85f5-e5fe72b59e04`; governance Audit `6a3ed87d-a992-4406-8ac8-233017301d35`.

Manifest canonical hash: `51f0b207c790e6ab0c3d67985e161ba0d0cc7b2feb888f545c1ff5eedacf5366`. Disposition canonical hash: `fff3b225184282e48dad30f4e56b16444df4241b5f647f2f3750ee4a254158f1`.

The governance Audit is present but is not the separately referenced curation audit. Retained curator decision `471971df-986f-5a99-ad15-1838f5772e34` is also a different identity and record type.

## 8. Bootstrap/import truthfulness

NOT EXECUTED. Importing the unchanged Publication requires its exact curation audit. Deriving a row from the harness, inserting a fresh audit under the historical ID, substituting the curator decision, changing the Publication FK, or disabling the FK would violate the evidence/immutability boundary. No workaround was used.

The new diagnostic is not an importer or eligibility service. It accepts no arbitrary target/Publication/payload and never authorizes database creation, even if a future dependency-presence check changes.

## 9. Post-import exact comparison

NOT EXECUTED: no import or live row-equality claim.

## 10. Pre-Activation lifecycle state

Only the retained offline state in section 2 exists. Live lineage counts and locks were not simulated.

## 11. Fresh authority

NOT REQUESTED/NOT USED: an earlier prerequisite failed. Intended activator remains `49132b9d-93ae-510a-8de0-ad36ef508f8f`. Historical publisher authority was not reused or represented as fresh Activation authority.

## 12. Actor SOD

Retained identities unchanged; PostgreSQL actor separation was not exercised. No synthetic fresh authority decision was generated.

## 13. First predecessor semantics

Expected predecessor remains explicit `NULL`, not the rule predecessor. No live zero-count proof was claimed.

## 14. Activation lineage

No entries appended or altered. Root/successor concurrency not tested.

## 15. No mutable pointer

No active/current/latest pointer added. Existing runtime and resolver bytes unchanged.

## 16. Claim

No Activation claim or operation identity created.

## 17. Idempotency

Operational tests NOT EXECUTED. The diagnostic material hash is not an Activation idempotency claim.

## 18. Lock order

No DB locks acquired. Required order remains claim → Activation lineage/predecessor → Publication → retained evidence identity → candidate → authority → capability → event/audit streams. No operational proof claimed.

## 19. Concurrency

All five PostgreSQL races NOT EXECUTED: same call, changed material, different contender, capability disable and authority revocation. Historical tests were not reused as Phase 31 proof.

## 20. Capability fence

No Activation capability enabled, disabled, granted or invoked. Admission/precommit tests NOT EXECUTED.

## 21. TOCTOU

Live precommit revalidation NOT EXECUTED. Offline hashes are not a substitute.

## 22. Activation transaction

No transaction or Activation graph member created.

## 23. Activation artifact

ABSENT. No Activation ID allocated or inferred.

## 24. Event

No activation_recorded, new publication, adoption or learning event emitted.

## 25. Outbox

No Activation Outbox or external dispatch. Retained Publication Outbox unchanged.

## 26. Audit

No Activation Audit. Missing historical curation audit not reconstructed.

## 27. Rollback matrix

0/11 executed, NOT PASS. Pre-database denial is not a transaction rollback test.

## 28. Lost response

NOT EXECUTED: no successful Activation commit to replay.

## 29. Ambiguous COMMIT

NOT EXECUTED: no transaction/socket/proxy. No ambiguous result fabricated.

## 30. Reconciliation

No live reconciliation. The diagnostic blocker is not an operational COMMITTED/NOT_COMMITTED/ABANDONED/INCONSISTENT classification.

## 31. Disable/re-enable

NOT EXECUTED. No capability history created or changed.

## 32. Repair authority

No repair principal/decision created. Repair must not fabricate evidence or rewrite history.

## 33. Principals/ACL

No roles/grants created. PostgreSQL catalog and hostile-principal matrix NOT EXECUTED.

## 34. SECURITY DEFINER

No function installed or owner/grant modified.

## 35. Hostile tests

8/8 offline regressions PASS: non-activated retained state, missing-row detection, no DB/runtime import dependency, manifest pin, disposition pin, policy pin, hashed nonzero CLI denial, verification-exception denial. These are not the PostgreSQL hostile-principal matrix.

## 36. Zero RuntimeAdoption

No operational RuntimeAdoption or live resolver invocation. No adoption ID/authority/row/event/Outbox/Audit created. Foundation unit tests use inert/mocked contracts and a dummy database backend.

## 37. Runtime invariance

Protected code and backend settings unchanged. No DB target state touched. This is non-execution/byte invariance, not a successful live Activation comparison.

## 38. Selector scan

Targeted scan of agent_runtime.py, recommendation.py, knowledge_rule_release.py and the new diagnostic found no new rule-runtime selector. Existing matches were ModelPolicy/AgentDefinition revision checks, current-transaction helper names and tenant current_setting. The inspected resolver requires an exact UUID. A full repository operational re-audit was not completed.

## 39. Automatic-learning invariance

No operational LearningSignal/Proposal/Review/Decision/Authorization/application, confidence, ModelPolicy, AgentDefinition, autonomy or compensation mutation.

## 40. Normative invariance

No normative data, rule semantic or certifiability mutation. Ten source-byte hashes unchanged.

## 41. Retained Activation manifest

NOT CREATED. A failure diagnostic is not governed-target-activation-evidence-manifest/v1.

## 42. Live graph verification

NOT EXECUTED. No live Activation integrity_verified=true assertion produced.

## 43. Pre-teardown lifecycle state

NOT APPLICABLE: no database created. Retained state remains section 2.

## 44. Teardown

NOT APPLICABLE: no Phase 31 database, roles, container, volume, proxy/socket, temporary directory/configuration, DSN or credentials created. Nothing destroyed; no fabricated teardown proof.

## 45. Activation disposition

NOT CREATED. ACTIVATED_POC_DISPOSED_WITH_RETAINED_EVIDENCE would be false.

## 46. Post-teardown offline verification

No Phase 31 teardown occurred. Existing Phase 29 offline query passed; Phase 31 dependency check denied. No database reconstruction.

## 47. Offline lifecycle query

```text
CREATED=true
APPLICATION_GOVERNED=true
PUBLISHED=true
ACTIVATED=false
RUNTIME_ADOPTED=false
RUNTIME_EFFECTIVE=false
database_reconstructed=false
```

These are retained Phase 29 facts, not newly generated Activation evidence.

## 48. Migration evolution

0024 remains absent. No schema change can recover missing historical evidence. Removing the frozen FK is not an acceptable fix.

## 49. PostgreSQL exact version

NOT STARTED/NOT QUERIED. Requested version: official PostgreSQL 18.6. No Phase 31 image/server/container/port/database/roles or creation/teardown command exists. Historical attestations were not copied as current observations.

## 50. Regression counts

New tests: 8/8 PASS. Focused evidence/release/preflight suite: 35/35 PASS. Full Foundation: 136/136 PASS. Counts overlap; do not sum them. New Python files: 2/2 in-memory compilation PASS.

Initial minimal test-settings attempt: 135 passed, 1 error because auth was missing from installed apps. Re-run with auth/contenttypes/Foundation passed all 136 without changing application files.

Full backend regression NOT RUN; the failed pre-database workflow did not load deployment settings or touch existing SQLite databases. PostgreSQL acceptance, Phase 26/27.2 harnesses, concurrency, ACL, rollback and reconciliation NOT EXECUTED.

Reproduce Foundation tests with the pinned environment and a dummy DB backend:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend backend/.venv/bin/python -c 'import django; from django.conf import settings; assert django.get_version() == "4.2.22"; settings.configure(SECRET_KEY="inert-phase31-test-only", INSTALLED_APPS=["django.contrib.auth","django.contrib.contenttypes","foundation"], DATABASES={"default":{"ENGINE":"django.db.backends.dummy"}}, USE_TZ=True, DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"); django.setup(); from django.test.runner import DiscoverRunner; raise SystemExit(DiscoverRunner(verbosity=1).run_tests(["foundation"]))'
```

## 51. Django integrity

Django 4.2.22 asserted. System check: no issues. `makemigrations foundation --check --dry-run` via call_command under the same dummy settings: no changes. Foundation-scoped checks, not production/deployment validation.

## 52. Migration hashes

23/23 match Phase 30 and this run's entry:

```text
0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51  backend/foundation/migrations/0001_foundation_tenant_projection.py
1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537  backend/foundation/migrations/0002_projection_organization_user_foundation.py
dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc  backend/foundation/migrations/0003_eventing_immutable_audit_foundation.py
045043275245e5d8068a8e03d122f5fe34b8f9f60b020336e61881550ecea125  backend/foundation/migrations/0004_qms_harmonized_context_foundation.py
96ab33a18252dc0c2e6142f7afdc02a165349d15d50b290b4092c844a1996e86  backend/foundation/migrations/0005_risk_opportunity_objective_foundation.py
033242bd6fe801da0b090a332b9f6d1b07dba77027a0334d1830e845cd51aa95  backend/foundation/migrations/0006_change_performance_measurement_foundation.py
c7f6a2030c9155714093a21fadb571a1cdeb8a121be5598540d4807af62283ec  backend/foundation/migrations/0007_document_evidence_foundation.py
285aecb34d5f7e8c1a1273c9622cde7933809949ac7bdbfca04e577e9e762032  backend/foundation/migrations/0008_evidence_coverage_normative_core_foundation.py
412c645974635959c74a446f64dc0a9b6dfd2a1a50a6a2e346698850e998effc  backend/foundation/migrations/0009_knowledge_layer_foundation.py
c4f37a9a3a8d0d20a049e4e1cc9c0e04feb947cbeec9cea18fa89b7964f57b79  backend/foundation/migrations/0010_governed_recommendation_foundation.py
cdb23edcad75e8a8781815dac847359a368b64d8ea4b607a40d01d5296c863a2  backend/foundation/migrations/0011_agent_definition_run_provenance_foundation.py
7f280e24a8e95858b8144aa6a85fc645245aa2c2d3c2ad5700dfbe19ac0f0fdc  backend/foundation/migrations/0012_agent_decision_human_decision_gate_foundation.py
06177fde1c25d884602a41d03df6d2625e8d15df18d7c66bffdb047348abf34b  backend/foundation/migrations/0013_action_execution_preparation_authorization_foundation.py
ee0e42a7d45803f633ca40d9b0ca20987a20acfdaf3452ee81d721cec29ada33  backend/foundation/migrations/0014_action_execution_synthetic_foundation.py
5e297591c8096938c90b6748d0d3ed22a8099cf8f4537e7f65f8bc6fa5beaba3  backend/foundation/migrations/0015_first_controlled_qms_mutation_poc.py
e922ff20285751193382a17d9fe7e71726511bff659f4e66b97748e6ad43cdd5  backend/foundation/migrations/0016_controlled_execution_recovery_hardening.py
580f16d1cdb10c30bae8f3e3c1667c3c4d2552b895fc9dea053d2c9b6adfaa38  backend/foundation/migrations/0017_effectiveness_check_foundation.py
703a85885a67df953f38ef35302205caeddea249104683f4f751ab20ece0696b  backend/foundation/migrations/0018_governed_learning_foundation.py
c188b638124404bba10cae4c94a678053d49d7a1d07c6e455a48e46524064b50  backend/foundation/migrations/0019_learning_proposal_review_application_authorization_foundation.py
491f21d3422c9c9a5866520f6623d3b9c9bea2139083f0128495dd7207d19894  backend/foundation/migrations/0020_exact_learning_delta_target_operation_contract.py
e796910c1660f701c3457b020792a158c06d3e58135a7ebba1728bd8b33c7a97  backend/foundation/migrations/0021_first_governed_knowledge_rule_application_poc.py
afefd7100a18e5c7324efaeb1af656225b309fd86f08673a8742f7f9f6c2e618  backend/foundation/migrations/0022_inert_rule_publication_activation_runtime_adoption.py
bb9889af836ae1e92ccf75b868c4c6a8c1ab9ba1e7d63464a2cbd749a872e642  backend/foundation/migrations/0023_retained_synthetic_source_reference_application.py
```

## 53. Source hashes

10/10 match Phase 30 and entry. Direct byte hashing, not new semantic reconciliation:

```text
30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6  docs/transformation/source-artifacts/ISO_SMART_AI_Aristas_Red.csv
11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3  docs/transformation/source-artifacts/ISO_SMART_AI_Arquitectura_Completa.mmd
e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa  docs/transformation/source-artifacts/ISO_SMART_AI_Arquitectura_Completa_Lucidchart.drawio
de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e  docs/transformation/source-artifacts/ISO_SMART_AI_DDL_PostgreSQL.sql
8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c  docs/transformation/source-artifacts/ISO_SMART_AI_Especificacion_Inicial_Integrada_v1_2026.docx
952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5  docs/transformation/source-artifacts/ISO_SMART_AI_Mapa_Maestro_Arquitectura.xlsx
c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb  docs/transformation/source-artifacts/ISO_SMART_AI_Mapa_Maestro_Datos.json
ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3  docs/transformation/source-artifacts/ISO_SMART_AI_Nodos_Red.csv
29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8  docs/transformation/source-artifacts/ISO_SMART_AI_OpenAPI.yaml
eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db  docs/transformation/source-artifacts/LEEME_Importacion_ISO_SMART_AI.txt
```

## 54. Governance hashes

All listed files unchanged during this run. Phase 30 records matching hashes for core learning/release policies, ADR-0013–0015, Phase 25.1–29 reports and retained evidence. Phase 30's own entry hash is not a self-attested historical hash.

```text
8fa5852a3cabf822c5213ae10bcae2a61f3910233ff1d915d4d1e1545df6a827  docs/adr/0013-knowledge-layer-rule-lineage-head-runtime-effective-separation.md
fa0e376e802f80e95d3961fabf8f6fe5e337f4b312062123ffd45c31bb300952  docs/adr/0014-separate-knowledge-layer-rule-publication-activation-runtime-adoption.md
57da49dff842349af8a7f3720595d858e96742d782bfe414174f84b8a1f3efea  docs/adr/0015-retained-cross-phase-evidence-and-synthetic-publication-fixture.md
29829c38745db67985fb1523837c79276508bdc9d2136b64442ea238ed13566f  docs/governance/CONTROLLED_QMS_ACTION_POLICY_V1.md
3e2f2b5b3f335bcb425c4b3d8043c2b541de56b0a7b14fbc63b8f48e4392758f  docs/governance/EFFECTIVENESS_CHECK_POLICY_V1.md
43c67505ec3e3d9df0d306012e2036ced7cf437de703e8ff95b709a7af08756d  docs/governance/FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_ACTIVATION_POC_POLICY_V1.md
1d6352eaac748fff42098242b39db63e5f446140cfc935e961eb078d40010ed8  docs/governance/FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_CANDIDATE_POLICY_V1.md
0dfa36804827f272ac7e289beab6e876d27af78b8ae06d3b8a5b5d46b9db8289  docs/governance/FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_POC_POLICY_V1.md
04458c4f1ccead125dd98ddac946ec9d77f8b0212412d13128355b10129c875c  docs/governance/GOVERNED_LEARNING_IMPLEMENTATION_AUTHORIZATION_V1.md
7d9c2fe30548bd18d390d119889c87a93595ac281fa3326691fe486bee49c4ec  docs/governance/GOVERNED_LEARNING_POLICY_V1.md
2d5beaebd5b2df1378c0f425354b45d52ff23dd1a5d158adad46572f7656c514  docs/governance/GOVERNED_LEARNING_PROPOSAL_REVIEW_APPLICATION_BOUNDARY_V1.md
1a5f7c7838c62ba76837c26fcfa4d29655294810f74afed33fdcf69dc373bb79  docs/governance/KNOWLEDGE_LAYER_RULE_GOVERNED_SOURCE_REFERENCE_APPLICATION_POLICY_V1.md
efdd4d8a679c7f18762bfe79c3e876e970f81fedb2848ef5cbf21e7aeb858556  docs/governance/KNOWLEDGE_LAYER_RULE_PUBLICATION_ACTIVATION_RUNTIME_ADOPTION_POLICY_V1.md
263003d342e6bf7a2b56c25dbbb230296b81280a1da45eb347b00898e3231e92  docs/governance/KNOWLEDGE_LAYER_RULE_RUNTIME_ADOPTION_AND_OPERATIONAL_REPAIR_DESIGN_V1.md
9272458cf9dc54f4f722b02502e5e85e9869cebb5e488f0ff15da82e77c07edd  docs/governance/evidence/PHASE28_3_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_CREATED_AND_RETAINED_V1.json
b8a7c9d5a5e423e03c25819d8715e00913edfabdeef57c6611a4906849c34536  docs/governance/evidence/PHASE28_3_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_DISPOSITION_V1.json
57633c70e0d66e2f1a7efbec0f06947cabadc1d4e0f117ca1f0dc4c305dbae9f  docs/governance/evidence/PHASE29_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_DISPOSITION_V1.json
fade372ec41dbeff118ddbb41cd154f8e8adb34799492a56f5e8d14db7e54b72  docs/governance/evidence/PHASE29_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_V1.json
6172874247eaa53d374e687073052c7e9ad8f333bfa94b135234bb8d2e02a600  docs/governance/fixtures/SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_SOURCE_MANIFEST_V1.json
f0fd1e6f142c8fa0b84febff197e80da8af310ccf90e8891e77b1b1d9bbb1ad1  docs/transformation/PHASE25_1_KNOWLEDGE_LAYER_RULE_INACTIVE_SUCCESSOR_COMPENSATION_LINEAGE_BLOCKER_CLOSURE_DESIGN_GATE_REPORT.md
ce36196c4094addba4fb31a512582a05af0113036c3894cb20eb938d1eefedd9  docs/transformation/PHASE26_FIRST_GOVERNED_LEARNING_TARGET_APPLICATION_KNOWLEDGE_LAYER_RULE_SOURCE_REFERENCE_POC_REPORT.md
ca6bf1920200595c73dc2fb654cdce74098b1a4a329813eaf409b52b73d4e5f4  docs/transformation/PHASE27_1_KNOWLEDGE_LAYER_RULE_ACTIVATION_RUNTIME_ADOPTION_BLOCKER_CLOSURE_DESIGN_GATE_REPORT.md
2194fc994417c9339bf8788d3b300f1c7010f4013cc3b322c9db0db2b99d6fb8  docs/transformation/PHASE27_2_INERT_PUBLICATION_ACTIVATION_RUNTIME_ADOPTION_FOUNDATION_IMPLEMENTATION_REPORT.md
3cc3418b48a0899cddc56636316a36cdabbd947d480e7d8e6b5f87d5863ed9e1  docs/transformation/PHASE27_PUBLICATION_ACTIVATION_RECONCILIATION_AND_REPAIR_HARDENING_GATE_REPORT.md
e8bdfcdbcbc07efc6e2f7ac473691ad07789cb467fc099be1c71174325b87afd  docs/transformation/PHASE28_1_EXACT_PUBLICATION_CANDIDATE_EVIDENCE_AND_PRECONDITION_BLOCKER_CLOSURE_REPORT.md
1d73b7e80a5b85730bbcfab1b6af6eb7f3689207b0161fa46f83aff3115118c0  docs/transformation/PHASE28_2_RETAINED_DETERMINISTIC_PUBLICATION_CANDIDATE_EVIDENCE_HARDENED_PUBLICATION_PRECONDITION_INERT_FOUNDATION_IMPLEMENTATION_REPORT.md
d7a35171c86887f322a4fa1bcf3a2de9d0ef36069fb0318792213a6afdc0670d  docs/transformation/PHASE28_3_FIRST_RETAINED_DETERMINISTIC_SYNTHETIC_KNOWLEDGE_LAYER_RULE_CANDIDATE_CREATION_PUBLICATION_POC_AUTHORIZATION_GATE_REPORT.md
bbd5ba9edf897e82da0283bd4acd5202586d503ee60852ee170d716b19661dc1  docs/transformation/PHASE28_FIRST_KNOWLEDGE_LAYER_RULE_PUBLICATION_SOURCE_POLICY_OPERATIONAL_AUTHORIZATION_DESIGN_GATE_REPORT.md
150285ede077ed0bb6ca3dad403a88c0a40363629d3ecdd42460f0180ce0a7df  docs/transformation/PHASE29_FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_EPHEMERAL_POSTGRESQL_18_6_POC_REPORT.md
35a198e5c0dc868d6ce4e32e8a202d1cd2a874dc898769a6ce5d5b414902041b  docs/transformation/PHASE30_FIRST_KNOWLEDGE_LAYER_RULE_ACTIVATION_SOURCE_POLICY_OPERATIONAL_AUTHORIZATION_DESIGN_GATE_REPORT.md
```

## 55. Runtime hashes

Unchanged from entry. Protected Foundation values also match Phase 30 where listed there:

```text
148370f559413b58561ac1d61e4ca10e19e91f04540aaa525a8d8447d8ca3818  backend/backend/models.py
1da64d5f1c8248a2c2e2e9cc586424bde185c85efd467923be28d5c1f2d170ba  backend/backend/settings.py
6767e2098365536b88d4d8e9afdaef0f8b796383c79d7f40e0e0ea91b964ec2d  backend/foundation/agent_runtime.py
461459401abb354b22c42eec05dcd9805e4fd7800554c67b96aee8885c6734ef  backend/foundation/audit.py
c7620cdfb0b51a0c1e022358dcbdae8a7e56b363e182dc09aa11ec675ecf95b8  backend/foundation/eventing.py
99d228984efe4bba15c76f91e157f2ddd66d8aec9b5bf153a21c095fd57ed8cf  backend/foundation/governed_learning_application.py
a7b0477f48120b852d9ec510d30e85d4700f5c0ba970e3ed3c9e244b1be4d7e9  backend/foundation/knowledge_rule_release.py
9dd94c945dd0c256c3872e82b45760b06c066a4364e3dc3d833d56c09645c244  backend/foundation/models.py
0211b25081cc90f61d6497faf101fad42d5a92cd960f5463b2df1efb09f0df95  backend/foundation/postgres_phase26_harness.py
b089ddf3fc37456041677d120348cb01e036897fbc57357f94dcb05888aeb9c8  backend/foundation/postgres_phase27_2_harness.py
655fbdd18437f3d04a838c4dfad0b5b5fb3f6cc2e3d53d29fcc21a22acc6648c  backend/foundation/recommendation.py
e128eead2a506d5181bc182e4cd94e18f98471832b795e675ea10e88c4c4c362  backend/foundation/test_knowledge_rule_release.py
e11ef3322b1d8ea5621072cb978f566d2c7ef90496eee7835506e7c99874741c  frontend/src/components/Layout/Sidebar.jsx
```

## 56. Git hygiene

Repeated `git status --short` preserves prior work. `git diff --check` reports only pre-existing Sidebar line 28 trailing whitespace. New files are separately whitespace-checked because their parent directories were already untracked:

- backend/foundation/phase31_activation_preflight.py
- backend/foundation/test_phase31_activation_preflight.py
- docs/transformation/PHASE31_FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_ACTIVATION_EPHEMERAL_POSTGRESQL_18_6_POC_REPORT.md

No AdminApps, MedSupplier, design-system or unrelated user files modified.

## 57. External effects

```text
production effects = 0
staging effects = 0
shared database effects = 0
RuntimeAdoption effects = 0
runtime cutover effects = 0
normative effects = 0
automatic learning effects = 0
external business effects = 0
Activation POC effect = 0 (blocked before database creation)
```

Exactly-one Activation was NOT achieved.

## 58. Residual risks

An authentic audit export may exist outside approved repository inputs; none was found here. Any later supplied evidence needs original retention provenance, full material and cross-link verification. UUIDs or code-derived rows are insufficient. Additional blockers may emerge after this dependency is resolved. Full required reading and operational acceptance remain unfinished.

## 59. P0/P1

Observed P0 violations/forbidden effects caused by this run: 0. Confirmed blocking retained-evidence completeness issue: 1 P1. Unexecuted criteria remain unproven, not PASS. Promotion conditions are not satisfied.

## 60. Final verdict

**PHASE 31 — NOT PROMOTED**

The stop boundary was honored. Continuation concerns only the missing retained Publication dependency, not RuntimeAdoption.

## 61. Exactly one NEXT_CODEX_PROMPT

```text
NEXT_CODEX_PROMPT

ISO SMART AI — PHASE 31.1 — EXACT RETAINED PUBLICATION CURATION-AUDIT EVIDENCE BLOCKER CLOSURE — OFFLINE ONLY

Work exclusively in /home/felipe/proyectos/isosmart. Phase 31 stopped before creating any database or Activation, with blocker MISSING_RETAINED_PUBLICATION_CURATION_AUDIT. Read AGENTS.md and the Phase 31 report, and complete relevant mandatory historical reading before any new design decision. Preserve migrations 0001–0023, historical reports/ADRs/policies/evidence, all authoritative sources, protected runtime/application files and unrelated changes including frontend/src/components/Layout/Sidebar.jsx:28.

Only candidate 01a0682b-dfc8-7b49-a601-f9bda29a70a5 is in scope: lineage/rule predecessor da72872a-3f3c-5fcd-86f7-0ed33e453522, version sN+1, full hash caa24592b509334af4cd60fd7d3f3c43989d864d3f1c6e6d0d3bf83a81871f81, semantic fingerprint 8465956c1daf27a9838bc1bfb468af3f518ae255b4662b2df40e7b8648516192, lifecycle hash 0adfd8075cc720140c6e1f0393d286799edac8f352efd9f1969816be83c51e52.

Only Publication e97576de-d4ef-520d-8592-d376ed401221 is in scope. Its retained manifest is docs/governance/evidence/PHASE29_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_V1.json, canonical hash 51f0b207c790e6ab0c3d67985e161ba0d0cc7b2feb888f545c1ff5eedacf5366, disposition canonical hash fff3b225184282e48dad30f4e56b16444df4241b5f647f2f3750ee4a254158f1. The artifact references normative.curation_audit ID 12d811ab-c3b4-4615-8972-75008a36e327, required by frozen migration 0022. This is distinct from governance Audit 6a3ed87d-a992-4406-8ac8-233017301d35 and curator evidence 471971df-986f-5a99-ad15-1838f5772e34.

Reproduce the offline Phase 31 diagnostic and its eight tests. Determine only whether authentic already-retained pre-teardown material for the exact missing audit exists in this workspace or evidence explicitly supplied by the user. Require complete historical id/action/entity_type/entity_id/actor_id/trace_id/payload_hash/occurred_at, verifiable retention provenance and exact linkage to the Publication. References, summaries, repeated diagnostic findings or deterministic reconstructions from the harness do not qualify.

Do not create PostgreSQL, import material, regenerate historical rows, run the Phase 29 publication harness, create another Publication/candidate/learning operation, allocate Activation/adoption IDs, invoke Activation or RuntimeAdoption, change runtime/configuration, rewrite frozen evidence, remove/relax the FK, deploy, access production/staging/shared databases or AdminApps DB, call providers or produce external effects. Do not advance to Phase 32.

If authentic complete retained material is unavailable, keep NOT PROMOTED and request that exact evidence or an explicit governance decision about the unavailable dependency. Do not invent a replacement or broaden scope. If authentic evidence is supplied, assess it offline and document an append-only evidence-extension proposal without overwriting the original manifest or claiming that the full Activation gate has passed. Accepted-input changes require explicit governance approval before another Activation POC.

Report evidence searched, provenance/hash/cross-link results, frozen-file checks, tests, remaining blocker and zero DB/Activation/RuntimeAdoption effects. Produce one blocker-only verdict and one next prompt; this offline closure does not authorize operational Activation.
```

| Component/test | State | Evidence | Risk/next action |
|---|---|---|---|
| Retained Phase 29 lifecycle | Existing verifier PASS | Published; not activated/adopted | Not import-dependency closure |
| Publication curation audit | BLOCKED | FK reference only; no row | Require authentic retained evidence |
| Phase 31 offline denial | 8/8 PASS | Exit 1; pinned input hashes | No DB creation authority |
| Focused / Foundation | 35/35 / 136/136 PASS | Django 4.2.22; dummy DB | Not PostgreSQL acceptance |
| Operational matrices | NOT EXECUTED | No database or Activation | Remain prerequisites |
| Migrations / sources | 23/23 / 10/10 MATCH | Exact inventories | Preserve |
| Activation manifest/disposition | ABSENT | No Activation occurred | Never fabricate |
| RuntimeAdoption / external effects | ZERO | No operational calls | Boundary remains closed |

