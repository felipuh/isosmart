# ISO SMART AI — Phase 28 first KnowledgeLayerRule publication source/policy/operational-authorization design gate

- Date: 2026-09-03 (`America/Costa_Rica`)
- Workspace: `/home/felipe/proyectos/isosmart`
- Nature: source, policy, security and operational-authorization design gate only
- Database/publication/activation/adoption/runtime/deployment/external effects: **ZERO**
- Verdict: **PHASE 28 — NOT PROMOTED**

## 1. Verdict

**PHASE 28 — NOT PROMOTED.** Candidate A (`vN+1`) is governance-superseded by
the separately governed compensation. Candidate B (`vN+2`) is the truthful
final leaf in the disposed Phase 26 proof, but it is not an exactly identifiable,
retained publication target: its UUID, lineage UUID, complete material hash,
semantic fingerprint, governing IDs and Receipt are absent from retained
evidence. Its source reference also binds a synthetic Phase 9 StandardEdition
fixture (`source_hash = "3" * 64`) and locators `clause/A`/`clause/B`, not one of
the ten authoritative source artifacts.

The current Phase 27.2 native publication capability additionally lacks the
mandatory current-leaf, Phase 26 Receipt/governance-chain, source locator/hash,
Phase 26 fingerprint and actor-level application-executor separation checks.
There are unresolved P0 and P1 blockers. No Product Policy and no successor ADR
are created.

## 2. Entry baseline

Phase 26 is accepted as promoted for its isolated ephemeral mechanism. Phase 27
is not promoted. Phase 27.1 is promoted by design. Phase 27.2 is promoted only
as an inert foundation. Migrations 0001–0022 are frozen; 0023 is absent.

Entry `git status` was captured before change. The worktree was already
materially dirty, including unrelated backend/frontend/SQLite work and
untracked foundation/governance history. This gate changes only this report.

No Phase 26 database exists to inspect. The Phase 26 report records teardown of
container, volume and temporary directory after run
`20260903T003052Z_f66933`.

## 3. Phase 26 lineage

The primary harness constructs:

```text
vN   version=phase26-vN          status=published, runtime-selected
  -> vN+1 version=phase26-vN-plus-1 status=draft, published_at=NULL
    -> vN+2 version=phase26-vN-plus-2 status=draft, published_at=NULL
```

The no-child predecessor query proved `vN+2` was the unique leaf after
compensation. All IDs are generated at run time (`uuid4()` or `uuidv7()`), and
the report/output does not freeze them.

## 4. Compensation semantics

Answers to the mandatory questions:

- **A — yes.** Compensation applies `R2 -> R1`, explicitly reversing the only
  locator change introduced by the forward `R1 -> R2` correction.
- **B — yes.** Migration 0021 requires the compensation `new_source` to equal
  the forward Receipt's exact `source_reference_before`; the harness verifies
  `vN+2.source_reference == R1`.
- **C — yes within the disposed proof.** `vN+2` is the unique current governed
  leaf after the successful compensation.
- **D — yes.** Publishing `vN+1` after compensation would publish the exact
  locator state that the later independent Proposal/Review/Decision/
  Authorization/Receipt reversed.
- **E — yes.** It would make the retained statement that compensation restored
  `R1` misleading as publication intent.
- **F — no.** `vN+1` remains an immutable draft but is independently ineligible:
  it is non-leaf and governance-superseded.

Compensation is a new governed successor, not rollback, deletion or mutation.

## 5. Governance truth precedence

Chronology and predecessor semantics control, not version text or timestamps.
The later compensation chain establishes `R1` at `vN+2` as final governed
intent. Publication must not resurrect `R2` from `vN+1`. Therefore Candidate A
fails even if its row and locator were technically intact.

## 6. vN+1 candidate matrix

