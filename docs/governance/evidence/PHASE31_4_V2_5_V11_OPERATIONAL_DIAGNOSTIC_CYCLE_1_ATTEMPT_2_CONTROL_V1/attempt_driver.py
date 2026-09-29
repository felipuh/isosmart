"""One-shot driver for V11 successor diagnostic cycle Attempt 2."""
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
AUTH = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_V11_OPERATIONAL_DIAGNOSTIC_CYCLE_1_ATTEMPT_2_AUTHORIZATION_V1.json"
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


def matching_processes(run_id=RUN_ID):
    matches = []
    marker = ("PHASE31_RUN_ID=" + run_id).encode()
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
    assert not subprocess.run(["git", "diff", "--name-only", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    assert not EVIDENCE.exists()
    assert digest(ROOT / AUTH_DOC["remediation"]["reconciliation_path"]) == AUTH_DOC["remediation"]["reconciliation_sha256"]
    previous = ROOT / AUTH_DOC["attempt_1_evidence"]["path"]
    assert digest(previous) == AUTH_DOC["attempt_1_evidence"]["sha256"]
    assert json.loads(previous.read_text())["zero_residual_resources"] is True
    startup_env = dict(os.environ, PYTHONPATH=str(ROOT.parent / "adminapps/backend"),
                       DJANGO_SETTINGS_MODULE="config.settings", ENVIRONMENT="test",
                       BILLING_SCHEDULER_ENABLED="false", DB_HOST="127.0.0.1", DB_PORT="1")
    startup = subprocess.run([os.environ["PHASE31_ADMINAPPS_PYTHON"], "-c",
        "import django,config.settings; django.setup(); import django_apscheduler,importlib.metadata as m,json,sys; "
        "print(json.dumps({'ADMINAPPS_DISPOSABLE_DJANGO_SETUP':'PASS','django_apscheduler':m.version('django-apscheduler'),'python':sys.version,'interpreter':sys.executable}))"],
        cwd=ROOT.parent / "adminapps/backend", env=startup_env, capture_output=True, text=True, check=True)
    write(CONTROL / "runtime_import_preflight.json", json.loads(startup.stdout), exclusive=True)
    assert not matching_processes()

    inputs = RunInputs(repository_root=ROOT, run_id=RUN_ID, authorization_artifact=AUTH,
        expected_authorization_sha256=digest(AUTH), current_integrity_generation=AUTH_DOC["integrity"]["generation"],
        expected_integrity_sha256=digest(INTEGRITY), evidence_root=EVIDENCE,
        execution_kind=DIAGNOSTIC_CLASSIFICATION, validation_attempt=ATTEMPT,
        consumption_registry=ROOT / AUTH_DOC["consumption_registry"], readiness_timeout_seconds=90)
    verified = verify_authorization(inputs)
    observed = inventory()
    assert all(item["returncode"] == 0 for item in observed.values())
    old_preflight = json.loads((ROOT / "docs/governance/evidence/PHASE31_4_V2_5_V11_OPERATIONAL_DIAGNOSTIC_CYCLE_1_ATTEMPT_1_CONTROL_V1/preflight.json").read_text())
    assert not matching_processes(old_preflight["run_id"])
    for resource in old_preflight["planned_resources"].values():
        for kind, key in (("containers", "container"), ("networks", "network"), ("volumes", "volume")):
            assert resource[key] not in observed[kind]["stdout"].splitlines()
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


class EvidencePopen(subprocess.Popen):
    """Retain safe authority process metadata without recording its environment."""
    def __init__(self, args, *positional, **kwargs):
        self.authority_operation = isinstance(args, (list, tuple)) and len(args) >= 3 and args[-1] == "authority" and "phase31_4_v2_5_operational_actions.py" in str(args[-2])
        super().__init__(args, *positional, **kwargs)
        if self.authority_operation:
            self.authority_metadata = {"argv": list(args), "interpreter": args[0], "pid": self.pid,
                "cwd": str(kwargs.get("cwd", ROOT)), "started_at": now(),
                "package_environment": (kwargs.get("env") or {}).get("PHASE31_ADMINAPPS_PYTHON"),
                "exit_status": None}
            write(CONTROL / "authority_process.json", self.authority_metadata)

    def __exit__(self, *args):
        result = super().__exit__(*args)
        if self.authority_operation:
            self.authority_metadata.update(exit_status=self.returncode, completed_at=now())
            write(CONTROL / "authority_process.json", self.authority_metadata)
        return result


def run():
    inputs = preflight()
    from foundation.phase31_4_v2_5_disposable_runner import DisposableEvidenceRunner
    from foundation.phase31_4_v2_5_live_executor import Phase31_4V25LiveEvidenceExecutor, build_live_execution_context
    from foundation.phase31_4_v2_5_operational_adapters import SubprocessOperationalAdapter, repository_operational_environment

    runner = DisposableEvidenceRunner(inputs)
    holder = {}
    outcome = {"run_id": RUN_ID, "attempt": ATTEMPT, "started_at": now(),
               "verdict": "V11_ATTEMPT_2_FAIL", "raw_credentials_recorded": False}
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
        outcome["verdict"] = "V11_ATTEMPT_2_PASS"
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
        planned = json.loads((CONTROL / "preflight.json").read_text())["planned_resources"]
        absent = all(resource[key] not in observed[kind]["stdout"].splitlines()
                     for resource in planned.values()
                     for kind, key in (("containers", "container"), ("networks", "network"), ("volumes", "volume")))
        residual_status = "PASS" if not processes and absent and all(x["returncode"] == 0 for x in observed.values()) and cleanup.get("status") == "PASS" else "FAIL"
        write(EVIDENCE / "independent_residual_check.json", {
            "status": residual_status, "checked_at": now(), "run_id": RUN_ID,
            "matching_processes": processes, "observations": observed,
            "zero_residual_resources": residual_status == "PASS",
        })
        if residual_status != "PASS":
            outcome["verdict"] = "V11_ATTEMPT_2_PASS_WITH_CLEANUP_FAILURE" if outcome["verdict"] == "V11_ATTEMPT_2_PASS" else "V11_ATTEMPT_2_FAIL"
        write(EVIDENCE / "execution_outcome.json", outcome)
        print(json.dumps({"verdict":outcome["verdict"],"evidence":str(EVIDENCE),"cleanup":residual_status}))


if __name__ == "__main__":
    from foundation.phase31_4_adminapps_runtime import disposable_adminapps_runtime
    runtime_path = None
    try:
        with disposable_adminapps_runtime(ROOT) as (runtime_env, runtime_evidence):
            runtime_path = Path(runtime_evidence["interpreter"]).parents[1]
            os.environ["PHASE31_ADMINAPPS_PYTHON"] = runtime_env["PHASE31_ADMINAPPS_PYTHON"]
            write(CONTROL / "runtime_provisioning.json", runtime_evidence, exclusive=True)
            original_popen = subprocess.Popen
            try:
                subprocess.Popen = EvidencePopen
                run()
            finally:
                subprocess.Popen = original_popen
    finally:
        os.environ.pop("PHASE31_ADMINAPPS_PYTHON", None)
        write(CONTROL / "python_runtime_cleanup.json", {"temporary_runtime_absent": runtime_path is None or not runtime_path.exists(),
            "credential_environment_reference_absent": "PHASE31_ADMINAPPS_PYTHON" not in os.environ})
