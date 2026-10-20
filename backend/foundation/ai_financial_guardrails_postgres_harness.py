"""Focused disposable-PostgreSQL acceptance for migration 0042.

Run through ``postgres_foundation_gate.py`` so the database, roles, generated
passwords, and output are run-scoped and torn down by the established harness.
No provider, network, or AdminApps operation is performed.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
import os
import sys
import threading
import time
from uuid import UUID
import unittest
from unittest.mock import patch

import postgres_foundation_harness as foundation


TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def runtime(alias, tenant):
    return foundation.runtime_transaction(alias, tenant)


class FinancialGuardrailPostgreSQLTests(unittest.TestCase):
    """Exercises database-backed admission and settlement as an RLS runtime role."""

    @classmethod
    def setUpClass(cls):
        foundation.configure_django()
        from django.db import connections
        from django.db.migrations.executor import MigrationExecutor

        executor = MigrationExecutor(connections["default"])
        executor.migrate([("foundation", "0041_ai_usage_retry_exhausted_recovery")])
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT to_regclass('ai_usage.financial_guardrail_policy')")
            require(cursor.fetchone()[0] is None, "0042 appeared before its predecessor state")
        MigrationExecutor(connections["default"]).migrate([("foundation", "0042_ai_financial_guardrails")])
        cls._seed_tenants_and_pricing()

    @classmethod
    def _seed_tenants_and_pricing(cls):
        from django.db import connections
        from django.utils import timezone
        from foundation.ai_financial_guardrails import FinancialGuardrailService
        from foundation.models import AIModelPricingVersion
        from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

        with connections["default"].cursor() as cursor:
            cursor.execute(
                "INSERT INTO qms.tenant_projection "
                "(id,adminapps_tenant_id,source_version,source_event_id,display_name_snapshot,"
                "lifecycle_status,provisioning_status,reconciliation_status,last_synced_at) "
                "VALUES (%s,%s,1,%s,'Tenant A','active','complete','in_sync',statement_timestamp()),"
                "(%s,%s,1,%s,'Tenant B','active','complete','in_sync',statement_timestamp())",
                [str(TENANT_A), "10000000-0000-4000-8000-000000000001", "a0000000-0000-4000-8000-000000000001",
                 str(TENANT_B), "20000000-0000-4000-8000-000000000001", "b0000000-0000-4000-8000-000000000001"],
            )
        AIModelPricingVersion.objects.using("default").create(
            provider="synthetic-provider", model_identifier="synthetic-model",
            effective_from=timezone.now() - timedelta(minutes=1), currency="USD", rate_unit=1000,
            input_token_rate=Decimal("0.1000000000"), output_token_rate=Decimal("0.4000000000"),
            source_reference="SYNTHETIC_TEST_TARIFF_ONLY", verification_status="verified",
        )
        service = FinancialGuardrailService(using="worker")
        for tenant in (TENANT_A, TENANT_B):
            identity = TrustedTenantIdentity(subject="postgres-acceptance", tenant_id=tenant)
            with trusted_tenant_context(identity, actor_id="test", trace_id="seed", using="worker"):
                from foundation.models import AIFinancialGuardrailPolicy
                AIFinancialGuardrailPolicy.objects.using("worker").create(
                    tenant_id=tenant, product_identifier="iso-smart", provider="synthetic-provider",
                    model_identifier="synthetic-model", period_start=timezone.now() - timedelta(minutes=1),
                    period_end=timezone.now() + timedelta(days=1), currency="USD", max_request_count=20,
                    max_input_tokens=1000, max_output_tokens=1000, max_reserved_cost=Decimal("100.0000000000"),
                    policy_scope="controlled_test", authority_reference="SYNTHETIC_POSTGRES_ACCEPTANCE",
                    status="enabled",
                )

    def _identity(self, tenant=TENANT_A):
        from foundation.tenant_context import TrustedTenantIdentity
        return TrustedTenantIdentity(subject="postgres-acceptance", tenant_id=tenant)

    def _reserve(self, invocation, *, tenant=TENANT_A, input_tokens=10, output_tokens=10):
        from foundation.ai_financial_guardrails import FinancialGuardrailService
        from foundation.tenant_context import trusted_tenant_context

        with trusted_tenant_context(self._identity(tenant), actor_id="test", trace_id=invocation, using="worker"):
            return FinancialGuardrailService(using="worker").reserve_controlled_test(
                tenant_id=tenant, invocation_id=invocation, provider="synthetic-provider",
                model_identifier="synthetic-model", input_token_bound=input_tokens,
                max_output_tokens=output_tokens, usage_record=None,
            )

    def test_01_migration_catalog_rls_roles_and_constraints(self):
        from django.db import connections

        app_role, worker_role = os.environ["FOUNDATION_APP_ROLE"], os.environ["FOUNDATION_WORKER_ROLE"]
        with connections["default"].cursor() as cursor:
            cursor.execute(
                "SELECT c.relname,c.relrowsecurity,c.relforcerowsecurity FROM pg_class c "
                "JOIN pg_namespace n ON n.oid=c.relnamespace "
                "WHERE n.nspname='ai_usage' AND c.relname IN ('financial_guardrail_policy','financial_reservation') "
                "ORDER BY c.relname"
            )
            require(cursor.fetchall() == [("financial_guardrail_policy", True, True), ("financial_reservation", True, True)],
                    "0042 tables must ENABLE and FORCE RLS")
            cursor.execute(
                "SELECT tablename,cmd,qual,with_check FROM pg_policies WHERE schemaname='ai_usage' "
                "AND tablename IN ('financial_guardrail_policy','financial_reservation') ORDER BY tablename"
            )
            policies = cursor.fetchall()
            require(len(policies) == 2 and all(row[1] == "ALL" for row in policies), "tenant ALL policies missing")
            require(all("app.tenant_id" in (row[2] or "") and "app.tenant_id" in (row[3] or "") for row in policies),
                    "tenant policy does not bind both visibility and writes")
            cursor.execute(
                "SELECT conname FROM pg_constraint WHERE conrelid='ai_usage.financial_reservation'::regclass "
                "AND contype IN ('u','f') ORDER BY conname"
            )
            constraints = {row[0] for row in cursor.fetchall()}
            require("ai_usage_financial_reservation_invocation" in constraints, "invocation uniqueness missing")
            require(len(constraints) >= 3, "required reservation foreign keys missing")
            cursor.execute("SELECT indexname FROM pg_indexes WHERE schemaname='ai_usage' AND tablename='financial_reservation'")
            require("ai_usage_financial_reservation_policy_idx" in {row[0] for row in cursor.fetchall()}, "policy index missing")
            cursor.execute("SELECT has_table_privilege(%s,'ai_usage.financial_reservation','INSERT,SELECT,UPDATE'), "
                           "has_table_privilege(%s,'ai_usage.financial_reservation','DELETE')", [worker_role, worker_role])
            require(cursor.fetchone() == (True, False), "runtime reservation permissions are not least privilege")
            cursor.execute("SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=%s", [app_role])
            require(cursor.fetchone() == (False, False), "app runtime role bypasses RLS")

    def test_02_rls_tenant_isolation_missing_context_and_trusted_identity_type(self):
        from django.db import connections
        from foundation.models import AIFinancialGuardrailPolicy, AIFinancialReservation
        from foundation.tenant_context import trusted_tenant_context

        reservation, _ = self._reserve("rls-a")
        with runtime("worker", TENANT_B) as cursor:
            cursor.execute("SELECT count(*) FROM ai_usage.financial_reservation WHERE id=%s", [str(reservation.id)])
            require(cursor.fetchone()[0] == 0, "tenant B read tenant A reservation")
            cursor.execute("UPDATE ai_usage.financial_reservation SET status='released' WHERE id=%s", [str(reservation.id)])
            require(cursor.rowcount == 0, "tenant B altered tenant A reservation")
            cursor.execute("SELECT count(*) FROM ai_usage.financial_guardrail_policy WHERE tenant_id=%s", [str(TENANT_A)])
            require(cursor.fetchone()[0] == 0, "tenant B read tenant A policy")
        connection = connections["worker"]
        connection.close()
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM ai_usage.financial_reservation")
            require(cursor.fetchone()[0] == 0, "missing tenant context did not fail closed")
        with self.assertRaises(TypeError):
            with trusted_tenant_context("request-controlled-tenant", actor_id="test", trace_id="x", using="worker"):
                pass
        with trusted_tenant_context(self._identity(), actor_id="test", trace_id="read", using="worker"):
            self.assertEqual(AIFinancialReservation.objects.using("worker").filter(pk=reservation.id).count(), 1)
            self.assertEqual(AIFinancialGuardrailPolicy.objects.using("worker").filter(tenant_id=TENANT_A).count(), 1)

    def test_03_concurrent_admission_quota_budget_and_duplicate_idempotency(self):
        from django.utils import timezone
        from foundation.ai_financial_guardrails import FinancialAdmissionDenied, FinancialGuardrailService
        from foundation.models import AIFinancialGuardrailPolicy, AIFinancialReservation
        from foundation.tenant_context import trusted_tenant_context

        with trusted_tenant_context(self._identity(), actor_id="test", trace_id="tight-policy", using="worker"):
            tight = AIFinancialGuardrailPolicy.objects.using("worker").create(
                tenant_id=TENANT_A, product_identifier="iso-smart", provider="synthetic-provider", model_identifier="tight-model",
                period_start=timezone.now() - timedelta(minutes=1), period_end=timezone.now() + timedelta(hours=1), currency="USD",
                max_request_count=1, max_input_tokens=100, max_output_tokens=100, max_reserved_cost=Decimal("0.0050000000"),
                policy_scope="controlled_test", authority_reference="SYNTHETIC_CONCURRENCY", status="enabled",
            )
        from foundation.models import AIModelPricingVersion
        AIModelPricingVersion.objects.using("default").create(
            provider="synthetic-provider", model_identifier="tight-model", effective_from=timezone.now() - timedelta(minutes=1),
            currency="USD", rate_unit=1000, input_token_rate=Decimal("0.1000000000"), output_token_rate=Decimal("0.4000000000"),
            source_reference="SYNTHETIC_TEST_TARIFF_ONLY", verification_status="verified",
        )
        barrier = threading.Barrier(2)
        original_pricing = __import__("foundation.ai_financial_guardrails", fromlist=["_pricing"])._pricing
        def slow_pricing(**kwargs):
            time.sleep(0.20)
            return original_pricing(**kwargs)
        def attempt(invocation):
            barrier.wait()
            try:
                with trusted_tenant_context(self._identity(), actor_id="concurrent", trace_id=invocation, using="worker"):
                    value, replay = FinancialGuardrailService(using="worker").reserve_controlled_test(
                        tenant_id=TENANT_A, invocation_id=invocation, provider="synthetic-provider", model_identifier="tight-model",
                        input_token_bound=10, max_output_tokens=5, usage_record=None)
                    return ("ok", str(value.id), replay)
            except FinancialAdmissionDenied as exc:
                return ("denied", exc.code, False)
        with patch("foundation.ai_financial_guardrails._pricing", side_effect=slow_pricing):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(attempt, ["concurrent-a", "concurrent-b"]))
        require(sum(item[0] == "ok" for item in results) == 1, f"concurrent cap admitted too many: {results}")
        require(any(item[1] in {"AI_REQUEST_QUOTA_EXHAUSTED", "AI_BUDGET_EXCEEDED"} for item in results if item[0] == "denied"),
                f"concurrent denial was not a guardrail: {results}")
        with trusted_tenant_context(self._identity(), actor_id="test", trace_id="verify", using="worker"):
            rows = list(AIFinancialReservation.objects.using("worker").filter(policy_id=tight.id))
            require(len(rows) == 1 and rows[0].reserved_cost <= tight.max_reserved_cost, "concurrency overspent the policy")
        first, replay_a = self._reserve("idempotent-a")
        second, replay_b = self._reserve("idempotent-a")
        require(first.id == second.id and not replay_a and replay_b, "stable invocation was not idempotent")
        with self.assertRaises(FinancialAdmissionDenied) as conflict:
            self._reserve("idempotent-a", input_tokens=11)
        self.assertEqual(conflict.exception.code, "AI_RESERVATION_IDENTITY_CONFLICT")

    def test_04_rollback_decimal_pricing_bounds_and_settlement_recovery(self):
        from django.db import connections
        from django.utils import timezone
        from foundation.ai_financial_guardrails import FinancialAdmissionDenied, FinancialGuardrailService
        from foundation.models import AIFinancialGuardrailPolicy, AIFinancialReservation
        from foundation.tenant_context import trusted_tenant_context

        with self.assertRaises(RuntimeError):
            with trusted_tenant_context(self._identity(), actor_id="test", trace_id="rollback", using="worker"):
                FinancialGuardrailService(using="worker").reserve_controlled_test(
                    tenant_id=TENANT_A, invocation_id="rolled-back", provider="synthetic-provider", model_identifier="synthetic-model",
                    input_token_bound=10, max_output_tokens=10, usage_record=None)
                raise RuntimeError("force outer rollback")
        with trusted_tenant_context(self._identity(), actor_id="test", trace_id="rollback-check", using="worker"):
            require(AIFinancialReservation.objects.using("worker").filter(invocation_id="rolled-back").count() == 0,
                    "rolled back reservation consumed budget")
        with self.assertRaises(FinancialAdmissionDenied) as invalid:
            self._reserve("invalid-bound", input_tokens=-1)
        self.assertEqual(invalid.exception.code, "AI_INPUT_BOUND_INVALID")
        with trusted_tenant_context(self._identity(), actor_id="test", trace_id="period-and-currency", using="worker"):
            AIFinancialGuardrailPolicy.objects.using("worker").create(
                tenant_id=TENANT_A, product_identifier="iso-smart", provider="synthetic-provider", model_identifier="currency-mismatch",
                period_start=timezone.now() - timedelta(minutes=1), period_end=timezone.now() + timedelta(hours=1), currency="EUR",
                max_request_count=1, max_input_tokens=10, max_output_tokens=10, max_reserved_cost=Decimal("1"),
                policy_scope="controlled_test", authority_reference="SYNTHETIC_CURRENCY", status="enabled",
            )
            AIFinancialGuardrailPolicy.objects.using("worker").create(
                tenant_id=TENANT_A, product_identifier="iso-smart", provider="synthetic-provider", model_identifier="expired-policy",
                period_start=timezone.now() - timedelta(days=2), period_end=timezone.now() - timedelta(days=1), currency="USD",
                max_request_count=1, max_input_tokens=10, max_output_tokens=10, max_reserved_cost=Decimal("1"),
                policy_scope="controlled_test", authority_reference="SYNTHETIC_PERIOD", status="enabled",
            )
        from foundation.models import AIModelPricingVersion
        AIModelPricingVersion.objects.using("default").create(
            provider="synthetic-provider", model_identifier="currency-mismatch", effective_from=timezone.now() - timedelta(minutes=1),
            currency="USD", rate_unit=1000, input_token_rate=Decimal("0.1000000000"), output_token_rate=Decimal("0.4000000000"),
            source_reference="SYNTHETIC_TEST_TARIFF_ONLY", verification_status="verified",
        )
        with trusted_tenant_context(self._identity(), actor_id="test", trace_id="currency", using="worker"):
            with self.assertRaises(FinancialAdmissionDenied) as currency_error:
                FinancialGuardrailService(using="worker").reserve_controlled_test(
                    tenant_id=TENANT_A, invocation_id="currency-mismatch", provider="synthetic-provider",
                    model_identifier="currency-mismatch", input_token_bound=1, max_output_tokens=1, usage_record=None)
            self.assertEqual(currency_error.exception.code, "AI_CURRENCY_MISMATCH")
            with self.assertRaises(FinancialAdmissionDenied) as period_error:
                FinancialGuardrailService(using="worker").reserve_controlled_test(
                    tenant_id=TENANT_A, invocation_id="expired-policy", provider="synthetic-provider",
                    model_identifier="expired-policy", input_token_bound=1, max_output_tokens=1, usage_record=None)
            self.assertEqual(period_error.exception.code, "AI_GUARDRAIL_POLICY_MISSING")
        reserved, _ = self._reserve("settlement-known", input_tokens=10, output_tokens=10)
        with trusted_tenant_context(self._identity(), actor_id="test", trace_id="settle", using="worker"):
            settled = FinancialGuardrailService(using="worker").settle(reservation_id=reserved.id, actual_cost=Decimal("0.0010000000"), usage_complete=True)
            repeated = FinancialGuardrailService(using="worker").settle(reservation_id=reserved.id, actual_cost=Decimal("0.0010000000"), usage_complete=True)
            require(settled.status == repeated.status == "settled" and repeated.settled_cost == Decimal("0.0010000000"), "settlement is not idempotent")
        unknown, _ = self._reserve("settlement-unknown")
        with trusted_tenant_context(self._identity(), actor_id="test", trace_id="unknown", using="worker"):
            unresolved = FinancialGuardrailService(using="worker").settle(reservation_id=unknown.id, actual_cost=None, usage_complete=False)
            require(unresolved.status == "unresolved" and unresolved.settled_cost is None, "unknown usage released exposure")
        released, _ = self._reserve("proven-not-dispatched")
        with trusted_tenant_context(self._identity(), actor_id="test", trace_id="release", using="worker"):
            result = FinancialGuardrailService(using="worker").release_before_dispatch(reservation_id=released.id)
            require(result.status == "released" and result.resolution_reason == "PROVEN_NOT_DISPATCHED", "proven non-execution was not released")
        with self.assertRaises(AIFinancialReservation.DoesNotExist):
            with trusted_tenant_context(self._identity(TENANT_B), actor_id="test", trace_id="cross-tenant", using="worker"):
                FinancialGuardrailService(using="worker").settle(reservation_id=unknown.id, actual_cost=Decimal("0"), usage_complete=True)


def run():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FinancialGuardrailPostgreSQLTests)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(f"AI_FINANCIAL_GUARDRAILS_POSTGRES_PASS={result.testsRun}")


if __name__ == "__main__":
    run()
