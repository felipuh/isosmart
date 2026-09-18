# ISO Smart AI — Phase 30 first KnowledgeLayerRule Activation source/policy and operational-authorization design gate

Design-only assessment date: 2026-09-03. Workspace: `/home/felipe/proyectos/isosmart`.

## 1. Verdict

PROMOTE. The exact retained Phase 29 Publication graph is complete, internally consistent, unchanged, and offline-verifiable. The new policy closes the operation-specific authority, separation-of-duties, first-predecessor, concurrency, TOCTOU, capability, atomic evidence, reconciliation, and zero-runtime-effect design requirements. Promotion is eligibility only; this phase performed no Activation.

## 2. Entry baseline

Verified entry state is `CREATED=true`, `APPLICATION_GOVERNED=true`, `PUBLISHED=true`, `ACTIVATED=false`, `RUNTIME_ADOPTED=false`, `RUNTIME_EFFECTIVE=false`, and `database_reconstructed=false`. Phase 29 created one ephemeral synthetic Publication and retained its evidence before complete teardown. The entry worktree was already dirty with user changes; those changes were treated as immutable context.

## 3. Frozen hashes

Direct SHA-256 comparison found: migrations 0001–0023 `23/23 MATCH`; sources `10/10 MATCH`; ADR-0013–0015 `3/3 MATCH`; governed-learning and KnowledgeLayerRule policies `MATCH`; Phase 25.1–29 reports `MATCH`; Phase 28.3 and Phase 29 evidence files and embedded canonical material hashes `MATCH`; protected application/runtime files `MATCH`. Migration 0024 is absent. Sections 43–46 record the inventories.

## 4. Exact retained candidate

The only candidate considered is:

- ID `01a0682b-dfc8-7b49-a601-f9bda29a70a5`;
- lineage and rule predecessor `da72872a-3f3c-5fcd-86f7-0ed33e453522`;
- version `sN+1`;
- full material hash `caa24592b509334af4cd60fd7d3f3c43989d864d3f1c6e6d0d3bf83a81871f81`;
- semantic fingerprint `8465956c1daf27a9838bc1bfb468af3f518ae255b4662b2df40e7b8648516192`;
- lifecycle hash `0adfd8075cc720140c6e1f0393d286799edac8f352efd9f1969816be83c51e52`.

No alternative candidate, inferred head, status-only match, or version-only match is eligible.

## 5. Exact retained Publication

The required Publication is `e97576de-d4ef-520d-8592-d376ed401221`, with claim `e97576de-d4ef-520d-8592-d376ed401221`, event `b19e4861-219d-4a07-8faf-656e02dbf9b4`, Outbox `4e78cfe6-8afa-400b-85f5-e5fe72b59e04`, Audit `6a3ed87d-a992-4406-8ac8-233017301d35`, and trace `ffd16da6-94a4-588d-b922-2fefd9bd8a01`. Its manifest material hash is `51f0b207c790e6ab0c3d67985e161ba0d0cc7b2feb888f545c1ff5eedacf5366`; disposition material hash is `fff3b225184282e48dad30f4e56b16444df4241b5f647f2f3750ee4a254158f1`.

## 6. Publication evidence verification

The retained verifier passed and returned the exact offline state in section 2. The focused Django evidence/release suite passed `27/27`; its system check reported no issues. Direct JSON inspection matched candidate, lineage, predecessor, version, all three candidate hashes, source manifest, Phase 28.3 creation manifest/disposition, application Receipt `01a0682b-dfa3-779c-89cd-1814e9209527`, curator evidence `471971df-986f-5a99-ad15-1838f5772e34`, Publication graph, fresh publisher authority, policy, idempotency, and teardown disposition. The evidence is retained, not reconstructed.

## 7. Source provenance

The exact source is deterministic synthetic fixture ID `6ec35e4a-bb8a-592b-bc6a-420691f4e8e3`, manifest schema `synthetic-knowledge-layer-rule-publication-source-manifest/v1`, canonical material hash `cf92c267439f94f302e67888665dbf99392592341a808f5fc00f4c32ef23dc24`, source material hash `efe61114215914ac486011e4efd9977b4fa2f1c34fa6fad67012a46ced85ab4f`, scheme `iso-smart-synthetic-poc-source-ref-v1`, and exact locator hash `0ad437944a111b3593ba29f52466416eed9b4f0b8e7e9247c082575df0d659b6`. It remains non-authoritative, non-normative, non-licensed, test-only, non-production, with `phase26_continuity_claim=false`. The manifest never becomes activation authority; the independent Product Policy alone authorizes the narrow future experiment.

