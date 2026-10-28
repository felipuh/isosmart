# Phase31.5 E-07 External Authority Enablement Package

Date: 2026-10-05 (America/Costa_Rica)

Classification: `AUTHORITY_ENABLEMENT_AND_EXECUTION_PREREQUISITE_PACKAGE`
Status: `NOT AN EXECUTION AUTHORIZATION`

## 1. Purpose and fixed boundary

This package converts the unresolved external E-07 blockers into minimum non-secret evidence, approval, decision, and stop-condition records. It is for the future authorized infrastructure/AdminApps operators and approvers. It does not identify an authentic target, collect any authentic metadata, execute a verification command, create or rotate a credential, inject a secret, restart `web`, or authorize any authentic rotation.

`Phase31.5 = EXECUTION_HELD`

`E-07 = BLOCKED_BY_EXTERNAL_AUTHORITY`

`E-08_BASELINE_PRESERVED = YES`

`E-08 = CLOSED_LOCAL_TECHNICAL_EVIDENCE`

The frozen source contract is: `apps.integration.models.IntegrationAPIKey` owns the lifecycle; `rotate_integration_api_key` is the rotation mechanism; migration `integration.0006_integration_api_key_lifecycle` is required; `web` consumes `ADMIN_APPS_API_KEY` and requires recreation/restart after replacement; outbox-worker has no proven direct dependency; management commands are fresh processes; and `ADMIN_PASSWORD_NOT_REQUIRED_FOR_ROTATION`.

No person may record, paste, upload, screen-capture, or transfer the generated credential through ChatGPT, Codex, Copilot, chat, a ticket, a governance artifact, a screenshot, shell history, persistent terminal log, CI log, application log, Git, or any unapproved channel.

## 2. Universal evidence and stop rules

Every future record must be secret-free. Evidence may contain opaque environment/deployment/record/audit/change identifiers only where the receiving governance policy classifies them as non-secret. It must never contain a raw credential, verifier/hash, password, MFA value, session token, private key, secret prefix where policy treats it as sensitive, command output containing a credential, or a replayable command transcript.

The evidence recorder must redact or omit any potentially secret field and must stop rather than improvise a new channel or recovery method. An approval is valid only when it identifies its scope, approver/authority, date or execution window, traceable approval reference, and any applicable change/incident reference. Expired, ambiguous, conflicting, or scope-incomplete evidence is a stop condition.

The following global stop conditions apply before and during future authentic execution:

- Any required gate below is absent, expired, contradictory, or not explicitly `PASS`/approved.
- The target record is inactive, ambiguously attributed, duplicated without a governed selection decision, or not eligible under the authentic lifecycle.
- The deployed AdminApps revision, migration ledger, schema, lifecycle model, or rotation operation is incompatible or unproven.
- The named operator is not authenticated, active, staff, or specifically approved.
- A secure receiver, non-recording handoff, or receiver injector is unapproved or cannot prevent secret persistence.
- The interruption decision, execution window, validation plan, or forward recovery is not approved.
- Any credential would be exposed to a prohibited recording, log, transcript, or conversation context.

## 3. Authentic target authorization record

Current state: `TARGET_IDENTITY_UNAVAILABLE`. This section is a blank future record; it does not assert any value now.

| Required non-secret field | Future authorized entry | Evidence/decision required |
|---|---|---|
| `ADMINAPPS_ENVIRONMENT_ID` | `UNRESOLVED` | Immutable environment identifier or governing inventory reference, supplied under metadata-only inspection authority. |
| `ADMINAPPS_ENVIRONMENT_CLASS` | `UNRESOLVED` | `production`, `staging`, or explicitly governed alternative, with classification owner. |
| `INTEGRATION_LOGICAL_NAME` | `UNRESOLVED` | Non-secret service/logical name and attribution evidence linking it to ISO Smart. |
| `INTEGRATION_API_KEY_RECORD_ID` | `UNRESOLVED` | Exact authentic primary-key identifier selected for lifecycle inspection; never the credential value. |
| `INTEGRATION_API_KEY_ACTIVE` | `UNRESOLVED` | Authorized metadata-only observation that the selected record is active. |
| `ISOSMART_ATTRIBUTION_VERIFIED` | `UNRESOLVED` | Operator attestation plus safe source-of-truth reference tying the record to the intended ISO Smart integration. |
| `DUPLICATE_CANDIDATES` | `UNRESOLVED` | Safe count/list of candidate identifiers or explicit zero result; if nonzero, a governed selection/disposition decision. |
| `LIFECYCLE_COMPATIBILITY` | `UNRESOLVED` | Evidence that the selected record is eligible for the source-defined lifecycle, including no conflicting lifecycle state. |
| `TARGET_AUTHORITY_REFERENCE` | `UNRESOLVED` | Metadata-inspection authorization and authority reference. |

