"""Phase 11 governed AgentDefinition, ModelPolicy and AgentRun provenance."""

import uuid

import django.db.models.deletion
from django.db import migrations, models


FORWARD_SQL = r"""
DO $migration$
DECLARE
    app_role text := current_setting('foundation.app_role', true);
    worker_role text := current_setting('foundation.worker_role', true);
    projector_role text := current_setting('foundation.projector_role', true);
    curator_role text := current_setting('foundation.agent_catalog_curator_role', true);
BEGIN
    IF app_role IS NULL OR app_role='' OR worker_role IS NULL OR worker_role='' OR
       projector_role IS NULL OR projector_role='' OR curator_role IS NULL OR curator_role='' THEN
        RAISE EXCEPTION 'Phase 11 runtime and agent catalog curator roles are required';
    END IF;

    CREATE SCHEMA IF NOT EXISTS governance;

    CREATE TABLE governance.model_policy (
        id uuid PRIMARY KEY,
        lineage_id uuid NOT NULL,
        policy_key varchar(160) NOT NULL,
        version varchar(80) NOT NULL,
        previous_revision_id uuid UNIQUE,
        approved_models jsonb NOT NULL DEFAULT '[]'::jsonb,
        data_classes jsonb NOT NULL DEFAULT '[]'::jsonb,
        guardrails jsonb NOT NULL DEFAULT '{}'::jsonb,
        human_gate_rules jsonb NOT NULL DEFAULT '{}'::jsonb,
        status varchar(24) NOT NULL DEFAULT 'draft',
        published_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT governance_model_policy_previous_fk FOREIGN KEY(previous_revision_id)
          REFERENCES governance.model_policy(id) ON DELETE RESTRICT,
        CONSTRAINT governance_model_policy_lineage_version_unique UNIQUE(lineage_id,version),
        CONSTRAINT governance_model_policy_key_version_unique UNIQUE(policy_key,version),
        CONSTRAINT governance_model_policy_status CHECK(status IN ('draft','published')),
        CONSTRAINT governance_model_policy_key_nonblank CHECK(btrim(policy_key)<>''),
        CONSTRAINT governance_model_policy_version_nonblank CHECK(btrim(version)<>''),
        CONSTRAINT governance_model_policy_json_shapes CHECK(
          jsonb_typeof(approved_models)='array' AND jsonb_typeof(data_classes)='array' AND
          jsonb_typeof(guardrails)='object' AND jsonb_typeof(human_gate_rules)='object'),
        CONSTRAINT governance_model_policy_publication_time CHECK(
          (status='draft' AND published_at IS NULL) OR (status='published' AND published_at IS NOT NULL))
    );
    CREATE UNIQUE INDEX governance_model_policy_root_unique
      ON governance.model_policy(policy_key) WHERE previous_revision_id IS NULL;

    CREATE TABLE governance.agent_definition (
        id uuid PRIMARY KEY,
        lineage_id uuid NOT NULL,
        agent_key varchar(160) NOT NULL,
        name varchar(240) NOT NULL,
        version varchar(80) NOT NULL,
        previous_revision_id uuid UNIQUE,
        purpose text NOT NULL,
        capability varchar(160) NOT NULL,
        autonomy_max smallint NOT NULL,
        model_policy_id uuid NOT NULL REFERENCES governance.model_policy(id) ON DELETE RESTRICT,
        status varchar(24) NOT NULL DEFAULT 'draft',
        published_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT governance_agent_definition_previous_fk FOREIGN KEY(previous_revision_id)
          REFERENCES governance.agent_definition(id) ON DELETE RESTRICT,
        CONSTRAINT governance_agent_definition_lineage_version_unique UNIQUE(lineage_id,version),
        CONSTRAINT governance_agent_definition_key_version_unique UNIQUE(agent_key,version),
        CONSTRAINT governance_agent_definition_status CHECK(status IN ('draft','published')),
        CONSTRAINT governance_agent_definition_autonomy CHECK(autonomy_max BETWEEN 0 AND 4),
        CONSTRAINT governance_agent_definition_nonblank CHECK(
          btrim(agent_key)<>'' AND btrim(name)<>'' AND btrim(version)<>'' AND
          btrim(purpose)<>'' AND btrim(capability)<>''),
        CONSTRAINT governance_agent_definition_publication_time CHECK(
          (status='draft' AND published_at IS NULL) OR (status='published' AND published_at IS NOT NULL))
    );
    CREATE UNIQUE INDEX governance_agent_definition_root_unique
      ON governance.agent_definition(agent_key) WHERE previous_revision_id IS NULL;

    CREATE TABLE governance.curation_audit (
        id uuid PRIMARY KEY,
        action varchar(160) NOT NULL,
        entity_type varchar(120) NOT NULL,
        entity_id uuid NOT NULL,
        actor_id varchar(255) NOT NULL,
        trace_id uuid NOT NULL,
        payload_hash varchar(64) NOT NULL,
        occurred_at timestamptz NOT NULL,
        CONSTRAINT governance_curation_audit_nonblank CHECK(
          btrim(action)<>'' AND btrim(entity_type)<>'' AND btrim(actor_id)<>''),
        CONSTRAINT governance_curation_audit_hash CHECK(payload_hash ~ '^[0-9a-f]{64}$')
    );

    CREATE TABLE qms.agent_run (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        agent_definition_id uuid NOT NULL REFERENCES governance.agent_definition(id) ON DELETE RESTRICT,
        model_policy_id uuid NOT NULL REFERENCES governance.model_policy(id) ON DELETE RESTRICT,
        capability varchar(160) NOT NULL,
        status varchar(24) NOT NULL DEFAULT 'running',
        requested_autonomy smallint NOT NULL,
        effective_autonomy_ceiling smallint NOT NULL,
        model_provider varchar(120),
        model_identifier varchar(200) NOT NULL,
        model_version varchar(120) NOT NULL,
        prompt_version varchar(120) NOT NULL,
        rule_bundle_version varchar(120) NOT NULL,
        dataset_version_reference text,
        embedding_namespace text,
        trace_id uuid NOT NULL,
        correlation_id uuid,
        causation_id uuid,
        started_at timestamptz NOT NULL,
        completed_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_agent_run_tenant_org_id_unique UNIQUE(tenant_id,organization_id,id),
        CONSTRAINT qms_agent_run_org_fk FOREIGN KEY(tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_agent_run_status CHECK(status IN ('running','completed','failed')),
        CONSTRAINT qms_agent_run_autonomy CHECK(
          requested_autonomy BETWEEN 0 AND 4 AND effective_autonomy_ceiling BETWEEN 0 AND 4 AND
          requested_autonomy <= effective_autonomy_ceiling),
        CONSTRAINT qms_agent_run_nonblank CHECK(
          btrim(capability)<>'' AND btrim(model_identifier)<>'' AND btrim(model_version)<>'' AND
          btrim(prompt_version)<>'' AND btrim(rule_bundle_version)<>''),
        CONSTRAINT qms_agent_run_completion CHECK(
          (status='running' AND completed_at IS NULL) OR
          (status IN ('completed','failed') AND completed_at IS NOT NULL AND completed_at>=started_at))
    );

    CREATE TABLE qms.agent_run_input (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        agent_run_id uuid NOT NULL,
        standard_edition_id uuid NOT NULL,
        requirement_control_id uuid NOT NULL,
        knowledge_layer_rule_id uuid NOT NULL REFERENCES normative.knowledge_layer_rule(id) ON DELETE RESTRICT,
        evidence_id uuid NOT NULL,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_agent_run_input_parent_fk FOREIGN KEY(tenant_id,organization_id,agent_run_id)
          REFERENCES qms.agent_run(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_agent_run_input_org_fk FOREIGN KEY(tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_agent_run_input_requirement_fk FOREIGN KEY(standard_edition_id,requirement_control_id)
          REFERENCES normative.requirement_control(standard_edition_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_agent_run_input_evidence_fk FOREIGN KEY(tenant_id,organization_id,evidence_id)
          REFERENCES qms.evidence(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_agent_run_input_exact_unique UNIQUE(
          agent_run_id,requirement_control_id,knowledge_layer_rule_id,evidence_id)
    );

    CREATE TABLE qms.agent_run_recommendation (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        agent_run_id uuid NOT NULL UNIQUE,
        recommendation_id uuid NOT NULL UNIQUE,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_agent_run_recommendation_run_fk FOREIGN KEY(tenant_id,organization_id,agent_run_id)
          REFERENCES qms.agent_run(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_agent_run_recommendation_output_fk FOREIGN KEY(tenant_id,organization_id,recommendation_id)
          REFERENCES qms.recommendation(tenant_id,organization_id,id) ON DELETE RESTRICT
    );

    CREATE INDEX qms_agent_run_tenant_org_started_idx ON qms.agent_run(tenant_id,organization_id,started_at);
    CREATE INDEX qms_agent_run_input_parent_idx ON qms.agent_run_input(tenant_id,organization_id,agent_run_id);

    CREATE FUNCTION governance.foundation_0011_validate_catalog_revision()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,governance AS $fn$
    DECLARE predecessor record; item jsonb;
    BEGIN
      IF TG_TABLE_NAME='model_policy' THEN
        FOR item IN SELECT value FROM jsonb_array_elements(NEW.approved_models) LOOP
          IF jsonb_typeof(item)<>'string' OR btrim(item #>> '{}')='' THEN
            RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='approved_models must contain nonblank strings';
          END IF;
        END LOOP;
      END IF;
      IF NEW.previous_revision_id IS NULL THEN
        IF NEW.lineage_id<>NEW.id THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='catalog root lineage must equal id'; END IF;
      ELSE
        IF TG_TABLE_NAME='model_policy' THEN
          SELECT lineage_id,policy_key AS logical_key,status INTO predecessor
            FROM governance.model_policy WHERE id=NEW.previous_revision_id;
          IF predecessor.status IS DISTINCT FROM 'published' OR predecessor.lineage_id<>NEW.lineage_id OR
             predecessor.logical_key IS DISTINCT FROM NEW.policy_key THEN
            RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='catalog revision requires exact published predecessor in same lineage';
          END IF;
        ELSE
          SELECT lineage_id,agent_key AS logical_key,status INTO predecessor
            FROM governance.agent_definition WHERE id=NEW.previous_revision_id;
          IF predecessor.status IS DISTINCT FROM 'published' OR predecessor.lineage_id<>NEW.lineage_id OR
             predecessor.logical_key IS DISTINCT FROM NEW.agent_key THEN
            RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='catalog revision requires exact published predecessor in same lineage';
          END IF;
        END IF;
      END IF;
      RETURN NEW;
    END $fn$;

    CREATE FUNCTION governance.foundation_0011_guard_catalog_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,governance AS $fn$
    BEGIN
      IF TG_OP='DELETE' THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='agent catalog history is append-only'; END IF;
      IF OLD.status='draft' AND NEW.status='published' AND NEW.published_at IS NOT NULL AND
         ROW(OLD.id,OLD.lineage_id,OLD.previous_revision_id) IS NOT DISTINCT FROM
         ROW(NEW.id,NEW.lineage_id,NEW.previous_revision_id) THEN
        IF TG_TABLE_NAME='model_policy' THEN
          IF ROW(OLD.policy_key,OLD.version,OLD.approved_models,OLD.data_classes,OLD.guardrails,OLD.human_gate_rules,OLD.created_at)
             IS DISTINCT FROM ROW(NEW.policy_key,NEW.version,NEW.approved_models,NEW.data_classes,NEW.guardrails,NEW.human_gate_rules,NEW.created_at)
            THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='policy material cannot change during publication'; END IF;
        ELSE
          IF ROW(OLD.agent_key,OLD.name,OLD.version,OLD.purpose,OLD.capability,OLD.autonomy_max,OLD.model_policy_id,OLD.created_at)
             IS DISTINCT FROM ROW(NEW.agent_key,NEW.name,NEW.version,NEW.purpose,NEW.capability,NEW.autonomy_max,NEW.model_policy_id,NEW.created_at)
            THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='agent definition material cannot change during publication'; END IF;
        END IF;
        RETURN NEW;
      END IF;
      RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='published catalog rows are immutable; create a new version';
    END $fn$;

    CREATE FUNCTION governance.foundation_0011_reject_curation_audit_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,governance AS $fn$
    BEGIN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='agent catalog curation audit is append-only'; END $fn$;

    CREATE FUNCTION qms.foundation_0011_validate_run()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms,governance AS $fn$
    DECLARE definition record; policy_status text;
    BEGIN
      SELECT status,capability,autonomy_max,model_policy_id INTO definition
        FROM governance.agent_definition WHERE id=NEW.agent_definition_id;
      SELECT status INTO policy_status FROM governance.model_policy WHERE id=NEW.model_policy_id;
      IF definition.status IS DISTINCT FROM 'published' OR policy_status IS DISTINCT FROM 'published' THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='agent run requires exact published definition and policy versions';
      END IF;
      IF definition.capability<>NEW.capability OR definition.model_policy_id<>NEW.model_policy_id OR
         NEW.effective_autonomy_ceiling>definition.autonomy_max THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='agent run metadata exceeds exact definition or policy binding';
      END IF;
      RETURN NEW;
    END $fn$;

    CREATE FUNCTION qms.foundation_0011_guard_run_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    BEGIN
      IF TG_OP='DELETE' THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='agent run history is immutable'; END IF;
      IF OLD.status='running' AND NEW.status IN ('completed','failed') AND NEW.completed_at IS NOT NULL AND
         ROW(OLD.id,OLD.tenant_id,OLD.organization_id,OLD.agent_definition_id,OLD.model_policy_id,OLD.capability,
             OLD.requested_autonomy,OLD.effective_autonomy_ceiling,OLD.model_provider,OLD.model_identifier,
             OLD.model_version,OLD.prompt_version,OLD.rule_bundle_version,OLD.dataset_version_reference,
             OLD.embedding_namespace,OLD.trace_id,OLD.correlation_id,OLD.causation_id,OLD.started_at,OLD.created_at)
         IS NOT DISTINCT FROM
         ROW(NEW.id,NEW.tenant_id,NEW.organization_id,NEW.agent_definition_id,NEW.model_policy_id,NEW.capability,
             NEW.requested_autonomy,NEW.effective_autonomy_ceiling,NEW.model_provider,NEW.model_identifier,
             NEW.model_version,NEW.prompt_version,NEW.rule_bundle_version,NEW.dataset_version_reference,
             NEW.embedding_namespace,NEW.trace_id,NEW.correlation_id,NEW.causation_id,NEW.started_at,NEW.created_at) THEN
        IF NEW.status='completed' AND NOT EXISTS(SELECT 1 FROM qms.agent_run_recommendation WHERE agent_run_id=OLD.id) THEN
          RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='completed agent run requires exact Recommendation linkage';
        END IF;
        RETURN NEW;
      END IF;
      RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='agent run provenance is immutable after start';
    END $fn$;

    CREATE FUNCTION qms.foundation_0011_validate_input()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms,normative AS $fn$
    DECLARE edition_status text; rule_status text; run_status text;
    BEGIN
      SELECT status INTO edition_status FROM normative.standard_edition WHERE id=NEW.standard_edition_id;
      SELECT status INTO rule_status FROM normative.knowledge_layer_rule WHERE id=NEW.knowledge_layer_rule_id;
      SELECT status INTO run_status FROM qms.agent_run WHERE id=NEW.agent_run_id;
      IF edition_status IS DISTINCT FROM 'published' OR rule_status IS DISTINCT FROM 'published' OR run_status IS DISTINCT FROM 'running' THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='run input requires running run and exact published edition/rule';
      END IF;
      RETURN NEW;
    END $fn$;

    CREATE FUNCTION qms.foundation_0011_reject_frozen_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    BEGIN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='agent run input/output provenance is append-only frozen history'; END $fn$;

    CREATE FUNCTION qms.foundation_0011_require_inputs()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    BEGIN
      IF NOT EXISTS(SELECT 1 FROM qms.agent_run_input WHERE agent_run_id=NEW.id) THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='agent run start requires frozen inputs';
      END IF;
      RETURN NULL;
    END $fn$;

    CREATE FUNCTION qms.foundation_0011_validate_recommendation_link()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    BEGIN
      IF EXISTS(
        (SELECT standard_edition_id,requirement_control_id,knowledge_layer_rule_id,evidence_id
           FROM qms.agent_run_input WHERE agent_run_id=NEW.agent_run_id
         EXCEPT
         SELECT standard_edition_id,requirement_control_id,knowledge_layer_rule_id,evidence_id
           FROM qms.recommendation_basis WHERE recommendation_id=NEW.recommendation_id)
        UNION ALL
        (SELECT standard_edition_id,requirement_control_id,knowledge_layer_rule_id,evidence_id
           FROM qms.recommendation_basis WHERE recommendation_id=NEW.recommendation_id
         EXCEPT
         SELECT standard_edition_id,requirement_control_id,knowledge_layer_rule_id,evidence_id
           FROM qms.agent_run_input WHERE agent_run_id=NEW.agent_run_id)
      ) THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RecommendationBasis must exactly match frozen AgentRun inputs';
      END IF;
      RETURN NEW;
    END $fn$;

    CREATE TRIGGER governance_model_policy_validate BEFORE INSERT ON governance.model_policy
      FOR EACH ROW EXECUTE FUNCTION governance.foundation_0011_validate_catalog_revision();
    CREATE TRIGGER governance_agent_definition_validate BEFORE INSERT ON governance.agent_definition
      FOR EACH ROW EXECUTE FUNCTION governance.foundation_0011_validate_catalog_revision();
    CREATE TRIGGER governance_model_policy_guard BEFORE UPDATE OR DELETE ON governance.model_policy
      FOR EACH ROW EXECUTE FUNCTION governance.foundation_0011_guard_catalog_mutation();
    CREATE TRIGGER governance_agent_definition_guard BEFORE UPDATE OR DELETE ON governance.agent_definition
      FOR EACH ROW EXECUTE FUNCTION governance.foundation_0011_guard_catalog_mutation();
    CREATE TRIGGER governance_curation_audit_guard BEFORE UPDATE OR DELETE ON governance.curation_audit
      FOR EACH ROW EXECUTE FUNCTION governance.foundation_0011_reject_curation_audit_mutation();
    CREATE TRIGGER qms_agent_run_validate BEFORE INSERT ON qms.agent_run
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0011_validate_run();
    CREATE TRIGGER qms_agent_run_guard BEFORE UPDATE OR DELETE ON qms.agent_run
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0011_guard_run_mutation();
    CREATE TRIGGER qms_agent_run_input_validate BEFORE INSERT ON qms.agent_run_input
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0011_validate_input();
    CREATE TRIGGER qms_agent_run_input_guard BEFORE UPDATE OR DELETE ON qms.agent_run_input
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0011_reject_frozen_mutation();
    CREATE TRIGGER qms_agent_run_recommendation_validate BEFORE INSERT ON qms.agent_run_recommendation
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0011_validate_recommendation_link();
    CREATE TRIGGER qms_agent_run_recommendation_guard BEFORE UPDATE OR DELETE ON qms.agent_run_recommendation
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0011_reject_frozen_mutation();
    CREATE CONSTRAINT TRIGGER qms_agent_run_inputs_complete AFTER INSERT ON qms.agent_run
      DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION qms.foundation_0011_require_inputs();

    ALTER TABLE qms.agent_run ENABLE ROW LEVEL SECURITY;
    ALTER TABLE qms.agent_run FORCE ROW LEVEL SECURITY;
    ALTER TABLE qms.agent_run_input ENABLE ROW LEVEL SECURITY;
    ALTER TABLE qms.agent_run_input FORCE ROW LEVEL SECURITY;
    ALTER TABLE qms.agent_run_recommendation ENABLE ROW LEVEL SECURITY;
    ALTER TABLE qms.agent_run_recommendation FORCE ROW LEVEL SECURITY;

    EXECUTE format('CREATE POLICY qms_agent_run_select ON qms.agent_run FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY qms_agent_run_insert ON qms.agent_run FOR INSERT TO %I,%I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY qms_agent_run_update ON qms.agent_run FOR UPDATE TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY qms_agent_run_delete ON qms.agent_run FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_agent_run_migrator ON qms.agent_run FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);

    EXECUTE format('CREATE POLICY qms_agent_run_input_select ON qms.agent_run_input FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY qms_agent_run_input_insert ON qms.agent_run_input FOR INSERT TO %I,%I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY qms_agent_run_input_update ON qms.agent_run_input FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_agent_run_input_delete ON qms.agent_run_input FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_agent_run_input_migrator ON qms.agent_run_input FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);

    EXECUTE format('CREATE POLICY qms_agent_run_recommendation_select ON qms.agent_run_recommendation FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY qms_agent_run_recommendation_insert ON qms.agent_run_recommendation FOR INSERT TO %I,%I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY qms_agent_run_recommendation_update ON qms.agent_run_recommendation FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_agent_run_recommendation_delete ON qms.agent_run_recommendation FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_agent_run_recommendation_migrator ON qms.agent_run_recommendation FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);

    EXECUTE format('GRANT USAGE ON SCHEMA governance TO %I,%I,%I,%I',app_role,worker_role,projector_role,curator_role);
    EXECUTE format('GRANT SELECT ON governance.model_policy,governance.agent_definition TO %I,%I,%I,%I',app_role,worker_role,projector_role,curator_role);
    EXECUTE format('GRANT INSERT ON governance.model_policy,governance.agent_definition,governance.curation_audit TO %I',curator_role);
    EXECUTE format('GRANT SELECT ON governance.curation_audit TO %I',curator_role);
    EXECUTE format('GRANT UPDATE(status,published_at) ON governance.model_policy,governance.agent_definition TO %I',curator_role);
    EXECUTE format('GRANT SELECT,INSERT ON qms.agent_run_input,qms.agent_run_recommendation TO %I,%I',app_role,worker_role);
    EXECUTE format('GRANT SELECT,INSERT ON qms.agent_run TO %I,%I',app_role,worker_role);
    EXECUTE format('GRANT UPDATE(status,completed_at) ON qms.agent_run TO %I,%I',app_role,worker_role);

    -- AgentRun is a tenant-scoped producer, so the worker receives only the
    -- append permissions needed for typed DomainEvent + Outbox creation.
    DROP POLICY foundation_domain_event_insert ON eventing.domain_event;
    DROP POLICY foundation_outbox_insert ON eventing.transactional_outbox;
    EXECUTE format('CREATE POLICY foundation_domain_event_insert ON eventing.domain_event FOR INSERT TO %I,%I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY foundation_outbox_insert ON eventing.transactional_outbox FOR INSERT TO %I,%I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('GRANT INSERT ON eventing.domain_event,eventing.transactional_outbox TO %I',worker_role);

    -- Phase 11 permits the tenant-scoped worker to use the already-governed
    -- Recommendation creation boundary; all Phase 10 constraints remain active.
    DROP POLICY qms_recommendation_insert ON qms.recommendation;
    DROP POLICY qms_recommendation_basis_insert ON qms.recommendation_basis;
    EXECUTE format('CREATE POLICY qms_recommendation_insert ON qms.recommendation FOR INSERT TO %I,%I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY qms_recommendation_basis_insert ON qms.recommendation_basis FOR INSERT TO %I,%I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('GRANT INSERT ON qms.recommendation,qms.recommendation_basis TO %I',worker_role);
END
$migration$;
"""


