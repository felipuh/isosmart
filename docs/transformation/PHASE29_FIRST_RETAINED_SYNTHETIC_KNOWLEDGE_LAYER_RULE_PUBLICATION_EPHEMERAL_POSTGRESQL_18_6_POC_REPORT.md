# ISO SMART AI — Phase 29 first retained synthetic KnowledgeLayerRule publication ephemeral PostgreSQL 18.6 POC

- Date: 2026-09-03 (`America/Costa_Rica`)
- Workspace: `/home/felipe/proyectos/isosmart`
- Nature: exact-candidate-only, ephemeral, synthetic, non-authoritative, non-normative, non-licensed, test-only, non-production

## 1. Verdict

The exact retained Phase 28.3 candidate completed one real native publication
transaction in isolated PostgreSQL 18.6. Its publication evidence was retained
before teardown, all scoped resources were destroyed, and the exact release
state was then verified offline without database reconstruction.

## 2. Entry baseline

Entry was Phase 28.3
`PROMOTED FOR FUTURE EPHEMERAL PUBLICATION POC OF EXACTLY ONE RETAINED SYNTHETIC CANDIDATE`.
Promotion did not mean the candidate was already published. Migrations
0001–0023, Phase 25.1–28.3 history, ADR-0013–0015, policies, ten sources,
retained creation/disposition evidence and protected runtime/application files
were treated as frozen.

## 3. Initial git status

Initial `git status` showed the pre-existing modified integration, leadership,
SQLite and frontend files plus the untracked Foundation/governance/
transformation work from earlier phases. No unrelated change was cleaned,
reset, stashed or overwritten. The known Sidebar line 28 whitespace remained.

## 4. Frozen hashes

Migrations 0001–0023 matched the 23 Phase 28.3 hashes byte-for-byte. Protected
hashes matched: models `9dd94c94…5c244`, application service
`99d22898…d8cf`, release service `a7b0477f…d7e9`, eventing
`c7620cdf…95b8`, audit `46145940…34ef`, AgentRun `6767e209…c2d`,
Recommendation `655fbdd1…6648c`, Phase 26 harness `0211b250…f95` and Phase
27.2 harness `b089ddf3…eb9c8`.

## 5. Exact candidate

- candidate `01a0682b-dfc8-7b49-a601-f9bda29a70a5`;
- lineage/predecessor `da72872a-3f3c-5fcd-86f7-0ed33e453522`;
- version `sN+1`;
- full hash `caa24592b509334af4cd60fd7d3f3c43989d864d3f1c6e6d0d3bf83a81871f81`;
- semantic fingerprint `8465956c1daf27a9838bc1bfb468af3f518ae255b4662b2df40e7b8648516192`;
- lifecycle hash `0adfd8075cc720140c6e1f0393d286799edac8f352efd9f1969816be83c51e52`.

## 6. Retained evidence import

Offline verification preceded all target creation. The zero-selector
`import_phase29_exact_retained_candidate_v1()` embedded only the verified
manifest contract and accepted no rule ID, payload, target, operation or
field/value arguments. It imported 20 immutable retained snapshot rows plus
the exact synthetic Standard, Edition, Layer, root and candidate.

## 7. Import truthfulness

The import was recorded as Phase 29 retained-evidence bootstrap into a new
ephemeral environment. Fresh database timestamps were used; historical
timestamps remained only inside immutable retained snapshot material. It did
not claim production restore, Phase 26 recovery, new learning, publication,
Activation or RuntimeAdoption.

## 8. Exact comparison

Every imported source/creation/disposition/root/candidate/Signal/Proposal/
Delta/Review/Decision/Authorization/Receipt/application-event/outbox/audit/
curator/policy snapshot was re-read and byte/material compared against the
verified manifest. Candidate ID, lineage, predecessor, version, source, three
hashes and all material hashes agreed before capability became eligible.

## 9. Import state machine

Append-only state history was exactly:

```text
RETAINED_EVIDENCE_ONLY
→ IMPORTED_UNPUBLISHED
→ PUBLICATION_PRECOMMIT_ELIGIBLE
→ PUBLISHED
```

