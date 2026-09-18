# Phase 31.4.5 Retry 4 — final support producer, installer, harness, and operational manifest closure report

## 1. Verdict

`PHASE 31.4.5 — RETRY 4 — NOT PROMOTED`

V2.4 is admitted and the offline contract/rendering skeleton is valid, but the
retained package is not executable: the producer maps and validates all 118
members without invoking the exact native operations, and the harness has the
required guards without concrete handlers for the PostgreSQL/lifecycle phases.

## 2. Entry state

The authorized 31.4.5B predecessor was accepted. Five predecessor contract
blockers were closed. `P1-CR2-SUPPORT-PRODUCER-ABSENT` and
`P1-CR2-INPUT-HASH-INVENTORY` entered open and remain open.

## 3. Scope guard / Git baseline

The first repository commands returned root
`/home/felipe/proyectos/isosmart`. The baseline contained the pre-existing
modified/untracked work listed by `git status --short`. `git diff --check`
reported only the preserved `frontend/src/components/Layout/Sidebar.jsx:28`
trailing whitespace warning. No sibling repository was read; no reset, stash,
clean, stage, commit, normalization, or unrelated edit occurred.

## 4. Predecessor hashes

- V2.4: `a102d278bf2e5ca6e9b8bf282f5402a54f52d4690beed2ecbed5145c56539387`
- V2.3→V2.4 changeset: `4204d022492de843d7f6763dfb05f3ce7ec5e166fc4c14de4b8b2c4cb80f27de`
- 31.4.5B validator: `10c8827ddd53fac92b44e4105bb61eec7f2114991309118bf3d3cc48c47e6308`
- 31.4.5B tests: `6672dc688e6748af292090178eb186aa90f0d32b309831265233bd247b4d8456`
- 31.4.5B generator: `934cbaf66895b9e68cc96a7c1c16bd9e2359d69ffe8de70871c52efe5c1e999a`
- Registry V2: `58b8278cbe05b0b5056e058bb3db1eecfc4d576cbef3dc5383c5e894900730fb`
- Closure V2: `80eb1e7f8e857712aa49bcca98f3d27da2b525ba98df16fa34651cf8254cc425`

## 5. Mandatory reading

`mandatory_implementation_reading_complete=true`. A repository-local ledger
read 60 mandatory files / 6,067,186 bytes, including AGENTS, V2.4, V2.3, the
changeset, ADR-0017/0018, policies, Registry/Closure, admission evidence, all
native producer sources, trusted tenant/audit code, and migrations 0001–0023.
Ledger SHA-256: `6547d1684ee4b7962d8d285f6a4b1e3e6728dd1915c40d2a3a56cbc7aa70b2d4`.

## 6. V2.4 admission

The permanent validator passed: 118 members, 13 DomainEvents, 13/13 matrix,
and zero source, identity, writer, serialization, downstream-reference,
physical-type, nullability, enum/CHECK, binding, or freeze defects.

## 7. Implementation inventory

Retained partial artifacts:

- `backend/foundation/phase31_4_v2_4_support_producer.py`
- `backend/foundation/phase31_4_v2_4_security_installer.py`
- `backend/foundation/postgres_phase31_4_clean_retry_3_harness.py`
- `backend/foundation/phase31_4_operational_manifest.py`
- `backend/foundation/test_phase31_4_v2_4_support_package.py`

No authoritative operational manifest was retained because executable closure
failed. A candidate manifest was generated and tested, then removed before
reporting so Clean Retry cannot treat incomplete bytes as authority.

## 8. Producer identifier

The retained plan uses exactly `phase31.4.4-exact-support-producer/v1`.

## 9. Parameterless interface

`build_support_plan()` has no parameters and accepts no caller business data.

## 10. 118-member mapping

The plan maps 118/118 qualified identities with zero duplicates, undeclared
outputs, or unmapped members. This is declarative coverage, not execution.

## 11. Binding renderer

All eight V2.4 binding kinds are recognized. Exact literals and references are
strictly type checked; deferred/native values raise rather than being guessed
or coerced.

## 12. Identity exception inventory

ADR-0018 deterministic replacements and exactly seven ADR-0017 Application
outputs are exposed. No eighth exception or ADR-0019 was added.

## 13. Audit native output handling

Audit identity remains `NATIVE_UUIDV7_OUTPUT`; the partial code never accepts
an arbitrary Audit ID. Native append execution is not yet wired.

## 14. 13-row Event implementation matrix

All 13 rows, sources, identity authorities, Outbox/Audit relationships and four
promoted serialization classifications are mapped. Native calls are not wired.

## 15. Outbox implementation

V2.4 linkage is validated by the permanent matrix. No live Outbox was created.

## 16. Serialization wiring