`TARGET_IDENTITY_PASS` requires all fields above, a single unambiguous active ISO Smart-attributed candidate (or an explicit authorized resolution of duplicates), lifecycle eligibility, and a traceable metadata-only inspection authority. It must be recorded as `FAIL`/`UNRESOLVED` if any material fact is unavailable. It must not be inferred from repository names, local fixtures, or deployment-looking configuration.

## 4. Runtime and migration proof record

Current state: `ADMINAPPS_RUNTIME_PROOF_UNAVAILABLE`.

The authorized verifier must supply secret-free, target-specific proof of all of the following:

| Requirement | Safe evidence form | Failure / stop condition |
|---|---|---|
| `integration.0006_integration_api_key_lifecycle` applied | Migration ledger result tied to `ADMINAPPS_ENVIRONMENT_ID`; no database dump or secrets. | Missing, pending, different, or unverifiable migration. |
| Deployed AdminApps revision/version | Immutable build/release identifier and deployment inventory reference. | Revision is unknown or cannot be compared to the reviewed lifecycle contract. |
| Lifecycle model availability | Non-secret authorized availability/diagnostic result for `IntegrationAPIKey` lifecycle fields. | Model unavailable, altered incompatibly, or result includes secret data. |
| Rotation operation availability | Non-secret command/function availability result naming `rotate_integration_api_key`; do not execute rotation. | Operation absent, inaccessible to the approved operator, or proof requires executing rotation. |
| Database/schema compatibility | Authorized schema/migration compatibility attestation or metadata-only report. | Version drift or incompatible schema is found. |
| Evidence 29/30 assumption drift | Verifier's explicit comparison/attestation against the frozen lifecycle contract. | Any drift is unexplained or requires a new technical adjudication. |

`ADMINAPPS_RUNTIME_READY` requires all six items, no incompatible drift, and evidence traceable to the selected authentic target. Local tests and local source are supporting evidence only; they cannot satisfy this gate. No listed command template is authorized to run under this package.

## 5. Authorized operator record

Current state: `AUTHORIZED_OPERATOR_NOT_IDENTIFIED`.

| Required non-secret field | Future authorized entry | Evidence required |
|---|---|---|
| `OPERATOR_IDENTITY` | `UNRESOLVED` | Governed personnel/service identity reference; no login material. |
| `OPERATOR_ROLE` | `UNRESOLVED` | Role assignment proving permitted AdminApps operation. |
| `OPERATOR_ACTIVE_STATUS` | `UNRESOLVED` | Identity/authorization-system attestation that status is active. |
| `OPERATOR_STAFF_STATUS` | `UNRESOLVED` | Attestation that status meets the lifecycle's staff requirement. |
| `ROTATION_SPECIFIC_APPROVAL` | `UNRESOLVED` | Explicit approval for this target, integration record, and planned window. |
| `APPROVING_AUTHORITY` | `UNRESOLVED` | Named authority role/office, not an invented individual. |
| `APPROVAL_REFERENCE` | `UNRESOLVED` | Traceable approval/change reference. |

`AUTHORIZED_OPERATOR_PASS` requires a uniquely identified future operator, independently confirmed active and staff status at execution time, an applicable role, and explicit rotation-specific authorization from the approving authority. Passwords, MFA codes, session tokens, private keys, and other authentication material are prohibited evidence. The initial ISO Smart administrator password is not a required rotation input: `ADMIN_PASSWORD_NOT_REQUIRED_FOR_ROTATION`.

## 6. Secret receiver and leakage-closure contract

Current state: `SECRET_RECEIVER_UNRESOLVED`.

