"""Controlled real-browser PostgreSQL E2E for onboarding Step 11.

Only external authentication bootstrap and inference are replaced by explicitly
opted-in local fixtures.  The browser invokes the real onboarding APIs and the
real Django services persist workflow, evidence, audit, event, and outbox data.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from uuid import uuid4

# The Foundation gate executes this file directly from ``foundation/``.
from qms_e2e_harness import ROLE_BINDINGS


BACKEND = Path(__file__).resolve().parents[1]
FRONTEND = BACKEND.parent / "frontend"
BACKEND_PORT = 8766
FRONTEND_PORT = 3012


def prepare_env():
    os.environ.update({
        "DJANGO_SETTINGS_MODULE": "backend.settings_value_discovery_e2e_controlled",
        "ISO_SMART_POSTGRES_INTEGRATION": "1",
        "VALUE_DISCOVERY_E2E_CONTROLLED_INTEGRATION": "1",
        "USE_SQLITE_DATABASE": "0",
        "DJANGO_ENV": "development",
        "DB_NAME": os.environ["FOUNDATION_DB_NAME"],
        "DB_USER": os.environ["FOUNDATION_MIGRATOR_ROLE"],
        "DB_PASSWORD": os.environ["FOUNDATION_MIGRATOR_PASSWORD"],
        "DB_HOST": os.environ["FOUNDATION_DB_HOST"],
        "DB_PORT": os.environ["FOUNDATION_DB_PORT"],
        "DB_SESSION_OPTIONS": " ".join(
            f"-c foundation.{setting}_role={os.environ[name]}"
            for setting, name in ROLE_BINDINGS
        ),
    })


def _complete_step_ten(*, identity, organization_id, user_projection_id, actor_id):
    from foundation.onboarding import (
        ONBOARDING_STEPS,
        OnboardingWorkflowService,
        OrganizationProfileCommandService,
    )

    workflow = OnboardingWorkflowService(using="app")
    for step in ONBOARDING_STEPS[:9]:
        workflow.transition(
            identity=identity,
            user_id=user_projection_id,
            step_key=step.key,
            to_status="complete",
            event_id=uuid4(),
            event_type="controlled_e2e.onboarding_prerequisite",
            source_reference=f"controlled-e2e:{step.key}",
            actor_id=actor_id,
            trace_id=uuid4(),
        )
    OrganizationProfileCommandService(using="app").save_profile(
        identity=identity,
        organization_id=organization_id,
        user_id=user_projection_id,
        profile={
            "role": "quality_manager",
            "expertise_level": "intermediate",
            "size_range": "51-200",
            "sites_count": 2,
            "countries": ["Costa Rica"],
            "sector": "manufacturing",
            "certification_status": "in_progress",
            "employees_count": 120,
        },
        event_id=uuid4(),
        actor_id=actor_id,
        trace_id=uuid4(),
    )


def seed():
    import django
    from django.core.management import call_command
    from django.utils import timezone

    sys.path.insert(0, str(BACKEND))
    os.chdir(BACKEND)
    django.setup()
    from foundation.models import Organization, TenantProjection, UserProjection
    from foundation.tenant_context import TrustedTenantIdentity

    call_command("migrate", database="default", verbosity=0, interactive=False)
    now = timezone.now()
    principals = {}
    for key, email in (("positive", "value.discovery@e2e.local"), ("negative", "value.discovery.failure@e2e.local")):
        external_tenant_id, tenant_id = uuid4(), uuid4()
        TenantProjection.objects.using("default").create(
            id=tenant_id,
            adminapps_tenant_id=external_tenant_id,
            source_version=1,
            source_event_id=uuid4(),
            display_name_snapshot=f"Value Discovery {key} E2E tenant",
            lifecycle_status="active",
            provisioning_status="complete",
            reconciliation_status="in_sync",
            last_synced_at=now,
        )
        identity = TrustedTenantIdentity(subject=f"controlled-e2e-{key}", tenant_id=tenant_id)
        actor_id, organization_id = uuid4(), uuid4()
        projection = UserProjection.objects.using("default").create(
            id=uuid4(),
            adminapps_user_id=actor_id,
            tenant_id=tenant_id,
            email=email,
            source_version=1,
            source_event_id=uuid4(),
            lifecycle_status="active",
            last_synced_at=now,
        )
        Organization.objects.using("default").create(
            id=organization_id,
            tenant_id=tenant_id,
            display_name=f"Value Discovery {key} organization",
        )
        _complete_step_ten(
            identity=identity,
            organization_id=organization_id,
            user_projection_id=projection.id,
            actor_id=actor_id,
        )
        principals[key] = {
            "organization_id": str(external_tenant_id),
            "user_id": str(actor_id),
            "canonical_organization_id": str(organization_id),
            "email": email,
        }
    return principals


def wait_http(url, timeout=90):
    deadline = time.time() + timeout
    while time.time() < deadline:
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
    principals = seed()
    server = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"127.0.0.1:{BACKEND_PORT}", "--noreload"],
        cwd=BACKEND,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        wait_http(f"http://127.0.0.1:{BACKEND_PORT}/api/v1/onboarding/status")
        env = os.environ.copy()
        env.update({
            "VITE_BACKEND_PROXY_TARGET": f"http://127.0.0.1:{BACKEND_PORT}",
            "BASE_URL": f"http://127.0.0.1:{FRONTEND_PORT}",
            "VALUE_DISCOVERY_E2E_PRINCIPALS": json.dumps(principals),
        })
        result = subprocess.run(
            [
                "npx", "playwright", "test",
                "tests/e2e-controlled/value-discovery-controlled.spec.js",
                "--config", "playwright.value-discovery.controlled.config.cjs",
            ],
            cwd=FRONTEND,
            env=env,
        )
        print(f"VALUE_DISCOVERY_CONTROLLED_AGENT_E2E_EXIT={result.returncode}")
        if result.returncode != 0:
            raise SystemExit(result.returncode)
        print("CONTROLLED_AGENT_E2E=PASS")
        print("REAL_AI_INFERENCE=NOT_EXECUTED_PROVIDER_NOT_CONFIGURED")
        print("REAL_BACKEND_POSTGRESQL_E2E=PASS")
    finally:
        server.terminate()
        try:
            stderr = server.communicate(timeout=10)[1]
        except Exception:
            server.kill()
            stderr = ""
        if os.getenv("VALUE_DISCOVERY_E2E_SHOW_SERVER_LOG") == "1":
            print(stderr[-4000:])


if __name__ == "__main__":
    main()
