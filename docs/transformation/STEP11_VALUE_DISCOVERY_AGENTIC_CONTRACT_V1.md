# Step 11 — Value Discovery Agentic Contract V1

`PRODUCT_SEMANTICS_OWNER_APPROVED`

## Authority and scope

The source artifacts define onboarding Step 11 as **Value Discovery**, identify
Organizational Profile, Impact / Savings, and Purpose / Alignment engines, and
place Step 12 after Step 11. They do not define the orchestration protocol,
LLM transport, financial gate, API routes, or result schema below.

Those elements are `TECHNICAL_OWNER_APPROVED_EXTENSION`. The source artifacts
remain unchanged. This contract does not implement the later Step 17 value
roadmap.

## Architecture

One `ValueDiscoveryService` orchestrates exactly three bounded capabilities:

1. Organizational Profile Intelligence;
2. Impact / Savings & preliminary Improvement Opportunities;
3. Purpose / Alignment Intelligence.

The model receives no tools or authority. It receives only the canonical Step
10 profile and the bounded declared-purpose statement. Each response is JSON
validated server-side before an authoritative transaction can begin.

`AgentRun` cannot represent Step 11 without fabricating its mandatory
normative requirement/rule/evidence inputs. The existing `AgentRun` contract
is therefore preserved unchanged. The narrow compatible extension is the
tenant-scoped, immutable `onboarding.value_discovery_execution` record. Its
ID is exposed as `agent_run_id` for Step 11 provenance only; it is not an
entry in the frozen source-defined agent catalog.

## Provider contract

The default provider uses the existing configurable OpenAI-compatible chat
completion settings (`AI_ASSISTANT_API_URL`, `AI_ASSISTANT_API_KEY`, and
`AI_ASSISTANT_MODEL`) with JSON-object responses and a bounded timeout.
Missing credentials, timeouts, HTTP failures, or malformed responses fail
closed: no result, transition, evidence, event, or Step 12 unlock is written.

`VALUE_DISCOVERY_PROVIDER=controlled` enables the deterministic fixture only
in development or with explicit `VALUE_DISCOVERY_ALLOW_CONTROLLED_PROVIDER`.
It is labeled `CONTROLLED_TEST`, never `REAL_AI`.

## Output semantics and hard gates

All capability outputs use `ValueDiscoveryResultV1`. References are limited to
actual Step 10 fields or `organization_declared_purpose`; unknown references,
oversized lists, malformed shapes, and numeric benefit claims are rejected.

Improvement opportunities are optional and preliminary. An empty list is
valid and is rendered as `NO_GROUNDED_OPPORTUNITIES_IDENTIFIED`.

Non-monetary value is qualitative only. Financial output is always:

```text
status   = NOT_ASSESSED
amount   = null
currency = null
reason   = NO_AUTHORIZED_FINANCIAL_BASELINE
```

No estimates, ROI, percentages, hours, findings, nonconformities, corrective
actions, or Step 17 roadmap artifacts are created by this contract.

## Completion and provenance

The server verifies a signed tenant principal, a tenant-owned organization,
the tenant user projection, a complete and hash-valid Step 10 profile, the
three validated capability outputs, and a non-stale profile before committing.
The final transaction writes immutable evidence, `ValueDiscoveryExecution`,
the Step 11 transition, `onboarding.value_discovery.completed`, a
transactional outbox row, and immutable audit record. Only then does the
existing workflow make Step 12 available.

The client cannot select a tenant. Replays with the original event ID return
the original committed result; changed material conflicts; a later event after
completion is rejected. Inference occurs before the final transaction, so no
database lock is held while awaiting the provider.

## API and browser

The implementation-defined, owner-approved routes are:

- `POST /v1/onboarding/value-discovery`
- `GET /v1/onboarding/value-discovery`
- `GET /v1/onboarding/value-discovery/{execution_id}`

The browser displays server-confirmed context, explicitly preliminary
opportunities, qualitative value areas, the financial unavailability notice,
purpose observations, limitations, and the persisted server result. It no
longer marks legacy onboarding complete immediately after Step 10.

## Validation evidence and limitations

Focused schema tests cover all three controlled capability shapes, financial
hard-gate rejection, and quantified opportunity rejection. Real provider
smoke testing requires an already configured, approved provider and is not
implied by controlled tests. PostgreSQL/RLS integration and controlled browser
E2E must run through the repository-managed PostgreSQL harness before this is
adjudicated as fully validated.