| Required field | Future authorized entry | Minimum acceptance evidence |
|---|---|---|
| `SECRET_RECEIVER_TYPE` | `UNRESOLVED` | Governed receiver category, not the secret. |
| `SECRET_RECEIVER_TARGET` | `UNRESOLVED` | Non-secret target identity mapped to intended `web` deployment. |
| `SECRET_RECEIVER_OWNER` | `UNRESOLVED` | Responsible authority/owner role. |
| `AUTHORIZED_SECRET_INJECTOR` | `UNRESOLVED` | Identity/role specifically allowed to update the receiver. |
| `SECRET_UPDATE_MECHANISM` | `UNRESOLVED` | Approved direct one-time mechanism described without replayable secret-bearing syntax. |
| `SECRET_PERSISTENCE_MODEL` | `UNRESOLVED` | Statement of permitted secret storage and retention. |
| `SECRET_ACCESS_CONTROL` | `UNRESOLVED` | Access-boundary attestation for receiver and injector. |
| `SECRET_AUDIT_MODEL` | `UNRESOLVED` | Secret-free audit event/reference model. |
| `SECRET_OUTPUT_CAPTURE_PROHIBITION` | `UNRESOLVED` | Explicit ban on secret recording/output capture and owner acknowledgement. |

The receiver must support direct insertion of the replacement without placing it in Git, chat, ticketing, governance evidence, screenshots, shell history, persistent terminal or session logs, CI logs, application logs, command transcripts, or conversation context. `SECRET_LEAKAGE_PATHS_CLOSED` requires written confirmation that each prohibited destination is technically prevented or procedurally excluded for the approved handoff and receiver update, plus a stop/escalation method if prevention fails.

## 7. One-time non-recording handoff contract

Current state: `NON_RECORDING_TRANSFER_UNRESOLVED`.

The lifecycle can emit a newly generated credential once; the future operation is therefore prohibited until this contract is explicitly approved. The future contract must identify, without exposing the value:

| Contract item | Required decision/evidence |
|---|---|
| Recipient | Authorized receiver/injector role and identity reference. |
| Channel | Approved direct secure channel/mechanism from rotation boundary to the receiver; no chat or transcript-mediated relay. |
| Stdout handling | How exposure is prevented or bounded, including disabled recording/capture and an authorized immediate stop if that guarantee cannot be made. |
| Terminal/session controls | How session recording, history, scrollback persistence, copy buffers, remote capture, and persistent logs are prevented or governed. |
| Receiver delivery | How the recipient inserts the value directly into the approved receiver without redisplay. |
| Evidence exclusion | How evidence proves completion with only safe identifiers/audit references and never the value or output. |
| Confirmation | Secret-free confirmation that the receiver update completed and is associated with the intended target. |
| Failed transfer | Immediate containment, no replay/copy of one-time output, escalation owner, and the approved forward-recovery decision. |
| Approval | `NON_RECORDING_HANDOFF_APPROVED`, approving authority, scope, window, and approval reference. |

Only an explicit approval satisfying every item above may set `NON_RECORDING_HANDOFF_APPROVED`. Until then, the state is `NON_RECORDING_TRANSFER_UNRESOLVED`, the rotation must not begin, and no future operator may rely on an informal verbal or chat-based handoff.

## 8. ISO Smart web cutover record

Current state: `WEB_RECEIVER_TARGET_UNRESOLVED`.

| Required field | Future authorized entry | Acceptance evidence |
|---|---|---|
| `ISOSMART_ENVIRONMENT` | `UNRESOLVED` | Environment identity/class matching the approved AdminApps target. |
| `WEB_DEPLOYMENT_ID` | `UNRESOLVED` | Exact immutable deployment/workload identity for `web`. |
| `WEB_SECRET_RECEIVER` | `UNRESOLVED` | Receiver target matching the approved secret receiver contract. |
| `WEB_RECEIVER_UPDATE_OPERATOR` | `UNRESOLVED` | Authorized injector identity/role. |
| `WEB_RESTART_OPERATOR` | `UNRESOLVED` | Operator authorized to recreate/restart `web`. |
| `WEB_RESTART_MECHANISM` | `UNRESOLVED` | Approved non-secret operational mechanism; no authentic command is supplied here. |
| `WEB_RESTART_APPROVAL` | `UNRESOLVED` | Scope/window approval for the restart/recreation. |
| `WEB_HEALTH_VALIDATION` | `UNRESOLVED` | Narrow secret-free health criterion and evidence reference. |
| `ADMINAPPS_AUTH_VALIDATION` | `UNRESOLVED` | Narrow secret-free authentication validation criterion and expected result. |

`WEB_CUTOVER_PATH_PASS` requires evidence that the receiver update changes only the intended `web` credential input, unrelated configuration is unchanged, `web` is recreated/restarted after receiver replacement, health is checked without displaying the credential, and AdminApps authentication is checked narrowly without a customer workflow. It also requires the named operators, mechanism, approval, and target to be mutually consistent. Any need to use a customer workflow or reveal the credential is a stop condition.

