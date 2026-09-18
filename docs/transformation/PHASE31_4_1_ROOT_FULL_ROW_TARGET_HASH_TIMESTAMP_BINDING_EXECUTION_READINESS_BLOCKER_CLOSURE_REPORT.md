# ISO SMART AI — Phase 31.4.1 root full-row target hash / timestamp binding

Date: 2026-09-08. Exclusive workspace: `/home/felipe/proyectos/isosmart`.
Design / diagnostic only. No PostgreSQL or lifecycle execution.

## 1. Verdict

**PHASE 31.4.1 — NOT PROMOTED**

B1 is not closed. The full schema and hash dependencies are now derived, but
the frozen package does not contain authentic root timestamps. Its declared
fresh-time execution model cannot reproduce a predetermined full-row target
hash before persistence. Two other fixed evidence hashes have no supplied
preimages. Reviewing the directly dependent Proposal path also exposes an
unbound mandatory supporting-signal graph. P0=0; P1=4 (B1–B4 below).

This is a completed diagnostic with a negative gate outcome, not an approved
successor execution package. No corrected target hash or Authorization was
issued. PostgreSQL creation and a Phase 31.4 retry remain unauthorized.

## 2. Entry blocker

Root and lineage: `bc5f4f17-294d-5abd-b27b-2d296921ffdf`, version `s0`.
Frozen full-row target hash:
`dbaa2e4eff3c980522a916d0cf2f10127e39f0af8dbfdacb469ac3015d8d87db`.
Frozen Delta hash:
`06f75de72e2a2ded515c223a1c62df6ab3780ebfe1ed0ccca71a22a222071c9e`.
Distinct selected-material root hash:
`3421457f44586a28cf4b6a242cb2f25929e3eae8689de214292639fcb89be3af`.

Phase 31.4 stopped before PostgreSQL creation. This task verifies that report's
integrity; it does not represent its statements as new live observations.
No timestamp preimage was searched, guessed or recovered from a hash.

## 3. Initial git status

The first repository command was `cd /home/felipe/proyectos/isosmart && git status --short`.
Exact output:

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

Before discovery/reading, targeted `git diff --check -- frontend/src/components/Layout/Sidebar.jsx`
returned exit 2 as shown below (the final space is displayed as `<SPACE>`):

```text
frontend/src/components/Layout/Sidebar.jsx:28: trailing whitespace.
+    { name: t('navigation.risks'), path: '/risks', icon: AlertTriangle, group: 'control' },<SPACE>
```

The trailing space in that existing file remains untouched. The diagnostic
line above describes it; this report does not deliberately contain whitespace
errors. All repository discovery used the exclusive working directory. No
sibling repository was enumerated, opened or executed against.

## 4. Frozen input verification

All required admission hashes were verified before design corrections; none
mismatched. Migration inventory serialization is sorted repository-relative
`path + NUL + lowercase file-byte SHA-256 + LF`, then SHA-256 of that stream.
It is **not** the SHA-256 of a JSON dictionary of file hashes.

| Input | Verified SHA-256 |
|---|---|
| Phase 31.3 report | `fc5f16abab801570aefd313b87cae1805f3e5067e73d01acebebce9519724a8f` |
| Phase 31.3.1 report | `5df6ba154a49d3aede4938bdcf17ff11d524e4d75526ba96b969df9ac6a3b6da` |
| Product Policy | `44535b47bda30a4319903d8b9f10be04890b4d9085c8955d57916f3616d9588d` |
| Source fixture | `e458cd0bb7eb11f96ce8723b0ab4dea97e4ca60b0e47a6f7e1fb1f38cef66d6b` |
| Lifecycle specification | `683f7c83ff3e3e16733d63288d317f8b3a14fe9e5bfaf2e86b0cf2e86b6ab6ca` |
| Semantic registry | `d5e1960801772af74d491c9c6f69a877b79f1e26b937701cf1a239114b37bf1c` |
| Expected closure | `d3455bc64957ef1aab5f618e552d9276bd6fd60e0b1ce2e7a8068e5c14c8917a` |
| ADR-0017 | `82501ef34edc6d7e76e0971d3d2607c58f229a1dd4dd26696dd227fb7e994edb` |
| Migrations 0001–0023 (23/23) | `cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc` |
| Phase 31.4 report | `2bd96b31bf55dd36b7a459b1ff511bea8cbe4de43562be9e97162ab2489aeb8d` |
| Phase 31.4 evidence file bytes | `b8490b2bb2cd059b015be7a97731dad009b45018fa822278b61daabb886fbf70` |
| Phase 31.4 detached ledger | `62e8de3eb43ea726ef3f48f2e2bef382342d941e6f3f403bcf7f4c31908eec70` |
| Phase 31.4 evidence canonical material | `aef497dcbe8bcb84efe4bcbb9cdcff74566b2fe4b8f05eeb80ba03aa1af3197f` |

The detached ledger's two entries match the finalized files. Its own hash is
a fresh observation, not a claimed signature or independent approval.
Evidence canonical hashing removes only `canonical_material_sha256`, then
uses sorted compact UTF-8 JSON. Migration 0024 is absent.

## 5. Mandatory reading completion

Completed semantic reading of the requested B1 input set:

- Complete Phase 31.3, Phase 31.3.1 and Phase 31.4 reports, including their
  continuations and limitations; complete ADR-0017 and Product Policy.
- Complete source fixture, lifecycle specification, semantic registry and
  expected closure. Phase 31.4 evidence was parsed in full; semantic fields
  were inspected and its hash inventories mechanically checked. Inventory
  parsing and file hashing are not represented as prose/code semantic reading.