## 8. Material invariance

Activation is append-only governance evidence. It may not alter the rule body, source reference, logic, evidence expectation, certifiability, lineage, rule predecessor, semantic fingerprint, full material hash, or lifecycle hash. The future transaction must compare the locked candidate against all frozen values at admission and precommit; any difference is a full rollback.

## 9. Lifecycle semantics

The preserved lifecycle is `VERSION_CREATED → VERSION_PUBLISHED → VERSION_ACTIVATED → RUNTIME_ADOPTED`. Phase 30 remains at `VERSION_PUBLISHED`. A successful Phase 31 POC would establish only `PUBLISHED=true`, `ACTIVATED=true`, `RUNTIME_ADOPTED=false`, `RUNTIME_EFFECTIVE=false`.

## 10. Activation authority

Phase 31 must resolve a fresh AdminApps decision for exact human actor `49132b9d-93ae-510a-8de0-ad36ef508f8f`. Required material is active access, verified MFA, global scope, exact permission `qms.knowledge_layer_rule.activate`, decision ID/version/hash, evaluation and expiry timestamps, `server_resolved=true`, and exact activation policy identity/version/file hash. Client-supplied, expired, cached-only, missing, or mismatched claims deny. Authority must be re-resolved/revalidated immediately before commit.

## 11. Actor SOD

The exact activator is distinct from proposer `24d89409-dbb2-5771-9296-166afd4039b6`, reviewer `f8853b40-ef90-53b4-bd1b-17f85bcd5d79`, proposal approver `02d02d75-1d97-5dc3-b494-50e83335492e`, application authorizer `b71e6996-1e15-5aef-b73b-db331b01305f`, application executor `d91b730d-5d5b-5a64-a25c-a0318385a6eb`, curator `1dab9ba5-5c8a-504c-81b8-0ac70f15af14`, publisher, adopter, and any repair authority. A collision denies before evidence creation and at precommit.

## 12. Publisher/activator separation

Phase 29 publisher `8069fbeb-0ef6-582c-8f3b-ff88e606c869` is prohibited as activator. Publishing supplies evidence but no Activation permission or approval. The retained publisher decision is historical provenance and cannot be reused as activation authority.

## 13. Activator/adopter separation

Activator `49132b9d-93ae-510a-8de0-ad36ef508f8f` is distinct from retained future-adopter role actor `0757c393-8c83-52be-ae2a-25385901f232`. Activation grants no adoption permission and produces no authority decision usable by a RuntimeAdoption boundary.

## 14. First Activation predecessor semantics

The expected predecessor Activation is explicitly `NULL`, meaning the first Activation in lineage `da72872a-3f3c-5fcd-86f7-0ed33e453522`. It is a typed expectation, not omission or inference. Migration 0022 already models an append-only activation table and a null-safe unique predecessor slot; its activation function denies a `NULL` predecessor when any activation already exists in the lineage. Phase 29 evidence proves the retained Activation count is zero. Phase 31 must lock the lineage and re-prove zero before insert.

## 15. Activation lineage

Rule lineage and Activation lineage are independent. The rule predecessor does not become the Activation predecessor. The first Activation has explicit predecessor `NULL`; any later Activation must reference the exact previous Activation and win a single unique successor slot. Recovery appends another transition; it does not modify earlier history.

## 16. No mutable pointer

No `current_activation_id`, `active_rule_id`, `current_rule`, `latest_active_rule`, or semantic equivalent is authorized. The repository/schema scan found no hidden mutable runtime pointer introduced by the release foundation. Only an exact future RuntimeAdoption artifact may select runtime material.

## 17. Idempotency

Canonical operation material binds Activation ID; candidate and Publication; candidate, retained-evidence, source, policy, authority, and capability hashes; explicit predecessor `NULL`; actor; idempotency-key hash; trace; operation/canonicalization versions; and deterministic evidence IDs. Same key plus identical material returns the same artifact or waits for it. Any changed field using the same key or artifact ID is a conflict. Timeout never permits claim theft.

## 18. Concurrency

Phase 31 acceptance requires: identical concurrent requests produce one Activation plus one replay/waiter; changed material produces one winner plus one conflict; a different Publication competing for the same predecessor is stale/conflict; capability disable racing commit causes precommit denial; authority revocation racing commit causes precommit denial. The null-safe predecessor constraint plus fixed locks must prove no root or successor fork.

