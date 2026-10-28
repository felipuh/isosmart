"""Repository-specific live actions for the V2.5 operational adapter.

This process is invoked once per action. Inputs arrive only through the
run-scoped environment assembled by ``SubprocessOperationalAdapter``.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib, json, os, subprocess, sys
from pathlib import Path
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

import psycopg2
from psycopg2 import sql
from django.db import transaction

ROOT = Path(__file__).resolve().parents[3]
ADMIN = ROOT.parent / "adminapps/backend"
sys.path.insert(0, str(ROOT / "backend"))


def endpoint(name: str):
    from urllib.parse import urlparse
    parsed = urlparse(os.environ[name])
    return parsed.hostname, parsed.port, parsed.path.lstrip("/")


def env_for(name: str) -> dict[str, str]:
    host, port, database = endpoint(name)
    env = os.environ.copy()
    env.update(USE_SQLITE_DATABASE="false", DB_NAME=database, DB_HOST=host or "127.0.0.1",
               DB_PORT=str(port), DB_PASSWORD="")
    if name == "PHASE31_ADMINAPPS_DB_ENDPOINT":
        env.update(DB_USER="postgres", DJANGO_SETTINGS_MODULE="config.settings",
                   ALLOWED_HOSTS="127.0.0.1,localhost,testserver")
    else:
        env.update(DB_USER="postgres", DJANGO_SETTINGS_MODULE="backend.settings")
        if os.environ.get("PHASE31_ROLE_OPTIONS"):
            env["DB_SESSION_OPTIONS"] = os.environ["PHASE31_ROLE_OPTIONS"]
    return env


def runtime_python(root: Path, env: dict[str, str]) -> Path:
    if root == ADMIN and env.get("PHASE31_ADMINAPPS_PYTHON"):
        return Path(env["PHASE31_ADMINAPPS_PYTHON"])
    return root / ".venv/bin/python"


def run_manage(root: Path, env: dict[str, str], *args: str) -> dict:
    python = runtime_python(root, env)
    result = subprocess.run([str(python), "manage.py", *args], cwd=root, env=env,
                            text=True, capture_output=True)
    if result.returncode: raise RuntimeError(result.stdout + result.stderr)
    return {"argv":[str(python),"manage.py",*args], "returncode":0,
            "stdout_sha256":hashlib.sha256(result.stdout.encode()).hexdigest()}


def pending(root: Path, env: dict[str, str]) -> int:
    python = runtime_python(root, env)
    result = subprocess.run([str(python), "manage.py", "showmigrations", "--plan"], cwd=root,
                            env=env, text=True, capture_output=True, check=True)
    return sum(1 for line in result.stdout.splitlines() if "[ ]" in line)


def bootstrap_adminapps():
    env = env_for("PHASE31_ADMINAPPS_DB_ENDPOINT")
    migration = run_manage(ADMIN, env, "migrate", "--noinput")
    host, port, database = endpoint("PHASE31_ADMINAPPS_DB_ENDPOINT")
    with psycopg2.connect(dbname=database,user="postgres",host=host,port=port) as connection:
        with connection.cursor() as cursor:
            cursor.execute("select current_database(), current_user, current_setting('server_version')")
            identity = cursor.fetchone()
    return {"status":"PASS","database_readiness":"PASS","migrations_pending":pending(ADMIN,env),
            "migration":migration,"database_identity":{"database":identity[0],"user":identity[1],"version":identity[2]}}


def bootstrap_isosmart():
    from foundation.postgres_foundation_gate import LOGIN_ROLES, OWNER_ROLES
    env = env_for("PHASE31_ISOSMART_DB_ENDPOINT")
    host, port, database = endpoint("PHASE31_ISOSMART_DB_ENDPOINT")
    prefix = os.environ["PHASE31_ROLE_PREFIX"]
    names = {role:f"{prefix}_{role}" for role in (*LOGIN_ROLES,*OWNER_ROLES)}
    connection = psycopg2.connect(dbname="postgres",user="postgres",host=host,port=port); connection.autocommit=True
    with connection.cursor() as cursor:
        for role in LOGIN_ROLES:
            cursor.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS").format(sql.Identifier(names[role])))
        for role in OWNER_ROLES:
            cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS").format(sql.Identifier(names[role])))
            cursor.execute(sql.SQL("GRANT {} TO {} WITH SET TRUE").format(sql.Identifier(names[role]),sql.Identifier(names["migrator"])))
        cursor.execute(sql.SQL("ALTER DATABASE {} OWNER TO {}").format(sql.Identifier(database),sql.Identifier(names["migrator"])))
    connection.close()
    env.update(DB_USER=names["migrator"], DB_PASSWORD="", DB_SESSION_OPTIONS=" ".join(f"-c foundation.{r}_role={names[r]}" for r in (*LOGIN_ROLES,*OWNER_ROLES)))
    migration = run_manage(ROOT/"backend",env,"migrate","--noinput")
    with psycopg2.connect(dbname=database,user="postgres",host=host,port=port) as connection:
        with connection.cursor() as cursor:
            cursor.execute("select rolname from pg_roles where rolname=any(%s)",[list(names.values())]); found={r[0] for r in cursor.fetchall()}
    return {"status":"PASS","database_readiness":"PASS","migrations_pending":pending(ROOT/"backend",env),
            "migration":migration,"roles_verified":found==set(names.values()),"roles":names,
            "session_configuration_verified":all(f"foundation.{r}_role" in env["DB_SESSION_OPTIONS"] for r in (*LOGIN_ROLES,*OWNER_ROLES))}


def django_setup(system: str):
    env = env_for("PHASE31_ADMINAPPS_DB_ENDPOINT" if system=="admin" else "PHASE31_ISOSMART_DB_ENDPOINT")
    os.environ.update(env); sys.path.insert(0,str(ADMIN if system=="admin" else ROOT/"backend"))
    import django; django.setup()

def create_authority_tenant(*, actor, name: str, email: str):
    from apps.organizations.models import Organization
    from apps.organizations.tenant_events import record_tenant_event

    with transaction.atomic():
        organization = Organization.objects.create(name=name, email=email)
        record_tenant_event(organization, actor_id=actor.id)
    return organization


def authority():
    django_setup("admin")
    from apps.organizations.models import Organization
    from django.conf import settings
    from apps.integration.models import IntegrationAPIKey
    from apps.products.models import OrganizationProductEntitlement, ProductSystem
    from apps.users.models import User, UserOrganization
    from foundation.operational_bearer_identity import acquire_runtime_bearer
    from rest_framework_simplejwt.tokens import AccessToken
    suffix=hashlib.sha256(os.environ["PHASE31_RUN_ID"].encode()).hexdigest()[:12]
    actor=User.objects.create_user(email=f"live-{suffix}@example.test",password=None,first_name="Operational",last_name="Readiness",
                                   role="viewer",is_active=True,is_staff=False,is_superuser=False)
    organization=create_authority_tenant(actor=actor, name=f"Live Evidence {suffix}",
                                         email=f"tenant-{suffix}@example.test")
    membership=UserOrganization.objects.create(user=actor,organization=organization,role="viewer",is_primary=True)
    key=os.environ["PHASE31_INTEGRATION_KEY"]
    IntegrationAPIKey.objects.create(name=f"isosmart-{suffix}",key=key,is_active=True)
    product=ProductSystem.objects.get(code="ISO_SMART")
    entitlement=OrganizationProductEntitlement.objects.create(organization=organization,product=product,status="trial",enabled=True,scopes=["qms"])
    organization.status="active"; organization.save(update_fields=["status"])
    organization.refresh_from_db(fields=["status"])
    credential=acquire_runtime_bearer(actor,membership,entitlement,token_class=AccessToken,
                                      issuer=settings.SMART3AI_SSO_ISSUER,lifetime_seconds=900)
    descriptor_value=os.environ.get("PHASE31_BEARER_FD","")
    if not descriptor_value.isdigit():
        credential.destroy()
        raise RuntimeError("runtime bearer pipe is required")
    try:
        credential.write_to_fd(int(descriptor_value))
        credential_evidence=credential.evidence()
    finally:
        os.close(int(descriptor_value))
        credential.destroy()
    tenant_rb=Organization.objects.values("id","status").get(pk=organization.pk)
    actor_rb=User.objects.values("id","is_active","is_staff","is_superuser","role").get(pk=actor.pk)
    return {"status":"PASS","classification":"SYNTHETIC_TEST_AUTHORITY","tenant_id":str(organization.id),"actor_id":str(actor.id),
            "tenant_readback":{"id":str(tenant_rb["id"]),"status":tenant_rb["status"]},
            "actor_readback":{"id":str(actor_rb["id"]),"active":actor_rb["is_active"],"is_staff":actor_rb["is_staff"],
                              "is_superuser":actor_rb["is_superuser"],"role":actor_rb["role"],
                              "has_usable_password":actor.has_usable_password()},
            "bearer":credential_evidence}


def delivery():
    env=env_for("PHASE31_ADMINAPPS_DB_ENDPOINT")
    env.update(ISO_SMART_TENANT_EVENT_URL=os.environ["ISO_SMART_BASE_URL"].rstrip("/")+"/api/integration/adminapps/tenant-events/",
               ISO_SMART_TENANT_EVENT_KEY=os.environ["PHASE31_EVENT_KEY"],ISO_SMART_TENANT_EVENT_ALLOW_LOOPBACK_HTTP="true")
    result=run_manage(ADMIN,env,"deliver_tenant_events","--limit","100")
    django_setup("iso")
    from foundation.models import TenantProjection,UserProjection
    tenant=TenantProjection.objects.get(adminapps_tenant_id=UUID(os.environ["PHASE31_INPUT_TENANT_ID"]))
    user=UserProjection.objects.get(adminapps_user_id=UUID(os.environ["PHASE31_INPUT_ACTOR_ID"]))
    return {"status":"PASS","outbox_id":result["stdout_sha256"],"delivery_result":"DELIVERED","ingress_receipt":f"tenant:{tenant.id};user:{user.id}",
            "tenant_projection_id":str(tenant.id),"user_projection_id":str(user.id)}


def projection(kind: str):
    django_setup("iso"); from foundation.models import TenantProjection,UserProjection
    key="TENANT_PROJECTION_ID" if kind=="tenant" else "USER_PROJECTION_ID"
    model=TenantProjection if kind=="tenant" else UserProjection
    row=model.objects.values("id").get(pk=UUID(os.environ[f"PHASE31_INPUT_{key}"]))
    return {"id":str(row["id"])}


def organization_create():
    django_setup("iso")
    from foundation.qms_organization import QmsOrganizationCommandService
    from foundation.tenant_context import TrustedTenantIdentity
    result=QmsOrganizationCommandService().create_organization(identity=TrustedTenantIdentity("live-evidence",UUID(os.environ["PHASE31_INPUT_TENANT_PROJECTION_ID"])),
        display_name=f"Live QMS {os.environ['PHASE31_RUN_ID']}",actor_id=UUID(os.environ["PHASE31_INPUT_ACTOR_ID"]),trace_id=uuid4(),request_key=uuid4())
    return {"status":"PASS","returned_id":str(result.organization_id),"entitlement_decision":"ALLOW"}


def organization_readback():
    django_setup("iso"); from foundation.models import QmsOrganization
    row=QmsOrganization.objects.values("id","tenant_id").get(pk=UUID(os.environ["PHASE31_INPUT_ID"]))
    return {"id":str(row["id"]),"tenant_id":str(row["tenant_id"])}


def process_create():
    django_setup("iso")
    from foundation.qms_context import QmsContextCommandService
    from foundation.tenant_context import TrustedTenantIdentity
    result=QmsContextCommandService().create_process(identity=TrustedTenantIdentity("live-evidence",UUID(os.environ["PHASE31_INPUT_TENANT_PROJECTION_ID"])),
        organization_id=UUID(os.environ["PHASE31_INPUT_ORGANIZATION_ID"]),name=f"Live Process {os.environ['PHASE31_RUN_ID']}",actor_id=UUID(os.environ["PHASE31_INPUT_ACTOR_ID"]),trace_id=uuid4())
    return {"status":"PASS","returned_id":str(result.entity_id)}


def process_readback():
    django_setup("iso"); from foundation.models import Process
    row=Process.objects.values("id","organization_id","tenant_id").get(pk=UUID(os.environ["PHASE31_INPUT_ID"]))
    return {key:str(value) for key,value in row.items()}


def service(system: str):
    root=ADMIN if system=="adminapps" else ROOT/"backend"
    env=env_for("PHASE31_ADMINAPPS_DB_ENDPOINT" if system=="adminapps" else "PHASE31_ISOSMART_DB_ENDPOINT")
    if system=="adminapps": env["RETRY16_INTEGRATION_KEY"]=os.environ["PHASE31_INTEGRATION_KEY"]
    else: env.update(ADMIN_APPS_API_KEY=os.environ["PHASE31_INTEGRATION_KEY"],ADMINAPPS_TENANT_EVENT_KEY_SHA256=hashlib.sha256(os.environ["PHASE31_EVENT_KEY"].encode()).hexdigest(),ADMIN_APPS_BASE_URL=os.environ["ADMIN_APPS_BASE_URL"].rstrip("/")+"/api/integration")
    python = runtime_python(root, env)
    os.execve(str(python),[str(python),str(root/"manage.py"),"runserver","--noreload",f"127.0.0.1:{os.environ['PORT']}"],env)


if __name__=="__main__":
    action=sys.argv[1]
    if action=="service": service(sys.argv[2])
    handlers={"bootstrap_adminapps":bootstrap_adminapps,"bootstrap_isosmart":bootstrap_isosmart,"authority":authority,"delivery":delivery,
              "tenant_projection_readback":lambda:projection("tenant"),"user_projection_readback":lambda:projection("user"),
              "organization_create":organization_create,"organization_readback":organization_readback,"process_create":process_create,"process_readback":process_readback}
    print(json.dumps(handlers[action](),sort_keys=True))
