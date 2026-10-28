# ISO SMART AI — Phase 31.3.1 exact-ID Application adapter architectural decision closure gate

- Decision date: 2026-09-04 (`America/Costa_Rica`).
- Workspace: `/home/felipe/proyectos/isosmart`.
- Nature: documentation/governance only; Phase 31.4 not executed.
- New durable repository artifacts: exactly one successor ADR and this report.

## 1. Verdict

`PHASE 31.3.1 — PROMOTED`

The exact-ID Application adapter is a genuine architectural decision: **YES**.
ADR-0017 records that decision and closes the single entry governance P1.
Promotion is architectural closure and conditional eligibility for the future
isolated POC, not proof of PostgreSQL equivalence or creation of lifecycle state.

## 2. Entry inconsistency and append-only correction

Phase 31.3 §21 explicitly calls the ephemeral exact-ID Application adapter
“the only new architectural decision” and then concludes that no successor ADR
was needed beyond Product Policy. The Phase 31.2 continuation requires a
successor ADR when a genuine new architectural decision is necessary;
`AGENTS.md` requires ADRs and transformation documentation to stay synchronized
with structural decisions. A new privileged execution path meets that rule.

The no-ADR conclusion is superseded by ADR-0017 and this report. Phase 31.3's
historical report/verdict and five-artifact execution package remain unchanged.
The rest of Phase 31.3 is not reopened. The directly relevant 0023 grammar
extension is recognized as existing promoted behavior, not treated as a new
adapter permission or a new governance inconsistency.

## 3. Initial Git status and scope

The first command inside the exclusive repository was `git status --short`,
before reading its files or making edits. Exact initial output:

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

All listed work was pre-existing, including the untracked Foundation, ADR and
governance directories. A preliminary path-only discovery from the parent
workspace returned ISO Smart paths; no sibling file content was read or
modified. The user's attachment was read to identify the request. All project
inspection, tests and edits then used the exclusive ISO Smart repository.
Temporary offline runner/hash inventories used `/tmp/isosmart-phase31-3-1-z5l2adfm`
and are not additional repository deliverables or runtime implementation.
No staging, reset, stash, commit, reformat or normalization occurred.

## 4. Frozen hashes and preservation

Before edits, a SHA-256 inventory captured 14,348 existing files, including all
protected documentation, code and local database files; volatile Python caches
were excluded. Every captured file was compared again after validation.
The protected domain inventories are listed below and in the full hash ledger
following §22. Inventory digests use sorted repository-relative paths, each
encoded as `path + NUL + lowercase file-byte SHA-256 + LF`, then SHA-256 of
that UTF-8 stream. All matching counts refer to entry/exit byte equality.

| Inventory | Entry/exit result | Inventory SHA-256 |
|---|---|---|
| foundation_migrations_0001_0023 | 23/23 MATCH | `cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc` |
| phase31_3_five_artifacts | 5/5 MATCH | `a9029943fc9dd43db7c6ba87031371165db0d41babf34b9cbddbeeeeefd3c29b` |
| authoritative_sources | 10/10 MATCH | `e03f58ae46964d8a3265ddf0b0c5b10a9dcc299bd7002bc88c97f3a8caa04266` |
| prior_ADRs | 16/16 MATCH | `d8aff5f8b8059f49466ab97f223ee4840df4cf7a8cb2defe45d67dfef84b8640` |
| historical_evidence | 4/4 MATCH | `f5ea7f6df6c878c47ceb8254eef43e926d9f05986199c7a0ccc01c67f4813aa7` |
| historical_reports | 47/47 MATCH | `25d2619374b2976d206210b6a8596be7e50d93bfc9e627a0ed86734169b1fa3f` |
| existing_governance_policies | 13/13 MATCH | `2ab5c9ef22e7f3330973b9e2a17b04e67225a034efd4da187e57acaf9a158cbd` |
| protected_implementation | 16/16 MATCH | `1d6971ac2e01a2e82b7482da3d847d494642046e2d85f1179782391bdd28abab` |

The five Phase 31.3 file hashes also match the promoted report §32; the 23
migration hashes match Phase 31.1's exact inventory; the ten authoritative
sources match their source manifest; the fourteen previously enumerated
protected Foundation files match Phase 31.1. All 16 prior ADRs are unchanged,
including mandatory ADR-0013–0016. Existing governance policies and all 47
historical Phase reports are frozen. Historical report inventory membership is
all pre-existing `docs/transformation/PHASE*` files, excluding this new report.

Migration-set hash is
`cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc`,
matching the frozen closure specification. Migration 0024 is absent.
Phase 31.3 report SHA-256 is `fc5f16abab801570aefd313b87cae1805f3e5067e73d01acebebce9519724a8f`.
No hash equality is presented as evidence of live database behavior.

## 5. Decision analysis and required reading

Semantic reading covered `AGENTS.md`; the complete Phase 31.2 and Phase 31.3
reports; ADR-0013–0016; the Phase 31.3 Product Policy and all three JSON
contracts; exact source bytes; migration 0021 and the directly relevant 0023;
the complete governed-learning Application service and Phase 26 harness;
Phase 28.3's identity, Application and retained-material paths; ADR-0003 and
the related RLS/SECURITY DEFINER design. Retained-evidence canonicalization,
hash helpers, existing Foundation tests and previous hash inventories were
also inspected. Harness source was read, never executed.

Evidence confirms that the existing service supplies Authorization, expected
Delta hash, actor, trace and optional forward Receipt, with no output-ID
parameters. The private successor primitive allocates one UUID dynamically;
the public Application primitive allocates six more. Phase 28.3 obtains the
candidate and Receipt IDs from Application results and then retains live rows.
That is different from requiring every identity before execution.

## 6. Why this is an architectural decision

