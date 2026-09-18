"""PostgreSQL 18.6 Phase-23 review/decision/authorization blocking matrix."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import postgres_foundation_harness as phase3
import postgres_phase21_harness as phase21


PHASE21 = ("foundation", "0018_governed_learning_foundation")
PHASE23 = ("foundation", "0019_learning_proposal_review_application_authorization_foundation")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def counts(models, alias, event_type):
    Review, Decision, Authorization, DomainEvent, Outbox, Audit = models
    return (
        Review.objects.using("default").count(), Decision.objects.using("default").count(),
        Authorization.objects.using("default").count(),
        DomainEvent.objects.using("default").filter(event_type=event_type).count(),
        Outbox.objects.using("default").filter(domain_event__event_type=event_type).count(),
        Audit.objects.using("default").filter(action=event_type).count(),
    )


def run():
    phase21.run()
    from django.db import connections

    phase3.migrate(PHASE23)
    with connections["default"].cursor() as cursor:
        cursor.execute(
            "SELECT to_regclass('qms.learning_proposal_review'),"
            "to_regclass('qms.learning_proposal_decision'),"
            "to_regclass('qms.learning_application_authorization')"
        )
        require(cursor.fetchone() == (
            "qms.learning_proposal_review", "qms.learning_proposal_decision",
            "qms.learning_application_authorization",
        ), "Phase 23 tables missing")
    phase3.migrate(PHASE21)
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.learning_proposal_review')")
        require(cursor.fetchone()[0] is None, "empty-history Phase 23 reverse failed")
    phase3.migrate(PHASE23)

    from foundation.agent_runtime import AgentCatalogCommandService
    from foundation.knowledge_layer import KnowledgeLayerCommandService
    from foundation.learning_proposal_governance import (
        CAPABILITY_BY_TARGET,
        GovernanceConflict,
        GovernanceFailurePoint,
        LearningApplicationAuthorizationCommandService,
        LearningProposalDecisionCommandService,
        LearningProposalReviewCommandService,
        LearningReviewFindings,
        TrustedLearningApplicationAuthority,
        TrustedLearningDecisionAuthority,
        TrustedLearningReviewAuthority,
    )
    from foundation.models import (
        AgentDefinition, DomainEvent, ImmutableAuditLog, KnowledgeLayerRule, ModelPolicy,
        LearningApplicationAuthorization, LearningProposal,
        LearningProposalDecision, LearningProposalReview,
        TransactionalOutbox,
    )
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

    # Three distinct synthetic humans are projections only; AdminApps decisions remain trusted inputs.
    actor_rows = []
    with connections["default"].cursor() as cursor:
        for index in range(3):
            projection_id, external_id = uuid4(), uuid4()
            cursor.execute(
                "INSERT INTO qms.user_projection"
                "(id,adminapps_user_id,tenant_id,source_version,source_event_id,lifecycle_status,last_synced_at) "
                "VALUES(%s,%s,%s,1,%s,'active',statement_timestamp())",
                [str(projection_id), str(external_id), str(phase3.TENANT_A), str(uuid4())],
            )
            actor_rows.append((projection_id, external_id))

    identity = TrustedTenantIdentity("phase23-global-governance", phase3.TENANT_A)
    reviewer = TrustedLearningReviewAuthority(
        identity, phase3.ORG_A, actor_rows[0][0], actor_rows[0][1],
        frozenset({"qms.learning_proposal.review"}), True, True, True,
        "adminapps-learning-review/v1", "phase23-review-authority",
    )
    approver = TrustedLearningDecisionAuthority(
        identity, phase3.ORG_A, actor_rows[1][0], actor_rows[1][1],
        frozenset({"qms.learning_proposal.decide"}), True, True, True,
        "adminapps-learning-decision/v1", "phase23-decision-authority",
    )
    authorizer = TrustedLearningApplicationAuthority(
        identity, phase3.ORG_A, actor_rows[2][0], actor_rows[2][1],
        frozenset({"qms.learning_application.authorize"}), True, True, True,
        "adminapps-learning-authorization/v1", "phase23-authorization-authority",
    )
    findings = LearningReviewFindings(
        summary="Exact proposal and target provenance reviewed; no prohibited change detected.",
        governance_domains=("ai_governance", "security"),
    )
    review_service = LearningProposalReviewCommandService()
    decision_service = LearningProposalDecisionCommandService()
    authorization_service = LearningApplicationAuthorizationCommandService()
    models = (
        LearningProposalReview, LearningProposalDecision,
        LearningApplicationAuthorization, DomainEvent,
        TransactionalOutbox, ImmutableAuditLog,
    )

    proposals = list(
        LearningProposal.objects.using("default")
        .filter(successor__isnull=True).order_by("target_type", "created_at")
    )
    require(len(proposals) >= 3, "three current Phase 21 proposals required")
    by_target = {row.target_type: row for row in proposals}
    require(set(CAPABILITY_BY_TARGET).issubset(by_target), "current proposal per target required")
    protected_before = phase21.protected_snapshot(connections["default"])

    # Review rollback: artifact/event/outbox/audit/before-commit are one unit.
    for point in GovernanceFailurePoint:
        before = counts(models, "learning_reviewer", "learning_proposal.reviewed")
        try:
            review_service.record_learning_proposal_review(
                authority=reviewer, proposal_id=by_target["AgentDefinition"].id,
                findings=findings, trace_id=uuid4(), failure_point=point,
            )
        except RuntimeError as exc:
            require("deliberate Phase 23 rollback" in str(exc), f"unexpected review rollback: {exc}")
        else:
            raise AssertionError(f"review failure point committed: {point.value}")
        after = counts(models, "learning_reviewer", "learning_proposal.reviewed")
        require(after == before, f"partial review governance unit at {point.value}")

    # Two independent review commands may both append evidence.
    def record_review(_):
        try:
            return LearningProposalReviewCommandService().record_learning_proposal_review(
                authority=reviewer, proposal_id=by_target["AgentDefinition"].id,
                findings=findings, trace_id=uuid4(),
            )
        except Exception as exc:
            connections["learning_reviewer"].close()
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        review_results = list(pool.map(record_review, range(2)))
    require(all(not isinstance(item, Exception) for item in review_results),
            f"concurrent reviews did not both append: {review_results}")
    review_ids = [item.artifact_id for item in review_results]

    # Proposal creator, reviewer-only authority, and non-human technical contexts cannot approve.
    creator_approver = TrustedLearningDecisionAuthority(
        identity, phase3.ORG_A,
        by_target["AgentDefinition"].actor_user_projection_id,
        by_target["AgentDefinition"].actor_external_id_snapshot,
        frozenset({"qms.learning_proposal.decide"}), True, True, True,
        "adminapps-learning-decision/v1", "phase23-self-decision-denied",
    )
    for denied_authority in (creator_approver, reviewer):
        try:
            decision_service.record_learning_proposal_decision(
                authority=denied_authority, proposal_id=by_target["AgentDefinition"].id,
                review_ids=review_ids, outcome="approved_for_application",
                rationale="This path must fail closed.", trace_id=uuid4(),
            )
        except (PermissionError, TypeError):
            pass
        else:
            raise AssertionError("creator or review-only authority approved a proposal")

    # Decision rollback and one-effective-decision concurrency/replay.
    for point in GovernanceFailurePoint:
        before = counts(models, "learning_approver", "learning_proposal.decision_recorded")
        try:
            decision_service.record_learning_proposal_decision(
                authority=approver, proposal_id=by_target["AgentDefinition"].id,
                review_ids=review_ids, outcome="approved_for_application",
                rationale="Eligible only to request a separate inert authorization.",
                trace_id=uuid4(), failure_point=point,
            )
        except RuntimeError as exc:
            require("deliberate Phase 23 rollback" in str(exc), f"unexpected decision rollback: {exc}")
        else:
            raise AssertionError(f"decision failure point committed: {point.value}")
        after = counts(models, "learning_approver", "learning_proposal.decision_recorded")
        require(after == before, f"partial decision governance unit at {point.value}")

    def decide(_):
        try:
            return LearningProposalDecisionCommandService().record_learning_proposal_decision(
                authority=approver, proposal_id=by_target["AgentDefinition"].id,
                review_ids=review_ids, outcome="approved_for_application",
                rationale="Eligible only to request a separate inert authorization.", trace_id=uuid4(),
            )
        except Exception as exc:
            connections["learning_approver"].close()
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        decision_results = list(pool.map(decide, range(2)))
    require(all(not isinstance(item, Exception) for item in decision_results),
            f"decision concurrency failed: {decision_results}")
    require(len({item.artifact_id for item in decision_results}) == 1 and
            sum(item.replayed for item in decision_results) == 1,
            "decision race did not yield one artifact plus deterministic replay")
    decision_id = decision_results[0].artifact_id

    creator_authorizer = TrustedLearningApplicationAuthority(
        identity, phase3.ORG_A,
        by_target["AgentDefinition"].actor_user_projection_id,
        by_target["AgentDefinition"].actor_external_id_snapshot,
        frozenset({"qms.learning_application.authorize"}), True, True, True,
        "adminapps-learning-authorization/v1", "phase23-self-grant-denied",
    )
    approver_as_authorizer = TrustedLearningApplicationAuthority(
        identity, phase3.ORG_A, actor_rows[1][0], actor_rows[1][1],
        frozenset({"qms.learning_application.authorize"}), True, True, True,
        "adminapps-learning-authorization/v1", "phase23-combined-duty-denied",
    )
    for denied_authority in (creator_authorizer, approver_as_authorizer):
        try:
            authorization_service.authorize_learning_proposal_application(
                authority=denied_authority, proposal_id=by_target["AgentDefinition"].id,
                decision_id=decision_id, capability_id="revise_agent_definition",
                idempotency_key=f"denied-{denied_authority.actor_external_id}", trace_id=uuid4(),
            )
        except PermissionError:
            pass
        else:
            raise AssertionError("creator or decision approver authorized the same proposal")

    # Authorization rollback, replay, and changed-provenance conflict.
    for point in GovernanceFailurePoint:
        before = counts(models, "learning_authorizer", "learning_application.authorized")
        try:
            authorization_service.authorize_learning_proposal_application(
                authority=authorizer, proposal_id=by_target["AgentDefinition"].id,
                decision_id=decision_id, capability_id="revise_agent_definition",
                idempotency_key="phase23-agent-auth", trace_id=uuid4(), failure_point=point,
            )
        except RuntimeError as exc:
            require("deliberate Phase 23 rollback" in str(exc), f"unexpected authorization rollback: {exc}")
        else:
            raise AssertionError(f"authorization failure point committed: {point.value}")
        after = counts(models, "learning_authorizer", "learning_application.authorized")
        require(after == before, f"partial authorization governance unit at {point.value}")

    first_authorization = authorization_service.authorize_learning_proposal_application(
        authority=authorizer, proposal_id=by_target["AgentDefinition"].id,
        decision_id=decision_id, capability_id="revise_agent_definition",
        idempotency_key="phase23-agent-auth", trace_id=uuid4(),
    )
    replay = authorization_service.authorize_learning_proposal_application(
        authority=authorizer, proposal_id=by_target["AgentDefinition"].id,
        decision_id=decision_id, capability_id="revise_agent_definition",
        idempotency_key="phase23-agent-auth", trace_id=uuid4(),
    )
    require(replay.replayed and replay.artifact_id == first_authorization.artifact_id,
            "exact authorization replay did not return the same artifact")
    require(authorization_service.classify_authorization(
        authority=authorizer, authorization_id=first_authorization.artifact_id) == "VALID",
        "fresh exact authorization was not VALID")

    # Build a second exact approved chain and prove same key + different provenance conflicts.
    knowledge_review = review_service.record_learning_proposal_review(
        authority=reviewer, proposal_id=by_target["KnowledgeLayerRule"].id,
        findings=findings, trace_id=uuid4(),
    )
    knowledge_decision = decision_service.record_learning_proposal_decision(
        authority=approver, proposal_id=by_target["KnowledgeLayerRule"].id,
        review_ids=[knowledge_review.artifact_id], outcome="approved_for_application",
        rationale="Separate exact knowledge proposal decision.", trace_id=uuid4(),
    )
    try:
        authorization_service.authorize_learning_proposal_application(
            authority=authorizer, proposal_id=by_target["KnowledgeLayerRule"].id,
            decision_id=knowledge_decision.artifact_id,
            capability_id="revise_knowledge_layer_rule",
            idempotency_key="phase23-agent-auth", trace_id=uuid4(),
        )
    except GovernanceConflict:
        pass
    else:
        raise AssertionError("same idempotency key accepted different proposal provenance")

    # Two authorizers racing the exact same tuple yield one immutable artifact and one replay.
    model_review = review_service.record_learning_proposal_review(
        authority=reviewer, proposal_id=by_target["ModelPolicy"].id,
        findings=findings, trace_id=uuid4(),
    )
    model_decision = decision_service.record_learning_proposal_decision(
        authority=approver, proposal_id=by_target["ModelPolicy"].id,
        review_ids=[model_review.artifact_id], outcome="approved_for_application",
        rationale="Separate exact ModelPolicy governance decision.", trace_id=uuid4(),
    )

    def authorize_model(_):
        try:
            return LearningApplicationAuthorizationCommandService().authorize_learning_proposal_application(
                authority=authorizer, proposal_id=by_target["ModelPolicy"].id,
                decision_id=model_decision.artifact_id, capability_id="revise_model_policy",
                idempotency_key="phase23-concurrent-model-auth", trace_id=uuid4(),
            )
        except Exception as exc:
            connections["learning_authorizer"].close()
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        concurrent_authorizations = list(pool.map(authorize_model, range(2)))
    require(all(not isinstance(item, Exception) for item in concurrent_authorizations),
            f"authorization concurrency failed: {concurrent_authorizations}")
    require(len({item.artifact_id for item in concurrent_authorizations}) == 1 and
            sum(item.replayed for item in concurrent_authorizations) == 1,
            "authorization race did not yield one artifact plus deterministic replay")
    model_authorization_id = concurrent_authorizations[0].artifact_id

    # Superseded P1 is historical only and cannot receive a decision.
    stale_proposal = LearningProposal.objects.using("default").filter(successor__isnull=False).first()
    require(stale_proposal is not None, "Phase 21 superseded proposal fixture missing")
    stale_review = review_service.record_learning_proposal_review(
        authority=reviewer, proposal_id=stale_proposal.id, findings=findings, trace_id=uuid4(),
    )
    try:
        decision_service.record_learning_proposal_decision(
            authority=approver, proposal_id=stale_proposal.id,
            review_ids=[stale_review.artifact_id], outcome="rejected",
            rationale="Historical stale proposal.", trace_id=uuid4(),
        )
    except GovernanceConflict:
        pass
    else:
        raise AssertionError("superseded proposal received a decision")

    # Governance activity itself has no target, runtime, autonomy, or normative effect.
    protected_after_governance = phase21.protected_snapshot(connections["default"])
    require(protected_after_governance == protected_before,
            "review/decision/authorization mutated a protected target")

    # Controlled existing curator path introduces drift; authorization remains immutable and classifies STALE.
    policy = ModelPolicy.objects.using("agent_catalog_curator").get(
        pk=by_target["ModelPolicy"].target_id
    )
    AgentCatalogCommandService(using="agent_catalog_curator").revise_model_policy(
        previous_revision_id=policy.id, version=f"{policy.version}-phase23-drift",
        approved_models=policy.approved_models, data_classes=policy.data_classes,
        guardrails=policy.guardrails, human_gate_rules=policy.human_gate_rules,
        actor_id="phase23-controlled-curator",
        trace_id=uuid4(),
    )
    require(authorization_service.classify_authorization(
        authority=authorizer, authorization_id=model_authorization_id) == "STALE",
        "target drift did not classify historical authorization as STALE")
    try:
        authorization_service.authorize_learning_proposal_application(
            authority=authorizer, proposal_id=by_target["ModelPolicy"].id,
            decision_id=model_decision.artifact_id, capability_id="revise_model_policy",
            idempotency_key="phase23-after-drift", trace_id=uuid4(),
        )
    except GovernanceConflict:
        pass
    else:
        raise AssertionError("target drift allowed a new authorization or rebinding")

    # A target-curator drift racing authorization ends either denied or historical-and-STALE.
    rule = KnowledgeLayerRule.objects.using("normative_curator").get(
        pk=by_target["KnowledgeLayerRule"].target_id
    )
    race_barrier = Barrier(2)

    def race_authorize():
        race_barrier.wait()
        try:
            return LearningApplicationAuthorizationCommandService().authorize_learning_proposal_application(
                authority=authorizer, proposal_id=by_target["KnowledgeLayerRule"].id,
                decision_id=knowledge_decision.artifact_id,
                capability_id="revise_knowledge_layer_rule",
                idempotency_key="phase23-knowledge-drift-race", trace_id=uuid4(),
            )
        except Exception as exc:
            connections["learning_authorizer"].close()
            return exc

    def race_drift():
        race_barrier.wait()
        try:
            return KnowledgeLayerCommandService(using="normative_curator").revise_knowledge_layer_rule(
                previous_revision_id=rule.id, version=f"{rule.version}-phase23-drift",
                logic_json=rule.logic_json, evidence_expectation=rule.evidence_expectation,
                source_reference=rule.source_reference, actor_id="phase23-controlled-curator",
                trace_id=uuid4(),
            )
        finally:
            connections["normative_curator"].close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        authorization_race = pool.submit(race_authorize)
        drift_race = pool.submit(race_drift)
        race_result = authorization_race.result()
        drift_race.result()
    if not isinstance(race_result, Exception):
        require(authorization_service.classify_authorization(
            authority=authorizer, authorization_id=race_result.artifact_id) == "STALE",
            "authorization that won before target drift did not become STALE")
    else:
        require(isinstance(race_result, GovernanceConflict) or "target drift" in str(race_result).lower(),
                f"target-drift race failed for an unexpected reason: {race_result}")

    # Tenant isolation, immutable raw SQL, catalog roles, and no target DML.
    visibility = []
    for alias, table in (
        ("learning_reviewer", "qms.learning_proposal_review"),
        ("learning_approver", "qms.learning_proposal_decision"),
        ("learning_authorizer", "qms.learning_application_authorization"),
    ):
        row = []
        for tenant in (phase3.TENANT_A, None, phase3.TENANT_B):
            with phase3.runtime_transaction(alias, tenant) as cursor:
                cursor.execute(f"SELECT count(*) FROM {table}")
                row.append(cursor.fetchone()[0])
        visibility.append(row)
        require(row[0] > 0 and row[1:] == [0, 0], f"Phase 23 RLS failed for {table}: {row}")

    for alias, table, column in (
        ("learning_reviewer", "qms.learning_proposal_review", "review_outcome"),
        ("learning_approver", "qms.learning_proposal_decision", "outcome"),
        ("learning_authorizer", "qms.learning_application_authorization", "authorization_status"),
    ):
        for statement in (f"UPDATE {table} SET {column}={column}", f"DELETE FROM {table}"):
            try:
                with phase3.runtime_transaction(alias, phase3.TENANT_A) as cursor:
                    cursor.execute(statement)
            except Exception:
                pass
            else:
                raise AssertionError(f"raw immutable history mutation succeeded: {statement}")

    with connections["default"].cursor() as cursor:
        principal_names = [
            os.environ["FOUNDATION_LEARNING_REVIEWER_ROLE"],
            os.environ["FOUNDATION_LEARNING_APPROVER_ROLE"],
            os.environ["FOUNDATION_LEARNING_AUTHORIZER_ROLE"],
        ]
        cursor.execute(
            "SELECT rolname,rolsuper,rolinherit,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls "
            "FROM pg_roles WHERE rolname=ANY(%s) ORDER BY rolname", [principal_names],
        )
        roles = cursor.fetchall()
        require(len(roles) == 3 and all(row[1:] == (False, False, False, False, False, False) for row in roles),
                f"Phase 23 principal attributes are elevated: {roles}")
        for role in principal_names:
            for table in (
                "governance.model_policy", "governance.agent_definition",
                "normative.knowledge_layer_rule", "normative.requirement_control",
            ):
                cursor.execute(
                    "SELECT has_table_privilege(%s,%s,'INSERT'),"
                    "has_table_privilege(%s,%s,'UPDATE'),has_table_privilege(%s,%s,'DELETE')",
                    [role, table, role, table, role, table],
                )
                require(cursor.fetchone() == (False, False, False),
                        f"Phase 23 principal has protected-target DML: {role} {table}")
        for technical_role in (
            os.environ["FOUNDATION_WORKER_ROLE"], os.environ["FOUNDATION_PROJECTOR_ROLE"],
            os.environ["FOUNDATION_AUDIT_WRITER_ROLE"], os.environ["FOUNDATION_EXECUTOR_ROLE"],
            os.environ["FOUNDATION_LEARNING_GOVERNANCE_ROLE"],
        ):
            cursor.execute(
                "SELECT has_table_privilege(%s,'qms.learning_proposal_decision','INSERT'),"
                "has_table_privilege(%s,'qms.learning_application_authorization','INSERT')",
                [technical_role, technical_role],
            )
            require(cursor.fetchone() == (False, False),
                    f"technical principal gained approval/authorization DML: {technical_role}")
        cursor.execute(
            "SELECT relname,relrowsecurity,relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='qms' AND "
            "relname IN ('learning_proposal_review','learning_proposal_decision','learning_application_authorization')"
        )
        rls = cursor.fetchall()
        require(len(rls) == 3 and all(row[1] and row[2] for row in rls),
                "Phase 23 ENABLE+FORCE RLS missing")

    with trusted_tenant_context(identity, actor_id="phase23-event-read", trace_id=uuid4(), using="learning_governance"):
        event_types = set(DomainEvent.objects.using("learning_governance").filter(
            event_type__startswith="learning_").values_list("event_type", flat=True))
    require(event_types == {
        "learning_signal.created", "learning_proposal.created",
        "learning_proposal.reviewed", "learning_proposal.decision_recorded",
        "learning_application.authorized",
    }, f"unauthorized Phase 23 learning event exists: {event_types}")

    retained_counts = (
        LearningProposalReview.objects.using("default").count(),
        LearningProposalDecision.objects.using("default").count(),
        LearningApplicationAuthorization.objects.using("default").count(),
    )
    try:
        phase3.migrate(PHASE21)
    except Exception as exc:
        require("forward-only after retained Phase 23 governance history exists" in str(exc),
                f"retained-history reverse failed for an unexpected reason: {exc}")
        connections["default"].close()
    else:
        raise AssertionError("0019 reverse deleted retained governance history")
    require((
        LearningProposalReview.objects.using("default").count(),
        LearningProposalDecision.objects.using("default").count(),
        LearningApplicationAuthorization.objects.using("default").count(),
    ) == retained_counts, "failed reverse did not preserve all Phase 23 history")

    print(json.dumps({
        "status": "PASS", "postgresql": "18.6",
        "migration": "0018 -> 0019 -> 0018 -> 0019 PASS before Phase 23 history",
        "retained_history": "0019 reverse denied and all governance rows preserved PASS",
        "review": "immutable exact proposal/target provenance; concurrent append PASS",
        "decision": "one exact approved outcome; concurrent replay; creator self-approval denied PASS",
        "authorization": "inert exact capability; replay/conflict; VALID->STALE classification PASS",
        "rollback_matrices": "review 5/5; decision 5/5; authorization 5/5 PASS",
        "protected_targets": "byte-state identical after all governance commands PASS",
        "drift": "controlled existing curator successor; no rebind/new authorization PASS",
        "rls": {"A_none_B": visibility, "enable_force": "3/3 PASS"},
        "least_privilege": "three real separate principals; no elevated attributes/target DML PASS",
        "events": sorted(event_types), "external_effects": "ZERO",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=__import__("sys").stderr)
        raise
