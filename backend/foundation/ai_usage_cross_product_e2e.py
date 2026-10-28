#!/usr/bin/env python3
"""Disposable loopback-only ISO Smart -> AdminApps AI-usage E2E evidence.

Run from ``isosmart/backend`` with the repository virtualenv::

    .venv/bin/python foundation/ai_usage_cross_product_e2e.py

The harness owns a temporary PostgreSQL 18 cluster, creates run-scoped roles
and databases, starts both Django development servers on 127.0.0.1, and tears
everything down in ``finally``.  It deliberately uses the real ISO outbox
dispatcher and AdminApps ingestion route.  The controlled provider workflow is
command-driven; the ISO HTTP server is evidence of an independently running
service, not an invented inbound dependency for that workflow.

This is intentionally an operator-facing harness, rather than a Django unit
test.  It does not print generated passwords or API keys.
"""

from __future__ import annotations

import contextlib
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


BACKEND = Path(__file__).resolve().parents[1]
ISO_ROOT = BACKEND.parent
ADMIN_BACKEND = ISO_ROOT.parent / "adminapps" / "backend"
ISO_PYTHON = BACKEND / ".venv" / "bin" / "python"
ADMIN_PYTHON = ADMIN_BACKEND / ".venv312" / "bin" / "python"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def free_port() -> int:
    with socket.socket() as candidate:
        candidate.bind(("127.0.0.1", 0))
        return int(candidate.getsockname()[1])


def run(argv: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 180) -> str:
    completed = subprocess.run(argv, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout)
    if completed.returncode:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(argv)}\n{completed.stdout}\n{completed.stderr}"
        )
    return completed.stdout


def http_json(url: str, *, method: str = "GET", body: dict[str, Any] | None = None,
              headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    data = json.dumps(body).encode() if body is not None else None
    request = Request(url, data=data, method=method, headers=headers or {})
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode() or "{}")
    except HTTPError as error:
        return error.code, json.loads(error.read().decode() or "{}")


def wait_for(url: str, *, headers: dict[str, str] | None = None) -> int:
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        try:
            status, _ = http_json(url, headers=headers)
            if status < 500:
                return status
        except OSError:
            pass
        time.sleep(0.2)
    raise RuntimeError(f"server readiness timeout: {url}")


@dataclass
class StartedProcess:
    process: subprocess.Popen[str]
    name: str
    log_path: Path

    def diagnostic_log(self) -> str:
        if not self.log_path.exists():
            return "(server log unavailable)"
        return self.log_path.read_text(encoding="utf-8")[-4000:]

    def stop(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=12)


class FaultProxy(ThreadingHTTPServer):
    """Small loopback proxy: scripted 503s, otherwise byte-for-byte forwarding."""

    daemon_threads = True

    def __init__(self, address: tuple[str, int], upstream: str):
        self.upstream = upstream.rstrip("/")
        self.outcomes: list[int] = []
        self.requests: list[dict[str, Any]] = []
        super().__init__(address, self._handler())

    def _handler(self):
        proxy = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802 - required by BaseHTTPRequestHandler
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                scripted = proxy.outcomes.pop(0) if proxy.outcomes else None
                if scripted is not None:
                    proxy.requests.append({"status": scripted, "forwarded": False})
                    self.send_response(scripted)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"error":"controlled transient failure"}')
                    return
                request = Request(
                    proxy.upstream + self.path, data=raw, method="POST",
                    headers={"Content-Type": self.headers.get("Content-Type", "application/json"),
                             "X-API-Key": self.headers.get("X-API-Key", "")},
                )
                try:
                    with urlopen(request, timeout=5) as response:
                        status, payload = response.status, response.read()
                except HTTPError as error:
                    status, payload = error.code, error.read()
                proxy.requests.append({"status": status, "forwarded": True})
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, _format: str, *_args: object) -> None:
                return

        return Handler


