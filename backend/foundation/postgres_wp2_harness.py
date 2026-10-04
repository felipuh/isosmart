"""Disposable PostgreSQL WP2 harness executed by ``postgres_foundation_gate``."""

import os
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import postgres_foundation_harness as foundation_gate


def run_action_execution_rollback_acceptance():
    """Exercise the source ActionExecution rollback contract on PostgreSQL.

    This deliberately reuses the promoted controlled-Opportunity capability;
    it is acceptance evidence for ``rollback_ref``, not another executor.
    """
    import postgres_phase14_harness as phase14
    import postgres_phase16_harness as phase16
    from django.db import DatabaseError, connections
    from foundation.action_execution import (
        ActionExecutionService, ExecutionPrincipalContext, ExecutionRejected,
        SyntheticPreconditionEvaluator,
    )
    from foundation.action_authorization import IdempotencyConflict
    from foundation.controlled_opportunity import ControlledOpportunityActionService
    from foundation.models import (
        ActionExecution, ActionExecutionReceipt, ActionExecutionRollback,
        ActionPlan, ImmutableAuditLog, Opportunity,
    )
    from foundation.qms_context import QmsContextCommandService
    from foundation.risk_objective import RiskOpportunityObjectiveCommandService
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

    identity = TrustedTenantIdentity("wp2-rollback-a", foundation_gate.TENANT_A)
    other_identity = TrustedTenantIdentity("wp2-rollback-b", foundation_gate.TENANT_B)
    trace = uuid4()
    ids, _ = phase14.seed_chain(connections["default"], foundation_gate.TENANT_A,
                                foundation_gate.ORG_A, "WP2RB", 3)
    process = QmsContextCommandService(using="app").create_process(
        identity=identity, organization_id=foundation_gate.ORG_A,
        name="WP2 rollback acceptance", actor_id="wp2-rollback", trace_id=trace,
    )
    created = RiskOpportunityObjectiveCommandService(using="app").create_opportunity(
        identity=identity, process_id=process.entity_id, hypothesis="Reversible fixture",
        benefit="Evidence", feasibility="Controlled", status="under_evaluation",
        actor_id="wp2-rollback", trace_id=trace,
    )
    with trusted_tenant_context(identity, actor_id="wp2-read", trace_id=trace, using="app"):
        original_leaf = Opportunity.objects.using("app").get(pk=created.entity_id)
    _, forward_auth = phase16.build_controlled_authorization(
        identity, ids, trace, original_leaf, "wp2-forward", "opportunity.defer_evaluation",
        "under_evaluation", "deferred",
    )
    controlled = ControlledOpportunityActionService(using="executor")
    forward = controlled.defer_evaluation(
        identity=identity, authorization_id=forward_auth.authorization_id,
        idempotency_key="wp2-forward",
    )
    with trusted_tenant_context(identity, actor_id="wp2-read", trace_id=trace, using="app"):
        deferred = Opportunity.objects.using("app").get(pk=forward.after_revision_id)
    resume_ids, resume_trace = phase14.seed_chain(
        connections["default"], foundation_gate.TENANT_A, foundation_gate.ORG_A, "WP2RBRES", 3)
    _, resume_auth = phase16.build_controlled_authorization(
        identity, resume_ids, resume_trace, deferred, "wp2-resume",
        "opportunity.resume_evaluation", "deferred", "under_evaluation",
    )
    rollback_service = ActionExecutionService(using="executor")
    principal = ExecutionPrincipalContext(identity, SyntheticPreconditionEvaluator({}))
    rollback = rollback_service.rollback_controlled_opportunity(
        principal=principal, original_execution_id=forward.execution_id,
        compensation_authorization_id=resume_auth.authorization_id,
        idempotency_key="wp2-rollback", reason="Source-backed rollback acceptance",
    )
    replay = rollback_service.rollback_controlled_opportunity(
        principal=principal, original_execution_id=forward.execution_id,
        compensation_authorization_id=resume_auth.authorization_id,
        idempotency_key="wp2-rollback", reason="Source-backed rollback acceptance",
    )
    require = foundation_gate.require
    require(rollback.id == replay.id, "rollback replay created a duplicate")
    with trusted_tenant_context(identity, actor_id="wp2-read", trace_id=trace, using="app"):
        source = ActionExecution.objects.using("app").get(pk=forward.execution_id)
        compensation = ActionExecution.objects.using("app").get(pk=rollback.compensating_execution_id)
        source_receipt = ActionExecutionReceipt.objects.using("app").get(action_execution_id=source.id)
        compensation_receipt = ActionExecutionReceipt.objects.using("app").get(action_execution_id=compensation.id)
        require(source.rollback_ref.id == rollback.id, "rollback_ref was not persisted")
        require(source.status == compensation.status == "succeeded", "terminal lineage missing")
        require(source_receipt.result_hash and compensation_receipt.result_hash, "receipt integrity missing")
        require(source_receipt.result["opportunity_lineage_id"] == compensation_receipt.result["opportunity_lineage_id"], "forward/reverse lineage differs")
        require(ActionExecutionRollback.objects.using("app").filter(original_execution_id=source.id).count() == 1, "duplicate rollback row")
        require(ImmutableAuditLog.objects.using("app").filter(entity_id=rollback.id, action="action_execution.rolled_back").count() == 1, "rollback audit provenance missing")
        resumed = Opportunity.objects.using("app").get(pk=compensation_receipt.result["after_revision_id"])
        require(resumed.status == "under_evaluation", "compensation did not restore controlled state")

    # Same source/key racing resolves to one immutable lineage record.
    def replay_race():
        try:
            return rollback_service.rollback_controlled_opportunity(
                principal=principal, original_execution_id=forward.execution_id,
                compensation_authorization_id=resume_auth.authorization_id,
                idempotency_key="wp2-rollback", reason="Source-backed rollback acceptance",
            ).id
        finally:
            connections["executor"].close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        raced = list(pool.map(lambda _: replay_race(), range(2)))
    require(raced == [rollback.id, rollback.id], "concurrent replay was not deterministic")

    # A successful but non-reversible synthetic execution cannot become lineage.
    synthetic_plan, synthetic_auth = phase14.build_authorization(identity, ids, trace, "wp2-nonreversible")
    with trusted_tenant_context(identity, actor_id="wp2-read", trace_id=trace, using="executor"):
        plan = ActionPlan.objects.using("executor").get(pk=synthetic_plan.action_plan_id)
    synthetic_principal = ExecutionPrincipalContext(
        identity,
        SyntheticPreconditionEvaluator({item["identity"]: "satisfied" for item in plan.preconditions}),
    )
    synthetic = ActionExecutionService(using="executor").execute_authorized_action(
        principal=synthetic_principal, authorization_id=synthetic_auth.authorization_id,
        idempotency_key="wp2-nonreversible", trace_id=trace,
    )
    for source_id, auth_id, expected in (
        (synthetic.execution_id, resume_auth.authorization_id, "not_reversible"),
        # The source execution already has immutable rollback lineage, so a
        # different request key is rejected before any compensation check.
        (forward.execution_id, forward_auth.authorization_id, "idempotency_conflict"),
    ):
        try:
            rollback_service.rollback_controlled_opportunity(
                principal=principal, original_execution_id=source_id,
                compensation_authorization_id=auth_id, idempotency_key=f"wp2-reject-{expected}", reason="reject",
            )
            raise AssertionError(f"{expected} accepted")
        except IdempotencyConflict:
            require(expected == "idempotency_conflict", "unexpected rollback idempotency conflict")
        except ExecutionRejected as exc:
            require(exc.reason_code == expected, f"wrong rejection: {exc.reason_code}")
    try:
        rollback_service.rollback_controlled_opportunity(
            principal=ExecutionPrincipalContext(other_identity, SyntheticPreconditionEvaluator({})),
            original_execution_id=forward.execution_id, compensation_authorization_id=resume_auth.authorization_id,
            idempotency_key="wp2-cross-tenant", reason="reject",
        )
        raise AssertionError("cross-tenant rollback was accepted")
    except ExecutionRejected as exc:
        require(exc.reason_code == "rollback_execution_not_found", "cross-tenant disclosure")
    with trusted_tenant_context(other_identity, actor_id="wp2-other", trace_id=uuid4(), using="app"):
        require(not ActionExecutionRollback.objects.using("app").filter(pk=rollback.id).exists(), "RLS read isolation failed")
    with trusted_tenant_context(identity, actor_id="wp2-read", trace_id=trace, using="app"):
        try:
            ActionExecutionRollback.objects.using("app").filter(pk=rollback.id).update(reason="mutated")
            raise AssertionError("rollback mutation was accepted")
        except DatabaseError:
            pass
    print("ACTION_EXECUTION_ROLLBACK_ACCEPTANCE_PASS=18")


