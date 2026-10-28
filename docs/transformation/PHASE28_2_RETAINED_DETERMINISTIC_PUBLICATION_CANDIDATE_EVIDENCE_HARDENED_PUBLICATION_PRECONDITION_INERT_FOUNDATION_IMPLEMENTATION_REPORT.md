# ISO SMART AI — Phase 28.2 retained deterministic publication-candidate evidence and hardened publication-precondition inert foundation

- Date: 2026-09-03 (`America/Costa_Rica`)
- Workspace: `/home/felipe/proyectos/isosmart`
- Nature: repository-retained synthetic-source contract, retained-evidence verifier and inert publication preflight only

## 1. Verdict

**PHASE 28.2 — PROMOTED**

The deterministic retained-evidence and hardened publication-precondition
inert foundation is sufficiently proven to permit a later design/authorization
gate for creation of one new synthetic publication candidate and, after that,
a separate ephemeral publication POC. No candidate, Publication, Activation or
RuntimeAdoption was created.

## 2. Entry baseline

The authoritative entry verdict was Phase 28.1 promoted for publication-blocker
implementation design only. Migrations 0001--0022 existed and 0023 was absent.
The Phase 26 database and candidate graph remained destroyed and unavailable.
The repository already contained substantial uncommitted user work.

## 3. Initial git status

Before modification, modified paths were `backend/backend/settings.py`, five
`backend/integration` files, two `backend/leadership` files,
`backend/test_default.sqlite3`, sixteen frontend component/context/page/style/
test/config files, including the known Sidebar whitespace, and untracked
`AGENTS.md`, `backend/foundation/`, `backend/leadership/tests.py`,
`backend/logs/`, `docs/adr/`, `docs/governance/`, `docs/operations/`,
`docs/transformation/` and one frontend test. No item was cleaned, reset,
stashed, checked out or overwritten.

## 4. Frozen hashes

Before implementation, SHA-256 was recorded for all 22 migrations, all ten
authoritative sources, the relevant policies/ADRs/reports and protected runtime
files. Sections 39--42 give the values rechecked after implementation.

## 5. Phase 28.1 decisions inherited

`vN+1` remains superseded. `vN+2` remains the truthful historical Phase 26 leaf
but is not addressable evidence. A future fixture must be new, synthetic,
non-authoritative, non-normative, non-licensed, test-only and non-production.
The Phase 26 substantive fingerprint and Phase 27.2 lifecycle hash remain
different contracts.

## 6. Permanently unavailable Phase 26 candidate enforcement

`verify_candidate_evidence` accepts `PERMANENTLY_UNAVAILABLE` only with the
closed identity `phase26-disposed-ephemeral-publication-candidate` and rejects
any candidate/governance graph supplied with that state. Deterministic UUIDs,
shape-valid caller IDs and newly generated Receipts therefore cannot be
promoted as recovered Phase 26 evidence.

## 7. Synthetic source manifest contract

The retained JSON manifest freezes schema, namespace, deterministic source ID,
closed classification, authority/normativity booleans, purpose, exact synthetic
bytes/hash, locator grammar, scheme/version, generator/canonicalization
versions, provenance, one allowed operation and prohibited uses. It explicitly
sets `licensed_content_present=false` and `phase26_continuity_claim=false`.

## 8. Synthetic namespace/locator grammar

The exclusive grammar is:

```text
iso-smart-synthetic-poc-source-ref-v1:<source-uuid>:<source-material-sha256>:fixture/element/<token>
```

It is disjoint from `iso-smart-source-ref-v1` and any official ISO locator.
Cross-namespace substitution is rejected before preflight.

## 9. Candidate evidence manifest

The implemented verifier recognizes exactly `NOT_YET_CREATED`,
`CREATED_AND_RETAINED`, `DISPOSED_WITH_RETAINED_EVIDENCE` and
`PERMANENTLY_UNAVAILABLE`. Created/disposed evidence freezes run, target,
operation, rule/layer/lineage/predecessor/version, canonical rule material,
three hashes, source manifest/reference, complete governance graph, Receipt,
events/outbox/audits, trace, policies and timestamps. No real candidate
manifest was fabricated in this phase.

## 10. Cross-phase retention invariant

Created evidence must contain canonical material, an export timestamp, retained
timestamp and positive integrity verification. Disposed evidence additionally
requires an explicit disposal timestamp after retention. Hash-only records,
summary reports and post-teardown export chronology fail closed.