No caller could directly set state and publication required the exact first
three states. Immediately after import the candidate was draft with
`published_at=NULL`; Publication, Activation and RuntimeAdoption were zero.

## 10. Publication authority

Fresh server-resolved synthetic AdminApps fixture decision
`bbb38a07-fa45-5e1a-b8cc-74c9b1edbda8`, hash
`8fef83a121eba045bc659c82bde715b56dc78490068e03d3d92d93e93b860069`,
authorized actor `8069fbeb-0ef6-582c-8f3b-ff88e606c869`. It was active,
MFA-verified, global, exact-permission scoped and valid for ten minutes. The
Phase 28.3 eligibility authority was not reused.

## 11. SOD

The publisher actor was compared as an exact UUID and remained distinct from
proposer, reviewer, proposal approver, application authorizer, application
executor, curator, activator and adopter. Revocation during a publication race
caused precommit denial and full rollback.

## 12. Capability fence

Publication capability was evaluated at admission and immediately before
commit. A concurrent append-only disable caused rollback. Re-enable was a new
decision linked to the disable predecessor; no history row was updated.

## 13. Claim

Claim/publication ID is `e97576de-d4ef-520d-8592-d376ed401221`. Its operation
material binds exact candidate/lineage/version, three hashes, source manifest,
creation manifest, creation disposition, Receipt, curator, fresh authority,
Phase 29 policy, idempotency, reason and trace.

## 14. Idempotency

Two concurrent identical calls produced one commit and one deterministic
replay of the same Publication. Changed reason/material under the same
publication/idempotency identity returned conflict. No duplicate was created.

## 15. Current leaf

The transaction acquired an exact lineage advisory lock and verified the
candidate via predecessor graph: it was the only leaf and had no successor.
No latest, current, max, timestamp or version-order inference was used.

## 16. TOCTOU

Immediately before mutation and again before commit the boundary revalidated
candidate identity, lineage/predecessor/leaf, draft state, full/lifecycle
hashes, retained Receipt and curator snapshots, authority leaf, SOD, policy,
capability, claim material, and zero Activation/RuntimeAdoption.

## 17. Publication transaction

One transaction committed claim, compatibility status/published time,
Publication, event, outbox, audit and terminal state. The dedicated function
uses `SECURITY DEFINER`, fixed `pg_catalog` search path, qualified objects, no
dynamic SQL and no arbitrary target/operation/status/payload selector.

## 18. Publication artifact

Publication `e97576de-d4ef-520d-8592-d376ed401221` is `NATIVE`, workflow
approved and binds the exact candidate/hash/fingerprint. Its retained material
hash is `b962792f…9c8b`.

## 19. Status/published_at compatibility

Before: `draft`, null. After: `published`,
`2026-09-03T20:18:53.895599+00:00`. Status alone is never accepted as evidence:
the offline verifier requires the complete claim/Publication/event/outbox/
audit/authority/policy graph. The synthetic root received no Publication.

## 20. Event

Exactly one `knowledge_layer_rule.published` schema v1 event
`b19e4861-219d-4a07-8faf-656e02dbf9b4` committed. Its sanitized payload binds
Publication, candidate, lineage/version, all hashes, source, Receipt, curator,
authority, policy, trace and timestamp, and explicitly records no activation,
adoption, runtime effect or licensed content.

## 21. Outbox

Outbox `4e78cfe6-8afa-400b-85f5-e5fe72b59e04` points to the exact event and
remained pending for the inert platform destination. No consumer or external
notification was invoked.

## 22. Audit

Immutable audit `6a3ed87d-a992-4406-8ac8-233017301d35` binds exact operation,
artifact, candidate, publisher/authority, policy, operation hash, payload hash,
trace and timestamp. Before/after and provenance are present in the same
payload committed by hash.

## 23. Rollback matrix

11/11 PASS: after claim, authority validation, capability admission, lineage
lock, target revalidation, status update, Publication insert, event, outbox,
audit and immediately before commit. Each left candidate draft/unpublished and
all publication/event/outbox/audit/Activation/RuntimeAdoption deltas zero.