- Complete migrations 0009, 0020, 0021, 0022 and 0023, including reverse paths.
  Long outputs were split; truncated source portions were retrieved separately.
- Complete `governed_learning_application.py`, `governed_learning.py`,
  `learning_proposal_governance.py`, `learning_delta.py`, `knowledge_layer.py`,
  `knowledge_rule_release.py`, `canonical.py`, `eventing.py`, `audit.py`,
  `tenant_context.py`, `retained_publication_evidence.py` and
  `phase283_retained_candidate.py`.
- Complete Phase 26 and Phase 28.3 harness source, read only. Their imports,
  migration/creation/application paths and export logic were not executed.
- Complete KnowledgeLayer/KnowledgeLayerRule/Binding/NormativeCurationAudit
  model definitions (`models.py:444–564`), corresponding 0009 state/schema,
  0018 supporting-signal guards and 0019 Review/Decision/Authorization guards.
  Unrelated model classes and unrelated migration sections are not claimed as
  a complete full-file reading.
- ADR-0003, ADR-0009 and ADR-0013–0016; 0020/0021 tenant RLS/grants and 0022
  global normative least-privilege boundaries. Resolver implementation was
  read but never invoked.

This finishes the B1-relevant semantic material explicitly left unread by
Phase 31.4. It is not a new review of every earlier phase or a full product
security audit. No historical Phase 29 lifecycle material was used to fill
this experiment's gaps.

## 6. Migration 0009 root schema

`normative.knowledge_layer_rule` has 13 persisted columns. No migration through
0023 adds/removes a root-row column. No generated identity/default UUID exists
in this SQL table: the caller supplies `id`; the Django unmanaged model's
UUID default is a separate application behavior. There is no `updated_at`,
tenant column, publication ID, authority field or joined Layer field in this
row. FK targets are retained separately and are not expanded by `to_jsonb(r)`.

The root must first be inserted as draft with `published_at=NULL`. Publication
is a subsequent valid transition against a published source edition.
Inserting a published root directly fails the guard, even with valid dates.

## 7. Migration 0021 full-row hash semantics

The complete source expression at 0021:293–299 is:

```sql
SELECT encode(sha256(convert_to('{"canonicalization":"iso-smart-canonical-json-v1","value":'||
  qms.foundation_0020_canonical_json_value(to_jsonb(r))||'}','UTF8')),'hex')
  FROM normative.knowledge_layer_rule r WHERE r.id=p_rule_id
```

At 0021:447–453 the exact root is locked; `before_hash` is recomputed and must
equal Authorization `target_hash`; `to_jsonb(target)` must equal Proposal
`target_snapshot`. The forward root must be published and have no successor.
The Delta target, canonical bytes and hash are revalidated as well.

Neither selected-material hashing nor a partial target snapshot can satisfy
these comparisons. Full-row candidate hashes are also used for Receipt
`after_hash` and Application curation `payload_hash` at Application time.

## 8. Migration 0023 effect / non-effect

0023 replaces exactly two closed source-reference grammar checks in the
promoted Application definition. It changes no row schema, timestamps,
canonicalization, target comparison, grants or ID allocation. Both future
reference and adapter paths must use the complete 0001–0023 baseline.
0022's selected material hash is separate and does not redefine 0021.

## 9. Complete root-row preimage

The following is declaration order, not hash key order. F=frozen constant;
D=deterministically derived from the candidate/Delta and locator-only copying;
S=state-dependent. Every field is included in 0021; **none is excluded**.
No root value is an authorized newly generated UUID. SQL nullability is shown
separately from the required value at Application admission.

| Field | SQL type / nullable | Classification and exact value / rule | SQL default |
|---|---|---|---|
| id | uuid / no | F: `bc5f4f17-294d-5abd-b27b-2d296921ffdf` | none |
| knowledge_layer_id | uuid / no | D/F: `ca734de0-7bfe-51e4-acce-639cc5f26f1d` | none |
| lineage_id | uuid / no | D/F: root ID, required by root identity constraint | none |
| rule_key | varchar(160) / no | D: `phase31.3.complete-retained-synthetic-lifecycle` | none |
| version | varchar(80) / no | F: `s0` | none |
| previous_revision_id | uuid / yes | F: JSON null | implicit SQL NULL |
| status | varchar(24) / no | F/S: `published` at admission; initially `draft` | `draft` |
| logic_json | jsonb / no | D: `{"fixture_only":true,"operator":"source_locator_is_retained","runtime_effect":false}` | `{}` |
| evidence_expectation | jsonb / no | D: `{"normative":false,"required":["synthetic_fixture_reference","transitive_retention_closure_v1"]}` | `{}` |
| source_reference | text / yes | F: exact Delta `payload.current_source_reference`, nonnull for this operation | implicit SQL NULL |
| certifiability_classification | varchar(40) / no | D/F: `non_certifiable_guidance` | same constant |
| published_at | timestamptz / yes | timestamp, S, nonnull at admission; exact value **UNBOUND** | implicit SQL NULL |
| created_at | timestamptz / no | timestamp, fresh/default unless explicitly assigned; exact value **UNBOUND** | `statement_timestamp()` |

Exact source reference:

```text
iso-smart-synthetic-poc-source-ref-v1:98939c5e-1a06-53c9-bbf9-07b21d81feb1:e458cd0bb7eb11f96ce8723b0ab4dea97e4ca60b0e47a6f7e1fb1f38cef66d6b:fixture/element/source-reference-before
```

The diagnostic JSON's `known_root_material` carries all 11 known values.
The two unknown fields are deliberately absent, not replaced by null or
string slot markers in a purported valid row. The seven shared/copied values
follow from 0021 copying prior material plus Phase 31.3's exact candidate.
Recomputing the ten-field 0022 root hash confirms that derivation, but cannot
prove a complete 0021 preimage. Logical preimage is precisely these 13 keys,
with genuine values for both missing timestamps and the agreed JSON context.