The adapter introduces an independently constrained privileged Application
path and changes identity allocation at a domain persistence boundary. It
requires decisions about ownership, grants, callable surface, immutable
history, transactional parity, retained evidence and teardown. These are
structural obligations even when the capability lasts for one POC.

The selected answer is YES. The Product Policy remains authoritative for its
product scope but cannot alone close the missing architecture record. No
repository evidence disproved the decision or required rewriting ADR-0013–0016.

## 7. Successor ADR identity and hash

Created [docs/adr/0017-ephemeral-exact-id-governed-application-adapter.md](../adr/0017-ephemeral-exact-id-governed-application-adapter.md).
Its SHA-256 is:

```text
82501ef34edc6d7e76e0971d3d2607c58f229a1dd4dd26696dd227fb7e994edb
```

ADR-0017 is the next sequential ADR after 0016. It succeeds without rewriting
prior decisions and contains no implementation SQL or code. Its fixed package
hashes and identity bindings were checked against the unchanged Phase 31.3
JSON. This report's hash is computed externally after finalization to avoid
recursive self-hashing.

## 8. Architectural problem

Migration 0021 uses `uuidv7()` for candidate, claim, Receipt, Event, Outbox,
curation Audit and immutable Application Audit. Phase 31.3 requires those
persisted identities to be predeclared. Altering migration 0021 or changing
the JSON to accept new IDs would violate the frozen baseline.

The reference is 0021 domain behavior under frozen migrations 0001–0023.
Migration 0023 already admits the exact synthetic source grammar by replacing
two grammar checks; it does not change identity allocation. Both future paths
must use that same promoted baseline. This is an explicit interpretation of
repository evidence, not a newly authorized source grammar change.

## 9. Selected solution

One specification-bound exact-ID adapter may exist inside the future isolated
Phase 31.4 PostgreSQL 18.6 environment. It reproduces promoted Application
semantics and substitutes only the frozen output identities for dynamically
allocated identity material. It is removed with the environment after the
frozen closure/teardown gate. No adapter implementation or database object was
created in Phase 31.3.1.

## 10. Exact scope

The experiment is `a3f8fd64-af24-5b31-977a-bcaf8146c563`; source is
`72d038c3-4ee5-5d40-a75b-398133dbed00`; root and lineage are
`bc5f4f17-294d-5abd-b27b-2d296921ffdf`. The only candidate the adapter may
create is `a55716fa-63c7-54eb-bda2-9c9666613b1a`, `s1`, with the exact root
as predecessor, draft/unpublished at Application return.

ADR-0017 enumerates the exact Proposal, Delta, Review, Decision, Authorization,
executor actor, claim, Event, Outbox, both Audits, Receipt, trace, target hashes,
operation and canonicalization. It binds all remaining source/support,
authority, SOD, policy, capability and evidence material to the frozen JSON.
Only its already-declared fresh slots may be filled at future execution.

## 11. Exact prohibitions

No arbitrary target selector, ID, field/value mutation, alternate source,
operation/version, generic dispatcher or replacement payload. No migration
0024, permanent function, production service, API, shared runtime capability
or reusable application framework. No Publication, Activation, RuntimeAdoption,
compensation, ModelPolicy/AgentDefinition mutation, autonomy change, normative
content mutation, alternate candidate, Phase 29 operation or external effect
through the adapter. Publication and Activation remain separately governed
future boundaries with independent actors and authority.

## 12. Behavioral-equivalence requirements

```text
exact-ID adapter behavior == promoted 0021 domain semantics
except for explicitly authorized identity preallocation
```

ADR-0017's blocking proof table requires comparison of validation outcomes,
candidate material, full-row/full-material hashes, substantive fingerprint,
lifecycle hash, lineage/predecessor, source-reference transition, Event
schema/material, Outbox, both Audits, Receipt, rollback, idempotency, stale
target, concurrent behavior, TOCTOU, and security/ACL behavior.

Deterministic comparable fixtures must run through the actual promoted
reference and the adapter. Preserve raw observations from both. Only the
seven output IDs and their dependent references may be related by an explicit
bijection for comparison. Verify original hashes first and recompute any
ID-dependent comparison hash; do not normalize persisted evidence or substitute
comparison IDs for the frozen retained candidate. Fresh values keep their
original validity, binding and canonicalization checks. There is no permission
to omit mismatched timestamps, source material or authority to claim parity.

The frozen Phase 31.3 outer admission, freshness, SOD, capability, precommit and
retention checks also remain mandatory. They do not authorize rewriting the
inner domain semantics. Any additional divergence is a blocking P1. If parity
cannot be demonstrated, **Phase 31.4 must stop before Publication**. No
PostgreSQL behavioral-equivalence result is claimed by this gate.

## 13. Least privilege

Every adapter function requires a dedicated `NOLOGIN NOSUPERUSER NOINHERIT
NOBYPASSRLS` owner, no table/sequence ownership, no persistent schema CREATE,
no executor-assumable membership, fixed safe search path, fully qualified
objects, no dynamic SQL and PUBLIC EXECUTE revoked. Only the exact ephemeral
LOGIN Application executor may execute the callable adapter entry; private
helpers remain private.

The executor is non-owner, non-superuser, NOINHERIT and NOBYPASSRLS, with no
direct table DML, CREATE, owner SET ROLE, curator/release/repair/capability
control authority. Tenant/organization context and exact actor are bound on
the same transaction/connection under fresh server-resolved authority.

## 14. SECURITY DEFINER boundary

`search_path=pg_catalog` is fixed; object qualification and absence of dynamic
SQL are mandatory. SECURITY DEFINER grants only the minimum access required
for the exact graph. Owner-only UPDATE privileges needed for row locks do not
authorize material mutation: immutable history guards stay effective. The
executor cannot invoke private primitives or turn the boundary into a generic
write surface. Tenant-scoped tables retain ENABLE/FORCE RLS and composite
constraints; global tables retain the promoted global security boundary.
Catalog inspections and hostile role-level tests in Phase 31.4 must prove
these conditions. Reading SQL alone is not that proof.

