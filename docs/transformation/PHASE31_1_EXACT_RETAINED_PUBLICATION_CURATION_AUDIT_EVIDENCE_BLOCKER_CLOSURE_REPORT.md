# ISO SMART AI — Phase 31.1 exact retained Publication curation-audit evidence blocker closure

- Assessment date: 2026-09-04 (`America/Costa_Rica`)
- Workspace: `/home/felipe/proyectos/isosmart`
- Gate: offline forensic evidence only
- Outcome: `AUTHENTIC COMPLETE RETAINED CURATION AUDIT NOT FOUND`

## 1. Verdict

`PHASE 31.1 — NOT PROMOTED — AUTHENTIC RETAINED CURATION-AUDIT EVIDENCE NOT FOUND`

The comprehensive permitted offline search found no authentic, complete,
pre-teardown retained material for `normative.curation_audit.id =
12d811ab-c3b4-4615-8972-75008a36e327`. The one retained Phase 29 occurrence is
the Publication foreign-key value, not the referenced row. No historical
field was generated, inferred, inserted, or relabelled as retained evidence.

## 2. Entry baseline

Entry verdict was `PHASE 31 — NOT PROMOTED`, stopped before PostgreSQL creation
with blocker `MISSING_RETAINED_PUBLICATION_CURATION_AUDIT`. The repository-only
Phase 29 verifier still establishes this retained state, which Phase 31.1 did
not change:

```text
CREATED=true
APPLICATION_GOVERNED=true
PUBLISHED=true
ACTIVATED=false
RUNTIME_ADOPTED=false
RUNTIME_EFFECTIVE=false
database_reconstructed=false
```

## 3. Initial git status

Captured before any Phase 31.1 change:

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

All entries were pre-existing. The known whitespace at
`frontend/src/components/Layout/Sidebar.jsx:28` was preserved. Nothing was
staged, stashed, reset, normalized, or committed.

## 4. Frozen baseline and hashes

Direct entry hashing covered exactly 23 migrations, 10 authoritative sources,
3 ADRs, 9 relevant policies, 4 retained evidence records, 12 lifecycle reports,
and 14 protected implementation/runtime files. The same inventories were
re-hashed after creation of this report and matched entry byte-for-byte. This
report is the only Phase 31.1 file and is not part of the frozen baseline.
Migration 0024 remained absent. Hash equality is byte-integrity evidence, not a
claim of semantic review by hashing.

## 5. Scope and evidence standard

The forensic content review was confined to the ISO Smart workspace and its
local Git object store. One initial `AGENTS.md` discovery command was mistakenly
rooted at the workspace parent: it returned only matching path names in sibling
repositories/dependency trees plus permission-denied messages. No sibling file
content was opened, searched, hashed, or modified, and every subsequent command
was rooted at `/home/felipe/proyectos/isosmart`. This bounded metadata-only scope
deviation is recorded as one P1 procedural violation below; it did not supply or
affect evidence. The run used no network, database, provider, AdminApps,
production, staging, or shared system. Positive proof required a complete row retained before Phase 29
teardown, with authentic provenance and cryptographic linkage. A UUID, adjacent
graph facts, executable code, deterministic fixtures, reports, and test
expectations were rejected as substitutes.

The schema, FK, creation/export, retained-manifest, diagnostic, and governance
sections necessary to decide this exact blocker were read and reconciled across
the Phase 25.1–31 lifecycle material, ADR-0013–0015, governed-learning and
KnowledgeLayerRule application/publication/activation/runtime-adoption policies,
Phase 28.3 and Phase 29 retained evidence/dispositions, Phase 29
exporter/verifier/service/harness, Phase 31 diagnostic/tests, migrations 0008,
0021, 0022 and 0023, and relevant model/eventing/audit definitions. Several
long historical reports/policies were reviewed by relevant sections rather than
read line-by-line in full; this report does not claim completion of the broader
reading program. That limitation cannot turn an absent retained row into
positive evidence and is handled conservatively by the non-promotion verdict.

## 6. Required missing curation audit

Required relation and row:

```text
relation=normative.curation_audit
id=12d811ab-c3b4-4615-8972-75008a36e327
```

