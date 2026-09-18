# Phase 31.4 — Clean Retry 3 — NOT_PROMOTED

Date: 2026-09-17. Stage A stopped on demonstrated frozen business-semantic
contradictions under request sections 27 and 53. Stage B was not entered.
The initial absence of production components is **not** the failure reason.

## A — Production runtime implementation

### Decisive source/contract contradictions

The frozen V2.4 ActionPlan is
`qms.action_plan::ae682a8f-d782-5b27-a148-aa10a940e03a`.
Its relevant values are `EXACT_LITERAL`, not runtime output slots.

| Frozen requirement | Native requirement | Evidence and consequence |
| --- | --- | --- |
| `/field_bindings/27/fields/10/value_binding/typed_value` is `["synthetic-test-only"]` | `ActionPreparationService.prepare_action_plan` calls `_preconditions`; each member must be an object with identity, type and expected value | Real Python invocation raises `ValueError: preconditions[0] must be an object` before the trusted transaction boundary. |
| `/field_bindings/27/fields/12/value_binding/typed_value` is `0` (A0) | Migration 0015 rejects `p.required_autonomy<>3` | The required `opportunity.defer_evaluation` cannot succeed with the exact frozen plan. |
| `/field_bindings/27/fields/15/value_binding/typed_value` is `"opportunity"` | The same SQL guard requires `p.target_type='Opportunity'` | An additional independently true rejection term. |
| Authorization/AgentRun effective ceilings and AgentDecision autonomy are all `0` | The SQL guard rejects each of these values below `3` | Increasing just the ActionPlan value would still fail, besides violating V2.4. |
| `/field_bindings/27/fields/14/value_binding/typed_value` is `"PHASE31.4.4A TEST ONLY — ActionPlan — target_id"` | Migration 0015 reads the opportunity using `p.target_id::uuid` | The frozen text is not a UUID. This is a further source-level incompatibility, not a measured SQL execution. |

Python evidence: `backend/foundation/action_authorization.py:102`, `:211`,
`:224`, `:240`. The function persists the normalized preconditions and includes
them in the canonical action-plan material; a wrapper cannot silently transform
the input and still retain the exact V2.4 field value and native hash semantics.

SQL evidence:
`backend/foundation/migrations/0015_first_controlled_qms_mutation_poc.py:258`
through the rejection at line 278, and target lookup at line 290. The frozen
guard raises SQLSTATE `42501`, `controlled governance validation denied`.
This is a static proof from the frozen SQL, **not a claim that PostgreSQL was
started or that this exception was observed in a live database**. With A0 and
the mismatched target type, the OR guard necessarily contains true terms even
if other terms evaluate to SQL NULL.

All migration files 0016–0023 were searched for a replacement of that function;
none replaces it. Migration 0016's recoverable execution wrapper calls the
same 0015 primitive, so supported retry/reconciliation does not remove the guard.

The two P1 groups are:

1. `P1-FROZEN-ACTION-PLAN-PRECONDITIONS` — exact frozen JSON cannot be accepted
   or produced by the required native ActionPlan validation.
2. `P1-FROZEN-CONTROLLED-OPPORTUNITY-GOVERNANCE` — exact A0/target material
   contradicts the frozen controlled-execution security/business guard.

ADR-0018 permits enumerated identity replacements and native or
fixture-equivalent validation. It does not authorize replacing precondition
objects with strings, raising frozen autonomy from A0 to A3, changing target
material, or bypassing the 0015 guard. The support-producer contract explicitly
requires native or equivalent validation and declared writes only. Product
Policy V2 fixes non-time business material at Freeze 0. The V2.4 authorization
also requires `business_semantics_changed=false` and `security_changed=false`.
The synthetic authority fixture authorizes operations; it does not replace
their business validation.

Consequently neither a new factory nor a new connection/transaction adapter
can reconcile these requirements. Fabricating successful bindings, inserting
rows around native validation, changing frozen literals, or weakening the
migration would violate the requested scope. Runtime implementation stops at
this semantic gate rather than declaring absent components to be blockers.

### Original blocker and implementation disposition

The historical original blocker is
`P1-RUNTIME-BOOTSTRAP-CONCRETE-OPERATION-BINDINGS-ABSENT`.
It is not marked closed. This run added four reproducible semantic diagnostic
tests and a guarded offline verification runner. It did not create a partial
production factory or report metadata callbacks as real operation bindings.

| Component / gate | This run's result |
| --- | --- |
| Production composition root / authorized runtime factory | Not implemented after the frozen-semantic stop; not the reason for the stop |
| 29 BoundOperations / concrete transaction adapter / execution port | Production composition not proved |
| Synthetic authority reader/store | Existing implementation retained; fixture integrity and six authority tests passed, including declared revision change and mocked rollback |
| POC connection provider / Django PostgreSQL binding / live installer binding | Not constructed or exercised |
| 33 phase handlers | Existing phase definitions and structural tests pass; production execution of 33 handlers not proved |
| Correction/closure record | Not created: offline P1 is not zero |
| Successor operational manifest V3 | Not created: implementation/test completion gate was not reached |
| `FINAL_EXPECTED_OPERATIONAL_MANIFEST_SHA256` | Not available; no final manifest exists |
| Implementation freeze / Stage B authorization | Not reached |

The authority blocker remains CLOSED. Its unchanged byte hashes are:

- Fixture: `d6d4391e7e6023d210296895f868fa9f9e1b4fd4a80476ae95e9f327d63665d5`.
- Authorization: `0d9dda57c1650aa4b2ba8fcd042b6981b2b89cdae844e009edc3c1252d4bc8db`.