## 9. Interruption approval contract

`NO_DUAL_KEY_GRACE_PERIOD` and AdminApps/ISO Smart cutover are not cross-system atomic.

`INTERRUPTION_EXPECTED = POSSIBLE`

No duration is defined or implied; zero downtime must not be claimed. Before execution, the approving authority must complete the following fields:

| Field | Future authorized entry | Required decision |
|---|---|---|
| `INTERRUPTION_WINDOW_ACCEPTED` | `UNRESOLVED` | Explicit acceptance that authentication interruption is possible. |
| `INTERRUPTION_APPROVING_AUTHORITY` | `UNRESOLVED` | Authority role/office empowered to accept impact. |
| `APPROVED_EXECUTION_WINDOW` | `UNRESOLVED` | Bounded window and timezone; no invented duration. |
| `CUSTOMER_IMPACT_ASSESSMENT` | `UNRESOLVED` | Impact/communications decision and confirmation that validation needs no customer workflow. |
| `ABORT_THRESHOLD` | `UNRESOLVED` | Pre-commit abort threshold plus post-commit escalation/forward-recovery threshold. |

`INTERRUPTION_APPROVED` requires all fields, applicable approvals, and a viable forward-recovery plan. The operation must not proceed merely because a maintenance window exists.

## 10. Forward-recovery contract and decision tree

Current state: `FORWARD_RECOVERY_UNRESOLVED`.

The frozen lifecycle evidence establishes that, after successful rotation commit, the former credential must not be assumed valid. `FORWARD_RECOVERY_ONLY_AFTER_ROTATION_COMMIT` is compatible with the lifecycle because the former credential is rotated/revoked. The source does not select an authentic receiver reinjection, retry/recreate, or incident operation; the authorized operator/incident authority must supply and approve that target-specific decision before execution.

| State | Meaning | Failure decision / authorized recovery requirement |
|---|---|---|
| `R0` | Rotation not committed. | `ABORT_WITHOUT_CREDENTIAL_CHANGE`; correct prerequisites and return to precheck. |
| `R1` | AdminApps rotation committed and replacement safely received. | If handoff/receiver delivery fails, do not reuse, reactivate, or assume validity of the former credential; contain the value in the approved non-recording boundary, hold affected consumer safely as approved, and invoke the named receiver/injection and incident authority's forward-recovery decision. |
| `R2` | ISO Smart receiver updated. | If receiver verification or following cutover step fails, do not redisplay the credential; preserve only secret-free receiver/audit evidence, use the preapproved retry/recreate path or escalate under the named decision authority. |
| `R3` | `web` restart/recreation attempted. | If `web` fails to restart or health validation fails, use the approved recovery/retry mechanism and escalation threshold; do not roll back by restoring the former credential. |
| `R4` | AdminApps authentication validated. | Capture only secret-free success evidence, then close under the approved change record. If validation is negative/indeterminate, treat as R3 recovery and escalate. |

To set `FORWARD_RECOVERY_DEFINED`, the future record must name the R1, R2, and R3 decision authority; approved receiver/retry/recreate or incident mechanism; permitted consumer safety posture; escalation trigger; evidence/audit references; and close criteria. A record that says only “rollback” or “retry” without these target-specific decisions fails the gate.

## 11. Separation of duties

No real persons are assigned by this package. The required role records are:

| Role | Responsibility | Prohibited action / control |
|---|---|---|
| Governance approver | Approves target scope, handoff, interruption, and recovery authority. | Must not approve an undefined receiver or undocumented recovery. |
| AdminApps rotation operator | Performs the future source-defined rotation only after all gates pass. | Must not expose the generated credential or operate without active/staff/rotation approval. |
| Secret receiver/injector | Directly receives and inserts value into approved receiver. | Must not use chat, ticket, Git, transcript, or persistent log as transfer media. |
| ISO Smart restart operator | Recreates/restarts intended `web` and carries out approved narrow checks. | Must not alter unrelated configuration or execute customer workflows for validation. |
| Evidence recorder/verifier | Records secret-free evidence and validates gates. | Must never persist authentic secret material or request it for proof. |

Whether one person may perform multiple roles is governed only by existing applicable governance. If such governance permits combination, the approving record must state the allowed combination and compensating review/control. This package neither invents mandatory organizational separation nor permits secret recording by any role.

## 12. Authentic rotation eligibility matrix

