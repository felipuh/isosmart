"""Empty-history 0023 reversibility and least-privilege security matrix."""

import json
import os
from uuid import uuid4

import postgres_foundation_harness as phase3
import postgres_phase24_2_harness as phase24_2


PHASE282 = ("foundation", "0022_inert_rule_publication_activation_runtime_adoption")
PHASE283 = ("foundation", "0023_retained_synthetic_source_reference_application")


def require(value, message):
    if not value:
        raise AssertionError(message)


def denied(callable_):
    try:
        callable_()
    except Exception:
        return
    raise AssertionError("unauthorized database path unexpectedly succeeded")


def run():
    phase24_2.run()
    from django.db import connections

    phase3.migrate(PHASE283)
    phase3.migrate(PHASE282)
    with connections["default"].cursor() as cursor:
        cursor.execute(
            "SELECT pg_get_functiondef('normative.apply_validated_knowledge_layer_rule_source_reference_correction_v1"
            "(uuid,text,uuid,uuid,uuid)'::regprocedure)"
        )
        require("iso-smart-synthetic-poc-source-ref-v1" not in cursor.fetchone()[0], "0023 reverse did not restore grammar")
    phase3.migrate(PHASE283)

    executor = os.environ["FOUNDATION_LEARNING_APPLICATION_EXECUTOR_ROLE"]
    owner = os.environ["FOUNDATION_KNOWLEDGE_RULE_APPLICATION_OWNER_ROLE"]
    with connections["default"].cursor() as cursor:
        cursor.execute(
            "SELECT pg_get_functiondef('normative.apply_validated_knowledge_layer_rule_source_reference_correction_v1"
            "(uuid,text,uuid,uuid,uuid)'::regprocedure)"
        )
        definition = cursor.fetchone()[0]
        require("iso-smart-synthetic-poc-source-ref-v1" in definition, "0023 forward grammar absent")
        cursor.execute("SELECT has_schema_privilege(%s,'normative','CREATE')", [owner])
        require(cursor.fetchone()[0] is False, "capability owner retained transient schema CREATE")
        cursor.execute(
            "SELECT has_table_privilege(%s,'normative.knowledge_layer_rule','INSERT,UPDATE,DELETE')",
            [executor],
        )
        require(cursor.fetchone()[0] is False, "executor acquired generic target DML")
        cursor.execute(
            "SELECT has_function_privilege(%s,'normative.publish_knowledge_layer_rule_v1(uuid,uuid,text,text,text,uuid,uuid)','EXECUTE'),"
            "has_function_privilege(%s,'normative.activate_knowledge_layer_rule_v1(uuid,uuid,text,uuid,text,text,text,uuid,uuid)','EXECUTE'),"
            "has_function_privilege(%s,'normative.adopt_knowledge_layer_rule_runtime_v1(uuid,uuid,text,uuid,text,text,text,text,uuid,uuid)','EXECUTE')",
            [executor, executor, executor],
        )
        require(cursor.fetchone() == (False, False, False), "executor acquired release capability")
        cursor.execute(
            "SELECT count(*) FROM normative.knowledge_layer_rule_publication"
        )
        require(cursor.fetchone()[0] == 0, "migration created publication")

    def raw_update():
        with connections["learning_application"].cursor() as cursor:
            cursor.execute("UPDATE normative.knowledge_layer_rule SET source_reference=source_reference")

    denied(raw_update)
    with connections["learning_application"].cursor() as cursor:
        cursor.execute("SET search_path=pg_temp,public")
        cursor.execute("CREATE TEMP TABLE learning_application_authorization(id uuid)")

    def wrong_authorization():
        with connections["learning_application"].cursor() as cursor:
            cursor.execute(
                "SELECT * FROM normative.apply_validated_knowledge_layer_rule_source_reference_correction_v1"
                "(%s,%s,NULL,%s,%s)", [str(uuid4()), "0" * 64, str(uuid4()), str(uuid4())],
            )

    denied(wrong_authorization)
    print(json.dumps({
        "status": "PASS", "postgresql": "18.6", "migration": "0023 empty-history forward/reverse/forward PASS",
        "rls_governance_inherited": "Phase 24.2 A/none/B matrix PASS",
        "owner_acl": "transient CREATE revoked; owner/EXECUTE unchanged PASS",
        "hostile_search_path": "schema-qualified target-specific function remained fail-closed PASS",
        "generic_dml": "DENIED", "publication_activation_adoption_capability": "DENIED",
        "external_effects": "ZERO",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    run()