## 15. Retention-closure relationship

Deterministic identity strengthens `TRANSITIVE RETENTION CLOSURE / v1`; it
never replaces live evidence. Every generated artifact must be re-read live,
canonicalized, hashed, included in the graph, exported before teardown and
cross-checked against the Phase 31.3 specification. Derive dependencies from
both the live schema/FK snapshot and the frozen semantic registry to a fixed
point. Retain every mandatory local dependency in full canonical form and
external authority with frozen provenance.

Retain every required `normative.curation_audit` row, including root creation,
Application and Publication. All eight fields are mandatory: `id`, `action`,
`entity_type`, `entity_id`, `actor_id`, `trace_id`, `payload_hash`, `occurred_at`.
The Application row is `ff75b1d0-a2ea-5eae-9064-b9114496047a`; the Publication
row is `5fa5038d-3042-481f-8162-e1144eebc815`. UUID-only rows and substitutes
from governance Audit do not satisfy closure.

Publication closure must pass before Activation. Teardown requires complete
closure, independent export/live material equality and no reconstruction need,
followed by the frozen disposition/authorization and post-teardown offline
verification. A failure preserves the live isolated environment by default;
the existing dual-control override yields permanently non-rematerializable,
operationally ineligible evidence, never PASS. This rule governs future
execution only; no environment exists from this gate.

## 16. Phase 29 separation

```text
publication_id=e97576de-d4ef-520d-8592-d376ed401221
missing_normative.curation_audit.id=12d811ab-c3b4-4615-8972-75008a36e327
classification=HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE
incident=RETENTION_CLOSURE_BREACH
historical_publication_verified=true
faithful_rematerialization_allowed=false
activation_input_allowed=false
runtime_adoption_input_allowed=false
reconstruction_allowed=false
```

ADR-0017 explicitly prohibits rematerializing or repairing either that
Publication or its missing audit, reusing their IDs, importing/reconstructing
their graph, weakening an FK, or claiming recovery/continuity. The historical
fact remains valid. Phase 32/RuntimeAdoption remains blocked. The unchanged
Phase 29 offline verifier returned CREATED, APPLICATION_GOVERNED and PUBLISHED
true; ACTIVATED, RUNTIME_ADOPTED, RUNTIME_EFFECTIVE and database_reconstructed
false.

## 17. Non-generalization rule

Successful Phase 31.4 use does not authorize productionizing the adapter,
retaining its executable capability after teardown, adding it to normal
runtime, using preallocated IDs generally, replacing migration 0021 or
exposing generic application operations. Any permanent exact-ID mechanism
requires its own independent architecture gate and migration/API/security
review. Retained proof of code/ACLs is evidence, not an installed capability.

## 18. Phase 31.4 blocking tests

Before Publication, compare both Application paths under the frozen baseline
and complete every proof category in ADR-0017. Exercise all 13 frozen
Application rollback points, mapping them to real reference failure boundaries,
and the frozen idempotency/concurrency/stale-target/TOCTOU/security matrices.
Check every transaction member and protected-state delta, including curation
Audit, rather than relying on the smaller counts in a historical harness.

The remaining lifecycle must separately pass the frozen Publication and
Activation authority, SOD, capability, atomicity, rollback, concurrency,
reconciliation, closure and hostile matrices. Preserve the specified lock
order; do not steal claims or repair an ambiguous commit automatically.
Retained rows, canonical hashes and exact cross-links must satisfy the frozen
JSON without reinterpretation. Missing evidence, unexpected drift or any
unproved category blocks progression; static review does not excuse it.

## 19. Validation actually executed

| Check | Result and limits |
|---|---|
| Frozen file integrity | All 14,348 captured existing files unchanged; domain counts and SHA-256 inventories in §4 and hash ledger. |
| Foundation migrations | 23/23 MATCH against entry and prior inventory; 0024 absent; migration-set digest matches Phase 31.3 closure JSON. |
| Phase 31.3 package | Five file hashes MATCH; three JSON files parse without mutation. |
| Canonical hashes | 12 offline recomputations PASS: source bytes/manifest, Delta, candidate full material/fingerprint/lifecycle, root full material, two locators and three idempotency keys. |
| Historical evidence | Four embedded canonical hashes independently recomputed, 4/4 MATCH; four file-byte hashes unchanged. |
| Semantic registry | 56 unique edges have required fields and inherited canonicalization; structural validation PASS, not live closure proof. |
| Foundation offline tests | 136/136 PASS through Django's initialized runner with a dummy database backend. |
| Django | 4.2.22; isolated auth/contenttypes/Foundation system check: zero issues. |
| Migration drift | `makemigrations --check --dry-run`: no changes in the isolated installed-app scope; no database connection or migration execution. |
| Phase 29 offline verifier | PASS, historical lifecycle unchanged and `database_reconstructed=false`. |
| Documentation | Exact identities/package hashes agree with frozen inputs; one new ADR, one report, one continuation prompt; new files pass whitespace and link checks. |
| `git diff --check` | Exit 2 only for known pre-existing `frontend/src/components/Layout/Sidebar.jsx:28` trailing whitespace, preserved unchanged. |
| Scoped whitespace | `git diff --check -- . ':(exclude)frontend/src/components/Layout/Sidebar.jsx'`: PASS; separate new-file whitespace checks PASS. |
| PostgreSQL acceptance/equivalence/RLS/ACL/concurrency/rollback suites | **NOT EXECUTED**. No PostgreSQL behavior was tested. |

The first offline suite attempt configured Foundation alone and produced
135 passing tests plus one setup error because `auth.User` was unavailable.
It was not acceptance evidence. Loading auth and contenttypes only in the
in-memory test configuration corrected that error; the subsequent full
136-test run passed. Repository settings and dependencies were not changed.
An interpreter check found Django 6.0.6 in `.venv312`; no suite ran there.
The required existing `.venv` supplied Django 4.2.22.