## 19. Lock order

All writers acquire: (1) exact idempotency/claim identity; (2) exact Activation lineage/predecessor slot; (3) exact Publication and retained evidence identity; (4) exact candidate; (5) exact authority decision; (6) exact capability leaf; (7) deterministic event/Outbox/Audit stream identities. The ordering is global and monotonic; callers never hold a later lock while seeking an earlier one. This serializes contenders and prevents circular wait between claim, lineage, evidence, and governance writers.

## 20. TOCTOU

Immediately before commit, Phase 31 revalidates candidate ID and three hashes; exact Publication and manifest/disposition hashes; Publication validity; source provenance; explicit predecessor and no competing successor; fresh authority/MFA/access/permission/global scope; all SOD rules; policy identity/version/hash; capability leaf; canonical idempotency material; and zero RuntimeAdoption for the new Activation. Any drift raises an error inside the transaction.

## 21. Capability fence

Activation capability is independent from learning application, Publication, RuntimeAdoption, repair, and capability control. The exact append-only decision is checked at admission and precommit. Disabled means deny; a later re-enable requires a new decision referencing the exact predecessor decision. Neither transition changes historical Activation or runtime state.

## 22. Event contract

The only event is `knowledge_layer_rule.activation_recorded`, schema `v1`. It means solely that the exact published revision passed Activation governance. Its payload freezes Activation/predecessor, Publication, candidate/lineage/version/three hashes, source manifest/material/reference hashes, actor, authority decision ID/version/hash, policy ID/version/file hash, capability decision ID/version/hash/state, trace, and recorded timestamp. It contains no licensed content or secret and asserts no adoption, effectiveness, deployment, learning success, or certification.

## 23. Audit contract

The immutable Audit freezes the exact candidate, Publication, Activation, predecessor `NULL`, actor/authority, policy, capability, all operation/evidence hashes, trace, and timestamp. It is append-only, payload-hashed, and cross-linked to the claim/event/Outbox. It records no target-body mutation and is never rewritten.

## 24. Atomicity

One PostgreSQL transaction persists claim + Activation + activation event + TransactionalOutbox + immutable Audit. The rule and Publication are locked/read only. The transaction creates no RuntimeAdoption and invokes no resolver. A missing member means the operation is not `COMMITTED`.

## 25. Rollback design

Failure injection points are: claim; authority validation; capability admission; predecessor lock; Publication validation; candidate validation; Activation insert; event; Outbox; Audit; immediately before commit. At every point the asserted post-failure deltas are Activation `0`, event `0`, Outbox `0`, Audit `0`, RuntimeAdoption `0`, and runtime `0`.

## 26. Ambiguous COMMIT

The only outcomes are `COMMITTED`, `NOT_COMMITTED`, `ABANDONED`, and `INCONSISTENT`. A lost response triggers exact graph reconciliation, not a blind retry and never an inference from `status=published`, `published_at`, or Publication presence.

## 27. Reconciliation

`COMMITTED` requires a mutually matching claim → Activation → exact Publication → candidate/hash graph plus event, Outbox, Audit, authority, policy, capability, and trace. `NOT_COMMITTED` requires absence of every durable Activation-operation artifact. `ABANDONED` requires an explicit append-only authorized disposition; timeout alone is insufficient. Any partial or mismatched graph—including wrong Publication/candidate/authority/predecessor—is `INCONSISTENT` and fails closed. No automatic repair or evidence fabrication is allowed.

## 28. Recovery

Governed reversal/change appends a later Activation referencing the exact current Activation predecessor and another exact published revision. It never updates/deletes an Activation or rewinds a pointer. History remains intact, and runtime remains unchanged until a separately authorized exact RuntimeAdoption exists.

## 29. Capability disable/re-enable

Disablement blocks only new Activations. It does not deactivate history, unpublish the candidate, alter RuntimeAdoption/runtime, or rewrite evidence. Re-enable is an append-only successor decision after independent authorization and does not retroactively validate a denied operation.

## 30. Repair authority

Repair may inspect, reconcile, classify, append an incident/operator disposition, disable the exact capability, and request governed recovery. It may not activate, publish, adopt, mutate the rule, rewrite event/audit, change lineage, create target revisions, fabricate missing graph members, or grant itself privilege.

## 31. Least privilege