REVERSE_SQL = r"""
DO $migration$
DECLARE app_role text := current_setting('foundation.app_role',true); worker_role text := current_setting('foundation.worker_role',true);
BEGIN
  IF worker_role IS NOT NULL AND worker_role<>'' THEN
    EXECUTE format('REVOKE INSERT ON eventing.domain_event,eventing.transactional_outbox FROM %I',worker_role);
    DROP POLICY foundation_domain_event_insert ON eventing.domain_event;
    DROP POLICY foundation_outbox_insert ON eventing.transactional_outbox;
    EXECUTE format('CREATE POLICY foundation_domain_event_insert ON eventing.domain_event FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY foundation_outbox_insert ON eventing.transactional_outbox FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
  END IF;
  REVOKE INSERT ON qms.recommendation,qms.recommendation_basis FROM CURRENT_USER;
  IF worker_role IS NOT NULL AND worker_role<>'' THEN
    EXECUTE format('REVOKE INSERT ON qms.recommendation,qms.recommendation_basis FROM %I',worker_role);
    DROP POLICY qms_recommendation_insert ON qms.recommendation;
    DROP POLICY qms_recommendation_basis_insert ON qms.recommendation_basis;
    EXECUTE format('CREATE POLICY qms_recommendation_insert ON qms.recommendation FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_recommendation_basis_insert ON qms.recommendation_basis FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
  END IF;
END $migration$;
DROP TABLE qms.agent_run_recommendation;
DROP TABLE qms.agent_run_input;
DROP TABLE qms.agent_run;
DROP TABLE governance.agent_definition;
DROP TABLE governance.model_policy;
DROP TABLE governance.curation_audit;
DROP FUNCTION qms.foundation_0011_validate_recommendation_link();
DROP FUNCTION qms.foundation_0011_require_inputs();
DROP FUNCTION qms.foundation_0011_reject_frozen_mutation();
DROP FUNCTION qms.foundation_0011_validate_input();
DROP FUNCTION qms.foundation_0011_guard_run_mutation();
DROP FUNCTION qms.foundation_0011_validate_run();
DROP FUNCTION governance.foundation_0011_reject_curation_audit_mutation();
DROP FUNCTION governance.foundation_0011_guard_catalog_mutation();
DROP FUNCTION governance.foundation_0011_validate_catalog_revision();
DROP SCHEMA governance;
"""