Reproducible successful Django command, run from `backend`:

```bash
.venv/bin/python -B - <<'PYTHON'
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.auth', 'django.contrib.contenttypes', 'foundation'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.dummy'}},
    SECRET_KEY='phase31-3-1-offline-only', USE_TZ=True,
    DEFAULT_AUTO_FIELD='django.db.models.BigAutoField', LOGGING_CONFIG=None,
)
import django
django.setup()
assert django.get_version() == '4.2.22'
from django.core.management import call_command
from django.test.runner import DiscoverRunner
call_command('check', verbosity=1)
call_command('makemigrations', check=True, dry_run=True, verbosity=1)
raise SystemExit(bool(DiscoverRunner(verbosity=1).run_tests(['foundation'])))
PYTHON
```

This restricted validation loads no normal application settings, database
credentials or file logging handlers. It is not a whole-product deployment
check. Offline evidence command from repository root:

```bash
PYTHONPATH=backend backend/.venv/bin/python -B backend/foundation/verify_phase29_post_teardown.py
```

Hash/JSON validation used Python standard-library SHA-256/JSON plus the
unchanged `foundation.retained_publication_evidence` canonical helpers.
Each evidence document was hashed after excluding only its own declared
manifest/disposition hash field. Source bytes were hashed without text
normalization. No new test or implementation file was added to the repository.

## 20. Zero effects

```text
database effects = 0
PostgreSQL effects = 0
candidate effects = 0
Publication effects = 0
Activation effects = 0
RuntimeAdoption effects = 0
runtime effects = 0
historical reconstruction effects = 0
normative effects = 0
automatic learning effects = 0
external business effects = 0
```

No database, container, role, schema, SQL function, lifecycle row, candidate,
Publication, Activation or RuntimeAdoption was created. No database acceptance
suite ran. Existing SQLite files were byte-hashed, not opened through a
connection. No AdminApps, MedSupplier, provider, API, production, staging,
shared database, deployment or external business operation was invoked.

## 21. P0/P1 and final repository status

```text
entry_P0=0
entry_governance_P1=1
closed_governance_P1=1
P0=0
P1=0
remaining_governance_ambiguities=0
phase31_4_executed=false
```

The single missing architectural record is closed. Future implementation parity
is deliberately an unexecuted blocking condition, not falsely counted as a
verified result. Phase 29's historical retention breach and the separate
RuntimeAdoption prohibition remain in force.

Final `git status --short` equals the initial output in §3 because both new
files are inside already-untracked directory entries. A per-file inventory
comparison, beyond porcelain's collapsed output, confirms exactly these two
new repository artifacts and no changed/missing pre-existing files:

```text
docs/adr/0017-ephemeral-exact-id-governed-application-adapter.md
docs/transformation/PHASE31_3_1_EXACT_ID_APPLICATION_ADAPTER_ARCHITECTURAL_DECISION_CLOSURE_GATE_REPORT.md
```

The known Sidebar whitespace and every unrelated entry modification remain
unchanged. Nothing was staged, committed, stashed, reset or deployed.

## 22. Promotion predicates and final verdict

```text
architectural_decision_explicit=true
ADR_created=true
ADR_consistent_with_phase31_3=true
phase31_3_machine_spec_unchanged=true
migration_0024_absent=true
behavioral_equivalence_contract_explicit=true
ephemeral_only=true
non_generic=true
least_privilege_explicit=true
phase29_reuse=false
runtime_adoption=false
database_effects=0
P0=0
P1=0
```

`PHASE 31.3.1 — PROMOTED`

This closes only the architectural documentation inconsistency. The future
Phase 31.4 must demonstrate parity before Publication and complete retained
closure before teardown. No future result is asserted here.

### Frozen file-byte hash ledger

All paths below are relative to the exclusive workspace. Every listed hash is
both the captured entry value and the verified exit value. The historical
reports block lists the directly relevant Phase 31 lineage; the inventory
summary covers all 47 pre-existing Phase reports. Other blocks enumerate their
complete category membership. Python caches are not evidence artifacts.

### foundation_migrations_0001_0023

