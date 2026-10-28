# First retained synthetic KnowledgeLayerRule Activation POC Product Policy v1

Status: `APPROVED FOR FUTURE EPHEMERAL ACTIVATION POC ONLY`

Policy identity: `first-retained-synthetic-klr-activation-poc-policy/v1`

Version: `v1`

Classification: non-normative, non-production Product Policy.

## 1. Authorization boundary

This policy authorizes one future, isolated, ephemeral PostgreSQL 18.6 proof of concept to record exactly one first `KnowledgeLayerRuleActivation`. It authorizes no action in Phase 30.

The only eligible graph is:

- candidate `01a0682b-dfc8-7b49-a601-f9bda29a70a5`;
- lineage and rule predecessor `da72872a-3f3c-5fcd-86f7-0ed33e453522`;
- version `sN+1`;
- full material hash `caa24592b509334af4cd60fd7d3f3c43989d864d3f1c6e6d0d3bf83a81871f81`;
- semantic fingerprint `8465956c1daf27a9838bc1bfb468af3f518ae255b4662b2df40e7b8648516192`;
- lifecycle hash `0adfd8075cc720140c6e1f0393d286799edac8f352efd9f1969816be83c51e52`;
- exact Publication `e97576de-d4ef-520d-8592-d376ed401221`;
- Publication event `b19e4861-219d-4a07-8faf-656e02dbf9b4`, Outbox `4e78cfe6-8afa-400b-85f5-e5fe72b59e04`, and Audit `6a3ed87d-a992-4406-8ac8-233017301d35`;
- Publication evidence manifest material hash `51f0b207c790e6ab0c3d67985e161ba0d0cc7b2feb888f545c1ff5eedacf5366`;
- Publication disposition material hash `fff3b225184282e48dad30f4e56b16444df4241b5f647f2f3750ee4a254158f1`.

Rule ID, status, version, timestamp, lineage head, newest rule, or latest Publication are never substitutes for this complete exact graph.

## 2. Source and material boundary

The source remains `RETAINED_DETERMINISTIC_SYNTHETIC_FIXTURE`, non-authoritative, non-normative, non-licensed, test-only, and non-production. Its manifest identity is `6ec35e4a-bb8a-592b-bc6a-420691f4e8e3`; canonical manifest material hash is `cf92c267439f94f302e67888665dbf99392592341a808f5fc00f4c32ef23dc24`; source material hash is `efe61114215914ac486011e4efd9977b4fa2f1c34fa6fad67012a46ced85ab4f`; source-reference scheme is `iso-smart-synthetic-poc-source-ref-v1`; exact locator hash is `0ad437944a111b3593ba29f52466416eed9b4f0b8e7e9247c082575df0d659b6`. There is no Phase 26 continuity claim.

The source manifest is evidence, never activation authority. Its prohibited-use classification remains frozen; this independent Product Policy is the only narrow authorization for the later governance-transition experiment. The candidate remains non-certifiable guidance and must never be presented as ISO text, licensed material, or official normative content.

Activation may append governance evidence only. It must not change the rule body, source reference, logic, evidence expectation, certifiability, lineage, rule predecessor, or any frozen hash.

## 3. Independent authority and separation of duties

The only intended activation actor is the exact retained human role actor `49132b9d-93ae-510a-8de0-ad36ef508f8f`. At the future operation, the server must resolve a new AdminApps decision proving: human actor type, active access, MFA verified, global governance scope, exact permission `qms.knowledge_layer_rule.activate`, decision ID, decision version, decision hash, evaluation timestamp, expiry/freshness, this policy identity/version/file hash, and `server_resolved=true`. Client-supplied or cached assertions fail closed.

The activation actor must be distinct from all prior role actors:

- publisher `8069fbeb-0ef6-582c-8f3b-ff88e606c869`;
- proposer `24d89409-dbb2-5771-9296-166afd4039b6`;
- reviewer `f8853b40-ef90-53b4-bd1b-17f85bcd5d79`;
- proposal approver `02d02d75-1d97-5dc3-b494-50e83335492e`;
- application authorizer `b71e6996-1e15-5aef-b73b-db331b01305f`;
- application executor `d91b730d-5d5b-5a64-a25c-a0318385a6eb`;
- curator `1dab9ba5-5c8a-504c-81b8-0ac70f15af14`;
- future adopter `0757c393-8c83-52be-ae2a-25385901f232`;
- any repair authority.

Activation confers no Publication, RuntimeAdoption, learning-application, repair, or capability-control permission. Publication confers no activation permission. Activation confers no adoption permission.

## 4. First-activation and lineage contract

The expected predecessor Activation is explicitly `NULL`. It means “first Activation in lineage `da72872a-3f3c-5fcd-86f7-0ed33e453522`,” not omitted, unknown, or inferred. The transaction must lock the exact activation lineage and prove that it contains zero Activation rows before insert. A uniqueness constraint equivalent to `UNIQUE NULLS NOT DISTINCT (lineage_id, predecessor_activation_id)` must prevent more than one root and more than one successor for any predecessor.

Rule lineage and Activation lineage remain independent. Any later recovery or transition appends a new Activation referencing an exact predecessor Activation. No Activation is updated or deleted, and no mutable active/current/latest pointer may be introduced.

## 5. Claim and idempotency

The canonical operation material must bind the Activation ID; exact candidate, Publication, and retained evidence hashes; full, semantic, and lifecycle hashes; source manifest/material/reference provenance; explicit predecessor `NULL`; activation actor and fresh authority decision; this policy identity/version/file hash; exact capability decision ID/version/hash/state; idempotency-key hash; trace ID; event, Outbox, and Audit IDs; and operation schema/canonicalization versions.