| Field | Directly established value | Eligibility consequence |
|---|---|---|
| Exact rule ID | **Not retained**; runtime-generated | FAIL |
| KnowledgeLayer ID | **Not retained**; selected by `.first()` | FAIL |
| Lineage ID | **Not retained** | FAIL |
| Revision/version | `phase26-vN-plus-1` | Informational only |
| Predecessor | exact runtime-generated `vN` ID, not retained | FAIL exactness |
| Target full-material hash | Receipt stored it, value not retained | FAIL |
| Semantic fingerprint | 64-char equality tested, value not retained | FAIL |
| Source before/after | `R1 -> R2`; `R1/R2` contain ephemeral edition UUID, hash `3` repeated 64 times, locators `clause/A -> clause/B` | FAIL authoritative provenance |
| Proposal / CanonicalDelta / Review / Decision / Authorization | separately created and checked; IDs/hashes not retained | FAIL exact chain |
| Application Receipt | exact row existed; ID and row not retained | FAIL |
| Event/audit | exact counts/links tested; IDs/payloads not retained | FAIL exactness |
| Publication / Activation / RuntimeAdoption | zero / zero / zero | Required inert state satisfied only in disposed proof |
| Compensation status | compensated by exact `vN+2` successor | FAIL superseded intent |
| Current lineage head | no | FAIL |
| Publication eligibility | **NOT ELIGIBLE** | stale, superseded non-leaf plus missing exact evidence/source validity |

## 7. vN+2 candidate matrix

| Field | Directly established value | Eligibility consequence |
|---|---|---|
| Exact rule ID | **Not retained**; runtime-generated | FAIL |
| KnowledgeLayer ID | **Not retained** | FAIL |
| Lineage ID | **Not retained** | FAIL |
| Revision/version | `phase26-vN-plus-2` | Informational only |
| Predecessor | exact runtime-generated `vN+1` ID, not retained | FAIL exactness |
| Target full-material hash | compensation Receipt stored it, value not retained | FAIL |
| Semantic fingerprint | equal to forward fingerprint in DB, value not retained | FAIL |
| Source before/after | `R2 -> R1`, restoring synthetic locator `clause/A` | FAIL authoritative provenance |
| Proposal C / CanonicalDelta C / Review C / Decision C / Authorization C | independent chain proved; exact IDs/hashes not retained | FAIL exact chain |
| Compensation Receipt | exact row linked forward Receipt; ID/row not retained | FAIL |
| Event/audit | count/link existence proved; IDs/payloads not retained | FAIL exactness |
| Publication / Activation / RuntimeAdoption | zero / zero / zero | Required inert state satisfied only in disposed proof |
| Current lineage head | yes in disposed Phase 26 proof | Truthful candidate class, but not an addressable retained candidate |
| Publication eligibility | **NOT ELIGIBLE** | exact identity/provenance/source and safe capability preconditions unresolved |

## 8. Current lineage head

Promoted lineage semantics define the head as the unique row for which no row
has `previous_revision_id = candidate.id`. Under that rule, the Phase 26 proof's
head after compensation was **vN+2**. No `MAX`, timestamp or version ordering is
used.

There is no current durable Phase 26 row to name or lock now. Therefore the
answer is: conceptual/test-evidence head = `vN+2`; exact retained current head =
**not available**. That distinction blocks publication authorization.

## 9. Semantic fingerprints

Phase 26 function `foundation_0021_rule_semantic_hash` includes:

```text
fingerprint_version, target_type, knowledge_layer_id, knowledge_layer_type,
standard_id, standard_edition_id, standard_edition_source_hash, lineage_id,
rule_key, logic_json, evidence_expectation, certifiability_classification,
source_reference_scheme
```

It excludes rule ID, version, predecessor, timestamps, status, `published_at`
and the locator component. The harness proved equality for `vN`, `vN+1` and
`vN+2`, but retained only “64 characters/equal,” not the exact digest.

Phase 27.2 `foundation_0022_rule_semantic_hash` is not the same contract: it
includes only `knowledge_layer_id`, `rule_key`, `logic_json`,
`evidence_expectation` and `certifiability_classification`. It omits the
fingerprint version, target type, layer type, standard/edition identity,
edition source hash, lineage and source-reference scheme. A future publication
cannot truthfully substitute this narrower digest for the missing Phase 26
fingerprint. Both candidates fail exact fingerprint proof.