```text
0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51  backend/foundation/migrations/0001_foundation_tenant_projection.py
1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537  backend/foundation/migrations/0002_projection_organization_user_foundation.py
dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc  backend/foundation/migrations/0003_eventing_immutable_audit_foundation.py
045043275245e5d8068a8e03d122f5fe34b8f9f60b020336e61881550ecea125  backend/foundation/migrations/0004_qms_harmonized_context_foundation.py
96ab33a18252dc0c2e6142f7afdc02a165349d15d50b290b4092c844a1996e86  backend/foundation/migrations/0005_risk_opportunity_objective_foundation.py
033242bd6fe801da0b090a332b9f6d1b07dba77027a0334d1830e845cd51aa95  backend/foundation/migrations/0006_change_performance_measurement_foundation.py
c7f6a2030c9155714093a21fadb571a1cdeb8a121be5598540d4807af62283ec  backend/foundation/migrations/0007_document_evidence_foundation.py
285aecb34d5f7e8c1a1273c9622cde7933809949ac7bdbfca04e577e9e762032  backend/foundation/migrations/0008_evidence_coverage_normative_core_foundation.py
412c645974635959c74a446f64dc0a9b6dfd2a1a50a6a2e346698850e998effc  backend/foundation/migrations/0009_knowledge_layer_foundation.py
c4f37a9a3a8d0d20a049e4e1cc9c0e04feb947cbeec9cea18fa89b7964f57b79  backend/foundation/migrations/0010_governed_recommendation_foundation.py
cdb23edcad75e8a8781815dac847359a368b64d8ea4b607a40d01d5296c863a2  backend/foundation/migrations/0011_agent_definition_run_provenance_foundation.py
7f280e24a8e95858b8144aa6a85fc645245aa2c2d3c2ad5700dfbe19ac0f0fdc  backend/foundation/migrations/0012_agent_decision_human_decision_gate_foundation.py
06177fde1c25d884602a41d03df6d2625e8d15df18d7c66bffdb047348abf34b  backend/foundation/migrations/0013_action_execution_preparation_authorization_foundation.py
ee0e42a7d45803f633ca40d9b0ca20987a20acfdaf3452ee81d721cec29ada33  backend/foundation/migrations/0014_action_execution_synthetic_foundation.py
5e297591c8096938c90b6748d0d3ed22a8099cf8f4537e7f65f8bc6fa5beaba3  backend/foundation/migrations/0015_first_controlled_qms_mutation_poc.py
e922ff20285751193382a17d9fe7e71726511bff659f4e66b97748e6ad43cdd5  backend/foundation/migrations/0016_controlled_execution_recovery_hardening.py
580f16d1cdb10c30bae8f3e3c1667c3c4d2552b895fc9dea053d2c9b6adfaa38  backend/foundation/migrations/0017_effectiveness_check_foundation.py
703a85885a67df953f38ef35302205caeddea249104683f4f751ab20ece0696b  backend/foundation/migrations/0018_governed_learning_foundation.py
c188b638124404bba10cae4c94a678053d49d7a1d07c6e455a48e46524064b50  backend/foundation/migrations/0019_learning_proposal_review_application_authorization_foundation.py
491f21d3422c9c9a5866520f6623d3b9c9bea2139083f0128495dd7207d19894  backend/foundation/migrations/0020_exact_learning_delta_target_operation_contract.py
e796910c1660f701c3457b020792a158c06d3e58135a7ebba1728bd8b33c7a97  backend/foundation/migrations/0021_first_governed_knowledge_rule_application_poc.py
afefd7100a18e5c7324efaeb1af656225b309fd86f08673a8742f7f9f6c2e618  backend/foundation/migrations/0022_inert_rule_publication_activation_runtime_adoption.py
bb9889af836ae1e92ccf75b868c4c6a8c1ab9ba1e7d63464a2cbd749a872e642  backend/foundation/migrations/0023_retained_synthetic_source_reference_application.py
```

### phase31_3_five_artifacts

```text
44535b47bda30a4319903d8b9f10be04890b4d9085c8955d57916f3616d9588d  docs/governance/COMPLETE_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_LIFECYCLE_POC_POLICY_V1.md
683f7c83ff3e3e16733d63288d317f8b3a14fe9e5bfaf2e86b0cf2e86b6ab6ca  docs/governance/fixtures/PHASE31_3_COMPLETE_RETAINED_SYNTHETIC_LIFECYCLE_SPEC_V1.json
e458cd0bb7eb11f96ce8723b0ab4dea97e4ca60b0e47a6f7e1fb1f38cef66d6b  docs/governance/fixtures/PHASE31_3_COMPLETE_RETAINED_SYNTHETIC_SOURCE_V1.txt
d3455bc64957ef1aab5f618e552d9276bd6fd60e0b1ce2e7a8068e5c14c8917a  docs/governance/fixtures/PHASE31_3_EXPECTED_RETENTION_CLOSURE_V1.json
d5e1960801772af74d491c9c6f69a877b79f1e26b937701cf1a239114b37bf1c  docs/governance/fixtures/PHASE31_3_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V1.json
```

### authoritative_sources

```text
30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6  docs/transformation/source-artifacts/ISO_SMART_AI_Aristas_Red.csv
11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3  docs/transformation/source-artifacts/ISO_SMART_AI_Arquitectura_Completa.mmd
e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa  docs/transformation/source-artifacts/ISO_SMART_AI_Arquitectura_Completa_Lucidchart.drawio
de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e  docs/transformation/source-artifacts/ISO_SMART_AI_DDL_PostgreSQL.sql
8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c  docs/transformation/source-artifacts/ISO_SMART_AI_Especificacion_Inicial_Integrada_v1_2026.docx
952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5  docs/transformation/source-artifacts/ISO_SMART_AI_Mapa_Maestro_Arquitectura.xlsx
c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb  docs/transformation/source-artifacts/ISO_SMART_AI_Mapa_Maestro_Datos.json
ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3  docs/transformation/source-artifacts/ISO_SMART_AI_Nodos_Red.csv
29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8  docs/transformation/source-artifacts/ISO_SMART_AI_OpenAPI.yaml
eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db  docs/transformation/source-artifacts/LEEME_Importacion_ISO_SMART_AI.txt
```

### prior_ADRs