The fixture has 29 decisions, remains test-only, uses revisioned fresh reads
and the declared TOCTOU transition, and requires no real AdminApps contact.
It was neither recreated nor changed.

### Fresh offline evidence

Reproduce from `/home/felipe/proyectos/isosmart`:

```bash
backend/.venv/bin/python backend/foundation/verify_phase31_4_runtime_semantics_offline.py
```

Exit status 1 is intentional: diagnostic reproduction success does not mean
the production gate passed. Saved raw results, test labels and 43 protected
file hash comparisons are in
`docs/governance/evidence/PHASE31_4_FROZEN_RUNTIME_SEMANTIC_REPRODUCTION_V1.json`.

Final diagnostic artifact SHA-256 values (not an operational manifest):

| Artifact | SHA-256 |
| --- | --- |
| `backend/foundation/test_phase31_4_frozen_runtime_semantics.py` | `44b8adf837b60a302b80dfba3de5adf213bac0535432f9e0c9436b8833524e11` |
| `backend/foundation/verify_phase31_4_runtime_semantics_offline.py` | `6c5723b32a03449e66fe94f7edcf08bb0cd067df9aa4b854d9760c81e8af01ad` |
| `docs/governance/evidence/PHASE31_4_FROZEN_RUNTIME_SEMANTIC_REPRODUCTION_V1.json` | `ed18a5bdd233fc976d199467651bb03775d18caefdc86965d55dabaac7d26e14` |
| Historical Retry5 manifest, unchanged | `3085b8b1c9fcf7448b1898118ed76d55e54fbd976961293c238cef72ece6ba0c` |

| Check | Measured result |
| --- | --- |
| Interpreter / Django | `backend/.venv`, Django 4.2.22 |
| Offline regression | 265 tests: 264 passed, 0 assertion failures, 1 error, 0 skipped |
| New semantic reproduction tests | 4/4 passed; they prove rejection, not lifecycle success |
| Existing authority suite | 6/6 passed |
| Django check | PASS, no issues, scoped auth/contenttypes/Foundation settings |
| `makemigrations --check --dry-run` | PASS, no changes, same isolated settings |
| Python compile | 381 backend files compiled in memory |
| Governance JSON | 39 existing JSON files parsed; generated evidence separately parsed after writing |
| Protected integrity | 43/43 hashes match, including all 23 migrations, source authorities, ADR-0017/0018 and Policy V2 |
| Migration 0024 | Absent |
| Declared counts | 118 members, 1664 fields, 13 DomainEvent paths, 29 operations, 53 security rows, 33 phases |
| Operation classifications | 22 direct native, 1 exact fixture adapter, 5 promoted SQL, 1 governed adapter |
| Database / PostgreSQL start / container start attempts | 0 / 0 / 0 |
| Business lifecycle / network / subprocess / resolver attempts | 0 / 0 / 0 / 0 |
| Offline P0 / confirmed semantic P1 | 0 observed / 2; full promotion gate does not pass |

The single regression error is the existing historical Retry5 manifest
rejecting `backend/foundation/phase31_4_postgres18_environment.py`:
`ManifestVerificationError: member byte integrity failure`.
This file was already in that state before this run and was not modified here.
The historical manifest and its test were preserved. Its stale implementation
hash is not used as the semantic stopping reason, and no successor manifest was
fabricated to conceal it.

The selected suite includes Foundation contract verification, V2 through V2.4
regressions, root/ADR-0017 checks, source reachability/serialization, authority,
environment/no-pull, teardown/failure preservation, manifest tamper and import
closure checks. Tests using mocks establish only their offline assertions.
They do not establish production composition, transaction atomicity, live
security, parity, or creation-through-activation success.

Repository hygiene: exact project root verified; unrelated work preserved;
`git diff --check` retains only the known trailing whitespace at
`frontend/src/components/Layout/Sidebar.jsx:28`. No reset, stash, clean, stage,
commit, pull, or deployment was performed. Initial discovery from the parent
directory listed sibling filenames before the attachment's repository-only
scope had been parsed; no sibling file contents were read or modified. All
edits and subsequent project inspection were inside `isosmart`.

## B — PostgreSQL 18.6 measured POC

**Not executed.** Stage A's frozen-semantic stop prevents Stage B authorization.
There is no newly created POC environment to preserve or tear down.

| Required live measurement | Result |
| --- | --- |
| Image / server version | Frozen specification retained: `docker.io/library/postgres:18.6`, digest `sha256:7341002d2b8c7c5bdd7542a671a95b36196c0b5b888daf454ae4fc33ba5346d7`, image ID `a6638641707cdf047e5d5c2781f437e2e809323cab22c70b280be8389fbb7878`, linux/amd64. No local-image inspection or live server measurement in this run. |
| Migrations / roles / RLS / privileges | Not applied or measured live |
| 33 phases / 29 operations / 118 members / 1664 fields | Not executed or compared live |
| Authority / TOCTOU | Offline reader and mocked rollback tests only; live all-or-zero rollback not measured |
| Events / Outbox / Audit | Native source reviewed and offline checks run; live rows and chain not measured |
| Concurrency / rollback / ambiguous commit | Not exercised live |
| Governed lifecycle / root Model B / dual reread | Not executed |
| ADR-0017 parity / Application | Not executed |
| Publication / premature Activation denial / Activation | Not executed |
| RuntimeAdoption / Phase29 | No operations or reconstruction performed; no live row-count assertion made |
| Deterministic export / independent reread / closure | Not produced or measured |
| Final live P0/P1 | Not measured; Stage A already has two confirmed semantic P1 groups |
| Guarded teardown / residue | Not applicable; no environment created |

The success verdicts are not issued. Production runtime completion and the
PostgreSQL 18.6 controlled POC have not been validated.
