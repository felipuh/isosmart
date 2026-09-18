# ISO SMART AI — Phase 26 governed KnowledgeLayerRule application POC

## 1. Verdict

**PHASE 26 — PROMOTED.** The ephemeral governed learning target application POC passed. This verdict authorizes neither production nor deployment, publication, activation, runtime adoption, a second target/operation, cross-tenant learning, or automatic learning.

## 2. Phase 25.1 authorization

Implementation is restricted to `KnowledgeLayerRule` and operation `learning.knowledge_layer_rule.source_reference.correct` version `v1`, under `KNOWLEDGE_LAYER_RULE_GOVERNED_SOURCE_REFERENCE_APPLICATION_POLICY_V1`. Phase 25.1 policy and ADR-0013 were not edited.

## 3. Migration 0021

`0021_first_governed_knowledge_rule_application_poc` is the sole schema evolution. It adds the exact claim, immutable Receipt/audit, typed target event/outbox, RLS/ACLs, target-specific functions and narrowly scoped compensation-aware validation. Migrations 0001–0020 remain byte-identical.

## 4. Exact operation

The public method/function implements only validated source-reference correction. Its signature has no target type, arbitrary field, arbitrary operation/payload, status, publication or activation parameter.

## 5. Canonical delta

The application reloads the one-to-one canonical delta, re-derives canonical bytes, checks SHA-256, operation/schema/canonicalization versions, exact target tuple, prior locator and published StandardEdition source hash. Phase 24.2 regression confirmed atomic, immutable canonical delta behavior.

## 6. Semantic fingerprint

Fingerprint version `iso-smart-knowledge-layer-rule-substantive-fingerprint-v1` freezes target type, layer/edition identity, lineage/rule identity, logic, evidence expectations, classification and source-reference scheme while excluding only the corrected locator. Forward and compensation Receipts carried the same 64-character SHA-256 fingerprint; the capability independently rejected inequality.

## 7. Governance chain

Proposal, selected Reviews, Decision and Authorization are reloaded and compared on proposal revision/material hash, delta ID/hash, operation ID/version, canonicalization/schema versions and exact target ID/lineage/version/hash. The authorization row is locked and revalidated immediately before mutation.

## 8. Legacy inertness

The inherited Phase 24.2 matrix passed: legacy proposals/reviews/decisions/authorizations remain `LEGACY_INERT`, receive no backfill and cannot cross the application boundary.

## 9. Target lock/revalidation

The exact target row is locked; the full target hash, frozen snapshot, lineage, version and absence of a child are checked after the lock. There is no rebase or latest-target substitution.

## 10. vN semantics

The fixture started as an exact published, runtime-effective `vN`. Its full JSON row was identical before and after forward application and compensation.

## 11. vN+1 semantics

Forward application created exactly one successor with `predecessor=vN`, the approved locator, `status=draft`, `published_at=NULL`, no runtime effect and no external effect.

## 12. vN+2 semantics

Separately governed compensation created exactly one successor with `predecessor=vN+1`, restored the exact pre-forward locator and remained draft, unpublished and non-runtime-effective.

## 13. Lineage head

The unique predecessor edge remained the no-fork authority. The leaf was `vN+1` after forward and `vN+2` after compensation; the tested lineage contained exactly three revisions.

## 14. Runtime-effective rule

The only published/runtime-eligible revision remained the exact `vN` after both operations. No mutable runtime pointer was introduced.

## 15. No-latest-wins evidence

Runtime/recommendation source was scanned for version-order/max-version resolution and the database selector was exercised against published status. Neither draft successor was eligible; no latest-wins adoption was found.

## 16. Shared curator primitive

`normative.foundation_0021_create_rule_successor` is a private `SECURITY DEFINER` primitive used by the existing curator wrapper and governed application wrapper. Direct/public/executor execution is revoked.

## 17. Golden parity

The curator wrapper created a canonical draft successor with exact lineage/predecessor and one curation audit, and rejected a draft predecessor. The learning wrapper shared successor validation while retaining its additional governance and Receipt requirements.

## 18. Target-specific capability

The sole executor capability is `apply_validated_knowledge_layer_rule_source_reference_correction_v1(uuid,text,uuid,uuid,uuid)`. Repository signature tests confirm the absence of generic dispatch or mutation arguments.

## 19. Executor principal

The ephemeral `foundation_klr_app_exec_<run>` role was LOGIN, NOSUPERUSER, NOINHERIT and NOBYPASSRLS, was not an owner, and had only schema usage plus EXECUTE on the exact capability.

## 20. Capability owner

The ephemeral `foundation_klr_app_owner_<run>` role was NOLOGIN, NOSUPERUSER, NOINHERIT and NOBYPASSRLS. It retained only the table/function privileges needed by the fixed capability and had no schema CREATE privilege after installation.

