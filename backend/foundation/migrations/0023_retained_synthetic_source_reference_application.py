"""Admit only the retained Phase 28.3 synthetic source-reference branch.

This migration changes no table, grant, role, publication, activation, or
runtime-adoption contract. It narrows the existing target-specific application
function to two closed grammars: the historical authoritative-style reference
and the retained non-authoritative synthetic POC reference.
"""

from django.db import migrations
from psycopg2 import sql


AUTHORITATIVE_PATTERN = (
    r"^iso-smart-source-ref-v1:[0-9a-f-]{36}:[0-9a-f]{64}:"
    r"[A-Za-z0-9][A-Za-z0-9._:/#-]{0,255}$"
)
SYNTHETIC_PATTERN = (
    r"^iso-smart-synthetic-poc-source-ref-v1:[0-9a-f-]{36}:[0-9a-f]{64}:"
    r"fixture/element/[A-Za-z0-9._~-]+$"
)
COMBINED_PATTERN = (
    r"^(iso-smart-source-ref-v1:[0-9a-f-]{36}:[0-9a-f]{64}:"
    r"[A-Za-z0-9][A-Za-z0-9._:/#-]{0,255}|"
    r"iso-smart-synthetic-poc-source-ref-v1:[0-9a-f-]{36}:[0-9a-f]{64}:"
    r"fixture/element/[A-Za-z0-9._~-]+)$"
)


def _replace_application_grammar(schema_editor, old, new):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('foundation.knowledge_rule_application_owner_role',true)")
        owner_role = cursor.fetchone()[0]
        if not owner_role:
            raise RuntimeError("0023 requires the existing KnowledgeLayerRule application capability owner")
        cursor.execute(
            sql.SQL("GRANT CREATE ON SCHEMA normative TO {}").format(sql.Identifier(owner_role))
        )
        cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(owner_role)))
    schema_editor.execute(
        """
        DO $migration$
        DECLARE
          definition text;
          old_pattern text := %s;
          new_pattern text := %s;
          occurrence_count integer;
        BEGIN
          SELECT pg_get_functiondef(
            'normative.apply_validated_knowledge_layer_rule_source_reference_correction_v1'
            '(uuid,text,uuid,uuid,uuid)'::regprocedure
          ) INTO STRICT definition;
          occurrence_count := (
            length(definition) - length(replace(definition, old_pattern, ''))
          ) / length(old_pattern);
          IF occurrence_count <> 2 THEN
            RAISE EXCEPTION '0023 expected exactly two closed source grammar checks, found %%', occurrence_count;
          END IF;
          definition := replace(definition, old_pattern, new_pattern);
          EXECUTE definition;
        END $migration$;
        """,
        params=(old, new),
    )
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("RESET ROLE")
        cursor.execute(
            sql.SQL("REVOKE CREATE ON SCHEMA normative FROM {}").format(sql.Identifier(owner_role))
        )


def forward(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        _replace_application_grammar(schema_editor, AUTHORITATIVE_PATTERN, COMBINED_PATTERN)


def reverse(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT EXISTS(
              SELECT 1 FROM qms.learning_target_application_receipt
              WHERE source_reference_before LIKE 'iso-smart-synthetic-poc-source-ref-v1:%%'
                 OR source_reference_after LIKE 'iso-smart-synthetic-poc-source-ref-v1:%%'
            )
            """
        )
        if cursor.fetchone()[0]:
            raise RuntimeError("0023 is forward-only after retained synthetic application history exists")
    _replace_application_grammar(schema_editor, COMBINED_PATTERN, AUTHORITATIVE_PATTERN)


class Migration(migrations.Migration):
    dependencies = [
        ("foundation", "0022_inert_rule_publication_activation_runtime_adoption"),
    ]
    operations = [migrations.RunPython(forward, reverse)]
