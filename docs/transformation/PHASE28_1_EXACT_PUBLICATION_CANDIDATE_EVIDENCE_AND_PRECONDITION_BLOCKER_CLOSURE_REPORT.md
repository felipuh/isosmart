# ISO SMART AI — Phase 28.1 exact publication-candidate evidence and precondition blocker closure

- Date: 2026-09-03 (`America/Costa_Rica`)
- Workspace: `/home/felipe/proyectos/isosmart`
- Nature: documentation, evidence, source-provenance and blocker-closure design gate
- Database, candidate, publication, activation, adoption, runtime, deployment and external effects: **ZERO**

## 1. Verdict

Phase 28.1 closes the design question through promotion path B. The original
Phase 26 publication candidate is permanently unavailable because the exact
complete graph was not retained and cannot be reconstructed truthfully. A
future isolated synthetic POC fixture is permitted only as a new lineage under
an explicit non-official, non-normative, non-licensed, test-only and
non-production classification. This gate authorizes only future implementation
of inert blocker foundations.

It authorizes no candidate creation, publication, activation, RuntimeAdoption,
migration 0023, runtime wiring, production, deployment or external effect.

## 2. Entry baseline

- Phase 26: promoted as an ephemeral governed target-application POC.
- Phase 27: not promoted.
- Phase 27.1: promoted for design.
- Phase 27.2: promoted for inert foundation only.
- Phase 28: not promoted; no candidate authorized.
- Migrations 0001--0022: frozen; 0023 absent.
- Phase 26 run: `20260903T003052Z_f66933`; disposed database
  `foundation_gate_20260903t003052zf66933`.

Entry `git status` was captured before writing. The worktree was already
materially dirty, including unrelated backend/frontend/SQLite changes and
untracked foundation/governance history. All were preserved.

## 3. Phase 28 blockers

Phase 28 identified seven P0 and three P1 conditions: no exact retained
candidate/graph, synthetic rather than authoritative source provenance,
semantic-hash substitution risk, absent Receipt/governance/curator checks,
missing actor-level SOD, missing current-leaf serialization, incomplete
idempotency/reconciliation/TOCTOU material, and legacy published-status runtime
compatibility risk. Phase 28.1 closes these as an exact future implementation
contract; it does not implement or exercise that contract.

## 4. Evidence search methodology

The search was read-only and covered tracked, untracked and ignored workspace
files, reports, manifests, test-result directories, logs, SQL/dump/backup-like
filenames, SQLite bytes, compiled artifacts and Git refs. Text and binary-safe
searches used the Phase 26 run/database names, `phase26-vN-plus-1/2`, source
scheme/hash, operation, Receipt table and graph fields. Candidate files were
hashed and stat metadata captured. The ten sources were read/parsed directly;
Office packages passed ZIP CRC and embedded-content search.

No external CI, cloud, production or staging was accessed. PostgreSQL was not
started; no database was restored; the Phase 26 fixture was not rerun.

## 5. Evidence-location inventory

| Path/type | Created / modified metadata | Provenance and Phase 26 association | Exact IDs/hashes/Receipt/graph/source | Classification |
|---|---|---|---|---|
| `backend/foundation/postgres_phase26_harness.py` — source | created `2026-09-02 18:05:19 -0600`; modified `18:30:29` | executable fixture definition, direct Phase 26 association | runtime-generated UUIDs; no emitted IDs, hashes, Receipt row or graph; synthetic source grammar only | authoritative for test design, not run evidence; reconstruction required |
| migration `0021` — source | created `2026-09-02 17:53:07`; modified `18:26:58` | promoted schema/function contract | table/function shapes and hash algorithms, no run values | authoritative contract, not candidate evidence |
| `governed_learning_application.py` — source | created/modified `2026-09-02 17:48:51` | Phase 26 service boundary | no run material | authoritative contract, incomplete for recovery |
| `learning_delta.py` and governance implementation — source | modified no later than `2026-08-25` for delta file | canonical delta and governance implementation | grammar/algorithms only; no Phase 26 rows | authoritative contract, incomplete for recovery |
| Phase 26 report — sanitized report | created/modified `2026-09-02 18:32:35` | names exact run and teardown | summary/counts/code hashes; no candidate UUIDs, full-material hashes, fingerprint, Receipt/event/outbox/audit rows | authentic summary only; incomplete |
| Phase 27/27.1/27.2/28 reports — sanitized reports | modified through `2026-09-03 08:34:09` | later reviews of Phase 26 | repeat classifications and implementation hashes; no original graph | authentic summaries only; incomplete |
| `backend/logs/ai/django.log` — ignored local log | created `2026-06-22`; modified `2026-09-02 20:13:22`; 6,553,560 bytes | no Phase 26 term, run, rule label, source scheme or Receipt event match | none | unrelated; not evidence |
| `frontend/test-results/.last-run.json` — ignored test result | created/modified `2026-08-13`; 45 bytes | predates Phase 26 and has no association | none | unrelated; not evidence |
| `backend/test_default.sqlite3` — local SQLite | created `2026-06-22`; modified `2026-07-29`; 1,904,640 bytes | predates Phase 26; binary strings contain no search marker | none | unrelated; not evidence |
| workspace SQL/log/backup/snapshot/archive candidates | filename and content scan current at gate time | only authoritative reference SQL and ordinary app logs exist; no dump, backup, Phase 26 manifest or archived output | none | no evidence candidate found |
| Git refs/history | current local refs searched | no Phase 26 commit/message or retained run artifact | none | no evidence candidate found |
| ten authoritative source artifacts | filesystem dates `2026-08-13`; hashes in section 48 | source intake package, not Phase 26 database evidence | authoritative package hashes; no R1/R2/run graph | authoritative sources, not recovery evidence |