Frozen migration 0008 defines exactly eight material columns: `id`, `action`,
`entity_type`, `entity_id`, `actor_id`, `trace_id`, `payload_hash`, and
`occurred_at`. There is no additional column in the Phase 29 frozen schema.
All are non-null; action/entity type/actor are nonblank; payload hash is exactly
64 lowercase hexadecimal characters. The table is append-only.

## 7. Exact candidate

```text
candidate=01a0682b-dfc8-7b49-a601-f9bda29a70a5
lineage_and_rule_predecessor=da72872a-3f3c-5fcd-86f7-0ed33e453522
version=sN+1
full_material_hash=caa24592b509334af4cd60fd7d3f3c43989d864d3f1c6e6d0d3bf83a81871f81
semantic_fingerprint=8465956c1daf27a9838bc1bfb468af3f518ae255b4662b2df40e7b8648516192
lifecycle_hash=0adfd8075cc720140c6e1f0393d286799edac8f352efd9f1969816be83c51e52
```

No alternate candidate was considered.

## 8. Exact Publication

```text
Publication/claim=e97576de-d4ef-520d-8592-d376ed401221
event=b19e4861-219d-4a07-8faf-656e02dbf9b4
Outbox=4e78cfe6-8afa-400b-85f5-e5fe72b59e04
governance_Audit=6a3ed87d-a992-4406-8ac8-233017301d35
manifest_canonical_hash=51f0b207c790e6ab0c3d67985e161ba0d0cc7b2feb888f545c1ff5eedacf5366
disposition_canonical_hash=fff3b225184282e48dad30f4e56b16444df4241b5f647f2f3750ee4a254158f1
```

Governance Audit `6a3ed87d…01d35` and curator evidence
`471971df-986f-5a99-ad15-1838f5772e34` are separately typed records and were
not substituted for the missing row.

## 9. Relevant frozen schema and FK contract

Migration 0022 makes `knowledge_layer_rule_publication.curation_audit_id` a
`NOT NULL UNIQUE` foreign key to `normative.curation_audit(id)` with
`ON DELETE RESTRICT`. Its truthful legacy import boundary reads the actual audit
row and requires the expected entity and `knowledge_layer_rule.published`
action. Consequently the Publication cannot be faithfully rematerialized from
the retained five-member release graph while the row is absent. Altering the
Publication, dropping/relaxing the FK, or inserting a recreated row is outside
the evidence gate and would not prove retention.

## 10. Evidence search methodology

The search used literal and structural, text and binary-safe scans. It checked:

- dashed UUID, compact hexadecimal UUID, and base64 UUID-byte encodings;
- `curation_audit`, `CurationAudit`, and `knowledge_layer_rule.published`;
- JSON objects recursively for the exact ID plus all eight schema keys;
- tracked and untracked project files, retained JSON, Markdown, Python, SQL,
  CSV, JSONL, project logs, snapshots, manifests, dispositions, reports, and
  archive/backup-like filenames;
- local Git history, all refs, stash inventory, and unreachable Git objects;
- Phase 29 creation, publication, export, teardown, and post-teardown code paths.

Dependency environments, node modules, Git internals during ordinary content
scans, and unrelated repositories were excluded. Git objects were inspected
separately through Git plumbing. Search stopped after these independent paths
converged on the same absence result.

## 11. Files and locations searched

The complete project tree was searched subject to the exclusions above,
including `backend/foundation/`, `backend/logs/`, `docs/adr/`,
`docs/governance/`, `docs/governance/evidence/`, `docs/operations/`,
`docs/transformation/`, `docs/transformation/source-artifacts/`, project-level
`logs/`, tracked history, refs, stashes, and unreachable objects. No project
`.dump`, `.bak`, retained SQL export, JSONL evidence stream, or archive holding
the row was found. Existing compressed dependency datasets were excluded as
irrelevant caches. The authoritative OOXML/drawio/source artifacts had no
Phase 29 run-evidence role and the binary-safe UUID scan produced no hit.

## 12. Exact-ID search results

Before this report, the dashed ID occurred in exactly three project files:

1. Phase 29 Publication manifest: one FK value;
2. Phase 31 preflight module: diagnostic constant and output;
3. Phase 31 report: description of the blocker.

The explicitly supplied user task also states the ID outside the repository;
it is an investigation directive, not historical project evidence.

There was no compact-hex or base64 UUID occurrence. Git history had no commit
selected by the exact string, no stash existed, and the inspected unreachable
blob/commits contained no UUID, curation-audit, or publication-action match.
This report adds documentation occurrences only and does not change the result.

