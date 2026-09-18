"""Phase 28.3 retained synthetic-candidate export and offline preflight helpers.

The creation manifest is immutable. Teardown is represented by a second,
append-only disposition document so database destruction never rewrites the
evidence that was verified against the live graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path
from threading import RLock
from typing import Any, Mapping
from uuid import UUID

from .retained_publication_evidence import (
    CANONICALIZATION_VERSION,
    CuratorEvidence,
    EvidenceError,
    PublicationSnapshot,
    TrustedPublicationAuthority,
    canonical_json,
    material_hash,
    verify_phase283_candidate_evidence,
)


def write_retained_json_once(path: Path, document: Mapping[str, Any]) -> bool:
    """Atomically retain exact JSON; an exact existing file is a replay."""
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        existing = json.loads(path.read_text(encoding="utf-8"))
        if canonical_json(existing) != canonical_json(document):
            raise EvidenceError(f"retained evidence conflict at {path}")
        return True
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return False


@dataclass
class RetainedEvidenceExportLedger:
    """One-process race fence complementing the filesystem O_EXCL boundary."""

    _guard: RLock = field(default_factory=RLock)

    def retain(self, path: Path, document: Mapping[str, Any]) -> bool:
        with self._guard:
            return write_retained_json_once(path, document)


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise EvidenceError("retained authority timestamp must be timezone-aware")
    return parsed


def publication_snapshot_from_retained_manifest(document: Mapping[str, Any]) -> PublicationSnapshot:
    """Build the inert preflight snapshot exclusively from verified evidence."""
    manifest = verify_phase283_candidate_evidence(document)
    candidate = manifest["candidate"]
    source = manifest["source"]
    chain = manifest["governance_chain"]
    curator_material = manifest["curator_evidence"]["material"]
    publisher_material = manifest["future_publisher_authority"]["material"]
    curator = CuratorEvidence(
        UUID(manifest["curator_evidence"]["id"]), manifest["curator_evidence"]["material_hash"],
        UUID(curator_material["actor_external_id"]), UUID(candidate["id"]),
        candidate["full_material_hash"], candidate["semantic_fingerprint"],
        source["manifest_hash"], source["reference_hash"],
        UUID(curator_material["authority_decision_id"]), curator_material["authority_decision_hash"],
        curator_material["server_resolved"], _dt(curator_material["valid_at"]),
    )
    authority = TrustedPublicationAuthority(
        UUID(publisher_material["actor_external_id"]),
        frozenset(publisher_material["permissions"]), publisher_material["mfa_verified"],
        publisher_material["access_active"], publisher_material["global_governance"],
        publisher_material["server_resolved"], publisher_material["authority_context_version"],
        UUID(publisher_material["authority_decision_id"]), publisher_material["authority_decision_hash"],
        _dt(publisher_material["resolved_at"]), _dt(publisher_material["expires_at"]),
    )
    policy = next(
        reference for reference in chain["policies"]
        if reference.get("policy_id") == "first-retained-synthetic-klr-publication-candidate-policy/v1"
    )
    return PublicationSnapshot(
        UUID(candidate["id"]), UUID(candidate["knowledge_layer_id"]), UUID(candidate["lineage_id"]),
        UUID(candidate["predecessor_rule_id"]), candidate["version"], (UUID(candidate["id"]),),
        False, "draft", False, False, candidate["full_material_hash"],
        candidate["semantic_fingerprint"], candidate["lifecycle_hash"], UUID(source["manifest_id"]),
        source["manifest_hash"], source["reference"], source["reference_hash"], chain,
        UUID(chain["application_receipt"]["id"]), chain["application_receipt"]["material_hash"],
        "NOT_APPLICABLE", None, True, policy["policy_id"], policy["version"],
        policy["material_hash"], manifest["operation_id"], manifest["operation_version"],
        curator, authority, {key: UUID(value) for key, value in manifest["role_actor_ids"].items()},
        manifest["expected_state_token"],
    )


def finalize_document_hash(document: dict[str, Any], hash_field: str) -> dict[str, Any]:
    document["canonicalization_version"] = CANONICALIZATION_VERSION
    document[hash_field] = material_hash({key: value for key, value in document.items() if key != hash_field})
    return document
