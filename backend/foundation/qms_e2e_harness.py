"""Controlled browser E2E harness for the QMS slice.

Runs inside the disposable PostgreSQL gate (FOUNDATION_HARNESS=foundation/qms_e2e_harness.py):
migrates, seeds one tenant with two users, serves the real ISO Smart backend with a
controlled principal, and runs the Playwright spec against it. CONTROLLED_INTEGRATION_E2E,
not a live AdminApps run.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from uuid import uuid4

BACKEND = Path(__file__).resolve().parents[1]
FRONTEND = BACKEND.parent / "frontend"
BACKEND_PORT = 8765
FRONT_PORT = 3011

ROLE_BINDINGS = (
    ("app", "FOUNDATION_APP_ROLE"), ("worker", "FOUNDATION_WORKER_ROLE"),
    ("projector", "FOUNDATION_PROJECTOR_ROLE"), ("audit_writer", "FOUNDATION_AUDIT_WRITER_ROLE"),
    ("normative_curator", "FOUNDATION_NORMATIVE_CURATOR_ROLE"),
    ("agent_catalog_curator", "FOUNDATION_AGENT_CATALOG_CURATOR_ROLE"),
    ("human_approver", "FOUNDATION_HUMAN_APPROVER_ROLE"),
    ("execution_authorizer", "FOUNDATION_EXECUTION_AUTHORIZER_ROLE"),
    ("executor", "FOUNDATION_EXECUTOR_ROLE"), ("qms_action_owner", "FOUNDATION_QMS_ACTION_OWNER_ROLE"),
    ("learning_governance", "FOUNDATION_LEARNING_GOVERNANCE_ROLE"),
    ("learning_reviewer", "FOUNDATION_LEARNING_REVIEWER_ROLE"),
    ("learning_approver", "FOUNDATION_LEARNING_APPROVER_ROLE"),
    ("learning_authorizer", "FOUNDATION_LEARNING_AUTHORIZER_ROLE"),
    ("learning_application_executor", "FOUNDATION_LEARNING_APPLICATION_EXECUTOR_ROLE"),
    ("knowledge_rule_application_owner", "FOUNDATION_KNOWLEDGE_RULE_APPLICATION_OWNER_ROLE"),
    ("rule_governance_owner", "FOUNDATION_RULE_GOVERNANCE_OWNER_ROLE"),
    ("rule_publisher", "FOUNDATION_RULE_PUBLISHER_ROLE"), ("rule_activator", "FOUNDATION_RULE_ACTIVATOR_ROLE"),
    ("rule_adopter", "FOUNDATION_RULE_ADOPTER_ROLE"), ("rule_resolver", "FOUNDATION_RULE_RESOLVER_ROLE"),
    ("release_repair", "FOUNDATION_RELEASE_REPAIR_ROLE"), ("release_controller", "FOUNDATION_RELEASE_CONTROLLER_ROLE"),
)


def prepare_env():
    os.environ.update({
        "DJANGO_SETTINGS_MODULE": "backend.settings_qms_e2e_controlled",
        "ISO_SMART_POSTGRES_INTEGRATION": "1", "QMS_E2E_CONTROLLED_INTEGRATION": "1",
        "USE_SQLITE_DATABASE": "0", "DJANGO_ENV": "development",
        "DB_NAME": os.environ["FOUNDATION_DB_NAME"], "DB_USER": os.environ["FOUNDATION_MIGRATOR_ROLE"],
        "DB_PASSWORD": os.environ["FOUNDATION_MIGRATOR_PASSWORD"],
        "DB_HOST": os.environ["FOUNDATION_DB_HOST"], "DB_PORT": os.environ["FOUNDATION_DB_PORT"],
        "DB_SESSION_OPTIONS": " ".join(
            f"-c foundation.{setting}_role={os.environ[name]}" for setting, name in ROLE_BINDINGS),
    })


def seed():
    import django
    from django.core.management import call_command
    from django.utils import timezone

    sys.path.insert(0, str(BACKEND))
    os.chdir(BACKEND)
    django.setup()
    from foundation.models import (
        Clause, Organization, RequirementControl, Standard, StandardEdition, TenantProjection, UserProjection,
    )
    call_command("migrate", database="default", verbosity=0, interactive=False)
    now = timezone.now()
    ext_tenant, tenant, org = uuid4(), uuid4(), uuid4()
    manager, other_user = uuid4(), uuid4()
    TenantProjection.objects.using("default").create(
        id=tenant, adminapps_tenant_id=ext_tenant, source_version=1, source_event_id=uuid4(),
        display_name_snapshot="QMS E2E tenant", lifecycle_status="active", provisioning_status="complete",
        reconciliation_status="in_sync", last_synced_at=now)
    for uid, email in ((manager, "manager@e2e.local"), (other_user, "colleague@e2e.local")):
        UserProjection.objects.using("default").create(
            id=uuid4(), adminapps_user_id=uid, tenant_id=tenant, email=email, source_version=1,
            source_event_id=uuid4(), lifecycle_status="active", last_synced_at=now)
    Organization.objects.using("default").create(id=org, tenant_id=tenant, display_name="QMS E2E Organization")
    standard = Standard.objects.using("default").create(code="ISO 9001 E2E fixture", title="Fixture", publisher="ISO")
    edition = StandardEdition.objects.using("default").create(
        standard_id=standard.id, edition="2026", status="draft", source_hash="a" * 64)
    clause = Clause.objects.using("default").create(standard_edition_id=edition.id, code="10.2", title="Fixture clause")
    RequirementControl.objects.using("default").create(
        standard_edition_id=edition.id, clause_id=clause.id, paraphrase="Fixture requirement paraphrase",
        applicability_rule={}, control_type="test_fixture", valid_from=now)
    edition.status = "published"
    edition.save(using="default", update_fields=("status",))
    return {"organization_id": str(ext_tenant), "manager_id": str(manager), "colleague_id": str(other_user)}


def wait_http(url, timeout=90):
    end = time.time() + timeout
    while time.time() < end:
        try:
            urllib.request.urlopen(url, timeout=2)
            return
        except urllib.error.HTTPError:
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError(f"{url} did not become reachable")


def main():
    prepare_env()
    ids = seed()
    py = sys.executable
    server = subprocess.Popen(
        [py, "manage.py", "runserver", f"127.0.0.1:{BACKEND_PORT}", "--noreload"], cwd=BACKEND,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        wait_http(f"http://127.0.0.1:{BACKEND_PORT}/api/v1/qms/capabilities")
        env = os.environ.copy()
        env.update({
            "VITE_BACKEND_PROXY_TARGET": f"http://127.0.0.1:{BACKEND_PORT}",
            "BASE_URL": f"http://127.0.0.1:{FRONT_PORT}",
            "QMS_E2E_PRINCIPAL": json.dumps(ids),
        })
        # Playwright config starts vite on a fixed port; use a dedicated config copy via CLI flags.
        result = subprocess.run(
            ["npx", "playwright", "test", "tests/e2e-controlled/qms-capa-controlled.spec.js",
             "--config", "playwright.controlled.config.cjs"],
            cwd=FRONTEND, env=env)
        print(f"CONTROLLED_INTEGRATION_E2E_EXIT={result.returncode}")
        if result.returncode != 0:
            raise SystemExit(result.returncode)
        print("CONTROLLED_INTEGRATION_E2E_PASS=1")
    finally:
        server.terminate()
        try:
            err = server.communicate(timeout=10)[1]
        except Exception:
            server.kill()
            err = ""
        if os.getenv("QMS_E2E_SHOW_SERVER_LOG") == "1":
            print(err[-4000:])


if __name__ == "__main__":
    main()