```text
50d01234ab08574a08e14caef63af29bf3cc01ea7dd563cfbe054af4950e9952  docs/adr/0001-modular-monolith-incremental-transformation.md
507e94fa2c3fff0c277f149a8a1529e551a9ac4a6560300792faf177e861c520  docs/adr/0002-adminapps-control-plane-boundary.md
bd73915f84f0194c48b97dbefac66700df132ebb76d50fc3f1f20f047fa7e9d3  docs/adr/0003-postgresql-rls-and-evidence-graph.md
eb534df58c2316c9825956698669a7777eae5a2de5c5c6844b5d25eb50729b3d  docs/adr/0004-transactional-outbox.md
e5265fc25b9da0622245e2d77ba5c33d928b066afca69f9af574b2cf285d207e  docs/adr/0005-governed-agent-runtime.md
734bc3df9bb2e9126de9bb9afcb485f589cf3b3386f0236403dbed063b75b2b5  docs/adr/0006-contract-first-openapi.md
093754f60206e07a53a7c8cccbb7594e43f0dfe71a615a95c83713282b999a92  docs/adr/0007-first-controlled-qms-domain-action-adapter.md
32a69a364966c27c45f5b04aaecc890677880158b7e2c65cb10b63e9c56036b0  docs/adr/0008-first-controlled-qms-action-product-policy.md
485f8943e2ddfdb2ff69d122a6535643debe17a2edc20d268b6fedb85ee99451  docs/adr/0009-transactional-domain-command-composition-least-privilege-executor.md
3a558515ea95872b6f5f131cb291e198bd022a33c6797b950eb81df7dabc4ca5  docs/adr/0010-controlled-execution-recovery-retained-history-policy.md
d241d8378a6ea5c94652ca26e44c00a63710a2ca7e338d4ed6071d0e260cc542  docs/adr/0011-effectiveness-assessment-governance-operational-readiness.md
4fd6b330081ad4cd24bb55792bf10e9529033156c43d70eba0868be25a403fd0  docs/adr/0012-governed-learning-proposal-review-target-application-boundary.md
8fa5852a3cabf822c5213ae10bcae2a61f3910233ff1d915d4d1e1545df6a827  docs/adr/0013-knowledge-layer-rule-lineage-head-runtime-effective-separation.md
fa0e376e802f80e95d3961fabf8f6fe5e337f4b312062123ffd45c31bb300952  docs/adr/0014-separate-knowledge-layer-rule-publication-activation-runtime-adoption.md
57da49dff842349af8a7f3720595d858e96742d782bfe414174f84b8a1f3efea  docs/adr/0015-retained-cross-phase-evidence-and-synthetic-publication-fixture.md
8a6ceb5d210045f012bba6b0e5ace378da8cbfe4f77a20f34be6009e4d5f0745  docs/adr/0016-historical-fact-rematerialization-eligibility-and-transitive-retention-closure.md
```

### historical_evidence

```text
9272458cf9dc54f4f722b02502e5e85e9869cebb5e488f0ff15da82e77c07edd  docs/governance/evidence/PHASE28_3_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_CREATED_AND_RETAINED_V1.json
b8a7c9d5a5e423e03c25819d8715e00913edfabdeef57c6611a4906849c34536  docs/governance/evidence/PHASE28_3_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_DISPOSITION_V1.json
57633c70e0d66e2f1a7efbec0f06947cabadc1d4e0f117ca1f0dc4c305dbae9f  docs/governance/evidence/PHASE29_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_DISPOSITION_V1.json
fade372ec41dbeff118ddbb41cd154f8e8adb34799492a56f5e8d14db7e54b72  docs/governance/evidence/PHASE29_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_V1.json
```

### historical_reports

```text
fc0a48200e96301adcdd1cd62d0e22a4c3f8804307fc9ccc632348190648282e  docs/transformation/PHASE31_1_EXACT_RETAINED_PUBLICATION_CURATION_AUDIT_EVIDENCE_BLOCKER_CLOSURE_REPORT.md
efe192d790f165858f7cc57051ce73b5c9ae4c703583a801803ce300510806f1  docs/transformation/PHASE31_2_UNAVAILABLE_HISTORICAL_TRANSITIVE_DEPENDENCY_GOVERNANCE_DECISION_GATE_REPORT.md
fc5f16abab801570aefd313b87cae1805f3e5067e73d01acebebce9519724a8f  docs/transformation/PHASE31_3_NEW_COMPLETE_RETAINED_SYNTHETIC_LIFECYCLE_DESIGN_AUTHORIZATION_GATE_REPORT.md
a2909cd47186bef32213f5508596693759fcb860d29a437ab84daee55a534daa  docs/transformation/PHASE31_FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_ACTIVATION_EPHEMERAL_POSTGRESQL_18_6_POC_REPORT.md
```

### existing_governance_policies

```text
44535b47bda30a4319903d8b9f10be04890b4d9085c8955d57916f3616d9588d  docs/governance/COMPLETE_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_LIFECYCLE_POC_POLICY_V1.md
29829c38745db67985fb1523837c79276508bdc9d2136b64442ea238ed13566f  docs/governance/CONTROLLED_QMS_ACTION_POLICY_V1.md
3e2f2b5b3f335bcb425c4b3d8043c2b541de56b0a7b14fbc63b8f48e4392758f  docs/governance/EFFECTIVENESS_CHECK_POLICY_V1.md
43c67505ec3e3d9df0d306012e2036ced7cf437de703e8ff95b709a7af08756d  docs/governance/FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_ACTIVATION_POC_POLICY_V1.md
1d6352eaac748fff42098242b39db63e5f446140cfc935e961eb078d40010ed8  docs/governance/FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_CANDIDATE_POLICY_V1.md
0dfa36804827f272ac7e289beab6e876d27af78b8ae06d3b8a5b5d46b9db8289  docs/governance/FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_POC_POLICY_V1.md
04458c4f1ccead125dd98ddac946ec9d77f8b0212412d13128355b10129c875c  docs/governance/GOVERNED_LEARNING_IMPLEMENTATION_AUTHORIZATION_V1.md
7d9c2fe30548bd18d390d119889c87a93595ac281fa3326691fe486bee49c4ec  docs/governance/GOVERNED_LEARNING_POLICY_V1.md
2d5beaebd5b2df1378c0f425354b45d52ff23dd1a5d158adad46572f7656c514  docs/governance/GOVERNED_LEARNING_PROPOSAL_REVIEW_APPLICATION_BOUNDARY_V1.md
7d5ed091f0d2c163dbf7b6b276e2978afd8086083435002a87270d4f11948f8d  docs/governance/HISTORICAL_LIFECYCLE_EVIDENCE_AND_TRANSITIVE_RETENTION_CLOSURE_POLICY_V1.md
1a5f7c7838c62ba76837c26fcfa4d29655294810f74afed33fdcf69dc373bb79  docs/governance/KNOWLEDGE_LAYER_RULE_GOVERNED_SOURCE_REFERENCE_APPLICATION_POLICY_V1.md
efdd4d8a679c7f18762bfe79c3e876e970f81fedb2848ef5cbf21e7aeb858556  docs/governance/KNOWLEDGE_LAYER_RULE_PUBLICATION_ACTIVATION_RUNTIME_ADOPTION_POLICY_V1.md
263003d342e6bf7a2b56c25dbbb230296b81280a1da45eb347b00898e3231e92  docs/governance/KNOWLEDGE_LAYER_RULE_RUNTIME_ADOPTION_AND_OPERATIONAL_REPAIR_DESIGN_V1.md
```