## 10. Source-reference provenance

The harness directly constructs:

```text
R1 = iso-smart-source-ref-v1:<ephemeral edition UUID>:<64 x "3">:clause/A
R2 = iso-smart-source-ref-v1:<ephemeral edition UUID>:<64 x "3">:clause/B
```

The edition comes from the first `KnowledgeLayer` returned by an unordered
`.first()`. That layer was introduced by the Phase 9 synthetic fixture with
`source_hash="3" * 64` and explicit source text “NON-OFFICIAL TEST FIXTURE:
source placeholder only.” Phase 26 validates grammar, identical edition/hash,
published fixture edition and locator difference. It does not prove either
locator against an authoritative artifact.

Candidate A points to R2; Candidate B restores R1. Neither locator nor the
synthetic source hash appears in the ten authoritative source artifacts. No
licensed normative content is inferred.

## 11. Authoritative source validation

All ten artifact bytes match the promoted hashes and were inspected directly:
DOCX and XLSX ZIP/CRC checks pass; JSON parses; textual CSV, SQL, OpenAPI,
Mermaid, Draw.io and import guide are readable. Direct searches across text and
embedded Office XML find no `clause/A`, `clause/B`, Phase 26 rule key or
`333...333` source hash.

Thus artifact-set integrity is **10/10 PASS**, but candidate source-reference
validity is **FAIL**. File integrity cannot validate a reference to a different
synthetic fixture.

## 12. Governance chain

The forward and compensation chains were separate and structurally tested.
The forward chain began from one LearningSignal; compensation reused applicable
authorized provenance but created an independent Proposal, CanonicalDelta,
Review, Decision and Authorization and linked the forward Receipt.

The exact artifact IDs, proposal material hashes, selected review-set hashes,
delta hashes, authorization snapshots and traces are not in the report or any
retained manifest. Existence in a destroyed database is not an exact chain
available to a future transaction. Both candidates fail this gate.

## 13. Forward Receipt

The 0021 schema can freeze operation/version, delta hash, before/after IDs,
versions and hashes, predecessor, source references, semantic fingerprint,
actor, trace, governance links, event/outbox/audit and false publication,
runtime-effect and external-effect flags. Phase 26 tested those predicates.

The actual forward Receipt ID and row are not retained. A later reconstruction
from the harness or successor label is prohibited. Candidate A and every chain
depending on that Receipt fail exactness.

## 14. Compensation Receipt

The compensation Receipt was separately created and linked the forward Receipt;
it recorded `result_published=false`, `runtime_effect_changed=false`, restored
R1 and made `vN+2` non-compensable under that same receipt direction. Its exact
ID and immutable row are not retained. Candidate B fails exact Receipt proof.

## 15. Candidate eligibility comparison

| Gate | vN+1 | vN+2 |
|---|---:|---:|
| Truthful current leaf | FAIL | proved only in disposed DB |
| Not governance-superseded | FAIL | PASS semantically |
| Exact rule/lineage/predecessor/hash/fingerprint retained | FAIL | FAIL |
| Authoritative source locator/hash | FAIL | FAIL |
| Exact retained governance chain and Receipt | FAIL | FAIL |
| Unpublished/inactive/unadopted | proved in disposed DB | proved in disposed DB |
| Current capability enforces every publication precondition | FAIL | FAIL |
| Overall | **NOT ELIGIBLE** | **NOT ELIGIBLE** |

## 16. Selected candidate or no-selection

**No candidate is selected.** `vN+2` is the only semantically defensible lineage
position, but “semantically preferred” is not “publication eligible.” Mandatory
exact evidence and operational controls are missing. Ambiguity must fail closed.

## 17. Publication authority