## 13. Semantic and structural search results

The Phase 29 harness contains the SQL that originally created the row in the
same transaction as Publication. It then exports `claim`, `artifact`, `event`,
`outbox`, and governance `audit`; it does not export the
`normative.curation_audit` row. The manifest recursively contains zero objects
whose `id` is the required UUID and whose keys include all eight required
columns. No partial object keyed by that ID was found. Phase 31 independently
reports `complete_retained_row_occurrences=0`.

Surrounding retained graph members preserve Publication timestamp, publisher,
trace, candidate, and operation hash facts. The harness makes it possible to
derive a likely row from those facts. The derivation is precisely the prohibited
reconstruction path and is not retained historical row material.

## 14. Occurrence classification

| Occurrence/artifact | Classification | Reason |
|---|---|---|
| Phase 29 manifest `live_graph.artifact.material.curation_audit_id` | `REFERENCE_ONLY` | UUID foreign key; no row object |
| Phase 29 claim/Publication/event/Outbox/governance Audit | `PARTIAL_RETAINED_ROW` only as surrounding facts, not as fragments of the row | Independently typed graph members; no proof that they are retained serialization of the audit row |
| Phase 29 harness SQL | `CODE_RECONSTRUCTION_SOURCE` | Can recreate probable values; not historical execution output |
| Phase 31 diagnostic and tests | `TEST_EXPECTATION` / diagnostic | Assert absence; do not retain the row |
| Phase 29/31 reports and this report | `DOCUMENTATION_ONLY` | Narrative/reference, not row material |
| Git unreachable objects | not relevant | No matching material |
| Authentic complete retained row | `AUTHENTIC_RETAINED_EVIDENCE` | **zero occurrences** |

Repeated references were not counted as independent evidence.

## 15. Candidate evidence artifacts

The only potentially relevant retained artifact is the Phase 29 Publication
manifest. It authenticates the Publication and the FK identity but does not
contain the referenced row. The disposition authenticates teardown and the
repository-only release state but does not extend the manifest. No separate
curation export, snapshot, transaction log, SQL dump, immutable log record, or
content-addressed row artifact survived. Therefore there is no qualifying
candidate artifact whose bytes could be authenticated as the historical row.

## 16. Complete-row assessment

Complete retained row occurrences: `0`.

No single retained record supplies the eight required fields. Independently
known surrounding values were not merged. The row is unavailable, not merely
hidden behind a verifier limitation.

## 17. Provenance assessment

No artifact establishes where and when the row itself was retained because no
row artifact exists. Phase 29 proves the row was created in the ephemeral
transaction and that the Publication referenced it. It also proves teardown.
It does not prove the row bytes/material were exported before teardown. There
is no pre-teardown file timestamp, immutable export membership, file hash,
canonical row hash, or modification history for the missing row. Provenance
therefore fails the positive-proof standard.

## 18. Cryptographic verification

Byte hashes and canonical/material hashes were kept distinct:

| Artifact | File-byte SHA-256 | Embedded/recomputed canonical hash |
|---|---|---|
| Phase 28.3 creation manifest | `9272458cf9dc54f4f722b02502e5e85e9869cebb5e488f0ff15da82e77c07edd` | `9ab80f4b0208e7dac971a0759df0bdb5c28392aa423ae11cbc0d483abb739a75` MATCH |
| Phase 28.3 disposition | `b8a7c9d5a5e423e03c25819d8715e00913edfabdeef57c6611a4906849c34536` | `964b632537323764de35f9132bf7e63966df29dc89d70c1166e432d4e6436b5c` MATCH |
| Phase 29 Publication manifest | `fade372ec41dbeff118ddbb41cd154f8e8adb34799492a56f5e8d14db7e54b72` | `51f0b207c790e6ab0c3d67985e161ba0d0cc7b2feb888f545c1ff5eedacf5366` MATCH |
| Phase 29 disposition | `57633c70e0d66e2f1a7efbec0f06947cabadc1d4e0f117ca1f0dc4c305dbae9f` | `fff3b225184282e48dad30f4e56b16444df4241b5f647f2f3750ee4a254158f1` MATCH |

Phase 29 component material hashes independently recomputed and matched:

```text
claim=ad6aca4f7b50ab33b9d2855333ed1993f9a6951168103e50a5ae3e62f2580b94
artifact=b962792fe31c19d9819566680365063194c84ce2e8ab9c39fa08dba69c279c8b
event=212f1b0d66623171322e429b0818bcfcec52d4307ffa3a3ddbe5ac17b22fda42
outbox=3011dee19f51cdc7c3b67bf618a6353d82b3fd87e0c46031607994d9e8f51fbd
governance_audit=829949aa513636e453ad6f0b838928a2256676c69d803a63895b2b066d06ef82
```

There is no byte hash or canonical/material hash for an exported historical
curation-audit row because no such artifact was found. Hash-valid surrounding
evidence cannot cryptographically authenticate absent material.

## 19. Publication cross-link verification

The retained artifact binds Publication `e97576de…01221` to candidate
`01a0682b…70a5`, lineage `da72872a…e522`, exact material/fingerprint hashes,
publisher `8069fbeb-0ef6-582c-8f3b-ff88e606c869`, trace
`ffd16da6-94a4-588d-b922-2fefd9bd8a01`, timestamp
`2026-09-03T20:18:53.895599+00:00`, and required audit ID
`12d811ab…e327`. Event, Outbox, claim, and governance Audit cross-links match.

What cannot be verified is the reverse link from an authentic retained
curation row: its actual action, entity, actor, trace, payload hash, and
timestamp are absent as row material. No alternate audit was substituted.

## 20. Reconstruction versus retention analysis

The Phase 29 harness allocated the audit ID and inserted the row; adjacent
retained members reveal values that code would use. Rerunning the harness,
evaluating deterministic UUID helpers, combining adjacent fields, or inserting
the probable tuple under the historical UUID would create a reconstruction.
It would demonstrate reproducibility, not retention. No such computation was
used as evidence and no historical row was generated.

## 21. Phase 31 diagnostic reproduction

The unchanged offline diagnostic exited nonzero as designed:

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

The diagnostic was not changed. Discovery was not conflated with Activation
authorization.

## 22. Offline test results

- Phase 29 repository-only lifecycle verification: PASS; exact seven-state
  output in section 2.
- Eight Phase 31 offline regressions: `8/8 PASS`.
- Focused retained-evidence/release/Phase 29/Phase 31 suite: `35/35 PASS`.
- Full Foundation suite with Django dummy backend: `136/136 PASS`.
- Django version assertion: `4.2.22 PASS`.
- Django isolated system check: zero issues.
- `makemigrations --check --dry-run foundation`: no changes detected.
- Existing Phase 31 Python modules compiled in memory with bytecode disabled:
  `2/2 PASS`.
- New Phase 31.1 Python code/tests: not applicable; none introduced.
- PostgreSQL operational/acceptance tests: `NOT EXECUTED`.

The focused suite is a subset of the Foundation suite; counts are not summed.
An initial 26-test direct invocation produced two settings-configuration errors,
not test failures; the same intended tests were rerun under isolated dummy
settings as the passing 35-test suite. No SQLite/user state was touched by the
Foundation runs.

## 23. Database non-creation proof

No PostgreSQL process/container was started and no DSN, credential, database,
role, schema, volume, socket, proxy, import, or migration execution was created.
The diagnostic statically imports no Django/psycopg/runtime release dependency;
its regression guards that boundary and reports creation unauthorized/false.
No database command or connector was invoked during this phase. This is
non-creation evidence, not a claim of teardown for resources that never existed.

## 24. Activation non-execution proof

No Activation ID, claim, artifact, event, Outbox, Audit, capability, authority,
manifest, disposition, or function invocation was created. The offline state
and diagnostic both report `ACTIVATED=false`/`activation_invoked=false`.
Operational Activation criteria remain `NOT EXECUTED`, not PASS.

## 25. RuntimeAdoption non-execution proof

No RuntimeAdoption ID, authority, artifact, event, Outbox, Audit, resolver call,
configuration change, wiring, or cutover occurred. Retained state remains
`RUNTIME_ADOPTED=false` and `RUNTIME_EFFECTIVE=false`.

## 26. Runtime, normative, and learning invariance

Protected runtime/application bytes matched entry. No AgentRun,
Recommendation, KnowledgeLayerRule, Standard, Edition, Clause,
RequirementControl, EvidenceCoverage, certifiability, learning signal/proposal,
review, decision, authorization, Receipt, compensation, confidence,
ModelPolicy, AgentDefinition, autonomy, or source material was created or
modified. Publication itself was not mutated.

