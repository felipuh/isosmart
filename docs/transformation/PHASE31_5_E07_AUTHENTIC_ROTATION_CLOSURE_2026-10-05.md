# Phase31.5 E-07 Authentic Credential Rotation Adjudication

Date: 2026-10-05 (UTC)
Starting commit: `be3dbebee6f91cc0f36d32a0a701ca37f92c77ef`
Branch: `hardening/p0-p1-enterprise-readiness`

## A. Executive Verdict

**E-07 = FAIL_AUTHENTIC_ROTATION_EVIDENCE_REQUIRED.**

Historical credential exposure is recorded for an initial administrator
password and a development AdminApps integration API-key fallback. The
bounded current-source scan found no high-confidence literal credential in
the relevant tracked source paths. Neither fact proves that the affected
credentials were invalidated or replaced by their authorities. No authentic
rotation evidence is available in the authorized local environment.

## B. Governance Integrity

The working branch is `hardening/p0-p1-enterprise-readiness`, and the stated
E-08 closure commit
`be3dbebee6f91cc0f36d32a0a701ca37f92c77ef` is both `HEAD` at task start and
present in branch history. The existing E-08 evidence records
`E-08 = CLOSED_LOCAL_TECHNICAL_EVIDENCE`,
`E-07 = FAIL_AUTHENTIC_ROTATION_EVIDENCE_REQUIRED`, and
`Phase31.5 = EXECUTION_HELD`.

The controlling entry-gate evidence identifies
`P0-31_5-ENTRY-COMMITTED-CREDENTIALS` as open. The Phase31.5 environment
evidence says the rotation mechanism and secret-manager/reference scheme are
not defined. This adjudication does not modify the hold, reopen E-08, authorize
Retry20, or perform Phase31.5 work.

## C. Starting Git State

At task start:

- Branch: `hardening/p0-p1-enterprise-readiness`
- `HEAD`: `be3dbebee6f91cc0f36d32a0a701ca37f92c77ef`
- Latest commit: `be3dbebe Close Phase31.5 E-08 auth and worker evidence`
- Upstream: `origin/hardening/p0-p1-enterprise-readiness`
- The branch was synchronized with its upstream.

Pre-existing unrelated worktree changes were present and remain out of scope:

- Modified: `backend/ai_modules/sca/services/context_analyzer.py`
- Modified: `docs/governance/tools/phase31_4_v2_5_operational_actions.py`
- Untracked Phase31.4 evidence, WP2/Phase32 reports, and supporting files under
  `backend/ai_modules/sca/services/`,
  `docs/governance/evidence/`, `docs/transformation/`, and
  `docs/transformation/phase32/`.

These changes were not modified, staged, or reverted by this task.

## D. E-07 Credential Inventory

| Credential | Purpose / consumer | Authority | Persistence and historical exposure | Rotation required | State |
|---|---|---|---|---|---|
| `ADMIN_APPS_API_KEY` (`X-API-Key`) | ISO Smart integration requests; `backend/integration/client.py` | AdminApps `IntegrationAPIKey` authority | Long-lived service credential. Evidence 01 records a hard-coded development fallback in `backend/backend/settings.py`. | Yes | `BLOCKED_BY_EXTERNAL_ROTATION_AUTHORITY` |
| Initial administrator password | Initial ISO Smart administrator bootstrap; `backend/authentication/scripts/create_initial_user.py` | Authorized ISO Smart account administrator/target account store | Password and credential-print path were recorded in versioned source by evidence 01. Whether the affected account/value was used is unverified. | Yes, if it may have been used; the usage determination itself is unavailable | `BLOCKED_BY_EXTERNAL_ROTATION_AUTHORITY` |
| Phase31 operational readiness bearer | One readiness identity request | AdminApps programmatic SimpleJWT issuance using the existing SSO signing subsystem | Ephemeral 900-second access token; anonymous pipe and in-memory buffer, overwritten at teardown; no persisted refresh credential; only a fingerprint enters evidence. | No; expiry is not rotation of the underlying API key | `ROTATION_NOT_REQUIRED` |

No other credential types were added to this E-07 inventory without source
evidence tying them to the committed-credentials finding. The
`ADMIN_APPS_API_KEY` is treated separately from the short-lived bearer; the
latter cannot establish that the former was rotated.

## E. Current Repository Secret State