## 24. Concurrency

Same exact material: one commit plus one replay. Changed material: conflict.
Different candidate: impossible through the fixed signature and denied through
the revoked generic native function. Capability-disable and authority-revoke
races both denied the affected transaction at precommit.

## 25. Lost response

Retry after the known successful commit returned the same Publication. No
second record or event was produced. Phase 27.2's independent real connection-
loss test also remained 140/140 PASS.

## 26. Ambiguous commit

The exact committed graph reconciled `COMMITTED`; an unadmitted identity
reconciled `NOT_COMMITTED`. `ABANDONED` still requires an explicit append-only
disposition and timeout is insufficient. Partial/mismatched evidence is
`INCONSISTENT`; the Phase 27.2 four-state matrix passed unchanged.

## 27. Reconciliation

Reconciliation was executed only by the dedicated repair principal. Candidate
status was not used as commit proof and no automatic repair or reconstruction
path exists.

## 28. Capability disable

Disablement blocked the racing new publication and did not change the candidate
outside the rolled-back transaction or alter Activation, RuntimeAdoption or
runtime state.

## 29. Capability re-enable

Re-enable appended a successor governance decision linked to the disable
record. Disable → enable history was preserved.

## 30. ACL/principals

The publisher was LOGIN, non-superuser, NOINHERIT, NOBYPASSRLS and non-owner.
It had no generic rule DML, activation/adoption/application/repair/curator
capability. The generic Phase 27.2 publication and legacy-import functions were
revoked from it for this POC.

## 31. SECURITY DEFINER

The exact publication owner was NOLOGIN, non-superuser, NOINHERIT,
NOBYPASSRLS and non-table-owner. Temporary schema CREATE used only for
ownership transfer was revoked. PUBLIC EXECUTE was revoked. Only the publisher
received the fixed function.

## 32. Hostile tests

Hostile `search_path=pg_temp,public` could not shadow qualified objects;
generic publication was absent from publisher ACL; wrong candidate was absent
from the signature; client authority flags failed typed validation; stale and
revoked authority, disabled capability and changed material denied. Phase
27.2 independently retained the complete publisher/activator/adopter/repair/
worker/projector and PUBLIC ACL matrix.

## 33. Zero Activation

Activation rows and activation events were exactly zero. No activation
function was called.

## 34. Zero RuntimeAdoption

RuntimeAdoption rows and events were exactly zero. No adoption function or
resolver was called.

## 35. Runtime invariance

Runtime behavior delta was zero. AgentRun and Recommendation files retained
their exact hashes and exact-ID resolution. No runtime configuration changed.

## 36. Normative invariance

Normative delta was zero. The synthetic rows were non-official,
non-authoritative, non-normative, non-licensed and disappeared with the POC DB.
No Standard/Clause/RequirementControl/EvidenceCoverage production semantics
changed.

## 37. Automatic-learning invariance

Automatic-learning delta was zero. No new Signal, Proposal, operation,
compensation, ModelPolicy, AgentDefinition or autonomy change occurred.

## 38. Migration evolution

No migration 0024 was required. Exact import/publication support existed only
inside the disposable POC database and was destroyed with it. Migrations
0001–0023 stayed frozen, avoiding a permanent generic import surface.

## 39. Publication evidence manifest

`PHASE29_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_V1.json` was
exported before teardown. Canonical manifest hash is
`51f0b207c790e6ab0c3d67985e161ba0d0cc7b2feb888f545c1ff5eedacf5366`;
file hash is `fade372e…4b72`.

## 40. Live graph verification

Candidate, claim, Publication, event, outbox, audit, authority, policy, source,
Receipt, curator and all hashes were re-read live. Component material hashes:
claim `ad6aca4f…0b94`, artifact `b962792f…9c8b`, event
`212f1b0d…da42`, outbox `3011dee1…1fbd`, audit `829949aa…ef82`.

## 41. Teardown

Run `20260903T201829Z_16bb0b` destroyed database
`foundation_gate_20260903t201829z16bb0b`, 24 scoped roles, container, volume
and temporary context. Absence checks passed. No DSN/password was retained.