## 27. Transitive retention closure observation

Phase 29 retained an internally verifiable five-member Publication release
graph but omitted a mandatory transitive relational dependency required by the
frozen rematerialization contract. This is an architectural observation, not a
way around the blocker.

A future separate design/governance gate should formalize
`TRANSITIVE RETENTION CLOSURE`: before teardown, every immutable relational
dependency necessary to faithfully rematerialize or independently verify a
retained Publication, Activation, or RuntimeAdoption graph must have canonical
retained material or an explicitly approved non-rematerialization contract.
The closure should be computed over enforced FKs and semantic preconditions,
then verified before teardown. Historical Phase 29 evidence remains immutable.

## 28. Migration hashes

Exact entry/final SHA-256 inventory; `23/23 MATCH`, migration 0024 absent:

```text
0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51  0001
1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537  0002
dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc  0003
045043275245e5d8068a8e03d122f5fe34b8f9f60b020336e61881550ecea125  0004
96ab33a18252dc0c2e6142f7afdc02a165349d15d50b290b4092c844a1996e86  0005
033242bd6fe801da0b090a332b9f6d1b07dba77027a0334d1830e845cd51aa95  0006
c7f6a2030c9155714093a21fadb571a1cdeb8a121be5598540d4807af62283ec  0007
285aecb34d5f7e8c1a1273c9622cde7933809949ac7bdbfca04e577e9e762032  0008
412c645974635959c74a446f64dc0a9b6dfd2a1a50a6a2e346698850e998effc  0009
c4f37a9a3a8d0d20a049e4e1cc9c0e04feb947cbeec9cea18fa89b7964f57b79  0010
cdb23edcad75e8a8781815dac847359a368b64d8ea4b607a40d01d5296c863a2  0011
7f280e24a8e95858b8144aa6a85fc645245aa2c2d3c2ad5700dfbe19ac0f0fdc  0012
06177fde1c25d884602a41d03df6d2625e8d15df18d7c66bffdb047348abf34b  0013
ee0e42a7d45803f633ca40d9b0ca20987a20acfdaf3452ee81d721cec29ada33  0014
5e297591c8096938c90b6748d0d3ed22a8099cf8f4537e7f65f8bc6fa5beaba3  0015
e922ff20285751193382a17d9fe7e71726511bff659f4e66b97748e6ad43cdd5  0016
580f16d1cdb10c30bae8f3e3c1667c3c4d2552b895fc9dea053d2c9b6adfaa38  0017
703a85885a67df953f38ef35302205caeddea249104683f4f751ab20ece0696b  0018
c188b638124404bba10cae4c94a678053d49d7a1d07c6e455a48e46524064b50  0019
491f21d3422c9c9a5866520f6623d3b9c9bea2139083f0128495dd7207d19894  0020
e796910c1660f701c3457b020792a158c06d3e58135a7ebba1728bd8b33c7a97  0021
afefd7100a18e5c7324efaeb1af656225b309fd86f08673a8742f7f9f6c2e618  0022
bb9889af836ae1e92ccf75b868c4c6a8c1ab9ba1e7d63464a2cbd749a872e642  0023
```

## 29. Source hashes

Exact entry/final SHA-256 inventory; `10/10 MATCH`:

```text
30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6  ISO_SMART_AI_Aristas_Red.csv
11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3  ISO_SMART_AI_Arquitectura_Completa.mmd
e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa  ISO_SMART_AI_Arquitectura_Completa_Lucidchart.drawio
de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e  ISO_SMART_AI_DDL_PostgreSQL.sql
8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c  ISO_SMART_AI_Especificacion_Inicial_Integrada_v1_2026.docx
952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5  ISO_SMART_AI_Mapa_Maestro_Arquitectura.xlsx
c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb  ISO_SMART_AI_Mapa_Maestro_Datos.json
ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3  ISO_SMART_AI_Nodos_Red.csv
29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8  ISO_SMART_AI_OpenAPI.yaml
eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db  LEEME_Importacion_ISO_SMART_AI.txt
```

## 30. Governance and evidence hashes

Entry/final SHA-256 counts and exact values:

- ADRs `3/3 MATCH`: ADR-0013 `8fa5852a3cabf822c5213ae10bcae2a61f3910233ff1d915d4d1e1545df6a827`;
  ADR-0014 `fa0e376e802f80e95d3961fabf8f6fe5e337f4b312062123ffd45c31bb300952`;
  ADR-0015 `57da49dff842349af8a7f3720595d858e96742d782bfe414174f84b8a1f3efea`.
- Relevant policies `9/9 MATCH`: governed learning
  `7d9c2fe30548bd18d390d119889c87a93595ac281fa3326691fe486bee49c4ec`;
  implementation authorization `04458c4f1ccead125dd98ddac946ec9d77f8b0212412d13128355b10129c875c`;
  review/application boundary `2d5beaebd5b2df1378c0f425354b45d52ff23dd1a5d158adad46572f7656c514`;
  source-reference application `1a5f7c7838c62ba76837c26fcfa4d29655294810f74afed33fdcf69dc373bb79`;
  publication/activation/adoption `efdd4d8a679c7f18762bfe79c3e876e970f81fedb2848ef5cbf21e7aeb858556`;
  runtime adoption/repair `263003d342e6bf7a2b56c25dbbb230296b81280a1da45eb347b00898e3231e92`;
  Phase 28.3 candidate `1d6352eaac748fff42098242b39db63e5f446140cfc935e961eb078d40010ed8`;
  Phase 29 Publication `0dfa36804827f272ac7e289beab6e876d27af78b8ae06d3b8a5b5d46b9db8289`;
  Phase 30 Activation `43c67505ec3e3d9df0d306012e2036ced7cf437de703e8ff95b709a7af08756d`.
- Retained evidence `4/4 MATCH`: byte hashes are listed in section 18;
  all four embedded canonical hashes independently recomputed and matched.
- Phase 25.1–31 lifecycle reports `12/12 MATCH`: `f0fd1e6f…1ad1`,
  `ce36196c…edd9`, `3cc3418b…d9e1`, `ca6bf192…e5f4`, `2194fc99…6fb8`,
  `bbd5ba9e…dc1`, `e8bdfcdb…7afd`, `1d73b7e8…18c0`, `d7a35171…670d`,
  `150285ed…a7df`, `35a198e5…041b`, `a2909cd4…daa` respectively in
  chronological Phase ordering.

## 31. Runtime and protected hashes

Exact entry/final SHA-256 inventory; `14/14 MATCH`:

```text
9dd94c945dd0c256c3872e82b45760b06c066a4364e3dc3d833d56c09645c244  models.py
99d228984efe4bba15c76f91e157f2ddd66d8aec9b5bf153a21c095fd57ed8cf  governed_learning_application.py
a7b0477f48120b852d9ec510d30e85d4700f5c0ba970e3ed3c9e244b1be4d7e9  knowledge_rule_release.py
c7620cdfb0b51a0c1e022358dcbdae8a7e56b363e182dc09aa11ec675ecf95b8  eventing.py
461459401abb354b22c42eec05dcd9805e4fd7800554c67b96aee8885c6734ef  audit.py
6767e2098365536b88d4d8e9afdaef0f8b796383c79d7f40e0e0ea91b964ec2d  agent_runtime.py
655fbdd18437f3d04a838c4dfad0b5b5fb3f6cc2e3d53d29fcc21a22acc6648c  recommendation.py
0211b25081cc90f61d6497faf101fad42d5a92cd960f5463b2df1efb09f0df95  postgres_phase26_harness.py
b089ddf3fc37456041677d120348cb01e036897fbc57357f94dcb05888aeb9c8  postgres_phase27_2_harness.py
63ceecd685570e33bea9a8abf56a12d98f297f6859d9c45b247291889442b517  postgres_phase28_3_harness.py
9f6ba75d92ed043e2a67e0c83051770613f40ed40a2e0d8067401a46ad0bcb70  postgres_phase29_harness.py
ff15b1b1a6eee128154168a89c52422061a8ea0bc41ab6667bccf2719c758403  phase29_publication_evidence.py
a6c6cad4b1b0c029ba39eb91ea4cf7aae3ce2c111ac580643fd3a1b9faa3cffd  phase31_activation_preflight.py
080fe74e50bf84655d20b170363529f5a9ee69dad2a112ded48a5418ffa661dd  test_phase31_activation_preflight.py
```

## 32. Git hygiene