The future activator role is LOGIN, non-superuser, `NOINHERIT`, `NOBYPASSRLS`, non-owner, without generic rule/table DML, schema CREATE, role escalation, Publication, RuntimeAdoption, learning application, repair, or control authority. Its sole positive grant is EXECUTE on the exact Activation boundary required by the ephemeral POC.

## 32. SECURITY DEFINER

If used, the owner is dedicated NOLOGIN, non-superuser, `NOINHERIT`, `NOBYPASSRLS`, and not a table owner. The function has a fixed `pg_catalog`-safe search path, fully qualified objects, PUBLIC EXECUTE revoked, activator-only EXECUTE, no dynamic SQL, and no arbitrary target, Publication, status, or state selector. The exact candidate/Publication are policy-bound and server-validated.

## 33. Hostile matrix

Phase 31 must deny: PUBLIC; publisher; application executor; curator; adopter; worker/projector; repair; spoofed actor; spoofed MFA; spoofed global scope; stale authority; revoked authority; wrong candidate; wrong Publication; wrong full/semantic/lifecycle/source/evidence/policy hash; wrong predecessor; disabled capability; hostile search path; latest/current/version/timestamp selectors; direct DML; and claim theft. Every denial must leave the six rollback deltas at zero.

## 34. Retained Activation evidence design

Before teardown, export `governed-target-activation-evidence-manifest/v1`. It must contain complete Phase 28.3 candidate and Phase 29 Publication evidence; Activation ID and predecessor `NULL`; candidate/Publication and all hashes; source provenance; fresh authority; activation policy; capability; event; Outbox; Audit; trace; Activation timestamp; `RuntimeAdoption count=0`; `runtime_effect_changed=false`; schema/canonicalization versions; and canonical manifest material hash. Append a separately hashed teardown disposition with absence proofs.

## 35. Offline Activation query

The retained verifier must answer, without database reconstruction: `CREATED=true`, `APPLICATION_GOVERNED=true`, `PUBLISHED=true`, `ACTIVATED=true`, `RUNTIME_ADOPTED=false`, `RUNTIME_EFFECTIVE=false`, and `database_reconstructed=false`. An incomplete or noncanonical manifest cannot answer affirmatively.

## 36. Zero RuntimeAdoption proof

Activation success requires pre/post snapshots showing RuntimeAdoption row and event deltas of zero, no adoption Outbox/Audit, no adoption authority use, no resolver invocation, and no exact adoption ID for the Activation. Teardown evidence retains the zero count. Phase 30 itself retained `ACTIVATED=false` and `RUNTIME_ADOPTED=false`.

## 37. Runtime invariance

`agent_runtime.py` and `recommendation.py` match their frozen hashes. Their behavior is not wired to Publication or Activation. Phase 31 must hash these and runtime configuration before/after, prove no exact RuntimeAdoption exists, and show AgentRun/Recommendation protected-state digests unchanged. Therefore Activation alone remains `RUNTIME_EFFECTIVE=false`.

## 38. Selector/fallback scan

The scan covered latest/current/head/leaf, maximum version/revision, newest activation/publication, and descending-time patterns. Relevant hits are governance-time stale-target/leaf proofs and test harness assertions, not runtime selectors. `InertRuntimeAdoptionResolver.resolve` accepts only an exact RuntimeAdoption ID; release tests explicitly reject omitted, `current`, `latest`, version, rule, layer, and timestamp substitutes. AgentRun and Recommendation contain no implicit KnowledgeLayerRule Activation/Adoption selection. One unrelated `leadership/views.py` descending version lookup selects a tenant-domain strategic-network projection, not KnowledgeLayerRule release/runtime material. P0 selector blockers: zero.

## 39. Automatic-learning invariance

The future Activation boundary may create no LearningSignal, LearningProposal, canonical delta, review, decision, learning application/Receipt, confidence update, compensation, ModelPolicy/AgentDefinition update, or autonomy change. Phase 31 snapshots these protected tables and requires zero deltas. Activation is release governance only.

## 40. Normative invariance

Standard, StandardEdition, Clause, RequirementControl, KnowledgeLayerRule material, bindings, evidence coverage, and certifiability remain unchanged. The candidate remains synthetic non-certifiable guidance and cannot become authoritative or licensed through Activation.

## 41. Effectiveness/release governance