## 21. Catalog evidence

`pg_roles`, `pg_proc`, `aclexplode`, `has_schema_privilege`, `has_table_privilege` and function privilege queries passed. PUBLIC, curator and other runtime principals lacked the application capability; the executor lacked target DML.

## 22. SECURITY DEFINER hardening

All privileged functions use a fixed `search_path=pg_catalog` and fully qualified relations. PUBLIC is revoked, private primitives are inaccessible, dynamic SQL exists only in migration-time identifier-safe role setup, and a hostile `pg_temp,public` search path could not hijack execution.

## 23. DML denials

Direct executor INSERT, UPDATE and DELETE against `normative.knowledge_layer_rule` were denied. Arbitrary successor construction, publication and activation are absent from the executor interface.

## 24. Idempotency

A durable application identity binds Proposal, Decision, Authorization, operation/version, delta hash, exact target and optional forward Receipt. Exact replay returned the same Receipt/successor; changed actor provenance conflicted, and a wrong expected delta hash was rejected even on replay.

## 25. Concurrency

Two real concurrent forward attempts produced one `vN+1` plus deterministic replay. Two concurrent compensation attempts produced one `vN+2` plus deterministic replay. No fork was observed.

## 26. TOCTOU

After authorization against an exact published rule, a legitimate curator successor was created first. Application then failed closed because the authorized target was no longer the lineage head; it created no application child.

## 27. Application Receipt

The immutable Receipt binds application identity, governance chain, operation/delta versions and hash, before/after target tuples and hashes, predecessor, locators, fingerprint, actor/trace, target event/outbox/audit, optional forward Receipt and the explicit false publication/runtime/external-effect flags.

## 28. Target Event/Outbox/Audit

Each successful application atomically produced one typed `knowledge_layer_rule.source_reference_corrected` schema-v1 event, one pending platform outbox row and one exact curation audit. It did not emit a generic `target.updated` event.

## 29. Application event/audit

No separate lifecycle event/outbox was introduced because the policy did not require one. One immutable application audit per Receipt records the exact governance/target/hash/actor/trace proof; rollback placeholders for absent lifecycle artifacts remained no-ops inside the same transaction.

## 30. Atomic transaction

The service owns one Django transaction on the dedicated application connection: bind trusted context, claim, governance validation, lock/revalidation, delta/fingerprint proof, successor, target event/outbox/audit, Receipt and application audit, then commit. The inner primitive explicitly rejected autocommit/direct invocation.

## 31. Forward rollback matrix

All 17 injection points passed (17/17). Each forced failure left claim, successor, Receipt, event, outbox and audits unchanged and retained the exact `vN`.

## 32. Compensation governance

Compensation used separate Proposal, canonical delta, Review, Decision and Authorization targeting the exact Receipt-produced inert `vN+1`. The database requires it to restore the exact pre-forward locator and revalidates the forward Receipt/runtime `vN`.

## 33. Compensation Receipt

Exactly one compensation Receipt linked the forward Receipt, `vN+1` and `vN+2`, retained the common fingerprint and recorded `result_published=false`, `runtime_effect_changed=false` and `external_effects=false`.

## 34. Compensation rollback matrix

All 17 compensation injection points passed (17/17). No partial `vN+2`, claim, Receipt, event, outbox or audit committed; `vN` and `vN+1` remained intact.

## 35. Stale compensation

A second independently governed compensation chain targeting the now-stale `vN+1` was denied after `vN+2` existed. No lineage rewriting or rebase occurred.

## 36. Historical provenance

Exact proposal target provenance and protected Recommendation, RecommendationBasis, AgentRun, AgentRunInput and KnowledgeLayerBinding digests were unchanged. No existing reference was rebound.

## 37. Normative invariance

Pre/post digests matched for Standard, StandardEdition, Clause, RequirementControl and EvidenceCoverage. Only the isolated non-certifiable test rule lineage gained its two authorized drafts.

## 38. Runtime invariance

The published selector continued to return only `vN`; recommendation/runtime protected-state digests matched and no draft was adopted.

## 39. ModelPolicy/AgentDefinition invariance

Full digests for ModelPolicy and AgentDefinition matched. No model, autonomy, human-gate or guardrail state changed.

## 40. Forward/reverse migration

Before application history, `0001..0021 -> 0020 -> 0021` passed on PostgreSQL 18.6. The reverse restores the prior proposal/current-target/rule-guard functions and removes only Phase 26 grants and objects.

## 41. Retained-history policy

After Phase 26 history existed, downgrade to 0020 failed closed with the explicit forward-only retained-history error. No Receipt, event, audit or successor was deleted.

## 42. 62+ acceptance results

The Phase 26 harness reported **113/113 PASS**, including the 62 required categories, 34 material rollback assertions, concurrency, replay/conflict, stale races, invariance, ACL/RLS, runtime and teardown evidence.