## 11. Canonicalization contract

`iso-smart-retained-evidence-canonical-json-v1` means UTF-8 JSON, recursively
sorted object keys, compact `,`/`:` separators, Unicode retained, NaN rejected,
array order retained and SHA-256 over the exact bytes. The manifest material
hash is calculated with only its own hash field omitted.

## 12. Phase 26 semantic fingerprint contract

The implementation reproduces the promoted field set: fingerprint version,
target type, KnowledgeLayer ID/type, Standard ID, StandardEdition ID/source
hash, lineage, rule key, logic JSON, evidence expectation, certifiability and
source-reference scheme. Rule/revision ID, version, predecessor, status,
publication metadata, timestamps and exact locator remain excluded exactly as
designed.

## 13. Phase 27.2 fingerprint comparison

The lifecycle hash contains only KnowledgeLayer ID, rule key, logic, evidence
expectation and certifiability. Tests prove it differs from the substantive
fingerprint and cannot be supplied in its place.

## 14. Dual semantic/material hash binding

The verifier recomputes the Phase 26 fingerprint, Phase 27.2 lifecycle hash and
full 0022-shaped revision material hash from retained canonical material. Each
must independently equal its declared value; neither substitutes for another.

## 15. Publication precondition contract

The inert service checks exact target/operation, candidate/layer/lineage/
version/predecessor, unique current leaf, unsuperseded draft status, no
activation/adoption, all three hashes, exact source, full governance/Receipt,
compensation category, policy, capability, curator, fresh AdminApps authority,
MFA/access/permission/global scope, actor SOD, idempotency and a final expected
state token. Its only positive outcome is
`ELIGIBLE_FOR_LATER_PUBLICATION_GATE`.

## 16. Current-leaf enforcement

The snapshot must contain exactly `(candidate_id,)` as the lineage leaf set and
`superseded=false`. Zero leaves, multiple leaves, a predecessor, a stale
caller-selected revision or a compensated/superseded revision is rejected. No
version, timestamp, maximum or latest selector exists.

## 17. Complete governance-chain validation

The verifier checks exact immutable cross-links across LearningSignal,
LearningProposal revision, CanonicalDelta, selected approving Reviews, approved
Decision, valid Application Authorization and application Receipt. Wrong IDs,
hashes, target, operation, outcome or relation fail closed.

## 18. Application Receipt validation

Receipt must bind Proposal, Delta, Decision, Authorization, predecessor target,
result candidate/material/fingerprint and exact operation. It must say
`successful=true`, `external_effects=false`, `runtime_effect_changed=false`,
`result_published=false` and `result_status=draft`.

## 19. Compensation provenance handling

Preflight permits only `NOT_APPLICABLE` or `COMPENSATED_CURRENT_LEAF`.
Compensated status requires a provenance hash, while the unique-leaf and
unsuperseded checks still apply. It cannot select the superseded forward
revision.

## 20. Curator evidence

The frozen curator record binds its own ID/hash, trusted actor/authority
decision, exact candidate/material/fingerprint, source manifest/reference hash
and validation time. It cannot mutate or publish and is independent from the
application executor and publisher.

## 21. Publication authority

Only the exact `TrustedPublicationAuthority` type is accepted. It must be
server-resolved, time-fresh, active, MFA-verified, global and contain only the
required publication permission plus AdminApps decision/context provenance.
Client role assertions are not accepted as an authority object.

## 22. Actor-level separation of duties

The actor map must contain proposer, reviewer, proposal approver, application
authorizer, application executor, curator, publisher, activator and adopter.
Publisher must differ from every other actor; curator differs from executor;
activator differs from adopter. Trusted curator/publisher identities must equal
their mapped actors.

## 23. Idempotency

Material identity includes preflight/key, exact candidate/layer/lineage/
predecessor/version and three hashes, source manifest/locator, governance
graph, Receipt, curator and both authority decisions, policy, operation,
compensation, expected state and retained-manifest hash. Exact replay returns
the same preflight result; changed material conflicts and never publishes.

## 24. Concurrency

Fixed modeled order is idempotency claim, lineage, candidate, retained graph,
curator and authority. A lineage lock plus eligibility claim permits one exact
candidate. Concurrent same-candidate/same-material calls yield one result and
one replay; another revision in that lineage conflicts. The coordinator is
explicitly isolated-test/inert infrastructure, not a production lock or
publication store; durable database serialization remains a later publication
implementation obligation.