Future authority must require a fresh server-resolved AdminApps decision for
identity, MFA, active access, global scope and exact
`qms.knowledge_layer_rule.publish` permission, plus a separate immutable
KnowledgeLayer curator approval. Client claims, tenant membership, proposer,
reviewer, approver, application authorizer, executor or Receipt alone cannot
authorize publication.

Current 0022 checks the publication LOGIN and authority session values, but its
native function creates the curation audit itself and accepts no independent
curator evidence. This is insufficient for this candidate class.

## 18. Separation of duties

Future same-chain constraints must compare immutable actor identities across
proposal creator, selected reviewers, approver, application authorizer,
application executor, curator and publisher. At minimum:

- publisher differs from the Phase 26 executor and curator for the revision;
- tenant authority cannot authorize a global publication;
- a technical principal cannot manufacture its own authority context; and
- role separation and actor separation are both enforced.

Migration 0022 separates database LOGIN capabilities, but native publication
does not load a governing Receipt and therefore cannot reject an actor who was
the application executor. FAIL.

## 19. Publication preconditions

The future command must revalidate under one lineage lock: exact rule ID,
lineage, predecessor, unique current leaf, material hash, Phase 26 fingerprint,
source reference and real source provenance, governing Receipt and complete
governance chain, policy, curator evidence, fresh publication authority,
capability fence, unpublished state, no intervening successor and no conflict.
Any mismatch fails closed.

The 0022 function checks only exact ID, draft state, absent timestamp, its own
material hash, no prior Publication and the capability/authority session. It
does not check child absence, Receipt, chain, source, independent curation or
Phase 26 fingerprint. FAIL.

## 20. Current-leaf requirement

**Required: YES.** There is no policy justification for publishing a
superseded non-leaf in the first POC. Convenience exceptions are prohibited.
The missing leaf check in 0022 is a P0 blocker because it would permit native
publication of `vN+1` even after `vN+2` exists.

## 21. Target hash

The exact candidate material hash must cover ID, KnowledgeLayer, lineage, rule
key, version, predecessor, logic, evidence expectation, full source reference
and classification using a named canonicalization. Migration 0022 computes
that shape, but the Phase 26 candidate values and digest are not retained.

## 22. Idempotency

Future identity must bind publication ID, candidate/lineage/predecessor,
material hash, Phase 26 fingerprint, governing Receipt, policy ID/version/hash,
curator evidence and authority provenance. Exact replay returns the same
Publication; any changed value conflicts.

Current 0022 operation material is only `rule_id:expected_hash:reason`; replay
does not compare Receipt, fingerprint, source, curator evidence, actor,
authority context or policy provenance. FAIL.

## 23. Concurrency

The future command must lock the lineage stream and use unique candidate plus
idempotency/material constraints. Concurrent attempts for the same exact leaf
yield one Publication and replay/conflict. A `vN+1`/`vN+2` race must serialize
on the same lineage and revalidate the unique leaf immediately before the
decision, making the stale attempt fail.

Existing uniqueness prevents two Publication rows for one exact rule, but it
does not arbitrate different revisions of one lineage and has no leaf check.
FAIL for the required different-revision race.

## 24. TOCTOU

Required order:

```text
claim -> authority -> capability -> lineage lock -> exact candidate/leaf ->
hash/fingerprint -> Receipt/governance -> source -> Publication + event/outbox/audit ->
authority/capability/hash/leaf recheck -> commit
```

0022 rechecks material hash and capability only. It does not recheck authority,
leaf, source, Receipt or governance immediately before commit. FAIL.

## 25. Atomicity

The 0022 foundation atomically persists claim, compatibility status,
Publication, curation row, event, outbox and audit or none. That mechanism is a
useful base. It still lacks the required evidence bindings; atomic persistence
of an incomplete decision graph cannot pass Phase 28.

## 26. Event contract

Future `knowledge_layer_rule.published` schema v1 must include bounded:
publication ID, exact rule/KnowledgeLayer/lineage/version/predecessor IDs,
material hash, Phase 26 fingerprint, source edition ID/hash and locator hash,
governing Receipt ID, policy ID/version/hash, curator evidence ID, authority
decision reference, trace, `activation_requested=false`,
`runtime_adoption_requested=false`, `runtime_effect_changed=false` and
`external_effects=false`.