Neither `gitleaks` nor `trufflehog` is installed. A bounded `rg` scan of the
three relevant first-party source files checked for private-key markers,
JWT-shaped values, and quoted high-confidence literal assignments to password,
API-key, secret, or token identifiers. It found **zero high-confidence
candidates** in those files. The relevant source still obtains the API key
through `ADMIN_APPS_API_KEY` and sends it using `X-API-Key`; no literal key was
found by the bounded scan.

An ignored, untracked `backend/.env` exists. It was not opened, copied, or
included in the scan result. Therefore this is a bounded finding about the
tracked E-07 source paths, not a claim that every ignored local file was
inspected.

`raw_credential_evidence_leaks = 0`.

## F. Historical Credential Exposure

Evidence
`docs/governance/evidence/phase31_5/01_environment.json` records both:

1. a hard-coded initial administrator password and credential-print path in
   `backend/authentication/scripts/create_initial_user.py`; and
2. a hard-coded development AdminApps integration credential fallback in
   `backend/backend/settings.py`.

The preceding repository audit in evidence 21 recorded zero first-party
current hits, two vendored dependency pattern hits, one history-matching
commit, and no raw secrets recorded. Git history metadata confirms the
relevant tracked paths and their source history; it does not establish an
authority-side credential event. No raw historical value was displayed or
copied into this report.

These are three separate findings and are not interchangeable:

- **Current tracked-source scan:** no high-confidence literal was found in the
  bounded E-07 files.
- **Historical exposure:** prior Phase31.5 evidence records credential-bearing
  source paths and a history match.
- **Authentic rotation:** no authority-side invalidation or replacement is
  evidenced.

Thus current-source cleanliness does not prove historical exposure was
remediated at the credential authority.

## G. Authentic Rotation Evidence

No rotation is proven. There is no authority event, rotation timestamp,
replacement safe fingerprint, old-credential rejection proof, or
replacement-acceptance proof for either the AdminApps API key or the initial
administrator password.

The operational bearer source contract confirms a 900-second token, pipe and
in-memory handling, teardown overwrite, `token_persisted=false`, and
fingerprint-only evidence. This confirms the handling contract for that
ephemeral bearer; it is neither long-lived credential rotation nor proof that
the AdminApps key is invalid.

## H. External Authority Blockers

**AdminApps API key:** the AdminApps credential authority must revoke the
possibly exposed key, issue a replacement, and install it through an approved
secret mechanism. Afterward, provide redacted authority event metadata,
timestamps and safe fingerprints, proof that the old key is rejected, and a
narrow approved identity/readiness proof for the replacement. Do not call
customer workflows to test it.

**Initial administrator password:** an authorized ISO Smart account
administrator must determine whether the historical value was used. If it may
have been used, reset or revoke the affected account credential and provide a
redacted event record and old-password rejection proof. Do not disclose either
password.

The local environment exposes no approved credential authority or configured
rotation mechanism. No external access attempt was made.

## I. Secret-Handling Integrity

No raw credential, JWT, password, API key, private key, or refresh token was
written to either evidence artifact or printed in the audit results. Historical
inspection was limited to source/path/commit metadata and prior redacted
governance findings. The ignored `backend/.env` was left untouched.

The new report and JSON must also pass the staged-diff secret scan before
publication. Required metric: `raw_credential_evidence_leaks = 0`.

## J. E-07 Adjudication

Both credentials with possible historical use remain without authority-backed
rotation evidence. The bearer token's expiry and safe handling do not close
either credential's requirement.

`E-07 = FAIL_AUTHENTIC_ROTATION_EVIDENCE_REQUIRED`

The blocker classification for both outstanding items is
`BLOCKED_BY_EXTERNAL_ROTATION_AUTHORITY`.

## K. Phase31.5 State

`E-08 = CLOSED_LOCAL_TECHNICAL_EVIDENCE`

`Phase31.5 = EXECUTION_HELD`

No phase execution, Retry20, deployment, customer-data access, external
delivery, or lifecycle transition is authorized by this evidence.

## L. Evidence and Publication

Machine-readable evidence:
`docs/governance/evidence/phase31_5/27_e07_authentic_rotation_2026-10-05.json`

This report:
`docs/transformation/PHASE31_5_E07_AUTHENTIC_ROTATION_CLOSURE_2026-10-05.md`

Evidence ID 27 was unused. Publication is limited to these two E-07-owned
files, using a normal commit and push after staged-diff secret review.
Unrelated pre-existing worktree changes remain unstaged. Commit and upstream
synchronization are verified separately from Git metadata; no self-referential
commit hash is embedded in the evidence artifact.