The existing policies separate effectiveness, Publication, Activation, and RuntimeAdoption. They do not require a new `EffectivenessCheck` before recording Activation, so Phase 30 does not invent one. The existing activation contract carries a compatibility assessment/hash; Phase 31 may freeze a POC-specific release-compatibility hash, but it is evidence rather than authority and cannot trigger Activation or adoption automatically. Any future runtime effectiveness assessment remains independent and post-adoption by separately approved policy.

## 42. Product Policy if promoted

Created `docs/governance/FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_ACTIVATION_POC_POLICY_V1.md`, status exactly `APPROVED FOR FUTURE EPHEMERAL ACTIVATION POC ONLY`, identity `first-retained-synthetic-klr-activation-poc-policy/v1`, version `v1`, file SHA-256 `43c67505ec3e3d9df0d306012e2036ced7cf437de703e8ff95b709a7af08756d`. It authorizes only Phase 31 eligibility for the exact candidate/Publication and performs no activation.

## 43. Migration hashes

All frozen migration files match:

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
0023 bb9889af836ae1e92ccf75b868c4c6a8c1ab9ba1e7d63464a2cbd749a872e642
0024 ABSENT
```

## 44. Source hashes

Direct reads/parses and hashes passed `10/10`:

```text
DOCX     8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c
Drawio   e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa
Mermaid  11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3
XLSX     952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5
JSON     c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb
SQL      de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e
Nodes    ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3
Edges    30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6
OpenAPI  29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8
LEEME    eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db
```

## 45. Governance hashes

Core policy and ADR SHA-256 values match:

```text
GOVERNED_LEARNING_POLICY_V1                                    7d9c2fe30548bd18d390d119889c87a93595ac281fa3326691fe486bee49c4ec
GOVERNED_LEARNING_IMPLEMENTATION_AUTHORIZATION_V1               04458c4f1ccead125dd98ddac946ec9d77f8b0212412d13128355b10129c875c
GOVERNED_LEARNING_PROPOSAL_REVIEW_APPLICATION_BOUNDARY_V1       2d5beaebd5b2df1378c0f425354b45d52ff23dd1a5d158adad46572f7656c514
KNOWLEDGE_LAYER_RULE_GOVERNED_SOURCE_REFERENCE_APPLICATION_V1   1a5f7c7838c62ba76837c26fcfa4d29655294810f74afed33fdcf69dc373bb79
KNOWLEDGE_LAYER_RULE_PUBLICATION_ACTIVATION_RUNTIME_ADOPTION_V1 efdd4d8a679c7f18762bfe79c3e876e970f81fedb2848ef5cbf21e7aeb858556
KNOWLEDGE_LAYER_RULE_RUNTIME_ADOPTION_AND_REPAIR_V1              263003d342e6bf7a2b56c25dbbb230296b81280a1da45eb347b00898e3231e92
Phase 28.3 candidate Product Policy                            1d6352eaac748fff42098242b39db63e5f446140cfc935e961eb078d40010ed8
Phase 29 publication Product Policy                           0dfa36804827f272ac7e289beab6e876d27af78b8ae06d3b8a5b5d46b9db8289
ADR-0013                                                     8fa5852a3cabf822c5213ae10bcae2a61f3910233ff1d915d4d1e1545df6a827
ADR-0014                                                     fa0e376e802f80e95d3961fabf8f6fe5e337f4b312062123ffd45c31bb300952
ADR-0015                                                     57da49dff842349af8a7f3720595d858e96742d782bfe414174f84b8a1f3efea
```

Historical report file hashes also match: Phase 25.1 `f0fd1e6f142c8fa0b84febff197e80da8af310ccf90e8891e77b1b1d9bbb1ad1`; Phase 26 `ce36196c4094addba4fb31a512582a05af0113036c3894cb20eb938d1eefedd9`; Phase 27 `3cc3418b48a0899cddc56636316a36cdabbd947d480e7d8e6b5f87d5863ed9e1`; Phase 27.1 `ca6bf1920200595c73dc2fb654cdce74098b1a4a329813eaf409b52b73d4e5f4`; Phase 27.2 `2194fc994417c9339bf8788d3b300f1c7010f4013cc3b322c9db0db2b99d6fb8`; Phase 28 `bbd5ba9edf897e82da0283bd4acd5202586d503ee60852ee170d716b19661dc1`; Phase 28.1 `e8bdfcdbcbc07efc6e2f7ac473691ad07789cb467fc099be1c71174325b87afd`; Phase 28.2 `1d73b7e80a5b85730bbcfab1b6af6eb7f3689207b0161fa46f83aff3115118c0`; Phase 28.3 `d7a35171c86887f322a4fa1bcf3a2de9d0ef36069fb0318792213a6afdc0670d`; Phase 29 `150285ede077ed0bb6ca3dad403a88c0a40363629d3ecdd42460f0180ce0a7df`.

Evidence file SHA-256 values are: synthetic source manifest `6172874247eaa53d374e687073052c7e9ad8f333bfa94b135234bb8d2e02a600`; Phase 28.3 manifest `9272458cf9dc54f4f722b02502e5e85e9869cebb5e488f0ff15da82e77c07edd`; Phase 28.3 disposition `b8a7c9d5a5e423e03c25819d8715e00913edfabdeef57c6611a4906849c34536`; Phase 29 manifest `fade372ec41dbeff118ddbb41cd154f8e8adb34799492a56f5e8d14db7e54b72`; Phase 29 disposition `57633c70e0d66e2f1a7efbec0f06947cabadc1d4e0f117ca1f0dc4c305dbae9f`. Embedded canonical hashes were independently verified and intentionally differ from file-byte hashes.

## 46. Runtime hashes

Protected hashes match:

```text
models.py                         9dd94c945dd0c256c3872e82b45760b06c066a4364e3dc3d833d56c09645c244
governed_learning_application.py 99d228984efe4bba15c76f91e157f2ddd66d8aec9b5bf153a21c095fd57ed8cf
knowledge_rule_release.py         a7b0477f48120b852d9ec510d30e85d4700f5c0ba970e3ed3c9e244b1be4d7e9
eventing.py                       c7620cdfb0b51a0c1e022358dcbdae8a7e56b363e182dc09aa11ec675ecf95b8
audit.py                          461459401abb354b22c42eec05dcd9805e4fd7800554c67b96aee8885c6734ef
agent_runtime.py                  6767e2098365536b88d4d8e9afdaef0f8b796383c79d7f40e0e0ea91b964ec2d
recommendation.py                 655fbdd18437f3d04a838c4dfad0b5b5fb3f6cc2e3d53d29fcc21a22acc6648c
postgres_phase26_harness.py       0211b25081cc90f61d6497faf101fad42d5a92cd960f5463b2df1efb09f0df95
postgres_phase27_2_harness.py     b089ddf3fc37456041677d120348cb01e036897fbc57357f94dcb05888aeb9c8
```

No protected file was edited.

## 47. Git hygiene

`git status --short` was captured before edits. Existing modified/untracked user work was preserved, including the known whitespace at `frontend/src/components/Layout/Sidebar.jsx:28`. Phase 30 adds exactly this report and the policy in section 42. It modifies no migration, application/runtime source, manifest, evidence, historical report/policy/ADR, or authoritative source artifact.

## 48. Zero-effect assertions

Phase 30 result: Activation delta `0`; RuntimeAdoption delta `0`; runtime behavior delta `0`; KnowledgeLayerRule delta `0`; Publication delta `0`; normative delta `0`; automatic-learning delta `0`; external business effects `0`. No database was created/imported/reconstructed, no capability granted, no deployment performed, and no external service invoked.

## 49. P0/P1 count

P0 = `0`. P1 = `0`. The exact policy resolves all listed design risks; Phase 31 must prove them operationally in an isolated ephemeral database before any broader decision.

## 50. Residual blockers

None for the narrowly bounded future ephemeral POC. This is not evidence that Activation has occurred or that production/runtime use is safe. Phase 31 remains blocked unless it can obtain the fresh exact AdminApps activation authority and independently prove every test and teardown condition in the prompt below; failure at runtime is a Phase 31 fail-closed result, not permission to relax policy.

## 51. Final verdict

**PHASE 30 — PROMOTED FOR FUTURE EPHEMERAL ACTIVATION POC OF EXACTLY ONE RETAINED PUBLISHED SYNTHETIC CANDIDATE**

## 52. Exactly one NEXT_CODEX_PROMPT

```text
NEXT_CODEX_PROMPT