## 10. Missing binding inventory

| Finding | Severity | Missing contract |
|---|---|---|
| B1 | P1 | Exact created/published root values, their source semantics, and stable rendering context; fixed target/Delta conflicts with fresh execution timestamps |
| B2 | P1 | Complete material/schema and generation rule for compatibility evidence `37d3d0bc-4387-581a-a627-f02a011250d1`, fixed hash `43c72090f30e90a4f3896b3d194aa264f421189f0589978453136464e270dbc9` |
| B3 | P1 | Complete material/schema and generation rule for release evidence `981e1753-dcd1-5f8d-8b10-49bfaed5eafb`, fixed hash `5583dd2939abe5e1e2d602cef33077685df8efb48f0c664812eaee138723d15a` |
| B4 | P1 | Exact nonfresh governance creation material and mandatory supporting LearningSignal/Effectiveness graph, including identity/provenance bindings |

B2/B3 each have only `{id,hash}` in the approved lifecycle JSON. The registry
requires complete canonical typed evidence with candidate/Publication/zero
runtime cross-links; neither the registry nor reports supply the missing
preimage. There is no evidence that those hashes are authentic hashes of
persisted rows with fresh fields; their preimage type is itself unspecified.
They cannot be declared intentionally live-derived merely because their values
are unavailable. They are independently unresolved prebound hashes.

B4 is directly relevant to rebuilding the governance chain after B1. The
0018 deferred `qms_learning_proposal_signal_required` trigger requires an
exact supporting signal. `create_proposal` also requires nonempty signal IDs;
`create_signal` requires an Effectiveness leaf and history. The Phase 31.3
inventory supplies neither graph. Its invariance contract prohibits creating
LearningSignal as unauthorized automatic learning. A future contract must
resolve this explicitly, not bypass the constraint, borrow Phase 29, or
silently create an extra experiment. Exact rationale/findings/domains,
projection IDs and governance child identities are also not fully specified;
fresh authority slots do not authorize inventing these nonfresh values.

## 11. Canonicalization

1. Source is the one persisted composite row selected by exact UUID.
2. PostgreSQL `to_jsonb(r)` converts its 13 columns into JSONB. UUIDs become
   lowercase hyphenated strings; SQL nullable values become JSON null.
   `logic_json`/`evidence_expectation` remain nested objects and arrays.
3. `foundation_0020_canonical_json_value` recursively orders object entries by
   SQL `ORDER BY key`, encodes keys with `to_jsonb(key)::text`, preserves array
   ordinality, inserts only `:` and `,`, and returns scalar `jsonb::text`.
   SQL ordering follows the database collation; the function does not specify
   `COLLATE "C"`. No universal RFC8785 equivalence is established by its name.
4. The literal envelope is `{"canonicalization":"iso-smart-canonical-json-v1","value":<value>}`.
   There is no row schema/version marker beyond this canonicalization marker;
   the row schema is the frozen migration baseline.
5. Hash UTF-8 bytes without BOM or appended LF using SHA-256; lowercase hex.

Booleans are `true`/`false`; null is unquoted `null`; strings keep their exact
JSON content/escapes. No decimal column exists in this root and its nested
fixture contains no numbers. For other JSONB numbers the scalar SQL renderer
is authoritative, not Python float formatting or RFC8785 number rewriting.
Python `Decimal` normalization in `canonical.py` produces a string, which is
not a general substitute for a PostgreSQL JSONB numeric scalar.

Timestamps are already strings after `to_jsonb`. SQL does not apply UTC
conversion, fixed fractional padding, `Z` substitution, or Python datetime
normalization. For ordinary finite timestamps the PostgreSQL JSON timestamp
representation uses ISO date/time with `T`, offset, and available fractional
precision; fractional zero padding must not be assumed. Session TimeZone
affects the rendered value. A future UTC profile must preserve the actual
PostgreSQL output (e.g. `+00:00`), and pin/verify the same rendering and ordering
context in every root read, Proposal/Review/Decision/Authorization and
Application connection. SQL `search_path=pg_catalog` does not pin TimeZone.

`canonical_hash(raw_to_jsonb_dictionary)` preserves timestamp strings and is
the Phase 26/28.3 path. Passing Python datetime objects instead normalizes them
to UTC with six digits and `Z` in `canonical.py`; those are different bytes.
Equal instants expressed as different JSON strings need not hash equally.
No PostgreSQL renderer or cross-collation equivalence was executed here.

## 12. Timestamp semantics

`created_at` is a `timestamptz` with no narrower precision modifier; SQL's
default is statement time, not transaction time. Explicit insert values are
schema-compatible. The Django model uses `auto_now_add`, assigning application
time on ORM creation instead of relying on that SQL default. The service has
no timestamp argument. `created_at` cannot change during publication: both
0009 and 0021 guards compare OLD/NEW. Once published, the whole row is immutable.

`published_at` starts NULL, has no fresh SQL default and is assigned during
publication. The curator ORM method uses `timezone.now()`. Phase 28.3's SQL
bootstrap uses `statement_timestamp()` on its separate UPDATE; native 0022
Publication also uses statement time. None guarantees equality with creation
time. Several statements in one transaction may have different statement
times. Microsecond-compatible precision and timezone-aware values are required;
neither the schema nor the fixture establishes particular fractional digits
or an authentic time pair. The schema does not enforce `published_at >= created_at`;
a successor's causality rule must explicitly do so if adopted.

## 13. Freshness / determinism analysis