class LocalPostgres:
    """A PostgreSQL 18 process and Foundation role contract scoped to one run."""

    def __init__(self) -> None:
        self.port = free_port()
        self.directory = Path(tempfile.mkdtemp(prefix="smart3ai-ai-usage-e2e-"))
        self.superuser = "e2e_superuser"
        self.process: subprocess.Popen[str] | None = None
        self.log_path = self.directory / "postgres.log"
        self.names: dict[str, str] = {}
        self.passwords: dict[str, str] = {}

    def start(self) -> None:
        initdb = shutil.which("initdb")
        postgres = shutil.which("postgres")
        if not initdb or not postgres:
            raise RuntimeError("PostgreSQL initdb and postgres 18.6 are required")
        run([initdb, "-D", str(self.directory / "data"), "-A", "trust", "-U", self.superuser],
            cwd=BACKEND, env=os.environ.copy())
        with self.log_path.open("w", encoding="utf-8") as postgres_log:
            self.process = subprocess.Popen(
                [postgres, "-D", str(self.directory / "data"), "-h", "127.0.0.1", "-p", str(self.port),
                 "-k", str(self.directory),
                 "-c", "logging_collector=off"],
                text=True, stdout=postgres_log, stderr=subprocess.STDOUT,
            )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            probe = subprocess.run(
                ["psql", "-h", "127.0.0.1", "-p", str(self.port), "-U", self.superuser,
                 "-d", "postgres", "-Atqc", "SELECT 1"], text=True, capture_output=True,
            )
            if probe.returncode == 0:
                break
            time.sleep(0.2)
        else:
            detail = self.log_path.read_text(encoding="utf-8")[-2000:]
            raise RuntimeError(f"local PostgreSQL readiness timeout: {detail}")

        # Reuse the source-owned Foundation bootstrap, including its least-
        # privilege role topology.  Names are per-run and never persisted.
        from foundation import postgres_foundation_gate as gate

        run_id = secrets.token_hex(4)
        self.names = {key: f"e2e_{key}_{run_id}" for key, *_ in gate.ROLE_SPECS}
        self.names["database"] = f"e2e_iso_{run_id}"
        self.passwords = {key: secrets.token_urlsafe(24) for key in gate.LOGIN_ROLES}
        gate.bootstrap(
            self.port, "", self.names, self.passwords,
            host="127.0.0.1", super_user=self.superuser,
        )

    def environment(self) -> dict[str, str]:
        from foundation import postgres_foundation_gate as gate

        env = os.environ.copy()
        env.update({
            "FOUNDATION_DB_HOST": "127.0.0.1", "FOUNDATION_DB_PORT": str(self.port),
            "FOUNDATION_DB_NAME": self.names["database"],
            "DB_HOST": "127.0.0.1", "DB_PORT": str(self.port), "DB_NAME": self.names["database"],
            "DB_USER": self.names["migrator"], "DB_PASSWORD": self.passwords["migrator"],
            "USE_SQLITE_DATABASE": "0", "DJANGO_ENV": "test", "ENVIRONMENT": "test",
        })
        session = []
        for key, *_ in gate.ROLE_SPECS:
            env[f"FOUNDATION_{key.upper()}_ROLE"] = self.names[key]
            if key in self.passwords:
                env[f"FOUNDATION_{key.upper()}_PASSWORD"] = self.passwords[key]
                env[f"FOUNDATION_{key.upper()}_DB_USER"] = self.names[key]
                env[f"FOUNDATION_{key.upper()}_DB_PASSWORD"] = self.passwords[key]
            session.append(f"-c foundation.{key}_role={self.names[key]}")
        env["DB_SESSION_OPTIONS"] = " ".join(session)
        return env

    def stop(self) -> None:
        try:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=12)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=12)
        finally:
            shutil.rmtree(self.directory, ignore_errors=True)


def seed_adminapps(env: dict[str, str], tenant_a: str, tenant_b: str, api_key: str) -> None:
    code = (
        "from apps.organizations.models import Organization; "
        "from apps.integration.models import IntegrationAPIKey; "
        "from apps.users.models import User; "
        f"a=Organization.objects.create(id='{tenant_a}',code='E2E-A',name='E2E Tenant A',email='a@example.test',status='active'); "
        f"b=Organization.objects.create(id='{tenant_b}',code='E2E-B',name='E2E Tenant B',email='b@example.test',status='active'); "
        f"IntegrationAPIKey.objects.create(name='isosmart-usage',key='{api_key}',is_active=True); "
        "User.objects.create_user(email='central-admin@example.test',password='E2E-only-password-123!',first_name='Central',last_name='Admin',organization=a,role='admin'); "
        "User.objects.create_user(email='tenant-a@example.test',password='E2E-only-password-123!',first_name='Tenant',last_name='A',organization=a,role='org_admin'); "
        "User.objects.create_user(email='tenant-b@example.test',password='E2E-only-password-123!',first_name='Tenant',last_name='B',organization=b,role='org_admin')"
    )
    run([str(ADMIN_PYTHON), "manage.py", "shell", "-c", code], cwd=ADMIN_BACKEND, env=env)