Every positive Phase 26-associated item either defines how fresh values would
be produced or summarizes predicates previously tested. None proves the exact
disposed rows. Therefore every recovery path would require reconstruction.

## 6. Evidence integrity hashes

| Evidence candidate | SHA-256 |
|---|---|
| Phase 26 harness | `0211b25081cc90f61d6497faf101fad42d5a92cd960f5463b2df1efb09f0df95` |
| migration 0021 | `e796910c1660f701c3457b020792a158c06d3e58135a7ebba1728bd8b33c7a97` |
| Phase 26 application service | `99d228984efe4bba15c76f91e157f2ddd66d8aec9b5bf153a21c095fd57ed8cf` |
| canonical learning delta | `8a3a2187567737ad2034ac6abf695dd73ce356356d3e1dd82c2e61f7fc0944cd` |
| Phase 26 report | `ce36196c4094addba4fb31a512582a05af0113036c3894cb20eb938d1eefedd9` |
| Phase 28 report | `bbd5ba9edf897e82da0283bd4acd5202586d503ee60852ee170d716b19661dc1` |
| ignored Django log | `16a2485c19fd59b34a5487a22a77d7dd5903613851620e2c351b4bb6e7bd3a54` |
| ignored frontend result | `91d1c43004802cd49950d78eb11c8fa7d05da8ffffe219a8b13b2f561bc00903` |
| local SQLite | `67e646cc6b1d4d62ce2d603b0373ac8c0d4c4863f5426389711ca7953a122ddd` |

Hashes establish the bytes inspected, not authority to reconstruct historical
rows.

## 7. Exact-ID recovery result

**NOT RECOVERED.** The vN/vN+1/vN+2, KnowledgeLayer, lineage, Standard,
StandardEdition, LearningSignal, Proposal, CanonicalDelta, Review, Decision,
Authorization, forward/compensation Receipt, event, outbox, audit and trace IDs
are not retained as exact run evidence. The exact target hashes, proposal/delta
hashes and Phase 26 semantic fingerprint are also absent.

## 8. Complete-graph recovery result

**NOT RECOVERED.** Neither the forward graph nor the separately governed
compensation graph is present or cryptographically proven. Counts and successful
predicate assertions in a sanitized report do not provide bidirectional row
identity/material. Partial structural knowledge is insufficient.

## 9. Recovery-versus-authorization distinction

Recovered identifiers alone would not authorize publication. Evidence would
still have to prove authenticity, integrity, association with the promoted run,
complete graph, target/hash/canonical-delta/Receipt correspondence, source
provenance, fingerprint and absence of reconstruction. `RECOVERED != AUTHORIZED`.

## 10. Reconstruction prohibition

No UUID was generated for Phase 26, no fixture rerun, order-derived ID,
equivalent row/hash, fabricated Receipt/event/audit or replacement database was
used. Equivalent new artifacts are not historical artifacts. This prohibition
is permanent for publication provenance.

## 11. Phase 26 candidate availability

```text
PHASE26_PUBLICATION_CANDIDATE = PERMANENTLY_UNAVAILABLE
```

