# Phase 24.2: additive inert exact learning-delta contract.  No target DML.

from django.db import migrations, models
import django.db.models.deletion
import uuid


FORWARD_SQL = r"""
DO $migration$
DECLARE
  learning_role text := current_setting('foundation.learning_governance_role',true);
  reviewer_role text := current_setting('foundation.learning_reviewer_role',true);
  approver_role text := current_setting('foundation.learning_approver_role',true);
  authorizer_role text := current_setting('foundation.learning_authorizer_role',true);
BEGIN
  IF learning_role IS NULL OR learning_role='' OR reviewer_role IS NULL OR reviewer_role='' OR
     approver_role IS NULL OR approver_role='' OR authorizer_role IS NULL OR authorizer_role='' THEN
    RAISE EXCEPTION 'Phase 24.2 requires the four existing learning governance principals';
  END IF;

  CREATE TABLE qms.learning_proposal_canonical_delta (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    organization_id uuid NOT NULL,
    learning_proposal_id uuid NOT NULL UNIQUE,
    canonicalization_version varchar(80) NOT NULL CHECK(canonicalization_version='iso-smart-learning-delta-canonical-v1'),
    delta_schema_version varchar(120) NOT NULL,
    operation_id varchar(160) NOT NULL,
    operation_version varchar(40) NOT NULL CHECK(operation_version='v1'),
    target_type varchar(80) NOT NULL,
    target_id uuid NOT NULL,
    target_lineage_id uuid NOT NULL,
    target_version varchar(120) NOT NULL CHECK(btrim(target_version)<>''),
    target_hash char(64) NOT NULL CHECK(target_hash ~ '^[0-9a-f]{64}$'),
    delta_document jsonb NOT NULL CHECK(jsonb_typeof(delta_document)='object'),
    canonical_bytes bytea NOT NULL,
    delta_hash char(64) NOT NULL CHECK(delta_hash ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT qms_learning_delta_tenant_org_id_unique UNIQUE(tenant_id,organization_id,id),
    CONSTRAINT qms_learning_delta_org_fk FOREIGN KEY(tenant_id,organization_id)
      REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT
  );

  ALTER TABLE qms.learning_proposal
    ADD COLUMN canonical_delta_id uuid UNIQUE,
    ADD COLUMN canonicalization_version varchar(80),
    ADD COLUMN delta_schema_version varchar(120),
    ADD COLUMN operation_id varchar(160),
    ADD COLUMN operation_version varchar(40),
    ADD COLUMN delta_hash char(64);
  ALTER TABLE qms.learning_proposal_review
    ADD COLUMN canonical_delta_id uuid, ADD COLUMN canonicalization_version varchar(80),
    ADD COLUMN delta_schema_version varchar(120), ADD COLUMN operation_id varchar(160),
    ADD COLUMN operation_version varchar(40), ADD COLUMN delta_hash char(64);
  ALTER TABLE qms.learning_proposal_decision
    ADD COLUMN canonical_delta_id uuid, ADD COLUMN canonicalization_version varchar(80),
    ADD COLUMN delta_schema_version varchar(120), ADD COLUMN operation_id varchar(160),
    ADD COLUMN operation_version varchar(40), ADD COLUMN delta_hash char(64);
  ALTER TABLE qms.learning_application_authorization
    ADD COLUMN canonical_delta_id uuid, ADD COLUMN canonicalization_version varchar(80),
    ADD COLUMN delta_schema_version varchar(120), ADD COLUMN operation_id varchar(160),
    ADD COLUMN operation_version varchar(40), ADD COLUMN delta_hash char(64);

  ALTER TABLE qms.learning_proposal_canonical_delta ADD CONSTRAINT qms_learning_delta_proposal_fk
    FOREIGN KEY(tenant_id,organization_id,learning_proposal_id)
    REFERENCES qms.learning_proposal(tenant_id,organization_id,id) ON DELETE RESTRICT
    DEFERRABLE INITIALLY DEFERRED;
  ALTER TABLE qms.learning_proposal ADD CONSTRAINT qms_learning_proposal_delta_fk
    FOREIGN KEY(tenant_id,organization_id,canonical_delta_id)
    REFERENCES qms.learning_proposal_canonical_delta(tenant_id,organization_id,id) ON DELETE RESTRICT
    DEFERRABLE INITIALLY DEFERRED;

  ALTER TABLE qms.learning_proposal DROP CONSTRAINT qms_learning_proposal_hashes;
  ALTER TABLE qms.learning_proposal ADD CONSTRAINT qms_learning_proposal_hashes CHECK(
    target_hash ~ '^[0-9a-f]{64}$' AND proposed_change_hash ~ '^[0-9a-f]{64}$' AND
    (delta_hash IS NULL OR delta_hash ~ '^[0-9a-f]{64}$'));

  ALTER TABLE qms.learning_application_authorization DROP CONSTRAINT qms_learning_authorization_capability;
  ALTER TABLE qms.learning_application_authorization ADD CONSTRAINT qms_learning_authorization_capability CHECK(
    (canonical_delta_id IS NULL AND ((target_type='ModelPolicy' AND capability_id='revise_model_policy') OR
      (target_type='AgentDefinition' AND capability_id='revise_agent_definition') OR
      (target_type='KnowledgeLayerRule' AND capability_id='revise_knowledge_layer_rule'))) OR
    (canonical_delta_id IS NOT NULL AND capability_id=operation_id AND capability_version=operation_version AND
      ((target_type='ModelPolicy' AND operation_id='learning.model_policy.approved_models.remove') OR
       (target_type='AgentDefinition' AND operation_id='learning.agent_definition.autonomy.reduce') OR
       (target_type='KnowledgeLayerRule' AND operation_id='learning.knowledge_layer_rule.source_reference.correct'))));

  CREATE FUNCTION qms.foundation_0020_complete_binding(
    p_delta uuid,p_canon text,p_schema text,p_operation text,p_version text,p_hash text)
  RETURNS boolean LANGUAGE sql IMMUTABLE SET search_path=pg_catalog AS $fn$
    SELECT (p_delta IS NULL AND p_canon IS NULL AND p_schema IS NULL AND p_operation IS NULL AND p_version IS NULL AND p_hash IS NULL)
        OR (p_delta IS NOT NULL AND p_canon='iso-smart-learning-delta-canonical-v1' AND
            p_schema IS NOT NULL AND p_operation IS NOT NULL AND p_version='v1' AND p_hash ~ '^[0-9a-f]{64}$')
  $fn$;

  ALTER TABLE qms.learning_proposal ADD CONSTRAINT qms_learning_proposal_complete_delta CHECK(
    qms.foundation_0020_complete_binding(canonical_delta_id,canonicalization_version,delta_schema_version,operation_id,operation_version,delta_hash));
  ALTER TABLE qms.learning_proposal_review ADD CONSTRAINT qms_learning_review_complete_delta CHECK(
    qms.foundation_0020_complete_binding(canonical_delta_id,canonicalization_version,delta_schema_version,operation_id,operation_version,delta_hash));
  ALTER TABLE qms.learning_proposal_decision ADD CONSTRAINT qms_learning_decision_complete_delta CHECK(
    qms.foundation_0020_complete_binding(canonical_delta_id,canonicalization_version,delta_schema_version,operation_id,operation_version,delta_hash));
  ALTER TABLE qms.learning_application_authorization ADD CONSTRAINT qms_learning_authorization_complete_delta CHECK(
    qms.foundation_0020_complete_binding(canonical_delta_id,canonicalization_version,delta_schema_version,operation_id,operation_version,delta_hash));

  CREATE FUNCTION qms.foundation_0020_reject_delta_mutation()
  RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $fn$
  BEGIN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='canonical learning delta is immutable and non-rebindable'; END $fn$;

  CREATE FUNCTION qms.foundation_0020_canonical_json_value(p_value jsonb)
  RETURNS text LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE SET search_path=pg_catalog AS $fn$
  DECLARE kind text; item record; pieces text:=''; separator text:='';
  BEGIN
    kind:=jsonb_typeof(p_value);
    IF kind='object' THEN
      FOR item IN SELECT key,value FROM jsonb_each(p_value) ORDER BY key LOOP
        pieces:=pieces||separator||to_jsonb(item.key)::text||':'||qms.foundation_0020_canonical_json_value(item.value);
        separator:=',';
      END LOOP;
      RETURN '{'||pieces||'}';
    ELSIF kind='array' THEN
      FOR item IN SELECT value FROM jsonb_array_elements(p_value) WITH ORDINALITY a(value,n) ORDER BY n LOOP
        pieces:=pieces||separator||qms.foundation_0020_canonical_json_value(item.value); separator:=',';
      END LOOP;
      RETURN '['||pieces||']';
    END IF;
    RETURN p_value::text;
  END $fn$;

  CREATE FUNCTION qms.foundation_0020_validate_delta()
  RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
  DECLARE doc_text text;
  BEGIN
    IF NEW.tenant_id IS DISTINCT FROM NULLIF(current_setting('app.tenant_id',true),'')::uuid THEN
      RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='trusted tenant context required for canonical delta';
    END IF;
    BEGIN doc_text := convert_from(NEW.canonical_bytes,'UTF8');
    EXCEPTION WHEN character_not_in_repertoire THEN RAISE EXCEPTION USING ERRCODE='22021',MESSAGE='canonical bytes must be UTF-8'; END;
    IF doc_text::jsonb<>NEW.delta_document OR
       convert_to(qms.foundation_0020_canonical_json_value(NEW.delta_document),'UTF8')<>NEW.canonical_bytes OR
       encode(sha256(NEW.canonical_bytes),'hex')<>NEW.delta_hash OR
       (SELECT count(*) FROM jsonb_object_keys(NEW.delta_document))<>10 OR
       NOT (NEW.delta_document ?& ARRAY['canonicalization_version','delta_schema_version','operation_id','operation_version','payload','target_hash','target_id','target_lineage_id','target_type','target_version']) OR
       NEW.delta_document->>'canonicalization_version'<>NEW.canonicalization_version OR
       NEW.delta_document->>'delta_schema_version'<>NEW.delta_schema_version OR
       NEW.delta_document->>'operation_id'<>NEW.operation_id OR NEW.delta_document->>'operation_version'<>NEW.operation_version OR
       NEW.delta_document->>'target_type'<>NEW.target_type OR NEW.delta_document->>'target_id'<>NEW.target_id::text OR
       NEW.delta_document->>'target_lineage_id'<>NEW.target_lineage_id::text OR
       NEW.delta_document->>'target_version'<>NEW.target_version OR NEW.delta_document->>'target_hash'<>NEW.target_hash THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='canonical delta bytes/document/hash/tuple mismatch';
    END IF;
    IF NOT ((NEW.target_type='ModelPolicy' AND NEW.operation_id='learning.model_policy.approved_models.remove' AND NEW.delta_schema_version='learning-model-policy-approved-model-removal-delta-v1') OR
            (NEW.target_type='AgentDefinition' AND NEW.operation_id='learning.agent_definition.autonomy.reduce' AND NEW.delta_schema_version='learning-agent-definition-autonomy-reduction-delta-v1') OR
            (NEW.target_type='KnowledgeLayerRule' AND NEW.operation_id='learning.knowledge_layer_rule.source_reference.correct' AND NEW.delta_schema_version='learning-knowledge-layer-rule-source-reference-correction-delta-v1')) THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='unknown exact target operation contract';
    END IF;
    RETURN NEW;
  END $fn$;

  CREATE FUNCTION qms.foundation_0020_validate_binding()
  RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
  DECLARE p record; d record;
  BEGIN
    IF TG_TABLE_NAME='learning_proposal' THEN p:=NEW; ELSE SELECT * INTO p FROM qms.learning_proposal WHERE id=NEW.learning_proposal_id; END IF;
    IF NEW.canonical_delta_id IS NULL THEN RETURN NEW; END IF;
    SELECT * INTO d FROM qms.learning_proposal_canonical_delta WHERE id=NEW.canonical_delta_id;
    IF d.id IS NULL OR d.learning_proposal_id<>p.id OR d.tenant_id<>p.tenant_id OR d.organization_id<>p.organization_id OR
       d.canonicalization_version<>NEW.canonicalization_version OR d.delta_schema_version<>NEW.delta_schema_version OR
       d.operation_id<>NEW.operation_id OR d.operation_version<>NEW.operation_version OR d.delta_hash<>NEW.delta_hash OR
       d.target_type<>NEW.target_type OR d.target_id<>NEW.target_id OR d.target_lineage_id<>NEW.target_lineage_id OR
       d.target_version<>NEW.target_version OR d.target_hash<>NEW.target_hash OR p.proposed_change_hash<>d.delta_hash THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='governance artifact does not bind the exact proposal-owned delta tuple';
    END IF;
    RETURN NEW;
  END $fn$;

  CREATE TRIGGER qms_learning_delta_validate BEFORE INSERT ON qms.learning_proposal_canonical_delta FOR EACH ROW EXECUTE FUNCTION qms.foundation_0020_validate_delta();
  CREATE TRIGGER qms_learning_delta_guard BEFORE UPDATE OR DELETE ON qms.learning_proposal_canonical_delta FOR EACH ROW EXECUTE FUNCTION qms.foundation_0020_reject_delta_mutation();
  CREATE TRIGGER qms_learning_proposal_delta_validate BEFORE INSERT ON qms.learning_proposal FOR EACH ROW EXECUTE FUNCTION qms.foundation_0020_validate_binding();
  CREATE TRIGGER qms_learning_review_delta_validate BEFORE INSERT ON qms.learning_proposal_review FOR EACH ROW EXECUTE FUNCTION qms.foundation_0020_validate_binding();
  CREATE TRIGGER qms_learning_decision_delta_validate BEFORE INSERT ON qms.learning_proposal_decision FOR EACH ROW EXECUTE FUNCTION qms.foundation_0020_validate_binding();
  CREATE TRIGGER qms_learning_authorization_delta_validate BEFORE INSERT ON qms.learning_application_authorization FOR EACH ROW EXECUTE FUNCTION qms.foundation_0020_validate_binding();

  ALTER TABLE qms.learning_proposal_canonical_delta ENABLE ROW LEVEL SECURITY;
  ALTER TABLE qms.learning_proposal_canonical_delta FORCE ROW LEVEL SECURITY;
  EXECUTE format('CREATE POLICY qms_learning_delta_select ON qms.learning_proposal_canonical_delta FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',learning_role,reviewer_role,approver_role,authorizer_role);
  EXECUTE format('CREATE POLICY qms_learning_delta_insert ON qms.learning_proposal_canonical_delta FOR INSERT TO %I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',learning_role);
  EXECUTE format('CREATE POLICY qms_learning_delta_migrator ON qms.learning_proposal_canonical_delta FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);
  EXECUTE format('GRANT SELECT,INSERT ON qms.learning_proposal_canonical_delta TO %I',learning_role);
  EXECUTE format('GRANT SELECT ON qms.learning_proposal_canonical_delta TO %I,%I,%I',reviewer_role,approver_role,authorizer_role);
  EXECUTE format('GRANT EXECUTE ON FUNCTION qms.foundation_0020_complete_binding(uuid,text,text,text,text,text) TO %I,%I,%I,%I',learning_role,reviewer_role,approver_role,authorizer_role);
END $migration$;
REVOKE ALL ON FUNCTION qms.foundation_0020_complete_binding(uuid,text,text,text,text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.foundation_0020_validate_delta() FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.foundation_0020_validate_binding() FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.foundation_0020_reject_delta_mutation() FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.foundation_0020_canonical_json_value(jsonb) FROM PUBLIC;
"""