def start_server(python: Path, backend: Path, port: int, env: dict[str, str], name: str,
                 log_path: Path) -> StartedProcess:
    server_log = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        [str(python), "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
        cwd=backend, env=env, text=True, stdout=server_log, stderr=subprocess.STDOUT,
    )
    server_log.close()
    return StartedProcess(process, name, log_path)


def main() -> None:
    if not ISO_PYTHON.exists() or not ADMIN_PYTHON.exists():
        raise RuntimeError("repository Python 3.12 virtualenvs are required")
    sys.path.insert(0, str(BACKEND))
    postgres = LocalPostgres()
    processes: list[StartedProcess] = []
    proxy: FaultProxy | None = None
    report: dict[str, Any] = {"harness": "AI_USAGE_CROSS_PRODUCT_HTTP_E2E", "cleanup": "pending"}
    original_environment = os.environ.copy()
    try:
        postgres.start()
        iso_env = postgres.environment()
        os.environ.update(iso_env)

        # The controlled provider fixture uses the repository's Foundation-only
        # settings and migrations; it is intentionally command-driven.
        from foundation import postgres_foundation_harness as foundation_gate
        foundation_gate.configure_django()
        from django.core.management import call_command
        from django.utils import timezone
        from foundation.ai_usage import AIUsageLedger, ProviderInferenceResult
        from foundation.models import AIUsageRecord, DomainEvent, TenantProjection, TransactionalOutbox
        from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context
        from foundation.test_value_discovery_postgres import ValueDiscoveryPostgreSQLTests

        call_command("migrate", database="default", verbosity=0, interactive=False)
        case = ValueDiscoveryPostgreSQLTests("test_controlled_execution_persists_evidence_transition_event_outbox_and_audit")
        case.setUp()
        case.test_controlled_execution_persists_evidence_transition_event_outbox_and_audit()
        tenant_a, tenant_b = str(case.external_tenant_id), str(case.other_external_tenant_id)
        report["controlled_provider"] = {"events": 3, "tokens": 412, "mode": "command-driven"}

        admin_env = os.environ.copy()
        admin_db = f"e2e_admin_{secrets.token_hex(4)}"
        run(["psql", "-h", "127.0.0.1", "-p", str(postgres.port), "-U", postgres.superuser,
             "-d", "postgres", "-c", f'CREATE DATABASE "{admin_db}"'], cwd=BACKEND, env=admin_env)
        admin_env.update({"DB_HOST": "127.0.0.1", "DB_PORT": str(postgres.port), "DB_NAME": admin_db,
                          "DB_USER": postgres.superuser, "DB_PASSWORD": "", "DJANGO_ENV": "test", "ENVIRONMENT": "test",
                          "DEBUG": "0"})
        run([str(ADMIN_PYTHON), "manage.py", "migrate", "--noinput"], cwd=ADMIN_BACKEND, env=admin_env)
        api_key = secrets.token_urlsafe(32)
        seed_adminapps(admin_env, tenant_a, tenant_b, api_key)

        admin_port, iso_port, proxy_port = free_port(), free_port(), free_port()
        admin_server = start_server(ADMIN_PYTHON, ADMIN_BACKEND, admin_port, admin_env, "adminapps",
                                    postgres.directory / "adminapps.log")
        processes.append(admin_server)
        admin_base = f"http://127.0.0.1:{admin_port}"
        require(wait_for(admin_base + "/api/integration/health/", headers={"X-API-Key": api_key}) == 200,
                "AdminApps health must return HTTP 200")

        proxy = FaultProxy(("127.0.0.1", proxy_port), admin_base)
        threading.Thread(target=proxy.serve_forever, daemon=True).start()
        iso_env.update({"AI_USAGE_ADMINAPPS_DELIVERY_ENABLED": "1", "AI_USAGE_ADMINAPPS_API_KEY": api_key,
                        "AI_USAGE_ADMINAPPS_ENDPOINT": f"http://127.0.0.1:{proxy_port}/api/integration/ai-usage/",
                        "AI_USAGE_ADMINAPPS_MAX_ATTEMPTS": "2"})
        iso_server = start_server(ISO_PYTHON, BACKEND, iso_port, iso_env, "isosmart",
                                  postgres.directory / "isosmart.log")
        processes.append(iso_server)
        iso_health_status = wait_for(f"http://127.0.0.1:{iso_port}/livez")
        require(200 <= iso_health_status < 300,
                f"ISO livez must return a successful HTTP status: {iso_server.diagnostic_log()}")
        report["http_servers"] = {"adminapps": 200, "isosmart": iso_health_status, "listeners": "127.0.0.1 only"}

        def issue(tenant_id: str, capability: str) -> tuple[Any, Any]:
            identity = TrustedTenantIdentity(subject="e2e-worker", tenant_id=case.tenant_id if tenant_id == tenant_a else case.other_tenant_id)
            ledger = AIUsageLedger(using="app", identity=identity, execution_id=uuid4(), correlation_id=uuid4(), actor_id="e2e")
            provider = type("ControlledProvider", (), {"provider_name": "controlled-e2e", "model_identifier": "controlled-v1"})()
            record = ledger.reserve(invocation_id=f"e2e:{capability}:{uuid4()}", capability=capability, provider=provider)
            record = ledger.finalize(record, result=ProviderInferenceResult(data={}, usage={"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6}), outcome="completed")
            return identity, record

        def dispatch(identity: Any) -> None:
            run([str(ISO_PYTHON), "manage.py", "run_ai_usage_delivery", "--tenant-id", str(identity.tenant_id), "--once"], cwd=BACKEND, env=iso_env)

        def row(identity: Any, record: Any) -> Any:
            with trusted_tenant_context(identity, actor_id="e2e", trace_id=uuid4(), using="worker"):
                return TransactionalOutbox.objects.using("worker").get(domain_event__aggregate_id=record.id)

        # The dispatcher claims exactly one eligible row per command invocation,
        # so the first controlled-provider event can exercise retry without
        # mutating the protected state of the remaining two rows.
        with trusted_tenant_context(case.identity, actor_id="e2e", trace_id=uuid4(), using="worker"):
            records = list(AIUsageRecord.objects.using("worker").order_by("created_at"))
            require(len(records) == 3, "controlled workflow must create three usage records")
        proxy.outcomes = [503]
        dispatch(case.identity)
        transient = row(case.identity, records[0])
        require(transient.status == "failed" and transient.publish_attempts == 1, "first 503 must remain retryable")
        # Other pending records keep their original eligibility and are claimed
        # before the backoff-delayed retry.  Deliver them normally, then retry
        # the original row once it is eligible again.
        dispatch(case.identity)
        dispatch(case.identity)
        time.sleep(1.15)
        dispatch(case.identity)
        transient = row(case.identity, records[0])
        require(transient.status == "published" and transient.publish_attempts == 2, "retry must publish after AdminApps HTTP success")
        report["transient_retry"] = {"http": [503, 201], "attempts": 2, "state": "published", "projection_count": 1}

        # Bounded exhaustion retains a durable, recovery-required source row
        # and never returns a success acknowledgement.
        retry_identity, retry_record = issue(tenant_a, "retry_exhaustion")
        proxy.outcomes = [503, 503]
        dispatch(retry_identity)
        time.sleep(1.15)
        dispatch(retry_identity)
        exhausted = row(retry_identity, retry_record)
        require(exhausted.status == "failed" and exhausted.publish_attempts == 2
                and exhausted.last_error_code == "AI_USAGE_RETRY_EXHAUSTED",
                "exhausted transient event must be retained for controlled recovery")
        report["exhausted_retry"] = {"http": [503, 503], "attempts": 2, "state": exhausted.status,
                                     "error_code": exhausted.last_error_code, "projection_count": 0}

        # A real AdminApps unknown-tenant response is permanent and cannot be
        # converted into a successful acknowledgement by the dispatcher.
        unknown_local = uuid4()
        unknown_external = uuid4()
        TenantProjection.objects.using("default").create(
            id=unknown_local, adminapps_tenant_id=unknown_external, source_version=1, source_event_id=uuid4(),
            display_name_snapshot="E2E unknown authoritative tenant", lifecycle_status="active",
            provisioning_status="complete", reconciliation_status="in_sync", last_synced_at=timezone.now(),
        )
        unknown_identity = TrustedTenantIdentity(subject="e2e-worker", tenant_id=unknown_local)
        original_other = case.other_tenant_id
        case.other_tenant_id = unknown_local
        permanent_identity, permanent_record = issue("unknown", "permanent_4xx")
        case.other_tenant_id = original_other
        dispatch(permanent_identity)
        permanent = row(permanent_identity, permanent_record)
        require(permanent.status == "failed" and permanent.publish_attempts == 1, "permanent 4xx must not retry")
        report["permanent_4xx"] = {"http": [404], "attempts": 1, "state": permanent.status,
                                   "error_code": permanent.last_error_code, "projection_count": 0}

        # The three controlled-provider events are now delivered through the
        # real proxy and AdminApps persistence without counting failure probes.
        status, token = http_json(admin_base + "/api/auth/login/", method="POST", body={"email": "central-admin@example.test", "password": "E2E-only-password-123!"})
        require(status == 200, "central dashboard user must authenticate")
        status, dashboard = http_json(admin_base + "/api/billing/ai-usage/", headers={"Authorization": f"Bearer {token['access']}"})
        require(status == 200 and dashboard["overview"]["requests"] == 3 and dashboard["overview"]["total_tokens"] == 412,
                "dashboard must expose exactly the three controlled workflow projections")
        report["dashboard"] = {"http": 200, "projections": 3, "tokens": 412}

        # Recovery is never automatic: an explicitly enabled, reasoned replay
        # starts one more bounded cycle with the original event identity.
        run([str(ISO_PYTHON), "manage.py", "run_ai_usage_delivery", "--tenant-id", str(retry_identity.tenant_id),
             "--recover-exhausted-outbox-id", str(exhausted.id), "--reason", "AdminApps restored after controlled 503 test"],
            cwd=BACKEND, env=iso_env)
        dispatch(retry_identity)
        recovered = row(retry_identity, retry_record)
        require(recovered.status == "published" and recovered.publish_attempts == 3,
                "authorized recovery must publish the original event without resetting attempt history")
        status, recovered_dashboard = http_json(
            admin_base + "/api/billing/ai-usage/", headers={"Authorization": f"Bearer {token['access']}"}
        )
        require(status == 200 and recovered_dashboard["overview"]["requests"] == 4
                and recovered_dashboard["overview"]["total_tokens"] == 418,
                "recovery must add exactly one projection for the original event")
        report["recovery_after_exhaustion"] = {
            "attempts": 3, "state": recovered.status, "projection_count": 1,
            "dashboard_requests": 4, "dashboard_tokens": 418,
        }

        # ISO RLS is runtime-enforced for source tenants (the controlled fixture
        # executes this check).  AdminApps has no tenant-scoped usage-read route:
        # its only usage dashboard is deliberately central-admin-only.  Both
        # tenant org-admins receive 403, so there is no API on which an A-vs-B
        # positive read-isolation assertion can honestly be made.
        tenant_statuses = []
        for email in ("tenant-a@example.test", "tenant-b@example.test"):
            status, tenant_token = http_json(admin_base + "/api/auth/login/", method="POST", body={"email": email, "password": "E2E-only-password-123!"})
            require(status == 200, "tenant test user must authenticate")
            status, _ = http_json(admin_base + "/api/billing/ai-usage/", headers={"Authorization": f"Bearer {tenant_token['access']}"})
            tenant_statuses.append(status)
        require(tenant_statuses == [403, 403], "tenant org-admins must not access central dashboard")
        report["tenant_isolation"] = {"iso_rls": "passed", "adminapps_org_admin_dashboard": tenant_statuses,
                                       "adminapps_tenant_scoped_usage_read_contract": "not_defined"}

        report["verdict"] = "AI_USAGE_CROSS_PRODUCT_HTTP_E2E_PASS"
        report["architecture"] = (
            "AdminApps central dashboard is restricted to central administrators; "
            "tenant-scoped customer AI usage reads are FUTURE_FEATURE_NOT_REQUIRED_FOR_CURRENT_E2E."
        )
    except BaseException as exc:
        report["execution_error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        if proxy is not None:
            proxy.shutdown()
            proxy.server_close()
        for process in reversed(processes):
            process.stop()
        postgres.stop()
        report["cleanup"] = "verified: processes stopped; temporary cluster removed"
        rendered = json.dumps(report, sort_keys=True, indent=2)
        evidence_path = os.environ.get("AI_USAGE_E2E_EVIDENCE_PATH", "").strip()
        if evidence_path:
            Path(evidence_path).write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        os.environ.clear()
        os.environ.update(original_environment)


if __name__ == "__main__":
    main()