ISO SMART AI — PHASE 31 — FIRST RETAINED SYNTHETIC KNOWLEDGE LAYER RULE ACTIVATION — EPHEMERAL POSTGRESQL 18.6 POC

Work only in /home/felipe/proyectos/isosmart. Preserve unrelated user work and the known whitespace at frontend/src/components/Layout/Sidebar.jsx:28. Read AGENTS.md, the Phase 25.1–30 reports, ADR-0013–0015, all governed-learning/KnowledgeLayerRule release policies, the Phase 28.3 candidate policy, Phase 29 publication policy, and FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_ACTIVATION_POC_POLICY_V1.md completely. Read migrations 0021–0023, Phase 26/27.2/28.3/29 harnesses, release/evidence services, models, eventing, audit, RLS/threat/migration designs, AgentRun, Recommendation, and all retained Phase 28.3/29 evidence directly. Run git status before editing. Treat migrations 0001–0023 and all historical sources/evidence/policies/reports/runtime files as byte-frozen; migration 0024 must remain absent unless a separately explicit instruction authorizes it.

Objective: in one new isolated, disposable PostgreSQL 18.6 environment, record exactly one first Activation for candidate 01a0682b-dfc8-7b49-a601-f9bda29a70a5 through exact Publication e97576de-d4ef-520d-8592-d376ed401221, retain canonical Activation evidence, tear the environment down, and verify the result offline. Do not consider any other candidate or Publication. Do not create RuntimeAdoption, runtime wiring/cutover, production/staging/deployment effects, automatic learning, normative changes, or external business effects.

