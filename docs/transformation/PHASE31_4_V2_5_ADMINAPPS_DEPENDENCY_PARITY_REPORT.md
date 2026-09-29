# Phase 31.4 V2.5 — AdminApps disposable dependency parity

Classification: `DISPOSABLE_DEPENDENCY_INSTALLATION_GAP_CONFIRMED` (case A).
`IS_DJANGO_APSCHEDULER_CANONICAL_DEPENDENCY = true`.

AdminApps unconditionally registers `django_apscheduler` in `config.settings`.
Its canonical `backend/requirements.txt` pins the runtime distribution
`django-apscheduler==0.7.0`. Both CI workflows and the development guide install
that manifest. No alternate Python manifest, lockfile, Dockerfile or deployment
manifest was found. Billing job enablement does not make application registration
optional. AdminApps' host Python 3.9.25 venv contains this package, but Attempt 1's
authority operation used ISO Smart's Python 3.12.13 venv, which does not. The
runner creates disposable databases, not Python environments, and previously
performed no dependency installation. Its AdminApps migration and service paths
used the AdminApps host venv, unlike its authority path.

One remediation provisions a temporary isolated venv from the entire existing
AdminApps requirements manifest and routes AdminApps migrations, authority and
service to that same interpreter. No host environment, canonical dependency
contract, scheduler behavior or Bearer contract is changed. The manifest has
conflicting pins with ISO Smart, so the environments remain separate. The
context removes the temporary venv on failure or after service teardown.

Validation performed for this change:

- 50/50 focused tests: seven dependency parity checks plus 43 Bearer, readiness,
  adapter, lifecycle and integrity checks; no skipped parity check.
- 2/2 operational command boundary checks.
- ISO Smart full regression: 575/575 PASS, Python 3.12.
- AdminApps full regression: 180/180 PASS in the newly provisioned Python 3.12
  runtime; its CI product-authority subset also passed 160/160.
- Real `import django`, `config.settings` load, `django.setup()` and
  `django_apscheduler` import: PASS. All 18 canonical direct pins verified.
- `pip check`: PASS. Default PyPI index; downloads only from
  `files.pythonhosted.org`; artifact SHA-256 values retained. No project lockfile
  exists for transitive dependencies; no index or TLS change was made.
- Raw runtime credential patterns in retained validation logs: zero.
- V12 successor integrity: PASS, 30 protected sources. V11 manifest and the 15
  pre-existing V11 history/evidence files remain byte-identical. The relevant
  previously untracked Attempt 1 evidence is retained as causal audit material.
- V2.4 historical migration integrity: PASS; no migrations changed.

The initial focused invocation lacked Django test settings and was cancelled;
the subsequent governed test-settings invocation had one assertion-order failure
in the new V12 verifier. The final verifier checks source bytes before change
classification, preserving the existing fail-closed assertion. The final 50-test
run and both full regressions above passed. No additional runtime blocker was
remediated.

Attempt 2 execution remains conditional on the independent one-shot artifact,
exact remediation commit, clean source worktree, real-runtime import preflight,
resource absence and mandatory teardown. Its driver owns provisioning through
cleanup and records safe authority PID/interpreter/argv metadata. Attempt 3 is
not authorized. Retry 20 remains NONE / not executed; its historical authority
remains SUPERSEDED_UNCONSUMED. Phase 31.5 remains EXECUTION_HELD.

Canonical evidence: `docs/governance/evidence/PHASE31_4_V2_5_ADMINAPPS_DEPENDENCY_PARITY_REVIEW_V1.json`.
Successor reconciliation: `docs/governance/evidence/PHASE31_4_V2_5_ADMINAPPS_DEPENDENCY_PARITY_SUCCESSOR_RECONCILIATION_V1.json`.