This classification concerns future publication only. It does not invalidate
the successful ephemeral Phase 26 POC or its promoted mechanism evidence.

## 12. vN+1 supersession

`vN+1` remains ineligible regardless of later evidence. The separately
governed compensation created `vN+2` and reversed `R2` to `R1`; publishing
`vN+1` would resurrect the state intentionally superseded by the later chain.

## 13. vN+2 truthful final intent

`vN+2` remains the truthful final leaf of the disposed Phase 26 lineage. That
historical statement is distinct from an addressable retained publication
candidate. The former is proven by the POC report; the latter is unavailable.

## 14. Permanent-unavailability decision

ADR-0015 records the intentional consequence of ephemeral teardown without a
cross-phase evidence manifest. Only discovery of a complete authentic retained
artifact, requiring no reconstruction, could reopen evidentiary review; partial
IDs or semantically equivalent reruns cannot.

## 15. Synthetic source-reference analysis

Implementation constructs and validates:

```text
R1 = iso-smart-source-ref-v1:<ephemeral StandardEdition UUID>:<64 x "3">:clause/A
R2 = iso-smart-source-ref-v1:<ephemeral StandardEdition UUID>:<64 x "3">:clause/B
```

The UUID was selected at runtime from a Phase 9 fixture. The source text says
`NON-OFFICIAL TEST FIXTURE`, publisher is `TEST`, and source hash is synthetic.
The grammar validates scheme, UUID, lowercase SHA-256-shaped value and locator;
it does not turn fixture bytes into an ISO locator.

## 16. Authoritative-source comparison

Direct text, binary-safe and embedded OOXML searches found no `clause/A`,
`clause/B`, Phase 26 rule key, source scheme or 64-character `3` hash in any of
the ten artifacts. None of the ten file hashes equals the synthetic hash. No
ephemeral StandardEdition UUID can be matched because its exact value was not
retained. Therefore no real source element or authoritative locator mapping
exists and none is inferred.

## 17. Synthetic source policy decision

**SYNTHETIC SOURCE POC PERMITTED**, but only for a future isolated gate as:

```text
NON_OFFICIAL_TEST_FIXTURE | NON_NORMATIVE | NON_LICENSED | TEST_ONLY | NON_PRODUCTION
```

This follows the non-certifiable KnowledgeLayer boundary, explicit Phase 9/26/
27.2 fixture convention, prohibition on licensed bodies, and separation of
Product Policy from ISO requirements. It does not authorize publication. An
authoritative candidate must use the separate authoritative-source validation
branch and cannot cite this fixture.

## 18. New-candidate-versus-recovery boundary

A future deterministic fixture is a **NEW CANDIDATE** with new identity,
lineage, hashes, canonical delta, governance chain, application Receipt,
events/audits and publication authorization. It must never be described as
recovered, recreated or equivalent Phase 26 `vN+2`.

## 19. Deterministic synthetic manifest design

The future repository-retained manifest is
`SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_FIXTURE_MANIFEST_V1`. Design-only
namespace UUID is UUIDv5(URL,
`https://iso-smart.local/fixture/publication_poc_fixture/v1`) =
`5352691a-f23c-5b70-ae29-5fc7c9fca0ce`; names are UTF-8 and UUIDv5-derived.

Required exact design:

| Field | Designed value/contract |
|---|---|
| `manifest_version` | `1` |
| `fixture_namespace` | `publication_poc_fixture/v1` |
| `source_fixture_id` | `6ec35e4a-bb8a-592b-bc6a-420691f4e8e3` |
| classification | all five closed classifications in section 17 |
| source bytes | UTF-8 lines: title; classification tuple; `element=A`; `element=B`; each LF-terminated |
| source SHA-256 | `d4ae0c59a471fa244db3bdbfef9d92d248a4e6d361a6ba790e5750ebe2a162d1` |
| Standard / Edition / Layer | `ff55b0db-673a-5e17-999d-336bc161d5dd` / `68982c5c-664f-54ab-9bb2-ee393852f57f` / `42625c31-0683-5726-b16c-c1ad9b69a208` |
| lineage / root / candidate design IDs | `c8e2b508-8763-53a2-8bda-c3c77a1aa21e` / `87020f62-38ed-58c0-a5de-bba62ff46926` / `4bbd886f-2398-506e-885c-6d2e87dd4b3d` |
| source reference | `iso-smart-source-ref-v1:68982c5c-664f-54ab-9bb2-ee393852f57f:d4ae0c59a471fa244db3bdbfef9d92d248a4e6d361a6ba790e5750ebe2a162d1:fixture/element/A` |
| layer/rule semantics | layer type `Quality Intelligence`; rule key `publication-poc.synthetic-source-reference`; logic `{"operator":"fixture_locator_is","value":"fixture/element/A"}`; evidence `{"required":["synthetic_fixture_reference"]}`; classification `non_certifiable_guidance` |
| Phase 26-compatible fingerprint | canonical JSON, sorted keys, compact UTF-8; expected SHA-256 `71b6ce51297dbc3fe9abcdc948a68d72653b73c76ffe0bebccda05ce7b3ea2e1` |
| Phase 27.2 lifecycle hash | exact narrower field set; expected SHA-256 `fed67ae8895077dd41c608154ef007fbac6c423bae3460cb0c76b46dfde64072` |
| target material hash | 0022 field shape and canonicalization; expected design SHA-256 `e89a48d7851567d0b1d18337593675aefc1ffd6b4ac735fcf2fc0832d629ce31` |
| operation profile | exact source-reference correction v1; no status/publication/activation/adoption input |
| governance reference | ADR-0015 plus existing Phase 25.1 and publication/activation/adoption policies; later explicit gate required |

The manifest also freezes generation algorithm, canonical bytes, every derived
name, tool-independent verification vectors, `licensed_content_present=false`
and `phase26_continuity_claim=false`. Nothing in this section creates rows.

## 20. Cross-phase evidence retention design

Before teardown, `GOVERNED_TARGET_APPLICATION_EVIDENCE_MANIFEST` must contain:
run ID; target type/ID/lineage/KnowledgeLayer/revision/predecessor; exact full
material hash; fingerprint and version; locator/hash/classification; Proposal
ID/hash; CanonicalDelta ID/hash; Review set IDs/hashes; Decision and
Authorization IDs/hashes; Receipt ID/hash and full sanitized material; event,
outbox and audit IDs/hashes; trace; migration version; policy IDs/versions/
hashes; creation time; canonicalization version; and manifest SHA-256.

It is generated and verified before teardown, contains no secret or licensed
body, is stored in a repository-approved sanitized evidence location, and is
immutable after promotion. Any change creates a successor manifest/version
that links the prior hash.

## 21. Phase 26 semantic fingerprint

`foundation_0021_rule_semantic_hash` hashes canonical JSON using
`qms.foundation_0020_canonical_json_value`, UTF-8 and SHA-256. Contract version
is `iso-smart-knowledge-layer-rule-substantive-fingerprint-v1`.

## 22. Fingerprint included fields

Exact fields: `fingerprint_version`, `target_type`, `knowledge_layer_id`,
`knowledge_layer_type`, `standard_id`, `standard_edition_id`,
`standard_edition_source_hash`, `lineage_id`, `rule_key`, `logic_json`,
`evidence_expectation`, `certifiability_classification`, and
`source_reference_scheme`.

## 23. Fingerprint excluded fields

Code intentionally excludes rule ID, version/revision, predecessor, status,
`published_at`, timestamps and the exact locator. The locator exclusion permits
the approved correction while the scheme, edition and source hash remain
frozen. Bindings/provenance are separate proof sets, not implied exclusions.

## 24. Phase 27.2 hash contract

`foundation_0022_rule_semantic_hash` hashes only `knowledge_layer_id`,
`rule_key`, `logic_json`, `evidence_expectation`, and
`certifiability_classification`. Its purpose is lifecycle-foundation consistency.
Separately, `foundation_0022_rule_material_hash` covers ID, layer, lineage, key,
version, predecessor, logic, evidence, full source reference and classification.

## 25. Hash-contract non-equivalence

The Phase 26 semantic fingerprint is not the Phase 27.2 semantic/lifecycle
hash. The latter omits version marker, target/layer type, Standard/Edition/source
identity, lineage and source-reference scheme. No publication may alias or
substitute the two.

## 26. Future publication hash requirements

Admission must independently bind and recompute: (A) full target material hash,
(B) Phase 26-compatible semantic fingerprint, (C) publication/lifecycle hash,
(D) source locator/hash/classification/manifest, and (E) governance/application
Receipt provenance. A mismatch in any one fails closed.

## 27. Current-leaf gap

