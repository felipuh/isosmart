"""Exercise the authentication lifecycle against the disposable E-08 PostgreSQL database."""

import hashlib
import json
import os
import sys
import tempfile
import time
from unittest.mock import patch
from uuid import uuid4


HOST = "isosmart.smart3ai.local"
ORIGIN = f"https://{HOST}"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def configure_environment():
    database_name = os.environ.get("FOUNDATION_DB_NAME", "")
    if not database_name.startswith("foundation_gate_"):
        raise RuntimeError("authentication proof requires the disposable Foundation database")

    os.environ.update({
        "DJANGO_SETTINGS_MODULE": "backend.settings",
        "DJANGO_ENV": "production",
        "DEBUG": "False",
        "SECRET_KEY": f"e08-auth-proof-{uuid4()}",
        "USE_SQLITE_DATABASE": "False",
        "ALLOWED_HOSTS": f"{HOST},localhost,testserver,127.0.0.1",
        "CSRF_TRUSTED_ORIGINS": ORIGIN,
        "SECURE_SSL_REDIRECT": "True",
        "CSRF_COOKIE_SECURE": "True",
        "AUTH_COOKIE_SECURE": "True",
        "AUTH_COOKIE_SAMESITE": "Lax",
        "OWNER_ORGANIZATION_ONLY_ACCESS": "True",
        "OWNER_ORGANIZATION_SLUG": "smart3ai",
        "OWNER_ORGANIZATION_NAME": "Smart3AI",
        "DB_NAME": database_name,
        "DB_USER": os.environ["FOUNDATION_MIGRATOR_ROLE"],
        "DB_PASSWORD": os.environ["FOUNDATION_MIGRATOR_PASSWORD"],
        "DB_HOST": os.environ["FOUNDATION_DB_HOST"],
        "DB_PORT": os.environ["FOUNDATION_DB_PORT"],
        "FOUNDATION_DB_NAME": database_name,
        "FOUNDATION_APP_DB_USER": os.environ["FOUNDATION_APP_ROLE"],
        "FOUNDATION_APP_DB_PASSWORD": os.environ["FOUNDATION_APP_PASSWORD"],
        "FOUNDATION_WORKER_DB_USER": os.environ["FOUNDATION_WORKER_ROLE"],
        "FOUNDATION_WORKER_DB_PASSWORD": os.environ["FOUNDATION_WORKER_PASSWORD"],
        "FOUNDATION_PROJECTOR_DB_USER": os.environ["FOUNDATION_PROJECTOR_ROLE"],
        "FOUNDATION_PROJECTOR_DB_PASSWORD": os.environ["FOUNDATION_PROJECTOR_PASSWORD"],
        "FOUNDATION_NORMATIVE_CURATOR_DB_USER": os.environ["FOUNDATION_NORMATIVE_CURATOR_ROLE"],
        "FOUNDATION_NORMATIVE_CURATOR_DB_PASSWORD": os.environ["FOUNDATION_NORMATIVE_CURATOR_PASSWORD"],
        "FOUNDATION_HUMAN_APPROVER_DB_USER": os.environ["FOUNDATION_HUMAN_APPROVER_ROLE"],
        "FOUNDATION_HUMAN_APPROVER_DB_PASSWORD": os.environ["FOUNDATION_HUMAN_APPROVER_PASSWORD"],
        "FOUNDATION_EXECUTION_AUTHORIZER_DB_USER": os.environ["FOUNDATION_EXECUTION_AUTHORIZER_ROLE"],
        "FOUNDATION_EXECUTION_AUTHORIZER_DB_PASSWORD": os.environ["FOUNDATION_EXECUTION_AUTHORIZER_PASSWORD"],
        "FOUNDATION_EXECUTOR_DB_USER": os.environ["FOUNDATION_EXECUTOR_ROLE"],
        "FOUNDATION_EXECUTOR_DB_PASSWORD": os.environ["FOUNDATION_EXECUTOR_PASSWORD"],
        "FOUNDATION_QMS_ACTION_OWNER_DB_USER": os.environ["FOUNDATION_QMS_ACTION_OWNER_ROLE"],
    })

    role_settings = {
        "app_role": "FOUNDATION_APP_ROLE",
        "worker_role": "FOUNDATION_WORKER_ROLE",
        "projector_role": "FOUNDATION_PROJECTOR_ROLE",
        "audit_writer_role": "FOUNDATION_AUDIT_WRITER_ROLE",
        "normative_curator_role": "FOUNDATION_NORMATIVE_CURATOR_ROLE",
        "agent_catalog_curator_role": "FOUNDATION_AGENT_CATALOG_CURATOR_ROLE",
        "human_approver_role": "FOUNDATION_HUMAN_APPROVER_ROLE",
        "execution_authorizer_role": "FOUNDATION_EXECUTION_AUTHORIZER_ROLE",
        "executor_role": "FOUNDATION_EXECUTOR_ROLE",
        "qms_action_owner_role": "FOUNDATION_QMS_ACTION_OWNER_ROLE",
        "learning_governance_role": "FOUNDATION_LEARNING_GOVERNANCE_ROLE",
        "learning_reviewer_role": "FOUNDATION_LEARNING_REVIEWER_ROLE",
        "learning_approver_role": "FOUNDATION_LEARNING_APPROVER_ROLE",
        "learning_authorizer_role": "FOUNDATION_LEARNING_AUTHORIZER_ROLE",
        "learning_application_executor_role": "FOUNDATION_LEARNING_APPLICATION_EXECUTOR_ROLE",
        "knowledge_rule_application_owner_role": "FOUNDATION_KNOWLEDGE_RULE_APPLICATION_OWNER_ROLE",
        "rule_governance_owner_role": "FOUNDATION_RULE_GOVERNANCE_OWNER_ROLE",
        "rule_publisher_role": "FOUNDATION_RULE_PUBLISHER_ROLE",
        "rule_activator_role": "FOUNDATION_RULE_ACTIVATOR_ROLE",
        "rule_adopter_role": "FOUNDATION_RULE_ADOPTER_ROLE",
        "rule_resolver_role": "FOUNDATION_RULE_RESOLVER_ROLE",
        "release_repair_role": "FOUNDATION_RELEASE_REPAIR_ROLE",
        "release_controller_role": "FOUNDATION_RELEASE_CONTROLLER_ROLE",
    }
    os.environ["DB_SESSION_OPTIONS"] = " ".join(
        f"-c foundation.{setting}={os.environ[variable]}"
        for setting, variable in role_settings.items()
    )