The claim is append-only and collision-safe. Identical material returns the same Activation as replay or waits for the winner. The same key or Activation ID with changed material is a conflict. No claim may be stolen, timed out into reuse, or retargeted.

## 6. Concurrency and lock order

Every writer must acquire locks in this order:

1. exact activation idempotency/claim identity;
2. exact activation lineage and explicit predecessor slot;
3. exact Publication row and retained Publication evidence identity;
4. exact candidate revision;
5. exact fresh authority decision;
6. exact append-only Activation capability leaf;
7. deterministic activation event, Outbox, and Audit stream identities.

No code path may acquire these in reverse. This serializes same-material replay, competing material, different-Publication attempts against the same predecessor, authority revocation, and capability disable races without an Activation fork. Authority and capability are checked at admission and again immediately before commit.

## 7. TOCTOU and capability fence

Immediately before commit, revalidate the candidate identity and three hashes; exact Publication and its retained evidence/disposition hashes; source provenance; explicit predecessor `NULL`; absence of any root/successor race; fresh AdminApps authority and all SOD rules; this policy identity/version/file hash; exact idempotency material; the independent Activation capability decision; and zero RuntimeAdoption referencing the new Activation. Any drift rolls back the whole transaction.

Activation capability is independent of learning application, Publication, RuntimeAdoption, repair, and control. Disabled means deny at admission and precommit. Re-enable is a later append-only capability decision, never an update.

## 8. Atomic evidence and event meaning

One transaction must persist exactly one claim, Activation artifact, `knowledge_layer_rule.activation_recorded` event schema `v1`, TransactionalOutbox row, and immutable Audit row. The event means only that the exact published revision passed activation governance. It does not mean adopted, effective, deployed, learned, effective in quality terms, or normatively certified.

The event and Audit freeze Activation ID; predecessor `NULL`; Publication ID and evidence hash; candidate, lineage, version, and three hashes; source manifest/material/reference hashes; activation actor; authority decision ID/version/hash and evaluation time; policy identity/version/file hash; capability decision ID/version/hash/state; trace; and recorded timestamp. They contain no licensed content or secrets.

Every injected failure at claim, authority validation, capability admission, predecessor lock, Publication validation, candidate validation, Activation insert, event, Outbox, Audit, or immediately before commit must leave zero Activation, event, Outbox, Audit, RuntimeAdoption, and runtime deltas.

## 9. Reconciliation and recovery

Ambiguous outcomes are exactly:

- `COMMITTED`: the complete mutually matching claim → Activation → exact Publication → candidate/hash plus event, Outbox, Audit, authority, policy, capability, and trace graph exists;
- `NOT_COMMITTED`: all durable evidence for the Activation operation is absent;
- `ABANDONED`: an authorized operator has appended an explicit immutable disposition; timeout is insufficient and the claim remains unavailable;
- `INCONSISTENT`: any partial, mismatched, substituted, or forked graph.

Reconciliation never infers success from candidate status or Publication. Repair may inspect, classify, append an incident/operator disposition, disable the exact capability, or request governed recovery. It may not activate, publish, adopt, mutate the rule, rewrite evidence, change lineage, fabricate missing evidence, or grant privilege. Recovery is a later independently governed append-only Activation transition and causes no runtime effect.

## 10. Least privilege and hostile matrix

The future activator is LOGIN, non-superuser, `NOINHERIT`, `NOBYPASSRLS`, non-owner, without generic table/rule DML and without Publication, RuntimeAdoption, learning-application, repair, or capability-control authority. It receives EXECUTE only on the exact Activation boundary.

If `SECURITY DEFINER` is used, its dedicated owner is NOLOGIN, non-superuser, `NOINHERIT`, `NOBYPASSRLS`, and not a table owner. The function uses a fixed safe `search_path`, fully qualified objects, no dynamic SQL, no arbitrary target/Publication/status/state selector, `PUBLIC` revoked, and EXECUTE granted only to the activator principal.

Phase 31 must prove denial for PUBLIC; publisher; application executor; curator; adopter; worker/projector; repair; spoofed actor, MFA, or global scope; stale or revoked authority; wrong candidate, Publication, hash, or predecessor; disabled capability; and hostile search path.

## 11. Retained evidence and teardown

Before teardown, export `governed-target-activation-evidence-manifest/v1` containing the complete Phase 28.3 candidate evidence, Phase 29 Publication evidence, Activation ID and explicit predecessor, candidate and Publication identities/hashes, semantic and lifecycle hashes, source provenance, authority, policy, capability, event, Outbox, Audit, trace, timestamp, `RuntimeAdoption count = 0`, `runtime_effect_changed=false`, and a canonical manifest material hash. Append a teardown disposition and verify it offline without reconstructing the database.

The offline result after a successful future POC must be exactly:

```text
CREATED=true
APPLICATION_GOVERNED=true
PUBLISHED=true
ACTIVATED=true
RUNTIME_ADOPTED=false
RUNTIME_EFFECTIVE=false
database_reconstructed=false
```

## 12. Explicit prohibitions

This policy does not authorize Phase 30 activation, migration 0024, permanent schema or grants, RuntimeAdoption, adoption event, resolver invocation, runtime wiring/cutover/configuration, production or staging, deployment, another candidate or Publication, automatic learning, compensation, confidence/ModelPolicy/AgentDefinition/autonomy change, normative or certifiability change, licensed material, or external business effects.

Effectiveness evidence is independent. Existing policy does not require a new effectiveness assessment to record Activation. A release-compatibility assessment hash may be frozen as operation evidence, but cannot authorize Activation, RuntimeAdoption, or automatic promotion.

Successful future Activation must leave `PUBLISHED=true`, `ACTIVATED=true`, `RUNTIME_ADOPTED=false`, and `RUNTIME_EFFECTIVE=false`. Any inability to prove the boundary is a fail-closed denial.