No external gate is marked `PASS` by this package.

| Gate | Current state | Required state before separate authorization | Minimum authoritative proof |
|---|---|---|---|
| Authentic target | `TARGET_IDENTITY_UNAVAILABLE` | `TARGET_IDENTITY_PASS` | §3 completed by metadata-only target authority. |
| Runtime | `ADMINAPPS_RUNTIME_PROOF_UNAVAILABLE` | `ADMINAPPS_RUNTIME_READY` | §4 migration, revision, model, operation, schema, and drift proof. |
| Operator | `AUTHORIZED_OPERATOR_NOT_IDENTIFIED` | `AUTHORIZED_OPERATOR_PASS` | §5 active/staff and rotation-specific approval proof. |
| Secret handoff | `SECRET_RECEIVER_UNRESOLVED` / `NON_RECORDING_TRANSFER_UNRESOLVED` | `SECRET_TRANSFER_PATH_PASS` | §§6–7 approved receiver and non-recording handoff. |
| Web cutover | `WEB_RECEIVER_TARGET_UNRESOLVED` | `WEB_CUTOVER_PATH_PASS` | §8 target, operator, restart, and narrow validation proof. |
| Interruption | `NOT_APPROVED` | `INTERRUPTION_APPROVED` | §9 explicit impact/window/abort approval. |
| Recovery | `FORWARD_RECOVERY_UNRESOLVED` | `FORWARD_RECOVERY_DEFINED` | §10 R1–R3 target-specific recovery authority and decisions. |
| Leakage controls | `UNASSESSED_FOR_AUTHENTIC_EXECUTION` | `SECRET_LEAKAGE_PATHS_CLOSED` | §§2, 6, and 7 controls accepted by responsible authority. |

`READY_FOR_AUTHENTIC_ROTATION_AUTHORIZATION` cannot result from this package. A separate bounded preflight may adjudicate that state only after every row is proven and approved.

## 13. Future authentic execution skeleton — non-executing

`NOT AN EXECUTION AUTHORIZATION`

The following is a symbolic sequence only. It contains no usable command, credential, environment value, or target instruction.

`PRECHECK` → `TARGET_LOCK` → `OPERATOR_AUTHORIZATION_CHECK` → `RECEIVER_READY_CHECK` → `ROTATE_ADMINAPPS_CREDENTIAL` → `NON_RECORDING_HANDOFF` → `UPDATE_ISOSMART_RECEIVER` → `RECREATE_OR_RESTART_WEB` → `NARROW_HEALTH_CHECK` → `ADMINAPPS_AUTH_CHECK` → `SECRET_FREE_EVIDENCE_CAPTURE` → `CLOSE_OR_FORWARD_RECOVER`

At each stage, stop if the relevant gate, approval, output-control guarantee, or recovery requirement is not satisfied. Before commit, use the approved R0 abort path. After commit, use only the approved forward-recovery decision tree.

## 14. Governance publication and E-08 preservation

`GOVERNANCE_BASELINE_LOCAL_ONLY`

Known governing commits remain unpublished locally unless evidence later shows otherwise. `publication_requirement_for_rotation = NOT_DEFINED_BY_INSPECTED_GOVERNANCE_ARTIFACTS`; this package does not classify publication as a rotation blocker and does not authorize a push.

`E-08_BASELINE_PRESERVED = YES`

`E-08 = CLOSED_LOCAL_TECHNICAL_EVIDENCE`

E-08 is not retested, reopened, or modified by this package.

## 15. Package verdict and remaining external inputs

`EXTERNAL_AUTHORITY_PACKAGE_COMPLETE`

The package defines exactly what external authorities must supply and approve before a separate bounded preflight may adjudicate authentic-rotation readiness. It does not mean any external gate is satisfied.

Remaining human/external inputs only:

- Authorized metadata-only identification and approval of the authentic AdminApps target and eligible `IntegrationAPIKey` record.
- Authentic AdminApps migration, revision, model/operation, schema, and drift evidence.
- An authenticated active staff operator and rotation-specific approval.
- An approved ISO Smart secret receiver, authorized injector, non-recording one-time handoff, and leakage-control evidence.
- An approved `web` receiver/restart/cutover and narrow validation path.
- Explicit interruption acceptance, execution window, customer-impact assessment, and abort threshold.
- Target-specific R1–R3 forward-recovery decisions and named incident/decision authority.

`Phase31.5 = EXECUTION_HELD`

No authentic rotation is authorized by this package.
