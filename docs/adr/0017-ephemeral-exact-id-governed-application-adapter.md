# ADR-0017: Ephemeral exact-ID governed Application adapter

- Status: Accepted for the future isolated Phase 31.4 POC only; no execution in Phase 31.3.1.
- Date: 2026-09-04 (`America/Costa_Rica`).
- Succeeds: ADR-0016; preserves ADR-0001–ADR-0016 byte-for-byte.
- Product Policy: `complete-retained-synthetic-klr-lifecycle-poc-policy/v1`.
- Decision gate: [Phase 31.3.1 report](../transformation/PHASE31_3_1_EXACT_ID_APPLICATION_ADAPTER_ARCHITECTURAL_DECISION_CLOSURE_GATE_REPORT.md).

## Context and architectural finding

**YES: the exact-ID Application adapter is a genuine architectural decision.**
Phase 31.3 report §21 identifies it as the only new architectural decision but
then concludes that no successor ADR is needed. A Product Policy specifies
allowed product behavior; it does not replace the required architectural
record for a new privileged execution path. This ADR closes that single
governance P1 by an append-only decision. The earlier report remains historical
and unchanged; its no-successor-ADR conclusion is superseded here only.

Frozen migration 0021's private
`normative.foundation_0021_create_rule_successor` allocates the candidate with
`uuidv7()`. Its public
`normative.apply_validated_knowledge_layer_rule_source_reference_correction_v1`
allocates claim, Receipt, Event, Outbox, curation Audit and Application Audit
the same way. The existing Application service has no output-ID parameters;
it owns one transaction on one connection and invokes that fixed primitive.
Phase 26 tests that architecture. Phase 28.3 fixes some fixture identities but
obtains candidate and Receipt IDs from the returned persisted result. Neither
establishes that all Application output IDs are known before execution.

Phase 31.3 instead freezes a complete retained graph before execution. Bridging
that mismatch requires an explicit choice of privileged boundary, identity
allocation, equivalence obligations and lifetime. Temporary lifetime narrows
the decision's scope; it does not remove its architectural nature.

The promoted reference is migration 0021 domain semantics within the frozen
0001–0023 migration baseline. Migration 0023 already adds the closed synthetic
source-reference grammar by replacing exactly two grammar checks in the 0021
function. That existing change is not a new adapter variance. Comparing the
synthetic fixture against bare 0021 without 0023 would test a different source
contract and is not valid parity evidence. Migrations 0021, 0022 and 0023 are
not rewritten, replaced, reversed or bypassed by this decision.

## Decision: ephemeral and specification-bound

A future Phase 31.4 may install one exact-ID Application adapter **only inside
its isolated ephemeral PostgreSQL 18.6 environment**. The executable database
capability, its dedicated roles and grants must be removed with that environment
after the frozen retention/teardown gate. Retained documentation and proof of
the executed definition are evidence, not an installed or reusable capability.
This ADR creates no implementation, database object or execution authority now.

The adapter consumes the following immutable package, using repository-relative
paths. File-byte SHA-256 values are admission checks, not replaceable defaults:

| Artifact | SHA-256 |
|---|---|
| `docs/governance/COMPLETE_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_LIFECYCLE_POC_POLICY_V1.md` | `44535b47bda30a4319903d8b9f10be04890b4d9085c8955d57916f3616d9588d` |
| `docs/governance/fixtures/PHASE31_3_COMPLETE_RETAINED_SYNTHETIC_SOURCE_V1.txt` | `e458cd0bb7eb11f96ce8723b0ab4dea97e4ca60b0e47a6f7e1fb1f38cef66d6b` |
| `docs/governance/fixtures/PHASE31_3_COMPLETE_RETAINED_SYNTHETIC_LIFECYCLE_SPEC_V1.json` | `683f7c83ff3e3e16733d63288d317f8b3a14fe9e5bfaf2e86b0cf2e86b6ab6ca` |
| `docs/governance/fixtures/PHASE31_3_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V1.json` | `d5e1960801772af74d491c9c6f69a877b79f1e26b937701cf1a239114b37bf1c` |
| `docs/governance/fixtures/PHASE31_3_EXPECTED_RETENTION_CLOSURE_V1.json` | `d3455bc64957ef1aab5f618e552d9276bd6fd60e0b1ce2e7a8068e5c14c8917a` |

The lifecycle JSON remains the authoritative execution contract. This ADR
neither substitutes a second specification nor permits changing IDs, hashes,
actors, lifecycle or closure semantics to make an implementation pass.