## 43. Inherited regressions

The final PostgreSQL run inherited and passed Phase 9/16/17/19/20/21/23/24.2 chains. Phase 24.2 additionally reported exact canonical delta/governance binding, legacy inertness, 7/7 rollback and protected-target invariance.

## 44. Backend/foundation results

Foundation: **100 PASS, 0 FAIL, 0 SKIP**, 0.072 s (baseline 97; delta +3). Explicit full backend apps: **198 PASS, 0 FAIL, 0 SKIP**, 3.844 s test time (baseline 195; delta +3). `manage.py test` without labels discovers zero in this repository layout, so the full installed app set was enumerated explicitly.

## 45. Django integrity

`manage.py check`: PASS, zero issues. `makemigrations --check --dry-run`: PASS, no changes detected. Python compilation of the foundation package: PASS.

## 46. Migration hashes

Promoted migrations 0001–0020: **20/20 MATCH**. Exact SHA-256 values remain those recorded in Phase 25.1. New migration 0021: `e796910c1660f701c3457b020792a158c06d3e58135a7ebba1728bd8b33c7a97`.

## 47. Source hashes

Authoritative sources: **10/10 MATCH**: DOCX `8308bde9…`, Draw.io `e0a59c91…`, Mermaid `11c2b461…`, XLSX `952d8ac9…`, JSON `c41e847e…`, SQL `de1b4899…`, nodes CSV `ecaecd25…`, edges CSV `30e3c052…`, OpenAPI `29ac5c2d…`, import guide `eb42315c…`. Direct ZIP/XML/text/JSON/CSV inspections remained valid.

## 48. Governance hashes

All unchanged: Phase 25.1 policy `1a5f7c78…`; ADR-0013 `8fa5852a…`; Phase 25.1 report `f0fd1e6f…`; Phase 24.2 report `a022736f…`; Phase 23 report `4cfe38a2…`; governed-learning policy `7d9c2fe3…`; implementation authorization `04458c4f…`; proposal review/application boundary `2d5beaeb…`.

## 49. Protected targets

The harness compared exact count/JSON aggregate digests across normative, learning, recommendation, model, agent and binding tables. All protected targets outside the isolated POC lineage matched their baseline state.

## 50. Zero external effects

Business effects were zero: no HTTP/provider/tool notification, AdminApps/MedSupplier/object-storage write or deployment. Subprocesses were confined to creating and destroying the isolated PostgreSQL test environment.

## 51. Teardown

Final run `20260903T003052Z_f66933` used Podman and official PostgreSQL 18.6 at sanitized endpoint `127.0.0.1:44563`, database `foundation_gate_20260903t003052zf66933`, dedicated per-run roles, an isolated named volume and temporary directory. Test infrastructure used scoped `podman run/volume create` and `podman rm --force/volume rm`; container absent, volume absent and temp directory absent all passed. Failure-path runs also reported teardown PASS.

## 52. Residual risks

No P0 or P1 remains within the POC scope. Production readiness is deliberately unresolved: ambiguous commit reconciliation, capability disablement, operational repair/observability, retained-history deployment procedure, publication authority, activation authority, release governance and effectiveness assessment require a post-POC design gate. This POC must not be used to activate either draft.

## 53. Final verdict

**PHASE 26 — PROMOTED.** Exact governed source-reference correction and separately governed compensation passed on real isolated PostgreSQL 18.6 with unchanged semantic fingerprint and runtime-effective `vN`, least privilege, atomicity, idempotency, concurrency, complete rollback matrices, inherited regressions, frozen hashes, zero external effects and verified teardown. Meaning: **ephemeral POC passed only**.

| Component/test | State | Evidence | Risk/next action |
|---|---|---|---|
| Authorization and exact capability | PASS | Fixed v1 operation/signature; governance tuple revalidated | Keep single target/operation |
| `vN -> vN+1 -> vN+2` | PASS | Exact linear lineage; drafts inert; common fingerprint | Do not publish or activate |
| Atomicity | PASS | Forward 17/17; compensation 17/17 | Design ambiguous-commit recovery |
| Concurrency/idempotency | PASS | One child plus deterministic replay in both paths | Add operational reconciliation gate |
| Least privilege/security | PASS | Catalog, ACL, RLS, DML denial, hostile path | Define capability disable procedure |
| Runtime/protected state | PASS | Runtime stays `vN`; protected digests match | Preserve explicit runtime adoption boundary |
| Regression/integrity | PASS | PG 113/113; foundation 100/100; backend 198/198 | Continue frozen baseline discipline |
| PostgreSQL lifecycle | PASS | Official 18.6; final run and teardown verified | No reuse of this ephemeral environment |
| Production/publication/activation | NOT AUTHORIZED | Explicit Phase 26 boundary | Next phase is design gate only |