The policy allows only declared fresh authority/capability, transaction-time
and live catalog slots at execution. The machine specification nevertheless
freezes the full-row hash inside its Delta. The hash binds timestamp **values**,
not expressions such as `statement_timestamp()` or slot names. Supplying a
fresh value changes the byte input. A valid preimage cannot be inferred from
the hash, and choosing dates to make it pass is forbidden.

Authority freshness remains independent of root fixture time. A synthetic
root date, if explicitly approved later, cannot be an authority evaluation
time or imply a fresh approval. A fixed authority-shaped test object is also
not a fresh server-resolved decision.

## 14. Model A / B / C comparison

| Model | Promoted semantics | Readiness consequence |
|---|---|---|
| A: prebound synthetic root timestamps | SQL allows explicit creation and draft→published values; no approved Phase 31.3 values or synthetic-time exception were found. Ordinary curator ORM API does not accept these values. | Requires explicit new synthetic-time semantics, insertion/publication route, policy/ADR and every changed dependent hash. It cannot authenticate the old hash. No dates selected here. |
| B: live timestamps then target hash | Matches Phase 26/28.3 read-persisted-root → `canonical_hash(snapshot)` → governance flow. | Preserves fresh times but abandons precreation freezing of exact target/Delta values. Requires an architectural and governance successor; values remain unknowable offline before the future root exists. |
| C: exclude fresh fields | Not supported by 0021 `to_jsonb(r)` contract. | Rejected. 0022's selected material function is not an alternative 0021 target validator. |

## 15. Selected model

**Model B is the evidence-supported recommendation for preserving the existing
fresh-time semantics. No operational model is newly adopted by this diagnostic.**
Selecting an executable A contract would require new synthetic dates, a
different fixture-time classification and complete approval material; it is
not discovery of omitted approved values. Selecting B cannot produce an exact
precreation hash offline and therefore does not satisfy this gate's promotion
predicates. The architecture and dependent B2–B4 contracts remain unresolved.
There is no implicit fourth model or timestamp-hash adapter exception.

## 16. Governance sequencing

The valid B sequence is:

```text
freeze source, root non-time fields, identities and derivation/authority rules
→ future isolated support and exact root creation as draft
→ root publication under the approved bootstrap/curation boundary
→ read complete persisted root in pinned JSON context
→ compute full-row target hash and retain exact snapshot
→ create/freeze Proposal and its owned canonical Delta atomically
→ Review exact Proposal/Delta/target
→ Decision over exact selected Review set
→ fresh Application Authorization over corrected material
→ governed Application with unchanged 0021 validation
```

The Proposal/Delta circular FKs are deferred under 0020; the promoted command
creates both in one transaction. A root hash must be known before that
transaction's exact bindings are built. A precreation rule contract could
authorize this future derivation; it is not a precreation authorization of an
unknown exact Delta. Phase 31.3's “execution-ready before DB creation” premise
must be explicitly superseded in that respect. No step in this sequence ran.

## 17. Corrected target hash

**UNAVAILABLE / NOT AUTHORIZED.** No authentic approved input supplies the two
values needed to reproduce the old target. No successor operational hash was
chosen. Machine `corrected_target_hash` is JSON null as diagnostic metadata,
not a permissible target value. The old value remains immutable history.

## 18. Delta impact

Changing the target hash necessarily changes `canonical_delta.material.target_hash`,
its exact canonical bytes and SHA-256. The remaining nine top-level fields and
locator-only payload may stay unchanged if their identities/semantics remain
authorized. The old Delta's bytes reproduce its frozen digest, but that proves
internal byte integrity only. It does not establish an admissible target.
No old Delta may be attached to a newly computed root hash.

## 19. Proposal impact

The full raw target snapshot and `target_hash` change; `proposed_change_hash`
and `delta_hash` must both become the new Delta digest. Proposal material hash
uses `_proposal_material` in `learning_proposal_governance.py:128–161`, not
the whole persisted Proposal row. It includes the target/Delta, tenant/org,
identity/revision/predecessor, scope/status and policy. It excludes Proposal
creation time but includes the timestamp-dependent target hash transitively.
Proposal provenance additionally binds supporting signal IDs. B4 prevents
claiming a complete executable Proposal from the current package.

## 20. Review impact

Rebuild target tuple, exact Delta binding and Proposal material hash. Retain
the complete new findings, actor/projection, policy, authority and timestamp.
`review_outcome` is the promoted `review_recorded`; the subsequent Decision
provides approval. A matching Review ID alone cannot carry approval forward.

## 21. Decision impact

Decision copies target/Delta/Proposal hash and exact Review ID set. Its identity
hash is `canonical_hash({proposal_id,proposal_material_hash,review_set_hash,
outcome,rationale,approver,policy_id})`. Sorted selected Review IDs may yield
the same review-set hash if IDs are retained; the Decision identity hash still
changes when Proposal material changes. A complete new Decision requires the
actual approved rationale and authority, not a diagnostic placeholder.

## 22. Authorization impact

Authorization must bind the new Proposal material hash, Decision, target tuple,
canonical Delta tuple and capability. The promoted Authorization idempotency
hash also includes exact authorizer, authority context and decision reference.
Fresh authority remains execution-derived; a historical Authorization or a
test object's matching ID cannot authorize new material. This phase creates
neither an approval record nor an authorized successor package.

## 23. Idempotency impact and before/after dependency graph

The three literal Phase 31.3 key strings and their raw SHA-256 hashes do not
contain the target/Delta. Those hashes can remain unchanged if IDs and key
semantics are explicitly retained and no earlier execution exists. They are
**not** Authorization `idempotency_hash` or 0021 claim `material_hash`.

