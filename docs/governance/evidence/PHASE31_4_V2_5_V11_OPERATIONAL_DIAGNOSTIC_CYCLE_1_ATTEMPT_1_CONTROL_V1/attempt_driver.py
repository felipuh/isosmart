"""One-shot driver for V11 successor diagnostic cycle Attempt 1."""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import traceback
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[4]
CONTROL = Path(__file__).resolve().parent
AUTH = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_V11_OPERATIONAL_DIAGNOSTIC_CYCLE_1_ATTEMPT_1_AUTHORIZATION_V1.json"
AUTH_DOC = json.loads(AUTH.read_text(encoding="utf-8"))
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


def write(path, value, *, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w", encoding="utf-8") as output:
        json.dump(value, output, indent=2, default=str)
        output.write("\n")


def command(argv):
    result = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=30)
    return {"argv": argv, "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def inventory():
    return {kind: command(argv) for kind, argv in {
        "containers": ["podman", "ps", "-a", "--format", "{{.Names}}"],
        "networks": ["podman", "network", "ls", "--format", "{{.Name}}"],
        "volumes": ["podman", "volume", "ls", "--format", "{{.Name}}"],
        "listeners": ["ss", "-ltnp"],
    }.items()}


def matching_processes():
    matches = []
    marker = ("PHASE31_RUN_ID=" + RUN_ID).encode()
    for path in Path("/proc").glob("[0-9]*/environ"):
        try:
            if marker in path.read_bytes().split(b"\0"):
                matches.append(int(path.parent.name))
        except (OSError, PermissionError):
            continue
    return matches


def preflight():
    from foundation.phase31_4_integrity_generations import verify_v24_historical_integrity, verify_v25_current_integrity
    from foundation.phase31_4_v2_5_disposable_runner import (
        DIAGNOSTIC_CLASSIFICATION, RunInputs, _database_name, _resource_prefix, verify_authorization,
    )
    from foundation.phase31_4_v2_5_operational_adapters import repository_operational_environment

    assert subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip() == AUTH_DOC["git_state"]["commit"]
    assert digest(INTEGRITY) == AUTH_DOC["integrity"]["sha256"]
    assert digest(ROOT / AUTH_DOC["parent_cycle_authorization"]["artifact_path"]) == AUTH_DOC["parent_cycle_authorization"]["sha256"]
    assert digest(ROOT / AUTH_DOC["bearer_contract"]["artifact_path"]) == AUTH_DOC["bearer_contract"]["sha256"]
    current = verify_v25_current_integrity(ROOT)
    verify_v24_historical_integrity(ROOT)
    assert current["generation_id"] == AUTH_DOC["integrity"]["generation"]
    protected_paths = [item["path"] for item in current["sources"]]
    drift = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", *protected_paths], cwd=ROOT,
                           text=True, capture_output=True, check=True).stdout.splitlines()
    assert not drift, drift
    assert not EVIDENCE.exists()
    assert not matching_processes()

    inputs = RunInputs(repository_root=ROOT, run_id=RUN_ID, authorization_artifact=AUTH,
        expected_authorization_sha256=digest(AUTH), current_integrity_generation=AUTH_DOC["integrity"]["generation"],
        expected_integrity_sha256=digest(INTEGRITY), evidence_root=EVIDENCE,
        execution_kind=DIAGNOSTIC_CLASSIFICATION, validation_attempt=ATTEMPT,
        consumption_registry=ROOT / AUTH_DOC["consumption_registry"], readiness_timeout_seconds=90)
    verified = verify_authorization(inputs)
    observed = inventory()
    assert all(item["returncode"] == 0 for item in observed.values())
    prefix = _resource_prefix(AUTH_DOC["canonical_run_slug"])
    resources = {role: {"container": f"{prefix}_{role}", "network": f"{prefix}_{role}_net",
                        "volume": f"{prefix}_{role}_data", "database": _database_name(AUTH_DOC["canonical_run_slug"], role)}
                 for role in ("adminapps", "isosmart")}
    for resource in resources.values():
        for kind, key in (("containers", "container"), ("networks", "network"), ("volumes", "volume")):
            assert resource[key] not in observed[kind]["stdout"].splitlines()
    environment = repository_operational_environment(ROOT, os.environ)
    checks = {
        "status": "PASS", "checked_at": now(), "run_id": RUN_ID,
        "authorization_sha256": verified.authorization_sha256,
        "git_commit": AUTH_DOC["git_state"]["commit"], "protected_source_drift": drift,
        "integrity": {"generation": current["generation_id"], "protected_sources": len(protected_paths), "historical_v24": "PASS"},
        "planned_resources": resources, "resource_inventory": observed, "prior_processes": [],
        "evidence_root": "ABSENT", "previous_consumption": False,
        "readiness": {"adminapps": environment["PHASE31_ADMINAPPS_READINESS_PATH"],
                      "isosmart": environment["PHASE31_ISOSMART_READINESS_PATH"],
                      "credentials": "X-API-Key and runtime Bearer; raw values excluded"},
        "service_commands": {name: shlex.split(environment[key]) for name, key in {
            "adminapps": "PHASE31_ADMINAPPS_START_COMMAND", "isosmart": "PHASE31_ISOSMART_START_COMMAND"}.items()},
    }
    write(CONTROL / "preflight.json", checks, exclusive=True)
    return inputs


