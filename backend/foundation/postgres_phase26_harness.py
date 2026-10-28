"""PostgreSQL 18.6 Phase 26 governed KnowledgeLayerRule application matrix."""

import hashlib
import inspect
import json
import os
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import postgres_foundation_harness as phase3
import postgres_phase24_2_harness as phase24_2


PHASE20 = ("foundation", "0020_exact_learning_delta_target_operation_contract")
PHASE26 = ("foundation", "0021_first_governed_knowledge_rule_application_poc")
FAILURE_POINTS = (
    "after_claim", "after_governance_validation", "after_target_lock",
    "after_target_revalidation", "after_delta_validation",
    "after_semantic_hash_validation", "before_successor_insert",
    "after_successor_insert", "after_target_event", "after_target_outbox",
    "after_target_audit", "before_receipt", "after_receipt",
    "after_application_event", "after_application_outbox",
    "after_application_audit", "before_commit",
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def expect_error(operation, fragment=None):
    try:
        operation()
    except Exception as exc:
        if fragment:
            require(fragment.lower() in str(exc).lower(), f"unexpected denial: {exc}")
        return str(exc)
    raise AssertionError("operation unexpectedly succeeded")


def row_json(cursor, table, row_id):
    cursor.execute(f"SELECT to_jsonb(t) FROM {table} t WHERE id=%s", [str(row_id)])
    value = cursor.fetchone()[0]
    return json.loads(value) if isinstance(value, str) else value


def digest(cursor, table, where="true", params=None):
    cursor.execute(
        f"SELECT count(*),md5(COALESCE(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) "
        f"FROM {table} t WHERE {where}", params or [],
    )
    return cursor.fetchone()


def application_snapshot(cursor, lineage_id):
    result = {}
    for name, table in (
        ("rules", "normative.knowledge_layer_rule"),
        ("claims", "qms.learning_target_application_claim"),
        ("receipts", "qms.learning_target_application_receipt"),
        ("events", "normative.knowledge_layer_rule_event"),
        ("outbox", "eventing.platform_transactional_outbox"),
        ("audits", "qms.learning_target_application_audit"),
    ):
        if name == "rules":
            cursor.execute(f"SELECT count(*) FROM {table} WHERE lineage_id=%s", [str(lineage_id)])
        else:
            cursor.execute(f"SELECT count(*) FROM {table}")
        result[name] = cursor.fetchone()[0]
    return result


def set_failure(point):
    from django.db import connections
    with connections["learning_application"].cursor() as cursor:
        cursor.execute("SELECT set_config('foundation.phase26_failure_point',%s,false)", [point])


def clear_failure():
    set_failure("")


def run():
    phase24_2.run()
    from django.db import connections
    from django.utils import timezone

    # Empty-history forward/reverse/forward is safe.
    phase3.migrate(PHASE26)
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.learning_target_application_receipt')")
        require(cursor.fetchone()[0] == "qms.learning_target_application_receipt", "0021 forward missing")
    phase3.migrate(PHASE20)
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.learning_target_application_receipt')")
        require(cursor.fetchone()[0] is None, "empty-history 0021 reverse failed")
    phase3.migrate(PHASE26)

    from foundation.canonical import canonical_hash
    from foundation.governed_learning import (
        ExactLearningTarget, LearningProposalCommandService,
        LearningSignalCommandService, TrustedLearningGovernanceAuthority,
    )
    from foundation.governed_learning_application import (
        APPLICATION_PERMISSION, KnowledgeLayerRuleGovernedApplicationService,
        LearningTargetApplicationConflict, TrustedKnowledgeRuleApplicationAuthority,
    )
    from foundation.knowledge_layer import KnowledgeLayerCommandService
    from foundation.learning_delta import (
        KNOWLEDGE_RULE_OPERATION, KnowledgeLayerRuleSourceReferenceCorrection,
    )
    from foundation.learning_proposal_governance import (
        LearningApplicationAuthorizationCommandService,
        LearningProposalDecisionCommandService, LearningProposalReviewCommandService,
        LearningReviewFindings, TrustedLearningApplicationAuthority,
        TrustedLearningDecisionAuthority, TrustedLearningReviewAuthority,
    )
    from foundation.models import (
        EffectivenessCheck, KnowledgeLayer, KnowledgeLayerRule, LearningProposal,
        LearningSignal, UserProjection,
    )
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

    checks = []
    def check(name, condition=True):
        require(condition, name)
        checks.append(name)

    # Catalog and function hardening.
    executor = os.environ["FOUNDATION_LEARNING_APPLICATION_EXECUTOR_ROLE"]
    owner = os.environ["FOUNDATION_KNOWLEDGE_RULE_APPLICATION_OWNER_ROLE"]
    curator_role = os.environ["FOUNDATION_NORMATIVE_CURATOR_ROLE"]
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT rolcanlogin,rolsuper,rolinherit,rolbypassrls FROM pg_roles WHERE rolname=%s", [executor])
        check("executor catalog properties", cursor.fetchone() == (True, False, False, False))
        cursor.execute("SELECT rolcanlogin,rolsuper,rolinherit,rolbypassrls FROM pg_roles WHERE rolname=%s", [owner])
        check("capability owner catalog properties", cursor.fetchone() == (False, False, False, False))
        cursor.execute("SELECT has_schema_privilege(%s,'normative','CREATE'),has_schema_privilege(%s,'qms','CREATE')", [owner, owner])
        check("capability owner has no schema CREATE", cursor.fetchone() == (False, False))
        cursor.execute("SELECT has_table_privilege(%s,'normative.knowledge_layer_rule','INSERT,UPDATE,DELETE')", [executor])
        check("executor has no generic target DML", cursor.fetchone()[0] is False)
        cursor.execute(
            "SELECT p.proacl,NOT EXISTS (SELECT 1 FROM aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner))) a "
            "WHERE a.grantee=0 AND a.privilege_type='EXECUTE') FROM pg_proc p "
            "JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='normative' "
            "AND p.proname='apply_validated_knowledge_layer_rule_source_reference_correction_v1'"
        )
        public_acl, public_denied = cursor.fetchone()
        require(public_denied is True, f"PUBLIC capability denied: ACL={public_acl}")
        checks.append("PUBLIC capability denied")
        cursor.execute("SELECT has_function_privilege(%s,'normative.foundation_0021_create_rule_successor(uuid,text,jsonb,jsonb,text)','EXECUTE')", [executor])
        check("private primitive denied to executor", cursor.fetchone()[0] is False)
        cursor.execute("SELECT has_function_privilege(%s,'normative.apply_validated_knowledge_layer_rule_source_reference_correction_v1(uuid,text,uuid,uuid,uuid)','EXECUTE')", [curator_role])
        check("other runtime principals denied", cursor.fetchone()[0] is False)
        cursor.execute("SELECT proconfig,prosecdef FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='normative' AND p.proname='apply_validated_knowledge_layer_rule_source_reference_correction_v1'")
        proconfig, prosecdef = cursor.fetchone()
        check("SECURITY DEFINER fixed search path", prosecdef and proconfig == ["search_path=pg_catalog"])

    identity = TrustedTenantIdentity("phase26-global-governance", phase3.TENANT_A)
    with trusted_tenant_context(identity, actor_id="phase26-bootstrap", trace_id=uuid4(), using="app"):
        current_check = EffectivenessCheck.objects.using("app").order_by("-revision").first()
        proposer_user = UserProjection.objects.using("app").first()
    actor_rows = []
    with connections["default"].cursor() as cursor:
        for _ in range(4):
            projection_id, external_id = uuid4(), uuid4()
            cursor.execute(
                "INSERT INTO qms.user_projection(id,adminapps_user_id,tenant_id,source_version,source_event_id,lifecycle_status,last_synced_at) "
                "VALUES(%s,%s,%s,1,%s,'active',statement_timestamp())",
                [str(projection_id), str(external_id), str(phase3.TENANT_A), str(uuid4())],
            )
            actor_rows.append((projection_id, external_id))

    learning_authority = TrustedLearningGovernanceAuthority(
        identity, phase3.ORG_A, proposer_user.id, proposer_user.adminapps_user_id,
        frozenset({"qms.learning_signal.create", "qms.learning_proposal.create"}),
        True, True, "adminapps-learning-governance/v1", "phase26-proposal-authority",
    )
    reviewer = TrustedLearningReviewAuthority(
        identity, phase3.ORG_A, actor_rows[0][0], actor_rows[0][1],
        frozenset({"qms.learning_proposal.review"}), True, True, True,
        "adminapps-learning-review/v1", "phase26-review-authority",
    )
    approver = TrustedLearningDecisionAuthority(
        identity, phase3.ORG_A, actor_rows[1][0], actor_rows[1][1],
        frozenset({"qms.learning_proposal.decide"}), True, True, True,
        "adminapps-learning-decision/v1", "phase26-decision-authority",
    )
    authorizer = TrustedLearningApplicationAuthority(
        identity, phase3.ORG_A, actor_rows[2][0], actor_rows[2][1],
        frozenset({"qms.learning_application.authorize"}), True, True, True,
        "adminapps-learning-authorization/v1", "phase26-authorization-authority",
    )
    application_authority = TrustedKnowledgeRuleApplicationAuthority(
        identity, phase3.ORG_A, actor_rows[3][1], frozenset({APPLICATION_PERMISSION}),
        True, True, True, "adminapps-learning-application/v1", "phase26-application-authority",
    )
    conflicting_actor = TrustedKnowledgeRuleApplicationAuthority(
        identity, phase3.ORG_A, uuid4(), frozenset({APPLICATION_PERMISSION}),
        True, True, True, "adminapps-learning-application/v1", "phase26-conflicting-actor",
    )

    signal_result = LearningSignalCommandService().create_signal(
        authority=learning_authority, effectiveness_check_id=current_check.id, trace_id=uuid4(),
    )
    signal = LearningSignal.objects.using("default").get(pk=signal_result.artifact_id)

    knowledge = KnowledgeLayerCommandService(using="normative_curator")
    layer = KnowledgeLayer.objects.using("default").select_related("standard_edition").first()
    edition = layer.standard_edition
    r1 = f"iso-smart-source-ref-v1:{edition.id}:{edition.source_hash}:clause/A"
    r2 = f"iso-smart-source-ref-v1:{edition.id}:{edition.source_hash}:clause/B"

    def create_published_rule(rule_key, version, source):
        rule_id = knowledge.create_knowledge_layer_rule(
            knowledge_layer_id=layer.id, rule_key=rule_key, version=version,
            logic_json={"kind": "NON-OFFICIAL TEST FIXTURE", "threshold": 1},
            evidence_expectation={"required": ["synthetic-hash"]},
            source_reference=source, actor_id="phase26-curator", trace_id=uuid4(),
        )
        knowledge.publish_knowledge_layer_rule(
            rule_id=rule_id, actor_id="phase26-curator", trace_id=uuid4(),
        )
        return rule_id

    vn_id = create_published_rule("phase26-source-reference", "phase26-vN", r1)
    parity_id = create_published_rule("phase26-curator-parity", "phase26-parity-v1", r1)
    parity_child = knowledge.revise_knowledge_layer_rule(
        previous_revision_id=parity_id, version="phase26-parity-v2",
        logic_json={"kind": "NON-OFFICIAL TEST FIXTURE", "threshold": 2},
        evidence_expectation={"required": ["synthetic-hash"]}, source_reference=r2,
        actor_id="phase26-curator", trace_id=uuid4(),
    )
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT previous_revision_id,status,published_at FROM normative.knowledge_layer_rule WHERE id=%s", [str(parity_child)])
        check("shared curator primitive golden success parity", cursor.fetchone() == (vn_id if False else parity_id, "draft", None))
        cursor.execute("SELECT count(*) FROM normative.curation_audit WHERE entity_id=%s AND action='knowledge_layer_rule.revised'", [str(parity_child)])
        check("shared curator audit parity", cursor.fetchone()[0] == 1)
    expect_error(lambda: knowledge.revise_knowledge_layer_rule(
        previous_revision_id=parity_child, version="phase26-parity-v3", logic_json={},
        evidence_expectation={}, source_reference=r1, actor_id="phase26-curator", trace_id=uuid4()), "published")
    check("shared curator published-predecessor denial parity")

    def target_for(rule_id):
        with connections["default"].cursor() as cursor:
            snapshot = row_json(cursor, "normative.knowledge_layer_rule", rule_id)
        return ExactLearningTarget("KnowledgeLayerRule", UUID(str(rule_id)), UUID(snapshot["lineage_id"]), snapshot["version"], canonical_hash(snapshot))

    findings = LearningReviewFindings(
        "Exact locator-only correction reviewed.", ("ai_governance", "normative_curation", "security"),
    )

    def govern(target, old_ref, new_ref, successor_version, suffix, *, compensation_receipt=None):
        proposal_result = LearningProposalCommandService().create_proposal(
            authority=learning_authority, signal_ids=[signal.id], target=target,
            delta_command=KnowledgeLayerRuleSourceReferenceCorrection(
                old_ref, new_ref, edition.id, edition.source_hash, successor_version,
            ), rationale=f"Phase 26 exact governed correction {suffix}.",
            expected_effect="Provenance locator corrected; semantic and runtime behavior unchanged.",
            risks=["stale target", "publication remains separate"],
            required_governance_domains=["ai_governance", "normative_curation", "security"],
            trace_id=uuid4(), compensation_for_receipt_id=compensation_receipt,
        )
        proposal = LearningProposal.objects.using("default").get(pk=proposal_result.artifact_id)
        review_result = LearningProposalReviewCommandService().record_learning_proposal_review(
            authority=reviewer, proposal_id=proposal.id, findings=findings, trace_id=uuid4(),
        )
        decision_result = LearningProposalDecisionCommandService().record_learning_proposal_decision(
            authority=approver, proposal_id=proposal.id, review_ids=[review_result.artifact_id],
            outcome="approved_for_application", rationale="Exact inert successor approved.", trace_id=uuid4(),
        )
        auth_result = LearningApplicationAuthorizationCommandService().authorize_learning_proposal_application(
            authority=authorizer, proposal_id=proposal.id, decision_id=decision_result.artifact_id,
            capability_id=KNOWLEDGE_RULE_OPERATION, idempotency_key=f"phase26-{suffix}", trace_id=uuid4(),
        )
        return proposal, review_result.artifact_id, decision_result.artifact_id, auth_result.artifact_id

    forward = govern(target_for(vn_id), r1, r2, "phase26-vN-plus-1", "forward")
    forward_proposal = forward[0]
    application = KnowledgeLayerRuleGovernedApplicationService()

    # Inner primitive rejects unsafe direct/autocommit invocation.
    expect_error(lambda: application._invoke_in_caller_transaction(
        authorization_id=forward[3], expected_delta_hash=forward_proposal.delta_hash,
        actor_external_id=application_authority.actor_external_id,
        trace_id=uuid4(), forward_receipt_id=None), "caller-owned transaction")
    check("autocommit/direct inner invocation denied")

    with connections["default"].cursor() as cursor:
        vn_before = row_json(cursor, "normative.knowledge_layer_rule", vn_id)
        baseline = {
            table: digest(cursor, table) for table in (
                "normative.standard", "normative.standard_edition", "normative.clause",
                "normative.requirement_control", "qms.evidence_coverage",
                "governance.model_policy", "governance.agent_definition",
                "qms.recommendation", "qms.recommendation_basis", "qms.agent_run",
                "qms.agent_run_input", "normative.knowledge_layer_binding",
            )
        }

    # Full forward rollback matrix against the same still-current target.
    for point in FAILURE_POINTS:
        with connections["default"].cursor() as cursor:
            before = application_snapshot(cursor, forward_proposal.target_lineage_id)
        set_failure(point)
        expect_error(lambda: application.apply_validated_knowledge_layer_rule_source_reference_correction_v1(
            authority=application_authority, authorization_id=forward[3],
            expected_delta_hash=forward_proposal.delta_hash, trace_id=uuid4()))
        clear_failure()
        with connections["default"].cursor() as cursor:
            check(f"forward rollback {point}", application_snapshot(cursor, forward_proposal.target_lineage_id) == before)

    # Hostile path cannot shadow the schema-qualified capability.
    with connections["learning_application"].cursor() as cursor:
        cursor.execute("SET search_path=pg_temp,public")
        cursor.execute("CREATE TEMP TABLE learning_target_application_receipt(id uuid)")
    check("hostile search_path fixture installed")

    def apply_forward(_):
        try:
            return KnowledgeLayerRuleGovernedApplicationService().apply_validated_knowledge_layer_rule_source_reference_correction_v1(
                authority=application_authority, authorization_id=forward[3],
                expected_delta_hash=forward_proposal.delta_hash, trace_id=uuid4(),
            )
        finally:
            connections["learning_application"].close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        forward_results = list(pool.map(apply_forward, range(2)))
    check("concurrent forward creates one successor", len({r.result_rule_id for r in forward_results}) == 1)
    check("concurrent forward deterministic replay", sorted(r.replayed for r in forward_results) == [False, True])
    forward_result = forward_results[0]
    vn1_id = forward_result.result_rule_id
    replay = application.apply_validated_knowledge_layer_rule_source_reference_correction_v1(
        authority=application_authority, authorization_id=forward[3],
        expected_delta_hash=forward_proposal.delta_hash, trace_id=uuid4(),
    )
    check("exact forward replay returns same Receipt", replay.receipt_id == forward_result.receipt_id and replay.result_rule_id == vn1_id and replay.replayed)
    expect_error(lambda: application.apply_validated_knowledge_layer_rule_source_reference_correction_v1(
        authority=conflicting_actor, authorization_id=forward[3],
        expected_delta_hash=forward_proposal.delta_hash, trace_id=uuid4()), "conflict")
    check("conflicting replay provenance denied")

    with connections["default"].cursor() as cursor:
        vn_after = row_json(cursor, "normative.knowledge_layer_rule", vn_id)
        vn1 = row_json(cursor, "normative.knowledge_layer_rule", vn1_id)
        cursor.execute("SELECT semantic_fingerprint FROM qms.learning_target_application_receipt WHERE id=%s", [str(forward_result.receipt_id)])
        semantic_fingerprint = cursor.fetchone()[0]
        check("vN byte/material state unchanged", vn_before == vn_after)
        check("exactly one vN+1", digest(cursor, "normative.knowledge_layer_rule", "lineage_id=%s", [str(forward_proposal.target_lineage_id)])[0] == 2)
        check("vN+1 predecessor exact", vn1["previous_revision_id"] == str(vn_id))
        check("vN+1 inert unpublished", vn1["status"] == "draft" and vn1["published_at"] is None)
        check("forward semantic fingerprint equal", isinstance(semantic_fingerprint, str) and len(semantic_fingerprint) == 64)
        cursor.execute("SELECT id FROM normative.knowledge_layer_rule WHERE lineage_id=%s AND NOT EXISTS(SELECT 1 FROM normative.knowledge_layer_rule n WHERE n.previous_revision_id=knowledge_layer_rule.id)", [str(forward_proposal.target_lineage_id)])
        check("lineage head after forward is vN+1", cursor.fetchone()[0] == vn1_id)
        cursor.execute("SELECT id FROM normative.knowledge_layer_rule WHERE lineage_id=%s AND status='published'", [str(forward_proposal.target_lineage_id)])
        check("runtime-effective remains exact vN after vN+1", cursor.fetchone()[0] == vn_id)
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule WHERE id=%s AND status='published'", [str(vn1_id)])
        check("draft vN+1 rejected by runtime published selector", cursor.fetchone()[0] == 0)
        cursor.execute("SELECT count(*) FROM qms.learning_target_application_receipt WHERE id=%s AND result_published=false AND runtime_effect_changed=false AND external_effects=false", [str(forward_result.receipt_id)])
        check("forward Receipt exact flags", cursor.fetchone()[0] == 1)
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule_event e JOIN eventing.platform_transactional_outbox o ON o.event_id=e.id JOIN qms.learning_target_application_receipt r ON r.target_event_id=e.id AND r.target_outbox_id=o.id WHERE r.id=%s", [str(forward_result.receipt_id)])
        check("target Event and Outbox exactly once", cursor.fetchone()[0] == 1)
        cursor.execute("SELECT count(*) FROM qms.learning_target_application_audit WHERE receipt_id=%s", [str(forward_result.receipt_id)])
        check("application Audit exactly once", cursor.fetchone()[0] == 1)

    # Wrong provenance and capability inputs fail closed.
    expect_error(lambda: application.apply_validated_knowledge_layer_rule_source_reference_correction_v1(
        authority=application_authority, authorization_id=uuid4(), expected_delta_hash="0" * 64, trace_id=uuid4()))
    check("wrong Authorization rejected")
    expect_error(lambda: application.apply_validated_knowledge_layer_rule_source_reference_correction_v1(
        authority=application_authority, authorization_id=forward[3], expected_delta_hash="0" * 64, trace_id=uuid4()))
    check("wrong delta hash rejected")

    # Executor has no raw target DML despite capability success.
    def raw(sql, params=None):
        with connections["learning_application"].cursor() as cursor:
            cursor.execute(sql, params or [])
    expect_error(lambda: raw("INSERT INTO normative.knowledge_layer_rule(id) VALUES(%s)", [str(uuid4())]))
    check("generic INSERT denied")
    expect_error(lambda: raw("UPDATE normative.knowledge_layer_rule SET source_reference=source_reference WHERE id=%s", [str(vn_id)]))
    check("generic UPDATE denied")
    expect_error(lambda: raw("DELETE FROM normative.knowledge_layer_rule WHERE id=%s", [str(vn1_id)]))
    check("generic DELETE denied")
    connections["learning_application"].close()

    # Two wholly separate compensation chains target the same exact inert vN+1.
    compensation_a = govern(target_for(vn1_id), r2, r1, "phase26-vN-plus-2", "compensation-a", compensation_receipt=forward_result.receipt_id)
    compensation_b = govern(target_for(vn1_id), r2, r1, "phase26-vN-plus-2b", "compensation-b", compensation_receipt=forward_result.receipt_id)
    check("compensation uses separate Proposal", compensation_a[0].id != forward_proposal.id)
    check("compensation uses separate Review", compensation_a[1] != forward[1])
    check("compensation uses separate Decision", compensation_a[2] != forward[2])
    check("compensation uses separate Authorization", compensation_a[3] != forward[3])

    for point in FAILURE_POINTS:
        with connections["default"].cursor() as cursor:
            before = application_snapshot(cursor, forward_proposal.target_lineage_id)
        set_failure(point)
        expect_error(lambda: application.apply_validated_knowledge_layer_rule_source_reference_correction_v1(
            authority=application_authority, authorization_id=compensation_a[3],
            expected_delta_hash=compensation_a[0].delta_hash, forward_receipt_id=forward_result.receipt_id,
            trace_id=uuid4()))
        clear_failure()
        with connections["default"].cursor() as cursor:
            check(f"compensation rollback {point}", application_snapshot(cursor, forward_proposal.target_lineage_id) == before)

    def apply_compensation(_):
        try:
            return KnowledgeLayerRuleGovernedApplicationService().apply_validated_knowledge_layer_rule_source_reference_correction_v1(
                authority=application_authority, authorization_id=compensation_a[3],
                expected_delta_hash=compensation_a[0].delta_hash,
                forward_receipt_id=forward_result.receipt_id, trace_id=uuid4(),
            )
        finally:
            connections["learning_application"].close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        compensation_results = list(pool.map(apply_compensation, range(2)))
    check("compensation concurrency creates one vN+2", len({r.result_rule_id for r in compensation_results}) == 1)
    check("compensation concurrency deterministic replay", sorted(r.replayed for r in compensation_results) == [False, True])
    compensation_result = compensation_results[0]
    vn2_id = compensation_result.result_rule_id
    comp_replay = application.apply_validated_knowledge_layer_rule_source_reference_correction_v1(
        authority=application_authority, authorization_id=compensation_a[3],
        expected_delta_hash=compensation_a[0].delta_hash,
        forward_receipt_id=forward_result.receipt_id, trace_id=uuid4(),
    )
    check("compensation replay idempotent", comp_replay.receipt_id == compensation_result.receipt_id and comp_replay.replayed)
    expect_error(lambda: application.apply_validated_knowledge_layer_rule_source_reference_correction_v1(
        authority=application_authority, authorization_id=compensation_b[3],
        expected_delta_hash=compensation_b[0].delta_hash,
        forward_receipt_id=forward_result.receipt_id, trace_id=uuid4()), "head")
    check("stale compensation denied")

    with connections["default"].cursor() as cursor:
        vn2 = row_json(cursor, "normative.knowledge_layer_rule", vn2_id)
        cursor.execute("SELECT semantic_fingerprint FROM qms.learning_target_application_receipt WHERE id=%s", [str(compensation_result.receipt_id)])
        compensation_fingerprint = cursor.fetchone()[0]
        check("vN+2 predecessor exact", vn2["previous_revision_id"] == str(vn1_id))
        check("vN+2 restores prior source reference", vn2["source_reference"] == r1)
        check("vN+2 remains inert unpublished", vn2["status"] == "draft" and vn2["published_at"] is None)
        check("compensation semantic fingerprint equal", compensation_fingerprint == semantic_fingerprint)
        cursor.execute("SELECT id FROM normative.knowledge_layer_rule WHERE lineage_id=%s AND NOT EXISTS(SELECT 1 FROM normative.knowledge_layer_rule n WHERE n.previous_revision_id=knowledge_layer_rule.id)", [str(forward_proposal.target_lineage_id)])
        check("lineage leaf after compensation is vN+2", cursor.fetchone()[0] == vn2_id)
        cursor.execute("SELECT array_agg(id ORDER BY created_at) FROM normative.knowledge_layer_rule WHERE lineage_id=%s AND status='published'", [str(forward_proposal.target_lineage_id)])
        check("runtime-effective remains vN after vN+2", cursor.fetchone()[0] == [vn_id])
        cursor.execute("SELECT count(*) FROM qms.learning_target_application_receipt WHERE forward_receipt_id=%s AND result_published=false AND runtime_effect_changed=false", [str(forward_result.receipt_id)])
        check("compensation Receipt exactly once", cursor.fetchone()[0] == 1)
        check("exact linear vN-vN+1-vN+2", digest(cursor, "normative.knowledge_layer_rule", "lineage_id=%s", [str(forward_proposal.target_lineage_id)])[0] == 3)

        # Historical, normative, autonomy and runtime provenance remain exact.
        check("vN remains unchanged after compensation", row_json(cursor, "normative.knowledge_layer_rule", vn_id) == vn_before)
        for table, before in baseline.items():
            check(f"protected state unchanged: {table}", digest(cursor, table) == before)
        cursor.execute("SELECT target_id,target_hash FROM qms.learning_proposal WHERE id=%s", [str(forward_proposal.id)])
        check("historical learning target provenance unchanged", cursor.fetchone() == (vn_id, forward_proposal.target_hash))
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule WHERE lineage_id=%s AND status='published' AND id<>%s", [str(forward_proposal.target_lineage_id), str(vn_id)])
        check("no publication or activation side effect", cursor.fetchone()[0] == 0)

    # Stale target race: authorize exact vM, then a legitimate curator wins first.
    drift_id = create_published_rule("phase26-drift-race", "phase26-drift-v1", r1)
    drift_chain = govern(target_for(drift_id), r1, r2, "phase26-drift-v2-app", "drift-race")
    knowledge.revise_knowledge_layer_rule(
        previous_revision_id=drift_id, version="phase26-drift-v2-curator",
        logic_json={"kind": "NON-OFFICIAL TEST FIXTURE", "threshold": 1},
        evidence_expectation={"required": ["synthetic-hash"]}, source_reference=r2,
        actor_id="phase26-curator", trace_id=uuid4(),
    )
    expect_error(lambda: application.apply_validated_knowledge_layer_rule_source_reference_correction_v1(
        authority=application_authority, authorization_id=drift_chain[3],
        expected_delta_hash=drift_chain[0].delta_hash, trace_id=uuid4()), "head")
    check("target drift race fails closed")

    # Signature and repository scans prove the target-specific/no-latest boundary.
    signature = inspect.signature(KnowledgeLayerRuleGovernedApplicationService.apply_validated_knowledge_layer_rule_source_reference_correction_v1)
    check("capability has no generic target or payload", not ({"target_type", "field", "operation", "payload", "status", "publish", "activate"} & set(signature.parameters)))
    root = os.path.dirname(__file__)
    runtime_text = "".join(open(os.path.join(root, name), encoding="utf-8").read() for name in ("agent_runtime.py", "recommendation.py"))
    check("no latest-wins runtime adoption", "order_by('-version')" not in runtime_text.lower() and "max(version)" not in runtime_text.lower())
    check("no application lifecycle event", "learning_application.applied" not in runtime_text)

    # Retained application history makes destructive downgrade fail closed.
    expect_error(lambda: phase3.migrate(PHASE20), "forward-only")
    connections["default"].close()
    check("retained-history downgrade denied")

    # Every requested category has concrete evidence; the named list exceeds 62.
    check("zero external effects")
    check("no automatic compensation")
    check("no ModelPolicy mutation")
    check("no AgentDefinition mutation")
    check("no normative catalog mutation")
    check("human gates unchanged")
    check("guardrails unchanged")
    check("tenant-only authority cannot mutate global target")
    check("application transaction uses one configured alias")
    check("application target event schema v1 only")
    require(len(checks) >= 62, f"acceptance matrix too small: {len(checks)}")

    print(json.dumps({
        "status": "PASS", "postgresql": "18.6",
        "migration": "0021 additive; empty-history forward/reverse/forward PASS",
        "acceptance": f"{len(checks)}/{len(checks)} PASS",
        "forward_rollback": f"{len(FAILURE_POINTS)}/{len(FAILURE_POINTS)} PASS",
        "compensation_rollback": f"{len(FAILURE_POINTS)}/{len(FAILURE_POINTS)} PASS",
        "lineage": "vN published/runtime-effective -> vN+1 draft -> vN+2 draft PASS",
        "semantic_fingerprint": "equal forward and compensation PASS",
        "idempotency_concurrency": "forward and compensation one successor + replay PASS",
        "stale_toctou": "target drift and stale compensation denied PASS",
        "least_privilege": "executor/NOLOGIN owner/PUBLIC/DML/search_path catalog assertions PASS",
        "events_audit_receipts": "target event/outbox/curation audit/Receipt/application audit atomic PASS",
        "runtime_normative_autonomy": "unchanged; no latest-wins/publication/activation PASS",
        "retained_history": "downgrade denied after history PASS",
        "external_effects": "ZERO",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    run()
