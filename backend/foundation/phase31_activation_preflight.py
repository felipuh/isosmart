"""Offline Phase 31 stop gate; no database, import, or activation capability.

The Phase 29 verifier proves its retained release summary. It does not prove
that all mandatory relational dependencies survived teardown. This additional
check reports that distinction without reconstructing historical rows.
"""

import hashlib
import json

from .phase29_publication_evidence import (
    CREATION_DISPOSITION_PATH,
    CREATION_PATH,
    PUBLICATION_DISPOSITION_PATH,
    PUBLICATION_PATH,
    ROOT,
    SOURCE_PATH,
    EvidenceError,
    material_hash,
    offline_release_state,
)


PUBLICATION_HASH = "51f0b207c790e6ab0c3d67985e161ba0d0cc7b2feb888f545c1ff5eedacf5366"
DISPOSITION_HASH = "fff3b225184282e48dad30f4e56b16444df4241b5f647f2f3750ee4a254158f1"
POLICY_HASH = "43c67505ec3e3d9df0d306012e2036ced7cf437de703e8ff95b709a7af08756d"
PUBLICATION_ID = "e97576de-d4ef-520d-8592-d376ed401221"
CURATION_AUDIT_ID = "12d811ab-c3b4-4615-8972-75008a36e327"
POLICY_PATH = ROOT / "docs/governance/FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_ACTIVATION_POC_POLICY_V1.md"


def _require(value, message):
    if not value:
        raise EvidenceError(message)


def _objects(value):
    """Inspect actual retained JSON objects, never derive a missing record."""
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _objects(child)


def inspect_exact_publication_import_dependency():
    """Read only the fixed, approved retained inputs; not an eligibility grant.

    Even a dependency being present would require a separately reviewed full
    Phase 31 preflight. Arbitrary payloads and supplemental evidence are not
    accepted here, and this function never authorizes database creation.
    """
    state = offline_release_state()
    documents = [json.loads(path.read_text(encoding="utf-8")) for path in (
        CREATION_PATH, CREATION_DISPOSITION_PATH, PUBLICATION_PATH,
        PUBLICATION_DISPOSITION_PATH, SOURCE_PATH,
    )]
    publication, disposition = documents[2:4]
    _require(publication["manifest_material_hash"] == PUBLICATION_HASH,
             "exact retained Publication manifest hash mismatch")
    _require(disposition["disposition_material_hash"] == DISPOSITION_HASH,
             "exact retained Publication disposition hash mismatch")
    _require(hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest() == POLICY_HASH,
             "Phase 30 Activation policy file hash mismatch")
    artifact = publication["live_graph"]["artifact"]["material"]
    _require(artifact["id"] == PUBLICATION_ID, "exact Publication ID mismatch")
    _require(artifact["curation_audit_id"] == CURATION_AUDIT_ID,
             "exact Publication curation audit reference mismatch")
    # An ID reference, curator decision, or another audit is not this row.
    required_columns = {
        "id", "action", "entity_type", "entity_id", "actor_id",
        "trace_id", "payload_hash", "occurred_at",
    }
    rows = [item for document in documents for item in _objects(document)
            if item.get("id") == CURATION_AUDIT_ID and required_columns <= item.keys()]
    return {
        "diagnostic_schema": "phase31-exact-publication-import-dependency/v1",
        "retained_release_state": state,
        "publication_id": PUBLICATION_ID,
        "publication_manifest_hash": PUBLICATION_HASH,
        "publication_disposition_hash": DISPOSITION_HASH,
        "activation_policy_file_sha256": POLICY_HASH,
        "required_relation": "normative.curation_audit",
        "required_row_id": CURATION_AUDIT_ID,
        "complete_retained_row_occurrences": len(rows),
        "dependency_material_present": bool(rows),
        "database_creation_authorized": False,
        "database_created": False,
        "database_reconstructed": False,
        "activation_invoked": False,
        "runtime_adoption_invoked": False,
        "full_activation_preflight_completed": False,
    }


def main():
    try:
        result = inspect_exact_publication_import_dependency()
        result["blocker"] = (
            "MISSING_RETAINED_PUBLICATION_CURATION_AUDIT"
            if not result["dependency_material_present"]
            else "FULL_ACTIVATION_PREFLIGHT_NOT_IMPLEMENTED"
        )
    except (EvidenceError, OSError, ValueError, KeyError, TypeError) as exc:
        result = {
            "blocker": "RETAINED_INPUT_VERIFICATION_FAILED",
            "detail": str(exc),
            "database_creation_authorized": False,
            "database_created": False,
            "database_reconstructed": False,
        }
    result["verdict"] = "PHASE 31 — NOT PROMOTED"
    result["diagnostic_material_hash"] = material_hash(result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