Confirmed. `publish_knowledge_layer_rule_v1` locks the candidate row and checks
draft state, timestamp, material hash and prior Publication, but not absence of
a child. Future code must lock a stable lineage stream, assert exact predecessor
and candidate revision, and execute `NOT EXISTS(child)` before write and again
precommit.

## 28. Receipt validation gap

Confirmed. Native publication accepts no application Receipt and reads none.
Future validation rejects missing/mismatched Receipt, wrong revision/hash/delta,
non-exact result relation, or a Receipt with `runtime_effect_changed != false`,
`result_published != false` or `external_effects != false`.

## 29. Complete governance validation gap

Confirmed. Publication currently does not load Proposal, CanonicalDelta,
selected Reviews, Decision or LearningApplicationAuthorization. Future code
must compare every ID/hash/operation/version/target tuple bidirectionally with
the candidate and Receipt and reject legacy-inert, stale, superseded or partial
chains.

## 30. Source-validation gap

Confirmed. Native publication does not validate the exact source reference.
Authoritative candidates require an authoritative locator/hash/edition proof;
synthetic candidates require exact manifest ID/hash and all closed
classifications. Cross-class substitution is denied.

## 31. Curator evidence gap

Confirmed. The current function creates its own compatibility curation audit;
it does not require an independent prior curator decision. Future publication
requires separate immutable curator evidence plus publisher authority. Neither
the learning chain nor Receipt implies curation.

## 32. Actor-level SOD gap

Confirmed. Distinct PostgreSQL principals do not prove distinct humans. Future
publication freezes and compares actor IDs. At minimum application executor !=
publisher and curator != publisher. Product Policy additionally enforces the
applicable separation from proposer, selected reviewer(s), approver and
application authorizer, with no client-asserted identity.

## 33. Publication idempotency gap

Current material is `rule_id:expected_hash:reason`. Future immutable material
identity includes candidate/lineage/predecessor, all four hashes, source
provenance, Receipt and governance graph, curator evidence, policy and publisher
authority provenance. Exact replay returns the same Publication; any changed
material conflicts.

## 34. Concurrency gap

Same-candidate uniqueness exists, but different revisions are not serialized.
Future fixed lock order is operation claim, lineage advisory/stream row,
candidate/predecessor, Receipt/governance, curator evidence and release claim.
A successor creation or C2 publication racing C1 makes stale C1 deny; no two
contradictory results commit.

## 35. TOCTOU gap

Immediately before commit, under retained locks, re-resolve fresh authority,
capability, current leaf, full hash, both semantic/lifecycle hashes, source
provenance, Receipt, complete chain, curator evidence, unpublished state, no
activation/adoption and material identity. Drift rolls back.

## 36. Atomicity gap

The future transaction contains claim, all validations, immutable Publication,
legacy status projection only if proven isolated, independent curation evidence
link, event, outbox and audit in one commit. It contains no Activation or
RuntimeAdoption. Phase 27.2 atomic mechanics are reusable only after the missing
bindings are added.

## 37. Event gap

Future `knowledge_layer_rule.published` v1 includes candidate, layer, lineage,
version/predecessor, material/fingerprint/lifecycle hashes, source
classification and locator/hash or manifest hash, Receipt, Proposal/delta/
Decision/Authorization references, curator evidence, publisher authority,
policy and trace. It asserts `activation_requested=false`,
`runtime_adoption_requested=false`, `runtime_effect_changed=false` and
`external_effects=false`.

## 38. Audit gap

The immutable audit freezes the same exact bounded provenance, actor-level SOD
result, reason, claim and timestamps. It stores no licensed normative body,
Evidence body, prompt, secret, token or unnecessary PII. Current 0022 audit
lacks Receipt/source/full-fingerprint/curator bindings.

## 39. Reconciliation gap

Outcomes remain exactly `COMMITTED`, `NOT_COMMITTED`, `ABANDONED` and
`INCONSISTENT`. COMMITTED requires the complete bidirectional graph, including
all new evidence bindings. Target state or Publication alone is insufficient;
no Publication, Receipt, curation or authority is reconstructed.

## 40. Legacy runtime compatibility

Current Recommendation/AgentRun accept a caller-supplied exact rule ID when
`status=published`; they are byte-unchanged and do not use RuntimeAdoption.
Thus a future synthetic publication POC must run in a database/role/runtime
isolation where its ID cannot reach those inputs, or native publication must
avoid/replace the compatibility projection only under a separately proven
contract. Required deltas remain Activation 0, RuntimeAdoption 0 and current
Recommendation/AgentRun behavior 0.