| Exact binding | Required value or authoritative JSON location |
|---|---|
| Experiment | `a3f8fd64-af24-5b31-977a-bcaf8146c563` |
| Synthetic source | `72d038c3-4ee5-5d40-a75b-398133dbed00`; exact `source` bytes, manifest, classification and locators |
| Root and lineage | `bc5f4f17-294d-5abd-b27b-2d296921ffdf`, `s0`, published at Application, root predecessor `NULL` |
| Candidate | `a55716fa-63c7-54eb-bda2-9c9666613b1a`, `s1`, predecessor exact root; draft and unpublished on Application return |
| Proposal | `a0c36b62-ab9e-5852-9228-19891ec48217` |
| Delta | `96895eeb-41a6-546a-a270-a72147271a4c`; exact `application.canonical_delta.material` and canonical bytes/hash |
| Sole selected Review | `54aa2fd0-1449-51bc-b543-5e607c84b59a` |
| Decision | `dbbf331b-0388-51a9-bca7-e9d1bbf84dd5` |
| Authorization | `4768a437-735b-5afb-903a-b362443fb1bf` |
| Application executor actor | `0ff68e3a-a186-5cca-b450-32b88cacd47e`; all other actors and SOD exact under `actor_sod` |
| Claim | `29c6f7d5-989b-5bf0-a494-7d22d83a6a18` |
| Event | `e01768a1-8e00-5fbc-a73f-cc1cf80af542` |
| Outbox | `8827890a-0465-5906-8125-716081bfae74` |
| Application curation Audit | `ff75b1d0-a2ea-5eae-9064-b9114496047a` |
| Immutable Application Audit | `c71bd788-df60-5d1a-895e-8a8274624886` |
| Receipt | `b35d11e1-6848-50b2-b760-dd09d38f0acb` |
| Application trace | `516edff7-ce39-5e41-9888-79828c2bc1d4`; all governance traces exact under `application` |
| Target hash | `dbaa2e4eff3c980522a916d0cf2f10127e39f0af8dbfdacb469ac3015d8d87db` |
| Candidate full-material hash | `e188e1302f8bcf6c1df4c07fe06eb5dc01d4824453bc7698537b6599571c6e3a` |
| Substantive fingerprint | `23cbf18249043f5f603dd6488760e4a64e29b97cc493909b7c622e978f42e4a6` |
| Lifecycle hash | `93a4e545bca381b18219eaaf7712222d27c9ea849e24de26024f766bb15adf2b` |
| Operation | `learning.knowledge_layer_rule.source_reference.correct` / `v1` |
| Delta canonicalization/schema | `iso-smart-learning-delta-canonical-v1` / `learning-knowledge-layer-rule-source-reference-correction-delta-v1` |
| Other hashes, policies, capabilities and canonicalization | Exact `source`, `lineage`, `application`, `authority_contract`, `capability_streams`, `canonicalization` and `canonical_operation_contracts` values |

Every event, Outbox, Audit, trace, source, support, evidence, policy and actor ID
outside this summary is also bound to the frozen package; omission from this
table grants no discretion. Fresh values may fill only the already declared
authority/capability, transaction timestamp and live schema observation slots,
under their frozen validation rules. No caller may select an arbitrary target,
ID, field, value, operation, version, source or replacement payload. No
latest/current/head/max-version/newest/timestamp target selection is permitted.

## Behaviorally equivalent domain operation

The required proof is:

```text
exact-ID adapter behavior == promoted 0021 domain semantics
except for explicitly authorized deterministic/preallocated identity material
```

The adapter preserves validation; the exact source-reference correction;
lineage and predecessor; immutable revision creation; substantive fingerprint;
Event, Outbox, both Audits and Receipt; one-connection transactional atomicity;
idempotency; locking and concurrency; stale-target/TOCTOU defenses; and security.
It changes only the locator between the exact before/after references in the
same synthetic edition and source hash, creating only the fixed candidate and
its mandatory Application graph. The predecessor is not mutated or published
by Application. Compensation is not authorized for this experiment.

Existing Phase 31.3 exact admission, fresh-authority, capability, SOD,
precommit and retention checks remain mandatory around that domain operation.
They do not authorize changing 0021's inner semantics, dropping validation,
changing receipt identity rules, weakening locks, skipping evidence or
replacing its hash algorithms. The 0021 full-row target/Receipt hash, 0022
selected full-material hash, substantive fingerprint and lifecycle hash remain
distinct. Any additional behavioral divergence is a blocking P1.

## Blocking proof before Publication

Phase 31.4 must compare both paths on deterministic comparable fixtures under
the same frozen migration baseline. The reference must invoke the promoted
Application primitive; comparing two copies of the adapter is insufficient.
Use isolated reference trials and adapter trials with equivalent exact input
material and initial state, before the retained lifecycle can reach Publication.
The adapter remains bound to the Phase 31.3 IDs even in tests; reference-only
generated IDs are not substitutes for the retained candidate.

