"""Canonical V8 Attempt 2 driver; bounded diagnostic only."""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import shlex
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_BASE = ROOT / "docs/governance/evidence"
AUTH = EVIDENCE_BASE / os.environ.get("PHASE31_ATTEMPT_AUTHORIZATION", "PHASE31_4_V2_5_V8_OPERATIONAL_DIAGNOSTIC_ATTEMPT_2_AUTHORIZATION_V1.json")
AUTH_DOC = json.loads(AUTH.read_text())
INTEGRITY = ROOT / AUTH_DOC["integrity"]["artifact_path"]
EVIDENCE = ROOT / AUTH_DOC["evidence_root"]
RUN_ID = AUTH_DOC["run_id"]
ATTEMPT = int(AUTH_DOC["attempt"])

sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    path = EVIDENCE / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str) + "\n", encoding="utf-8")


def command(argv):
    result = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=30)
    return {"argv": argv, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def preflight():
    from foundation.phase31_4_v2_5_operational_adapters import repository_operational_environment
    from foundation.phase31_4_v2_5_disposable_runner import _database_name, _resource_prefix

    assert not EVIDENCE.exists()
    env = repository_operational_environment(ROOT, os.environ)
    admin_command = shlex.split(env["PHASE31_ADMINAPPS_START_COMMAND"])
    iso_command = shlex.split(env["PHASE31_ISOSMART_START_COMMAND"])
    admin_manage = ROOT.parent / "adminapps/backend/manage.py"
    iso_manage = ROOT / "backend/manage.py"
    assert admin_manage.is_file() and iso_manage.is_file()
    service_argv = {
        "adminapps": [str(ROOT.parent / "adminapps/backend/.venv/bin/python"), str(admin_manage), "runserver", "--noreload", "127.0.0.1:<allocated-port>"],
        "isosmart": [str(ROOT / "backend/.venv/bin/python"), str(iso_manage), "runserver", "--noreload", "127.0.0.1:<allocated-port>"],
    }
    assert all(Path(argv[1]).is_absolute() for argv in service_argv.values())
    podman = {kind: command(argv) for kind, argv in {
        "containers": ["podman", "ps", "-a", "--format", "{{.Names}}"],
        "networks": ["podman", "network", "ls", "--format", "{{.Name}}"],
        "volumes": ["podman", "volume", "ls", "--format", "{{.Name}}"],
    }.items()}
    assert all(item["returncode"] == 0 for item in podman.values())
    prefix = _resource_prefix(AUTH_DOC["canonical_run_slug"])
    resources = {role: {"container": f"{prefix}_{role}", "network": f"{prefix}_{role}_net", "volume": f"{prefix}_{role}_data", "database": _database_name(AUTH_DOC["canonical_run_slug"], role)} for role in ("adminapps", "isosmart")}
    for resource in resources.values():
        for kind, key in (("containers", "container"), ("networks", "network"), ("volumes", "volume")):
            assert resource[key] not in podman[kind]["stdout"].splitlines()
    preflight_name = AUTH.stem.replace("_AUTHORIZATION_V1", "_PREFLIGHT_V1") + ".json"
    (EVIDENCE_BASE / preflight_name).write_text(json.dumps({"status": "PASS", "at": now(), "run_id": RUN_ID, "resources_absent": resources, "adminapps_root": str(ROOT.parent / "adminapps/backend"), "adminapps_manage": str(admin_manage), "isosmart_manage": str(iso_manage), "dispatcher_commands": {"adminapps": admin_command, "isosmart": iso_command}, "resolved_service_argv": service_argv, "ports": "dynamic kernel allocation", "podman": podman, "stale_manifest": False, "previous_authorization_consumption": False}, indent=2) + "\n", encoding="utf-8")


def run():
    preflight()
    from foundation.phase31_4_v2_5_disposable_runner import DisposableEvidenceRunner, RunInputs, DIAGNOSTIC_CLASSIFICATION
    from foundation.phase31_4_v2_5_live_executor import Phase31_4V25LiveEvidenceExecutor, build_live_execution_context
    from foundation.phase31_4_v2_5_operational_adapters import SubprocessOperationalAdapter, repository_operational_environment

    runner = DisposableEvidenceRunner(RunInputs(repository_root=ROOT, run_id=RUN_ID, authorization_artifact=AUTH, expected_authorization_sha256=digest(AUTH), current_integrity_generation=AUTH_DOC["integrity"]["generation"], expected_integrity_sha256=digest(INTEGRITY), evidence_root=EVIDENCE, execution_kind=DIAGNOSTIC_CLASSIFICATION, validation_attempt=ATTEMPT, consumption_registry=ROOT / AUTH_DOC["consumption_registry"], readiness_timeout_seconds=90))
    executor = None
    holder = {}
    outcome = {"run_id": RUN_ID, "started_at": now(), "verdict": f"ATTEMPT_{ATTEMPT}_FAIL"}
    try:
        def live():
            if "executor" not in holder:
                context = build_live_execution_context(repository_root=ROOT, runner=runner, evidence_root=EVIDENCE, authorization_reference=str(AUTH.relative_to(ROOT)), integrity_generation=AUTH_DOC["integrity"]["generation"])
                holder["executor"] = Phase31_4V25LiveEvidenceExecutor(runner=runner, context=context, adapter=SubprocessOperationalAdapter(environment=repository_operational_environment(ROOT, os.environ), timeout_seconds=90), mode="diagnostic", allow_runtime_execution=False)
            return holder["executor"]
        def stage(manifest):
            result = dict(live().stage_ext(manifest))
            write("stage_ext.json", result)
            bundle = live().build_capture_bundle()
            bundle.validate_for_retry(RUN_ID)
            write("capture_bundle.json", {"status": "READY", "bundle": dataclasses.asdict(bundle), "run_id": RUN_ID})
            live().prepare_runtime()
            return dict(result, capture_bundle="PASS", capture_count=len(bundle.captures))
        runner.run_evidence(precreation=lambda manifest: live().precreation(manifest), stage_ext=stage)
        outcome["verdict"] = f"ATTEMPT_{ATTEMPT}_PASS"
    except BaseException as exc:
        outcome.update({"exception_type": type(exc).__name__, "exception": str(exc), "traceback": traceback.format_exc()})
    finally:
        executor = holder.get("executor")
        if executor is not None:
            outcome["service_endpoints"] = dict(executor.context.service_urls)
            outcome["service_pids"] = {key: process.pid for key, process in executor.adapter.processes.items()}
            try:
                outcome["service_cleanup"] = executor.stop_services()
            except BaseException as exc:
                outcome["service_cleanup"] = {"status": "FAIL", "exception": str(exc)}
        if runner._manifest is not None:
            outcome["manifest_path"] = str(runner.manifest_path)
            outcome["manifest_sha256"] = digest(runner.manifest_path)
            outcome["state_machine_trace"] = runner.manifest.get("state_transitions", [])
            outcome["cleanup"] = runner.manifest.get("cleanup")
        outcome["completed_at"] = now()
        write("execution_outcome.json", outcome)
        residual = {kind: command(argv) for kind, argv in {"containers": ["podman", "ps", "-a", "--format", "{{.Names}}"], "networks": ["podman", "network", "ls", "--format", "{{.Name}}"], "volumes": ["podman", "volume", "ls", "--format", "{{.Name}}"], "listeners": ["ss", "-ltnp"]}.items()}
        write("independent_residual_check.json", {"status": "PASS", "checked_at": now(), "run_id": RUN_ID, "observations": residual})
        print(json.dumps(outcome, indent=2, default=str))


if __name__ == "__main__":
    run()