## 42. Post-teardown offline verification

Repository-only verification returned:

```text
CREATED=true
APPLICATION_GOVERNED=true
PUBLISHED=true
ACTIVATED=false
RUNTIME_ADOPTED=false
RUNTIME_EFFECTIVE=false
database_reconstructed=false
```

## 43. Publication disposition

Append-only disposition state is
`PUBLISHED_POC_DISPOSED_WITH_RETAINED_EVIDENCE`, canonical hash
`fff3b225184282e48dad30f4e56b16444df4241b5f647f2f3750ee4a254158f1`.
It binds publication manifest, teardown hash `589b7c91…831d` and offline
verification hash `65dd9e28…927e` without changing the publication manifest.

## 44. Offline release-state query

`verify_phase29_post_teardown.py` reads only retained repository evidence and
returns the exact state above. Removing an audit, changing candidate/state or
asserting runtime effect fails closed.

## 45. Regression counts

- Phase 29 PostgreSQL checks: 29 PASS; rollback 11/11.
- Focused retained/release tests: 27/27 PASS.
- Foundation: 128/128 PASS.
- Backend: 226/226 PASS.
- Phase 26 PostgreSQL: 113/113 PASS, forward and compensation rollback 17/17.
- Phase 27.2 PostgreSQL: 140/140 PASS, all four reconciliation states.
- Sources: 10/10 direct read/parse/hash PASS.

## 46. Django integrity

Pinned Django 4.2.22 system check reported zero issues.
`makemigrations --check --dry-run foundation` reported no changes. Python
compilation passed.

## 47. Migration hashes

All hashes 0001–0023 matched the Phase 28.3 frozen inventory, including 0021
`e796910c…a97`, 0022 `afefd710…e618` and 0023 `bb9889af…e642`.

## 48. Source hashes

All ten exact Phase 28.3 source hashes matched. CSV, UTF-8, XML, JSON, YAML and
OOXML ZIP/CRC parsing passed; no source was rewritten.

## 49. Governance hashes

Historical governed-learning/application/release policies and ADR-0013–0015
retained their Phase 28.3 hashes. New Phase 29 publication-only policy file
hash is `0dfa36804827f272ac7e289beab6e876d27af78b8ae06d3b8a5b5d46b9db8289`;
its structured material hash is `fde8534b…fd13`.

## 50. Runtime/protected hashes

All protected hashes listed in section 4 matched. The selector scan found only
historical harness ordering/event-version uses, not a runtime KnowledgeLayerRule
latest/current/head/max/timestamp fallback.

## 51. Git hygiene

Phase 29 added only the exact service/evidence/harness/verifier/tests, one new
publication policy, two retained evidence records and this report. No frozen or
unrelated file was modified. `git diff --check` reported only the pre-existing
Sidebar line 28 trailing whitespace.

## 52. External effects

```text
production effects = 0
staging effects = 0
shared DB effects = 0
activation effects = 0
RuntimeAdoption effects = 0
runtime cutover effects = 0
normative effects = 0
automatic learning effects = 0
external business effects = 0
publication POC effect = exactly one ephemeral synthetic publication
```

## 53. Residual risks

The published revision exists only as retained evidence after teardown and is
not active or runtime-effective. A future activation gate must independently
validate publication evidence, new activation authority, actor SOD, exact
publication binding, capability/idempotency/concurrency/TOCTOU and retained
evidence. This promotion grants no such authority.

## 54. P0/P1

```text
P0 blockers = 0
P1 blockers = 0
```

## 55. Final verdict

**PHASE 29 — PROMOTED FOR EPHEMERAL PUBLICATION POC ONLY**

Promotion does not authorize Activation, RuntimeAdoption, runtime cutover,
production, deployment, another publication target, another learning
operation or automatic learning.

## 56. NEXT_CODEX_PROMPT

