"""PostgreSQL 18.6 Phase 28.3 retained synthetic candidate creation gate."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
from uuid import UUID, NAMESPACE_URL, uuid4, uuid5

import postgres_foundation_harness as phase3
import postgres_phase19_harness as phase19


PHASE283 = ("foundation", "0023_retained_synthetic_source_reference_application")
ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "docs/governance/fixtures/SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_SOURCE_MANIFEST_V1.json"
EVIDENCE_PATH = ROOT / "docs/governance/evidence/PHASE28_3_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_CREATED_AND_RETAINED_V1.json"
NAMESPACE = uuid5(NAMESPACE_URL, "https://iso-smart.local/phase28.3/new-deterministic-synthetic-publication-poc-lineage/v1")
FAILURE_POINTS = (
    "after_claim", "after_governance_validation", "after_target_lock", "after_target_revalidation",
    "after_delta_validation", "after_semantic_hash_validation", "before_successor_insert",
    "after_successor_insert", "after_target_event", "after_target_outbox", "after_target_audit",
    "before_receipt", "after_receipt", "after_application_event", "after_application_outbox",
    "after_application_audit", "before_commit",
)


def uid(name):
    return uuid5(NAMESPACE, name)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def row_json(cursor, table, row_id):
    cursor.execute(f"SELECT to_jsonb(t) FROM {table} t WHERE id=%s", [str(row_id)])
    row = cursor.fetchone()
    require(row is not None, f"missing live row {table}/{row_id}")
    return json.loads(row[0]) if isinstance(row[0], str) else row[0]


def table_digest(cursor, table, where="true", params=None):
    cursor.execute(
        f"SELECT count(*),md5(COALESCE(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) FROM {table} t WHERE {where}",
        params or [],
    )
    return cursor.fetchone()


def material_reference(material_hash, material, **binding):
    result = {"id": str(material["id"]), "material_hash": material_hash(material), "material": material}
    result.update(binding)
    return result


def application_snapshot(cursor, lineage_id):
    cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule WHERE lineage_id=%s", [str(lineage_id)])
    rules = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM qms.learning_target_application_receipt WHERE target_lineage_id=%s", [str(lineage_id)])
    receipts = cursor.fetchone()[0]
    cursor.execute(
        "SELECT count(*) FROM normative.knowledge_layer_rule_event e "
        "JOIN normative.knowledge_layer_rule r ON r.id=e.aggregate_id WHERE r.lineage_id=%s", [str(lineage_id)],
    )
    events = cursor.fetchone()[0]
    return rules, receipts, events


def run():
    phase19.run()
    from django.db import connections
    from foundation.canonical import canonical_hash
    from foundation.governed_learning import (
        ExactLearningTarget, LearningProposalCommandService, LearningSignalCommandService,
        TrustedLearningGovernanceAuthority,
    )
    from foundation.governed_learning_application import (
        APPLICATION_PERMISSION, KnowledgeLayerRuleGovernedApplicationService,
        TrustedKnowledgeRuleApplicationAuthority,
    )
    from foundation.learning_delta import KNOWLEDGE_RULE_OPERATION, KnowledgeLayerRuleSourceReferenceCorrection
    from foundation.learning_proposal_governance import (
        LearningApplicationAuthorizationCommandService, LearningProposalDecisionCommandService,
        LearningProposalReviewCommandService, LearningReviewFindings,
        TrustedLearningApplicationAuthority, TrustedLearningDecisionAuthority,
        TrustedLearningReviewAuthority,
    )
    from foundation.models import EffectivenessCheck, LearningProposal
    from foundation.phase283_retained_candidate import (
        RetainedEvidenceExportLedger, publication_snapshot_from_retained_manifest,
    )
    from foundation.retained_publication_evidence import (
        CANONICALIZATION_VERSION, CandidateEvidenceState, FINGERPRINT_VERSION,
        InertPublicationPreflightService, OPERATION_ID, OPERATION_VERSION,
        PHASE283_CANDIDATE_CLASSIFICATION, SOURCE_SCHEME, full_rule_material_hash,
        load_and_verify_synthetic_source_manifest, material_hash, phase26_semantic_fingerprint,
        phase272_lifecycle_hash, verify_phase283_candidate_evidence,
    )
    from foundation.tenant_context import TrustedTenantIdentity

    phase3.migrate(PHASE283)
    checks = []

    def check(name, condition=True):
        require(condition, name)
        checks.append(name)

    source_manifest = load_and_verify_synthetic_source_manifest(SOURCE_PATH)
    source_hash = source_manifest["source_material_sha256"]
    source_id = UUID(source_manifest["deterministic_source_id"])
    root_ref = f"{SOURCE_SCHEME}:{source_id}:{source_hash}:fixture/element/A"
    candidate_ref = f"{SOURCE_SCHEME}:{source_id}:{source_hash}:fixture/element/B"
    standard_id, edition_id, layer_id, root_id = uid("standard"), source_id, uid("knowledge-layer"), uid("root-rule")
    run_id = uid(f"run/{os.environ['FOUNDATION_DB_NAME']}")
    actor_ids = {role: uid(f"actor/{role}") for role in (
        "proposer", "reviewer", "proposal_approver", "application_authorizer",
        "application_executor", "curator", "publisher", "activator", "adopter",
    )}
    projection_ids = {role: uid(f"projection/{role}") for role in actor_ids}
    trace_id = uid("application-trace")

    with connections["default"].cursor() as cursor:
        cursor.execute("SHOW server_version_num")
        check("PostgreSQL exact version", cursor.fetchone()[0] == "180006")
        cursor.execute(
            "SELECT pg_get_functiondef('normative.apply_validated_knowledge_layer_rule_source_reference_correction_v1"
            "(uuid,text,uuid,uuid,uuid)'::regprocedure)"
        )
        function_definition = cursor.fetchone()[0]
        check("0023 synthetic grammar installed", "iso-smart-synthetic-poc-source-ref-v1" in function_definition)
        check("0023 authoritative grammar preserved", "iso-smart-source-ref-v1" in function_definition)
        protected_before = {
            table: table_digest(cursor, table) for table in (
                "normative.clause", "normative.requirement_control", "qms.evidence_coverage",
                "governance.model_policy", "governance.agent_definition", "qms.recommendation",
                "qms.recommendation_basis", "qms.agent_run", "qms.agent_run_input",
                "normative.knowledge_layer_binding",
            )
        }
        for role, external_id in actor_ids.items():
            cursor.execute(
                "INSERT INTO qms.user_projection(id,adminapps_user_id,tenant_id,source_version,source_event_id,"
                "lifecycle_status,last_synced_at) VALUES(%s,%s,%s,1,%s,'active',statement_timestamp())",
                [str(projection_ids[role]), str(external_id), str(phase3.TENANT_A), str(uid(f"projection-event/{role}"))],
            )
        cursor.execute(
            "INSERT INTO normative.standard(id,code,title,publisher) VALUES(%s,%s,%s,%s)",
            [str(standard_id), "SYNTHETIC-TEST-ONLY-NON-OFFICIAL-P28.3",
             "Non-official deterministic synthetic fixture; non-normative and non-licensed",
             "ISO SMART SYNTHETIC FIXTURE — NOT ISO"],
        )
        cursor.execute(
            "INSERT INTO normative.standard_edition(id,standard_id,edition,status,source_hash) "
            "VALUES(%s,%s,%s,'published',%s)",
            [str(edition_id), str(standard_id), "fixture-v1-non-production", source_hash],
        )
        cursor.execute(
            "INSERT INTO normative.knowledge_layer(id,standard_edition_id,layer_type,certifiability_classification) "
            "VALUES(%s,%s,%s,'non_certifiable_guidance')",
            [str(layer_id), str(edition_id), "SYNTHETIC_TEST_ONLY_SOURCE_REFERENCE_POC"],
        )
        cursor.execute(
            "INSERT INTO normative.knowledge_layer_rule(id,knowledge_layer_id,lineage_id,rule_key,version,"
            "previous_revision_id,status,logic_json,evidence_expectation,source_reference,"
            "certifiability_classification,published_at) VALUES(%s,%s,%s,%s,'sN',NULL,'draft',%s::jsonb,%s::jsonb,%s,"
            "'non_certifiable_guidance',NULL)",
            [str(root_id), str(layer_id), str(root_id), "publication-poc.synthetic-source-reference",
             json.dumps({"fixture_only": True, "operator": "source_locator_is_retained"}, sort_keys=True),
             json.dumps({"required": ["synthetic_fixture_reference"], "normative": False}, sort_keys=True), root_ref],
        )
        cursor.execute(
            "UPDATE normative.knowledge_layer_rule SET status='published',published_at=statement_timestamp() WHERE id=%s",
            [str(root_id)],
        )
        root_db = row_json(cursor, "normative.knowledge_layer_rule", root_id)
        cursor.execute(
            "INSERT INTO normative.curation_audit(id,action,entity_type,entity_id,actor_id,trace_id,payload_hash,occurred_at) "
            "VALUES(%s,'knowledge_layer_rule.synthetic_fixture_bootstrapped','knowledge_layer_rule',%s,%s,%s,%s,statement_timestamp())",
            [str(uid("root-curation-audit")), str(root_id), str(actor_ids["curator"]), str(uid("root-trace")), canonical_hash(root_db)],
        )

    identity = TrustedTenantIdentity("phase28.3-synthetic-global-governance", phase3.TENANT_A)
    proposer = TrustedLearningGovernanceAuthority(
        identity, phase3.ORG_A, projection_ids["proposer"], actor_ids["proposer"],
        frozenset({"qms.learning_signal.create", "qms.learning_proposal.create"}), True, True,
        "adminapps-phase28.3-learning-governance/v1", "phase28.3-proposer-authority",
    )
    reviewer = TrustedLearningReviewAuthority(
        identity, phase3.ORG_A, projection_ids["reviewer"], actor_ids["reviewer"],
        frozenset({"qms.learning_proposal.review"}), True, True, True,
        "adminapps-phase28.3-review/v1", "phase28.3-review-authority",
    )
    approver = TrustedLearningDecisionAuthority(
        identity, phase3.ORG_A, projection_ids["proposal_approver"], actor_ids["proposal_approver"],
        frozenset({"qms.learning_proposal.decide"}), True, True, True,
        "adminapps-phase28.3-decision/v1", "phase28.3-decision-authority",
    )
    authorizer = TrustedLearningApplicationAuthority(
        identity, phase3.ORG_A, projection_ids["application_authorizer"], actor_ids["application_authorizer"],
        frozenset({"qms.learning_application.authorize"}), True, True, True,
        "adminapps-phase28.3-authorization/v1", "phase28.3-application-authorization",
    )
    executor = TrustedKnowledgeRuleApplicationAuthority(
        identity, phase3.ORG_A, actor_ids["application_executor"], frozenset({APPLICATION_PERMISSION}),
        True, True, True, "adminapps-phase28.3-application/v1", "phase28.3-application-executor-authority",
    )

    current_checks = list(EffectivenessCheck.objects.using("default").filter(
        tenant_id=phase3.TENANT_A, successor__isnull=True,
    ))
    require(len(current_checks) == 1, "exact tenant-isolated EffectivenessCheck leaf prerequisite missing or ambiguous")
    current_check = current_checks[0]
    signal_result = LearningSignalCommandService().create_signal(
        authority=proposer, effectiveness_check_id=current_check.id, trace_id=uid("signal-trace"),
    )
    with connections["default"].cursor() as cursor:
        root_db = row_json(cursor, "normative.knowledge_layer_rule", root_id)
    target = ExactLearningTarget("KnowledgeLayerRule", root_id, root_id, "sN", canonical_hash(root_db))
    proposal_result = LearningProposalCommandService().create_proposal(
        authority=proposer, signal_ids=[signal_result.artifact_id], target=target,
        delta_command=KnowledgeLayerRuleSourceReferenceCorrection(root_ref, candidate_ref, edition_id, source_hash, "sN+1"),
        rationale="Correct only the locator in the retained non-authoritative synthetic fixture namespace.",
        expected_effect="Create one inert draft successor; semantics, runtime, publication, activation and adoption remain unchanged.",
        risks=["stale predecessor", "synthetic provenance confusion", "publication remains separately prohibited"],
        required_governance_domains=["ai_governance", "normative_curation", "security"],
        trace_id=uid("proposal-trace"),
    )
    proposal = LearningProposal.objects.using("default").get(pk=proposal_result.artifact_id)
    review_result = LearningProposalReviewCommandService().record_learning_proposal_review(
        authority=reviewer, proposal_id=proposal.id,
        findings=LearningReviewFindings(
            "Exact synthetic locator-only correction reviewed; no normative or runtime meaning changes.",
            ("ai_governance", "normative_curation", "security"),
        ), trace_id=uid("review-trace"),
    )
    decision_result = LearningProposalDecisionCommandService().record_learning_proposal_decision(
        authority=approver, proposal_id=proposal.id, review_ids=[review_result.artifact_id],
        outcome="approved_for_application", rationale="Approve only one inert synthetic draft successor.",
        trace_id=uid("decision-trace"),
    )
    authorization_result = LearningApplicationAuthorizationCommandService().authorize_learning_proposal_application(
        authority=authorizer, proposal_id=proposal.id, decision_id=decision_result.artifact_id,
        capability_id=KNOWLEDGE_RULE_OPERATION, idempotency_key="phase28.3-retained-synthetic-candidate-v1",
        trace_id=uid("authorization-trace"),
    )
    application = KnowledgeLayerRuleGovernedApplicationService()

    # The target-application transaction rolls back fully at every material boundary.
    for point in FAILURE_POINTS:
        with connections["default"].cursor() as cursor:
            before = application_snapshot(cursor, root_id)
        with connections["learning_application"].cursor() as cursor:
            cursor.execute("SELECT set_config('foundation.phase26_failure_point',%s,false)", [point])
        try:
            application.apply_validated_knowledge_layer_rule_source_reference_correction_v1(
                authority=executor, authorization_id=authorization_result.artifact_id,
                expected_delta_hash=proposal.delta_hash, trace_id=trace_id,
            )
        except Exception:
            pass
        else:
            raise AssertionError(f"application committed at injected failure point {point}")
        with connections["learning_application"].cursor() as cursor:
            cursor.execute("SELECT set_config('foundation.phase26_failure_point','',false)")
        with connections["default"].cursor() as cursor:
            check(f"application rollback {point}", application_snapshot(cursor, root_id) == before)

    def apply_exact(_):
        try:
            return KnowledgeLayerRuleGovernedApplicationService().apply_validated_knowledge_layer_rule_source_reference_correction_v1(
                authority=executor, authorization_id=authorization_result.artifact_id,
                expected_delta_hash=proposal.delta_hash, trace_id=trace_id,
            )
        finally:
            connections["learning_application"].close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(apply_exact, range(2)))
    check("concurrent exact creation one candidate", len({result.result_rule_id for result in results}) == 1)
    check("concurrent exact creation deterministic replay", sorted(result.replayed for result in results) == [False, True])
    result = results[0]
    candidate_id, receipt_id = result.result_rule_id, result.receipt_id

    # Changed material against the consumed predecessor is stale and creates no fork.
    changed_ref = f"{SOURCE_SCHEME}:{source_id}:{source_hash}:fixture/element/C"
    try:
        LearningProposalCommandService().create_proposal(
            authority=proposer, signal_ids=[signal_result.artifact_id], target=target,
            delta_command=KnowledgeLayerRuleSourceReferenceCorrection(root_ref, changed_ref, edition_id, source_hash, "sN+1-conflict"),
            rationale="Concurrency stale-delta negative fixture.", expected_effect="None.", risks=["stale"],
            required_governance_domains=["ai_governance", "normative_curation", "security"], trace_id=uid("stale-proposal-trace"),
        )
    except Exception:
        check("same lineage changed delta stale conflict")
    else:
        raise AssertionError("changed delta created a second proposal against a consumed predecessor")

    with connections["default"].cursor() as cursor:
        root_db = row_json(cursor, "normative.knowledge_layer_rule", root_id)
        candidate_db = row_json(cursor, "normative.knowledge_layer_rule", candidate_id)
        signal_db = row_json(cursor, "qms.learning_signal", signal_result.artifact_id)
        proposal_db = row_json(cursor, "qms.learning_proposal", proposal.id)
        cursor.execute("SELECT id FROM qms.learning_proposal_canonical_delta WHERE learning_proposal_id=%s", [str(proposal.id)])
        delta_id = cursor.fetchone()[0]
        delta_db = row_json(cursor, "qms.learning_proposal_canonical_delta", delta_id)
        review_db = row_json(cursor, "qms.learning_proposal_review", review_result.artifact_id)
        decision_db = row_json(cursor, "qms.learning_proposal_decision", decision_result.artifact_id)
        authorization_db = row_json(cursor, "qms.learning_application_authorization", authorization_result.artifact_id)
        receipt_db = row_json(cursor, "qms.learning_target_application_receipt", receipt_id)
        event_db = row_json(cursor, "normative.knowledge_layer_rule_event", receipt_db["target_event_id"])
        outbox_db = row_json(cursor, "eventing.platform_transactional_outbox", receipt_db["target_outbox_id"])
        audit_db = row_json(cursor, "qms.learning_target_application_audit", receipt_db["application_audit_id"])
        cursor.execute(
            "SELECT id::text FROM normative.knowledge_layer_rule r WHERE lineage_id=%s AND NOT EXISTS "
            "(SELECT 1 FROM normative.knowledge_layer_rule child WHERE child.previous_revision_id=r.id) ORDER BY id",
            [str(root_id)],
        )
        leaf_ids = [row[0] for row in cursor.fetchall()]
        check("candidate singleton current leaf", leaf_ids == [str(candidate_id)])
        check("candidate predecessor exact", candidate_db["previous_revision_id"] == str(root_id))
        check("candidate draft unpublished", candidate_db["status"] == "draft" and candidate_db["published_at"] is None)
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule_publication")
        publication_rows = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule_activation")
        activation_rows = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule_runtime_adoption")
        adoption_rows = cursor.fetchone()[0]
        cursor.execute(
            "SELECT count(*) FILTER(WHERE event_type='knowledge_layer_rule.published'),"
            "count(*) FILTER(WHERE event_type='knowledge_layer_rule.activation_recorded'),"
            "count(*) FILTER(WHERE event_type='knowledge_layer_rule.runtime_adopted') "
            "FROM normative.knowledge_layer_rule_governance_event"
        )
        publication_events, activation_events, adoption_events = cursor.fetchone()
        check("zero publication", publication_rows == publication_events == 0)
        check("zero activation", activation_rows == activation_events == 0)
        check("zero runtime adoption", adoption_rows == adoption_events == 0)
        protected_after = {table: table_digest(cursor, table) for table in protected_before}
        check("protected runtime and normative tables invariant", protected_after == protected_before)
        cursor.execute(
            "SELECT rolcanlogin,rolsuper,rolinherit,rolbypassrls FROM pg_roles WHERE rolname=%s",
            [os.environ["FOUNDATION_LEARNING_APPLICATION_EXECUTOR_ROLE"]],
        )
        check("application executor least privilege role", cursor.fetchone() == (True, False, False, False))
        cursor.execute(
            "SELECT has_table_privilege(%s,'normative.knowledge_layer_rule','INSERT,UPDATE,DELETE')",
            [os.environ["FOUNDATION_LEARNING_APPLICATION_EXECUTOR_ROLE"]],
        )
        check("application executor no generic target DML", cursor.fetchone()[0] is False)
        cursor.execute(
            "SELECT has_function_privilege(%s,'normative.publish_knowledge_layer_rule_v1(uuid,uuid,text,text,text,uuid,uuid)','EXECUTE')",
            [os.environ["FOUNDATION_LEARNING_APPLICATION_EXECUTOR_ROLE"]],
        )
        check("application executor no publication capability", cursor.fetchone()[0] is False)

    def rule_material(row):
        return {
            "id": row["id"], "knowledge_layer_id": row["knowledge_layer_id"],
            "knowledge_layer_type": "SYNTHETIC_TEST_ONLY_SOURCE_REFERENCE_POC",
            "standard_id": str(standard_id), "standard_edition_id": str(edition_id),
            "standard_edition_source_hash": source_hash, "lineage_id": row["lineage_id"],
            "rule_key": row["rule_key"], "version": row["version"],
            "previous_revision_id": row["previous_revision_id"], "logic_json": row["logic_json"],
            "evidence_expectation": row["evidence_expectation"], "source_reference": row["source_reference"],
            "source_reference_scheme": SOURCE_SCHEME,
            "certifiability_classification": row["certifiability_classification"],
        }

    root_material, candidate_material = rule_material(root_db), rule_material(candidate_db)
    root_full, candidate_full = full_rule_material_hash(root_material), full_rule_material_hash(candidate_material)
    semantic = phase26_semantic_fingerprint(root_material)
    lifecycle = phase272_lifecycle_hash(root_material)
    check("semantic fingerprint preserved", semantic == phase26_semantic_fingerprint(candidate_material) == receipt_db["semantic_fingerprint"])
    check("full material changed", root_full != candidate_full)
    check("lifecycle hash preserved", lifecycle == phase272_lifecycle_hash(candidate_material))

    common = {"target_rule_id": str(root_id), "operation_id": OPERATION_ID, "operation_version": OPERATION_VERSION}
    signal_ref = material_reference(material_hash, signal_db, **common)
    proposal_ref = material_reference(material_hash, proposal_db, learning_signal_id=str(signal_result.artifact_id), **common)
    delta_ref = material_reference(material_hash, delta_db, proposal_revision_id=str(proposal.id), **common)
    review_ref = material_reference(
        material_hash, review_db, proposal_revision_id=str(proposal.id), canonical_delta_id=str(delta_id),
        outcome="APPROVE", selected=True,
    )
    decision_ref = material_reference(
        material_hash, decision_db, proposal_revision_id=str(proposal.id), canonical_delta_id=str(delta_id), outcome="APPROVED",
    )
    authorization_ref = material_reference(
        material_hash, authorization_db, decision_id=str(decision_result.artifact_id), status="VALID", **common,
    )
    receipt_ref = material_reference(
        material_hash, receipt_db, proposal_revision_id=str(proposal.id), canonical_delta_id=str(delta_id),
        decision_id=str(decision_result.artifact_id), application_authorization_id=str(authorization_result.artifact_id),
        result_rule_id=str(candidate_id), result_material_hash=candidate_full,
        result_semantic_fingerprint=semantic, successful=True, external_effects=False,
        runtime_effect_changed=False, result_published=False, result_status="draft", **common,
    )
    event_ref = material_reference(
        material_hash, event_db, receipt_id=str(receipt_id), result_rule_id=str(candidate_id),
    )
    outbox_ref = material_reference(material_hash, outbox_db, event_id=str(event_db["id"]))
    audit_ref = material_reference(material_hash, audit_db, receipt_id=str(receipt_id))

    policy_material = {
        "id": str(uid("phase28.3-policy")),
        "policy_id": "first-retained-synthetic-klr-publication-candidate-policy/v1", "version": "v1",
        "authorization": "FUTURE_EPHEMERAL_PUBLICATION_POC_ELIGIBILITY_ONLY",
        "candidate_id": str(candidate_id), "lineage_id": str(root_id), "predecessor_rule_id": str(root_id),
        "candidate_version": "sN+1", "candidate_full_material_hash": candidate_full,
        "semantic_fingerprint": semantic, "lifecycle_hash": lifecycle,
        "publication_authorized": False, "activation_authorized": False,
        "runtime_adoption_authorized": False, "production_authorized": False,
    }
    policy_ref = material_reference(
        material_hash, policy_material, policy_id=policy_material["policy_id"], version="v1",
    )
    existing_policy_materials = []
    for name, relative, policy_id in (
        ("learning-policy", "docs/governance/GOVERNED_LEARNING_POLICY_V1.md", "governed-learning-policy/v1"),
        ("application-policy", "docs/governance/KNOWLEDGE_LAYER_RULE_GOVERNED_SOURCE_REFERENCE_APPLICATION_POLICY_V1.md", "knowledge-layer-rule-governed-source-reference-application-policy/v1"),
        ("publication-policy", "docs/governance/KNOWLEDGE_LAYER_RULE_PUBLICATION_ACTIVATION_RUNTIME_ADOPTION_POLICY_V1.md", "knowledge-layer-rule-publication-activation-runtime-adoption/v1"),
    ):
        file_hash = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        material = {"id": str(uid(f"policy/{name}")), "policy_id": policy_id, "version": "v1", "file": relative, "file_sha256": file_hash}
        existing_policy_materials.append(material_reference(material_hash, material, policy_id=policy_id, version="v1"))

    now = datetime.now(timezone.utc)
    curator_material = {
        "id": str(uid("curator-evidence")), "actor_external_id": str(actor_ids["curator"]),
        "candidate_id": str(candidate_id), "candidate_material_hash": candidate_full,
        "semantic_fingerprint": semantic, "source_manifest_hash": source_manifest["manifest_material_hash"],
        "source_reference_hash": hashlib.sha256(candidate_ref.encode()).hexdigest(),
        "authority_decision_id": str(uid("curator-authority-decision")),
        "authority_decision_hash": material_hash({"authority": "phase28.3-curator", "server_resolved": True}),
        "server_resolved": True, "valid_at": now.isoformat(), "decision": "VALIDATED_FOR_LATER_PUBLICATION_GATE_ONLY",
    }
    curator_ref = material_reference(material_hash, curator_material)
    publisher_material = {
        "id": str(uid("publisher-eligibility-authority")), "actor_external_id": str(actor_ids["publisher"]),
        "authority_type": "PUBLICATION_POC_ELIGIBILITY_AUTHORITY", "publication_invoked": False,
        "permissions": ["qms.knowledge_layer_rule.publish"], "mfa_verified": True, "access_active": True,
        "global_governance": True, "server_resolved": True,
        "authority_context_version": "adminapps-phase28.3-future-publisher-eligibility/v1",
        "authority_decision_id": str(uid("publisher-authority-decision")),
        "authority_decision_hash": material_hash({"authority": "phase28.3-future-publisher", "eligibility_only": True}),
        "resolved_at": now.isoformat(), "expires_at": (now + timedelta(minutes=30)).isoformat(),
    }
    publisher_ref = material_reference(material_hash, publisher_material)
    chain = {
        "learning_signal": signal_ref, "learning_proposal_revision": proposal_ref,
        "canonical_delta": delta_ref, "selected_reviews": [review_ref], "decision": decision_ref,
        "application_authorization": authorization_ref, "application_receipt": receipt_ref,
        "domain_events": [event_ref], "transactional_outbox": [outbox_ref],
        "immutable_audits": [audit_ref], "policies": existing_policy_materials + [policy_ref],
    }
    manifest = {
        "manifest_schema": "governed-target-application-evidence-manifest/v1",
        "evidence_state": CandidateEvidenceState.CREATED_AND_RETAINED.value, "run_id": str(run_id),
        "candidate_classification": PHASE283_CANDIDATE_CLASSIFICATION, "target_type": "KnowledgeLayerRule",
        "operation_id": OPERATION_ID, "operation_version": OPERATION_VERSION,
        "fingerprint_version": FINGERPRINT_VERSION,
        "generator_contract_version": "governed-target-application-evidence-export/v1",
        "source_classification": "RETAINED_DETERMINISTIC_SYNTHETIC_FIXTURE", "phase26_continuity_claim": False,
        "root": {"id": str(root_id), "knowledge_layer_id": str(layer_id), "lineage_id": str(root_id),
                 "version": "sN", "full_material_hash": root_full, "semantic_fingerprint": semantic,
                 "lifecycle_hash": lifecycle, "fixture_only": True},
        "candidate": {"id": str(candidate_id), "knowledge_layer_id": str(layer_id), "lineage_id": str(root_id),
                      "predecessor_rule_id": str(root_id), "version": "sN+1",
                      "full_material_hash": candidate_full, "semantic_fingerprint": semantic,
                      "lifecycle_hash": lifecycle},
        "canonical_root_material": root_material, "canonical_rule_material": candidate_material,
        "source": {"manifest_id": str(source_id), "manifest_hash": source_manifest["manifest_material_hash"],
                   "material_hash": source_hash, "reference_before": root_ref,
                   "reference_before_hash": hashlib.sha256(root_ref.encode()).hexdigest(),
                   "reference_after": candidate_ref, "reference": candidate_ref,
                   "reference_hash": hashlib.sha256(candidate_ref.encode()).hexdigest()},
        "governance_chain": chain,
        "current_leaf_proof": {"lineage_id": str(root_id), "leaf_ids": leaf_ids, "unique": True,
                               "candidate_version": "sN+1", "selection_method": "EXACT_PREDECESSOR_GRAPH"},
        "curator_evidence": curator_ref, "future_publisher_authority": publisher_ref,
        "role_actor_ids": {role: str(value) for role, value in actor_ids.items()},
        "expected_state_token": material_hash({"candidate": str(candidate_id), "leaf_ids": leaf_ids,
                                                "status": "draft", "published": False, "active": False, "adopted": False}),
        "zero_effects": {"publication_rows": publication_rows, "activation_rows": activation_rows,
                         "runtime_adoption_rows": adoption_rows, "publication_events": publication_events,
                         "activation_events": activation_events, "runtime_adoption_events": adoption_events},
        "trace_id": str(trace_id), "correlation_ids": [str(proposal.id), str(receipt_id)],
        "created_at": candidate_db["created_at"], "exported_at": now.isoformat(),
        "retained_at": (now + timedelta(microseconds=1)).isoformat(),
        "retention_integrity_verified": True, "integrity_verified": True, "live_graph_verified": True,
        "teardown_intent": "DESTROY_COMPLETE_EPHEMERAL_POSTGRESQL_ENVIRONMENT",
        "canonicalization_version": CANONICALIZATION_VERSION,
    }
    manifest["manifest_material_hash"] = material_hash(manifest)
    verify_phase283_candidate_evidence(manifest, source_manifest=source_manifest)
    snapshot = publication_snapshot_from_retained_manifest(manifest)
    live_preflight = InertPublicationPreflightService().evaluate(
        preflight_id=uid("live-preflight"), idempotency_key_hash=material_hash({"preflight": "phase28.3-live"}),
        retained_manifest=manifest, snapshot_provider=lambda: snapshot, now=now + timedelta(seconds=1),
    )
    check("live publication preflight eligible only", live_preflight.outcome == "ELIGIBLE_FOR_LATER_PUBLICATION_GATE")

    ledger = RetainedEvidenceExportLedger()
    with ThreadPoolExecutor(max_workers=2) as pool:
        replay_flags = list(pool.map(lambda _: ledger.retain(EVIDENCE_PATH, manifest), range(2)))
    check("evidence export race one canonical manifest", sorted(replay_flags) == [False, True])
    retained = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    verify_phase283_candidate_evidence(retained, source_manifest=source_manifest)
    check("retained bytes verify before teardown")

    print(json.dumps({
        "status": "PASS", "postgresql": "18.6", "run_id": str(run_id),
        "candidate_id": str(candidate_id), "root_id": str(root_id), "lineage_id": str(root_id),
        "receipt_id": str(receipt_id), "manifest_path": str(EVIDENCE_PATH),
        "manifest_material_hash": manifest["manifest_material_hash"],
        "semantic_fingerprint": semantic, "root_full_material_hash": root_full,
        "candidate_full_material_hash": candidate_full, "lifecycle_hash": lifecycle,
        "rollback_matrix": f"{len(FAILURE_POINTS)}/{len(FAILURE_POINTS)} PASS",
        "checks": len(checks), "publication_rows": 0, "activation_rows": 0,
        "runtime_adoption_rows": 0, "live_preflight": live_preflight.outcome,
    }, indent=2))


if __name__ == "__main__":
    run()
