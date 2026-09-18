# Phase 31.4.4 supporting fixture producer contract V1

The future producer is a parameterless, exact-scope operation for experiment
`a3f8fd64-af24-5b31-977a-bcaf8146c563`. It cannot accept an arbitrary table,
model, UUID, operation, actor, JSON value, target or field list. Its complete
write set is the subset of `future_row_universe` whose producer begins with
`phase31.4.4-exact-support`, `phase31.4.4-isolated-catalog`,
`phase31.4.4-agent-provenance`, `phase31.4.4-controlled-opportunity`,
`phase31.4.4-effectiveness`, or `phase31.4.4-learning-signal`.

For each named operation the producer owns the connection and transaction:
BEGIN; bind the trusted tenant, actor and trace inside that transaction; run
native or ADR-0018 fixture-equivalent validation; write only declared rows;
repeat tenant, authority, capability, predecessor, hash and leaf validation
immediately before commit; COMMIT; reread and retain outputs before their next
consumer. It never wraps existing trusted-tenant services in an outer
transaction.

The owner role `phase31_4_4_support_owner` is NOLOGIN, NOSUPERUSER, NOINHERIT,
NOBYPASSRLS and is not a table owner. The executor
`phase31_4_4_support_executor` is LOGIN, NOSUPERUSER, NOINHERIT, NOBYPASSRLS
and is not an owner. Search path is `pg_catalog`; all objects are qualified;
dynamic SQL, role escalation, generic DML, table ownership and PUBLIC EXECUTE
are forbidden.

The machine contract's table matrix is authoritative. Each tenant table gets a
named ephemeral policy limited to both exact roles and the one fixture tenant;
`USING` and `WITH CHECK` both require the trusted tenant setting. Hostile tests
must prove cross-tenant denial. Grants without the applicable policy fail. All
ephemeral policies and functions are removed at teardown.

Ordinary deterministic fixture rows use enumerated ADR-0018 identities.
Immutable audit log IDs remain native UUIDv7 outputs and are retained after
commit. Migration 0022 children retain its MD5/suffix algorithm. ADR-0017 is
used only for its seven Application outputs.

