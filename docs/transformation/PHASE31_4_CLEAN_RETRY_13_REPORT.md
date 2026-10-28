# Phase 31.4 V2.5 Clean Retry 13

## Verdict

**NOT_PROMOTED.** Historical/current guard reconciliation is complete and the full offline gate is green. Retry 13 was then executed with fresh PostgreSQL 18.6 resources. Bootstrap, migrations, and Stage EXT passed, but live V2.5 execution reproduced the Retry 12 AgentDecision capture blocker at `ACTION_PLAN_PREPARATION` after 14 of 33 phases. Teardown passed.

## 23 legacy failures

All `23/23` baseline failures were classified and resolved: Category A `0`, Category B `22`, Category C `1`, Category D `0`, Category E `0`. The failure-by-failure assertion, expected/actual values, artifact, generation, scopes, cause, disposition, and post-fix result are recorded in `docs/governance/evidence/PHASE31_4_RETRY13_LEGACY_FAILURE_INVENTORY_V1.json`.

## V2.4 historical guards

**PASS.** The exact V2.4 contract SHA remains mandatory. Its historical migration manifest contains exactly migrations `0001`–`0023`, validates their existing hashes and aggregate hash, and makes no claim that successor migration filenames cannot exist. V2.4 was not modified.

## V2.5 current guards

**PASS.** The current manifest separately protects 24 migrations plus material identity, Stage EXT, PostgreSQL bootstrap, runtime composition, authority, native-execution, binding, and generation-guard sources. Each protected source has a semantic role and approval evidence. Unrecorded current drift fails closed.

## Migration 0024

`0024_adminapps_ingress_receipt.py` is retained as legitimate Stage EXT successor architecture. It supplies the pre-projection receipt, organization-create idempotency, RLS, grants, and reversible teardown. It is absent from the V2.4 historical manifest and present in the V2.5 current manifest.

## Protected source hashes

The V2.4-era `backend/backend/settings.py` hash `1da64d5f...170ba` remains in historical evidence. The V2.5 current hash is `f2630ca3...ccc8`, linked through `predecessor_sha256` to ADR-0020 and Retry 10 evidence. No historical hash was overwritten.

## Full regression

`250` tests executed: `250 PASS`, `0 FAIL`, `0 ERROR`, `0 SKIP`. This includes six integrity-generation anti-regression tests in addition to the original 244.

## Offline P0/P1

Before resource creation: `P0=0`, `P1=0`.

## Retry 13

**EXECUTED / NOT_PROMOTED.** Two fresh pinned PostgreSQL 18.6 environments were created. No Retry 14 was allocated and no prior retry state was reused.

## PostgreSQL and migrations

- role bootstrap and database target guard: `PASS`
- AdminApps migrations: `61` applied, `PASS`
- ISO Smart migrations: `92` applied, pending `0`, `PASS`
- fake migrations: `0`; manual schema patches: `0`; SQLite target: prohibited

## Stage EXT

**PASS.** The fresh chain produced distinct live AdminApps tenant, local tenant projection, QMS organization, and QMS process identities. Persisted process, tenant, and organization references matched exactly.

## Live phases

`14/33` executed and all 14 executed phases passed. Execution then failed closed before `ACTION_PLAN_PREPARATION` because the native AgentDecision capture did not exist.

## Captures

Expected native captures: `565`. At failure, one phase-native Opportunity capture had been registered; the full native capture set was not executed. Registry total including handed-off upstream records was `5`. Result: **incomplete**.

## Upstream captures

Expected contract fields: `5`. Exact contract fields were registered for tenant projection ID, organization ID, and process ID (`3/5`). The handoff registered the external actor under `adminapps_user_id` rather than the contract's local UserProjection ID, and did not separately register `adminapps_tenant_id`. Result: **incomplete**.

## Retry 12 P1

`P1-RETRY12-V25-ACTIONPLAN-AGENT-DECISION-LIVE-BINDING-MISSING` remains **OPEN / LIVE_REPRODUCED_RETRY13**. The prior `CODE_REMEDIATED / LIVE_CLOSURE_PENDING` assessment was disproved: the phase registry does not invoke the prerequisite native AgentDefinition, AgentRun, Recommendation, and AgentDecision chain before resolving ActionPlan inputs. Literal fallback remains correctly forbidden.

## Graph

Structural contract: `118/118` members and `1664/1664` fields, PASS offline. Live resolved-graph validation was not reached.

## Exact comparison

Not executed; mismatch count cannot be claimed.

## Security / A3 / transactions / events

PostgreSQL role bootstrap and Stage EXT security passed. Full native authority/A3, transaction, controlled revision, reference/invariant, and event/outbox/audit validation were not reached.

## V2.4 SHA

`a102d278bf2e5ca6e9b8bf282f5402a54f52d4690beed2ecbed5145c56539387` — **PASS**.

## Teardown

**PASS.** Both Retry 13 containers, volumes, and isolated networks were removed and post-teardown inventory verification found no Retry 13 resources.

## Promotion

**NOT_PROMOTED.** Live P0=`0`, live P1=`1`. Required 33/33 phases, 565/565 native captures, 5/5 upstream captures, live Retry 12 blocker closure, resolved graph, exact comparison, A3, transaction, and complete event/outbox/audit evidence are absent.
