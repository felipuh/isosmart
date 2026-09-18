# ADR-0019: Native identity resolution for Phase 31.4 V2.5

- Status: Accepted for the V2.5 offline regression and authorized Stage B
- Date: 2026-09-17

V2.4 remains historical and immutable. V2.5 models identities created by the
product as `CAPTURE_NATIVE_OUTPUT`; consumers use `REFERENCE_RESOLVED_BINDING`
after capture. Initial Opportunity creation captures `uuid4()` and binds
`lineage_id` to that captured ID. ActionPlan preparation captures its native
UUID. A controlled Opportunity successor captures the native UUIDv7 and uses
runtime invariants for lineage, revision increment, and predecessor.

The resolver executes native work first, retains every authoritative output,
resolves references, evaluates acyclic invariants, materializes the complete
graph, and only then canonicalizes and hashes it. Pre-execution comparison of
random UUIDs is deliberately excluded; exact comparison after resolution is
required. No product API is changed to accept predetermined UUIDs.