def run():
    full_repository = os.getenv("FULL_REPOSITORY_TESTS") == "1"
    full_regression = full_repository or os.getenv("FULL_FOUNDATION_TESTS") == "1"
    if full_regression:
        os.environ.update({
            "DJANGO_SETTINGS_MODULE": "backend.settings_postgres_integration",
            "ISO_SMART_POSTGRES_INTEGRATION": "1",
            "USE_SQLITE_DATABASE": "0",
            "DB_NAME": os.environ["FOUNDATION_DB_NAME"],
            "DB_USER": os.environ["FOUNDATION_MIGRATOR_ROLE"],
            "DB_PASSWORD": os.environ["FOUNDATION_MIGRATOR_PASSWORD"],
            "DB_HOST": os.environ["FOUNDATION_DB_HOST"],
            "DB_PORT": os.environ["FOUNDATION_DB_PORT"],
        })
        role_bindings = (
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
            ("rule_publisher", "FOUNDATION_RULE_PUBLISHER_ROLE"),
            ("rule_activator", "FOUNDATION_RULE_ACTIVATOR_ROLE"),
            ("rule_adopter", "FOUNDATION_RULE_ADOPTER_ROLE"),
            ("rule_resolver", "FOUNDATION_RULE_RESOLVER_ROLE"),
            ("release_repair", "FOUNDATION_RELEASE_REPAIR_ROLE"),
            ("release_controller", "FOUNDATION_RELEASE_CONTROLLER_ROLE"),
        )
        os.environ["DB_SESSION_OPTIONS"] = " ".join(
            f"-c foundation.{setting}_role={os.environ[env_name]}"
            for setting, env_name in role_bindings
        )
        import django

        django.setup()
        from django.conf import settings

        settings.IS_DEVELOPMENT = False
        if "testserver" not in settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS.append("testserver")
        os.chdir(Path(__file__).parents[1])
        for alias in ("audit_writer",):
            settings.DATABASES[alias] = dict(settings.DATABASES["default"])
            settings.DATABASES[alias]["USER"] = os.environ["FOUNDATION_AUDIT_WRITER_ROLE"]
            settings.DATABASES[alias]["PASSWORD"] = os.environ["FOUNDATION_AUDIT_WRITER_PASSWORD"]
    else:
        foundation_gate.configure_django()
        from django.conf import settings

        settings.IS_DEVELOPMENT = False

    from django.core.management import call_command

    call_command("migrate", database="default", verbosity=0, interactive=False)

    if not full_regression:
        from foundation.test_source_artifact_postgres_integration import (
            SourceArtifactPostgreSQLIntegrationTests,
        )

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(
            SourceArtifactPostgreSQLIntegrationTests,
        )
        result = unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
        run_action_execution_rollback_acceptance()
        print(f"WP2_POSTGRES_TESTS_PASS={result.testsRun}")

    if full_regression:
        from django.test.utils import setup_test_environment, teardown_test_environment
        # Match Django's runner (including in-memory email), while reusing only
        # the disposable database already migrated by the official harness.
        setup_test_environment()
        loader = unittest.defaultTestLoader
        full_suite = loader.discover(
            str(Path(__file__).parent.parent), pattern="test*.py",
            top_level_dir=str(Path(__file__).parent.parent),
        ) if full_repository else unittest.TestSuite([
            loader.loadTestsFromName("foundation.tests"),
            loader.discover(
                str(Path(__file__).parent), pattern="test_*.py",
                top_level_dir=str(Path(__file__).parent.parent),
            ),
        ])
        try:
            full_result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(full_suite)
        finally:
            teardown_test_environment()
        print(f"REGRESSION_COUNTS run={full_result.testsRun} failures={len(full_result.failures)} "
              f"errors={len(full_result.errors)} skipped={len(full_result.skipped)}")
        if not full_result.wasSuccessful():
            raise SystemExit(1)
        print(f"FOUNDATION_FULL_TESTS_PASS={full_result.testsRun}")


if __name__ == "__main__":
    run()
