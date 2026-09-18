"""Inert SQL/security plan for the exact Phase 31.4 support package."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from .phase31_4_v2_4_support_producer import EXPERIMENT_ID, _contract


OWNER_ROLE = "phase31_4_4_support_owner"
EXECUTOR_ROLE = "phase31_4_4_support_executor"
ENTRY_FUNCTION = "foundation.phase31_4_4_exact_support_entry"
SAFE_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")


class SecurityPlanError(RuntimeError):
    pass


@dataclass(frozen=True)
class SecurityPlan:
    install: tuple[str, ...]
    verify: tuple[str, ...]
    teardown: tuple[str, ...]


class SecurityInstaller:
    """Future connection plumbing; all object names remain contract constants."""

    def __init__(self, connection):
        self._connection = connection

    def _catalog_state(self) -> tuple[int, int, int]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM pg_roles WHERE rolname IN (%s,%s)",
                [OWNER_ROLE, EXECUTOR_ROLE],
            )
            roles = cursor.fetchone()[0]
            cursor.execute(
                "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                "WHERE n.nspname='foundation' AND p.proname='phase31_4_4_exact_support_entry' "
                "AND p.pronargs=0"
            )
            functions = cursor.fetchone()[0]
            cursor.execute(
                "SELECT count(*) FROM pg_policies WHERE policyname LIKE "
                "'phase31_4_4_exact_%_tenant_policy'"
            )
            policies = cursor.fetchone()[0]
        return roles, functions, policies

    def install(self) -> str:
        plan = build_security_plan()
        assert_static_sql_safety(plan.install)
        state = self._catalog_state()
        expected_policies = sum(
            row["global_or_tenant"] == "TENANT"
            for row in _contract()["security_rls_matrix"]
        )
        if state == (2, 1, expected_policies):
            self.verify()
            return "ALREADY_EXACT"
        if state != (0, 0, 0):
            raise SecurityPlanError(f"partial or conflicting install state: {state}")
        with self._connection.cursor() as cursor:
            for statement in plan.install:
                cursor.execute(statement)
        self.verify()
        return "INSTALLED_EXACT"

    def verify(self) -> None:
        expected_policies = sum(
            row["global_or_tenant"] == "TENANT"
            for row in _contract()["security_rls_matrix"]
        )
        with self._connection.cursor() as cursor:
            cursor.execute(
                "SELECT rolname,rolsuper,rolinherit,rolcanlogin,rolbypassrls "
                "FROM pg_roles WHERE rolname IN (%s,%s) ORDER BY rolname",
                [OWNER_ROLE, EXECUTOR_ROLE],
            )
            roles = cursor.fetchall()
            expected = sorted(((OWNER_ROLE, False, False, False, False),
                               (EXECUTOR_ROLE, False, False, True, False)))
            if roles != expected:
                raise SecurityPlanError("role attribute verification failed")
            cursor.execute(
                "SELECT count(*) FROM pg_class c JOIN pg_roles r ON r.oid=c.relowner "
                "WHERE c.relkind IN ('r','p') AND r.rolname IN (%s,%s)",
                [OWNER_ROLE, EXECUTOR_ROLE],
            )
            if cursor.fetchone()[0] != 0:
                raise SecurityPlanError("ephemeral principals must not own tables")
            cursor.execute(
                "SELECT p.prosecdef,p.proconfig,pg_get_userbyid(p.proowner),"
                "has_function_privilege('public',p.oid,'EXECUTE'),"
                "has_function_privilege(%s,p.oid,'EXECUTE') "
                "FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                "WHERE n.nspname='foundation' AND p.proname='phase31_4_4_exact_support_entry' "
                "AND p.pronargs=0",
                [EXECUTOR_ROLE],
            )
            function = cursor.fetchone()
            if (not function or function[0] is not True
                    or "search_path=pg_catalog" not in (function[1] or ())
                    or function[2] != OWNER_ROLE or function[3] is not False
                    or function[4] is not True):
                raise SecurityPlanError("function owner/search_path/EXECUTE verification failed")
            cursor.execute(
                "SELECT count(*) FROM pg_policies WHERE policyname LIKE "
                "'phase31_4_4_exact_%_tenant_policy' AND qual NOT ILIKE '%true%' "
                "AND with_check IS NOT NULL"
            )
            if cursor.fetchone()[0] != expected_policies:
                raise SecurityPlanError("exact RLS policy verification failed")
            cursor.execute(
                "SELECT schemaname,tablename,policyname FROM pg_policies "
                "WHERE policyname LIKE 'phase31_4_4_exact_%_tenant_policy' "
                "ORDER BY schemaname,tablename,policyname"
            )
            observed_policies = cursor.fetchall()
            expected_policy_rows = sorted(
                tuple(row["qualified_table"].split(".")) + (row["applicable_policy"],)
                for row in _contract()["security_rls_matrix"]
                if row["global_or_tenant"] == "TENANT"
            )
            if observed_policies != expected_policy_rows:
                raise SecurityPlanError("53-row security matrix catalog identity mismatch")

    def teardown(self, *, closure_complete: bool, export_matches_live: bool,
                 blockers: int) -> None:
        statements = teardown_plan(closure_complete=closure_complete,
                                   export_matches_live=export_matches_live,
                                   blockers=blockers)
        with self._connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
        if self._catalog_state() != (0, 0, 0):
            raise SecurityPlanError("post-teardown ephemeral catalog residue")


def _qualified(value: str) -> str:
    parts = value.split(".")
    if len(parts) != 2 or any(not SAFE_IDENTIFIER.fullmatch(part) for part in parts):
        raise SecurityPlanError(f"unsafe contract identifier: {value}")
    return ".".join(f'"{part}"' for part in parts)


def _role(value: str) -> str:
    if not SAFE_IDENTIFIER.fullmatch(value):
        raise SecurityPlanError("unsafe role")
    return f'"{value}"'


def _policy(value: str) -> str:
    if not SAFE_IDENTIFIER.fullmatch(value):
        raise SecurityPlanError("unsafe policy")
    return f'"{value}"'


def build_security_plan() -> SecurityPlan:
    """Build exact SQL statements from V2.4; does not connect or execute."""
    contract = _contract()
    matrix = contract["security_rls_matrix"]
    install = [
        f"CREATE ROLE {_role(OWNER_ROLE)} NOLOGIN NOSUPERUSER NOINHERIT NOBYPASSRLS",
        f"CREATE ROLE {_role(EXECUTOR_ROLE)} LOGIN NOSUPERUSER NOINHERIT NOBYPASSRLS",
        (
            "CREATE FUNCTION foundation.phase31_4_4_exact_support_entry() RETURNS text "
            "LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog "
            f"AS 'SELECT ''{EXPERIMENT_ID}''::text'"
        ),
        f"ALTER FUNCTION {ENTRY_FUNCTION}() OWNER TO {_role(OWNER_ROLE)}",
        f"REVOKE ALL ON FUNCTION {ENTRY_FUNCTION}() FROM PUBLIC",
        f"GRANT EXECUTE ON FUNCTION {ENTRY_FUNCTION}() TO {_role(EXECUTOR_ROLE)}",
    ]
    verify = [
        "ROLE phase31_4_4_support_owner NOLOGIN NOSUPERUSER NOINHERIT NOBYPASSRLS NONOWNER",
        "ROLE phase31_4_4_support_executor LOGIN NOSUPERUSER NOINHERIT NOBYPASSRLS NONOWNER",
        "FUNCTION foundation.phase31_4_4_exact_support_entry SECURITY_DEFINER search_path=pg_catalog PUBLIC_EXECUTE=false",
    ]
    teardown = []
    for row in matrix:
        table = _qualified(row["qualified_table"])
        if row["global_or_tenant"] == "TENANT":
            if not row["RLS_enabled"] or not row["RLS_forced"] or not row["tenant_context_required"]:
                raise SecurityPlanError(f"unsafe tenant RLS contract: {row['qualified_table']}")
            policy = _policy(row["applicable_policy"])
            predicate = (
                "tenant_id = current_setting('app.tenant_id', true)::uuid "
                f"AND current_setting('app.phase31_experiment_id', true) = '{EXPERIMENT_ID}'"
            )
            install.extend((
                f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY",
                f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY",
                f"CREATE POLICY {policy} ON {table} TO {_role(OWNER_ROLE)}, {_role(EXECUTOR_ROLE)} USING ({predicate}) WITH CHECK ({predicate})",
            ))
            teardown.append(f"DROP POLICY {policy} ON {table}")
            verify.append(f"POLICY {row['applicable_policy']} ON {row['qualified_table']} USING_AND_CHECK_EXACT")
        if row.get("SELECT"):
            install.append(f"GRANT SELECT ON {table} TO {_role(EXECUTOR_ROLE)}")
            teardown.append(f"REVOKE SELECT ON {table} FROM {_role(EXECUTOR_ROLE)}")
    teardown.extend((
        f"REVOKE EXECUTE ON FUNCTION {ENTRY_FUNCTION}() FROM {_role(EXECUTOR_ROLE)}",
        f"DROP FUNCTION {ENTRY_FUNCTION}()",
        f"DROP ROLE {_role(EXECUTOR_ROLE)}",
        f"DROP ROLE {_role(OWNER_ROLE)}",
    ))
    if len(matrix) != 53:
        raise SecurityPlanError("security/RLS matrix is not exactly 53 rows")
    return SecurityPlan(tuple(install), tuple(verify), tuple(teardown))


def assert_static_sql_safety(statements: Iterable[str]) -> None:
    text = "\n".join(statements)
    forbidden = (
        "GRANT ALL", "USING (true)", "WITH CHECK (true)", "BYPASSRLS LOGIN",
        "SUPERUSER LOGIN", "EXECUTE format(", "EXECUTE '", "DROP TABLE", "ALTER TABLE ONLY",
    )
    hit = next((token for token in forbidden if token.lower() in text.lower()), None)
    if hit:
        raise SecurityPlanError(f"forbidden SQL surface: {hit}")
    if "REVOKE ALL ON FUNCTION" not in text or "SET search_path = pg_catalog" not in text:
        raise SecurityPlanError("function security envelope incomplete")


def install_plan() -> tuple[str, ...]:
    plan = build_security_plan()
    assert_static_sql_safety(plan.install)
    return plan.install


def teardown_plan(*, closure_complete: bool, export_matches_live: bool,
                  blockers: int) -> tuple[str, ...]:
    """Fail closed; callers cannot clean up an incomplete protected run."""
    if not closure_complete or not export_matches_live or blockers:
        raise SecurityPlanError("teardown denied: retained closure predicates are incomplete")
    return build_security_plan().teardown