Retain raw inputs, live outputs, failures, row deltas, function definitions and
ACL observations for both paths. Define the comparison before accepting
results. A bijection may relate only 0021-generated output IDs to the seven
frozen output IDs, including every dependent FK and payload reference. Verify
each path's original canonical hashes first, then recompute any ID-dependent
comparison hash over the explicitly mapped comparison material. The mapping
must not alter persisted rows, exported evidence, source material, validation
outcomes, authority, target hashes or the Phase 31.3 contract. Independent runs'
declared fresh timestamps/authority slots must be validated for their original
freshness and binding; they must not be discarded to hide a mismatch.

| Proof category | Required comparison and blocking result |
|---|---|
| Validation outcomes | Valid exact chain succeeds; missing/wrong/stale Proposal, Delta, Review, Decision, Authorization, actor, scope, permission or hashes fail closed with the same domain outcome/error class and zero writes. Separately exercise the frozen outer admission/precommit controls. |
| Candidate material | Same copied logic, evidence expectation, classification, version, locator-only transition, draft status and null publication timestamp; only candidate identity allocation differs. |
| Hashes | Recompute both paths' full-row and full-material hashes with their actual material; compare substantive fingerprint and lifecycle hash using their separate frozen algorithms. The retained adapter candidate must match every exact Phase 31.3 hash. |
| Lineage/predecessor | Same exact root, layer, rule key and lineage; one successor, no fork/cycle/self-edge, unchanged predecessor. |
| Source transition | Exact before to exact after locator; same edition/source hash and closed synthetic grammar from 0023; no alternate or authoritative source substitution. |
| Event | Exactly one `knowledge_layer_rule.source_reference_corrected`, schema integer `1` (v1), exact aggregate/version, bounded payload/hash, trace and inert state flags. |
| Outbox | Exactly one matching event FK, `platform.knowledge-layer-rule` destination, `pending` state and valid live timestamps; no delivery/external effect. |
| Audits | Full eight-field curation Audit and distinct immutable Application Audit, exact actions, actor, target, trace, payload hash and Receipt links. |
| Receipt | Same governance set, operation/canonicalization/schema, delta, before/after, predecessor, fingerprint, flags and Event/Outbox/Audit links; exact replay returns the original Receipt. |
| Rollback | All 13 frozen Application injection points plus corresponding material boundaries in the reference; candidate/claim/Event/Outbox/curation Audit/Receipt/Application Audit all-or-zero, protected state unchanged. |
| Idempotency | Identical material yields original result/replay or waiter; conflicting material or reused artifact ID denies; timeout cannot steal a claim. No new Receipt on replay. |
| Stale target and TOCTOU | Drift, consumed predecessor, authorization revocation, capability disablement, SOD or source/hash mismatch denies before commit with all deltas zero. |
| Concurrency | Exercise frozen identical and changed-material races, stale predecessor and revocation/disablement races with real concurrent sessions; one winner plus replay/waiter or conflict, no duplicate graph. |
| Security/ACL | Catalog plus role-level execution tests prove dedicated ownership, RLS, fixed search path, PUBLIC denial, no direct DML, no role escalation/private-primitive access or release authority; hostile path and tenant/actor spoofing fail closed. |

**If parity is missing, ambiguous or fails, Phase 31.4 stops before Publication.**
Source inspection, matching IDs, existing Phase 26/28.3 results and offline
tests cannot prove this future PostgreSQL behavior. Do not change the frozen
specification or broaden the identity exception to clear a failing proof.

## Least privilege and SECURITY DEFINER boundary

Every adapter database function has a dedicated owner with `NOLOGIN`,
`NOSUPERUSER`, `NOINHERIT`, `NOBYPASSRLS`, no table or sequence ownership,
no persistent schema CREATE, no role escalation and no assumable membership
for the executor or other application principals. Functions use fixed
`search_path=pg_catalog`, fully qualified objects, no dynamic SQL and no
arbitrary selectors. PUBLIC EXECUTE is revoked. The sole callable adapter
entry is granted only to the exact ephemeral LOGIN Application executor;
private helpers are not granted to it. Ownership is not a second public API.

The executor is non-owner, `NOSUPERUSER`, `NOINHERIT`, `NOBYPASSRLS`, with no
direct table DML, schema CREATE, SET ROLE to owners, curator membership,
Publication, Activation, RuntimeAdoption, repair or capability-control power.
Bind the frozen executor actor and trusted tenant/organization context on the
same connection; an actor UUID or caller-supplied session setting alone is
not fresh authority. Require server-resolved permission, global scope, MFA,
active access, policy, SOD and enabled capability at admission and precommit.

