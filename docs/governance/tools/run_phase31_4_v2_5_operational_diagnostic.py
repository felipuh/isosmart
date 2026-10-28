"""Run one bounded live-executor diagnostic; never runs the V2.5 clean retry."""
from __future__ import annotations
import json, os, sys
from hashlib import sha256
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE","backend.settings")
import django
django.setup()
from foundation.phase31_4_v2_5_disposable_runner import DIAGNOSTIC_CLASSIFICATION, DisposableEvidenceRunner, RunInputs
from foundation.phase31_4_v2_5_live_executor import Phase31_4V25LiveEvidenceExecutor, build_live_execution_context
from foundation.phase31_4_v2_5_operational_adapters import SubprocessOperationalAdapter, repository_operational_environment
RUN_ID="Phase 31.4 V2.5 Live Executor Operational Diagnostic 20260924 Attempt 3"
SLUG="Phase_31.4_V2.5_Live_Executor_Operational_Diagnostic_20260924_Attempt_3"
EVIDENCE=ROOT/"docs/governance/evidence/runs"/SLUG
AUTH=EVIDENCE/"authorization_diagnostic_v1.json"
INTEGRITY=ROOT/"docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V6.json"

runner=DisposableEvidenceRunner(RunInputs(repository_root=ROOT,run_id=RUN_ID,authorization_artifact=AUTH,
    expected_authorization_sha256=sha256(AUTH.read_bytes()).hexdigest(),current_integrity_generation="PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V6",
    expected_integrity_sha256=sha256(INTEGRITY.read_bytes()).hexdigest(),evidence_root=EVIDENCE,
    execution_kind=DIAGNOSTIC_CLASSIFICATION,validation_attempt=3,readiness_timeout_seconds=90))
holder={}
def live():
    if "executor" not in holder:
        context=build_live_execution_context(repository_root=ROOT,runner=runner,evidence_root=EVIDENCE,
            authorization_reference=str(AUTH.relative_to(ROOT)),integrity_generation="PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V6")
        holder["executor"]=Phase31_4V25LiveEvidenceExecutor(runner=runner,context=context,
            adapter=SubprocessOperationalAdapter(environment=repository_operational_environment(ROOT,os.environ),timeout_seconds=90),
            mode="diagnostic",allow_runtime_execution=False)
    return holder["executor"]
def stage(manifest):
    executor=live()
    result=dict(executor.stage_ext(manifest)); bundle=executor.build_capture_bundle()
    result.update(capture_bundle="PASS",capture_count=len(bundle.captures),classification="LIVE_EXECUTOR_OPERATIONAL_DIAGNOSTIC")
    return result
try:
    result=runner.run_evidence(precreation=lambda manifest: live().precreation(manifest),stage_ext=stage)
finally:
    if "executor" in holder: holder["executor"].stop_services()
print(json.dumps(result,indent=2,sort_keys=True))
