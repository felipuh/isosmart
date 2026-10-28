# LAB05-C1-R3 — integrated ISO Smart / AdminApps HTTP SSO

Date: 2026-10-28 (America/Costa_Rica).

## A. Executive Verdict

**LAB05_C1_R3_ISOSMART_HTTP_E2E_PASS**. Real ISO login, CENTRAL RS256,
live introspection, User/UserProfile persistence, protected endpoints, tenant
isolation, durable revocation and fail-closed behavior passed. R1/R2 are accepted
baselines; neither acceptance suite was rerun. Full machine-readable evidence:
`docs/security/LAB05-C1-R3/evidence.json`; request matrix: `HTTP_MATRIX.md` there.

## B. Real Integrated Architecture

AdminApps SSO and two ISO WSGI instances listen on separate loopback TCP ports.
Two new disposable PostgreSQL clusters use private Unix sockets and SCRAM runtime
credentials. Central runs as `lab04_sso`; ISO A/B authenticate directly as
`iso_runtime_a` / `iso_runtime_b`. ISO never uses the owner principal at runtime.
Maintenance creates schema and synthetic fixtures before serving traffic.

The R1 registered client, issuer, audience, kid, product `ISO_SMART`, technical
credential and ephemeral RSA key are reused. Only the public CENTRAL keyring is
exported to ISO. A separate ephemeral LOCAL key signs the existing cookie session
envelopes. Synthetic passwords, proofs, keys and cluster data are not retained.
No external HTTP destination or production setting is used.

## C. Central Authentication HTTP Results

ISO's existing `central_request` performs actual requests to AdminApps login and
introspection. The issued CENTRAL proof is independently verified for RS256, kid,
issuer, audience, client, product and tenant. The local envelope expires no later
than its central proof. Real introspection validates lifecycle and product access.
Unregistered clients/credentials, wrong audience/product, forged technical headers,
invalid signatures, issuer/client/product/tenant mismatches and altered central
roles are rejected. Both LOCAL and embedded CENTRAL negative inputs are covered.

## D. ISO Smart Login and Protected Endpoints

The existing CSRF and login routes issue HttpOnly access/refresh cookies. Real
`central_auth.sync_identity` creates User/UserProfile/Organization projections.
`/api/auth/me/` returns the correct subject, tenant and role. ResourceViewSet creates
a resource under tenant A; B cannot list/retrieve A's object or create a resource
with its viewer role. A foreign object lookup returns 404 after the real filtered
handler; authorization denials and revoked calls do not enter protected handlers.

## E. ORM and RLS Results

R2's real-model projection is reused, extended only by `resources.Resource` and
the lab-only `lab_tenant_authority` table. ISO has no billing tables or migration
recorder. No consumer migrations are executed or faked. Identity catalogs remain
global as documented in R2; memberships, organizations and resources have forced
RLS. The shared subject keeps distinct roles in A/B without elevation.

The authority table maps SQL `session_user` to central tenant. Runtime can only
read this mapping. Middleware compares it to the configured instance tenant and
actual SQL principal on every request; existing proof validation checks the
centrally authenticated tenant before projection. A deliberately mismatched
mapping returns 503 without handler execution or writes. Headers cannot select a
principal. Runtime queries are observed to contain no SET ROLE. SQL denies schema
creation, RLS disabling, TRUNCATE, privilege escalation, mapping changes and
cross-tenant writes. Evidence includes table/identity-column grants.

## F. Revocation and Fail-Closed Results

AdminApps logout durably marks the session revoked with exactly one logout outbox
record. The exact earlier cookie/proof is replayed: protected GET/POST fail, no
handler runs, and every consumer table snapshot is unchanged. Each request uses a
new PostgreSQL connection, verified by distinct backend PIDs. Denial survives a
real AdminApps process restart; an unrelated valid tenant-B session recovers.

Removing central scopes revokes the existing session; restoring scopes requires
reauthentication. Killing the central process makes protected GET/POST and login
return 503. Even an intentionally installed matching local password cannot bypass
the authority. No authentication, ORM, HTTP or persistence mocks are used.

## G. Implemented Corrections

The first real integration defect was `/api/auth/me/` returning 500 because it
ordered UserProfile by nonexistent `is_primary`. It now queries the exact
profile/organization in the centrally validated session and fails closed if that
profile is absent. No migration or new model field was needed.

Opt-in orchestration, tenant binding, real Resource projection and observation
were added. SQL writes are narrowed to required tables/columns; unused R2 reset,
blacklist and audit table/sequence grants are removed in the R3 cluster only.
Each ISO settings instance loads its own SQL credential, not the provisioning
owner credential or the other tenant's credential.

## H. HTTP Test Matrix

The retained matrix lists all request scenarios and exact HTTP statuses, including
positive login/me/resource access; CSRF; tenant and shared-user isolation; signature,
issuer, audience, client, product, scopes, headers, central logout and outage.
Separate evidence records every real central request initiated by the consumer.
No raw token, password, private key or full response body enters this evidence.

## I. Commits and Remote SHA Verification

AdminApps baseline: `5190c9b0830fa1f85b8a9ac576e9df3d60383a21`.
ISO sanitized baseline: `1b9a50f92eb4c0c4b0658c0d2dc60225ec63c602`.
Both baseline upstream SHAs were independently verified with `git ls-remote`.
Changes are committed separately on `lab05/c1-r3-http-sso-sanitized-20261028` in
each repository. The delivery message records the final commit SHAs and matching
remote SHAs; this avoids self-referential hashes inside the commits. No history
merge, force push, empty commit or credential-bearing ancestor is introduced.

## J. Final Git Status

Publication uses only the reviewed R3 changes, after index and complete reachable
history secret audits. Final worktree/upstream status is recorded in the delivery
message. The original `/home/felipe/proyectos/isosmart` checkout is preserved;
implementation uses the existing sanitized `isosmart-lab05-c1-r2` worktree.

## K. Remaining Blockers

No blocker remains for this laboratory acceptance. Production release remains
outside scope: this is a non-migratable narrow model projection, loopback HTTP,
ephemeral configuration, one OS account and a fixed instance per tenant. Full
application workflows, production tenant routing and process/filesystem isolation
are not certified. A foreign cookie with an RLS-hidden profile currently returns
generic 503 rather than 401; it grants no access and performs no writes.

`PRODUCTION_READY = FALSE`

`PHASE31_5 = EXECUTION_HELD`

`S3_DECISION_02A_NOT_CLOSED`

`NO_DEPLOYMENT`

`NO_SHARED_DB_MUTATION`