The required classifications are represented without new locks. The partial
package cannot yet prove each native invocation is reached by its phase handler.

## 17. Transaction composition

The exact per-operation composition is retained and no outer lifecycle
transaction exists. Concrete operation ownership is not executed by the harness.

## 18. Fresh authority/precommit

The contract requires immediate precommit revalidation. No real AdminApps path
was added. Concrete synthetic authority envelopes remain unwired.

## 19. AgentRun

The plan retains `agent_run.started` / `agent_run.completed`, AgentRun identity,
parent-creation serialization and parent-row locking. No execution occurred.

## 20. Action lifecycle

Decision → Plan → DryRun → Approval → Authorization → Execution order remains
in V2.4 and is not collapsed.

## 21. Effectiveness

No successful effectiveness was manufactured; the evidence/evaluation call is
not yet wired.

## 22. Learning lifecycle

Signal → Proposal → Review → Decision → Authorization remains ordered. There
is no automatic learning.

## 23. Root Model B

Draft, governed publication, commit, dual reread and canonical equality phases
are ordered, but concrete handlers are absent.

## 24. ADR-0017 parity

Application is transition-guarded on parity PASS. The differential executor is
not implemented, so parity implementation is incomplete.

## 25. Publication chain

Admission, native Publication, checkpoint, B2, B3, closure, live comparison,
eligibility, Activation admission and native Activation are ordered and guarded.
Their concrete handlers are absent.

## 26. Native release identities

V2.4/migration 0022 native MD5/suffix vectors remain unchanged; no UUIDv5
substitution was introduced.

## 27. RuntimeAdoption prohibition

The 33-phase machine has no RuntimeAdoption phase. Resolver invocations: 0.

## 28. Phase29 prohibition

V2.4 operational Phase29 dependencies remain empty. No reconstruction occurred.

## 29. Installer

An inert statement renderer exists. It has no import-time or live effects. A
complete idempotent executing installer/catalog verifier is not yet wired.

## 30. Roles

Owner is rendered NOLOGIN/NOSUPERUSER/NOINHERIT/NOBYPASSRLS; executor is
LOGIN/NOSUPERUSER/NOINHERIT/NOBYPASSRLS. Both are non-owner by contract.

## 31. SQL security

Fixed `pg_catalog` search path, qualified relations, PUBLIC revoke, exact
EXECUTE grant, and static rejection of dynamic SQL/broad grants are present.

## 32. RLS

All 53 matrix rows are consumed; tenant policies bind trusted tenant plus the
fixed experiment and preserve ENABLE/FORCE RLS. No true predicate exists.

## 33. Privileges

Only contract-declared SELECT and exact function EXECUTE are rendered for the
executor. No broad DML or `GRANT ALL` is present.

## 34. Install verifier

Exact verification expectations are rendered, but a catalog-reading executor
is absent. This is part of the implementation blocker.

## 35. Teardown

The plan removes only ephemeral policies, grants, function and roles.

## 36. Teardown gate

Teardown denies incomplete closure, live/export mismatch, or any blocker. No
finally/context-manager/shell-trap cleanup exists.

## 37. Clean Retry 3 harness

The exact 33 phases are present. `run_clean_retry_3()` verifies the externally
authorized manifest first, then stops because the concrete backend is absent.

## 38. Phase machine

The declared order exactly matches the requested machine.

## 39. Transition guards

Skipping is denied. Application requires parity; Publication requires
admission; B2/B3 require Publication; Activation requires eligibility;
teardown requires the gate.

## 40. Failure preservation

Failure evidence retains current phase, blocker, environment/database/container
identity slots, retained locations, closure state and teardown eligibility.

## 41. Import closure

The verifier computes project-local Python import closure using AST and rejects
missing closure members. No unresolved dynamic import was introduced.

## 42. Operational manifest

`operational_manifest_complete=false`; no authoritative manifest is retained.

## 43. Manifest members

A non-authoritative 81-member candidate demonstrated the required entry schema
and was removed after the executable-package blocker was confirmed.

## 44. Order-sensitive members

The verifier checks migrations 0001–0023, the 15 freeze points and all 33 phases
in semantic order.

## 45. Manifest verifier

External expected hash, schema, path safety, duplicates, byte hashes, V2.4,
Registry, Closure, migrations, 0024 absence and import closure fail closed.

## 46. Manifest negative tests

The removed candidate passed wrong-hash, unsafe-path, duplicate and independent
81-member digest tamper tests. These are not claimed as final package tests.

## 47. External manifest SHA-256

Not published. Clean Retry 3 is not eligible.

## 48. Producer tests

Current focused package: 10/10 PASS.

## 49. Security tests

Role, RLS, privilege, SQL safety and fail-closed teardown static tests PASS.

## 50. Harness tests

Order, skip, parity, Activation, teardown and protected-failure guards PASS.

