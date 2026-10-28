# AdminApps AI Financial Authority V1.1 — Implementation Readiness

**Status:** planning and acceptance artifact only. No slice is authorized to start by this document.

## Acceptance matrix

| ID | Invariant / contract section | Responsible system | Proposed implementation location | Required verification | Remaining dependency |
| --- | --- | --- | --- | --- | --- |
| FIN-01 | AdminApps sole authority (§1–2) | AdminApps | new financial authority app/schema | authority-boundary integration test | slice authorization |
| FIN-02 | registered producer only (§3) | AdminApps | integration + financial registration models | revoked/generic/cross-product credential denial | auth mechanism approval |
| FIN-03 | trusted tenant (§4) | ISO Smart + AdminApps | ISO adapter; AdminApps admission service | stale/conflict/user UUID spoofing matrix | integration authorization |
| FIN-04 | all scopes atomic (§5) | AdminApps | budget/reservation service | PostgreSQL concurrent global/product race | policy semantics approval |
| FIN-05 | decimal/currency/period (§5) | AdminApps | tariff/budget models | decimal, rollover, FX-rejection tests | tariff/rounding approval |
| FIN-06 | no double spend (§6) | AdminApps | decision/settlement constraints | duplicate/concurrent/lost-response tests | schema approval |
| FIN-07 | uncertainty retained (§7) | AdminApps + ISO Smart | settlement/evidence/outbox adapter | A–F transition and TTL tests | evidence retention policy |
| FIN-08 | immutable financial evidence (§8) | AdminApps PostgreSQL | migrations, roles, triggers, RLS | update/delete/forge/no-context denial | DBA governance |
| FIN-09 | financial RBAC (§9) | AdminApps | users/permissions/admin workflows | org admin/producer denied; SOD audit | role-owner approval |
| FIN-10 | safe v1 HTTP (§10) | AdminApps + ISO Smart | internal API/OpenAPI/client | schema, 503/timeout/retry contract tests | API owner approval |
| FIN-11 | activation prerequisites (§11) | both | controlled validation harnesses | disposable PostgreSQL evidence | operating authorization |
| FIN-12 | input bound separate (§1, §12) | ISO Smart + governance | provider adapter/bounding contract | exact-model bound proof | provider/model and input-bound approval |

## Bounded future slices

| Slice | Entry criteria | Work and tests | Exit condition | Stop condition |
| --- | --- | --- | --- | --- |
| S1 — data, immutable audit, PostgreSQL | V1.1 human approval; DBA role model approved | financial data models; append-only triggers/grants/RLS; migration tests for immutability and tenant isolation | disposable PostgreSQL proves roles, RLS, and immutable evidence | any runtime role can alter/delete/forge evidence |
| S2 — producer identity and financial RBAC | S1 accepted; credential/role governance approved | registration lifecycle; dedicated credential binding; financial permission family; revocation/RBAC/SOD tests | generic keys, customer admins, and revoked registrations are denied | authentication mechanism or separation-of-duties unresolved |
| S3 — atomic admission/reservation | S1/S2 accepted; budget policy/rounding approved | policy/tariff/budget records; serializable all-scope admission; idempotency | concurrency and replay tests prove no excess/double reserve | exact tariff/policy semantics missing or race fails |
| S4 — settlement, recovery, evidence | S3 accepted; evidence retention/reconciliation governance approved | settlement identity, A–F evidence, liability/manual resolution | evidence transition, duplicate and uncertain-use tests pass | uncertain exposure can release without proof |
| S5 — PostgreSQL concurrency/RLS and HTTP validation | S1–S4 accepted | API schema/error contract; fault/retry tests; full PostgreSQL validation | controlled validation report accepted | any ambiguity permits dispatch or cross-tenant access |
| S6 — ISO Smart integration | S5 accepted; separate integration authorization | adapter/client behind existing fail-closed boundary; projection/assertion and outbox tests | no provider call; synthetic end-to-end evidence accepted | missing input bound, provider/tariff approval, or operating authorization |

S6 does not authorize real inference. A later operating decision must separately prove FIN-12 and authorize provider execution.

## Exact prerequisites for the first AdminApps batch

1. Human approval of V1.1 and S1 scope; named AdminApps financial-policy owner and DBA/recovery governor.
2. Approved database role/ownership model, retention and break-glass audit requirements.
3. Approval of the dedicated credential-backed producer-registration approach and financial RBAC role ownership.
4. A clean AdminApps implementation branch/worktree preserving current local changes, plus disposable PostgreSQL test environment.
5. Explicit statement that the first batch is S1/S2 only and does not authorize endpoint exposure, ISO Smart integration, tariff activation, paid inference, deployment, or credentials.

