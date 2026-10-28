from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
contract=json.loads((ROOT/"docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json").read_text())
rows=[]
for member in contract["field_bindings"]:
    identity=member["member_identity"]
    table=identity["qualified_table_or_artifact_index"]
    member_key=f"{table}::{identity['primary_key_or_artifact_id']}"
    for field in member["fields"]:
        binding=field.get("value_binding", {})
        value=binding.get("typed_value") or binding.get("expected_output")
        if binding.get("kind") == "EXACT_LITERAL" and isinstance(value, str) and len(value)==36 and value.count("-")==4:
            rows.append({"uuid":value,"member":member_key,"field":field["name"],"binding_kind":binding["kind"],"classification":"HISTORICAL_OR_STATIC_LITERAL_REQUIRES_AUDIT" if table.startswith("qms.") else "STATIC_CONTRACT_IDENTITY"})
required_live=[row for row in rows if row["classification"]=="HISTORICAL_OR_STATIC_LITERAL_REQUIRES_AUDIT"]
out={"artifact_schema":"phase31.4-retry12-live-identity-audit/v1","retry_id":"Phase 31.4 V2.5 Clean Retry 12","identity_map":{"adminapps_tenant_id":"canonical AdminApps Organization.id","tenant_projection_id":"local ISO Smart TenantProjection.id","qms_organization_id":"local ISO Smart Organization.id","process_id":"local ISO Smart Process.id","opportunity_id":"native Opportunity.id"},"historical_live_identity_literals_remaining":len(required_live),"required_live_remediations":required_live,"process_historical_uuid":"506d920c-fe62-53c0-aac8-9c1ca8ca78ed","tenant_historical_projection_uuid":"daa6bb22-660c-56f5-aadf-c63f06b01731","result":"P1_OPEN" if required_live else "PASS"}
(ROOT/"docs/governance/evidence/PHASE31_4_CLEAN_RETRY_12_IDENTITY_AUDIT.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps({"historical_live_identity_literals_remaining":len(required_live),"result":out["result"]},sort_keys=True))