```text
BEFORE (historical, non-executable target binding)
unknown root timestamps/context → fixed H0=dbaa2e4e…7db
H0 → Delta0=06f75de7…19e → Proposal material P0
P0 + selected Review set + outcome/rationale/approver → Decision identity
P0 + H0 + Delta0 + Decision + capability + authorizer + fresh authority + key
  → Authorization idempotency hash A0
Proposal ID | Decision ID | Authorization ID | operation | version | Delta0 |
  root ID | root version | H0 | empty forward-Receipt slot
  → SHA-256 application_identity I0
I0 | PostgreSQL review_ids_snapshot::text | A0 | executor UUID
  → SHA-256 claim material M0

AFTER (conditional Model B, no instantiated operational values)
actual persisted timestamps/pinned context → H1
H1 → new Delta1 → new Proposal material P1
P1 + exact Review set + approved decision material → new Decision identity
P1 + H1 + Delta1 + Decision + fresh authorizer authority + key → A1
same identity formula with Delta1,H1 → I1
same claim formula with I1,A1 → M1
new Delta1/H1/candidate live full-row hash → Receipt/Event/Audit payloads
complete new typed rows → retained member hashes → closure digests/manifests
```

For forward Application the final empty slot in `concat_ws('|',...)` is an
empty string, not SQL null; the input ends with `|`. Review array SQL text is
not canonical compact array serialization for multi-item arrays. The single
frozen Review avoids separator ambiguity, but future vectors must preserve
the exact SQL renderer. Neither formula hashes the literal application key
hash directly. Full row hashes for claim/Receipt/Audits additionally contain
fresh persisted timestamps and must be calculated after creation.

Native 0022 Publication `operation_material_hash` is SHA-256 of
`candidate_uuid:expected_selected_hash:reason`; root timestamp correction
alone does not change it. Native Activation operation hash is SHA-256 of
`publication_uuid:expected_selected_hash:ROOT:compatibility_hash:reason`
for a null predecessor. B2's correction can change that hash. The stronger
outer lifecycle-operation envelopes also bind closure/authority/policy/
capability material and must be rebuilt. Neither inner native hash is a
substitute for the required outer envelope.

## 24. Retention-closure impact

A timestamp-only B1 correction changes no table, FK, row-column schema or
semantic edge. Source bytes, candidate selected material, substantive
fingerprint and lifecycle hash remain unchanged. Existing closure member IDs
may remain stable under §25. However root full-row hash, affected governance
rows, Receipt/Event/Audit material and recursive closure/member/manifest
digests change. No fixed future manifest digest was supplied; the closure
specification already derives those from live full canonical material.

Application curation payload uses candidate **0021 full-row** after-hash;
Publication curation payload uses candidate **0022 selected-material** hash.
Their full eight-field row hashes include their own times and remain live
derived. Both must be retained without aliasing.

B4 is separate: restoring the missing supporting-signal graph adds mandatory
members and may require explicit additional semantic edges. The current lower
bound permits discovery growth, but does not authorize inventing inputs.
Only once those edges are designed should a successor registry/closure spec
be issued. No unaffected artifact was version-bumped for symmetry here.
Runtime-zero assertions do not change under any valid B1 resolution.

## 25. ID stability

All existing IDs are preserved. They derive from namespace UUID + fixed label,
not target hash; 0022 release children derive from base UUID + suffix. A future
successor can retain these only if identity semantics remain unchanged, it
explicitly supersedes the defective precreation material, and no history
exists under the old execution contract. The verified Phase 31.4 report states
none exists. New content hashes alone do not require new UUIDs under these
derivations. Missing supporting graph IDs are not supplied or approved here.
Reference-generated candidate IDs remain confined to ADR-0017 comparison.

## 26. ADR-0017 compatibility

ADR-0017 remains unchanged and in force. Its sole adapter exception is the
seven preallocated Application output IDs. No second exception for target
hashing, timestamp omission, default suppression or validation bypass is
permitted. An accepted successor must explicitly supersede its obsolete
package/hash references without claiming the original ADR already authorized
new values. Its behavioral equivalence obligations remain intact.

## 27. Reference-path compatibility

Model B's read-root-then-govern ordering is compatible in source with both
paths: both compare their actual complete root hash to their exact governed
material. A future A fixture might also be compatible via a properly approved
root bootstrap, but changing candidate timestamps or the reference primitive
to imitate an adapter would add an unauthorized difference. Neither path has
been proved against PostgreSQL in this phase. Original hashes and fresh
authority/time bindings must be verified before output-ID comparison; fresh
slots may not simply be dropped from parity evidence.

## 28. Complete execution-readiness scan

All 20 literal 64-hex leaf occurrences in the lifecycle JSON were enumerated
with JSON paths in `frozen_hash_scan`; duplicated source and target values
remain separate occurrences. Embedded locator source hashes were additionally
verified through exact source/locator recomputations. The scan covers all
prebound hash leaves, not just those with a field named `hash`.