SECURITY DEFINER permits only the minimal writes/reads/locks needed for this
exact graph. Any UPDATE privilege required by PostgreSQL row locking belongs
only to the inaccessible owner and never authorizes material mutation; frozen
immutability triggers remain effective. Tenant-scoped rows retain ENABLE/FORCE
RLS and tenant/organization constraints; global normative rows retain the
promoted global boundary. No bypass, disabled trigger, relaxed FK or grant to
PUBLIC may be used to achieve parity. The dynamic DDL in historical migrations
is not permission for dynamic SQL inside an adapter function.

## Scope, lifetime and non-generalization

This is not migration 0024, a generic application framework, production
service, API, shared runtime capability, reusable target dispatcher or
permanent SECURITY DEFINER surface. Migrations 0001–0023 remain byte-frozen
and 0024 remains absent. The adapter may create only the exact synthetic
Application candidate and mandatory Application evidence above.

It may not publish, activate, create RuntimeAdoption, mutate ModelPolicy or
AgentDefinition, change autonomy, mutate normative content, operate on another
candidate or Phase 29, compensate, invoke a runtime resolver, perform external
effects or access production/staging/shared databases. The separately governed
future Publication and Activation boundaries retain their own actors,
authorities and frozen contracts; Application never chains them automatically.

Successful Phase 31.4 use does **not** authorize productionizing the adapter,
retaining its executable capability after teardown, adding it to normal
runtime, using preallocated IDs generally, replacing migration 0021 or exposing
generic application operations. Any permanent exact-ID mechanism requires an
independent architecture gate and migration/API/security review. POC success
creates no precedent or implicit approval for that work.

## Transitive retention closure and historical separation

Deterministic identity strengthens `TRANSITIVE RETENTION CLOSURE / v1` by
allowing prior enumeration and exact cross-checking; predeclared identity is
not evidence by itself. Every generated artifact must still be re-read live,
canonicalized, hashed, included in the closure graph, exported before teardown
and checked against Phase 31.3. Live persisted material is mandatory.

Derive closure from the live schema/FK snapshot and frozen semantic registry
to a fixed point. Retain every mandatory local dependency's full canonical
typed material and each external authority's frozen provenance. This includes
every required `normative.curation_audit` row: root creation, Application and
Publication, with all eight fields, never just its UUID or a governance Audit
substitute. The frozen lower bound can only grow by mandatory discovery.
Missing/unknown/conflicting material is `RETENTION_CLOSURE_BREACH`.

Publication closure must be complete before Activation. Before teardown,
export, independently re-read via a new read-only transaction, compare all
material/hashes/cross-links and require `closure_complete=true`,
`export_matches_live_graph=true`, `reconstruction_required=false`. Then record
the frozen pre-teardown disposition, authorize teardown, remove the environment
and adapter, and verify offline without reconstruction. On failure preserve
the live isolated environment by default. Only the already governed dual-control
override may tear down incomplete evidence, permanently non-rematerializable
and operationally ineligible, never PASS. This bounded inspection retention
does not authorize reuse, continued execution or retention after teardown.

The adapter must never rematerialize or repair Phase 29 Publication
`e97576de-d4ef-520d-8592-d376ed401221` or fabricate the missing
`normative.curation_audit.id = 12d811ab-c3b4-4615-8972-75008a36e327`.
Phase 29 remains `HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE` with
`RETENTION_CLOSURE_BREACH`; its historical fact remains true and its operational
use remains denied. No import, reconstruction, replacement, ID reuse, recovery
or continuity claim is permitted. Phase 32/RuntimeAdoption remains blocked.

## Alternatives and consequences

Keeping dynamically allocated identities cannot meet the predeclared retained
graph. Editing 0021 or creating 0024 violates the frozen scope. Rewriting the
Phase 31.3 JSON, copying rows after execution, spoofing `uuidv7()` through a
search path, bypassing guards or using a generic privileged dispatcher either
changes the contract or weakens security. Treating the choice as policy-only
leaves the architectural decision unrecorded. These alternatives are rejected.

The selected solution preserves the promoted domain boundary and frozen
history while making identity allocation explicit for one experiment. Its
cost is a mandatory differential proof and careful removal of the privileged
surface. Its remaining implementation risk is behavioral drift: that is a
future blocking test, never a claim of equivalence established by this ADR.
Phase 31.3.1 performs documentation/offline validation only and has zero
database, lifecycle, runtime, normative, learning or external business effects.