def apply_phase11(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_phase11(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0010_governed_recommendation_foundation")]
    operations = [migrations.SeparateDatabaseAndState(
        database_operations=[migrations.RunPython(apply_phase11, reverse_phase11)],
        state_operations=[
            migrations.CreateModel(name="ModelPolicy", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("lineage_id", models.UUIDField()), ("policy_key", models.CharField(max_length=160)),
                ("version", models.CharField(max_length=80)), ("approved_models", models.JSONField(default=list)),
                ("data_classes", models.JSONField(default=list)), ("guardrails", models.JSONField(default=dict)),
                ("human_gate_rules", models.JSONField(default=dict)),
                ("status", models.CharField(choices=[("draft","Draft"),("published","Published")],default="draft",max_length=24)),
                ("published_at", models.DateTimeField(blank=True,null=True)), ("created_at", models.DateTimeField(auto_now_add=True)),
                ("previous_revision", models.OneToOneField(blank=True,db_column="previous_revision_id",null=True,on_delete=django.db.models.deletion.PROTECT,related_name="next_revision",to="foundation.modelpolicy")),
            ], options={"managed":False,"db_table":'governance"."model_policy'}),
            migrations.CreateModel(name="AgentDefinition", fields=[
                ("id", models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),
                ("lineage_id",models.UUIDField()),("agent_key",models.CharField(max_length=160)),("name",models.CharField(max_length=240)),
                ("version",models.CharField(max_length=80)),("purpose",models.TextField()),("capability",models.CharField(max_length=160)),
                ("autonomy_max",models.PositiveSmallIntegerField()),
                ("status",models.CharField(choices=[("draft","Draft"),("published","Published")],default="draft",max_length=24)),
                ("published_at",models.DateTimeField(blank=True,null=True)),("created_at",models.DateTimeField(auto_now_add=True)),
                ("previous_revision",models.OneToOneField(blank=True,db_column="previous_revision_id",null=True,on_delete=django.db.models.deletion.PROTECT,related_name="next_revision",to="foundation.agentdefinition")),
                ("model_policy",models.ForeignKey(db_column="model_policy_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.modelpolicy")),
            ],options={"managed":False,"db_table":'governance"."agent_definition'}),
            migrations.CreateModel(name="AgentCatalogCurationAudit",fields=[
                ("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),("action",models.CharField(max_length=160)),
                ("entity_type",models.CharField(max_length=120)),("entity_id",models.UUIDField()),("actor_id",models.CharField(max_length=255)),
                ("trace_id",models.UUIDField()),("payload_hash",models.CharField(max_length=64)),("occurred_at",models.DateTimeField()),
            ],options={"managed":False,"db_table":'governance"."curation_audit'}),
            migrations.CreateModel(name="AgentRun",fields=[
                ("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),("capability",models.CharField(max_length=160)),
                ("status",models.CharField(choices=[("running","Running"),("completed","Completed"),("failed","Failed")],default="running",max_length=24)),
                ("requested_autonomy",models.PositiveSmallIntegerField()),("effective_autonomy_ceiling",models.PositiveSmallIntegerField()),
                ("model_provider",models.CharField(blank=True,max_length=120,null=True)),("model_identifier",models.CharField(max_length=200)),
                ("model_version",models.CharField(max_length=120)),("prompt_version",models.CharField(max_length=120)),
                ("rule_bundle_version",models.CharField(max_length=120)),("dataset_version_reference",models.TextField(blank=True,null=True)),
                ("embedding_namespace",models.TextField(blank=True,null=True)),("trace_id",models.UUIDField()),
                ("correlation_id",models.UUIDField(blank=True,null=True)),("causation_id",models.UUIDField(blank=True,null=True)),
                ("started_at",models.DateTimeField()),("completed_at",models.DateTimeField(blank=True,null=True)),("created_at",models.DateTimeField(auto_now_add=True)),
                ("tenant",models.ForeignKey(db_column="tenant_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.tenantprojection")),
                ("organization",models.ForeignKey(db_column="organization_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.organization")),
                ("agent_definition",models.ForeignKey(db_column="agent_definition_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.agentdefinition")),
                ("model_policy",models.ForeignKey(db_column="model_policy_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.modelpolicy")),
            ],options={"managed":False,"db_table":'qms"."agent_run'}),
            migrations.CreateModel(name="AgentRunInput",fields=[
                ("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),("created_at",models.DateTimeField(auto_now_add=True)),
                ("tenant",models.ForeignKey(db_column="tenant_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.tenantprojection")),
                ("organization",models.ForeignKey(db_column="organization_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.organization")),
                ("agent_run",models.ForeignKey(db_column="agent_run_id",on_delete=django.db.models.deletion.PROTECT,related_name="frozen_inputs",to="foundation.agentrun")),
                ("standard_edition",models.ForeignKey(db_column="standard_edition_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.standardedition")),
                ("requirement_control",models.ForeignKey(db_column="requirement_control_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.requirementcontrol")),
                ("knowledge_layer_rule",models.ForeignKey(db_column="knowledge_layer_rule_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.knowledgelayerrule")),
                ("evidence",models.ForeignKey(db_column="evidence_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.evidence")),
            ],options={"managed":False,"db_table":'qms"."agent_run_input'}),
            migrations.CreateModel(name="AgentRunRecommendation",fields=[
                ("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),("created_at",models.DateTimeField(auto_now_add=True)),
                ("tenant",models.ForeignKey(db_column="tenant_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.tenantprojection")),
                ("organization",models.ForeignKey(db_column="organization_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.organization")),
                ("agent_run",models.OneToOneField(db_column="agent_run_id",on_delete=django.db.models.deletion.PROTECT,related_name="recommendation_link",to="foundation.agentrun")),
                ("recommendation",models.OneToOneField(db_column="recommendation_id",on_delete=django.db.models.deletion.PROTECT,related_name="agent_run_link",to="foundation.recommendation")),
            ],options={"managed":False,"db_table":'qms"."agent_run_recommendation'}),
        ],
    )]