Final `git status --short` differs from entry only by this report within the
already-untracked `docs/transformation/` parent, so porcelain cannot list it as
a separate top-level entry. `git diff --check` reports only the known
pre-existing Sidebar line 28 trailing whitespace. A separate whitespace scan of
this report passes. No file was staged or committed.

## 33. External and zero effects

```text
database creation effects = 0
PostgreSQL effects = 0
production effects = 0
staging effects = 0
shared database effects = 0
Publication mutation effects = 0
Activation effects = 0
RuntimeAdoption effects = 0
runtime cutover effects = 0
normative effects = 0
automatic learning effects = 0
external business effects = 0
```

No teardown is claimed for resources that were never created.

## 34. P0, P1, and blocker count

```text
P0 violations caused by Phase 31.1 = 0
P1 procedural violations caused by Phase 31.1 = 1 (bounded parent-path metadata traversal; no sibling content read or changed)
retained-evidence blockers = 1
unexecuted PostgreSQL operational criteria = present; NOT EXECUTED
architectural observations = 1 (transitive retention closure)
```

The blocker remains `MISSING_RETAINED_PUBLICATION_CURATION_AUDIT`. It is not
downgraded by the valid `PUBLISHED=true` retained release-state result.

## 35. Residual risks

The Phase 29 Publication remains historically proven by its retained release
graph, but cannot be faithfully rematerialized under the frozen relational
contract. Attempting to continue would invite silent reconstruction or FK
weakening. No amount of repeated workspace searching can supply provenance
that was not retained. Only new authentic user-supplied pre-teardown evidence
could justify another forensic assessment. The next action is a governance
decision about the unavailable transitive dependency, not another search or
Activation attempt.

## 36. Final verdict

`PHASE 31.1 — NOT PROMOTED — AUTHENTIC RETAINED CURATION-AUDIT EVIDENCE NOT FOUND`

The missing curation audit remains unavailable. Phase 29 Publication remains
historically proven by its retained release graph, but the Publication cannot
yet be faithfully rematerialized under the frozen relational contract. Phase
31 Activation cannot proceed. No evidence was fabricated, no database was
created, no Activation occurred, and no RuntimeAdoption occurred.

## 37. NEXT_CODEX_PROMPT

Execute **PHASE 31.2 — UNAVAILABLE HISTORICAL TRANSITIVE DEPENDENCY GOVERNANCE
DECISION GATE — DESIGN ONLY** exclusively in
`/home/felipe/proyectos/isosmart`. Treat Phase 31.1 outcome
`AUTHENTIC COMPLETE RETAINED CURATION AUDIT NOT FOUND` as final unless the user
supplies new authentic pre-teardown evidence. Read `AGENTS.md`, the complete
Phase 25.1–31.1 lifecycle reports, ADR-0013–0015, governed-learning and
KnowledgeLayerRule application/publication/activation/runtime-adoption
policies, frozen migrations 0008 and 0021–0023, and the exact Phase 28.3/29
retained evidence. Decide, by append-only governance and without implementation,
how ISO Smart handles Publication `e97576de-d4ef-520d-8592-d376ed401221`
whose mandatory frozen FK dependency `normative.curation_audit.id =
12d811ab-c3b4-4615-8972-75008a36e327` was not retained. Evaluate explicit
options such as permanent non-rematerializability classification, continued
historical-verification-only treatment, or a future separately approved
superseding lifecycle experiment, and formalize a prospective
`TRANSITIVE RETENTION CLOSURE` rule for Publication, Activation, and
RuntimeAdoption teardown gates. Do not reconstruct or infer the missing row,
rerun Phase 29, retry the same forensic search without new evidence, alter the
Publication or historical manifests, relax/drop the FK, modify migrations
0001–0023, add migration 0024, create/import a database, activate, adopt at
runtime, change runtime/normative/learning behavior, access AdminApps or any
external/production/staging/shared system, or advance to Phase 32. Preserve
the lifecycle state `CREATED=true`, `APPLICATION_GOVERNED=true`,
`PUBLISHED=true`, `ACTIVATED=false`, `RUNTIME_ADOPTED=false`,
`RUNTIME_EFFECTIVE=false`, `database_reconstructed=false`. Produce one
append-only design-gate report, retain all historical evidence unchanged, and
fail closed if the governance treatment is not explicit and independently
authorized.