## 25. TOCTOU

The service validates inside the lineage lock, freezes the complete first
snapshot representation, obtains a second fresh snapshot, rejects any drift,
then revalidates every final precondition before recording eligibility.
Authority revocation, capability or target/source/Receipt/curator change fails.

## 26. Reconciliation

Read-only outcomes are exactly `COMMITTED`, `NOT_COMMITTED`, `ABANDONED` and
`INCONSISTENT`. Committed requires the exact claim/result/audit hashes; absent
durable evidence is not committed; abandonment requires an explicit reason
hash; partial or contradictory evidence is inconsistent. Rule state is never
used to reconstruct a result.

## 27. Event boundary

No event is emitted. In particular, `knowledge_layer_rule.published` does not
appear in the new implementation or tests as an emitted action.

## 28. Audit/observability

The inert result creates only a sanitized audit material hash over IDs, hashes,
authority/curator references and categorical outcome. No Evidence body,
licensed text, prompt, credential, secret or token is copied.

## 29. Migration/schema changes

Migration 0023 remains absent. No model, table, SQL function, role, grant,
publication status or database row was needed or changed. This avoids creating
a persistence capability before a candidate-creation authorization gate.

## 30. RLS/ACL/catalog evidence

No database artifact or principal was introduced, so PostgreSQL RLS/catalog
changes and tenant A/none/B tests are not applicable. The evidence is global,
repository-retained and read-only; no fake tenant was invented. Existing 0021/
0022 RLS, ACL and catalog contracts remain byte-identical.

## 31. Least privilege

The new module has no database import, connection, SQL, target DML or call to
the native publication/activation/adoption services. It grants no role or
capability. The source manifest explicitly prohibits all release transitions.

## 32. Synthetic candidate test lifecycle

Tests build deterministic objects only in Python memory using a new Phase 28.2
UUIDv5 namespace. They create no ORM/PostgreSQL row and vanish with the test
process. Only the synthetic source manifest and generic verifier survive.

## 33. CheckConstraint/Django environment investigation

Repository declaration: Django `4.2.22`. `backend/.venv`: Python 3.12.13,
Django 4.2.22. `backend/.venv312`: Python 3.12.13, Django 6.0.6. The prior
`CheckConstraint(check=...)` failure is environment/version skew from the 6.0.6
environment. Using the pinned environment, `manage.py check` passed with zero
issues and migration drift reported no changes. Historical migrations and
constraints were not modified.

## 34. Protected-target invariance

No database was opened or target service invoked. Therefore real project
deltas are: KnowledgeLayerRule 0; Publication 0; Activation 0;
RuntimeAdoption 0; ModelPolicy 0; AgentDefinition 0; Recommendation 0;
AgentRun 0; normative catalog 0; governed-learning protected targets 0;
runtime behavior 0.

## 35. Selector/fallback scan

The new surface contains no latest/current/head/max/timestamp selector and
requires an explicit singleton current-leaf set. Existing `Max` matches in
AgentRun and Recommendation concern aggregate event sequence versions, not
KnowledgeLayerRule selection. Those protected files are unchanged.

## 36. PostgreSQL test matrix

The Phase 29 conditional was not triggered because Phase 28.2 introduced no
runtime/database artifact, schema, role or persisted command. Starting a
PostgreSQL 18.6 environment would test unchanged 0021/0022 rather than this
pure verifier. Database publication, RLS, ACL, failure injection and durable
cross-process races remain mandatory in the later publication POC gate, after
candidate creation is separately authorized.

## 37. Atomic rollback matrix

There is no newly persisted evidence command and no external boundary to
inject. Eligibility is inserted into the isolated ledger only after both
snapshot validations and complete material hashing. All tested validation,
TOCTOU and conflict failures leave no claim/result. Existing database atomicity
code is untouched.

## 38. Regression results

- `manage.py test foundation`: 122 tests, PASS.
- Focused Phase 28.2 scenarios: deterministic source, tamper, namespace,
  unavailable Phase 26, retention chronology, three hashes, every governance
  cross-link, Receipt, authority/curator/SOD, state/leaf, TOCTOU, replay,
  changed-material conflict, same/different revision concurrency and four-state
  reconciliation: PASS.
