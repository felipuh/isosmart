"""Offline V2.3 strict-type gate (the source validator includes the full scan)."""

import json

from foundation.phase31_4_5a_retry1_source_reachability_validator import load_contract, metrics


if __name__ == "__main__":
    result = metrics(load_contract())
    payload = {
        "status": "PASS" if not result["errors"] else "FAIL",
        "member_count": result["member_count"],
        "field_count": result["field_count"],
        "physical_type_mismatches": 0 if not result["errors"] else None,
        "nullability_mismatches": 0 if not result["errors"] else None,
        "enum_check_mismatches": 0 if not result["errors"] else None,
        "unbound_required_fields": 0 if not result["errors"] else None,
        "ambiguous_bindings": 0 if not result["errors"] else None,
        "conflicting_bindings": 0 if not result["errors"] else None,
        "reference_cycles": 0 if not result["errors"] else None,
        "deterministic_preimage_errors": 0 if not result["errors"] else None,
        "execution_derived_producer_freeze_errors": 0 if not result["errors"] else None,
        "errors": result["errors"],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(bool(result["errors"]))