## 51. Regressions

- V2.4 permanent validator: PASS, 13/13.
- V2/V2.1/V2.2/V2.3/V2.4 focused regressions: 109/109 PASS.
- Authoritative Foundation offline verifier: 155/155 PASS; 372 Python files compiled.
- Django 4.2.22 system check: PASS; migration dry-run: no changes.
- Governance JSON parsing: 32/32 PASS.
- One raw discovery invocation ran 177 tests but had six import/setup errors;
  it is recorded as an invocation error and not counted as functional PASS.
- Two initial direct validator invocations failed before validation because the
  package import root was wrong; the authoritative module invocation passed.

## 52. Implementation hashes

- producer: `c800cd67017bb6f2a06b046062192418b5076ee6c9223d12c0512d89aab198f0`
- security installer: `8427f7e7a42276b060b24f305ed256a50e522425bc2e9d29c28a8390991ea6aa`
- harness: `2efb0f14dcd48723a9ec8cdabb30290f8d27bc57026fb4538130bf185be3a084`
- manifest verifier: `b2674d7a88d3d986f091c765d85521c5132a3f9883da0e35923b4b848751a03e`
- package tests: `17ea256c2281bb8742f1f53c5a5e979d5aacd9bd84e315391625c6066d646570`

## 53. Migration/source/protected hashes

The V2.4 permanent validator verified every frozen migration and authoritative
producer source hash. Migrations 0001–0023 are unchanged, 0024 is absent, and
protected runtime changes by Retry4 are zero.

## 54. Operational criteria NOT EXECUTED

PostgreSQL startup, container/database/role creation, migration application,
live RLS verification, installation, producer/support fixture, DomainEvent and
Audit writes, races, rollback/ambiguous-commit tests, live ADR-0017 parity,
Application, Publication, B2, B3, Publication closure, Activation and teardown
were all NOT EXECUTED.

## 55. Git hygiene

Only isolated partial Phase31.4 files and this report were added. Unrelated work
and the known Sidebar warning were preserved.

## 56. Zero effects

Database, PostgreSQL, container, roles, migrations, producer, fixture, Event,
Outbox, Audit, Opportunity, Effectiveness, LearningSignal, Proposal,
Application, Publication, Activation, RuntimeAdoption, resolver, cutover,
production, staging, shared DB, AdminApps, MedSupplier, external API and
Phase29 reconstruction effects are all zero.

## 57. Blocker closure

```text
P1-V2_1-STRICT-PHYSICAL-TYPE-CONFLICTS=CLOSED
P1-V2_2-AGENT_RUN-START-EVENT-SERIALIZATION=CLOSED
P1-V2_2-AGENT_RUN-SOURCE-IDENTITY=CLOSED
P1-DOMAIN-EVENT-SOURCE-REACHABILITY=CLOSED
P1-DOMAIN-EVENT-SERIALIZATION=CLOSED
P1-CR2-SUPPORT-PRODUCER-ABSENT=OPEN_EXECUTABLE_NATIVE_OPERATION_WIRING
P1-CR2-INPUT-HASH-INVENTORY=OPEN_PENDING_EXECUTABLE_PACKAGE
```

## 58. P0/P1

`P0=0`; `P1=2`.

## 59. Residual risks

The exact 118-member contract plan must be turned into explicit native-operation
calls with retained outputs, fresh authority and precommit hooks. Every harness
phase then needs a concrete handler plus catalog-install verification. Freezing
hashes before that work would authorize a package that necessarily stops.

## 60. Final verdict

`PHASE 31.4.5 — RETRY 4 — NOT PROMOTED`

### Continuation status — 2026-09-10

Work resumed under the report's continuation without database, network,
container, lifecycle or resolver effects. The retained package now additionally
contains `backend/foundation/phase31_4_v2_4_execution_wiring.py`, which assigns
all 118 qualified members to the closed producer/phase set and validates 29
named Python/SQL source operations against frozen repository source. The strict
renderer now evaluates all 145 RFC4122 UUIDv5 derivations and all seven
ADR-0017 mapped identities exactly while continuing to reject unretained live
outputs. The security installer now has a future idempotent three-state path
(exact/absent/partial-conflict), catalog verification and guarded teardown.
The harness now fails closed on every missing phase handler instead of allowing
a no-op phase PASS.

Continuation validation: V2.4 permanent validator 13/13 PASS; combined current
contract/package suite 122/122 PASS; current package suite 13/13 PASS; Python
compilation PASS. Current hashes:

- producer: `768f6f8ac480cb3b38d9e9e336379a71e6551a2227dcb76b0127c635aa4feced`
- security installer: `b037a8f6a196806b19a93e910961ac2eb64590a8aad5be24ddc69a6263698433`
- execution wiring: `0e120148a54757a83ad57696393813b5b17e486c6caaeb4dc273c7a45d60a55b`
- harness: `5446a0a5324531255f66f04e65f5a1b847bea25f1b337205e5337dc075dae568`
- manifest verifier: `b2674d7a88d3d986f091c765d85521c5132a3f9883da0e35923b4b848751a03e`
- package tests: `28b51c1365ed3a132f2b875ab09be74666765b97429db78813aa4faa37b546f3`

The verdict remains NOT PROMOTED because the exact environment backend and
concrete transaction-owning implementations behind the phase handlers are
still absent; the retained placeholder artifact producers intentionally raise
instead of predicting PostgreSQL values. Therefore the authoritative manifest
remains absent and the same two P1 blockers remain open, now narrowed to that
concrete backend/native invocation layer.

## 61. NEXT_CODEX_PROMPT

```text
ISO SMART AI — PHASE 31.4.5 — RETRY 5 — EXECUTABLE NATIVE-OPERATION WIRING AND FINAL OPERATIONAL MANIFEST CLOSURE — OFFLINE ONLY

Work exclusively in /home/felipe/proyectos/isosmart. Begin with pwd, git status --short, git diff --check, and git rev-parse --show-toplevel; require the exact root and preserve all unrelated work plus the known frontend/src/components/Layout/Sidebar.jsx:28 whitespace warning. Never access sibling repositories. Use only backend/.venv and make zero database, PostgreSQL, network, container, lifecycle, resolver, AdminApps, MedSupplier, deployment, production, staging, or shared-system attempts. Do not execute migrations, create migration 0024, modify migrations 0001–0023, change V2.4/Registry/Closure/ADR-0017/ADR-0018, add a lock or identity exception, invoke RuntimeAdoption, reconstruct Phase29, or begin Phase 32.

Authoritative V2.4 is docs/governance/fixtures/PHASE31_4_5B_ROW_LEVEL_EXECUTION_CONTRACT_V2_4.json with SHA-256 a102d278bf2e5ca6e9b8bf282f5402a54f52d4690beed2ecbed5145c56539387. Re-run backend/.venv/bin/python -m foundation.phase31_4_5b_source_reachability_validator from backend and require 13/13 PASS before editing. Read the Retry4 report and inspect the retained partial files: phase31_4_v2_4_support_producer.py, phase31_4_v2_4_security_installer.py, postgres_phase31_4_clean_retry_3_harness.py, phase31_4_operational_manifest.py, and test_phase31_4_v2_4_support_package.py.

Close exactly two P1s without architecture changes. First, replace the producer's plan-only boundary with explicit, parameterless, experiment-locked orchestration that invokes every V2.4-named native/source operation in its own trusted transaction, renders all 1664 fields under strict types, retains every native/deferred output before downstream use, performs exact immediate precommit revalidation and postcommit rereads, preserves all 13 Event/Outbox/Audit contracts and their promoted serialization classifications, implements the synthetic fresh-authority envelope, root Model B, exact seven-output ADR-0017 parity path, Publication admission/native/checkpoint/B2/B3/closure/live-compare/eligibility chain, Activation admission/native path, and makes RuntimeAdoption and Phase29 operational use unreachable. No generic row writer, selector, caller business inputs, dynamic SQL, outer lifecycle transaction, predicted output, extra row, lock, retry promise, or identity substitution.

Second, replace the inert installer/harness skeleton with a complete future executable backend: idempotent role/function/policy/grant installation and exact catalog verification for all 53 security rows; owner/executor attributes and nonownership; safe search_path, qualified objects, PUBLIC revoke, least privilege, no broad DML; fail-closed teardown limited to ephemeral objects; and concrete handlers for all 33 ordered harness phases. Manifest verification with an externally supplied expected hash must be phase zero and must be the only predecessor of environment creation. Application requires parity PASS, Activation requires the complete Publication chain, and teardown requires P0=P1=0 plus complete live/export closure. Protected failure must persist sanitized evidence and preserve the environment.

Add offline positive/adversarial tests proving concrete native call wiring rather than only plan coverage, all transition/security/teardown rules, exact import closure, and independent tampering for every required artifact class. After every implementation byte and test is final, create docs/governance/evidence/PHASE31_4_5_RETRY4_OPERATIONAL_INPUT_MANIFEST_V1.json last with explicit repository-relative members, ordered migration/freeze/phase sets, complete project-local import closure, no self/report hash, and no mutable member. Run the authoritative offline verifiers with all attempt counters zero, compute the external manifest SHA-256, and publish it in a new completion report and exactly one subsequent Clean Retry 3 prompt only if the executable package is genuinely complete. Otherwise remain NOT PROMOTED and name the exact function/member/phase blocker. PostgreSQL acceptance remains future work.
```