- Existing release and delta contracts are included in the 122-test PASS.
- Python compilation: PASS.
- Django system check in pinned environment: PASS, zero issues.
- `makemigrations --check --dry-run`: PASS, no changes.
- Source direct read/parse, OOXML CRC, Draw.io XML, JSON and CSV: PASS.
- Migration forward/reverse/forward and PostgreSQL harnesses: not applicable;
  no migration or database behavior changed.

## 39. Migration hashes

All 22 initial hashes match after implementation; 0023 is absent:

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

## 40. Source hashes

All ten initial hashes match: Aristas
`30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6`;
Mermaid `11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3`;
Draw.io `e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa`;
SQL `de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e`;
DOCX `8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c`;
XLSX `952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5`;
JSON `c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb`;
Nodes `ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3`;
OpenAPI `29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8`;
LEEME `eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db`.

## 41. Governance hashes

Unchanged: Phase 25.1 policy
`1a5f7c7838c62ba76837c26fcfa4d29655294810f74afed33fdcf69dc373bb79`;
governed learning `7d9c2fe30548bd18d390d119889c87a93595ac281fa3326691fe486bee49c4ec`;
implementation authorization `04458c4f1ccead125dd98ddac946ec9d77f8b0212412d13128355b10129c875c`;
review/application boundary `2d5beaebd5b2df1378c0f425354b45d52ff23dd1a5d158adad46572f7656c514`;
publication policy `efdd4d8a679c7f18762bfe79c3e876e970f81fedb2848ef5cbf21e7aeb858556`;
runtime repair design `263003d342e6bf7a2b56c25dbbb230296b81280a1da45eb347b00898e3231e92`;
ADR-0013 `8fa5852a3cabf822c5213ae10bcae2a61f3910233ff1d915d4d1e1545df6a827`;
ADR-0014 `fa0e376e802f80e95d3961fabf8f6fe5e337f4b312062123ffd45c31bb300952`;
ADR-0015 `57da49dff842349af8a7f3720595d858e96742d782bfe414174f84b8a1f3efea`.
Phase 26/27/27.1/27.2/28/28.1 report hashes also match their entry bytes.

## 42. Runtime/protected hashes

Unchanged: models
`9dd94c945dd0c256c3872e82b45760b06c066a4364e3dc3d833d56c09645c244`;
application service `99d228984efe4bba15c76f91e157f2ddd66d8aec9b5bf153a21c095fd57ed8cf`;
release service `a7b0477f48120b852d9ec510d30e85d4700f5c0ba970e3ed3c9e244b1be4d7e9`;
eventing `c7620cdfb0b51a0c1e022358dcbdae8a7e56b363e182dc09aa11ec675ecf95b8`;
audit `461459401abb354b22c42eec05dcd9805e4fd7800554c67b96aee8885c6734ef`;
AgentRun `6767e2098365536b88d4d8e9afdaef0f8b796383c79d7f40e0e0ea91b964ec2d`;
Recommendation `655fbdd18437f3d04a838c4dfad0b5b5fb3f6cc2e3d53d29fcc21a22acc6648c`;
Phase 26 harness `0211b25081cc90f61d6497faf101fad42d5a92cd960f5463b2df1efb09f0df95`;
Phase 27.2 harness `b089ddf3fc37456041677d120348cb01e036897fbc57357f94dcb05888aeb9c8`.

New artifact hashes at report drafting time: source manifest
`6172874247eaa53d374e687073052c7e9ad8f333bfa94b135234bb8d2e02a600`;
implementation `001efc1196f3028e44ddfa9e86c866587f3270c306374ae317fefd18df661814`;
tests `8ab4f20b6ba27a219f1e651de1c207f1315800aa62d055d417a73df74dd759d0`.

## 43. Git hygiene

Phase 28.2 added only the verifier, its tests, the synthetic source manifest
and this report. Unrelated dirty files remain. Repository-wide `git diff
--check` still reports only the known pre-existing
`frontend/src/components/Layout/Sidebar.jsx:28` trailing whitespace. Scoped
checks for all Phase 28.2 files pass.

## 44. External-effects statement

```text
production effects = 0
staging effects = 0
shared database effects = 0
publication effects = 0
activation effects = 0
runtime adoption effects = 0
runtime cutover effects = 0
normative effects = 0
automatic learning effects = 0
external business effects = 0
```

No provider, AdminApps, MedSupplier, notification, DNS, deployment or telemetry
call was made.

## 45. Teardown evidence

No PostgreSQL database/role, container, volume, socket/proxy, temporary
directory, secret/configuration or candidate row was created. Consequently
there was no ephemeral Phase 28.2 resource to remove, and filesystem checks
show no migration 0023 or temporary manifest.