| Material family | Classification / result |
|---|---|
| Source bytes, manifest, source hashes and both locators | reproducibly prebound; exact recomputations pass |
| Root selected material | reproducibly prebound, ten fields; does not solve B1 |
| Root complete row / two target-hash occurrences | unresolved B1 |
| Frozen Delta canonical digest | reproducible bytes, unresolved target admission dependency B1 |
| Candidate selected material / substantive / lifecycle | reproducibly prebound, separate algorithms; candidate identity uses ADR-0017 |
| Three literal idempotency key hashes | reproducibly prebound; not inner governance material hashes |
| Publication curation payload | reproducibly prebound candidate selected hash; full audit row is live derived |
| Compatibility and release evidence fixed hashes | unresolved B2/B3 |
| Candidate 0021 after-hash, Receipt and full audit/claim/outbox rows | intentionally live-derived from actual persisted times under promoted rules; never equated with selected hashes |
| Seven Application UUIDv7 outputs | output identity mapped by ADR-0017; all dependent hashes recomputed |
| Native 0022 release child IDs | reproducibly prebound by frozen base/suffix algorithm |
| Authority/capability decisions and their complete row/provenance hashes | intentionally live-derived under declared fresh slots; original material retained, no fresh values manufactured here |
| Proposal supporting graph and nonfresh governance material | unresolved B4; cannot be reclassified as a fresh-time slot |
| Remaining generated governance/event/audit identities | require explicit binding under B4; ADR-0017 does not authorize arbitrary governance identity replacement |
| Live schema observations, full typed retention members, manifests/dispositions | intentionally live-derived under closure rules; no fixed digest has been proved before execution |

There are two additional unresolved fixed evidence hashes besides B1, plus
the directly dependent B4 input contract. No broad operational parity,
concurrency or security gate was reopened or replaced by this scan.

## 29. Machine-readable successor artifact

No authorized successor correction artifact was created because B1 is not
closed. Instead the diagnostic-only artifact is:

`docs/governance/evidence/PHASE31_4_1_ROOT_BINDING_DIAGNOSTIC_VECTORS_V1.json`.

It records predecessor hash, all 11 known root values, the unknown fields,
13-column order, 20-path hash inventory, B1–B4, explicit no-authorization flags,
test-only vectors, frozen file hashes, regression results and preservation
evidence. It is canonicalizable and independently file-byte hashable, but
must never be consumed as an execution fixture or proof that B1 is corrected.

## 30. Product Policy / addendum

None issued. The current work cannot truthfully approve an exact successor
package with unknown target and missing evidence/governance material. A future
accepted successor must preserve Phase 31.3 as historical, record the first
Phase 31.4 precreation failure/no lifecycle state, explicitly supersede only
affected bindings, prohibit Phase 29 reuse, preserve ADR-0017 semantics and
keep RuntimeAdoption prohibited. Diagnostics do not supply that approval.

## 31. ADR decision

No successor ADR was issued as accepted architecture. Adopting Model B requires
one because it moves the exact target/Delta freeze after live root persistence.
Adopting Model A would also require one to separate synthetic root timestamps
from fresh execution/authority time. This is not a mere transcription fix:
no authentic omitted values were found. The unresolved choice and dependent
contract defects are reported explicitly rather than hidden in a new ADR's
“accepted” status. No new canonical target abstraction is proposed.

## 32. Offline vectors

The JSON retains exact row, envelope, hash, target snapshot, Delta, canonical
Delta bytes/hash, Proposal hash input, Review binding, Decision identity input,
Authorization hash-link/idempotency input and 0021 identity/claim strings.
These are **counterfactual diagnostic probes**, not corrected operational
material, real decisions or persisted evidence.

Probe creation time uses the predecessor report's offline observation string
`2026-09-04T23:18:38.591092+00:00` only as an explicit test input. Probe publication
is +2 microseconds; tamper is +1 microsecond. This does not assert those times
belong to the frozen root or are fresh. Equality is not inferred. No search
for a matching preimage is performed. The probe's strict six-digit UTC profile
validates already-rendered test strings; it is not a general PostgreSQL
timestamp serializer or a proposed override of SQL behavior.

| Diagnostic value | Exact digest |
|---|---|
| Probe full row | `0b776692c06f19897381b615abfdacf0ef256dfa8bfd1cf243160a571ea6707d` |
| Probe Delta | `d0cdaa86e9c86fb4f978c3cb2adc52641ab1e0188dd80d4137f2996fc8998233` |
| Probe Proposal material | `3435a44cbf829d530d1c39cf2e206a522d37a23dcbdf208cb8beccc436c3eb7d` |

Downstream numerical vectors are in the JSON. Deliberately synthetic Decision
rationale and authority strings are labeled `DIAGNOSTIC_ONLY_NOT_AUTHORITY`;
they demonstrate dependency propagation only. None is a valid fresh authority
or complete persisted governance row. Exact accepted successor vectors 1–8
remain unavailable, and this prevents promotion.

## 33. Negative tests

The new test module proves diagnostic-profile failure for missing created_at,
missing published_at, changed created_at, changed published_at, an equivalent
instant rendered with `-06:00`, old target hash against the probe row, old
Delta against the probe target, old Delta binding in a probe Authorization,
and selected-material hash substituted for full-row hash. Additional tests
reject null timestamps/extra columns and demonstrate that datetime-object
normalization differs from raw JSON-string hashing. Valid probe byte and
dependent-hash recomputations pass.

These tests validate the documented offline hash links and failure conditions,
not execution of SQL guards or the Application service. They cannot prove
rejection against an authorized corrected row because none exists. No
PostgreSQL parity result is implied by the negative tests.

## 34. Validation counts

- Relevant Foundation tests: **36 PASS**; new B1 diagnostic tests: **19 PASS**.
  Combined selected suite: **55 executed, 0 failures, 0 errors, 0 skips**.
- Django **4.2.22**, `backend/.venv`, in-memory settings with only auth,
  contenttypes and Foundation, dummy database, normal settings/logging disabled.
  System check: zero issues. `makemigrations --check --dry-run`: no changes.
- Python in-memory compile: **351 backend source files PASS**, excluding
  hidden/vendor/cache paths; no `.venv312` use.
- Original canonical recomputations: **12/12 MATCH**. These include source,
  manifest, Delta, both selected materials, substantive/lifecycle hashes,
  both locators and three key hashes; explicitly exclude B1/B2/B3 preimages.
