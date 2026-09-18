"""Phase 28.2 retained evidence and inert publication-preflight contracts.

Nothing in this module writes a KnowledgeLayerRule, Publication, Activation or
RuntimeAdoption.  The only result is a content-addressed eligibility record for
a later, separately authorized gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pathlib import Path
import re
from threading import RLock
from types import MappingProxyType
from typing import Any, Callable, Mapping
from uuid import UUID


CANONICALIZATION_VERSION = "iso-smart-retained-evidence-canonical-json-v1"
FINGERPRINT_VERSION = "iso-smart-knowledge-layer-rule-substantive-fingerprint-v1"
SOURCE_SCHEME = "iso-smart-synthetic-poc-source-ref-v1"
SOURCE_NAMESPACE = "iso-smart/publication-poc-fixture/v1"
TARGET_TYPE = "KnowledgeLayerRule"
OPERATION_ID = "learning.knowledge_layer_rule.source_reference.correct"
OPERATION_VERSION = "v1"
PUBLICATION_PERMISSION = "qms.knowledge_layer_rule.publish"
PHASE283_CANDIDATE_CLASSIFICATION = "NEW_DETERMINISTIC_SYNTHETIC_PUBLICATION_POC_LINEAGE"
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
LOCATOR_RE = re.compile(r"^fixture/element/[A-Za-z0-9._~-]+$")
SOURCE_REFERENCE_RE = re.compile(
    rf"^{re.escape(SOURCE_SCHEME)}:([0-9a-f-]{{36}}):([0-9a-f]{{64}}):(fixture/element/[A-Za-z0-9._~-]+)$"
)


class EvidenceError(ValueError):
    """Retained evidence is absent, malformed, inconsistent or untrusted."""


class PreflightConflict(RuntimeError):
    """An immutable identity or lineage already has different material."""


class CandidateEvidenceState(str, Enum):
    NOT_YET_CREATED = "NOT_YET_CREATED"
    CREATED_AND_RETAINED = "CREATED_AND_RETAINED"
    DISPOSED_WITH_RETAINED_EVIDENCE = "DISPOSED_WITH_RETAINED_EVIDENCE"
    PERMANENTLY_UNAVAILABLE = "PERMANENTLY_UNAVAILABLE"


class ReconciliationOutcome(str, Enum):
    COMMITTED = "COMMITTED"
    NOT_COMMITTED = "NOT_COMMITTED"
    ABANDONED = "ABANDONED"
    INCONSISTENT = "INCONSISTENT"


def canonical_json(value: Any) -> str:
    """Canonical UTF-8 JSON: sorted object keys, compact separators, no NaN."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def material_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require_hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not HASH_RE.fullmatch(value):
        raise EvidenceError(f"{field} must be an exact lowercase SHA-256")
    return value


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{field} is required")
    return value


