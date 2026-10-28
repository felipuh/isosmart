"""Exact retained-evidence contract for the Phase 29 publication POC.

This module is deliberately database independent.  It validates the immutable
Phase 28.3 inputs, the pre-teardown Phase 29 publication export, and the
post-teardown disposition without reconstructing any database row.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping
from uuid import UUID

from .retained_publication_evidence import (
    EvidenceError,
    canonical_json,
    load_and_verify_synthetic_source_manifest,
    material_hash,
    verify_phase283_candidate_evidence,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "docs/governance/fixtures/SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_SOURCE_MANIFEST_V1.json"
CREATION_PATH = ROOT / "docs/governance/evidence/PHASE28_3_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_CREATED_AND_RETAINED_V1.json"
CREATION_DISPOSITION_PATH = ROOT / "docs/governance/evidence/PHASE28_3_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_DISPOSITION_V1.json"
PUBLICATION_PATH = ROOT / "docs/governance/evidence/PHASE29_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_V1.json"
PUBLICATION_DISPOSITION_PATH = ROOT / "docs/governance/evidence/PHASE29_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_DISPOSITION_V1.json"

EXACT_CANDIDATE_ID = "01a0682b-dfc8-7b49-a601-f9bda29a70a5"
EXACT_LINEAGE_ID = "da72872a-3f3c-5fcd-86f7-0ed33e453522"
EXACT_VERSION = "sN+1"
EXACT_FULL_HASH = "caa24592b509334af4cd60fd7d3f3c43989d864d3f1c6e6d0d3bf83a81871f81"
EXACT_SEMANTIC_FINGERPRINT = "8465956c1daf27a9838bc1bfb468af3f518ae255b4662b2df40e7b8648516192"
EXACT_LIFECYCLE_HASH = "0adfd8075cc720140c6e1f0393d286799edac8f352efd9f1969816be83c51e52"
EXACT_SOURCE_MANIFEST_HASH = "cf92c267439f94f302e67888665dbf99392592341a808f5fc00f4c32ef23dc24"
EXACT_CREATION_HASH = "9ab80f4b0208e7dac971a0759df0bdb5c28392aa423ae11cbc0d483abb739a75"
EXACT_CREATION_DISPOSITION_HASH = "964b632537323764de35f9132bf7e63966df29dc89d70c1166e432d4e6436b5c"
EXACT_RECEIPT_ID = "01a0682b-dfa3-779c-89cd-1814e9209527"
PUBLICATION_POLICY_ID = "first-retained-synthetic-klr-publication-poc-policy/v1"
PUBLICATION_POLICY_VERSION = "v1"


class PublicationImportState(str, Enum):
    RETAINED_EVIDENCE_ONLY = "RETAINED_EVIDENCE_ONLY"
    IMPORTED_UNPUBLISHED = "IMPORTED_UNPUBLISHED"
    PUBLICATION_PRECOMMIT_ELIGIBLE = "PUBLICATION_PRECOMMIT_ELIGIBLE"
    PUBLISHED = "PUBLISHED"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _without(document: Mapping[str, Any], field: str) -> dict[str, Any]:
    return {key: value for key, value in document.items() if key != field}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def _uuid(value: Any, field: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise EvidenceError(f"{field} must be an exact UUID") from exc


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise EvidenceError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise EvidenceError(f"{field} must carry an offset")
    return value


def verify_phase28_publication_inputs() -> tuple[dict[str, Any], dict[str, Any], Mapping[str, Any]]:
    source = load_and_verify_synthetic_source_manifest(SOURCE_PATH)
    creation = _load(CREATION_PATH)
    verify_phase283_candidate_evidence(creation, source_manifest=source)
    disposition = _load(CREATION_DISPOSITION_PATH)
    _require(creation.get("manifest_material_hash") == EXACT_CREATION_HASH, "wrong Phase 28.3 creation manifest")
    _require(source.get("manifest_material_hash") == EXACT_SOURCE_MANIFEST_HASH, "wrong synthetic source manifest")
    _require(disposition.get("created_manifest_hash") == EXACT_CREATION_HASH, "disposition/creation mismatch")
    _require(disposition.get("candidate_id") == EXACT_CANDIDATE_ID, "disposition/candidate mismatch")
    _require(disposition.get("evidence_state") == "DISPOSED_WITH_RETAINED_EVIDENCE", "creation evidence not disposed")
    _require(
        material_hash(_without(disposition, "disposition_material_hash")) == EXACT_CREATION_DISPOSITION_HASH
        == disposition.get("disposition_material_hash"),
        "Phase 28.3 disposition material mismatch",
    )
    candidate = creation.get("candidate", {})
    exact = {
        "id": EXACT_CANDIDATE_ID,
        "lineage_id": EXACT_LINEAGE_ID,
        "predecessor_rule_id": EXACT_LINEAGE_ID,
        "version": EXACT_VERSION,
        "full_material_hash": EXACT_FULL_HASH,
        "semantic_fingerprint": EXACT_SEMANTIC_FINGERPRINT,
        "lifecycle_hash": EXACT_LIFECYCLE_HASH,
    }
    _require(all(candidate.get(key) == value for key, value in exact.items()), "exact candidate identity/material mismatch")
    _require(
        creation["governance_chain"]["application_receipt"]["id"] == EXACT_RECEIPT_ID,
        "exact application Receipt mismatch",
    )
    return creation, disposition, source


def publication_policy_material(policy_path: Path) -> dict[str, Any]:
    return {
        "policy_id": PUBLICATION_POLICY_ID,
        "version": PUBLICATION_POLICY_VERSION,
        "file": str(policy_path.relative_to(ROOT)),
        "file_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        "candidate_id": EXACT_CANDIDATE_ID,
        "publication_only": True,
        "activation_authorized": False,
        "runtime_adoption_authorized": False,
    }


def verify_publication_manifest(document: Mapping[str, Any]) -> Mapping[str, Any]:
    verify_phase28_publication_inputs()
    _require(document.get("manifest_schema") == "governed-target-publication-evidence-manifest/v1", "unknown publication manifest schema")
    _require(document.get("evidence_state") == "PUBLISHED_AND_RETAINED", "publication evidence state is not retained")
    _require(document.get("candidate_id") == EXACT_CANDIDATE_ID, "publication candidate mismatch")
    _require(document.get("lineage_id") == EXACT_LINEAGE_ID, "publication lineage mismatch")
    _require(document.get("candidate_version") == EXACT_VERSION, "publication version mismatch")
    _require(document.get("candidate_material_hash") == EXACT_FULL_HASH, "publication full hash mismatch")
    _require(document.get("semantic_fingerprint") == EXACT_SEMANTIC_FINGERPRINT, "publication semantic fingerprint mismatch")
    _require(document.get("lifecycle_hash") == EXACT_LIFECYCLE_HASH, "publication lifecycle hash mismatch")
    _require(document.get("source_manifest_hash") == EXACT_SOURCE_MANIFEST_HASH, "publication source mismatch")
    _require(document.get("creation_manifest_hash") == EXACT_CREATION_HASH, "publication creation evidence mismatch")
    _require(document.get("creation_disposition_hash") == EXACT_CREATION_DISPOSITION_HASH, "publication disposition mismatch")
    _require(document.get("application_receipt_id") == EXACT_RECEIPT_ID, "publication Receipt mismatch")
    states = document.get("import_state_history")
    _require(states == [state.value for state in PublicationImportState], "publication import state machine was skipped")
    publication = document.get("publication")
    _require(isinstance(publication, dict), "publication artifact is absent")
    for field in ("id", "claim_id", "event_id", "outbox_id", "audit_id", "trace_id"):
        _uuid(publication.get(field), f"publication.{field}")
    _require(publication.get("event_type") == "knowledge_layer_rule.published", "wrong publication event")
    _require(publication.get("event_schema_version") == 1, "wrong publication event schema")
    _require(publication.get("candidate_status_before") == "draft", "wrong publication before state")
    _require(publication.get("candidate_status_after") == "published", "wrong publication after state")
    _require(publication.get("published_at") is not None, "published_at missing")
    _timestamp(publication["published_at"], "publication.published_at")
    for field in ("claim", "artifact", "event", "outbox", "audit"):
        item = document.get("live_graph", {}).get(field)
        _require(isinstance(item, dict), f"live graph {field} is absent")
        _require(material_hash(item.get("material")) == item.get("material_hash"), f"live graph {field} hash mismatch")
    authority = document.get("publisher_authority", {})
    _uuid(authority.get("actor_external_id"), "publisher_authority.actor_external_id")
    _uuid(authority.get("authority_decision_id"), "publisher_authority.authority_decision_id")
    _require(authority.get("server_resolved") is True and authority.get("mfa_verified") is True, "publisher authority is not trusted")
    _require(authority.get("access_active") is True and authority.get("global_governance") is True, "publisher authority is not active/global")
    _require(authority.get("permission") == "qms.knowledge_layer_rule.publish", "publisher permission mismatch")
    _require(authority.get("actor_external_id") == document.get("role_actor_ids", {}).get("publisher"), "publisher identity mismatch")
    others = {value for key, value in document.get("role_actor_ids", {}).items() if key != "publisher"}
    _require(authority["actor_external_id"] not in others, "publisher separation of duties failed")
    policy = document.get("publication_policy", {})
    _require(policy.get("policy_id") == PUBLICATION_POLICY_ID and policy.get("version") == PUBLICATION_POLICY_VERSION, "publication policy mismatch")
    zero = document.get("zero_effects", {})
    for key in ("activation_rows", "runtime_adoption_rows", "activation_events", "runtime_adoption_events", "runtime_behavior_delta", "normative_delta", "automatic_learning_delta", "external_business_effects"):
        _require(zero.get(key) == 0, f"non-zero forbidden effect: {key}")
    _require(document.get("runtime_effect_changed") is False, "publication changed runtime effect")
    _require(document.get("integrity_verified") is True and document.get("live_graph_verified") is True, "publication graph not verified live")
    _require(material_hash(_without(document, "manifest_material_hash")) == document.get("manifest_material_hash"), "publication manifest material hash mismatch")
    return document


def verify_publication_disposition(document: Mapping[str, Any], publication: Mapping[str, Any]) -> Mapping[str, Any]:
    verify_publication_manifest(publication)
    _require(document.get("disposition_schema") == "governed-target-publication-evidence-disposition/v1", "unknown publication disposition schema")
    _require(document.get("state") == "PUBLISHED_POC_DISPOSED_WITH_RETAINED_EVIDENCE", "wrong publication disposition state")
    _require(document.get("candidate_id") == EXACT_CANDIDATE_ID, "publication disposition candidate mismatch")
    _require(document.get("publication_manifest_hash") == publication.get("manifest_material_hash"), "publication disposition manifest mismatch")
    _timestamp(document.get("disposed_at"), "disposed_at")
    teardown = document.get("teardown_evidence", {})
    _require(all(teardown.get(key) is True for key in ("database_absent", "roles_absent", "container_absent", "volume_absent", "temp_absent")), "ephemeral teardown is incomplete")
    _require(document.get("post_teardown_verification", {}).get("database_reconstructed") is False, "database reconstruction is forbidden")
    _require(document.get("post_teardown_verification", {}).get("offline_release_state_verified") is True, "offline release state was not verified")
    _require(material_hash(teardown) == document.get("teardown_evidence_hash"), "teardown evidence hash mismatch")
    _require(material_hash(document.get("post_teardown_verification")) == document.get("post_teardown_verification_hash"), "post-teardown verification hash mismatch")
    _require(material_hash(_without(document, "disposition_material_hash")) == document.get("disposition_material_hash"), "publication disposition hash mismatch")
    return document


def offline_release_state(publication_path: Path = PUBLICATION_PATH, disposition_path: Path = PUBLICATION_DISPOSITION_PATH) -> dict[str, Any]:
    publication = _load(publication_path)
    disposition = _load(disposition_path)
    verify_publication_disposition(disposition, publication)
    return {
        "candidate_id": EXACT_CANDIDATE_ID,
        "CREATED": True,
        "APPLICATION_GOVERNED": True,
        "PUBLISHED": True,
        "ACTIVATED": False,
        "RUNTIME_ADOPTED": False,
        "RUNTIME_EFFECTIVE": False,
        "database_reconstructed": False,
    }


def retain_exclusive(path: Path, document: Mapping[str, Any]) -> None:
    encoded = (json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    try:
        with path.open("xb") as handle:
            handle.write(encoded)
    except FileExistsError:
        if path.read_bytes() != encoded:
            raise EvidenceError(f"immutable retained evidence conflict at {path}")