REVERSE_SQL = r"""
DO $migration$ BEGIN
 IF EXISTS(SELECT 1 FROM qms.learning_proposal_canonical_delta) THEN
   RAISE EXCEPTION '0020 is forward-only after exact learning delta history exists';
 END IF;
END $migration$;
DROP TABLE qms.learning_proposal_canonical_delta CASCADE;
DROP TRIGGER qms_learning_proposal_delta_validate ON qms.learning_proposal;
DROP TRIGGER qms_learning_review_delta_validate ON qms.learning_proposal_review;
DROP TRIGGER qms_learning_decision_delta_validate ON qms.learning_proposal_decision;
DROP TRIGGER qms_learning_authorization_delta_validate ON qms.learning_application_authorization;
ALTER TABLE qms.learning_application_authorization DROP COLUMN canonical_delta_id,DROP COLUMN canonicalization_version,DROP COLUMN delta_schema_version,DROP COLUMN operation_id,DROP COLUMN operation_version,DROP COLUMN delta_hash;
ALTER TABLE qms.learning_proposal_decision DROP COLUMN canonical_delta_id,DROP COLUMN canonicalization_version,DROP COLUMN delta_schema_version,DROP COLUMN operation_id,DROP COLUMN operation_version,DROP COLUMN delta_hash;
ALTER TABLE qms.learning_proposal_review DROP COLUMN canonical_delta_id,DROP COLUMN canonicalization_version,DROP COLUMN delta_schema_version,DROP COLUMN operation_id,DROP COLUMN operation_version,DROP COLUMN delta_hash;
ALTER TABLE qms.learning_proposal DROP COLUMN canonical_delta_id,DROP COLUMN canonicalization_version,DROP COLUMN delta_schema_version,DROP COLUMN operation_id,DROP COLUMN operation_version,DROP COLUMN delta_hash;
ALTER TABLE qms.learning_proposal ADD CONSTRAINT qms_learning_proposal_hashes CHECK(target_hash ~ '^[0-9a-f]{64}$' AND proposed_change_hash ~ '^[0-9a-f]{64}$');
ALTER TABLE qms.learning_application_authorization ADD CONSTRAINT qms_learning_authorization_capability CHECK(
 (target_type='ModelPolicy' AND capability_id='revise_model_policy') OR
 (target_type='AgentDefinition' AND capability_id='revise_agent_definition') OR
 (target_type='KnowledgeLayerRule' AND capability_id='revise_knowledge_layer_rule'));
DROP FUNCTION qms.foundation_0020_validate_binding();
DROP FUNCTION qms.foundation_0020_validate_delta();
DROP FUNCTION qms.foundation_0020_reject_delta_mutation();
DROP FUNCTION qms.foundation_0020_canonical_json_value(jsonb);
DROP FUNCTION qms.foundation_0020_complete_binding(uuid,text,text,text,text,text);
"""