It means publication governance completed only; never activated, adopted,
deployed, effective or successful learning. The current payload omits several
mandatory bindings.

## 27. Audit contract

Immutable audit must freeze the same exact candidate/hash/fingerprint/source,
Receipt, publisher/AdminApps provenance, curator evidence, policy, reason,
trace and timestamps. Store source locator itself only when allowed; otherwise
store its canonical hash plus the already canonical target reference. Never
copy raw licensed body, prompts, PII, credentials or secrets. Current 0022
audit does not freeze Receipt/source/fingerprint/curator bindings. FAIL.

## 28. No Activation proof

No publication was invoked. No database was opened. Publication row delta = 0;
Activation row delta = 0. Future publication must preserve Activation delta 0.

## 29. No RuntimeAdoption proof

No publication was invoked. RuntimeAdoption row delta = 0. Future publication
must preserve RuntimeAdoption delta 0 and must not emit or dispatch an adoption
command.

## 30. Runtime invariance

Runtime files remain byte-identical to the Phase 27.2 baseline:

- `agent_runtime.py`: `6767e2098365536b88d4d8e9afdaef0f8b796383c79d7f40e0e0ea91b964ec2d`
- `recommendation.py`: `655fbdd18437f3d04a838c4dfad0b5b5fb3f6cc2e3d53d29fcc21a22acc6648c`

They accept caller-supplied exact rule IDs and require `status=published`; they
do not import the Phase 27.2 resolver. Phase 28 makes no runtime change.

## 31. Legacy compatibility risk

Native publication necessarily changes legacy `status/published_at`. Current
Recommendation/AgentRun paths treat any caller-supplied exact published rule as
eligible without Activation or RuntimeAdoption. Although there is no automatic
latest lookup, an upstream caller could explicitly supply the newly published
candidate. Until runtime cutover, a publication POC must prove candidate IDs
cannot reach those caller inputs (isolated DB/roles and no runtime invocation),
or it is blocked. This remains a P0 operational isolation requirement.

## 32. Fallback-selector scan

The repository-wide code scan produced 1,104 broad textual matches; most are
unrelated uses of ordinary words. Relevant dispositions are:

| Path/function | Match | Disposition |
|---|---|---|
| `foundation/recommendation.py`, recommendation basis load | exact supplied rule ID + `status=published` | no latest fallback; legacy publication eligibility risk |
| `foundation/agent_runtime.py`, `start_agent_run` | exact supplied rule ID + `status=published` | no latest fallback; same risk |
| migration 0022 `resolve_knowledge_layer_rule_runtime_adoption_v1` | exact adoption ID join | safe and not wired to runtime |
| migration 0021 target/application functions | `NOT EXISTS(child)` | safe promoted leaf semantics |
| migration 0022 `foundation_0022_capability_enabled` | no-child capability-decision leaf | relevant only to fence history, not rule selection |
| migration 0022 `publish_knowledge_layer_rule_v1` | **no rule-child/current-leaf predicate** | unsafe stale-revision publication path |
| `postgres_phase26_harness.py` fixture selection | unordered `KnowledgeLayer.objects...first()` | not runtime selection, but unsafe/non-reproducible source provenance for publication eligibility |
| `leadership/views.py` line 915 and integration/authentication matches | unrelated application entities | not KnowledgeLayerRule resolution |

No latest/max/timestamp selector implicitly adopts a rule. The blocker is the
legacy exact-ID-plus-published contract and missing leaf/evidence gates.

## 33. Ambiguous COMMIT

Required outcomes remain `COMMITTED`, `NOT_COMMITTED`, `ABANDONED` and
`INCONSISTENT`. COMMITTED must prove claim, exact Publication, rule/hash/
fingerprint/source/Receipt/governance, event, outbox, audit, curator,
authority, policy and trace bidirectionally. Publication existence or status
alone is insufficient.