- JSON/schema validation: full parse, diagnostic contract tests, exact schema
  field set, canonical byte recomputation and registry structural checks.
  No general PostgreSQL renderer or live schema validation is claimed.
- Network/database attempts and resolver invocations during guarded validation:
  **0**. RuntimeAdoption resolver test excluded before execution; its signature
  may be inspected without calling it. Publication revocation test also excluded
  to avoid invoking lifecycle services. Phase 29/31 historical evidence tests
  and all PostgreSQL harnesses excluded. The entire Foundation suite was not run.

Raw successful output and exact selected test labels are retained in the JSON.
All PostgreSQL acceptance/equivalence/rollback/concurrency/ACL/RLS tests remain
**NOT EXECUTED**. No fixture reconstruction or post-teardown lifecycle verifier
was run. Routine read-only inspection errors (an oversized inventory output,
a nonexistent evidence-key lookup, and no-match searches) did not mutate
inputs or produce acceptance claims; bounded reads/file inventories corrected
those inspection steps.

## 35. Migration / source / governance / runtime hashes

The diagnostic JSON retains full repository-relative file/hash mappings for
required inputs and all 23 migrations, plus all 210 predecessor-protected
files, each freshly matching. This includes protected runtime, release/resolver,
settings, Application, models, governance and source artifacts. This is byte
preservation, not inspection or reuse of historical lifecycle data as input.
All 14,349 pre-existing inventoried tracked/nonignored regular files were
captured after read-only inspection and before deliverable edits; final
comparison and exact new-file inventory are recorded below. Python caches
and symlinks are not part of this regular-file inventory.

Final comparison: **14,349/14,349 pre-existing regular files unchanged**;
**210/210 protected files unchanged**, **34/34 frozen input files MATCH**,
**23/23 migrations MATCH**, aggregate unchanged and **0024 absent**.
Registry structural validation: **56/56 edges PASS** (required fields,
unique source/edge pairs and permitted dispositions); no live closure claimed.
Exactly three durable new files were added, listed in the diagnostic JSON's
`final_integrity.new_durable_files`; both task-owned temporary inventories
were removed. Final git status equals the recorded initial output byte-for-byte.

Independent final file-byte SHA-256:

- Diagnostic JSON: `f68ef16adebb569239c284fcc8cc93dc5942f86bcfc49c2e09a4cbdc1e2f1108`.
- Offline test module: `a21472ec51bf2950c2b90ab854b1a2a3691e07eea2f799cb9348363f6f9f04dc`.

The report does not embed its own hash. These hashes identify diagnostic
artifacts only and do not authorize successor execution material.

## 36. Git hygiene

Only this report, the diagnostic JSON and the new offline test module are
durable additions. No runtime code, migration, source, policy, ADR or original
fixture was edited. No reset, stash, clean, stage, commit or normalization.
Temporary validation inventories were task-owned and removed after recording
their results. Final porcelain remains the initial output because all three
new files lie inside already-untracked directory entries; per-file comparison
is therefore the preservation evidence, not porcelain alone.

Full `git diff --check` retains only the known Sidebar line 28 error; scoped
check excluding Sidebar and new-artifact whitespace checks pass.

## 37. Zero effects

```text
database effects=0
PostgreSQL effects=0
candidate execution effects=0
Application execution effects=0
Publication effects=0
Activation effects=0
RuntimeAdoption effects=0
resolver invocation=0
runtime effects=0
production effects=0
staging effects=0
shared DB effects=0
AdminApps real effects=0
external API effects=0
normative effects=0
automatic learning effects=0
external business effects=0
historical reconstruction effects=0
```

These are task non-execution statements, not queried row counts. No database,
container, role, adapter, lifecycle row, live approval or retained operational
manifest was created. No external service was contacted. No installed or
shared environment was inspected. No teardown was needed or authorized.

## 38. P0 / P1

P0=0; P1=4: B1 root/full-row freshness binding; B2 compatibility preimage;
B3 release preimage; B4 directly dependent Proposal/governance input graph.
Schema completeness is established, but an authentic complete value preimage
is not. Additional unresolved prebound evidence hashes=2; unresolved target
binding remains B1. No blocker was downgraded to a warning.

## 39. Residual risks

Any future successor must distinguish root time, raw JSON rendering, immutable
authority provenance and actual fresh authority. It must reconcile B4 without
loosening 0018 or expanding ADR-0017's identity exception implicitly. B2/B3
cannot be replaced by arbitrary material that merely has a valid hash shape.
Live PostgreSQL parity and all original operational gates remain blocking
even after a later successful offline correction.

Phase 29 remains `HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE` with
`RETENTION_CLOSURE_BREACH`; no reconstruction, reuse or continuity claim.
RuntimeAdoption and Phase 32 remain prohibited.

## 40. Final verdict

**PHASE 31.4.1 — NOT PROMOTED**

No clean Phase 31.4 retry is authorized. The only continuation is a bounded
design correction resolving B1 and its explicitly identified dependent inputs.

## 41. Exactly one continuation prompt

