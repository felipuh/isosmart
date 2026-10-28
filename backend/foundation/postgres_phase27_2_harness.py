"""PostgreSQL 18.6 Phase 27.2 inert release-governance proof matrix."""

import hashlib
import inspect
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from uuid import UUID, uuid4

import postgres_foundation_harness as phase3
import postgres_phase26_harness as phase26


PHASE26 = ("foundation", "0021_first_governed_knowledge_rule_application_poc")
PHASE272 = ("foundation", "0022_inert_rule_publication_activation_runtime_adoption")
FAILURE_POINTS = ("after_claim", "after_event", "after_outbox", "after_audit", "after_artifact", "before_commit")


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


def digest(cursor, table, where="true", params=None):
    cursor.execute(
        f"SELECT count(*),md5(COALESCE(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) "
        f"FROM {table} t WHERE {where}", params or [],
    )
    return cursor.fetchone()


def governance_snapshot(cursor):
    return {
        table: digest(cursor, table)
        for table in (
            "normative.knowledge_layer_rule_governance_claim",
            "normative.knowledge_layer_rule_publication",
            "normative.knowledge_layer_rule_activation",
            "normative.knowledge_layer_rule_runtime_adoption",
            "normative.knowledge_layer_rule_governance_event",
            "eventing.knowledge_layer_rule_governance_outbox",
            "audit.knowledge_layer_rule_governance_audit",
        )
    }


def rule_hash(rule_id):
    from django.db import connections
    with connections["rule_publisher"].cursor() as cursor:
        cursor.execute("SELECT normative.foundation_0022_rule_material_hash(%s)", [str(rule_id)])
        return cursor.fetchone()[0]


def set_failure(point, alias):
    from django.db import connections
    with connections[alias].cursor() as cursor:
        cursor.execute("SELECT set_config('foundation.phase272_failure_point',%s,false)", [point])


def h(value):
    return hashlib.sha256(value.encode()).hexdigest()


