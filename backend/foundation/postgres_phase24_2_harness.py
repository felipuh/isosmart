"""PostgreSQL 18.6 Phase-24.2 inert exact-delta blocking matrix."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import postgres_foundation_harness as phase3
import postgres_phase19_harness as phase19
import postgres_phase21_harness as phase21


PHASE23 = ("foundation", "0019_learning_proposal_review_application_authorization_foundation")
PHASE24_2 = ("foundation", "0020_exact_learning_delta_target_operation_contract")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def run():
    phase19.run()
    from django.db import connections
    phase3.migrate(PHASE24_2)
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.learning_proposal_canonical_delta')")
        require(cursor.fetchone()[0] == "qms.learning_proposal_canonical_delta", "0020 forward missing")
    phase3.migrate(PHASE23)
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.learning_proposal_canonical_delta')")
        require(cursor.fetchone()[0] is None, "empty-history 0020 reverse failed")
    phase3.migrate(PHASE24_2)

    from foundation.governed_learning import (
        ExactProposalFailurePoint, LearningFailurePoint, LearningProposalCommandService,
        LearningSignalCommandService,
        TrustedLearningGovernanceAuthority,
    )
    from foundation.learning_delta import (
        MODEL_POLICY_OPERATION, ModelPolicyApprovedModelRemoval,
        eligibility_classification,
    )
    from foundation.learning_proposal_governance import (
        GovernanceConflict, LearningApplicationAuthorizationCommandService,
        LearningProposalDecisionCommandService, LearningProposalReviewCommandService,
        LearningReviewFindings, TrustedLearningApplicationAuthority,
        TrustedLearningDecisionAuthority, TrustedLearningReviewAuthority,
    )
    from foundation.models import (
        DomainEvent, EffectivenessCheck, LearningApplicationAuthorization, LearningProposal,
        LearningProposalCanonicalDelta, LearningProposalDecision,
        LearningProposalReview, LearningSignal, ModelPolicy, UserProjection,
    )
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.learning_proposal_canonical_delta')")
        require(cursor.fetchone()[0] == "qms.learning_proposal_canonical_delta", "0020 delta table missing")
        cursor.execute("SELECT count(*) FROM qms.learning_proposal WHERE canonical_delta_id IS NOT NULL")
        require(cursor.fetchone()[0] == 0, "migration backfilled legacy proposals")
        cursor.execute("SELECT count(*) FROM qms.learning_proposal_review WHERE canonical_delta_id IS NOT NULL")
        require(cursor.fetchone()[0] == 0, "migration upgraded legacy reviews")
        cursor.execute("SELECT count(*) FROM qms.learning_proposal_decision WHERE canonical_delta_id IS NOT NULL")
        require(cursor.fetchone()[0] == 0, "migration upgraded legacy decisions")
        cursor.execute("SELECT count(*) FROM qms.learning_application_authorization WHERE canonical_delta_id IS NOT NULL")
        require(cursor.fetchone()[0] == 0, "migration upgraded legacy authorizations")

    protected_before = phase21.protected_snapshot(connections["default"])
    identity = TrustedTenantIdentity("phase24-2-learning", phase3.TENANT_A)
    user = UserProjection.objects.using("default").filter(tenant_id=phase3.TENANT_A).first()
    learning_authority = TrustedLearningGovernanceAuthority(
        identity, phase3.ORG_A, user.id, user.adminapps_user_id,
        frozenset({"qms.learning_signal.create", "qms.learning_proposal.create"}), True, True,
        "adminapps-learning-governance/v1", "phase24-2-exact-delta-create",
    )
    target = phase21.target_reference(connections["default"], "ModelPolicy", "governance.model_policy")
    policy = ModelPolicy.objects.using("default").get(pk=target.target_id)
    require(bool(policy.approved_models), "ModelPolicy fixture needs an approved model")
    command = ModelPolicyApprovedModelRemoval((sorted(policy.approved_models)[0],), "phase24-2-draft-v2")
    current_check = EffectivenessCheck.objects.using("default").order_by("-revision").first()
    signal_result = LearningSignalCommandService().create_signal(
        authority=learning_authority, effectiveness_check_id=current_check.id, trace_id=uuid4())
    signal = LearningSignal.objects.using("default").get(pk=signal_result.artifact_id)
    service = LearningProposalCommandService()
    legacy_result = service.create_proposal(
        authority=learning_authority, signal_ids=[signal.id], target=target,
        proposed_change_hash="c" * 64, rationale="Historical hash-only proposal.",
        expected_effect="None.", risks=["legacy inert"],
        required_governance_domains=["ai_governance"], trace_id=uuid4())
    legacy = LearningProposal.objects.using("default").get(pk=legacy_result.artifact_id)
    require(eligibility_classification(legacy) == "LEGACY_INERT", "legacy proposal became eligible")

    # The newly introduced material boundary rolls back delta and proposal together.
    for point in (ExactProposalFailurePoint.AFTER_DELTA, LearningFailurePoint.AFTER_ARTIFACT,
                  LearningFailurePoint.AFTER_LINKS, LearningFailurePoint.AFTER_EVENT,
                  LearningFailurePoint.AFTER_OUTBOX, LearningFailurePoint.AFTER_AUDIT,
                  LearningFailurePoint.BEFORE_COMMIT):
        before = (LearningProposal.objects.using("default").count(),
                  LearningProposalCanonicalDelta.objects.using("default").count())
        try:
            service.create_proposal(
                authority=learning_authority, signal_ids=[signal.id], target=target,
                delta_command=command, rationale="Exact inert delta rollback fixture.",
                expected_effect="No target effect.", risks=["review required"],
                required_governance_domains=["ai_governance"], trace_id=uuid4(),
                failure_point=point,
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError(f"exact proposal boundary committed at {point.value}")
        after = (LearningProposal.objects.using("default").count(),
                 LearningProposalCanonicalDelta.objects.using("default").count())
        require(after == before, f"proposal/delta half-pair at {point.value}")

    created = service.create_proposal(
        authority=learning_authority, signal_ids=[signal.id], target=target,
        delta_command=command, rationale="Exact approved-model removal contract only.",
        expected_effect="No target effect in Phase 24.2.", risks=["review required"],
        required_governance_domains=["ai_governance", "security"], trace_id=uuid4(),
    )
    proposal = LearningProposal.objects.using("default").get(pk=created.artifact_id)
    delta = LearningProposalCanonicalDelta.objects.using("default").get(learning_proposal_id=proposal.id)
    require(proposal.canonical_delta_id == delta.id and proposal.delta_hash == delta.delta_hash and
            proposal.proposed_change_hash == delta.delta_hash, "proposal/delta one-to-one hash binding failed")
    require(eligibility_classification(proposal) == "CANONICAL_DELTA_V1_ELIGIBLE", "new exact proposal is ineligible")

    def concurrent_exact(index):
        try:
            return LearningProposalCommandService().create_proposal(
                authority=learning_authority, signal_ids=[signal.id], target=target,
                delta_command=command, rationale=f"Concurrent exact contract {index}.",
                expected_effect="No target effect.", risks=["review required"],
                required_governance_domains=["ai_governance"], trace_id=uuid4())
        finally:
            connections["learning_governance"].close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        concurrent_results = list(pool.map(concurrent_exact, range(2)))
    concurrent_deltas = list(LearningProposalCanonicalDelta.objects.using("default").filter(
        learning_proposal_id__in=[item.artifact_id for item in concurrent_results]))
    require(len(concurrent_deltas) == 2 and len({row.delta_hash for row in concurrent_deltas}) == 1,
            "concurrent exact proposal creation was not deterministic and independently bound")

    actors = []
    with connections["default"].cursor() as cursor:
        for _ in range(3):
            projection_id, external_id = uuid4(), uuid4()
            cursor.execute(
                "INSERT INTO qms.user_projection(id,adminapps_user_id,tenant_id,source_version,source_event_id,lifecycle_status,last_synced_at) "
                "VALUES(%s,%s,%s,1,%s,'active',statement_timestamp())",
                [str(projection_id), str(external_id), str(phase3.TENANT_A), str(uuid4())],
            )
            actors.append((projection_id, external_id))
    reviewer = TrustedLearningReviewAuthority(identity, phase3.ORG_A, *actors[0],
        frozenset({"qms.learning_proposal.review"}), True, True, True, "review/v1", "phase24-2-review")
    approver = TrustedLearningDecisionAuthority(identity, phase3.ORG_A, *actors[1],
        frozenset({"qms.learning_proposal.decide"}), True, True, True, "decision/v1", "phase24-2-decision")
    authorizer = TrustedLearningApplicationAuthority(identity, phase3.ORG_A, *actors[2],
        frozenset({"qms.learning_application.authorize"}), True, True, True, "authorization/v1", "phase24-2-authorization")
    legacy_review_result = LearningProposalReviewCommandService().record_learning_proposal_review(
        authority=reviewer, proposal_id=legacy.id,
        findings=LearningReviewFindings("Legacy history review.", ("ai_governance",)), trace_id=uuid4())
    legacy_decision_result = LearningProposalDecisionCommandService().record_learning_proposal_decision(
        authority=approver, proposal_id=legacy.id, review_ids=[legacy_review_result.artifact_id],
        outcome="approved_for_application", rationale="Historical inert decision.", trace_id=uuid4())
    legacy_auth_result = LearningApplicationAuthorizationCommandService().authorize_learning_proposal_application(
        authority=authorizer, proposal_id=legacy.id, decision_id=legacy_decision_result.artifact_id,
        capability_id="revise_model_policy", idempotency_key="phase24-2-legacy", trace_id=uuid4())
    for artifact in (
        LearningProposalReview.objects.using("default").get(pk=legacy_review_result.artifact_id),
        LearningProposalDecision.objects.using("default").get(pk=legacy_decision_result.artifact_id),
        LearningApplicationAuthorization.objects.using("default").get(pk=legacy_auth_result.artifact_id),
    ):
        require(eligibility_classification(artifact) == "LEGACY_INERT",
                "legacy governance artifact became eligible")
    review_result = LearningProposalReviewCommandService().record_learning_proposal_review(
        authority=reviewer, proposal_id=proposal.id,
        findings=LearningReviewFindings("Exact delta reviewed.", ("ai_governance", "security")), trace_id=uuid4())
    decision_result = LearningProposalDecisionCommandService().record_learning_proposal_decision(
        authority=approver, proposal_id=proposal.id, review_ids=[review_result.artifact_id],
        outcome="approved_for_application", rationale="Inert eligibility only.", trace_id=uuid4())
    try:
        LearningApplicationAuthorizationCommandService().authorize_learning_proposal_application(
            authority=authorizer, proposal_id=proposal.id, decision_id=decision_result.artifact_id,
            capability_id="revise_model_policy", idempotency_key="phase24-2-old-capability", trace_id=uuid4())
    except PermissionError:
        pass
    else:
        raise AssertionError("old revise_* capability authorized an exact delta")
    auth_result = LearningApplicationAuthorizationCommandService().authorize_learning_proposal_application(
        authority=authorizer, proposal_id=proposal.id, decision_id=decision_result.artifact_id,
        capability_id=MODEL_POLICY_OPERATION, idempotency_key="phase24-2-exact-capability", trace_id=uuid4())
    auth_replay = LearningApplicationAuthorizationCommandService().authorize_learning_proposal_application(
        authority=authorizer, proposal_id=proposal.id, decision_id=decision_result.artifact_id,
        capability_id=MODEL_POLICY_OPERATION, idempotency_key="phase24-2-exact-capability", trace_id=uuid4())
    require(auth_replay.replayed and auth_replay.artifact_id == auth_result.artifact_id,
            "exact authorization replay was not idempotent")
    review = LearningProposalReview.objects.using("default").get(pk=review_result.artifact_id)
    decision = LearningProposalDecision.objects.using("default").get(pk=decision_result.artifact_id)
    authorization = LearningApplicationAuthorization.objects.using("default").get(pk=auth_result.artifact_id)
    tuples = {(row.canonical_delta_id, row.delta_hash, row.operation_id, row.operation_version)
              for row in (proposal, review, decision, authorization)}
    require(len(tuples) == 1, "end-to-end governance delta tuple differs")

    # Raw mutation/rebinding and least privilege remain denied.
    with connections["default"].cursor() as cursor:
        for role in (os.environ["FOUNDATION_LEARNING_GOVERNANCE_ROLE"],
                     os.environ["FOUNDATION_LEARNING_REVIEWER_ROLE"],
                     os.environ["FOUNDATION_LEARNING_APPROVER_ROLE"],
                     os.environ["FOUNDATION_LEARNING_AUTHORIZER_ROLE"]):
            for table in ("governance.model_policy", "governance.agent_definition", "normative.knowledge_layer_rule"):
                cursor.execute("SELECT has_table_privilege(%s,%s,'INSERT,UPDATE,DELETE')", [role, table])
                require(not cursor.fetchone()[0], f"Phase 24.2 role gained target DML: {role} {table}")
        cursor.execute("SELECT relrowsecurity,relforcerowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='qms' AND c.relname='learning_proposal_canonical_delta'")
        require(cursor.fetchone() == (True, True), "canonical delta lacks ENABLE+FORCE RLS")
    try:
        with trusted_tenant_context(identity, actor_id=user.adminapps_user_id, trace_id=uuid4(), using="learning_governance"):
            LearningProposalCanonicalDelta.objects.using("learning_governance").filter(pk=delta.id).update(delta_hash="f" * 64)
    except Exception:
        connections["learning_governance"].close()
    else:
        raise AssertionError("canonical delta UPDATE succeeded")

    require(phase21.protected_snapshot(connections["default"]) == protected_before,
            "Phase 24.2 changed protected target byte-state")
    with trusted_tenant_context(identity, actor_id="phase24-2-event-read", trace_id=uuid4(), using="learning_governance"):
        events = set(DomainEvent.objects.using("learning_governance").filter(event_type__startswith="learning_").values_list("event_type", flat=True))
    require(events <= {"learning_signal.created", "learning_proposal.created", "learning_proposal.reviewed",
                       "learning_proposal.decision_recorded", "learning_application.authorized"},
            f"application event was introduced: {events}")

    print(json.dumps({
        "status": "PASS", "postgresql": "18.6", "migration": "0020 additive PASS",
        "canonical_delta": "atomic one-to-one immutable exact bytes/hash PASS",
        "governance_binding": "proposal/review/decision/authorization identical tuple PASS",
        "legacy": "proposal/review/decision/authorization LEGACY_INERT; no backfill PASS",
        "rollback": "7/7 exact proposal/delta boundaries PASS",
        "rls": "ENABLE+FORCE; least privilege; no target DML PASS",
        "protected_targets": "byte-state invariant; zero successor PASS",
        "events": sorted(events), "external_effects": "ZERO",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    run()