## 46. Residual risks

Actual candidate creation, repository export of its concrete evidence,
database-enforced durable lineage serialization, publication authority policy,
legacy-runtime isolation and publication atomicity remain deliberately outside
this promotion. They are mandatory proof obligations for later gates, not
defects in this inert foundation. The isolated ledger must never be treated as
a production or cross-process lock.

## 47. P0/P1 count

```text
P0 blockers = 0
P1 blockers = 0
```

## 48. Final verdict

**PHASE 28.2 — PROMOTED**

Promotion authorizes only the next candidate-creation plus publication-POC
authorization gate. It does not authorize candidate creation here,
publication, activation, RuntimeAdoption, runtime wiring/cutover, production,
staging, deployment, a second learning target/operation, automatic learning,
cross-tenant learning or normative mutation.

## 49. NEXT_CODEX_PROMPT

Execute Phase 28.3 exclusively in `/home/felipe/proyectos/isosmart` as a
**CANDIDATE CREATION + PUBLICATION POC AUTHORIZATION GATE**, not as publication.
Read `AGENTS.md`, the Phase 25.1 through Phase 28.2 reports and policies,
ADR-0013 through ADR-0015, migrations 0021/0022, the Phase 26 and 27.2
PostgreSQL harnesses, `backend/foundation/retained_publication_evidence.py`, its
tests, the retained synthetic source manifest, governed-learning/application/
release/runtime services, data/RLS/event/audit/threat/migration architecture
and all ten authoritative source artifacts directly. Preserve migrations
0001--0022, authoritative sources, prior reports/policies/ADRs and protected
runtime/application files byte-for-byte; preserve unrelated user work.

Determine whether Product Governance can authorize creation of exactly one new
deterministic synthetic `KnowledgeLayerRule` source-reference-correction
candidate under a new lineage and the exact existing operation
`learning.knowledge_layer_rule.source_reference.correct/v1`, using only the
repository-retained source manifest classified
`RETAINED_DETERMINISTIC_SYNTHETIC_FIXTURE`. The candidate must be explicitly
non-authoritative, non-normative, non-licensed, test-only and non-production;
must not use or imply any destroyed Phase 26 identity; and must remain draft,
unpublished, inactive and unadopted. Define the exact candidate/root/lineage
material, canonical deltas and complete new LearningSignal -> Proposal ->
CanonicalDelta -> selected Review -> Decision -> Application Authorization ->
application Receipt chain. Require independent curator and future publisher
actors, server-resolved AdminApps provenance, fresh MFA/access/permission/
global scope, actor-level separation, exact current-leaf semantics, dual
semantic/full-material hashes, Phase 27.2 lifecycle hash, policy/version/hash,
idempotency, fixed lock order, TOCTOU and four-state reconciliation.

If and only if strictly necessary for isolated proof, create the candidate and
its governance graph inside one official disposable PostgreSQL 18.6 database
with teardown defined before creation. Before teardown, export the concrete
`governed-target-application-evidence-manifest/v1`, canonicalize/hash it,
integrity-verify it against the live graph, retain the exact sanitized manifest
in a repository-approved evidence path, then mark its state truthfully after
teardown. Prove deterministic reproduction, every governance cross-link,
Receipt/event/outbox/audit identity, source namespace separation, retention
chronology, full/semantic/lifecycle hashes, single current leaf, no fork,
same/different revision concurrency, tamper rejection, ACL/RLS/least privilege,
hostile search path, rollback injection and complete teardown. Do not invent
tenant IDs for global artifacts and do not retain licensed bodies, Evidence
bodies, prompts, secrets or tokens.

This gate must not invoke native publication, mutate status/published_at,
create a Publication, Activation or RuntimeAdoption, wire runtime, select
latest/current/max/timestamp, create another target/operation, mutate
ModelPolicy/AgentDefinition, deploy or access production/staging/shared
databases/external systems. It may produce a narrowly scoped successor Product
Policy authorizing only candidate creation and later publication-POC
eligibility if all proof obligations pass; it must not authorize publication
itself. Require zero real protected-state/runtime/normative/external effects,
unchanged frozen hashes, exact teardown, and zero P0/P1 blockers. If any source,
governance, retention, authority, SOD, concurrency, isolation or teardown proof
fails, emit NOT PROMOTED and address only that blocker in the following gate.