## 41. Future DB contract

Additive implementation may add: evidence-manifest identity/hash/version and
immutable successor link; candidate-to-Receipt and candidate-to-fingerprint
bindings; source-provenance enum plus mutually exclusive authoritative/synthetic
constraints; curator evidence FK/hash; governance material hash; actor SOD
evidence; extended publication material identity; lineage stream lock/key;
unique publication per exact candidate; indexes for current-leaf and graph
reconciliation; immutable guards and retained-history reverse protection.

No generic payload/DML, fake tenant scope or migration 0023 is created here.

## 42. Future service contract

```text
load candidate
-> resolve fresh publication authority
-> validate actor-level SOD
-> check capability fence
-> lock lineage in fixed order
-> verify exact current leaf/predecessor/revision
-> verify target material hash
-> verify Phase 26-compatible fingerprint
-> verify publication lifecycle hash
-> verify source provenance branch
-> verify exact application Receipt
-> verify complete governance chain and curator evidence
-> compute immutable idempotency material
-> append Publication + projection + event/outbox/audit atomically
-> revalidate every mutable precondition
-> commit
```

No Activation or RuntimeAdoption is invoked or requested.

## 43. Future test matrix

Mandatory tests are: (1) exact retained candidate accepted; (2) missing evidence
rejected; (3) reconstructed evidence rejected; (4) wrong Receipt; (5) wrong
Proposal; (6) wrong delta; (7) wrong Review; (8) wrong Decision; (9) wrong
Authorization; (10) wrong locator; (11) wrong source hash; (12) synthetic-as-
authoritative; (13) wrong fingerprint; (14) 0022-for-0021 hash substitution;
(15) stale/non-leaf; (16) actor SOD; (17) stale authority; (18) capability
disabled; (19) exact replay; (20) changed material conflict; (21) concurrent
same candidate; (22) different-revision race; (23) target drift; (24) Receipt
drift; (25) source drift; (26) event rollback; (27) outbox rollback; (28) audit
rollback; (29) precommit rollback; (30) no Activation; (31) no RuntimeAdoption;
(32) runtime unchanged; (33) normative state unchanged; (34) no automatic
learning; (35) ambiguous-COMMIT reconciliation; (36) retained-history reverse
protection.

The matrix also validates manifest canonicalization vectors, cross-class source
denial, every graph FK/hash, hostile search path, ACL/owner properties and
isolation from legacy runtime inputs.

## 44. P0/P1 classification

For a future **inert blocker-implementation phase**, all P0/P1 conditions now
have explicit deny rules, storage bindings, lock order, atomic graph, test and
reconciliation obligations: **0 unresolved design P0; 0 unresolved design P1**.

Implementation evidence is deliberately outstanding and fail-closed. Any
missing current-leaf, provenance, fingerprint, Receipt/governance, SOD, runtime
isolation or normative-contamination control is P0. Any incomplete idempotency,
concurrency, reconciliation, audit, history retention or zero-runtime-effect
proof is P1 and blocks later promotion.

## 45. Promotion-path decision

Path A fails: authentic complete recovery did not occur. Path B passes at
design level: permanent loss is formally recorded; synthetic test provenance
is narrowly allowed; deterministic fixture and retention contracts are exact;
new/old candidates cannot be confused; hardened preconditions are specified;
and this phase performs no runtime implementation or publication authorization.

## 46. ADR

Created successor ADR-0015,
`docs/adr/0015-retained-cross-phase-evidence-and-synthetic-publication-fixture.md`,
SHA-256 `57da49dff842349af8a7f3720595d858e96742d782bfe414174f84b8a1f3efea`.
ADR-0013 and ADR-0014 remain byte-identical.

## 47. Migration hashes

Migrations 0001--0022 are **22/22 MATCH**:

```text
0001 0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51
0002 1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537
0003 dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc
0004 045043275245e5d8068a8e03d122f5fe34b8f9f60b020336e61881550ecea125
0005 96ab33a18252dc0c2e6142f7afdc02a165349d15d50b290b4092c844a1996e86
0006 033242bd6fe801da0b090a332b9f6d1b07dba77027a0334d1830e845cd51aa95
0007 c7f6a2030c9155714093a21fadb571a1cdeb8a121be5598540d4807af62283ec
0008 285aecb34d5f7e8c1a1273c9622cde7933809949ac7bdbfca04e577e9e762032
0009 412c645974635959c74a446f64dc0a9b6dfd2a1a50a6a2e346698850e998effc
0010 c4f37a9a3a8d0d20a049e4e1cc9c0e04feb947cbeec9cea18fa89b7964f57b79
0011 cdb23edcad75e8a8781815dac847359a368b64d8ea4b607a40d01d5296c863a2
0012 7f280e24a8e95858b8144aa6a85fc645245aa2c2d3c2ad5700dfbe19ac0f0fdc
0013 06177fde1c25d884602a41d03df6d2625e8d15df18d7c66bffdb047348abf34b
0014 ee0e42a7d45803f633ca40d9b0ca20987a20acfdaf3452ee81d721cec29ada33
0015 5e297591c8096938c90b6748d0d3ed22a8099cf8f4537e7f65f8bc6fa5beaba3
0016 e922ff20285751193382a17d9fe7e71726511bff659f4e66b97748e6ad43cdd5
0017 580f16d1cdb10c30bae8f3e3c1667c3c4d2552b895fc9dea053d2c9b6adfaa38
0018 703a85885a67df953f38ef35302205caeddea249104683f4f751ab20ece0696b
0019 c188b638124404bba10cae4c94a678053d49d7a1d07c6e455a48e46524064b50
0020 491f21d3422c9c9a5866520f6623d3b9c9bea2139083f0128495dd7207d19894
0021 e796910c1660f701c3457b020792a158c06d3e58135a7ebba1728bd8b33c7a97
0022 afefd7100a18e5c7324efaeb1af656225b309fd86f08673a8742f7f9f6c2e618
```

Migration 0023 is **ABSENT**.

## 48. Source hashes

Authoritative sources are **10/10 MATCH** and directly readable:

```text
DOCX     8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c
Draw.io  e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa
Mermaid  11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3
XLSX     952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5
Nodes    ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3
Edges    30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6
SQL      de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e
OpenAPI  29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8
JSON     c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb
LEEME    eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db
```

DOCX/XLSX CRC, JSON parse, CSV reads and all text reads passed. Integrity does
not create a correspondence with the Phase 26 synthetic source.

## 49. Governance hashes

Unchanged baselines: Phase 25.1 policy `1a5f7c7838c62ba76837c26fcfa4d29655294810f74afed33fdcf69dc373bb79`;
governed-learning policy `7d9c2fe30548bd18d390d119889c87a93595ac281fa3326691fe486bee49c4ec`;
implementation authorization `04458c4f1ccead125dd98ddac946ec9d77f8b0212412d13128355b10129c875c`;
review/application boundary `2d5beaebd5b2df1378c0f425354b45d52ff23dd1a5d158adad46572f7656c514`;
publication/activation/adoption policy `efdd4d8a679c7f18762bfe79c3e876e970f81fedb2848ef5cbf21e7aeb858556`;
ADR-0013 `8fa5852a3cabf822c5213ae10bcae2a61f3910233ff1d915d4d1e1545df6a827`;
ADR-0014 `fa0e376e802f80e95d3961fabf8f6fe5e337f4b312062123ffd45c31bb300952`.

## 50. Runtime/protected hashes

Unchanged: models `9dd94c945dd0c256c3872e82b45760b06c066a4364e3dc3d833d56c09645c244`;
Phase 26 application `99d228984efe4bba15c76f91e157f2ddd66d8aec9b5bf153a21c095fd57ed8cf`;
Phase 27.2 release service `a7b0477f48120b852d9ec510d30e85d4700f5c0ba970e3ed3c9e244b1be4d7e9`;
eventing `c7620cdfb0b51a0c1e022358dcbdae8a7e56b363e182dc09aa11ec675ecf95b8`;
audit `461459401abb354b22c42eec05dcd9805e4fd7800554c67b96aee8885c6734ef`;
AgentRun runtime `6767e2098365536b88d4d8e9afdaef0f8b796383c79d7f40e0e0ea91b964ec2d`;
Recommendation `655fbdd18437f3d04a838c4dfad0b5b5fb3f6cc2e3d53d29fcc21a22acc6648c`;
Phase 26 harness `0211b25081cc90f61d6497faf101fad42d5a92cd960f5463b2df1efb09f0df95`;
Phase 27.2 harness `b089ddf3fc37456041677d120348cb01e036897fbc57357f94dcb05888aeb9c8`.

## 51. Git hygiene

