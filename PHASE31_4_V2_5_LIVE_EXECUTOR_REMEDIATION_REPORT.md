# Phase 31.4 V2.5 Live Executor Remediation

## Status

LIVE_EXECUTOR_CODE_PASS / INTEGRITY_RECONCILIATION_REQUIRED

## Scope

This remediation targets the bridge between the reusable disposable runner and the live V2.5 runtime evidence contract. The executor remains intentionally separated from Retry 20 and from any Phase 31.5 trigger path.

## Guardrails maintained

- No Retry 20 authorization consumption.
- No Retry 20 execution.
- No Phase 31.5 start.
- Stage EXT must be live and fresh; historical/fixture data is rejected.
- Runtime handoff does not trigger a formal clean retry unless the caller explicitly enables execution.

## Implementation

The bridge is implemented in [backend/foundation/phase31_4_v2_5_live_executor.py](backend/foundation/phase31_4_v2_5_live_executor.py), with focused regression checks in [backend/foundation/test_phase31_4_v2_5_live_executor.py](backend/foundation/test_phase31_4_v2_5_live_executor.py).

### What changed

- Added a fail-closed `LiveExecutorError` that includes the concrete classification code in the raised string.
- Aligned the Stage EXT resolution contract to the six live identity values required by the runtime:
  - tenant
  - actor
  - tenant_projection
  - user_projection
  - organization
  - process
- Ensured the capture bundle is built only from fresh Stage EXT values and rejects historical or fixture inputs.
- Wrapped runtime handoff so a non-executing runtime stub still receives session metadata without attempting a formal retry.

## Verification

Command run:

```bash
cd /home/felipe/proyectos/isosmart/backend && PYTHONPATH=/home/felipe/proyectos/isosmart/backend DJANGO_SETTINGS_MODULE=backend.settings /home/felipe/proyectos/isosmart/backend/.venv/bin/python -m django test foundation.test_phase31_4_v2_5_live_executor --verbosity 2
```

Result:

- 9 tests ran
- 9 tests passed
- Exit code: 0

## Conclusion

The live executor bridge is code-valid and passes the focused contract suite. However, a broader enterprise-level integrity reconciliation remains required before claiming full repository-wide execution authority beyond this isolated, verified evidence bridge.