Execute **PHASE 30 — FIRST KNOWLEDGE LAYER RULE ACTIVATION SOURCE/POLICY + OPERATIONAL AUTHORIZATION DESIGN GATE — DESIGN ONLY** exclusively in `/home/felipe/proyectos/isosmart`. Read `AGENTS.md`, the complete Phase 25.1–29 reports, ADR-0013–0015, all governed-learning and KnowledgeLayerRule application/publication/activation/runtime-adoption policies, all ten authoritative source artifacts directly, migrations 0021–0023, the Phase 26/27.2/28.3/29 harnesses, the Phase 28.3 creation manifest and disposition, Phase 29 publication manifest `docs/governance/evidence/PHASE29_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_V1.json` with canonical hash `51f0b207c790e6ab0c3d67985e161ba0d0cc7b2feb888f545c1ff5eedacf5366`, and Phase 29 disposition with canonical hash `fff3b225184282e48dad30f4e56b16444df4241b5f647f2f3750ee4a254158f1`. Preserve migrations 0001–0023, every historical report/ADR/policy/evidence artifact, authoritative sources, protected runtime/application files, unrelated user work and the known Sidebar whitespace byte-for-byte. Design only whether exact published candidate `01a0682b-dfc8-7b49-a601-f9bda29a70a5`, lineage/predecessor `da72872a-3f3c-5fcd-86f7-0ed33e453522`, version `sN+1`, full hash `caa24592b509334af4cd60fd7d3f3c43989d864d3f1c6e6d0d3bf83a81871f81`, semantic fingerprint `8465956c1daf27a9838bc1bfb468af3f518ae255b4662b2df40e7b8648516192`, lifecycle hash `0adfd8075cc720140c6e1f0393d286799edac8f352efd9f1969816be83c51e52`, Publication `e97576de-d4ef-520d-8592-d376ed401221`, event `b19e4861-219d-4a07-8faf-656e02dbf9b4`, Outbox `4e78cfe6-8afa-400b-85f5-e5fe72b59e04`, audit `6a3ed87d-a992-4406-8ac8-233017301d35`, source, Receipt, curator, publisher authority and Phase 29 policy is eligible for a future separately authorized ephemeral Activation POC. Evaluate exact retained Publication evidence; source provenance; all hashes; publication and fresh activation authority; actor-level SOD; publication→activation binding; current activation predecessor; exact idempotency and same/different-material concurrency; lineage locks and TOCTOU; append-only capability disable/re-enable; ambiguous COMMIT outcomes `COMMITTED`, `NOT_COMMITTED`, `ABANDONED`, `INCONSISTENT`; activation event/outbox/audit; recovery without pointer rewind; least privilege/RLS/SECURITY DEFINER; hostile tests; retained evidence/teardown design; and zero RuntimeAdoption/runtime/normative/automatic-learning/external effects. Do not create or import a database target, do not activate, do not create RuntimeAdoption, do not change runtime behavior/configuration/resolvers, do not add a migration or grants, do not deploy, and do not access production/staging/shared databases or external systems. If any exact retained Publication evidence is missing, mismatched or reconstructed, emit NOT PROMOTED and address only that blocker; otherwise produce a design-gate report that authorizes at most a future ephemeral Activation POC and still performs no Activation.

| Component/test | State | Evidence | Risk/next action |
|---|---|---|---|
| Exact retained import | PASS | 20 immutable snapshots; exact fixed import | Preserve non-generic boundary |
| Publication | PASS | `e97576de…01221`; complete exact graph | Retained evidence only after teardown |
| Rollback/concurrency | PASS | 11/11; one commit + one replay | Re-prove separately for Activation |
| Authority/SOD/capability | PASS | fresh authority; revoke/disable races denied | New activation authority required |
| Activation/RuntimeAdoption | ZERO | zero rows/events and no calls | Remain prohibited |
| Runtime/normative/external | ZERO | protected hashes and effect counters | No cutover |
| Retention/teardown/offline query | PASS | manifest `51f0b207…f5366`; disposition `fff3b225…158f1` | Never reconstruct |
| Foundation/backend/PostgreSQL | PASS | 128/128; 226/226; 113/113; 140/140 | Phase 30 design only |
| Final risk | 0 P0 / 0 P1 | all Phase 29 gates passed | Activation remains separately gated |
