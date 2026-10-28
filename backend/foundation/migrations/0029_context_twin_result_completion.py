from django.db import migrations


FORWARD_SQL = r"""
CREATE OR REPLACE FUNCTION qms.foundation_0011_guard_run_mutation()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
DECLARE metadata_result_exists boolean := false;
BEGIN
  IF TG_OP='DELETE' THEN
    RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='agent run history is immutable';
  END IF;
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
    IF NEW.status='completed' AND NOT EXISTS(
      SELECT 1 FROM qms.agent_run_recommendation WHERE agent_run_id=OLD.id
    ) THEN
      SELECT EXISTS(
        SELECT 1 FROM eventing.domain_event AS event
        WHERE event.tenant_id=OLD.tenant_id
          AND event.aggregate_type='agent_run'
          AND event.aggregate_id=OLD.id
          AND event.event_type='agent_run.completed'
          AND event.payload->'execution_result'->>'not_normative_assessment'='true'
          AND event.payload->'execution_result'->'provenance'->>'agent_run_id'=OLD.id::text
          AND event.payload->'execution_result'->'provenance'->>'input_snapshot_hash' ~ '^[0-9a-f]{64}$'
          AND jsonb_typeof(event.payload->'execution_result'->'semantic_result')='object'
          AND (
            (OLD.capability='source.context_twin_orchestrator'
              AND event.payload->'execution_result'->>'result_scope'='heuristic_metadata_analysis_only'
              AND event.payload->'execution_result'->'provenance'->>'adapter'='ContextTwinMetadataAdapter'
              AND event.payload->'execution_result'->'provenance' ? 'input_snapshot'
              AND event.payload->'execution_result'->'provenance' ? 'evidence_ids')
            OR
            (OLD.capability='source.scope_assurance_agent'
              AND event.payload->'execution_result'->>'result_scope'='structural_scope_process_count_only'
              AND event.payload->'execution_result'->'provenance'->>'adapter'='ScopeAssuranceProcessCountAdapter'
              AND event.payload->'execution_result'->'provenance' ? 'scope_snapshot'
              AND event.payload->'execution_result'->'provenance'->>'scope_id' IS NOT NULL
              AND jsonb_typeof(event.payload->'execution_result'->'semantic_result'->'linked_process_count')='number')
            OR
            (OLD.capability='source.process_graph_agent'
              AND event.payload->'execution_result'->>'result_scope'='canonical_process_relationship_graph_only'
              AND event.payload->'execution_result'->'provenance'->>'adapter'='ProcessGraphAdapter'
              AND event.payload->'execution_result'->'provenance' ? 'canonical_graph_snapshot'
              AND jsonb_typeof(event.payload->'execution_result'->'semantic_result'->'nodes')='array'
              AND jsonb_typeof(event.payload->'execution_result'->'semantic_result'->'edges')='array')
          )
      ) INTO metadata_result_exists;
      IF NOT metadata_result_exists THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='completed agent run requires Recommendation or exact Context Twin metadata result';
      END IF;
    END IF;
    RETURN NEW;
  END IF;
  RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='agent run provenance is immutable after start';
END $fn$;
"""

REVERSE_SQL = r"""
CREATE OR REPLACE FUNCTION qms.foundation_0011_guard_run_mutation()
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
"""


class Migration(migrations.Migration):
    dependencies = [("foundation", "0028_capability_activation")]
    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]