def forward(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


binding_fields = [
    ("canonical_delta_id", models.UUIDField(blank=True, null=True)),
    ("canonicalization_version", models.CharField(blank=True, max_length=80, null=True)),
    ("delta_schema_version", models.CharField(blank=True, max_length=120, null=True)),
    ("operation_id", models.CharField(blank=True, max_length=160, null=True)),
    ("operation_version", models.CharField(blank=True, max_length=40, null=True)),
    ("delta_hash", models.CharField(blank=True, max_length=64, null=True)),
]


class Migration(migrations.Migration):
    dependencies = [("foundation", "0019_learning_proposal_review_application_authorization_foundation")]
    state_operations = [
        migrations.CreateModel(
            name="LearningProposalCanonicalDelta",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("canonicalization_version", models.CharField(max_length=80)),
                ("delta_schema_version", models.CharField(max_length=120)),
                ("operation_id", models.CharField(max_length=160)),
                ("operation_version", models.CharField(max_length=40)),
                ("target_type", models.CharField(max_length=80)), ("target_id", models.UUIDField()),
                ("target_lineage_id", models.UUIDField()), ("target_version", models.CharField(max_length=120)),
                ("target_hash", models.CharField(max_length=64)), ("delta_document", models.JSONField()),
                ("canonical_bytes", models.BinaryField()), ("delta_hash", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("learning_proposal", models.OneToOneField(db_column="learning_proposal_id", on_delete=django.db.models.deletion.PROTECT, related_name="owned_canonical_delta", to="foundation.learningproposal")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
            ], options={"db_table": 'qms"."learning_proposal_canonical_delta', "managed": False},
        ),
        migrations.AddField(
            model_name="learningproposal", name="canonical_delta",
            field=models.OneToOneField(blank=True, db_column="canonical_delta_id", null=True,
                on_delete=django.db.models.deletion.PROTECT, related_name="bound_proposal",
                to="foundation.learningproposalcanonicaldelta"),
        ),
    ]
    for model_name in ("learningproposalreview", "learningproposaldecision", "learningapplicationauthorization"):
        for name, field in binding_fields:
            state_operations.append(migrations.AddField(model_name=model_name, name=name, field=field))
    for name, field in binding_fields[1:]:
        state_operations.append(migrations.AddField(model_name="learningproposal", name=name, field=field))
    operations = [migrations.SeparateDatabaseAndState(
        database_operations=[migrations.RunPython(forward, reverse)],
        state_operations=state_operations,
    )]