Freeze and verify before import: lineage/rule predecessor da72872a-3f3c-5fcd-86f7-0ed33e453522; version sN+1; full hash caa24592b509334af4cd60fd7d3f3c43989d864d3f1c6e6d0d3bf83a81871f81; semantic fingerprint 8465956c1daf27a9838bc1bfb468af3f518ae255b4662b2df40e7b8648516192; lifecycle hash 0adfd8075cc720140c6e1f0393d286799edac8f352efd9f1969816be83c51e52; Publication event b19e4861-219d-4a07-8faf-656e02dbf9b4; Outbox 4e78cfe6-8afa-400b-85f5-e5fe72b59e04; Audit 6a3ed87d-a992-4406-8ac8-233017301d35; Publication manifest material hash 51f0b207c790e6ab0c3d67985e161ba0d0cc7b2feb888f545c1ff5eedacf5366; disposition material hash fff3b225184282e48dad30f4e56b16444df4241b5f647f2f3750ee4a254158f1. Verify the entire retained candidate/application/curator/Publication/authority/policy/idempotency/disposition graph and reject reconstruction or substitution.

Retain source classification exactly: synthetic manifest ID 6ec35e4a-bb8a-592b-bc6a-420691f4e8e3; canonical hash cf92c267439f94f302e67888665dbf99392592341a808f5fc00f4c32ef23dc24; material hash efe61114215914ac486011e4efd9977b4fa2f1c34fa6fad67012a46ced85ab4f; source scheme iso-smart-synthetic-poc-source-ref-v1; locator hash 0ad437944a111b3593ba29f52466416eed9b4f0b8e7e9247c082575df0d659b6; non-authoritative, non-normative, non-licensed, test-only, non-production, no Phase 26 continuity claim. Never treat source or status=published as authority.

Use policy first-retained-synthetic-klr-activation-poc-policy/v1, version v1, file SHA-256 43c67505ec3e3d9df0d306012e2036ced7cf437de703e8ff95b709a7af08756d. Obtain a fresh server-resolved AdminApps decision for exact human activator 49132b9d-93ae-510a-8de0-ad36ef508f8f proving active access, MFA, global scope, qms.knowledge_layer_rule.activate, decision ID/version/hash, evaluation/expiry, and policy binding. Revalidate precommit. Deny client-supplied/stale/revoked authority. Enforce activator distinct from publisher 8069fbeb-0ef6-582c-8f3b-ff88e606c869, proposer 24d89409-dbb2-5771-9296-166afd4039b6, reviewer f8853b40-ef90-53b4-bd1b-17f85bcd5d79, approver 02d02d75-1d97-5dc3-b494-50e83335492e, authorizer b71e6996-1e15-5aef-b73b-db331b01305f, executor d91b730d-5d5b-5a64-a25c-a0318385a6eb, curator 1dab9ba5-5c8a-504c-81b8-0ac70f15af14, adopter 0757c393-8c83-52be-ae2a-25385901f232, and repair authority.