## 34. Reconciliation

Current 0022 reconciliation checks the core claim/artifact/event/outbox/audit
IDs, operation hash and trace. It does not rederive or compare the newly
required Receipt, governance, source, Phase 26 fingerprint and independent
curation bindings. NOT_COMMITTED is legal only with no durable evidence;
ABANDONED requires append-only disposition; every partial/mismatch is
INCONSISTENT. No automatic repair or reconstruction is allowed.

Known committed response loss returns the same artifact. Ambiguous COMMIT is
classified before any retry.

## 35. Capability fence

Publication requires the exact append-only `PUBLICATION` fence at admission
and precommit. Disabled means deny new publication only. Re-enable is a new
governed decision referencing the exact disable predecessor; direct update is
forbidden. Historical Publication, Activation, Adoption, rule lineage and
Receipts remain unchanged.

## 36. Least privilege

The future POC publisher must be a real LOGIN, NOSUPERUSER, NOINHERIT,
NOBYPASSRLS, non-owner, with no generic rule DML, Activation, Adoption,
learning-application or normative-curator capability. It receives EXECUTE only
on the exact corrected publication function. The 0022 role shape is suitable
as a base but cannot compensate for missing semantic/SOD checks.

## 37. SECURITY DEFINER design

Use a dedicated NOLOGIN/NOSUPERUSER/NOINHERIT/NOBYPASSRLS owner, fixed
`search_path=pg_catalog`, fully qualified objects, PUBLIC revoke and one exact
publisher grant. No dynamic target SQL, arbitrary status/field/value or generic
payload. Hostile `pg_temp,public` tests are mandatory. The typed function must
accept exact Receipt/curator/policy identities or derive them by immutable
candidate relation; it must never trust client-supplied assertions alone.

## 38. Repair boundary

Repair may inspect, reconcile, classify, append incident/disposition, disable
the exact capability and request governed recovery. It cannot publish, mutate
the candidate, manufacture Receipt/curation/authority, alter lineage, activate,
adopt or rewrite history. Partial evidence remains INCONSISTENT.

## 39. Retained history

After any future publication evidence exists, destructive downgrade may not
erase Publication, claim, event, outbox, audit, Receipt or governance chain.
Use expand/contract and forward fixes. Publication never creates compensation,
resumes old lineage or changes `vN+1`/`vN+2`.

## 40. Automatic-learning prohibition

Publication creates no LearningSignal, Proposal, confidence change, model or
policy update, AgentDefinition change, compensation, retrieval change,
autonomy change or external effect. Event consumers must not auto-trigger the
next stage.

## 41. Normative invariance

Future publication may not change Standard, StandardEdition, Clause,
RequirementControl, EvidenceCoverage or certifiability semantics.
KnowledgeLayerRule remains `non_certifiable_guidance`. The current Phase 26
fixture is explicitly non-official and is not evidence of normative truth.

## 42. Protected-target invariance

Phase 28 changes no runtime, schema, test, security, model, target, grant, role,
event implementation or executor. Current hashes match the Phase 27.2 protected
implementation baseline for models, KnowledgeLayer commands, application,
eventing, audit, Recommendation and AgentRun.

## 43. P0/P1 classification

Unresolved **P0** blockers:

1. Candidate A is governance-superseded; current native publication has no
   leaf check and could publish it.
2. Neither candidate has a retained exact ID/lineage/hash/fingerprint/Receipt/
   governance chain; reconstruction would falsify provenance.
3. Candidate references a synthetic source hash/locator not validated against
   the authoritative artifact set.
4. Publication recomputes a narrower 0022 semantic hash rather than binding the
   exact Phase 26 fingerprint.
5. Publication does not validate the application/compensation Receipt,
   governance chain or independent curator evidence.
6. Actor-level SOD does not prove the Phase 26 executor cannot publish.
7. Legacy `status=published` is still sufficient for explicitly supplied
   runtime rule IDs, requiring strict isolation for any future POC.

Unresolved **P1** blockers:

1. Publication idempotency/material identity omits Receipt, source,
   fingerprint, curator and authority/policy provenance.
2. Different-revision concurrency does not serialize/revalidate the rule
   lineage leaf.
3. Publication reconciliation/event/audit graphs omit the exact Phase 28
   evidence set and precommit revalidation is incomplete.

Promotion requires 0 P0 and 0 P1. Result: FAIL.

## 44. Product Policy if promoted

Not created. No revision is authorized for Phase 29.

## 45. ADR if justified

Not created. The governing architectural decision—current-leaf truth and
separate publication/activation/adoption—already exists in ADR-0013/0014. This
gate discovers evidence and implementation nonconformance; it does not approve
a new architecture.

## 46. Migration hashes

Migrations 0001–0022 are **22/22 MATCH** against the frozen promoted list:

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
0012 7f280e24a8e95858b8144aa6a85fc645aa2c2d3c2ad5700dfbe19ac0f0fdc
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

Migration 0023: **ABSENT**.

## 47. Source hashes

Authoritative sources are **10/10 MATCH**:

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

## 48. Governance hashes

```text
Phase 25.1 source-reference policy 1a5f7c7838c62ba76837c26fcfa4d29655294810f74afed33fdcf69dc373bb79
ADR-0013                        8fa5852a3cabf822c5213ae10bcae2a61f3910233ff1d915d4d1e1545df6a827
ADR-0014                        fa0e376e802f80e95d3961fabf8f6fe5e337f4b312062123ffd45c31bb300952
Governed-learning policy        7d9c2fe30548bd18d390d119889c87a93595ac281fa3326691fe486bee49c4ec
Implementation authorization    04458c4f1ccead125dd98ddac946ec9d77f8b0212412d13128355b10129c875c
Review/application boundary     2d5beaebd5b2df1378c0f425354b45d52ff23dd1a5d158adad46572f7656c514
Phase 27 design                 263003d342e6bf7a2b56c25dbbb230296b81280a1da45eb347b00898e3231e92
Phase 27.1 policy               efdd4d8a679c7f18762bfe79c3e876e970f81fedb2848ef5cbf21e7aeb858556
Phase 26 report                 ce36196c4094addba4fb31a512582a05af0113036c3894cb20eb938d1eefedd9
Phase 27 report                 3cc3418b48a0899cddc56636316a36cdabbd947d480e7d8e6b5f87d5863ed9e1
Phase 27.1 report               ca6bf1920200595c73dc2fb654cdce74098b1a4a329813eaf409b52b73d4e5f4
```

## 49. Git hygiene

Only this exact report is added by Phase 28. Pre-existing unrelated changes are
preserved. No frozen migration or existing governance/runtime/source artifact
is edited. Final validation must use scoped whitespace checks because the
repository already contains unrelated dirty files.

## 50. External effects

Zero. No publication function, database, network provider, AdminApps,
MedSupplier, object storage, notification, deployment, production, staging or
shared resource was used. Publication/Activation/RuntimeAdoption row deltas are
all zero by absence of any database operation. No candidate status or
`published_at` changed.

## 51. Residual blockers

The exact blocker is not “which revision number is newer.” Governance selects
`vN+2` over `vN+1`, but the selected class cannot be authorized because exact
candidate/provenance/source evidence was destroyed or never retained and the
current publication capability does not enforce the Phase 28 eligibility
contract. A blocker-closure phase must create a truthful, deterministic,
repository-retained candidate evidence manifest from an isolated synthetic
lineage tied to a declared source fixture, align the fingerprint contract, and
harden publication admission/reconciliation without publishing anything.

## 52. Final verdict

**PHASE 28 — NOT PROMOTED.** No candidate is authorized. `vN+1` is stale and
governance-superseded. `vN+2` represents the final compensated intent but lacks
the exact retained identity, provenance, authoritative source validation and
enforceable publication controls required for a future POC. No Product Policy,
ADR, publication, activation, adoption, runtime change, migration 0023,
deployment or external effect occurred.