def main():
    configure_environment()
    checks = 0

    def check(condition, message):
        nonlocal checks
        require(condition, message)
        checks += 1

    with tempfile.TemporaryDirectory(prefix="isosmart-e08-auth-logs-") as log_directory:
        os.environ["ISOSMART_LOG_DIR"] = log_directory
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        import django

        django.setup()

        from django.conf import settings
        from django.core.management import call_command
        from django.db import connections
        from django.test import Client, RequestFactory
        from django.urls import reverse
        from authentication.middleware import OrganizationMiddleware
        from authentication.models import RefreshTokenBlacklist, User, UserProfile
        from core.models import Organization
        from rest_framework_simplejwt.tokens import AccessToken

        call_command("migrate", database="default", verbosity=0, interactive=False)

        external_org_id = str(uuid4())
        foreign_external_org_id = str(uuid4())
        external_user_id = str(uuid4())
        email = f"e08-{uuid4().hex}@example.invalid"
        primary_org_name = "Smart3AI"
        foreign_user = User.objects.create_user(
            email=f"e08-foreign-{uuid4().hex}@example.invalid",
            password=None,
            first_name="E08",
            last_name="Foreign",
            is_active=True,
        )
        foreign_org = Organization.objects.create(
            external_id=foreign_external_org_id,
            name="E08 Foreign Tenant",
            slug=f"e08-foreign-{uuid4().hex[:12]}",
        )
        foreign_profile = UserProfile.objects.create(
            user=foreign_user, organization=foreign_org, role="user", is_active=True,
        )

        migrator_user = settings.DATABASES["default"]["USER"]
        migrator_password = settings.DATABASES["default"]["PASSWORD"]
        connections.close_all()
        settings.DATABASES["default"]["USER"] = os.environ["FOUNDATION_APP_ROLE"]
        settings.DATABASES["default"]["PASSWORD"] = os.environ["FOUNDATION_APP_PASSWORD"]

        with connections["default"].cursor() as cursor:
            cursor.execute(
                "SELECT current_user, rolsuper, rolbypassrls "
                "FROM pg_roles WHERE rolname = current_user"
            )
            database_role, is_superuser, bypasses_rls = cursor.fetchone()
        check(
            database_role == os.environ["FOUNDATION_APP_ROLE"]
            and not is_superuser
            and not bypasses_rls,
            "HTTP authentication did not use the restricted application role",
        )

        login_url = reverse("authentication:login")
        csrf_url = reverse("authentication:csrf")
        me_url = reverse("authentication:me")
        refresh_url = reverse("authentication:refresh")
        logout_url = reverse("authentication:logout")
        access_cookie = "isosmart_access"
        refresh_cookie = "isosmart_refresh"
        csrf_cookie = "csrftoken"
        request_meta = {
            "secure": True,
            "HTTP_HOST": HOST,
            "HTTP_ORIGIN": ORIGIN,
            "HTTP_X_FORWARDED_PROTO": "https",
        }

        valid_credentials = {
            "valid": True,
            "user": {
                "id": external_user_id,
                "email": email,
                "first_name": "E08",
                "last_name": "Authentication",
            },
            "current_organization": {
                "id": external_org_id,
                "name": primary_org_name,
                "slug": "smart3ai",
                "is_active": True,
            },
            "organizations": [{"id": external_org_id, "name": primary_org_name}],
            "current_role": "user",
        }

        def validate_credentials(*, password, **kwargs):
            return valid_credentials if password == "synthetic-e08-credential" else {
                "valid": False,
                "error": "synthetic invalid credentials",
            }

        with (
            patch(
                "integration.client.admin_apps_client.validate_credentials",
                side_effect=validate_credentials,
            ),
            patch(
                "integration.client.admin_apps_client.validate_product_access",
                return_value={"allowed": True, "reason": "synthetic local proof"},
            ),
            patch(
                "integration.client.admin_apps_client.get_organization",
                return_value={"id": external_org_id, "name": primary_org_name},
            ),
            patch(
                "integration.client.admin_apps_client.get_user",
                return_value={"user": {}},
            ),
        ):
            client = Client(enforce_csrf_checks=True)
            csrf_response = client.get(csrf_url, **request_meta)
            check(csrf_response.status_code == 200, "CSRF endpoint did not issue a cookie")
            csrf_token = client.cookies[csrf_cookie].value
            csrf_morsel = csrf_response.cookies[csrf_cookie]
            csrf_attributes = {
                key: csrf_morsel[key] for key in ("secure", "samesite", "httponly")
            }
            check(
                bool(csrf_morsel["secure"])
                and csrf_morsel["samesite"] == "Lax"
                and not csrf_morsel["httponly"],
                f"CSRF cookie attributes do not match the production contract: {csrf_attributes}",
            )

            invalid_login = client.post(
                login_url,
                data=json.dumps({"email": email, "password": "synthetic-invalid-credential"}),
                content_type="application/json",
                **request_meta,
            )
            check(invalid_login.status_code == 400, "invalid credentials were not rejected")

            wrong_tenant_login = client.post(
                login_url,
                data=json.dumps({
                    "email": email,
                    "password": "synthetic-e08-credential",
                    "organization_id": foreign_external_org_id,
                }),
                content_type="application/json",
                **request_meta,
            )
            check(
                wrong_tenant_login.status_code == 400,
                "login accepted an organization absent from the user's tenant set",
            )
            user = User.objects.get(email=email)
            primary_org = Organization.objects.get(external_id=external_org_id)
            primary_profile = UserProfile.objects.get(
                user=user, organization=primary_org,
            )

            login_response = client.post(
                login_url,
                data=json.dumps({"email": email, "password": "synthetic-e08-credential"}),
                content_type="application/json",
                HTTP_X_CSRFTOKEN=csrf_token,
                **request_meta,
            )
            login_payload = login_response.json()
            check(
                login_response.status_code == 200,
                "valid PostgreSQL-backed login failed: "
                f"status={login_response.status_code}, response={login_payload}",
            )
            check(
                "access" not in login_payload and "refresh" not in login_payload,
                "JWTs were exposed in the login response body",
            )
            check(
                login_payload["profile"]["organization"] == primary_org.id,
                "login response did not select the authenticated user's tenant",
            )
            for cookie_name, max_age in (
                (access_cookie, settings.AUTH_ACCESS_COOKIE_AGE),
                (refresh_cookie, settings.AUTH_REFRESH_COOKIE_AGE),
            ):
                cookie = login_response.cookies[cookie_name]
                check(
                    bool(cookie["httponly"])
                    and bool(cookie["secure"])
                    and cookie["samesite"] == "Lax"
                    and cookie["path"] == "/"
                    and int(cookie["max-age"]) == max_age,
                    f"{cookie_name} attributes do not match the production contract",
                )

            me_response = client.get(me_url, **request_meta)
            check(
                me_response.status_code == 200
                and me_response.json()["profile"]["id"] == primary_profile.id
                and me_response.json()["profile"]["organization"] == primary_org.id,
                "authenticated /me did not resolve the user's selected tenant",
            )

            no_cookie_client = Client(enforce_csrf_checks=True)
            check(
                no_cookie_client.get(me_url, **request_meta).status_code == 401,
                "unauthenticated /me request was not rejected",
            )
            malformed_client = Client(enforce_csrf_checks=True)
            malformed_client.cookies[access_cookie] = "not-a-jwt"
            check(
                malformed_client.get(me_url, **request_meta).status_code == 401,
                "malformed access cookie was not rejected",
            )
            expired_client = Client(enforce_csrf_checks=True)
            expired_access = AccessToken.for_user(user)
            expired_access["exp"] = int(time.time()) - 10
            expired_access["organization_id"] = primary_org.id
            expired_client.cookies[access_cookie] = str(expired_access)
            check(
                expired_client.get(me_url, **request_meta).status_code == 401,
                "expired access cookie was not rejected",
            )

            foreign_client = Client(enforce_csrf_checks=True)
            foreign_access = AccessToken.for_user(user)
            foreign_access["organization_id"] = foreign_org.id
            foreign_access["profile_id"] = foreign_profile.id
            foreign_client.cookies[access_cookie] = str(foreign_access)
            foreign_request = RequestFactory().get(me_url)
            foreign_request.COOKIES[access_cookie] = str(foreign_access)
            OrganizationMiddleware(lambda request: None).process_request(foreign_request)
            foreign_me = foreign_client.get(me_url, **request_meta)
            check(
                foreign_request.user_profile is None
                and foreign_me.status_code == 200
                and foreign_me.json()["profile"] is None
                and all(
                    item["id"] != foreign_org.id
                    for item in foreign_me.json()["organizations"]
                ),
                "foreign-tenant profile or organization became visible",
            )

            old_refresh = client.cookies[refresh_cookie].value
            missing_csrf_client = Client(enforce_csrf_checks=True)
            missing_csrf_client.cookies[refresh_cookie] = old_refresh
            check(
                missing_csrf_client.post(refresh_url, **request_meta).status_code == 403,
                "refresh-cookie request without CSRF was not rejected",
            )
            invalid_csrf_client = Client(enforce_csrf_checks=True)
            invalid_csrf_client.cookies[refresh_cookie] = old_refresh
            invalid_csrf_client.cookies[csrf_cookie] = "a" * 32
            check(
                invalid_csrf_client.post(
                    refresh_url,
                    HTTP_X_CSRFTOKEN="b" * 32,
                    **request_meta,
                ).status_code == 403,
                "refresh-cookie request with invalid CSRF was not rejected",
            )

            rotated = client.post(
                refresh_url, HTTP_X_CSRFTOKEN=csrf_token, **request_meta,
            )
            check(rotated.status_code == 200, "valid refresh did not rotate tokens")
            rotated_refresh = client.cookies[refresh_cookie].value
            check(rotated_refresh != old_refresh, "refresh token did not rotate")
            old_hash = hashlib.sha256(old_refresh.encode("utf-8")).hexdigest()
            old_blacklist = RefreshTokenBlacklist.objects.get(token_hash=old_hash)
            check(old_blacklist.token == "", "rotated refresh token was stored in plaintext")

            replay_client = Client(enforce_csrf_checks=True)
            replay_client.cookies[refresh_cookie] = old_refresh
            replay_client.cookies[csrf_cookie] = csrf_token
            check(
                replay_client.post(
                    refresh_url,
                    HTTP_X_CSRFTOKEN=csrf_token,
                    **request_meta,
                ).status_code == 401,
                "rotated refresh token replay was not rejected",
            )

            missing_logout_csrf = Client(enforce_csrf_checks=True)
            missing_logout_csrf.cookies[access_cookie] = client.cookies[access_cookie].value
            missing_logout_csrf.cookies[refresh_cookie] = rotated_refresh
            check(
                missing_logout_csrf.post(logout_url, **request_meta).status_code == 403,
                "logout without CSRF was not rejected",
            )
            invalid_logout_csrf = Client(enforce_csrf_checks=True)
            invalid_logout_csrf.cookies[access_cookie] = client.cookies[access_cookie].value
            invalid_logout_csrf.cookies[refresh_cookie] = rotated_refresh
            invalid_logout_csrf.cookies[csrf_cookie] = "a" * 32
            check(
                invalid_logout_csrf.post(
                    logout_url,
                    HTTP_X_CSRFTOKEN="b" * 32,
                    **request_meta,
                ).status_code == 403,
                "logout with invalid CSRF was not rejected",
            )

            logout_response = client.post(
                logout_url, HTTP_X_CSRFTOKEN=csrf_token, **request_meta,
            )
            check(logout_response.status_code == 200, "valid logout failed")
            for cookie_name in (access_cookie, refresh_cookie):
                check(
                    client.cookies[cookie_name].value == "",
                    f"{cookie_name} was not cleared on logout",
                )
            logout_hash = hashlib.sha256(rotated_refresh.encode("utf-8")).hexdigest()
            logout_blacklist = RefreshTokenBlacklist.objects.get(token_hash=logout_hash)
            check(logout_blacklist.token == "", "logout stored the refresh token in plaintext")

            revoked_client = Client(enforce_csrf_checks=True)
            revoked_client.cookies[refresh_cookie] = rotated_refresh
            revoked_client.cookies[csrf_cookie] = csrf_token
            check(
                revoked_client.post(
                    refresh_url,
                    HTTP_X_CSRFTOKEN=csrf_token,
                    **request_meta,
                ).status_code == 401,
                "logout-revoked refresh token was accepted",
            )

        connections.close_all()
        settings.DATABASES["default"]["USER"] = migrator_user
        settings.DATABASES["default"]["PASSWORD"] = migrator_password

    print(f"E08_AUTH_POSTGRES_PROOF_PASS checks={checks}")


if __name__ == "__main__":
    main()