def _require_uuid(value: Any, field: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise EvidenceError(f"{field} must be an exact UUID") from exc


def _without_hash(document: Mapping[str, Any], hash_field: str) -> dict[str, Any]:
    return {key: value for key, value in document.items() if key != hash_field}


def _timestamp(value: Any, field: str) -> datetime:
    _require_text(value, field)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise EvidenceError(f"{field} must carry an offset")
    return parsed


def load_and_verify_synthetic_source_manifest(path: Path) -> Mapping[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    required_classification = [
        "NON_OFFICIAL_TEST_FIXTURE", "NON_NORMATIVE", "NON_LICENSED", "TEST_ONLY", "NON_PRODUCTION"
    ]
    exact = {
        "manifest_schema": "synthetic-knowledge-layer-rule-publication-source-manifest/v1",
        "synthetic_source_namespace": SOURCE_NAMESPACE,
        "source_classification": "RETAINED_DETERMINISTIC_SYNTHETIC_FIXTURE",
        "authoritative": False,
        "normative": False,
        "licensed_content_present": False,
        "phase26_continuity_claim": False,
        "locator_scheme": SOURCE_SCHEME,
        "source_reference_scheme_version": "v1",
        "generator_contract_version": "iso-smart-synthetic-publication-source-generator/v1",
        "canonicalization_version": CANONICALIZATION_VERSION,
        "allowed_operation": f"{OPERATION_ID}/{OPERATION_VERSION}",
    }
    for field, expected in exact.items():
        if document.get(field) != expected:
            raise EvidenceError(f"synthetic source manifest {field} is not exact")
    if document.get("closed_classification") != required_classification:
        raise EvidenceError("synthetic source closed classification is not exact")
    _require_uuid(document.get("deterministic_source_id"), "deterministic_source_id")
    _require_text(document.get("purpose"), "purpose")
    _require_text(document.get("provenance_statement"), "provenance_statement")
    if document.get("locator_grammar") != f"{SOURCE_SCHEME}:<source-uuid>:<source-material-sha256>:fixture/element/<token>":
        raise EvidenceError("synthetic locator grammar is not exact")
    prohibited = set(document.get("prohibited_uses", []))
    if not {"publication", "activation", "runtime_adoption", "phase26_recovery", "authoritative_citation"} <= prohibited:
        raise EvidenceError("synthetic source prohibited uses are incomplete")
    source_material = document.get("source_material")
    if not isinstance(source_material, str) or "ISO " in source_material or "shall" in source_material.lower():
        raise EvidenceError("synthetic material is absent or could be confused with normative content")
    if hashlib.sha256(source_material.encode("utf-8")).hexdigest() != _require_hash(
        document.get("source_material_sha256"), "source_material_sha256"
    ):
        raise EvidenceError("synthetic source material hash mismatch")
    if material_hash(_without_hash(document, "manifest_material_hash")) != _require_hash(
        document.get("manifest_material_hash"), "manifest_material_hash"
    ):
        raise EvidenceError("synthetic source manifest material hash mismatch")
    return MappingProxyType(json.loads(canonical_json(document)))


def phase26_semantic_fingerprint(rule: Mapping[str, Any]) -> str:
    """Python verification vector matching foundation_0021_rule_semantic_hash fields."""
    fields = (
        "knowledge_layer_id", "knowledge_layer_type", "standard_id", "standard_edition_id",
        "standard_edition_source_hash", "lineage_id", "rule_key", "logic_json",
        "evidence_expectation", "certifiability_classification", "source_reference_scheme",
    )
    missing = [field for field in fields if field not in rule]
    if missing:
        raise EvidenceError(f"semantic fingerprint fields missing: {','.join(missing)}")
    payload = {field: rule[field] for field in fields}
    payload.update(fingerprint_version=FINGERPRINT_VERSION, target_type=TARGET_TYPE)
    return material_hash(payload)


def phase272_lifecycle_hash(rule: Mapping[str, Any]) -> str:
    fields = ("knowledge_layer_id", "rule_key", "logic_json", "evidence_expectation", "certifiability_classification")
    if any(field not in rule for field in fields):
        raise EvidenceError("Phase 27.2 lifecycle hash fields are incomplete")
    return material_hash({field: rule[field] for field in fields})


def full_rule_material_hash(rule: Mapping[str, Any]) -> str:
    fields = (
        "id", "knowledge_layer_id", "lineage_id", "rule_key", "version", "previous_revision_id",
        "logic_json", "evidence_expectation", "source_reference", "certifiability_classification",
    )
    if any(field not in rule for field in fields):
        raise EvidenceError("full rule material fields are incomplete")
    return material_hash({field: rule[field] for field in fields})


_CHAIN_FIELDS = (
    "learning_signal", "learning_proposal_revision", "canonical_delta", "selected_reviews",
    "decision", "application_authorization", "application_receipt", "domain_events",
    "transactional_outbox", "immutable_audits", "policies",
)


def _verify_reference(reference: Mapping[str, Any], field: str) -> None:
    _require_uuid(reference.get("id"), f"{field}.id")
    _require_hash(reference.get("material_hash"), f"{field}.material_hash")


def verify_candidate_evidence(document: Mapping[str, Any]) -> Mapping[str, Any]:
    """Verify a retained manifest without reconstructing anything from target state."""
    if document.get("manifest_schema") != "governed-target-application-evidence-manifest/v1":
        raise EvidenceError("unknown candidate evidence schema")
    state = CandidateEvidenceState(document.get("evidence_state"))
    if state is CandidateEvidenceState.PERMANENTLY_UNAVAILABLE:
        if document.get("candidate") or document.get("governance_chain"):
            raise EvidenceError("permanently unavailable evidence cannot accept caller-supplied historical IDs")
        if document.get("unavailable_identity") != "phase26-disposed-ephemeral-publication-candidate":
            raise EvidenceError("unknown permanently unavailable classification")
    elif state is CandidateEvidenceState.NOT_YET_CREATED:
        if document.get("candidate") or document.get("governance_chain"):
            raise EvidenceError("not-yet-created evidence cannot contain candidate history")
    else:
        exact = {
            "target_type": TARGET_TYPE,
            "operation_id": OPERATION_ID,
            "operation_version": OPERATION_VERSION,
            "fingerprint_version": FINGERPRINT_VERSION,
            "generator_contract_version": "governed-target-application-evidence-export/v1",
        }
        for field, expected in exact.items():
            if document.get(field) != expected:
                raise EvidenceError(f"candidate evidence {field} is not exact")
        _require_uuid(document.get("run_id"), "run_id")
        if document.get("source_classification") != "RETAINED_DETERMINISTIC_SYNTHETIC_FIXTURE":
            raise EvidenceError("candidate source classification is not the retained synthetic branch")
        if document.get("phase26_continuity_claim") is not False:
            raise EvidenceError("Phase 26 identity continuity is forbidden")
        candidate = document.get("candidate")
        if not isinstance(candidate, dict):
            raise EvidenceError("candidate evidence is required")
        for field in ("id", "knowledge_layer_id", "lineage_id", "predecessor_rule_id"):
            _require_uuid(candidate.get(field), f"candidate.{field}")
        _require_text(candidate.get("version"), "candidate.version")
        for field in ("full_material_hash", "semantic_fingerprint", "lifecycle_hash"):
            _require_hash(candidate.get(field), f"candidate.{field}")
        if candidate["semantic_fingerprint"] == candidate["lifecycle_hash"]:
            raise EvidenceError("Phase 26 fingerprint and Phase 27.2 lifecycle hash must remain distinct")
        rule_material = document.get("canonical_rule_material")
        if not isinstance(rule_material, dict):
            raise EvidenceError("canonical rule material is required; hashes alone cannot reconstruct evidence")
        if full_rule_material_hash(rule_material) != candidate["full_material_hash"]:
            raise EvidenceError("full candidate material hash mismatch")
        if phase26_semantic_fingerprint(rule_material) != candidate["semantic_fingerprint"]:
            raise EvidenceError("Phase 26-compatible semantic fingerprint mismatch")
        if phase272_lifecycle_hash(rule_material) != candidate["lifecycle_hash"]:
            raise EvidenceError("Phase 27.2 lifecycle hash mismatch")
        if any(rule_material.get(key) != candidate[value] for key, value in (
            ("id", "id"), ("knowledge_layer_id", "knowledge_layer_id"),
            ("lineage_id", "lineage_id"), ("previous_revision_id", "predecessor_rule_id"),
            ("version", "version"),
        )):
            raise EvidenceError("canonical rule identity does not match candidate identity")
        source = document.get("source")
        if not isinstance(source, dict):
            raise EvidenceError("source evidence is required")
        _require_uuid(source.get("manifest_id"), "source.manifest_id")
        _require_hash(source.get("manifest_hash"), "source.manifest_hash")
        _require_hash(source.get("reference_hash"), "source.reference_hash")
        match = SOURCE_REFERENCE_RE.fullmatch(_require_text(source.get("reference"), "source.reference"))
        if not match or match.group(2) != _require_hash(source.get("material_hash"), "source.material_hash"):
            raise EvidenceError("source reference namespace or material hash mismatch")
        if rule_material["source_reference"] != source["reference"] or rule_material["source_reference_scheme"] != SOURCE_SCHEME:
            raise EvidenceError("canonical rule source is not exactly bound to retained source evidence")
        if rule_material["standard_edition_source_hash"] != source["material_hash"]:
            raise EvidenceError("semantic source hash is not bound to retained source material")
        chain = document.get("governance_chain")
        if not isinstance(chain, dict) or any(field not in chain for field in _CHAIN_FIELDS):
            raise EvidenceError("complete governance chain is required")
        for field in _CHAIN_FIELDS:
            value = chain[field]
            if field in {"selected_reviews", "domain_events", "transactional_outbox", "immutable_audits", "policies"}:
                if not isinstance(value, list) or not value:
                    raise EvidenceError(f"{field} must contain retained references")
                for index, reference in enumerate(value):
                    _verify_reference(reference, f"{field}[{index}]")
            else:
                _verify_reference(value, field)
        signal = chain["learning_signal"]
        proposal = chain["learning_proposal_revision"]
        delta = chain["canonical_delta"]
        decision = chain["decision"]
        authorization = chain["application_authorization"]
        receipt = chain["application_receipt"]
        common = {
            "target_rule_id": candidate["predecessor_rule_id"],
            "operation_id": OPERATION_ID,
            "operation_version": OPERATION_VERSION,
        }
        for name, reference in (("learning_signal", signal), ("learning_proposal_revision", proposal),
                                ("canonical_delta", delta), ("application_authorization", authorization),
                                ("application_receipt", receipt)):
            if any(reference.get(key) != value for key, value in common.items()):
                raise EvidenceError(f"{name} is not bound to the exact target operation")
        if proposal.get("learning_signal_id") != signal["id"]:
            raise EvidenceError("Proposal does not reference the exact LearningSignal")
        if delta.get("proposal_revision_id") != proposal["id"]:
            raise EvidenceError("CanonicalDelta does not reference the exact Proposal revision")
        for review in chain["selected_reviews"]:
            if (review.get("proposal_revision_id") != proposal["id"] or
                    review.get("canonical_delta_id") != delta["id"] or
                    review.get("outcome") != "APPROVE" or review.get("selected") is not True):
                raise EvidenceError("selected Review is not exact approved evidence")
        if (decision.get("proposal_revision_id") != proposal["id"] or
                decision.get("canonical_delta_id") != delta["id"] or decision.get("outcome") != "APPROVED"):
            raise EvidenceError("Decision is not exact approval evidence")
        if (authorization.get("decision_id") != decision["id"] or authorization.get("status") != "VALID"):
            raise EvidenceError("Application Authorization is stale, wrong or invalid")
        if (receipt.get("proposal_revision_id") != proposal["id"] or
                receipt.get("canonical_delta_id") != delta["id"] or
                receipt.get("decision_id") != decision["id"] or
                receipt.get("application_authorization_id") != authorization["id"] or
                receipt.get("result_rule_id") != candidate["id"] or
                receipt.get("result_material_hash") != candidate["full_material_hash"] or
                receipt.get("result_semantic_fingerprint") != candidate["semantic_fingerprint"]):
            raise EvidenceError("application Receipt does not bind the exact governance result")
        event_ids = {reference["id"] for reference in chain["domain_events"]}
        if any(event.get("receipt_id") != receipt["id"] or event.get("result_rule_id") != candidate["id"]
               for event in chain["domain_events"]):
            raise EvidenceError("DomainEvent references are not bound to the application Receipt")
        if any(outbox.get("event_id") not in event_ids for outbox in chain["transactional_outbox"]):
            raise EvidenceError("TransactionalOutbox does not reference a retained DomainEvent")
        if any(audit.get("receipt_id") != receipt["id"] for audit in chain["immutable_audits"]):
            raise EvidenceError("ImmutableAuditLog does not reference the exact Receipt")
        if any(not policy.get("policy_id") or not policy.get("version") for policy in chain["policies"]):
            raise EvidenceError("policy ID/version/hash evidence is incomplete")
        required_receipt = {
            "successful": True, "external_effects": False, "runtime_effect_changed": False,
            "result_published": False, "result_status": "draft",
        }
        if any(receipt.get(key) != value for key, value in required_receipt.items()):
            raise EvidenceError("application Receipt is not exact inert success evidence")
        _require_uuid(document.get("trace_id"), "trace_id")
        created_at = _timestamp(document.get("created_at"), "created_at")
        exported_at = _timestamp(document.get("exported_at"), "exported_at")
        retained_at = _timestamp(document.get("retained_at"), "retained_at")
        if not created_at <= exported_at <= retained_at:
            raise EvidenceError("candidate evidence export/retention chronology is invalid")
        if document.get("retention_integrity_verified") is not True:
            raise EvidenceError("retention before teardown was not integrity-verified")
        if state is CandidateEvidenceState.DISPOSED_WITH_RETAINED_EVIDENCE:
            disposed_at = _timestamp(document.get("disposed_at"), "disposed_at")
            if retained_at > disposed_at:
                raise EvidenceError("evidence was not retained before destructive teardown")
    if document.get("canonicalization_version") != CANONICALIZATION_VERSION:
        raise EvidenceError("candidate evidence canonicalization is not exact")
    expected = material_hash(_without_hash(document, "manifest_material_hash"))
    if expected != _require_hash(document.get("manifest_material_hash"), "manifest_material_hash"):
        raise EvidenceError("candidate evidence manifest material hash mismatch")
    return MappingProxyType(json.loads(canonical_json(document)))


def _verify_exact_material_reference(reference: Mapping[str, Any], field: str) -> None:
    """Require a reference to carry the exact sanitized material it hashes."""
    _verify_reference(reference, field)
    exact_material = reference.get("material")
    if not isinstance(exact_material, dict):
        raise EvidenceError(f"{field}.material is required")
    if str(exact_material.get("id")) != reference["id"]:
        raise EvidenceError(f"{field}.material identity mismatch")
    if material_hash(exact_material) != reference["material_hash"]:
        raise EvidenceError(f"{field}.material hash mismatch")


def verify_phase283_candidate_evidence(
    document: Mapping[str, Any], *, source_manifest: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    """Verify the complete Phase 28.3 export without access to PostgreSQL."""
    verified = verify_candidate_evidence(document)
    if verified.get("candidate_classification") != PHASE283_CANDIDATE_CLASSIFICATION:
        raise EvidenceError("candidate is not the independent Phase 28.3 synthetic lineage")
    if verified.get("evidence_state") != CandidateEvidenceState.CREATED_AND_RETAINED.value:
        raise EvidenceError("the immutable creation manifest must remain CREATED_AND_RETAINED")
    if verified.get("integrity_verified") is not True or verified.get("live_graph_verified") is not True:
        raise EvidenceError("live graph and retained integrity must be verified before teardown")
    if verified.get("teardown_intent") != "DESTROY_COMPLETE_EPHEMERAL_POSTGRESQL_ENVIRONMENT":
        raise EvidenceError("exact teardown intent is missing")

    root = verified.get("root")
    root_material = verified.get("canonical_root_material")
    candidate = verified["candidate"]
    candidate_material = verified["canonical_rule_material"]
    if not isinstance(root, dict) or not isinstance(root_material, dict):
        raise EvidenceError("exact root identity and canonical material are required")
    for field in ("id", "knowledge_layer_id", "lineage_id"):
        _require_uuid(root.get(field), f"root.{field}")
    for field in ("full_material_hash", "semantic_fingerprint", "lifecycle_hash"):
        _require_hash(root.get(field), f"root.{field}")
    if root_material.get("previous_revision_id") is not None:
        raise EvidenceError("synthetic root must not fabricate a predecessor")
    if (root_material.get("id") != root["id"] or
            root_material.get("lineage_id") != root["lineage_id"] or
            candidate["predecessor_rule_id"] != root["id"] or
            candidate["lineage_id"] != root["lineage_id"]):
        raise EvidenceError("root/candidate predecessor lineage is not exact")
    if full_rule_material_hash(root_material) != root["full_material_hash"]:
        raise EvidenceError("root full material hash mismatch")
    if phase26_semantic_fingerprint(root_material) != root["semantic_fingerprint"]:
        raise EvidenceError("root semantic fingerprint mismatch")
    if phase272_lifecycle_hash(root_material) != root["lifecycle_hash"]:
        raise EvidenceError("root lifecycle hash mismatch")
    if root["semantic_fingerprint"] != candidate["semantic_fingerprint"]:
        raise EvidenceError("locator correction changed substantive semantics")
    if root["lifecycle_hash"] != candidate["lifecycle_hash"]:
        raise EvidenceError("locator correction changed lifecycle material")
    if root["full_material_hash"] == candidate["full_material_hash"]:
        raise EvidenceError("root and candidate full material hashes must differ")

    source = verified["source"]
    if source.get("reference_before") != root_material.get("source_reference"):
        raise EvidenceError("root source locator is not retained exactly")
    if source.get("reference_after") != candidate_material.get("source_reference"):
        raise EvidenceError("candidate source locator is not retained exactly")
    for name in ("reference_before", "reference_after"):
        match = SOURCE_REFERENCE_RE.fullmatch(_require_text(source.get(name), f"source.{name}"))
        if not match or match.group(1) != source["manifest_id"] or match.group(2) != source["material_hash"]:
            raise EvidenceError(f"source.{name} is outside the retained synthetic namespace")
    if source["reference_before"] == source["reference_after"]:
        raise EvidenceError("source-reference correction must change the locator")
    if hashlib.sha256(source["reference_before"].encode()).hexdigest() != _require_hash(
        source.get("reference_before_hash"), "source.reference_before_hash"
    ):
        raise EvidenceError("root source-reference hash mismatch")
    if hashlib.sha256(source["reference_after"].encode()).hexdigest() != source["reference_hash"]:
        raise EvidenceError("candidate source-reference hash mismatch")
    if source_manifest is not None:
        if source["manifest_id"] != source_manifest.get("deterministic_source_id"):
            raise EvidenceError("source manifest identity mismatch")
        if source["manifest_hash"] != source_manifest.get("manifest_material_hash"):
            raise EvidenceError("source manifest material hash mismatch")
        if source["material_hash"] != source_manifest.get("source_material_sha256"):
            raise EvidenceError("source bytes hash mismatch")

    chain = verified["governance_chain"]
    for field in _CHAIN_FIELDS:
        value = chain[field]
        if isinstance(value, list):
            for index, reference in enumerate(value):
                _verify_exact_material_reference(reference, f"{field}[{index}]")
        else:
            _verify_exact_material_reference(value, field)

    leaf = verified.get("current_leaf_proof")
    if not isinstance(leaf, dict) or leaf.get("leaf_ids") != [candidate["id"]] or leaf.get("unique") is not True:
        raise EvidenceError("retained current-leaf proof is not the exact candidate singleton")
    if leaf.get("lineage_id") != candidate["lineage_id"] or leaf.get("candidate_version") != candidate["version"]:
        raise EvidenceError("retained current-leaf identity mismatch")

    curator = verified.get("curator_evidence")
    publisher = verified.get("future_publisher_authority")
    roles = verified.get("role_actor_ids")
    if not isinstance(curator, dict) or not isinstance(publisher, dict) or not isinstance(roles, dict):
        raise EvidenceError("curator, future publisher, and actor SOD evidence are required")
    _verify_exact_material_reference(curator, "curator_evidence")
    _verify_exact_material_reference(publisher, "future_publisher_authority")
    required_roles = {
        "proposer", "reviewer", "proposal_approver", "application_authorizer",
        "application_executor", "curator", "publisher", "activator", "adopter",
    }
    if set(roles) != required_roles:
        raise EvidenceError("actor-level separation evidence is incomplete")
    normalized_roles = {key: _require_uuid(value, f"role_actor_ids.{key}") for key, value in roles.items()}
    if len(set(normalized_roles.values())) != len(normalized_roles):
        raise EvidenceError("Phase 28.3 requires pairwise-distinct synthetic actors")
    if curator["material"].get("actor_external_id") != roles["curator"]:
        raise EvidenceError("curator actor does not match SOD evidence")
    if publisher["material"].get("actor_external_id") != roles["publisher"]:
        raise EvidenceError("future publisher actor does not match SOD evidence")
    if publisher["material"].get("authority_type") != "PUBLICATION_POC_ELIGIBILITY_AUTHORITY":
        raise EvidenceError("future authority must remain non-executing POC eligibility only")
    if publisher["material"].get("publication_invoked") is not False:
        raise EvidenceError("future publisher evidence cannot execute publication")

    effects = verified.get("zero_effects")
    expected_zero = {
        "publication_rows": 0, "activation_rows": 0, "runtime_adoption_rows": 0,
        "publication_events": 0, "activation_events": 0, "runtime_adoption_events": 0,
    }
    if not isinstance(effects, dict) or any(effects.get(key) != value for key, value in expected_zero.items()):
        raise EvidenceError("zero publication/activation/adoption evidence is incomplete")
    return verified


def verify_phase283_disposition(
    document: Mapping[str, Any], *, created_manifest: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Verify the append-only post-teardown disposition record."""
    if document.get("disposition_schema") != "governed-target-application-evidence-disposition/v1":
        raise EvidenceError("unknown Phase 28.3 disposition schema")
    if document.get("evidence_state") != CandidateEvidenceState.DISPOSED_WITH_RETAINED_EVIDENCE.value:
        raise EvidenceError("disposition state is not exact")
    if document.get("created_manifest_hash") != created_manifest.get("manifest_material_hash"):
        raise EvidenceError("disposition does not bind the immutable creation manifest")
    _require_uuid(document.get("run_id"), "disposition.run_id")
    if document["run_id"] != created_manifest.get("run_id"):
        raise EvidenceError("disposition run identity mismatch")
    disposed_at = _timestamp(document.get("disposed_at"), "disposed_at")
    if disposed_at < _timestamp(created_manifest.get("retained_at"), "retained_at"):
        raise EvidenceError("teardown predates evidence retention")
    teardown = document.get("teardown_evidence")
    verification = document.get("post_teardown_verification")
    if not isinstance(teardown, dict) or not all(teardown.get(key) is True for key in (
        "database_absent", "roles_absent", "container_absent", "volume_absent", "temp_absent",
    )):
        raise EvidenceError("complete teardown absence evidence is required")
    if material_hash(teardown) != _require_hash(document.get("teardown_evidence_hash"), "teardown_evidence_hash"):
        raise EvidenceError("teardown evidence hash mismatch")
    if not isinstance(verification, dict) or verification.get("manifest_verified") is not True or verification.get("preflight_outcome") != "ELIGIBLE_FOR_LATER_PUBLICATION_GATE" or verification.get("database_reconstructed") is not False:
        raise EvidenceError("post-teardown verification/preflight evidence is incomplete")
    if material_hash(verification) != _require_hash(
        document.get("post_teardown_verification_hash"), "post_teardown_verification_hash"
    ):
        raise EvidenceError("post-teardown verification hash mismatch")
    if document.get("canonicalization_version") != CANONICALIZATION_VERSION:
        raise EvidenceError("disposition canonicalization mismatch")
    if material_hash(_without_hash(document, "disposition_material_hash")) != _require_hash(
        document.get("disposition_material_hash"), "disposition_material_hash"
    ):
        raise EvidenceError("disposition material hash mismatch")
    return MappingProxyType(json.loads(canonical_json(document)))


@dataclass(frozen=True)
class TrustedPublicationAuthority:
    actor_external_id: UUID
    permissions: frozenset[str]
    mfa_verified: bool
    access_active: bool
    global_governance: bool
    server_resolved: bool
    authority_context_version: str
    authority_decision_id: UUID
    authority_decision_hash: str
    resolved_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class CuratorEvidence:
    evidence_id: UUID
    evidence_hash: str
    actor_external_id: UUID
    candidate_id: UUID
    candidate_material_hash: str
    semantic_fingerprint: str
    source_manifest_hash: str
    source_reference_hash: str
    authority_decision_id: UUID
    authority_decision_hash: str
    server_resolved: bool
    valid_at: datetime


@dataclass(frozen=True)
class PublicationSnapshot:
    candidate_id: UUID
    knowledge_layer_id: UUID
    lineage_id: UUID
    predecessor_rule_id: UUID
    version: str
    current_leaf_ids: tuple[UUID, ...]
    superseded: bool
    status: str
    active: bool
    runtime_adopted: bool
    full_material_hash: str
    semantic_fingerprint: str
    lifecycle_hash: str
    source_manifest_id: UUID
    source_manifest_hash: str
    source_reference: str
    source_reference_hash: str
    governance_chain_hashes: Mapping[str, Any]
    application_receipt_id: UUID
    application_receipt_hash: str
    compensation_status: str
    compensation_provenance_hash: str | None
    capability_enabled: bool
    policy_id: str
    policy_version: str
    policy_hash: str
    operation_id: str
    operation_version: str
    curator: CuratorEvidence
    authority: TrustedPublicationAuthority
    role_actor_ids: Mapping[str, UUID]
    expected_state_token: str


@dataclass(frozen=True)
class PublicationPreflightResult:
    preflight_id: UUID
    eligible: bool
    replayed: bool
    candidate_id: UUID
    lineage_id: UUID
    operation_material_hash: str
    audit_material_hash: str
    outcome: str = "ELIGIBLE_FOR_LATER_PUBLICATION_GATE"


class InertPublicationPreflightLedger:
    """Deterministic isolated-test coordinator; callers must retain results externally.

    It models the fixed lock order ``idempotency claim -> lineage -> candidate ->
    retained graph -> curator -> authority``. It is deliberately not a publication
    store and is not usable by the native publication service.
    """

    def __init__(self) -> None:
        self._guard = RLock()
        self._lineage_locks: dict[UUID, RLock] = {}
        self._claims: dict[str, PublicationPreflightResult] = {}
        self._lineage_eligibility: dict[UUID, UUID] = {}
        self._abandoned: dict[UUID, str] = {}

    def lock_for(self, lineage_id: UUID) -> RLock:
        with self._guard:
            return self._lineage_locks.setdefault(lineage_id, RLock())

    def admit(self, key_hash: str, result: PublicationPreflightResult) -> PublicationPreflightResult:
        with self._guard:
            prior = self._claims.get(key_hash)
            if prior:
                if prior.operation_material_hash != result.operation_material_hash:
                    raise PreflightConflict("idempotency key has different publication-preflight material")
                return PublicationPreflightResult(**{**prior.__dict__, "replayed": True})
            prior_candidate = self._lineage_eligibility.get(result.lineage_id)
            if prior_candidate is not None and prior_candidate != result.candidate_id:
                raise PreflightConflict("a different revision in the lineage is already preflight-eligible")
            self._lineage_eligibility[result.lineage_id] = result.candidate_id
            self._claims[key_hash] = result
            return result

    def abandon(self, preflight_id: UUID, reason_hash: str) -> None:
        self._abandoned[preflight_id] = _require_hash(reason_hash, "reason_hash")

    def reconcile(self, preflight_id: UUID, *, result_hash: str | None, audit_hash: str | None) -> ReconciliationOutcome:
        matches = [result for result in self._claims.values() if result.preflight_id == preflight_id]
        if preflight_id in self._abandoned:
            return ReconciliationOutcome.ABANDONED if not matches else ReconciliationOutcome.INCONSISTENT
        if not matches:
            return ReconciliationOutcome.NOT_COMMITTED if result_hash is None and audit_hash is None else ReconciliationOutcome.INCONSISTENT
        if len(matches) != 1 or result_hash != matches[0].operation_material_hash or audit_hash != matches[0].audit_material_hash:
            return ReconciliationOutcome.INCONSISTENT
        return ReconciliationOutcome.COMMITTED


class InertPublicationPreflightService:
    def __init__(self, ledger: InertPublicationPreflightLedger | None = None) -> None:
        self.ledger = ledger or InertPublicationPreflightLedger()

    def evaluate(
        self, *, preflight_id: UUID, idempotency_key_hash: str,
        retained_manifest: Mapping[str, Any], snapshot_provider: Callable[[], PublicationSnapshot],
        now: datetime | None = None,
    ) -> PublicationPreflightResult:
        manifest = verify_candidate_evidence(retained_manifest)
        if CandidateEvidenceState(manifest["evidence_state"]) not in {
            CandidateEvidenceState.CREATED_AND_RETAINED,
            CandidateEvidenceState.DISPOSED_WITH_RETAINED_EVIDENCE,
        }:
            raise EvidenceError("candidate has no retained publication evidence")
        key_hash = _require_hash(idempotency_key_hash, "idempotency_key_hash")
        first = snapshot_provider()
        with self.ledger.lock_for(first.lineage_id):
            self._validate(first, manifest, now or datetime.now(timezone.utc))
            first_state = repr(first)
            final = snapshot_provider()
            if first_state != repr(final):
                raise EvidenceError("publication preflight TOCTOU drift")
            self._validate(final, manifest, now or datetime.now(timezone.utc))
            operation_material = self._operation_material(manifest, final, UUID(str(preflight_id)), key_hash)
            result = PublicationPreflightResult(
                preflight_id=UUID(str(preflight_id)), eligible=True, replayed=False,
                candidate_id=final.candidate_id, lineage_id=final.lineage_id,
                operation_material_hash=operation_material,
                audit_material_hash=material_hash({
                    "preflight_id": str(preflight_id), "operation_material_hash": operation_material,
                    "authority_decision_id": str(final.authority.authority_decision_id),
                    "curator_evidence_id": str(final.curator.evidence_id), "outcome": "ELIGIBLE",
                }),
            )
            return self.ledger.admit(key_hash, result)

    @staticmethod
    def _validate(snapshot: PublicationSnapshot, manifest: Mapping[str, Any], now: datetime) -> None:
        candidate = manifest["candidate"]
        source = manifest["source"]
        chain = manifest["governance_chain"]
        expected = {
            "candidate_id": candidate["id"], "knowledge_layer_id": candidate["knowledge_layer_id"],
            "lineage_id": candidate["lineage_id"], "predecessor_rule_id": candidate["predecessor_rule_id"],
            "version": candidate["version"], "full_material_hash": candidate["full_material_hash"],
            "semantic_fingerprint": candidate["semantic_fingerprint"], "lifecycle_hash": candidate["lifecycle_hash"],
            "source_manifest_id": source["manifest_id"], "source_manifest_hash": source["manifest_hash"],
            "source_reference": source["reference"], "source_reference_hash": source["reference_hash"],
            "application_receipt_id": chain["application_receipt"]["id"],
            "application_receipt_hash": chain["application_receipt"]["material_hash"],
        }
        for field, value in expected.items():
            actual = getattr(snapshot, field)
            normalized = str(actual) if isinstance(actual, UUID) else actual
            if normalized != value:
                raise EvidenceError(f"exact publication precondition mismatch: {field}")
        if snapshot.operation_id != OPERATION_ID or snapshot.operation_version != OPERATION_VERSION:
            raise EvidenceError("target operation identity mismatch")
        if snapshot.current_leaf_ids != (snapshot.candidate_id,) or snapshot.superseded:
            raise EvidenceError("candidate is not the one exact current lineage leaf")
        if snapshot.status != "draft" or snapshot.active or snapshot.runtime_adopted:
            raise EvidenceError("candidate must remain unpublished, inactive and unadopted")
        if snapshot.semantic_fingerprint == snapshot.lifecycle_hash:
            raise EvidenceError("narrow lifecycle hash cannot substitute for semantic fingerprint")
        if not snapshot.capability_enabled:
            raise EvidenceError("publication capability is disabled")
        authority = snapshot.authority
        if type(authority) is not TrustedPublicationAuthority or not authority.server_resolved:
            raise PermissionError("server-resolved AdminApps publication authority required")
        if (PUBLICATION_PERMISSION not in authority.permissions or not authority.mfa_verified or
                not authority.access_active or not authority.global_governance):
            raise PermissionError("fresh MFA, access, permission and global scope required")
        if authority.resolved_at.tzinfo is None or authority.expires_at.tzinfo is None or not (authority.resolved_at <= now < authority.expires_at):
            raise PermissionError("publication authority is stale")
        _require_hash(authority.authority_decision_hash, "authority.authority_decision_hash")
        curator = snapshot.curator
        if not curator.server_resolved or curator.valid_at.tzinfo is None or curator.valid_at > now:
            raise PermissionError("trusted immutable curator evidence required")
        curator_expected = (
            str(snapshot.candidate_id), snapshot.full_material_hash, snapshot.semantic_fingerprint,
            snapshot.source_manifest_hash, snapshot.source_reference_hash,
        )
        curator_actual = (
            str(curator.candidate_id), curator.candidate_material_hash, curator.semantic_fingerprint,
            curator.source_manifest_hash, curator.source_reference_hash,
        )
        if curator_actual != curator_expected:
            raise EvidenceError("curator evidence is not bound to exact candidate/source material")
        for value, field in ((curator.evidence_hash, "curator.evidence_hash"),
                             (curator.authority_decision_hash, "curator.authority_decision_hash"),
                             (snapshot.policy_hash, "policy_hash"),
                             (snapshot.expected_state_token, "expected_state_token")):
            _require_hash(value, field)
        required_roles = {
            "proposer", "reviewer", "proposal_approver", "application_authorizer",
            "application_executor", "curator", "publisher", "activator", "adopter",
        }
        if set(snapshot.role_actor_ids) != required_roles:
            raise EvidenceError("actor-level separation evidence is incomplete")
        actors = snapshot.role_actor_ids
        if actors["publisher"] != authority.actor_external_id or actors["curator"] != curator.actor_external_id:
            raise EvidenceError("trusted authority actors do not match role evidence")
        if any(actors["publisher"] == actors[role] for role in required_roles - {"publisher"}):
            raise PermissionError("publisher must be actor-independent from all other governance roles")
        if actors["curator"] == actors["application_executor"] or actors["activator"] == actors["adopter"]:
            raise PermissionError("actor-level separation of duties failed")
        expected_chain = {field: chain[field] for field in _CHAIN_FIELDS}
        if canonical_json(snapshot.governance_chain_hashes) != canonical_json(expected_chain):
            raise EvidenceError("complete immutable governance chain mismatch")
        if snapshot.compensation_status not in {"NOT_APPLICABLE", "COMPENSATED_CURRENT_LEAF"}:
            raise EvidenceError("compensation status is missing or ineligible")
        if snapshot.compensation_status == "COMPENSATED_CURRENT_LEAF" and not snapshot.compensation_provenance_hash:
            raise EvidenceError("compensation provenance is required")

    @staticmethod
    def _operation_material(
        manifest: Mapping[str, Any], snapshot: PublicationSnapshot,
        preflight_id: UUID, idempotency_key_hash: str,
    ) -> str:
        return material_hash({
            "operation": f"publication-preflight/{OPERATION_VERSION}",
            "preflight_id": str(preflight_id), "idempotency_key_hash": idempotency_key_hash,
            "candidate_id": str(snapshot.candidate_id),
            "knowledge_layer_id": str(snapshot.knowledge_layer_id),
            "lineage_id": str(snapshot.lineage_id),
            "predecessor_rule_id": str(snapshot.predecessor_rule_id),
            "candidate_version": snapshot.version,
            "candidate_material_hash": snapshot.full_material_hash,
            "semantic_fingerprint": snapshot.semantic_fingerprint,
            "lifecycle_hash": snapshot.lifecycle_hash,
            "source_manifest_id": str(snapshot.source_manifest_id),
            "source_manifest_hash": snapshot.source_manifest_hash,
            "source_reference": snapshot.source_reference,
            "source_reference_hash": snapshot.source_reference_hash,
            "governance_chain": snapshot.governance_chain_hashes,
            "application_receipt_id": str(snapshot.application_receipt_id),
            "application_receipt_hash": snapshot.application_receipt_hash,
            "curator_evidence_id": str(snapshot.curator.evidence_id),
            "curator_evidence_hash": snapshot.curator.evidence_hash,
            "curator_authority_decision_id": str(snapshot.curator.authority_decision_id),
            "curator_authority_decision_hash": snapshot.curator.authority_decision_hash,
            "publication_authority_decision_id": str(snapshot.authority.authority_decision_id),
            "publication_authority_decision_hash": snapshot.authority.authority_decision_hash,
            "publication_authority_context_version": snapshot.authority.authority_context_version,
            "policy_id": snapshot.policy_id, "policy_version": snapshot.policy_version,
            "policy_hash": snapshot.policy_hash, "target_operation_id": snapshot.operation_id,
            "target_operation_version": snapshot.operation_version,
            "compensation_status": snapshot.compensation_status,
            "compensation_provenance_hash": snapshot.compensation_provenance_hash,
            "expected_state_token": snapshot.expected_state_token,
            "retained_manifest_hash": manifest["manifest_material_hash"],
        })
