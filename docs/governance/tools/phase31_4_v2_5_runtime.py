"""Offline V2.5 binding validator and post-native identity resolver."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from uuid import UUID


ALLOWED = {"EXACT_LITERAL", "DETERMINISTIC_DERIVATION", "CAPTURE_NATIVE_OUTPUT", "REFERENCE_RESOLVED_BINDING", "DERIVED_RUNTIME_INVARIANT", "ADR0017_MAPPED_OUTPUT"}


def _key(member):
    identity = member["member_identity"]
    return f"{identity['qualified_table_or_artifact_index']}::{identity['primary_key_or_artifact_id']}"


def validate(contract):
    errors = []
    members = {_key(member): member for member in contract["field_bindings"]}
    fields = {(key, field["name"]): field for key, member in members.items() for field in member["fields"]}

    def value(key, name):
        binding = fields[(key, name)]["value_binding"]
        return binding.get("typed_value")

    if value("qms.action_plan::ae682a8f-d782-5b27-a148-aa10a940e03a", "target_type") != "Opportunity":
        errors.append("controlled target_type is not native Opportunity")
    if value("qms.action_plan::ae682a8f-d782-5b27-a148-aa10a940e03a", "required_autonomy") != 3:
        errors.append("ActionPlan required_autonomy is not A3")
    for key, name in [
        ("governance.agent_definition::d8d5730c-d390-5be6-af6a-e4ab9d4cf155", "autonomy_max"),
        ("qms.agent_run::b87bdcde-c623-522f-a0ac-ff81f61df8e8", "effective_autonomy_ceiling"),
        ("qms.agent_decision::2a100aee-ebdd-5807-aab0-f8c4265e8e63", "decision_autonomy"),
        ("qms.execution_authorization::040b78af-e99d-5154-bb8f-246a87819be5", "effective_autonomy_ceiling"),
    ]:
        if value(key, name) != 3:
            errors.append(f"{key}.{name} is not A3")
    if len(members) != 118:
        errors.append(f"member_count={len(members)}")
    if sum(len(member["fields"]) for member in members.values()) != 1664:
        errors.append("field_count mismatch")
    for key, field in fields.items():
        binding = field.get("value_binding", {})
        kind = binding.get("kind")
        if kind not in ALLOWED:
            errors.append(f"unsupported binding {key[0]}.{key[1]}:{kind}")
        source = binding.get("source_member")
        if source and (source, binding.get("source_field")) not in fields:
            errors.append(f"unresolved reference {key[0]}.{key[1]} -> {source}.{binding.get('source_field')}")
        if kind == "CAPTURE_NATIVE_OUTPUT" and not binding.get("native_source"):
            errors.append(f"capture without authoritative source {key[0]}.{key[1]}")
        if kind == "DERIVED_RUNTIME_INVARIANT" and not binding.get("acyclic"):
            errors.append(f"cyclic invariant {key[0]}.{key[1]}")
    return errors


def resolve_graph(contract, captures):
    """Materialize a contract graph after native capture, then hash canonical JSON."""
    graph = deepcopy(contract)
    members = {_key(member): member for member in graph["field_bindings"]}
    resolved = {}
    visiting = set()

    def resolve(key, name):
        token = (key, name)
        if token in visiting:
            raise ValueError(f"cyclic binding at {key}.{name}")
        if token in resolved:
            return resolved[token]
        visiting.add(token)
        field = next(item for item in members[key]["fields"] if item["name"] == name)
        binding = field["value_binding"]
        kind = binding["kind"]
        if kind == "EXACT_LITERAL":
            value = binding.get("typed_value")
        elif kind == "CAPTURE_NATIVE_OUTPUT":
            value = captures[f"{key}.{name}"]
        elif kind == "REFERENCE_RESOLVED_BINDING":
            value = resolve(binding["source_member"], binding["source_field"])
        elif kind == "DERIVED_RUNTIME_INVARIANT":
            source = binding["source_bindings"][0]
            value = resolve(source.rsplit(".", 1)[0], source.rsplit(".", 1)[1]) + 1
        elif kind == "DETERMINISTIC_DERIVATION":
            value = binding["expected_output"]
        elif kind == "ADR0017_MAPPED_OUTPUT":
            value = binding.get("mapped_output", binding.get("typed_value", binding.get("expected_output")))
        else:
            raise ValueError(f"unresolvable binding {key}.{name}:{kind}")
        visiting.remove(token)
        resolved[token] = value
        return value

    for key, member in members.items():
        materialized = {}
        for field in member["fields"]:
            materialized[field["name"]] = resolve(key, field["name"])
        member["resolved_fields"] = materialized
    canonical = json.dumps(graph, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return graph, hashlib.sha256(canonical.encode()).hexdigest()


def main():
    root = Path(__file__).resolve().parents[3]
    path = root / "docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
    contract = json.loads(path.read_text())
    errors = validate(contract)
    if errors:
        raise SystemExit(json.dumps({"P0": len(errors), "P1": 0, "errors": errors}, indent=2))
    print(json.dumps({"P0": 0, "P1": 0, "members": 118, "fields": 1664, "status": "PASS"}, sort_keys=True))


if __name__ == "__main__":
    main()