### protected_implementation

```text
1da64d5f1c8248a2c2e2e9cc586424bde185c85efd467923be28d5c1f2d170ba  backend/backend/settings.py
6767e2098365536b88d4d8e9afdaef0f8b796383c79d7f40e0e0ea91b964ec2d  backend/foundation/agent_runtime.py
461459401abb354b22c42eec05dcd9805e4fd7800554c67b96aee8885c6734ef  backend/foundation/audit.py
c7620cdfb0b51a0c1e022358dcbdae8a7e56b363e182dc09aa11ec675ecf95b8  backend/foundation/eventing.py
99d228984efe4bba15c76f91e157f2ddd66d8aec9b5bf153a21c095fd57ed8cf  backend/foundation/governed_learning_application.py
a7b0477f48120b852d9ec510d30e85d4700f5c0ba970e3ed3c9e244b1be4d7e9  backend/foundation/knowledge_rule_release.py
9dd94c945dd0c256c3872e82b45760b06c066a4364e3dc3d833d56c09645c244  backend/foundation/models.py
ff15b1b1a6eee128154168a89c52422061a8ea0bc41ab6667bccf2719c758403  backend/foundation/phase29_publication_evidence.py
a6c6cad4b1b0c029ba39eb91ea4cf7aae3ce2c111ac580643fd3a1b9faa3cffd  backend/foundation/phase31_activation_preflight.py
0211b25081cc90f61d6497faf101fad42d5a92cd960f5463b2df1efb09f0df95  backend/foundation/postgres_phase26_harness.py
b089ddf3fc37456041677d120348cb01e036897fbc57357f94dcb05888aeb9c8  backend/foundation/postgres_phase27_2_harness.py
63ceecd685570e33bea9a8abf56a12d98f297f6859d9c45b247291889442b517  backend/foundation/postgres_phase28_3_harness.py
9f6ba75d92ed043e2a67e0c83051770613f40ed40a2e0d8067401a46ad0bcb70  backend/foundation/postgres_phase29_harness.py
655fbdd18437f3d04a838c4dfad0b5b5fb3f6cc2e3d53d29fcc21a22acc6648c  backend/foundation/recommendation.py
080fe74e50bf84655d20b170363529f5a9ee69dad2a112ded48a5418ffa661dd  backend/foundation/test_phase31_activation_preflight.py
e11ef3322b1d8ea5621072cb978f566d2c7ef90496eee7835506e7c99874741c  frontend/src/components/Layout/Sidebar.jsx
```

## 23. Exactly one continuation prompt