Expected Activation predecessor is explicitly NULL and means first Activation in the exact lineage. Lock and prove zero existing Activations. Keep rule and Activation lineages separate; use null-safe uniqueness so no root/successor fork exists. Create no mutable current/latest/active pointer. Canonical idempotency material must bind Activation ID, candidate/Publication/evidence/source hashes, explicit predecessor, actor/fresh authority, policy, exact capability decision, idempotency key, trace, operation versions, and deterministic evidence IDs. Identical concurrent material yields one Activation plus one replay/waiter; changed material yields winner/conflict; different Publication on the same predecessor is stale/conflict; disable and revocation races deny at precommit.

Use one global lock order: claim; Activation lineage/predecessor; exact Publication/evidence; exact candidate; authority; Activation capability; deterministic event/Outbox/Audit streams. Check the independent append-only Activation capability at admission and precommit. Prove disable/re-enable history, with disable affecting only new operations. Immediately precommit revalidate every identity/hash, Publication validity, source, predecessor/no competitor, authority/SOD, policy, capability, idempotency material, and zero RuntimeAdoption for the new Activation.

In one transaction persist claim + Activation + knowledge_layer_rule.activation_recorded schema v1 + TransactionalOutbox + immutable Audit. Event/Audit must freeze the exact Activation/predecessor/Publication/candidate/lineage/version/hashes/source/actor/authority/policy/capability/trace/timestamp, contain no licensed content or secrets, and assert no adoption/effectiveness/deployment/certification. Never mutate the rule or Publication. Inject failures at claim, authority validation, capability admission, predecessor lock, Publication validation, candidate validation, Activation insert, event, Outbox, Audit, and precommit; each must leave Activation/event/Outbox/Audit/RuntimeAdoption/runtime deltas zero.

Reconcile ambiguous commit only as COMMITTED, NOT_COMMITTED, ABANDONED, or INCONSISTENT. COMMITTED requires the complete matching graph; NOT_COMMITTED requires total durable absence; ABANDONED requires an explicit append-only disposition and never claim theft; partial/mismatched evidence is INCONSISTENT. Repair can inspect/classify/append disposition/disable/request recovery only and cannot fabricate, activate, publish, adopt, mutate, rewrite, change lineage, or escalate.

Use least privilege: activator LOGIN, non-superuser, NOINHERIT, NOBYPASSRLS, non-owner, no generic DML/schema creation/role escalation or other lifecycle authority, exact Activation EXECUTE only. If SECURITY DEFINER is used, give it a dedicated NOLOGIN non-superuser NOINHERIT NOBYPASSRLS non-table-owner; fixed safe search_path, qualified objects, PUBLIC revoked, no dynamic SQL or arbitrary selector. Test denials for PUBLIC, publisher, executor, curator, adopter, worker/projector, repair, spoofed actor/MFA/scope, stale/revoked authority, wrong candidate/Publication/hash/predecessor, disabled capability, hostile search_path, direct DML, fallback selectors, and claim theft.

Prove RuntimeAdoption row/event/Outbox/Audit delta=0, no resolver invocation, no adoption ID, runtime configuration/AgentRun/Recommendation byte and state invariance, no LearningSignal/Proposal/application/confidence/ModelPolicy/AgentDefinition/autonomy/compensation changes, no Standard/Edition/Clause/RequirementControl/certifiability changes, and zero external business effects. Search and inspect all relevant latest/current/head/leaf/max/newest/descending-time selectors; any implicit runtime Activation/Adoption is P0.

Before teardown, export governed-target-activation-evidence-manifest/v1 with complete Phase 28.3 and Phase 29 evidence, Activation/predecessor, all identities/hashes/source, fresh authority, policy, capability, event/Outbox/Audit, trace/timestamp, RuntimeAdoption count=0, runtime_effect_changed=false, and canonical manifest hash. Append a hashed teardown disposition. Tear down the container, database, roles, volume, and temporary material. Without reconstructing the database, verify exactly CREATED=true, APPLICATION_GOVERNED=true, PUBLISHED=true, ACTIVATED=true, RUNTIME_ADOPTED=false, RUNTIME_EFFECTIVE=false, database_reconstructed=false.

Run focused unit/system/static/docs checks, the PostgreSQL 18.6 acceptance/rollback/concurrency/ACL/reconciliation matrix, protected regressions, frozen migration/source/governance/runtime hashes, git diff --check, and final git status. Report exact test counts, hashes, teardown evidence, zero-effect deltas, P0/P1 counts, residual blockers, and one final verdict. If any exact invariant cannot be proven, fail closed, tear down, retain truthful failure evidence, and do not claim Activation success.
```