def run():
    inputs = preflight()
    from foundation.phase31_4_v2_5_disposable_runner import DisposableEvidenceRunner
    from foundation.phase31_4_v2_5_live_executor import Phase31_4V25LiveEvidenceExecutor, build_live_execution_context
    from foundation.phase31_4_v2_5_operational_adapters import SubprocessOperationalAdapter, repository_operational_environment

    runner = DisposableEvidenceRunner(inputs)
    holder = {}
    outcome = {"run_id": RUN_ID, "attempt": ATTEMPT, "started_at": now(),
               "verdict": "SUCCESSOR_CYCLE_ATTEMPT_1_FAIL", "raw_credentials_recorded": False}
    try:
        def live():
            if "executor" not in holder:
                context = build_live_execution_context(repository_root=ROOT, runner=runner, evidence_root=EVIDENCE,
                    authorization_reference=str(AUTH.relative_to(ROOT)), integrity_generation=AUTH_DOC["integrity"]["generation"])
                holder["executor"] = Phase31_4V25LiveEvidenceExecutor(
                    runner=runner, context=context,
                    adapter=SubprocessOperationalAdapter(environment=repository_operational_environment(ROOT, os.environ), timeout_seconds=90),
                    mode="diagnostic", allow_runtime_execution=False)
            return holder["executor"]

        def stage(manifest):
            result = dict(live().stage_ext(manifest))
            write(EVIDENCE / "stage_ext.json", result)
            bundle = live().build_capture_bundle()
            bundle.validate_for_retry(RUN_ID)
            write(EVIDENCE / "capture_bundle.json", {"status": "CAPTURE_BUNDLE_READY",
                "bundle": dataclasses.asdict(bundle), "run_id": RUN_ID})
            live().prepare_runtime()
            return dict(result, capture_bundle="PASS", capture_count=len(bundle.captures))

        runner.run_evidence(precreation=lambda manifest: live().precreation(manifest), stage_ext=stage)
        outcome["verdict"] = "SUCCESSOR_OPERATIONAL_DIAGNOSTIC_TARGET_ACHIEVED"
    except BaseException as exc:
        outcome.update({"exception_type": type(exc).__name__, "exception": str(exc), "traceback": traceback.format_exc()})
    finally:
        executor = holder.get("executor")
        if executor is not None:
            outcome["service_endpoints"] = dict(executor.context.service_urls)
            try:
                outcome["service_cleanup"] = executor.stop_services()
            except BaseException as exc:
                outcome["service_cleanup"] = {"status": "FAIL", "exception": str(exc)}
        if runner._manifest is not None:
            outcome["manifest_path"] = str(runner.manifest_path)
            outcome["manifest_sha256"] = digest(runner.manifest_path)
            outcome["state_machine_trace"] = runner.manifest.get("state_transitions", [])
            outcome["cleanup"] = runner.manifest.get("cleanup")
            outcome["failure"] = runner.manifest.get("failure")
        outcome["completed_at"] = now()
        write(EVIDENCE / "execution_outcome.json", outcome)
        observed = inventory()
        processes = matching_processes()
        cleanup = outcome.get("cleanup") or {}
        residual_status = "PASS" if not processes and cleanup.get("status") == "PASS" else "FAIL"
        write(EVIDENCE / "independent_residual_check.json", {
            "status": residual_status, "checked_at": now(), "run_id": RUN_ID,
            "matching_processes": processes, "observations": observed,
            "zero_residual_resources": residual_status == "PASS",
        })
        print(json.dumps(outcome, indent=2, default=str))


if __name__ == "__main__":
    run()