```text
NEXT_CODEX_PROMPT

ISO SMART AI — PHASE 31.4.1 BLOCKER-SPECIFIC SUCCESSOR DESIGN GATE — B1 ROOT TIME/FULL-ROW BINDING AND DIRECT DEPENDENCIES B2–B4 — NO POSTGRESQL

Work exclusively in /home/felipe/proyectos/isosmart. Before repository discovery/reading, cd there, run git status --short, record its exact output and run targeted git diff --check. Read AGENTS.md. Preserve every unrelated file and existing Sidebar.jsx:28 trailing space. Do not inspect siblings, reset, stash, clean, stage or commit. Use backend/.venv Django 4.2.22; never .venv312.

Read the complete Phase31_4_1_ROOT_FULL_ROW_TARGET_HASH_TIMESTAMP_BINDING_EXECUTION_READINESS_BLOCKER_CLOSURE_REPORT.md and PHASE31_4_1_ROOT_BINDING_DIAGNOSTIC_VECTORS_V1.json. Their probes are DIAGNOSTIC_ONLY_NOT_AUTHORIZED and must never be treated as approved root timestamps, governance material or execution inputs. Read complete Phase 31.3/31.3.1/31.4 reports, ADR-0017, Product Policy, exact source/lifecycle/registry/closure, complete 0009/0020/0021/0022/0023, Application/governed-learning/governance/canonical/event/audit code, Phase 26/28.3 source paths, KnowledgeLayerRule models and RLS/least privilege. Do not execute harnesses.

Before corrections require exact hashes: Phase31.3 report fc5f16abab801570aefd313b87cae1805f3e5067e73d01acebebce9519724a8f; Phase31.3.1 report 5df6ba154a49d3aede4938bdcf17ff11d524e4d75526ba96b969df9ac6a3b6da; Policy 44535b47bda30a4319903d8b9f10be04890b4d9085c8955d57916f3616d9588d; source e458cd0bb7eb11f96ce8723b0ab4dea97e4ca60b0e47a6f7e1fb1f38cef66d6b; lifecycle 683f7c83ff3e3e16733d63288d317f8b3a14fe9e5bfaf2e86b0cf2e86b6ab6ca; registry d5e1960801772af74d491c9c6f69a877b79f1e26b937701cf1a239114b37bf1c; closure d3455bc64957ef1aab5f618e552d9276bd6fd60e0b1ce2e7a8068e5c14c8917a; ADR0017 82501ef34edc6d7e76e0971d3d2607c58f229a1dd4dd26696dd227fb7e994edb; migration-set cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc. Verify all individual migrations and 0024 absence. Verify Phase31.4 report 2bd96b31bf55dd36b7a459b1ff511bea8cbe4de43562be9e97162ab2489aeb8d, evidence b8490b2bb2cd059b015be7a97731dad009b45018fa822278b61daabb886fbf70 and ledger 62e8de3eb43ea726ef3f48f2e2bef382342d941e6f3f403bcf7f4c31908eec70. Stop NOT PROMOTED on mismatch.

Resolve B1 explicitly: root bc5f4f17-294d-5abd-b27b-2d296921ffdf has 13 hashed fields, 11 known values and no authentic created_at/published_at. Its old target dbaa2e4eff3c980522a916d0cf2f10127e39f0af8dbfdacb469ac3015d8d87db is embedded in Delta 06f75de72e2a2ded515c223a1c62df6ab3780ebfe1ed0ccca71a22a222071c9e. Do not guess dates, search preimages, remove fields, substitute 0022 selected hashes or weaken validation. Decide and document either an explicitly approved synthetic-time Model A with new exact values/full preimage or Model B with live root persistence before exact target/Delta/Proposal freeze. B is the current recommendation, not an adopted execution contract; under B stop requiring an unknowable precreation numerical target and explicitly govern the execution-derived package. Record the genuinely new architecture in a successor ADR and an explicit policy successor only when complete and authorized; never label diagnostics as approval.

Resolve B2 and B3 by authentic exact compatibility/release evidence preimages or explicit successor material/derivation rules with full schema and hashes. Old hashes are 43c72090f30e90a4f3896b3d194aa264f421189f0589978453136464e270dbc9 and 5583dd2939abe5e1e2d602cef33077685df8efb48f0c664812eaee138723d15a. Resolve B4: promoted 0018 requires supporting LearningSignal/Effectiveness history, missing in the Phase31.3 package. Define an authorized wholly new synthetic supporting graph, projections and nonfresh Proposal/Review/Decision material with exact identities/provenance; reconcile the no-unauthorized-LearningSignal rule explicitly. Do not bypass guards, borrow Phase29, or let the Application adapter create unapproved governance material. Preserve existing IDs only under explicit successor identity/change-control semantics.

Produce only necessary append-only successor contracts, evidence, offline tests and report. Recompute every affected target/Delta/Proposal/Review/Decision/Authorization/idempotency/claim/Receipt/Event/Audit/closure binding. Distinguish raw key SHA-256 from Authorization idempotency_hash and 0021 claim identity/material. Preserve PostgreSQL raw timestamp strings and pin JSON rendering/order context; do not feed normalized datetime objects as equivalent raw JSON. Version registry/closure only when edges or contracts actually change. Audit all prebound hashes, including defaults, generated IDs, timestamps and fresh authority fields; unresolved bindings remain P1.

No PostgreSQL, containers, roles, migrations, adapter installation, Application, Publication, Activation, RuntimeAdoption or resolver invocation. No production/staging/shared DB, real AdminApps, external API, deployment, normative or learning effect. No Phase29 reconstruction/reuse; its HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE / RETENTION_CLOSURE_BREACH classification remains permanent. Phase32 stays blocked.

Run only relevant offline Foundation and new contract/negative tests, canonical recomputations, JSON/schema checks, Python in-memory compile, Django system check, makemigrations --check --dry-run, historical/migration/protected-byte checks, git diff --check and final status. Explicitly exclude resolver-invoking and historical-lifecycle tests. Keep PostgreSQL parity/rollback/concurrency/ACL/RLS NOT EXECUTED. Return a precise verdict and exactly one next prompt; only a fully accepted successor with no P0/P1 may propose a future clean Phase31.4 retry, which must repeat every original isolation, parity, security, lifecycle, complete Publication closure-before-Activation, independent re-read, teardown and zero-RuntimeAdoption gate.
```
