# AdminApps AI Financial Authority — Amendment 01 Decision Record

**Decision:** amend the proposal from V1 to V1.1; no runtime change is authorized.

| Amendment | Decision | Reason | Source traceability |
| --- | --- | --- | --- |
| 01 Producer identity | Add immutable `ProducerRegistration`; choose dedicated registered hashed `IntegrationAPIKey` over TLS for V1.1, explicitly not mTLS. | V1 described a principal but lacked authoritative registration and avoided a mechanism decision. | AdminApps `apps/integration/models.py` (`IntegrationAPIKey`, lifecycle/audit); V1 §3. |
| 02 Tenant assertion | Require active/complete/in-sync `TenantProjection` evidence and AdminApps-side organization/entitlement validation. | Prevent user UUID impersonation and stale projection authority. | ISO Smart `foundation/models.py` (`TenantProjection`); migration `0001`; V1 §§1,3. |
| 03 Budget scopes | Define global + tenant-product scopes, canonical locks, serializable transaction, decimal/currency/period/exposure rules. | V1 required all scopes but did not fully specify their semantics. | V1 §4; ISO PostgreSQL validation report concurrency/decimal evidence. |
| 04 Idempotency | Fix admission and settlement identities, canonical hashes, constraints, and duplicate semantics. | Prevent replay and conflicting retry effects. | V1 §§3–6; ISO migration `0042` controlled-test uniqueness evidence. |
| 05 Financial evidence | Classify A–F, durable evidence, unresolved liability, and projection linkage. | Timeouts/missing usage cannot be released by convention. | V1 §5; ISO validation report settlement/recovery results; `AIUsageProjection`. |
| 06 Database immutability | Require append-only grants, trigger enforcement, forced RLS, separated roles and governed recovery. | Application convention alone cannot protect financial evidence. | ISO PostgreSQL validation report and foundation PostgreSQL role/RLS patterns. |
| 07 Financial RBAC | Add central financial permissions separate from `IsAdmin`, org admin, and producer credentials. | Existing AdminApps generic admin permissions are insufficient financial authority. | `apps/users/permissions.py`; V1 §7. |
| 08 HTTP contract | Add v1 schemas, error/status mappings, correlation and ambiguity reconciliation procedure. | A timeout/lost response must not lead to a duplicate spend or assumed permission. | V1 §§3,6; ISO fail-closed execution boundary. |

## Adjudication outcome

The former `ADMINAPPS_AI_FINANCIAL_CONTRACT_V1_REVISION_REQUIRED` findings are addressed in the V1.1 proposal. Approval remains blocked on the named human governance and pricing/input-bound decisions; that is expected approval work, not an architectural incoherence. V1.1 does not approve implementation, provider access, or spending.