```text
NEXT_CODEX_PROMPT

ISO SMART AI — PHASE 31.4 — NEW COMPLETE RETAINED SYNTHETIC LIFECYCLE — ISOLATED EPHEMERAL POSTGRESQL 18.6 CREATION-THROUGH-ACTIVATION POC

Work exclusively in /home/felipe/proyectos/isosmart. Run git status --short first, read AGENTS.md, and preserve all unrelated work, including frontend/src/components/Layout/Sidebar.jsx:28. This is a new isolated synthetic experiment, not recovery of any historical candidate. Read the complete Phase 31.3 and Phase 31.3.1 reports and ADR-0013–0017, migrations 0021–0023, the governed-learning Application service and the relevant Phase 26/28.3 harnesses and least-privilege/RLS architecture.

Consume these exact authoritative inputs before any database work:
1. docs/governance/COMPLETE_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_LIFECYCLE_POC_POLICY_V1.md
2. docs/governance/fixtures/PHASE31_3_COMPLETE_RETAINED_SYNTHETIC_SOURCE_V1.txt
3. docs/governance/fixtures/PHASE31_3_COMPLETE_RETAINED_SYNTHETIC_LIFECYCLE_SPEC_V1.json
4. docs/governance/fixtures/PHASE31_3_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V1.json
5. docs/governance/fixtures/PHASE31_3_EXPECTED_RETENTION_CLOSURE_V1.json
6. docs/adr/0017-ephemeral-exact-id-governed-application-adapter.md
7. docs/transformation/PHASE31_3_1_EXACT_ID_APPLICATION_ADAPTER_ARCHITECTURAL_DECISION_CLOSURE_GATE_REPORT.md

Verify the five-artifact byte hashes against ADR-0017 and the Phase 31.3/31.3.1 reports. Require ADR-0017 SHA-256 82501ef34edc6d7e76e0971d3d2607c58f229a1dd4dd26696dd227fb7e994edb, a promoted Phase 31.3.1 report with P0=0/P1=0, migration-set SHA-256 cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc, migrations 0001–0023 unchanged and 0024 absent. Preserve all historical policies/reports/evidence, authoritative sources and protected runtime/application files. Capture the finalized Phase 31.3.1 report's byte hash as an immutable execution input. Any changed/missing input stops the gate before database creation; never reinterpret the frozen execution specification.

Execute at most one retained creation-through-Activation lifecycle under the frozen experiment a3f8fd64-af24-5b31-977a-bcaf8146c563. Source/support rows, root bc5f4f17-294d-5abd-b27b-2d296921ffdf, candidate a55716fa-63c7-54eb-bda2-9c9666613b1a, Proposal/Delta/Review/Decision/Authorization, actors, SOD, hashes, canonicalization, policies, capabilities, claims, events, Outboxes, Audits, Receipt and traces must be exactly those specified. Fill only already-declared fresh authority/capability/timestamp/live-schema slots under their frozen rules. Do not choose new retained IDs, alter source material, silently amend a target hash or weaken a constraint to make execution possible. Any inability to satisfy an exact binding is a blocker.

Use only a dedicated isolated ephemeral PostgreSQL 18.6 environment, with no production/staging/shared database or external service access. Implement/install the exact-ID Application adapter only there under ADR-0017; do not create migration 0024 or a permanent application/API/runtime surface. Its dedicated owner must be NOLOGIN NOSUPERUSER NOINHERIT NOBYPASSRLS and non-table-owner; functions use search_path=pg_catalog, qualified objects, no dynamic SQL, PUBLIC EXECUTE revoked, and only the exact ephemeral Application executor receives the callable entry. The executor has no direct DML, role escalation, private primitive, Publication, Activation, RuntimeAdoption, repair or capability-control access. Preserve RLS, immutable guards, frozen grants and exact trusted authority binding.

BEFORE PUBLICATION, demonstrate the blocking equivalence contract: exact-ID adapter behavior == promoted 0021 domain semantics except explicitly authorized identity preallocation. Both paths must use frozen 0001–0023, including 0023's already-promoted synthetic grammar. Run deterministic comparable reference/adapter trials in isolation, retaining raw live evidence; the reference must execute the actual promoted primitive. Compare validation outcomes, resulting candidate material, full-row/full-material hashes, semantic fingerprint, lifecycle hash, lineage/predecessor, source transition, event type/schema/material, Outbox, both Audits, Receipt, rollback, idempotency, stale-target, concurrency, TOCTOU and security/ACL behavior. Follow ADR-0017's bounded seven-output-ID comparison and independently verify original canonical hashes and declared fresh slots. The adapter must still accept only the exact frozen candidate/graph; comparison outputs cannot replace retained identities or evidence. Any unproved parity, extra behavioral divergence or failed test stops Phase 31.4 BEFORE Publication. Do not broaden the exception or rewrite the specification.

After parity passes, execute only exact source/support/root -> governed Application candidate s1 -> separate native Publication cf4db0d2-a312-5a44-91cf-6e14f5cd600e -> first Activation 676ad5e4-e167-5336-93ae-5a9f1d4388d3 with predecessor NULL. Fresh server-resolved authority, exact actor/permission/global scope/MFA/access/policy and independent enabled capabilities must pass admission and immediate precommit checks. Execute every frozen SOD, idempotency, lock-order, concurrency, stale-predecessor, TOCTOU, rollback, reconciliation and hostile matrix. Each failure must produce the required zero deltas; classify partial graphs INCONSISTENT, never infer commit from target state, steal a claim, retry blindly or repair automatically. Publication closure must pass before Activation.

Require full TRANSITIVE RETENTION CLOSURE / v1 from both the live schema/FK snapshot and the frozen semantic registry. Retain complete canonical material for every mandatory local dependency and frozen provenance for every external authority, including all source/support, root, candidate, Application, Publication and Activation graphs, policy, capability, idempotency, compatibility/release evidence, manifests/dispositions and zero-downstream assertions. Retain EVERY mandatory normative.curation_audit row with all eight fields, including root creation, Application ff75b1d0-a2ea-5eae-9064-b9114496047a and Publication 5fa5038d-3042-481f-8162-e1144eebc815. UUID-only material, expected fixtures, summaries and substituted governance Audits are not retained evidence. Re-read generated artifacts live, canonicalize, hash, include them in the closure graph, export before teardown and cross-check against the frozen specification.

Follow the exact order: execute -> compute closure -> verify -> export/fsync -> independent live re-read in a new read-only transaction -> compare material/hashes/cross-links -> assert closure_complete=true, export_matches_live_graph=true, reconstruction_required=false -> frozen pre-teardown disposition -> authorize teardown -> remove the environment and executable adapter/roles/grants -> offline verify without reconstruction. Incomplete closure blocks teardown by default; preserve the live isolated environment for inspection. Only a separately authorized frozen dual-control override may destroy incomplete evidence, permanently non-rematerializable and operationally ineligible, never PASS. Verify environment/adapter removal after authorized teardown. Offline success must be exactly CREATED=true, APPLICATION_GOVERNED=true, PUBLISHED=true, ACTIVATED=true, RUNTIME_ADOPTED=false, RUNTIME_EFFECTIVE=false, database_reconstructed=false, retention_closure_complete=true, reconstruction_required=false.

Never rematerialize, repair, import, reconstruct or reuse Phase 29 Publication e97576de-d4ef-520d-8592-d376ed401221 or missing normative.curation_audit 12d811ab-c3b4-4615-8972-75008a36e327. Phase 29 remains HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE with RETENTION_CLOSURE_BREACH. No continuity claim or Phase 31 retry. RuntimeAdoption and Phase 32 remain prohibited: zero adoption rows/events/Outboxes/Audits, adoption-authority use, resolver invocation and runtime cutover. Do not mutate ModelPolicy, AgentDefinition, autonomy, runtime configuration/selectors or normative content; authorize automatic learning/compensation; contact AdminApps/MedSupplier/providers/external APIs; deploy; claim certification; or cause external business effects. Successful adapter use grants no production, persistence, general preallocated-ID, migration replacement or generic API precedent.

Retain a Phase 31.4 report and complete evidence with exact commands, test counts, raw comparison provenance, hashes, zero prohibited effects, closure/export-live/teardown and post-teardown verification results. Run applicable PostgreSQL acceptance and offline/Foundation/Django/hash/git hygiene checks only inside the authorized isolation constraints. Return NOT PROMOTED for any P0/P1, unproved parity, frozen-contract mismatch, missing closure member, failed live comparison, reconstruction need, unauthorized teardown or prohibited effect. Do not advance to RuntimeAdoption.
```