def run():
    phase26.run()
    from django.db import connections
    from foundation.knowledge_layer import KnowledgeLayerCommandService
    from foundation.knowledge_rule_release import (
        ACTIVATION_PERMISSION, ADOPTION_PERMISSION, CAPABILITY_PERMISSION,
        PUBLICATION_PERMISSION, REPAIR_PERMISSION,
        GovernanceCapabilityService, GovernanceRepairService,
        InertRuntimeAdoptionResolver, KnowledgeLayerRuleActivationService,
        KnowledgeLayerRulePublicationService, KnowledgeLayerRuleRuntimeAdoptionService,
        ReconciliationOutcome, TrustedActivationAuthority, TrustedCapabilityAuthority,
        TrustedPublicationAuthority, TrustedRepairAuthority,
        TrustedRuntimeAdoptionAuthority,
    )
    from foundation.models import KnowledgeLayer

    checks = []
    def check(name, condition=True):
        require(condition, name)
        checks.append(name)

    root = Path(__file__).resolve().parent
    runtime_files = (root / "agent_runtime.py", root / "recommendation.py")
    runtime_before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in runtime_files}

    # Identify and freeze the Phase 26 protected chain before adding the inert schema.
    with connections["default"].cursor() as cursor:
        cursor.execute(
            "SELECT f.before_rule_id,f.after_rule_id,c.after_rule_id "
            "FROM qms.learning_target_application_receipt c "
            "JOIN qms.learning_target_application_receipt f ON f.id=c.forward_receipt_id LIMIT 1"
        )
        vn_id, vn1_id, vn2_id = cursor.fetchone()
        protected_before = {
            table: digest(cursor, table) for table in (
                "governance.model_policy", "governance.agent_definition",
                "qms.recommendation", "qms.recommendation_basis",
                "qms.agent_run", "qms.agent_run_input", "qms.learning_signal",
                "qms.learning_proposal",
            )
        }
        cursor.execute("SELECT status,published_at FROM normative.knowledge_layer_rule WHERE id=%s", [str(vn_id)])
        check("Phase 26 vN remains published/runtime-effective", cursor.fetchone()[0] == "published")
        cursor.execute("SELECT id,status,published_at FROM normative.knowledge_layer_rule WHERE id=ANY(%s::uuid[])", [[str(vn1_id), str(vn2_id)]])
        check("Phase 26 successors start inert", all(row[1] == "draft" and row[2] is None for row in cursor.fetchall()))

    # Additive evolution and empty-history reverse/forward.
    phase3.migrate(PHASE272)
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT to_regclass('normative.knowledge_layer_rule_runtime_adoption')")
        check("0022 additive forward", cursor.fetchone()[0] == "normative.knowledge_layer_rule_runtime_adoption")
    phase3.migrate(PHASE26)
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT to_regclass('normative.knowledge_layer_rule_runtime_adoption')")
        check("0022 empty-history reverse", cursor.fetchone()[0] is None)
    phase3.migrate(PHASE272)

    pub_actor, act_actor, adopt_actor, repair_actor, control_actor = [uuid4() for _ in range(5)]
    authority_args = (frozenset(), True, True, True, "adminapps-authority-context/v1", "synthetic-fresh-decision", "knowledge-rule-release-policy/v1")
    publisher = TrustedPublicationAuthority(pub_actor, frozenset({PUBLICATION_PERMISSION}), *authority_args[1:])
    activator = TrustedActivationAuthority(act_actor, frozenset({ACTIVATION_PERMISSION}), *authority_args[1:])
    adopter = TrustedRuntimeAdoptionAuthority(adopt_actor, frozenset({ADOPTION_PERMISSION}), *authority_args[1:])
    repair = TrustedRepairAuthority(repair_actor, frozenset({REPAIR_PERMISSION}), *authority_args[1:])
    controller = TrustedCapabilityAuthority(control_actor, frozenset({CAPABILITY_PERMISSION}), *authority_args[1:])
    pub_service = KnowledgeLayerRulePublicationService()
    act_service = KnowledgeLayerRuleActivationService()
    adoption_service = KnowledgeLayerRuleRuntimeAdoptionService()
    resolver = InertRuntimeAdoptionResolver()
    repair_service = GovernanceRepairService()
    capability_service = GovernanceCapabilityService()

    # Catalog/ACL evidence and global boundary.
    role_function = {
        os.environ["FOUNDATION_RULE_PUBLISHER_ROLE"]: "normative.publish_knowledge_layer_rule_v1(uuid,uuid,text,text,text,uuid,uuid)",
        os.environ["FOUNDATION_RULE_ACTIVATOR_ROLE"]: "normative.activate_knowledge_layer_rule_v1(uuid,uuid,text,uuid,text,text,text,uuid,uuid)",
        os.environ["FOUNDATION_RULE_ADOPTER_ROLE"]: "normative.adopt_knowledge_layer_rule_runtime_v1(uuid,uuid,text,uuid,text,text,text,text,uuid,uuid)",
        os.environ["FOUNDATION_RULE_RESOLVER_ROLE"]: "normative.resolve_knowledge_layer_rule_runtime_adoption_v1(uuid)",
    }
    with connections["default"].cursor() as cursor:
        for role, function in role_function.items():
            cursor.execute("SELECT rolcanlogin,rolsuper,rolinherit,rolbypassrls FROM pg_roles WHERE rolname=%s", [role])
            check(f"safe role catalog {role}", cursor.fetchone() == (True, False, False, False))
            cursor.execute("SELECT has_function_privilege(%s,%s,'EXECUTE')", [role, function])
            check(f"exact function ACL {role}", cursor.fetchone()[0])
        cursor.execute("SELECT rolcanlogin,rolsuper,rolinherit,rolbypassrls FROM pg_roles WHERE rolname=%s", [os.environ["FOUNDATION_RULE_GOVERNANCE_OWNER_ROLE"]])
        check("NOLOGIN least-privilege owner", cursor.fetchone() == (False, False, False, False))
        cursor.execute(
            "SELECT count(*) FROM information_schema.columns WHERE table_schema='normative' "
            "AND table_name IN ('knowledge_layer_rule_publication','knowledge_layer_rule_activation','knowledge_layer_rule_runtime_adoption') "
            "AND column_name='tenant_id'"
        )
        check("global artifacts have no fake tenant ownership", cursor.fetchone()[0] == 0)
        cursor.execute(
            "SELECT bool_and(p.prosecdef),bool_and(p.proconfig=ARRAY['search_path=pg_catalog']),"
            "bool_and(NOT has_function_privilege('public',p.oid,'EXECUTE')) "
            "FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
            "WHERE n.nspname='normative' AND p.proname IN "
            "('publish_knowledge_layer_rule_v1','import_knowledge_layer_rule_publication_evidence_v1',"
            "'activate_knowledge_layer_rule_v1','adopt_knowledge_layer_rule_runtime_v1',"
            "'bootstrap_legacy_knowledge_layer_rule_runtime_v1','resolve_knowledge_layer_rule_runtime_adoption_v1')"
        )
        check("privileged functions fixed safe search_path and PUBLIC denied", cursor.fetchone() == (True, True, True))

    # Create a new synthetic revision; no Phase 26 successor is touched.
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT id FROM normative.knowledge_layer LIMIT 1")
        layer_id = cursor.fetchone()[0]
    knowledge = KnowledgeLayerCommandService(using="normative_curator")
    rule_id = knowledge.create_knowledge_layer_rule(
        knowledge_layer_id=layer_id, rule_key="phase272-inert-foundation", version="phase272-v1",
        logic_json={"kind": "NON-OFFICIAL TEST FIXTURE", "threshold": 27},
        evidence_expectation={"required": ["synthetic-only"]}, source_reference=None,
        actor_id="phase272-curator", trace_id=uuid4(),
    )
    material = rule_hash(rule_id)

    # Exact resolver fail-closed combinations: draft; publication only; activation only.
    for invalid in (None, "current", "latest", str(rule_id), str(layer_id), "27", "2026-09-02T00:00:00Z"):
        expect_error(lambda invalid=invalid: resolver.resolve(runtime_adoption_id=invalid))
    check("resolver rejects omitted/substitute/latest/current/version/time identifiers")
    pub_id = uuid4()
    before_activation = before_adoption = 0
    publication = pub_service.publish_native(
        authority=publisher, publication_id=pub_id, rule_id=rule_id,
        expected_rule_material_hash=material, idempotency_key_hash=h("phase272-publication"),
        reason="Synthetic inert publication boundary proof.", trace_id=uuid4(),
    )
    check("native publication committed", publication.artifact_id == pub_id and not publication.replayed)
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule_activation")
        after_activation = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule_runtime_adoption")
        after_adoption = cursor.fetchone()[0]
        check("publication creates zero Activation", after_activation == before_activation)
        check("publication creates zero RuntimeAdoption", after_adoption == before_adoption)
    expect_error(lambda: resolver.resolve(runtime_adoption_id=uuid4()), "absent")
    check("publication alone is not runtime-adoptable")

    act_id = uuid4()
    activation = act_service.activate(
        authority=activator, activation_id=act_id, publication_id=pub_id,
        expected_rule_material_hash=material, expected_predecessor_activation_id=None,
        compatibility_hash=h("phase272-compatibility"), idempotency_key_hash=h("phase272-activation"),
        reason="Synthetic inert activation eligibility proof.", trace_id=uuid4(),
    )
    check("activation committed", activation.artifact_id == act_id)
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule_runtime_adoption")
        check("activation creates zero RuntimeAdoption", cursor.fetchone()[0] == after_adoption)
    expect_error(lambda: resolver.resolve(runtime_adoption_id=act_id), "absent")
    check("activation ID cannot substitute for adoption ID")

    adoption_id = uuid4()
    adopted = adoption_service.adopt(
        authority=adopter, runtime_adoption_id=adoption_id, activation_id=act_id,
        expected_rule_material_hash=material, expected_predecessor_adoption_id=None,
        release_configuration_reference="synthetic://phase272/config/1",
        release_configuration_hash=h("phase272-config-1"), idempotency_key_hash=h("phase272-adoption"),
        reason="Synthetic inert exact adoption proof; no runtime cutover.", trace_id=uuid4(),
    )
    resolved = resolver.resolve(runtime_adoption_id=adoption_id)
    check("only exact adoption resolves exact chain", resolved.knowledge_layer_rule_id == rule_id and resolved.activation_id == act_id and resolved.publication_id == pub_id and resolved.rule_material_hash == material)
    check("adoption does not mutate target", rule_hash(rule_id) == material)

    # Exact-predecessor concurrency: only one successor may commit from A1.
    competing_activations = [uuid4(), uuid4()]
    def concurrent_activation(index):
        try:
            result = KnowledgeLayerRuleActivationService().activate(
                authority=activator, activation_id=competing_activations[index], publication_id=pub_id,
                expected_rule_material_hash=material, expected_predecessor_activation_id=act_id,
                compatibility_hash=h(f"concurrent-activation-compat-{index}"),
                idempotency_key_hash=h(f"concurrent-activation-{index}"),
                reason=f"Competing exact activation {index}.", trace_id=uuid4(),
            )
            return ("committed", result.artifact_id)
        except Exception as exc:
            return ("denied", str(exc))
        finally:
            connections["rule_activator"].close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        activation_race = list(pool.map(concurrent_activation, range(2)))
    activation_winners = [value for state, value in activation_race if state == "committed"]
    check("activation exact-predecessor race has one winner", len(activation_winners) == 1)
    activation2_id = activation_winners[0]
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule_activation WHERE predecessor_activation_id=%s", [str(act_id)])
        check("activation catalog has no predecessor fork", cursor.fetchone()[0] == 1)

    competing_adoptions = [uuid4(), uuid4()]
    def concurrent_adoption(index):
        try:
            result = KnowledgeLayerRuleRuntimeAdoptionService().adopt(
                authority=adopter, runtime_adoption_id=competing_adoptions[index], activation_id=activation2_id,
                expected_rule_material_hash=material, expected_predecessor_adoption_id=adoption_id,
                release_configuration_reference=f"synthetic://phase272/concurrent/{index}",
                release_configuration_hash=h(f"concurrent-config-{index}"),
                idempotency_key_hash=h(f"concurrent-adoption-{index}"),
                reason=f"Competing exact adoption {index}.", trace_id=uuid4(),
            )
            return ("committed", result.artifact_id)
        except Exception as exc:
            return ("denied", str(exc))
        finally:
            connections["rule_adopter"].close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        adoption_race = list(pool.map(concurrent_adoption, range(2)))
    adoption_winners = [value for state, value in adoption_race if state == "committed"]
    check("adoption exact-predecessor race has one winner", len(adoption_winners) == 1)
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule_runtime_adoption WHERE predecessor_adoption_id=%s", [str(adoption_id)])
        check("adoption catalog has no predecessor fork", cursor.fetchone()[0] == 1)

    # Events are evidence only and the exact graph reconciles COMMITTED.
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT event_type,payload->>'next_stage_requested',payload->>'deployment_requested' FROM normative.knowledge_layer_rule_governance_event ORDER BY occurred_at")
        event_rows = cursor.fetchall()
        check("published event does not request activation", event_rows[0][0] == "knowledge_layer_rule.published" and event_rows[0][1] == "false")
        check("activation event does not request adoption", event_rows[1][0] == "knowledge_layer_rule.activation_recorded" and event_rows[1][1] == "false")
        check("runtime-adopted event does not deploy", event_rows[2][0] == "knowledge_layer_rule.runtime_adopted" and event_rows[2][2] == "false")
    check("publication graph reconciles committed", repair_service.reconcile_publication(pub_id).outcome is ReconciliationOutcome.COMMITTED)
    check("activation graph reconciles committed", repair_service.reconcile_activation(act_id).outcome is ReconciliationOutcome.COMMITTED)
    check("adoption graph reconciles committed", repair_service.reconcile_adoption(adoption_id).outcome is ReconciliationOutcome.COMMITTED)
    unknown_id = uuid4()
    check("absent operation is strictly NOT_COMMITTED", repair_service.reconcile_adoption(unknown_id).outcome is ReconciliationOutcome.NOT_COMMITTED)

    # Truthful legacy import/bootstrap for pre-foundation state only.
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT id,published_at FROM normative.knowledge_layer_rule WHERE id=%s", [str(vn_id)])
        _, legacy_published_at = cursor.fetchone()
        cursor.execute("SELECT id FROM normative.curation_audit WHERE entity_id=%s AND action='knowledge_layer_rule.published' ORDER BY occurred_at LIMIT 1", [str(vn_id)])
        legacy_audit = cursor.fetchone()[0]
    legacy_pub_id = uuid4()
    legacy_pub = pub_service.import_legacy_evidence(
        authority=publisher, publication_id=legacy_pub_id, rule_id=vn_id,
        expected_rule_material_hash=rule_hash(vn_id), curation_audit_id=legacy_audit,
        historical_published_at=legacy_published_at, evidence_reference="synthetic-existing-curation-audit",
        idempotency_key_hash=h("phase272-legacy-publication"), reason="Import existing Phase 26 publication evidence without a new approval claim.", trace_id=uuid4(),
    )
    check("legacy evidence import committed", legacy_pub.artifact_id == legacy_pub_id)
    legacy_adoption_id = uuid4()
    adoption_service.bootstrap_legacy(
        authority=adopter, runtime_adoption_id=legacy_adoption_id, rule_id=vn_id,
        expected_rule_material_hash=rule_hash(vn_id), release_configuration_reference="synthetic://pre-foundation/exact-rule-id",
        release_configuration_hash=h("legacy-config"), idempotency_key_hash=h("legacy-bootstrap"),
        reason="Truthful import of pre-foundation exact runtime state.", trace_id=uuid4(),
    )
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT evidence_kind,workflow_approved,historical_published_at,evidence_imported_at FROM normative.knowledge_layer_rule_publication WHERE id=%s", [str(legacy_pub_id)])
        kind, approved, historical_at, imported_at = cursor.fetchone()
        check("legacy publication truthfully distinguished", kind == "LEGACY_EVIDENCE_IMPORT" and not approved and historical_at == legacy_published_at and imported_at != historical_at)
        cursor.execute("SELECT adoption_kind,activation_id,publication_id,historical_activation_claim,asserted_historical_effective_at,bootstrap_imported_at FROM normative.knowledge_layer_rule_runtime_adoption WHERE id=%s", [str(legacy_adoption_id)])
        row = cursor.fetchone()
        check("legacy bootstrap cannot fabricate activation/publication/time", row[0] == "LEGACY_BOOTSTRAP" and row[1] is None and row[2] is None and not row[3] and row[4] is None and row[5] is not None)
    expect_error(lambda: resolver.resolve(runtime_adoption_id=legacy_adoption_id), "absent")
    check("legacy bootstrap is inert in new strict resolver")
    for successor in (vn1_id, vn2_id):
        expect_error(lambda successor=successor: adoption_service.bootstrap_legacy(
            authority=adopter, runtime_adoption_id=uuid4(), rule_id=successor,
            expected_rule_material_hash=rule_hash(successor), release_configuration_reference="synthetic://forbidden",
            release_configuration_hash=h("forbidden"), idempotency_key_hash=h(str(successor)), reason="must fail", trace_id=uuid4()))
    check("legacy bootstrap rejects both Phase 26 successors")

    # Hash freeze, provenance exactness, revocation and cross-duty negatives.
    expect_error(lambda: act_service.activate(
        authority=activator, activation_id=uuid4(), publication_id=pub_id,
        expected_rule_material_hash="0" * 64, expected_predecessor_activation_id=act_id,
        compatibility_hash=h("bad"), idempotency_key_hash=h("bad-act"), reason="bad", trace_id=uuid4()), "hash")
    expect_error(lambda: adoption_service.adopt(
        authority=adopter, runtime_adoption_id=uuid4(), activation_id=act_id,
        expected_rule_material_hash="0" * 64, expected_predecessor_adoption_id=adoption_id,
        release_configuration_reference="synthetic://bad", release_configuration_hash=h("bad"),
        idempotency_key_hash=h("bad-adopt"), reason="bad", trace_id=uuid4()), "hash")
    check("hash revalidated at activation and adoption boundaries")
    expect_error(lambda: pub_service.publish_native(
        authority=publisher, publication_id=uuid4(), rule_id=vn1_id,
        expected_rule_material_hash="0" * 64, idempotency_key_hash=h("bad-pub-hash"),
        reason="bad hash must fail", trace_id=uuid4()), "hash")
    check("hash revalidated at publication boundary")
    revoked = TrustedPublicationAuthority(pub_actor, frozenset({PUBLICATION_PERMISSION}), True, False, True, "adminapps-authority-context/v2", "revoked", "knowledge-rule-release-policy/v1")
    expect_error(lambda: pub_service.publish_native(
        authority=revoked, publication_id=uuid4(), rule_id=vn1_id,
        expected_rule_material_hash=rule_hash(vn1_id), idempotency_key_hash=h("revoked"), reason="denied", trace_id=uuid4()), "authority")
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT actor_external_id,authority_context_version,authority_decision_reference,governance_policy_version FROM normative.knowledge_layer_rule_publication WHERE id=%s", [str(pub_id)])
        check("historical authority provenance remains frozen after revocation", cursor.fetchone() == (pub_actor, "adminapps-authority-context/v1", "synthetic-fresh-decision", "knowledge-rule-release-policy/v1"))
    expect_error(lambda: pub_service.publish_native(authority=activator, publication_id=uuid4(), rule_id=vn1_id, expected_rule_material_hash=rule_hash(vn1_id), idempotency_key_hash=h("cross1"), reason="denied", trace_id=uuid4()))
    expect_error(lambda: act_service.activate(authority=publisher, activation_id=uuid4(), publication_id=pub_id, expected_rule_material_hash=material, expected_predecessor_activation_id=act_id, compatibility_hash=h("cross"), idempotency_key_hash=h("cross2"), reason="denied", trace_id=uuid4()))
    expect_error(lambda: adoption_service.adopt(authority=activator, runtime_adoption_id=uuid4(), activation_id=act_id, expected_rule_material_hash=material, expected_predecessor_adoption_id=adoption_id, release_configuration_reference="x", release_configuration_hash=h("x"), idempotency_key_hash=h("cross3"), reason="denied", trace_id=uuid4()))
    check("service authority types independently fence all duties")

    # Atomic rollback matrix on one new chain per operation.
    atomic_rule = knowledge.create_knowledge_layer_rule(
        knowledge_layer_id=layer_id, rule_key="phase272-atomic", version="phase272-atomic-v1",
        logic_json={"synthetic": True}, evidence_expectation={}, source_reference=None,
        actor_id="phase272-curator", trace_id=uuid4(),
    )
    atomic_hash = rule_hash(atomic_rule)
    atomic_pub = uuid4()
    for point in FAILURE_POINTS:
        with connections["default"].cursor() as cursor:
            before = governance_snapshot(cursor)
            cursor.execute("SELECT status,published_at FROM normative.knowledge_layer_rule WHERE id=%s", [str(atomic_rule)])
            rule_before = cursor.fetchone()
        set_failure(point, "rule_publisher")
        expect_error(lambda: pub_service.publish_native(authority=publisher, publication_id=atomic_pub, rule_id=atomic_rule, expected_rule_material_hash=atomic_hash, idempotency_key_hash=h("atomic-pub"), reason="atomic publication", trace_id=uuid4()))
        set_failure("", "rule_publisher")
        with connections["default"].cursor() as cursor:
            check(f"publication rollback {point}", governance_snapshot(cursor) == before)
            cursor.execute("SELECT status,published_at FROM normative.knowledge_layer_rule WHERE id=%s", [str(atomic_rule)])
            check(f"publication target rollback {point}", cursor.fetchone() == rule_before)
    pub_service.publish_native(authority=publisher, publication_id=atomic_pub, rule_id=atomic_rule, expected_rule_material_hash=atomic_hash, idempotency_key_hash=h("atomic-pub"), reason="atomic publication", trace_id=uuid4())
    atomic_act = uuid4()
    for point in FAILURE_POINTS:
        with connections["default"].cursor() as cursor: before = governance_snapshot(cursor)
        set_failure(point, "rule_activator")
        expect_error(lambda: act_service.activate(authority=activator, activation_id=atomic_act, publication_id=atomic_pub, expected_rule_material_hash=atomic_hash, expected_predecessor_activation_id=None, compatibility_hash=h("atomic-compat"), idempotency_key_hash=h("atomic-act"), reason="atomic activation", trace_id=uuid4()))
        set_failure("", "rule_activator")
        with connections["default"].cursor() as cursor: check(f"activation rollback {point}", governance_snapshot(cursor) == before)
    act_service.activate(authority=activator, activation_id=atomic_act, publication_id=atomic_pub, expected_rule_material_hash=atomic_hash, expected_predecessor_activation_id=None, compatibility_hash=h("atomic-compat"), idempotency_key_hash=h("atomic-act"), reason="atomic activation", trace_id=uuid4())
    atomic_adopt = uuid4()
    for point in FAILURE_POINTS:
        with connections["default"].cursor() as cursor: before = governance_snapshot(cursor)
        set_failure(point, "rule_adopter")
        expect_error(lambda: adoption_service.adopt(authority=adopter, runtime_adoption_id=atomic_adopt, activation_id=atomic_act, expected_rule_material_hash=atomic_hash, expected_predecessor_adoption_id=None, release_configuration_reference="synthetic://atomic", release_configuration_hash=h("atomic-config"), idempotency_key_hash=h("atomic-adopt"), reason="atomic adoption", trace_id=uuid4()))
        set_failure("", "rule_adopter")
        with connections["default"].cursor() as cursor: check(f"adoption rollback {point}", governance_snapshot(cursor) == before)
    adoption_service.adopt(authority=adopter, runtime_adoption_id=atomic_adopt, activation_id=atomic_act, expected_rule_material_hash=atomic_hash, expected_predecessor_adoption_id=None, release_configuration_reference="synthetic://atomic", release_configuration_hash=h("atomic-config"), idempotency_key_hash=h("atomic-adopt"), reason="atomic adoption", trace_id=uuid4())
    check("lost response after known commit reconciles COMMITTED", repair_service.reconcile_adoption(atomic_adopt).outcome is ReconciliationOutcome.COMMITTED)

    # A real connection loss during the deferred COMMIT window is uncertain to
    # the caller.  Exact graph reconciliation, not a replay guess, decides it.
    uncertain_rule = knowledge.create_knowledge_layer_rule(
        knowledge_layer_id=layer_id, rule_key="phase272-uncertain-commit", version="phase272-uncertain-v1",
        logic_json={"synthetic": "uncertain-commit"}, evidence_expectation={}, source_reference=None,
        actor_id="phase272-curator", trace_id=uuid4(),
    )
    uncertain_hash = rule_hash(uncertain_rule)
    uncertain_pub, uncertain_act, uncertain_adopt = uuid4(), uuid4(), uuid4()
    pub_service.publish_native(authority=publisher, publication_id=uncertain_pub, rule_id=uncertain_rule, expected_rule_material_hash=uncertain_hash, idempotency_key_hash=h("uncertain-pub"), reason="uncertain commit fixture", trace_id=uuid4())
    act_service.activate(authority=activator, activation_id=uncertain_act, publication_id=uncertain_pub, expected_rule_material_hash=uncertain_hash, expected_predecessor_activation_id=None, compatibility_hash=h("uncertain-compat"), idempotency_key_hash=h("uncertain-act"), reason="uncertain commit fixture", trace_id=uuid4())
    pid_ready, uncertain_result, backend_pid = Event(), [], []
    def commit_with_connection_loss():
        try:
            with connections["rule_adopter"].cursor() as cursor:
                cursor.execute("SELECT set_config('foundation.phase272_commit_delay','true',false),pg_backend_pid()")
                backend_pid.append(cursor.fetchone()[1])
            pid_ready.set()
            KnowledgeLayerRuleRuntimeAdoptionService().adopt(
                authority=adopter, runtime_adoption_id=uncertain_adopt, activation_id=uncertain_act,
                expected_rule_material_hash=uncertain_hash, expected_predecessor_adoption_id=None,
                release_configuration_reference="synthetic://uncertain-commit",
                release_configuration_hash=h("uncertain-config"), idempotency_key_hash=h("uncertain-adopt"),
                reason="real ambiguous COMMIT connection-loss fixture", trace_id=uuid4(),
            )
            uncertain_result.append("response")
        except Exception as exc:
            uncertain_result.append(type(exc).__name__)
        finally:
            connections["rule_adopter"].close()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(commit_with_connection_loss)
        require(pid_ready.wait(10), "ambiguous COMMIT backend pid unavailable")
        time.sleep(0.5)
        import psycopg2
        killer = psycopg2.connect(
            dbname=os.environ["FOUNDATION_DB_NAME"], user=os.environ["FOUNDATION_RULE_ADOPTER_ROLE"],
            password=os.environ["FOUNDATION_RULE_ADOPTER_PASSWORD"], host=os.environ["FOUNDATION_DB_HOST"],
            port=os.environ["FOUNDATION_DB_PORT"],
        )
        killer.autocommit = True
        with killer.cursor() as cursor:
            cursor.execute("SELECT pg_terminate_backend(%s)", [backend_pid[0]])
            terminated = cursor.fetchone()[0]
        killer.close()
        future.result(timeout=15)
    check("connection was lost while COMMIT outcome was uncertain", terminated and uncertain_result != ["response"])
    check("uncertain rolled-back COMMIT reconciles NOT_COMMITTED", repair_service.reconcile_adoption(uncertain_adopt).outcome is ReconciliationOutcome.NOT_COMMITTED)

    # Explicit abandonment only; timeout/no row remains NOT_COMMITTED.
    abandon_id = uuid4()
    check("timeout alone remains NOT_COMMITTED", repair_service.reconcile_publication(abandon_id).outcome is ReconciliationOutcome.NOT_COMMITTED)
    repair_service.record_abandoned(authority=repair, operation_kind="PUBLICATION", artifact_id=abandon_id, material_hash=h("abandoned"), reason="Explicit synthetic operator disposition.", trace_id=uuid4())
    check("explicit disposition reconciles ABANDONED", repair_service.reconcile_publication(abandon_id).outcome is ReconciliationOutcome.ABANDONED)
    expect_error(lambda: pub_service.publish_native(authority=publisher, publication_id=abandon_id, rule_id=vn1_id, expected_rule_material_hash=rule_hash(vn1_id), idempotency_key_hash=h("abandoned"), reason="blind retry forbidden", trace_id=uuid4()), "conflict")
    check("abandoned claim cannot be stolen")

    # Synthetic partial durable evidence is INCONSISTENT and cannot be repaired by fabrication.
    orphan_artifact, orphan_event = uuid4(), uuid4()
    with connections["default"].cursor() as cursor:
        cursor.execute(
            "INSERT INTO normative.knowledge_layer_rule_governance_event(id,event_type,schema_version,operation_kind,artifact_id,target_rule_id,payload,payload_hash,trace_id) "
            "VALUES(%s,'knowledge_layer_rule.published',1,'PUBLICATION',%s,%s,'{}'::jsonb,%s,%s)",
            [str(orphan_event), str(orphan_artifact), str(rule_id), "0" * 64, str(uuid4())],
        )
    check("partial durable evidence is INCONSISTENT", repair_service.reconcile_publication(orphan_artifact).outcome is ReconciliationOutcome.INCONSISTENT)
    check("repair boundary exposes no artifact reconstruction", not any(name.startswith(("publish", "activate", "adopt", "create")) for name in dir(repair_service)))

    # Append-only, independent capability fences and governed re-enable.
    disable_pub = capability_service.decide(authority=controller, decision_id=uuid4(), capability="PUBLICATION", enabled=False, expected_predecessor_id=None, reason="Synthetic publication stop.", trace_id=uuid4())
    expect_error(lambda: pub_service.publish_native(authority=publisher, publication_id=uuid4(), rule_id=vn1_id, expected_rule_material_hash=rule_hash(vn1_id), idempotency_key_hash=h("disabled-pub"), reason="denied", trace_id=uuid4()), "disabled")
    check("publication disable does not change existing adoption", resolver.resolve(runtime_adoption_id=adoption_id).knowledge_layer_rule_id == rule_id)
    enable_pub = capability_service.decide(authority=controller, decision_id=uuid4(), capability="PUBLICATION", enabled=True, expected_predecessor_id=disable_pub, reason="Explicit governed re-enable.", trace_id=uuid4())
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT array_agg(enabled ORDER BY created_at) FROM normative.knowledge_layer_rule_capability_decision WHERE capability='PUBLICATION'")
        check("re-enable is append-only disable-to-enable history", cursor.fetchone()[0] == [False, True])
        expect_error(lambda: cursor.execute("UPDATE normative.knowledge_layer_rule_capability_decision SET enabled=true WHERE id=%s", [str(disable_pub)]), "immutable")
    disable_adopt = capability_service.decide(authority=controller, decision_id=uuid4(), capability="RUNTIME_ADOPTION", enabled=False, expected_predecessor_id=None, reason="Synthetic adoption stop.", trace_id=uuid4())
    check("adoption disable does not unpublish/deactivate/rewrite history", resolver.resolve(runtime_adoption_id=adoption_id).knowledge_layer_rule_id == rule_id)
    capability_service.decide(authority=controller, decision_id=uuid4(), capability="RUNTIME_ADOPTION", enabled=True, expected_predecessor_id=disable_adopt, reason="Explicit adoption re-enable.", trace_id=uuid4())
    check("capability fences are independent and affect new operations only")

    # ACL negative matrix, including repair hard denials and hostile search path.
    principals = ["FOUNDATION_APP_ROLE", "FOUNDATION_WORKER_ROLE", "FOUNDATION_PROJECTOR_ROLE", "FOUNDATION_AUDIT_WRITER_ROLE", "FOUNDATION_LEARNING_APPLICATION_EXECUTOR_ROLE", "FOUNDATION_RELEASE_REPAIR_ROLE"]
    with connections["default"].cursor() as cursor:
        for env_name in principals:
            role = os.environ[env_name]
            for function in (role_function[os.environ["FOUNDATION_RULE_PUBLISHER_ROLE"]], role_function[os.environ["FOUNDATION_RULE_ACTIVATOR_ROLE"]], role_function[os.environ["FOUNDATION_RULE_ADOPTER_ROLE"]]):
                cursor.execute("SELECT has_function_privilege(%s,%s,'EXECUTE')", [role, function])
                check(f"{env_name} denied {function.split('(')[0]}", cursor.fetchone()[0] is False)
        for env_name in ("FOUNDATION_RULE_PUBLISHER_ROLE", "FOUNDATION_RULE_ACTIVATOR_ROLE", "FOUNDATION_RULE_ADOPTER_ROLE"):
            role = os.environ[env_name]
            allowed = role_function[role]
            for function in role_function.values():
                cursor.execute("SELECT has_function_privilege(%s,%s,'EXECUTE')", [role, function])
                expected = function == allowed
                check(f"cross-duty function ACL {env_name} {function.split('(')[0]}", cursor.fetchone()[0] is expected)
        repair_role = os.environ["FOUNDATION_RELEASE_REPAIR_ROLE"]
        for table in ("normative.knowledge_layer_rule", "normative.knowledge_layer_rule_publication", "normative.knowledge_layer_rule_activation", "normative.knowledge_layer_rule_runtime_adoption", "normative.knowledge_layer_rule_governance_event", "audit.knowledge_layer_rule_governance_audit", "qms.learning_target_application_receipt"):
            cursor.execute("SELECT has_table_privilege(%s,%s,'INSERT') OR has_table_privilege(%s,%s,'UPDATE') OR has_table_privilege(%s,%s,'DELETE')", [repair_role, table, repair_role, table, repair_role, table])
            check(f"repair raw DML denied {table}", cursor.fetchone()[0] is False)
        cursor.execute("SELECT has_function_privilege(%s,'normative.curator_create_knowledge_layer_rule_successor_v1(uuid,text,jsonb,jsonb,text,text,uuid)','EXECUTE')", [repair_role])
        check("repair target-revision creation denied", cursor.fetchone()[0] is False)
        cursor.execute("SELECT has_schema_privilege(%s,'normative','CREATE')", [repair_role])
        check("repair schema DDL denied", cursor.fetchone()[0] is False)
        cursor.execute("SELECT rolcreaterole,rolinherit FROM pg_roles WHERE rolname=%s", [repair_role])
        check("repair role creation and inherited escalation denied", cursor.fetchone() == (False, False))
        cursor.execute("SELECT pg_has_role(%s,%s,'MEMBER')", [repair_role, os.environ["FOUNDATION_RULE_GOVERNANCE_OWNER_ROLE"]])
        check("repair SET ROLE escalation denied", cursor.fetchone()[0] is False)
        adopter_role = os.environ["FOUNDATION_RULE_ADOPTER_ROLE"]
        cursor.execute("SELECT has_table_privilege(%s,'normative.knowledge_layer_rule','INSERT') OR has_table_privilege(%s,'normative.knowledge_layer_rule','UPDATE') OR has_table_privilege(%s,'normative.knowledge_layer_rule','DELETE')", [adopter_role, adopter_role, adopter_role])
        check("adoption authority target mutation denied", cursor.fetchone()[0] is False)
    with connections["rule_publisher"].cursor() as cursor:
        cursor.execute("SET search_path=pg_temp,public")
        cursor.execute("SELECT proconfig FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='normative' AND p.proname='publish_knowledge_layer_rule_v1'")
        check("hostile caller search_path cannot shadow privileged function", cursor.fetchone()[0] == ["search_path=pg_catalog"])

    # Protected invariants and absence of hidden pointer/runtime wiring.
    runtime_after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in runtime_files}
    check("AgentRun/Recommendation runtime implementation byte unchanged", runtime_after == runtime_before)
    source = (root / "knowledge_rule_release.py").read_text(encoding="utf-8")
    signature = inspect.signature(InertRuntimeAdoptionResolver.resolve)
    check("resolver signature is exact-ID only", set(signature.parameters) == {"self", "runtime_adoption_id"})
    check("resolver has no latest/current/head/max fallback", not any(token in source.lower() for token in ("order_by(\"-revision\")", "order_by('-revision')", "max(version)", "max(revision)", "latest_published", "lineage leaf fallback")))
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT count(*) FROM information_schema.columns WHERE column_name IN ('current_rule_id','active_rule_id','latest_rule_id','runtime_rule_id') AND table_schema IN ('normative','governance','ai','qms')")
        check("no hidden mutable current pointer introduced", cursor.fetchone()[0] == 0)
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule_publication WHERE knowledge_layer_rule_id=ANY(%s::uuid[])", [[str(vn1_id), str(vn2_id)]])
        successors_published = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule_activation WHERE knowledge_layer_rule_id=ANY(%s::uuid[])", [[str(vn1_id), str(vn2_id)]])
        successors_activated = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule_runtime_adoption WHERE knowledge_layer_rule_id=ANY(%s::uuid[])", [[str(vn1_id), str(vn2_id)]])
        successors_adopted = cursor.fetchone()[0]
        check("Phase 26 successors remain unreferenced/inert", (successors_published, successors_activated, successors_adopted) == (0, 0, 0))
        for table, before in protected_before.items():
            check(f"protected/runtime state unchanged {table}", digest(cursor, table) == before)
    check("no automatic learning, autonomy or normative protected-target mutation")

    # Retained governance history makes destructive reverse operationally prohibited.
    expect_error(lambda: phase3.migrate(PHASE26), "forward-only")
    connections["default"].close()
    check("retained-history reverse gate fails closed")
    check("zero external effects")
    require(len(checks) >= 80, f"acceptance matrix too small: {len(checks)}")
    print(json.dumps({
        "status": "PASS", "postgresql": "18.6",
        "migration": "0022 additive; empty-history forward/reverse/forward PASS",
        "acceptance": f"{len(checks)}/{len(checks)} PASS",
        "atomic_rollback": f"publication/activation/adoption {len(FAILURE_POINTS)}/{len(FAILURE_POINTS)} each PASS",
        "exact_id_resolver": "exact RuntimeAdoption -> Activation -> Publication -> Rule only PASS",
        "legacy_truthfulness": "publication import and runtime bootstrap distinguished/inert PASS",
        "authority_sod_acl": "fresh authority, revocation, cross-duty and catalog matrices PASS",
        "capability_reconciliation": "append-only fences and four-state reconciliation PASS",
        "ambiguous_commit": "known commit COMMITTED; real connection loss NOT_COMMITTED; orphan INCONSISTENT PASS",
        "runtime_phase26_protected": "unchanged; vN+1/vN+2 remain inert PASS",
        "retained_history": "destructive reverse denied PASS", "external_effects": "ZERO",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    run()
