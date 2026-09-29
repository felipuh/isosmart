"""Real subprocess/HTTP adapters for the V2.5 live evidence executor.

Each one-shot operation is an explicit command supplied by release tooling and
must emit one JSON object on its final stdout line.  Services are real child
processes with dynamic ports and HTTP readiness checks.  There is deliberately
no fixture, ORM shortcut, or success fallback.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import hashlib
import os
from pathlib import Path
import shlex
import socket
import subprocess
import secrets
import time
from typing import Any, Mapping, Sequence
from urllib.request import urlopen

from .phase31_4_v2_5_live_executor import LiveExecutionContext, LiveExecutorError


class SubprocessOperationalAdapter:
    test_only = False

    _COMMANDS = {
        "bootstrap_adminapps": "PHASE31_ADMINAPPS_BOOTSTRAP_COMMAND",
        "bootstrap_isosmart": "PHASE31_ISOSMART_BOOTSTRAP_COMMAND",
        "authority": "PHASE31_ADMINAPPS_AUTHORITY_COMMAND",
        "delivery": "PHASE31_EVENT_DELIVERY_COMMAND",
        "tenant_projection_readback": "PHASE31_TENANT_PROJECTION_READBACK_COMMAND",
        "user_projection_readback": "PHASE31_USER_PROJECTION_READBACK_COMMAND",
        "organization_create": "PHASE31_QMS_ORGANIZATION_CREATE_COMMAND",
        "organization_readback": "PHASE31_QMS_ORGANIZATION_READBACK_COMMAND",
        "process_create": "PHASE31_PROCESS_CREATE_COMMAND",
        "process_readback": "PHASE31_PROCESS_READBACK_COMMAND",
    }

    def __init__(self, *, environment: Mapping[str, str], timeout_seconds: float = 60.0) -> None:
        self.environment = dict(environment)
        self.environment.setdefault("PHASE31_INTEGRATION_KEY", secrets.token_urlsafe(32))
        self.environment.setdefault("PHASE31_EVENT_KEY", secrets.token_urlsafe(32))
        self.timeout_seconds = timeout_seconds
        self.processes: dict[str, subprocess.Popen[str]] = {}
        self.logs: list[Any] = []

    @staticmethod
    def _free_port() -> int:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0)); return int(sock.getsockname()[1])

    def _env(self, context: LiveExecutionContext, extra: Mapping[str, Any] | None = None) -> dict[str, str]:
        env = os.environ.copy(); env.update(self.environment); env.update(context.environment)
        env.update(PHASE31_ADMINAPPS_DB_ENDPOINT=context.adminapps_db_endpoint,
                   PHASE31_ISOSMART_DB_ENDPOINT=context.isosmart_db_endpoint,
                   PHASE31_RUN_ID=context.run_id, PHASE31_EVIDENCE_ROOT=str(context.evidence_root))
        prefix = "p314_" + hashlib.sha256(context.run_slug.encode()).hexdigest()[:12]
        roles = ("migrator","app","worker","projector","audit_writer","normative_curator","agent_catalog_curator","human_approver","execution_authorizer","executor","qms_action_owner","learning_governance","learning_reviewer","learning_approver","learning_authorizer","learning_application_executor","knowledge_rule_application_owner","rule_governance_owner","rule_publisher","rule_activator","rule_adopter","rule_resolver","release_repair","release_controller")
        env.setdefault("PHASE31_ROLE_PREFIX", prefix)
        env.setdefault("PHASE31_ROLE_OPTIONS", " ".join(f"-c foundation.{role}_role={prefix}_{role}" for role in roles))
        for key, value in (extra or {}).items():
            if value is not None: env[f"PHASE31_INPUT_{str(key).upper()}"] = str(value)
        return env

    def _command(self, operation: str) -> Sequence[str]:
        variable = self._COMMANDS[operation]
        value = self.environment.get(variable)
        if not value: raise LiveExecutorError("OPERATIONAL_ADAPTER_REQUIRED", f"required command is not configured: {variable}")
        argv = shlex.split(value)
        if not argv: raise LiveExecutorError("OPERATIONAL_ADAPTER_REQUIRED", f"empty command: {variable}")
        return argv

    def _run(self, operation: str, context: LiveExecutionContext, extra: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        started = datetime.now(timezone.utc).isoformat()
        completed = subprocess.run(self._command(operation), cwd=context.repository_root,
            env=self._env(context, extra), text=True, capture_output=True, timeout=self.timeout_seconds, check=False)
        log_path = context.evidence_root / f"{operation}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(completed.stdout + completed.stderr, encoding="utf-8")
        if completed.returncode:
            raise LiveExecutorError("OPERATIONAL_COMMAND_FAILURE", f"{operation} exited {completed.returncode}; log={log_path}", step=operation)
        try: payload = json.loads(completed.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError) as exc:
            raise LiveExecutorError("OPERATIONAL_COMMAND_FAILURE", f"{operation} did not emit JSON; log={log_path}") from exc
        if not isinstance(payload, dict): raise LiveExecutorError("OPERATIONAL_COMMAND_FAILURE", f"{operation} JSON must be an object")
        return {**payload, "command": list(self._command(operation)), "started_at": started,
                "completed_at": datetime.now(timezone.utc).isoformat(), "log": str(log_path)}

    def bootstrap_adminapps(self, context: LiveExecutionContext) -> Mapping[str, Any]: return self._run("bootstrap_adminapps", context)
    def bootstrap_isosmart(self, context: LiveExecutionContext) -> Mapping[str, Any]: return self._run("bootstrap_isosmart", context)

    def _start(self, name: str, context: LiveExecutionContext) -> Mapping[str, Any]:
        variable = f"PHASE31_{name.upper()}_START_COMMAND"
        raw = self.environment.get(variable)
        if not raw: raise LiveExecutorError("OPERATIONAL_ADAPTER_REQUIRED", f"required command is not configured: {variable}")
        port = self._free_port(); base_url = f"http://127.0.0.1:{port}"
        env = self._env(context); env.update(PORT=str(port), PHASE31_SERVICE_PORT=str(port))
        if name == "adminapps": env["ADMIN_APPS_BASE_URL"] = base_url
        else: env["ISO_SMART_BASE_URL"] = base_url
        log_path = context.evidence_root / f"{name}_service.log"; log_path.parent.mkdir(parents=True, exist_ok=True)
        log = log_path.open("w", encoding="utf-8"); self.logs.append(log)
        process = subprocess.Popen(shlex.split(raw), cwd=context.repository_root, env=env, stdout=log, stderr=subprocess.STDOUT, text=True)
        health_path = self.environment.get(f"PHASE31_{name.upper()}_READINESS_PATH", "/health/")
        deadline = time.monotonic() + self.timeout_seconds; last_error = ""
        while time.monotonic() < deadline:
            if process.poll() is not None: raise LiveExecutorError(f"{name.upper()}_START_FAILURE", f"service exited {process.returncode}; log={log_path}")
            try:
                with urlopen(base_url + health_path, timeout=1) as response:
                    if 200 <= response.status < 400:
                        self.processes[name] = process
                        return {"status": "PASS", "pid": process.pid, "readiness": "PASS", "base_url": base_url,
                                "readiness_url": base_url + health_path, "log": str(log_path), "started_at": datetime.now(timezone.utc).isoformat()}
            except Exception as exc: last_error = str(exc)
            time.sleep(.2)
        process.terminate(); process.wait(timeout=10)
        raise LiveExecutorError(f"{name.upper()}_START_FAILURE", f"readiness timeout: {last_error}; log={log_path}")

    def start_adminapps(self, context: LiveExecutionContext) -> Mapping[str, Any]: return self._start("adminapps", context)
    def start_isosmart(self, context: LiveExecutionContext) -> Mapping[str, Any]: return self._start("isosmart", context)
    def create_adminapps_authority(self, context: LiveExecutionContext) -> Mapping[str, Any]: return self._run("authority", context)
    def deliver_projection_events(self, context: LiveExecutionContext, authority: Mapping[str, Any]) -> Mapping[str, Any]: return self._run("delivery", context, authority)
    def read_tenant_projection(self, context: LiveExecutionContext, delivery: Mapping[str, Any]) -> Mapping[str, Any]: return self._run("tenant_projection_readback", context, delivery)
    def read_user_projection(self, context: LiveExecutionContext, delivery: Mapping[str, Any]) -> Mapping[str, Any]: return self._run("user_projection_readback", context, delivery)
    def create_qms_organization(self, context: LiveExecutionContext, authority: Mapping[str, Any], delivery: Mapping[str, Any]) -> Mapping[str, Any]: return self._run("organization_create", context, {**authority, **delivery})
    def read_qms_organization(self, context: LiveExecutionContext, returned_id: str) -> Mapping[str, Any]: return self._run("organization_readback", context, {"id": returned_id})
    def create_process(self, context: LiveExecutionContext, organization_id: str, authority: Mapping[str, Any]) -> Mapping[str, Any]: return self._run("process_create", context, {**authority, "organization_id": organization_id})
    def read_process(self, context: LiveExecutionContext, returned_id: str) -> Mapping[str, Any]: return self._run("process_readback", context, {"id": returned_id})

    def stop_services(self) -> Mapping[str, Any]:
        stopped: dict[str, Any] = {}
        for name, process in reversed(tuple(self.processes.items())):
            process.terminate()
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
            stopped[name] = {"pid": process.pid, "exit_code": process.returncode, "absent": process.poll() is not None}
        for log in self.logs: log.close()
        self.processes.clear(); self.logs.clear()
        return {"status": "PASS" if all(item["absent"] for item in stopped.values()) else "FAIL", "services": stopped}


def repository_operational_environment(repository_root: str | Path,
                                       base: Mapping[str, str] | None = None) -> dict[str, str]:
    """Build the concrete command map shipped with this repository."""
    root = Path(repository_root).resolve()
    python = root / "backend/.venv/bin/python"
    actions = root / "docs/governance/tools/phase31_4_v2_5_operational_actions.py"
    if not python.is_file() or not actions.is_file():
        raise LiveExecutorError("OPERATIONAL_ADAPTER_REQUIRED", "repository operational runtime is incomplete")
    env = dict(base or {})
    for operation, variable in SubprocessOperationalAdapter._COMMANDS.items():
        env.setdefault(variable, shlex.join((str(python), str(actions), operation)))
    env.setdefault("PHASE31_ADMINAPPS_START_COMMAND", shlex.join((str(python), str(actions), "service", "adminapps")))
    env.setdefault("PHASE31_ISOSMART_START_COMMAND", shlex.join((str(python), str(actions), "service", "isosmart")))
    env.setdefault("PHASE31_ADMINAPPS_READINESS_PATH", "/api/health/")
    env.setdefault("PHASE31_ISOSMART_READINESS_PATH", "/health")
    return env