Only this report and ADR-0015 are introduced by Phase 28.1. Existing dirty work
is preserved. Scoped whitespace validation is required because repository-wide
status includes unrelated user work. No implementation, migration, source,
policy, historical ADR/report, test, SQLite file or external workspace is
modified.

Scoped `git diff --no-index --check` passed for both new documents. Django
`manage.py check` was attempted without starting PostgreSQL but could not reach
the check framework: the installed Django rejected the pre-existing
`models.CheckConstraint(check=...)` call while importing
`backend/foundation/models.py` (`TypeError: unexpected keyword argument
'check'`). This gate does not claim a Django PASS and did not modify code or
dependencies to mask the unrelated environment/API mismatch. A migrations
dry-run was not repeated because it crosses the same failed setup path.

## 52. Zero external effects

Confirmed deltas: Publication 0; Activation 0; RuntimeAdoption 0;
KnowledgeLayerRule 0; candidate status 0; `published_at` 0; runtime behavior 0;
ModelPolicy 0; AgentDefinition 0; normative catalog 0; external effects 0.
No database/network/provider/AdminApps/MedSupplier/object-storage/notification/
deployment action occurred.

## 53. Residual blocker

There is no unresolved design blocker for the next **inert blocker-
implementation** phase. Actual implementation and PostgreSQL evidence remain
mandatory and unauthorized here. Publication itself remains blocked until a
later gate has an actually retained new candidate, passes all implementation
tests, proves legacy-runtime isolation and issues explicit publication policy/
authorization.

## 54. Final verdict

**PHASE 28.1 — PROMOTED FOR PUBLICATION-BLOCKER IMPLEMENTATION DESIGN ONLY**

Meaning: the old Phase 26 candidate is unavailable, the new deterministic
fixture is design-only, and no candidate or release transition is authorized.

## NEXT_CODEX_PROMPT

Execute Phase 28.2 exclusively in `/home/felipe/proyectos/isosmart` as an
INERT PUBLICATION-BLOCKER FOUNDATION IMPLEMENTATION. Read `AGENTS.md`, the
Phase 26, 27, 27.1, 27.2, 28 and 28.1 reports, Phase 25.1 Product Policy,
governed-learning and publication/activation/runtime-adoption policies,
ADR-0013 through ADR-0015, migrations 0021/0022, both PostgreSQL harnesses,
application/publication/runtime services, data architecture, RLS design,
threat model and all ten authoritative sources. Preserve migrations 0001--0022
and authoritative/governance/runtime artifacts byte-for-byte. Implement only:
(1) a repository-retained deterministic
`SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_FIXTURE_MANIFEST_V1` foundation
under namespace `publication_poc_fixture/v1`, explicitly
NON_OFFICIAL_TEST_FIXTURE/NON_NORMATIVE/NON_LICENSED/TEST_ONLY/NON_PRODUCTION
and never identified with Phase 26; (2) an immutable, sanitized
`GOVERNED_TARGET_APPLICATION_EVIDENCE_MANIFEST` generated and verified before
teardown; and (3) hardened publication preconditions/bindings for exact current
leaf, predecessor/lineage serialization, full material hash, Phase 26-compatible
semantic fingerprint kept distinct from the Phase 27.2 lifecycle hash, exact
source-provenance class, application Receipt and complete Proposal/
CanonicalDelta/Review/Decision/Authorization graph, independent curator
evidence, actor-level SOD, full idempotency material, TOCTOU revalidation,
atomic event/outbox/audit and four-state reconciliation. Use an additive
migration only if this entire inert contract requires it; do not mutate 0022.
Prove the 36-test matrix plus canonical manifest vectors, least privilege,
concurrency, rollback, retained-history reverse protection, source-class
separation, and legacy Recommendation/AgentRun isolation on a disposable
PostgreSQL 18.6 environment with mandatory teardown. Do not create the
candidate lineage or any candidate row; do not invoke publication; do not
create Activation or RuntimeAdoption; do not wire runtime; do not create a
publication-authorizing Product Policy; do not access production, staging,
external CI, cloud storage or external systems; do not deploy. Require 22/22
migration hashes, 10/10 authoritative-source hashes, unchanged governance/
runtime/protected hashes, zero database business-state and external effects,
and 0 P0/P1 blockers. If any exact provenance, current-leaf, Receipt,
fingerprint, SOD, isolation, atomicity or reconciliation requirement cannot be
implemented without candidate creation or historical reconstruction, fail
closed and report NOT PROMOTED without advancing to publication.
