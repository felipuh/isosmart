import inspect
import json
from pathlib import Path
from uuid import UUID

from django.apps import apps
from django.test import SimpleTestCase

from foundation.adminapps_adapter import ContractOnlyAdminAppsAdapter
from foundation.failure_semantics import BoundaryStatus
from foundation.canonical import CANONICAL_JSON_VERSION, canonical_hash, canonical_json
from foundation.eventing import OrganizationEventingService, PayloadIntegrityConflict
from foundation.models import (
    ActionPlan,
    ActionPlanDryRun,
    ActionExecution,
    ActionExecutionReceipt,
    AgentDefinition,
    AgentDecision,
    AgentRun,
    AgentRunInput,
    AgentRunRecommendation,
    Approval,
    Change,
    ChangeProcess,
    ContextItem,
    ConsumerReceipt,
    DomainEvent,
    Document,
    DocumentVersion,
    Evidence,
    EvidenceCoverage,
    EffectivenessCheck,
    EffectivenessEvidence,
    LearningProposal,
    LearningProposalReview,
    LearningProposalDecision,
    LearningApplicationAuthorization,
    LearningProposalSignal,
    LearningSignal,
    LearningSignalEffectiveness,
    ExecutionAuthorization,
    ImmutableAuditLog,
    KnowledgeLayer,
    KnowledgeLayerBinding,
    KnowledgeLayerRule,
    MeasurementDefinition,
    ModelPolicy,
    Organization,
    Objective,
    Opportunity,
    Process,
    QmsScope,
    QmsScopeProcess,
    Recommendation,
    RecommendationBasis,
    Risk,
    Stakeholder,
    StakeholderRequirement,
    Standard,
    StandardEdition,
    Clause,
    RequirementControl,
    TenantProjection,
    TransactionalOutbox,
    UserProjection,
)
from foundation.action_authorization import (
    EVENT_CONTRACTS as PHASE13_EVENT_CONTRACTS,
    ActionPreparationService,
    ExecutionAuthorizationService,
    ExecutionAuthorizerContext,
    IdempotencyConflict,
    _preconditions,
    action_plan_canonical_state,
)
from foundation.action_execution import (
    EVENT_CONTRACTS as PHASE14_EVENT_CONTRACTS,
    EXECUTOR_ALLOWLIST,
    ActionExecutionService,
    ExecutionPrincipalContext,
    ExecutorInvocation,
    ExecutorRegistry,
    SyntheticNoOpExecutor,
    SyntheticPreconditionEvaluator,
)
from foundation.agent_runtime import (
    EVENT_CONTRACTS as PHASE11_EVENT_CONTRACTS,
    AgentCatalogCommandService,
    AgentRunCommandService,
)
from foundation.human_decision import (
    EVENT_CONTRACTS as PHASE12_EVENT_CONTRACTS,
    AgentDecisionCommandService,
    AuthorizedHumanContext,
    HumanDecisionGateService,
    _human_gate_required,
)
from foundation.qms_context import EVENT_CONTRACTS, QmsContextCommandService
from foundation.risk_objective import (
    EVENT_CONTRACTS as PHASE5_EVENT_CONTRACTS,
    RiskOpportunityObjectiveCommandService,
)
from foundation.change_performance import (
    EVENT_CONTRACTS as PHASE6_EVENT_CONTRACTS,
    ChangePerformanceCommandService,
)
from foundation.document_evidence import (
    EVENT_CONTRACTS as PHASE7_EVENT_CONTRACTS,
    DocumentEvidenceCommandService,
    sha256_exact_bytes,
)
from foundation.normative_coverage import (
    EVENT_CONTRACTS as PHASE8_EVENT_CONTRACTS,
    EvidenceCoverageCommandService,
    NormativeCatalogCommandService,
)
from foundation.knowledge_layer import (
    KnowledgeCatalogQueryService,
    KnowledgeLayerCommandService,
)
from foundation.recommendation import (
    EVENT_CONTRACTS as PHASE10_EVENT_CONTRACTS,
    RecommendationCommandService,
    RecommendationSemanticContract,
    _assumptions,
    _confidence,
)
from foundation.projection_contract import (
    ContractValidationError,
    ProjectionEvent,
    validate_projection_event,
)
from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context
from foundation.effectiveness import (
    POLICY_ID as EFFECTIVENESS_POLICY_ID,
    EffectivenessCheckCommandService,
    ExactEvidenceReference,
    GovernedEffectivenessPlan,
    EffectivenessReviewCategory,
    EffectivenessReviewQueueService,
    TrustedEffectivenessAuthority,
)


class FoundationBoundaryTests(SimpleTestCase):
    def test_permanent_context_api_has_no_request_tenant_input(self):
        parameters = set(inspect.signature(trusted_tenant_context).parameters)
        self.assertTrue({"tenant_id", "body", "query", "header"}.isdisjoint(parameters))

    def test_synthetic_resolver_is_not_part_of_permanent_runtime(self):
        import foundation.tenant_context as tenant_context

        self.assertFalse(hasattr(tenant_context, "SyntheticTrustedTenantResolver"))
        self.assertFalse(hasattr(tenant_context, "set_tenant_context"))

    def test_status_values_match_approved_foundation_model(self):
        self.assertEqual(
            set(TenantProjection.LifecycleStatus.values),
            {"pending", "active", "suspended", "deprovisioning", "deleted_tombstone", "drifted", "unknown"},
        )
        self.assertEqual(
            set(TenantProjection.ReconciliationStatus.values),
            {"in_sync", "stale", "missing_local", "unexpected_local", "version_conflict", "authority_unavailable"},
        )


class ProjectionContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        fixture_path = Path(__file__).with_name("fixtures") / "adminapps_projection_events.json"
        cls.fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))

    def test_valid_tenant_and_user_contract_fixtures(self):
        for fixture in ("tenant_valid", "tenant_version_advancement", "user_valid", "user_version_advancement"):
            self.assertIsInstance(validate_projection_event(self.fixtures[fixture]), ProjectionEvent)

    def test_duplicate_fixture_explicitly_references_material_event(self):
        self.assertEqual(self.fixtures["tenant_duplicate_replay"], {"fixture_ref": "tenant_valid"})

    def test_malformed_payload_wrong_schema_and_unknown_type_are_422_equivalent(self):
        for fixture in ("malformed_payload", "wrong_schema_version", "unknown_event_type"):
            with self.subTest(fixture=fixture), self.assertRaises(ContractValidationError) as caught:
                validate_projection_event(self.fixtures[fixture])
            self.assertEqual(caught.exception.status_equivalent, 422)

    def test_identity_source_and_version_fields_are_mandatory(self):
        for field in ("event_id", "source", "schema_version", "source_version"):
            malformed = dict(self.fixtures["tenant_valid"])
            malformed.pop(field)
            with self.subTest(field=field), self.assertRaises(ContractValidationError):
                validate_projection_event(malformed)

    def test_wrong_source_and_aggregate_mismatch_fail_closed(self):
        wrong_source = dict(self.fixtures["tenant_valid"], source="browser")
        wrong_aggregate = dict(self.fixtures["tenant_valid"], aggregate_type="user")
        with self.assertRaises(ContractValidationError):
            validate_projection_event(wrong_source)
        with self.assertRaises(ContractValidationError):
            validate_projection_event(wrong_aggregate)

    def test_transport_free_adapter_validates_before_writer(self):
        calls = []

        class RecordingWriter:
            def apply(self, event):
                calls.append(event)
                return "written"

        adapter = ContractOnlyAdminAppsAdapter(writer=RecordingWriter())
        self.assertEqual(adapter.receive(self.fixtures["tenant_valid"]), "written")
        self.assertIsInstance(calls[0], ProjectionEvent)
        with self.assertRaises(ContractValidationError):
            adapter.receive(self.fixtures["malformed_payload"])
        self.assertEqual(len(calls), 1)

    def test_projection_models_contain_no_authentication_authority(self):
        user_fields = {field.name for field in UserProjection._meta.get_fields()}
        forbidden = {
            "password", "password_hash", "mfa_secret", "token", "access_token",
            "refresh_token", "global_role", "entitlement", "billing_status",
        }
        self.assertTrue(user_fields.isdisjoint(forbidden))
        self.assertNotEqual(UserProjection, __import__("django.contrib.auth").contrib.auth.get_user_model())

    def test_organization_is_distinct_from_tenant_projection_and_has_internal_id(self):
        self.assertIsNot(Organization, TenantProjection)
        self.assertEqual(Organization._meta.pk.name, "id")
        self.assertNotIn("adminapps_tenant_id", {field.name for field in Organization._meta.get_fields()})

    def test_future_boundary_failure_semantics_are_explicit(self):
        self.assertEqual(
            {status.name: status.value for status in BoundaryStatus},
            {
                "AUTHENTICATION_INVALID": 401,
                "AUTHORIZATION_DENIED": 403,
                "PROJECTION_CONFLICT": 409,
                "CONTRACT_INVALID": 422,
                "AUTHORITY_UNAVAILABLE": 503,
            },
        )


class Phase3ContractTests(SimpleTestCase):
    def test_payload_hash_is_stable_across_mapping_order(self):
        left = {"z": [3, 2, 1], "nested": {"b": True, "a": None}, "text": "á"}
        right = {"text": "á", "nested": {"a": None, "b": True}, "z": [3, 2, 1]}
        self.assertEqual(canonical_hash(left), canonical_hash(right))
        self.assertIn(CANONICAL_JSON_VERSION, canonical_json(left))

    def test_payload_substitution_has_a_distinct_hash_and_conflict_semantics(self):
        self.assertNotEqual(canonical_hash({"value": 1}), canonical_hash({"value": 2}))
        self.assertEqual(PayloadIntegrityConflict.status_equivalent, 409)

    def test_phase3_models_are_tenant_scoped_and_history_models_are_separate(self):
        for model in (DomainEvent, TransactionalOutbox, ConsumerReceipt, ImmutableAuditLog):
            self.assertIn("tenant", {field.name for field in model._meta.get_fields()})
        self.assertNotEqual(DomainEvent, TransactionalOutbox)
        self.assertNotIn("payload", {field.name for field in TransactionalOutbox._meta.get_fields()})

    def test_organization_command_exposes_one_atomic_business_boundary(self):
        parameters = set(inspect.signature(OrganizationEventingService.rename).parameters)
        self.assertTrue({"identity", "organization_id", "display_name", "trace_id"} <= parameters)
        self.assertFalse(hasattr(OrganizationEventingService, "create_event"))
        self.assertFalse(hasattr(OrganizationEventingService, "create_outbox"))

    def test_no_generic_event_injection_view_exists_in_foundation(self):
        foundation = Path(__file__).parent
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in foundation.glob("*.py")
            if path.name != "tests.py"
        )
        self.assertNotIn("POST /v1/events", source)
        self.assertNotIn("class DomainEventView", source)


class Phase4QmsContextContractTests(SimpleTestCase):
    def test_harmonized_objects_are_single_business_models(self):
        self.assertEqual(
            {Stakeholder, StakeholderRequirement, Process, ContextItem, QmsScope, QmsScopeProcess},
            {Stakeholder, StakeholderRequirement, Process, ContextItem, QmsScope, QmsScopeProcess},
        )
        source = Path(__file__).with_name("models.py").read_text(encoding="utf-8")
        for forbidden in ("ISO9001Stakeholder", "ISO14001Stakeholder", "ISO9001Process"):
            self.assertNotIn(forbidden, source)

    def test_every_phase4_object_is_directly_tenant_and_organization_scoped(self):
        for model in (Stakeholder, StakeholderRequirement, Process, ContextItem, QmsScope, QmsScopeProcess):
            fields = {field.name for field in model._meta.get_fields()}
            self.assertTrue({"tenant", "organization"} <= fields, model.__name__)

    def test_material_history_models_expose_explicit_lineage(self):
        for model in (StakeholderRequirement, ContextItem, QmsScope):
            fields = {field.name for field in model._meta.get_fields()}
            self.assertTrue({"lineage_id", "revision", "previous_revision"} <= fields, model.__name__)

    def test_event_catalog_is_typed_and_schema_versioned(self):
        self.assertEqual(set(EVENT_CONTRACTS), {
            "stakeholder.created", "stakeholder.updated",
            "stakeholder_requirement.created", "stakeholder_requirement.superseded",
            "process.created", "process.updated", "context_item.created",
            "context_item.superseded", "qms_scope.created", "qms_scope.revised",
        })
        self.assertEqual(set(EVENT_CONTRACTS.values()), {1})

    def test_commands_do_not_expose_event_or_audit_injection(self):
        required = {
            "create_stakeholder", "update_stakeholder", "create_stakeholder_requirement",
            "supersede_stakeholder_requirement", "create_process", "update_process",
            "create_context_item", "supersede_context_item", "create_scope", "revise_scope",
        }
        self.assertTrue(required <= set(dir(QmsContextCommandService)))
        self.assertFalse(hasattr(QmsContextCommandService, "create_event"))
        self.assertFalse(hasattr(QmsContextCommandService, "append_audit"))


class Phase5RiskOpportunityObjectiveContractTests(SimpleTestCase):
    def test_harmonized_business_objects_are_independent_models(self):
        self.assertEqual(len({Risk, Opportunity, Objective}), 3)
        source = Path(__file__).with_name("models.py").read_text(encoding="utf-8")
        for forbidden in ("ISO9001Risk", "ISO14001Risk", "ISO45001Risk", "ISO9001Objective"):
            self.assertNotIn(forbidden, source)
        self.assertNotIn("risk_type", {field.name for field in Opportunity._meta.get_fields()})

    def test_source_backed_fields_are_explicit_without_premature_subsystems(self):
        risk = {field.name for field in Risk._meta.get_fields()}
        opportunity = {field.name for field in Opportunity._meta.get_fields()}
        objective = {field.name for field in Objective._meta.get_fields()}
        self.assertTrue({"process", "cause", "event", "consequence", "likelihood", "impact", "residual"} <= risk)
        self.assertTrue({"process", "hypothesis", "benefit", "feasibility", "status"} <= opportunity)
        self.assertTrue({"owner", "metric", "target", "due_date", "status"} <= objective)
        self.assertNotIn("evidence", objective)

    def test_every_phase5_object_has_tenant_organization_and_linear_history(self):
        for model in (Risk, Opportunity, Objective):
            fields = {field.name for field in model._meta.get_fields()}
            self.assertTrue({"tenant", "organization", "lineage_id", "revision", "previous_revision"} <= fields)

    def test_phase5_events_are_typed_and_schema_versioned(self):
        self.assertEqual(set(PHASE5_EVENT_CONTRACTS), {
            "risk.created", "risk.revised", "opportunity.created", "opportunity.revised",
            "opportunity.status_changed", "objective.created", "objective.revised",
            "objective.status_changed",
        })
        self.assertEqual(set(PHASE5_EVENT_CONTRACTS.values()), {1})

    def test_material_commands_are_explicit_without_injection_paths(self):
        required = {
            "create_risk", "revise_risk", "create_opportunity", "revise_opportunity",
            "change_opportunity_status", "create_objective", "revise_objective",
            "change_objective_status",
        }
        self.assertTrue(required <= set(dir(RiskOpportunityObjectiveCommandService)))
        self.assertFalse(hasattr(RiskOpportunityObjectiveCommandService, "create_event"))
        self.assertFalse(hasattr(RiskOpportunityObjectiveCommandService, "append_audit"))


class Phase6ChangePerformanceContractTests(SimpleTestCase):
    def test_change_is_a_permanent_business_object_with_linear_history(self):
        fields = {field.name for field in Change._meta.get_fields()}
        self.assertTrue({
            "tenant", "organization", "lineage_id", "revision", "previous_revision",
            "change_type", "purpose", "impact", "status", "approval_id",
        } <= fields)
        self.assertNotIn("budget", fields)
        self.assertNotIn("risk_score", fields)

    def test_only_source_backed_change_process_relation_is_materialized(self):
        fields = {field.name for field in ChangeProcess._meta.get_fields()}
        self.assertTrue({"tenant", "organization", "change_revision", "process"} <= fields)
        change_fields = {field.name for field in Change._meta.get_fields()}
        self.assertTrue({"risk", "opportunity", "objective"}.isdisjoint(change_fields))

    def test_measurement_gate_is_definition_only_without_kpi_or_records(self):
        fields = {field.name for field in MeasurementDefinition._meta.get_fields()}
        self.assertTrue({
            "tenant", "organization", "lineage_id", "revision", "previous_revision",
            "process", "what_is_measured", "method", "measurement_timing",
        } <= fields)
        source = Path(__file__).with_name("models.py").read_text(encoding="utf-8")
        self.assertNotIn("class KPI", source)
        self.assertNotIn("class MeasurementRecord", source)

    def test_objective_metric_id_resolves_to_measurement_definition(self):
        metric = Objective._meta.get_field("metric")
        self.assertIs(metric.remote_field.model, MeasurementDefinition)
        self.assertEqual(metric.db_column, "metric_id")

    def test_phase6_commands_and_events_are_explicit(self):
        self.assertEqual(set(PHASE6_EVENT_CONTRACTS), {
            "change.created", "change.revised", "change.status_changed",
            "measurement_definition.created", "measurement_definition.revised",
        })
        self.assertEqual(set(PHASE6_EVENT_CONTRACTS.values()), {1})
        required = {
            "create_change", "revise_change", "change_change_status",
            "define_measurement", "revise_measurement_definition",
        }
        self.assertTrue(required <= set(dir(ChangePerformanceCommandService)))
        self.assertFalse(hasattr(ChangePerformanceCommandService, "record_measurement"))
        self.assertFalse(hasattr(ChangePerformanceCommandService, "create_event"))


class Phase7DocumentEvidenceContractTests(SimpleTestCase):
    def test_document_is_logical_identity_and_version_is_separate(self):
        document_fields = {field.name for field in Document._meta.get_fields()}
        version_fields = {field.name for field in DocumentVersion._meta.get_fields()}
        self.assertTrue({"tenant", "organization", "document_type", "owner", "current_version"} <= document_fields)
        self.assertTrue({
            "tenant", "organization", "document", "version", "predecessor",
            "content_reference", "content_hash", "approved_by", "effective_at",
        } <= version_fields)
        self.assertNotIn("content_hash", document_fields)

    def test_exact_binary_hash_has_no_text_or_json_canonicalization(self):
        self.assertEqual(
            sha256_exact_bytes(b"phase-7\x00fixture\n"),
            "4dd79e1d2237f1fc3cadc396222e314b11432133e18dacab319d737988e372e9",
        )
        with self.assertRaises(TypeError):
            sha256_exact_bytes("phase-7 fixture")

    def test_evidence_is_canonical_append_only_revision_model(self):
        fields = {field.name for field in Evidence._meta.get_fields()}
        self.assertTrue({
            "tenant", "organization", "lineage_id", "revision", "previous_revision",
            "source_type", "source_uri", "content_hash", "captured_at", "trust_score",
            "document_version",
        } <= fields)
        source = Path(__file__).with_name("models.py").read_text(encoding="utf-8")
        self.assertNotIn("ISO9001Evidence", source)

    def test_only_exact_document_version_provenance_relation_is_present(self):
        relation = Evidence._meta.get_field("document_version")
        self.assertIs(relation.remote_field.model, DocumentVersion)
        evidence_fields = {field.name for field in Evidence._meta.get_fields()}
        self.assertTrue({"process", "risk", "opportunity", "objective", "change", "requirement"}.isdisjoint(evidence_fields))

    def test_phase7_commands_and_events_are_explicit(self):
        self.assertEqual(set(PHASE7_EVENT_CONTRACTS), {
            "document.created", "document.metadata_revised", "document.version_created",
            "evidence.created", "evidence.superseded",
        })
        self.assertEqual(set(PHASE7_EVENT_CONTRACTS.values()), {1})
        self.assertTrue({
            "create_document", "revise_document_metadata", "create_document_version",
            "create_evidence", "supersede_evidence",
        } <= set(dir(DocumentEvidenceCommandService)))
        self.assertFalse(hasattr(DocumentEvidenceCommandService, "update_document_version"))
        self.assertFalse(hasattr(DocumentEvidenceCommandService, "create_event"))


class Phase8NormativeCoverageContractTests(SimpleTestCase):
    def test_normative_catalog_is_global_and_edition_safe(self):
        for model in (Standard, StandardEdition, Clause, RequirementControl):
            self.assertNotIn("tenant", {field.name for field in model._meta.get_fields()})
        self.assertIs(StandardEdition._meta.get_field("standard").remote_field.model, Standard)
        self.assertIs(Clause._meta.get_field("standard_edition").remote_field.model, StandardEdition)
        self.assertIs(RequirementControl._meta.get_field("standard_edition").remote_field.model, StandardEdition)
        self.assertIs(RequirementControl._meta.get_field("clause").remote_field.model, Clause)
        self.assertNotEqual(RequirementControl, StakeholderRequirement)

    def test_edition_states_are_source_bounded(self):
        self.assertEqual(set(StandardEdition.Status.values), {"draft", "published"})

    def test_coverage_freezes_exact_business_and_normative_revisions(self):
        fields = {field.name for field in EvidenceCoverage._meta.get_fields()}
        self.assertTrue({
            "tenant", "organization", "evidence", "standard_edition",
            "requirement_control", "confidence", "validation_status",
            "validated_by", "validated_at", "created_at",
        } <= fields)
        self.assertIs(EvidenceCoverage._meta.get_field("evidence").remote_field.model, Evidence)
        self.assertIs(
            EvidenceCoverage._meta.get_field("standard_edition").remote_field.model,
            StandardEdition,
        )
        self.assertIs(
            EvidenceCoverage._meta.get_field("requirement_control").remote_field.model,
            RequirementControl,
        )

    def test_phase8_commands_and_tenant_event_are_explicit(self):
        self.assertEqual(PHASE8_EVENT_CONTRACTS, {"evidence_coverage.recorded": 1})
        self.assertTrue({
            "create_standard", "create_standard_edition", "add_clause",
            "add_requirement_control", "publish_standard_edition",
        } <= set(dir(NormativeCatalogCommandService)))
        self.assertTrue(hasattr(EvidenceCoverageCommandService, "record_evidence_coverage"))
        self.assertFalse(hasattr(NormativeCatalogCommandService, "create_event"))
        self.assertFalse(hasattr(EvidenceCoverageCommandService, "create_event"))


class Phase9KnowledgeLayerContractTests(SimpleTestCase):
    def test_global_models_and_exact_relationships_are_explicit(self):
        for model in (KnowledgeLayer, KnowledgeLayerRule, KnowledgeLayerBinding):
            self.assertNotIn("tenant", {field.name for field in model._meta.get_fields()})
        self.assertIs(
            KnowledgeLayer._meta.get_field("standard_edition").remote_field.model,
            StandardEdition,
        )
        self.assertIs(
            KnowledgeLayerRule._meta.get_field("knowledge_layer").remote_field.model,
            KnowledgeLayer,
        )
        self.assertIs(
            KnowledgeLayerRule._meta.get_field("previous_revision").remote_field.model,
            KnowledgeLayerRule,
        )
        self.assertIs(
            KnowledgeLayerBinding._meta.get_field("knowledge_layer_rule").remote_field.model,
            KnowledgeLayerRule,
        )
        self.assertIs(
            KnowledgeLayerBinding._meta.get_field("requirement_control").remote_field.model,
            RequirementControl,
        )

    def test_certifiability_is_typed_not_an_ambiguous_boolean(self):
        self.assertEqual(
            set(RequirementControl.CertifiabilityClassification.values),
            {"normative_requirement"},
        )
        self.assertEqual(
            set(KnowledgeLayerRule.CertifiabilityClassification.values),
            {"non_certifiable_guidance"},
        )
        for model in (RequirementControl, KnowledgeLayer, KnowledgeLayerRule):
            self.assertNotIn("certifiable", {field.name for field in model._meta.get_fields()})

    def test_future_serialization_contract_never_presents_guidance_as_requirement(self):
        requirement = RequirementControl()
        layer = KnowledgeLayer()
        rule = KnowledgeLayerRule()
        requirement_contract = KnowledgeCatalogQueryService.classification_contract(requirement)
        layer_contract = KnowledgeCatalogQueryService.classification_contract(layer)
        rule_contract = KnowledgeCatalogQueryService.classification_contract(rule)
        self.assertTrue(requirement_contract["is_certifiable_customer_requirement"])
        self.assertEqual(requirement_contract["presentation_kind"], "Requirement")
        self.assertFalse(layer_contract["is_certifiable_customer_requirement"])
        self.assertFalse(rule_contract["is_certifiable_customer_requirement"])
        self.assertEqual(rule_contract["presentation_kind"], "Guidance")

    def test_rule_and_binding_states_and_semantics_are_source_bounded(self):
        self.assertEqual(set(KnowledgeLayerRule.Status.values), {"draft", "published"})
        self.assertEqual(set(KnowledgeLayerBinding.Status.values), {"draft", "published"})
        self.assertEqual(set(KnowledgeLayerBinding.RelationshipType.values), {"informs"})
        self.assertEqual(set(KnowledgeLayerBinding.SemanticEffect.values), {"guidance_only"})

    def test_material_workflows_are_explicit_and_out_of_scope_runtime_is_absent(self):
        self.assertTrue({
            "create_knowledge_layer", "create_knowledge_layer_rule",
            "revise_knowledge_layer_rule", "publish_knowledge_layer_rule",
            "create_knowledge_layer_binding", "publish_knowledge_layer_binding",
        } <= set(dir(KnowledgeLayerCommandService)))
        for forbidden in (
            "save", "create_recommendation", "create_agent_run", "infer",
            "traverse_graph", "create_domain_event",
        ):
            self.assertFalse(hasattr(KnowledgeLayerCommandService, forbidden))


class Phase10RecommendationContractTests(SimpleTestCase):
    def test_models_have_exact_tenant_organization_and_frozen_references(self):
        recommendation_fields = {field.name for field in Recommendation._meta.get_fields()}
        self.assertTrue({
            "id", "tenant", "organization", "title", "body", "confidence",
            "assumptions", "impact", "status", "intended_autonomy", "created_at",
        } <= recommendation_fields)
        basis_fields = {field.name for field in RecommendationBasis._meta.get_fields()}
        self.assertTrue({
            "tenant", "organization", "recommendation", "standard_edition",
            "requirement_control", "knowledge_layer_rule", "evidence", "rationale",
            "model_provider", "model_identifier", "model_version", "prompt_version",
            "rule_bundle_version", "dataset_version_reference", "embedding_namespace",
            "trace_id",
        } <= basis_fields)
        self.assertIs(
            RecommendationBasis._meta.get_field("requirement_control").remote_field.model,
            RequirementControl,
        )
        self.assertIs(
            RecommendationBasis._meta.get_field("knowledge_layer_rule").remote_field.model,
            KnowledgeLayerRule,
        )
        self.assertIs(
            RecommendationBasis._meta.get_field("evidence").remote_field.model,
            Evidence,
        )
        self.assertNotIn("evidence_coverage", basis_fields)

    def test_semantic_categories_are_not_interchangeable(self):
        self.assertEqual(
            RecommendationSemanticContract.classify(RequirementControl()),
            "certifiable_normative_requirement",
        )
        self.assertEqual(
            RecommendationSemanticContract.classify(KnowledgeLayerRule()),
            "non_certifiable_guidance",
        )
        self.assertEqual(
            RecommendationSemanticContract.classify(Evidence()),
            "observed_supporting_evidence",
        )
        self.assertEqual(
            RecommendationSemanticContract.classify(Recommendation()),
            "derived_advisory_proposal",
        )

    def test_confidence_and_assumptions_are_strongly_validated(self):
        self.assertEqual(str(_confidence("0.8750")), "0.8750")
        for invalid in (-0.1, 1.1, "not-a-number", None):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                _confidence(invalid)
        self.assertEqual(_assumptions([" A1 ", "A2"]), ["A1", "A2"])
        for invalid in ("hidden", [""], [None]):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                _assumptions(invalid)

    def test_only_source_backed_creation_event_and_explicit_command_exist(self):
        self.assertEqual(PHASE10_EVENT_CONTRACTS, {"recommendation.created": 1})
        self.assertEqual(set(Recommendation.Status.values), {"proposed"})
        self.assertTrue(hasattr(RecommendationCommandService, "create_recommendation"))
        for forbidden in (
            "execute", "execute_action", "approve", "create_agent_run",
            "create_agent_decision", "save", "infer",
        ):
            self.assertFalse(hasattr(RecommendationCommandService, forbidden))


class Phase11AgentRuntimeContractTests(SimpleTestCase):
    def test_catalogs_are_global_versioned_and_semantically_separate(self):
        for model in (AgentDefinition, ModelPolicy):
            fields = {field.name for field in model._meta.get_fields()}
            self.assertNotIn("tenant", fields)
            self.assertTrue({"lineage_id", "version", "previous_revision", "status"} <= fields)
        self.assertIsNot(AgentDefinition, ModelPolicy)
        self.assertIs(AgentDefinition._meta.get_field("model_policy").remote_field.model, ModelPolicy)
        self.assertEqual(set(AgentDefinition.Status.values), {"draft", "published"})
        self.assertEqual(set(ModelPolicy.Status.values), {"draft", "published"})

    def test_run_and_frozen_input_are_tenant_organization_safe(self):
        run_fields = {field.name for field in AgentRun._meta.get_fields()}
        self.assertTrue({
            "tenant", "organization", "agent_definition", "model_policy", "capability",
            "status", "requested_autonomy", "effective_autonomy_ceiling",
            "model_provider", "model_identifier", "model_version", "prompt_version",
            "rule_bundle_version", "dataset_version_reference", "embedding_namespace",
            "trace_id", "correlation_id", "causation_id", "started_at", "completed_at",
        } <= run_fields)
        input_fields = {field.name for field in AgentRunInput._meta.get_fields()}
        self.assertTrue({"tenant", "organization", "agent_run", "standard_edition",
                         "requirement_control", "knowledge_layer_rule", "evidence"} <= input_fields)
        self.assertNotIn("context_blob", input_fields)
        self.assertNotIn("evidence_coverage", input_fields)

    def test_recommendation_is_linked_without_aggregate_duplication(self):
        fields = {field.name for field in AgentRunRecommendation._meta.get_fields()}
        self.assertTrue({"tenant", "organization", "agent_run", "recommendation"} <= fields)
        run_fields = {field.name for field in AgentRun._meta.get_fields()}
        self.assertTrue({"title", "body", "confidence", "assumptions"}.isdisjoint(run_fields))
        self.assertIs(AgentRunRecommendation._meta.get_field("recommendation").remote_field.model,
                      Recommendation)

    def test_commands_events_and_no_execution_boundary_are_explicit(self):
        self.assertEqual(PHASE11_EVENT_CONTRACTS, {
            "agent_run.started": 1, "agent_run.completed": 1, "agent_run.failed": 1,
        })
        self.assertTrue({"create_model_policy", "revise_model_policy", "publish_model_policy",
                         "create_agent_definition", "revise_agent_definition",
                         "publish_agent_definition"} <= set(dir(AgentCatalogCommandService)))
        self.assertTrue({"start_agent_run", "complete_agent_run_with_recommendation",
                         "fail_agent_run"} <= set(dir(AgentRunCommandService)))
        for forbidden in ("infer", "execute", "execute_action", "approve", "create_agent_decision"):
            self.assertFalse(hasattr(AgentRunCommandService, forbidden))


class Phase12HumanDecisionGateContractTests(SimpleTestCase):
    def test_agent_decision_and_approval_are_distinct_source_backed_records(self):
        decision_fields = {field.name for field in AgentDecision._meta.get_fields()}
        self.assertTrue({
            "tenant", "organization", "agent_run", "recommendation", "decision_type",
            "payload", "confidence", "explainability", "decision_autonomy",
            "human_gate_required", "trace_id", "created_at",
        } <= decision_fields)
        approval_fields = {field.name for field in Approval._meta.get_fields()}
        self.assertTrue({
            "tenant", "organization", "agent_decision", "recommendation", "required_role",
            "decision", "decided_by", "adminapps_user_id_snapshot", "actor_type",
            "comments", "decided_at", "trace_id",
        } <= approval_fields)
        self.assertIsNot(AgentDecision, Approval)
        self.assertIsNot(Recommendation, Approval)
        self.assertEqual(set(Approval.Decision.values), {"approve", "reject", "request_changes"})

    def test_human_command_never_accepts_spoofable_authority_fields(self):
        for method_name in ("record_human_approval", "record_human_rejection", "request_human_changes"):
            parameters = set(inspect.signature(getattr(HumanDecisionGateService, method_name)).parameters)
            self.assertIn("authority", parameters)
            self.assertTrue({"tenant_id", "actor_id", "approver_role", "required_role"}.isdisjoint(parameters))

    def test_agent_or_system_principal_cannot_become_human_authority(self):
        identity = TrustedTenantIdentity("fixture", UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"))
        for principal_type in ("agent", "system"):
            with self.subTest(principal_type=principal_type), self.assertRaises(ValueError):
                AuthorizedHumanContext(
                    identity=identity,
                    user_projection_id=UUID("50000000-0000-4000-8000-000000000001"),
                    adminapps_user_id=UUID("50000000-0000-4000-8000-000000000001"),
                    authorized_roles=("quality_approver",), principal_type=principal_type,
                    authority_source="controlled_test_fixture",
                )

    def test_policy_gate_and_no_execution_commands_are_explicit(self):
        class Policy:
            human_gate_rules = {
                "required_autonomy_levels": ["A2", "A4"],
                "required_role": "quality_approver",
            }

        self.assertFalse(_human_gate_required(Policy(), 0))
        self.assertTrue(_human_gate_required(Policy(), 2))
        self.assertTrue(_human_gate_required(Policy(), 3))
        self.assertTrue(_human_gate_required(Policy(), 4))
        self.assertEqual(PHASE12_EVENT_CONTRACTS, {
            "agent_decision.recorded": 1, "approval.recorded": 1,
        })
        self.assertTrue(hasattr(AgentDecisionCommandService, "record_agent_decision"))
        for service in (AgentDecisionCommandService, HumanDecisionGateService):
            for forbidden in ("execute", "execute_action", "tool_call", "mutate_process"):
                self.assertFalse(hasattr(service, forbidden))


class Phase13ActionAuthorizationContractTests(SimpleTestCase):
    def test_models_are_distinct_exact_and_non_executing(self):
        plan = {field.name for field in ActionPlan._meta.get_fields()}
        self.assertTrue({
            "tenant", "organization", "agent_decision", "recommendation",
            "action_type", "target_type", "target_id", "parameters", "impact",
            "reversibility", "preconditions", "dry_run_supported",
            "required_autonomy", "action_plan_hash", "idempotency_key", "trace_id",
        } <= plan)
        dry_run = {field.name for field in ActionPlanDryRun._meta.get_fields()}
        self.assertTrue({"action_plan", "action_plan_hash", "precondition_results",
                         "intended_state_delta", "validation_status"} <= dry_run)
        authorization = {field.name for field in ExecutionAuthorization._meta.get_fields()}
        self.assertTrue({
            "action_plan", "action_plan_hash", "dry_run", "agent_decision",
            "recommendation", "effective_approval", "agent_run", "agent_definition",
            "model_policy", "effective_autonomy_ceiling", "impact", "reversibility",
            "outcome", "idempotency_key", "authorization_request_hash", "actor_type",
        } <= authorization)
        self.assertEqual(set(ExecutionAuthorization.Outcome.values), {"authorized"})
        self.assertIsNot(ActionPlan, ExecutionAuthorization)

    def test_canonical_hash_covers_material_fields_not_volatile_fields(self):
        common = dict(
            organization_id=UUID("aaaaaaaa-1000-4000-8000-000000000001"),
            agent_decision_id=UUID("aaaaaaaa-2000-4000-8000-000000000001"),
            recommendation_id=UUID("aaaaaaaa-3000-4000-8000-000000000001"),
            action_type="prepare_change", target_type="change", target_id="logical-1",
            parameters={"status": "proposed"}, impact="high",
            reversibility="irreversible", preconditions=[{
                "identity": "revision", "type": "exact_value", "expected": 7,
                "required": True, "source_reference": "change:logical-1",
            }], dry_run_supported=True, required_autonomy=3,
        )
        left = canonical_hash(action_plan_canonical_state(**common))
        reordered = dict(common, parameters={"status": "proposed"})
        self.assertEqual(left, canonical_hash(action_plan_canonical_state(**reordered)))
        self.assertNotEqual(left, canonical_hash(action_plan_canonical_state(
            **dict(common, parameters={"status": "approved"}))))

    def test_preconditions_are_structured_and_fail_closed_capable(self):
        valid = _preconditions([{"identity": "r1", "type": "exact_value",
                                "expected": 1, "required": True}])
        self.assertEqual(valid[0]["identity"], "r1")
        for invalid in ("free text", [{}], [{"identity": "x", "type": "t"}],
                        [{"identity": "x", "type": "t", "expected": 1,
                          "required": "yes"}]):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                _preconditions(invalid)

    def test_commands_events_authority_and_idempotency_are_explicit(self):
        self.assertEqual(set(PHASE13_EVENT_CONTRACTS), {
            "action_plan.prepared", "action_plan.dry_run_completed",
            "execution_authorization.granted", "execution_authorization.denied",
        })
        self.assertTrue(hasattr(ActionPreparationService, "prepare_action_plan"))
        self.assertTrue(hasattr(ActionPreparationService, "run_action_plan_dry_run"))
        self.assertTrue(hasattr(ExecutionAuthorizationService,
                                "evaluate_execution_authorization"))
        parameters = set(inspect.signature(
            ExecutionAuthorizationService.evaluate_execution_authorization).parameters)
        self.assertTrue({"authority", "action_plan_id", "dry_run_id",
                         "idempotency_key"} <= parameters)
        self.assertTrue({"tenant_id", "approver", "role", "autonomy"}.isdisjoint(parameters))
        self.assertEqual(IdempotencyConflict.status_equivalent, 409)
        identity = TrustedTenantIdentity("fixture", UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"))
        with self.assertRaises(ValueError):
            ExecutionAuthorizerContext(identity=identity, principal_type="worker")

    def test_no_execution_or_business_mutation_surface_exists(self):
        for service in (ActionPreparationService, ExecutionAuthorizationService):
            for forbidden in ("execute", "execute_action", "call_tool", "mutate_process",
                              "mutate_risk", "mutate_objective", "mutate_change"):
                self.assertFalse(hasattr(service, forbidden))


class Phase14SyntheticActionExecutionContractTests(SimpleTestCase):
    def test_execution_attempt_and_receipt_are_exact_distinct_records(self):
        execution = {field.name for field in ActionExecution._meta.get_fields()}
        self.assertTrue({
            "tenant", "organization", "execution_authorization", "action_plan",
            "action_plan_hash", "executor_type", "status", "attempt_number",
            "retry_of", "precondition_results", "idempotency_key", "trace_id",
            "started_at", "completed_at",
        } <= execution)
        receipt = {field.name for field in ActionExecutionReceipt._meta.get_fields()}
        self.assertTrue({
            "tenant", "organization", "action_execution", "executor_type", "outcome",
            "result", "result_hash", "action_plan_hash", "trace_id", "started_at",
            "completed_at",
        } <= receipt)
        self.assertEqual(set(ActionExecution.Status.values), {"running", "succeeded", "failed"})
        self.assertEqual(
            set(ActionExecution.ExecutorType.values),
            {"synthetic_noop", "controlled_opportunity"},
        )

    def test_executor_registry_is_closed_and_noop_result_is_deterministic(self):
        self.assertEqual(set(EXECUTOR_ALLOWLIST), {"synthetic_noop"})
        registry = ExecutorRegistry.synthetic_only()
        invocation = ExecutorInvocation(
            execution_id=UUID("aaaaaaaa-0000-4000-8000-000000000001"),
            action_plan_id=UUID("aaaaaaaa-0000-4000-8000-000000000002"),
            action_plan_hash="a" * 64, action_type="synthetic", target_type="none",
            target_id="none",
        )
        left = registry.resolve("synthetic_noop").execute(invocation)
        right = SyntheticNoOpExecutor().execute(invocation)
        self.assertEqual(left, right)
        self.assertEqual(left.result["classification"], "NON-PRODUCTION")
        self.assertEqual(left.result["effect"], "NO-OP")
        self.assertFalse(left.result["business_state_changed"])
        for forbidden in ("http", "shell", "database", "tool", "unknown"):
            with self.subTest(forbidden=forbidden), self.assertRaises(Exception):
                registry.resolve(forbidden)

    def test_execution_command_accepts_only_trusted_resolved_authority(self):
        parameters = set(inspect.signature(
            ActionExecutionService.execute_authorized_action).parameters)
        self.assertTrue({"principal", "authorization_id", "idempotency_key", "trace_id"} <= parameters)
        self.assertTrue({"tenant_id", "executor", "autonomy", "approved", "role",
                         "action_payload"}.isdisjoint(parameters))
        identity = TrustedTenantIdentity("fixture", UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"))
        evaluator = SyntheticPreconditionEvaluator({})
        with self.assertRaises(ValueError):
            ExecutionPrincipalContext(identity, evaluator, executor_type="http")

    def test_events_and_no_external_effect_surface_are_explicit(self):
        self.assertEqual(PHASE14_EVENT_CONTRACTS, {
            "action_execution.started": 1,
            "action_execution.succeeded": 1,
            "action_execution.failed": 1,
        })
        source = Path(__file__).with_name("action_execution.py").read_text(encoding="utf-8")
        for forbidden in ("import requests", "import httpx", "import subprocess",
                          "import socket", "os.system", "Popen(", "run("):
            self.assertNotIn(forbidden, source)
        for forbidden in ("mutate_process", "mutate_risk", "mutate_objective",
                          "mutate_change", "effectiveness_check", "rollback_action"):
            self.assertFalse(hasattr(ActionExecutionService, forbidden))


class Phase19EffectivenessCheckContractTests(SimpleTestCase):
    def test_models_preserve_exact_provenance_and_evidence_revision_snapshots(self):
        check_fields = {field.name for field in EffectivenessCheck._meta.get_fields()}
        self.assertTrue({
            "tenant", "organization", "action_execution", "receipt", "action_plan",
            "execution_authorization", "agent_decision", "recommendation",
            "opportunity_lineage_id", "before_opportunity_revision",
            "resulting_opportunity_revision", "outcome", "actor_user_projection",
            "actor_external_id_snapshot", "due_at", "measurement_definition",
            "predecessor", "revision", "trace_id",
        } <= check_fields)
        link_fields = {field.name for field in EffectivenessEvidence._meta.get_fields()}
        self.assertTrue({
            "effectiveness_check", "evidence", "evidence_lineage_id_snapshot",
            "evidence_revision_snapshot", "evidence_content_hash_snapshot", "criterion_role",
        } <= link_fields)

    def test_outcome_taxonomy_does_not_collapse_uncertainty(self):
        self.assertEqual(set(EffectivenessCheck.Outcome.values), {
            "effective", "ineffective", "inconclusive", "unknown",
        })
        self.assertNotEqual(EffectivenessCheck.Outcome.INCONCLUSIVE, EffectivenessCheck.Outcome.UNKNOWN)

    def test_command_has_trusted_authority_and_no_client_authority_inputs(self):
        parameters = set(inspect.signature(
            EffectivenessCheckCommandService.record_effectiveness_check).parameters)
        self.assertTrue({"authority", "plan", "outcome", "evidence", "trace_id"} <= parameters)
        self.assertTrue({
            "tenant_id", "organization_id", "actor_id", "role", "permissions",
            "mfa", "headers", "body", "query",
        }.isdisjoint(parameters))

    def test_authority_is_human_adminapps_resolved_and_correction_is_independent(self):
        tenant = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        organization = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
        authority = TrustedEffectivenessAuthority(
            identity=TrustedTenantIdentity("reviewer", tenant),
            organization_id=organization,
            actor_user_projection_id=UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
            actor_external_id=UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd"),
            permissions=frozenset({"qms.effectiveness_check.record"}),
            mfa_verified=True, access_active=True, authority_context_version="adminapps/v1",
            authority_decision_reference="decision-1",
        )
        EffectivenessCheckCommandService._validate_authority(authority, correction=False)
        with self.assertRaises(PermissionError):
            EffectivenessCheckCommandService._validate_authority(authority, correction=True)
        with self.assertRaises(TypeError):
            EffectivenessCheckCommandService._validate_authority(object(), correction=False)

    def test_measurement_definition_is_exactly_conditional(self):
        common = dict(
            action_execution_id=UUID("aaaaaaaa-0000-4000-8000-000000000001"),
            organization_id=UUID("aaaaaaaa-0000-4000-8000-000000000002"),
            opportunity_lineage_id=UUID("aaaaaaaa-0000-4000-8000-000000000003"),
            due_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            criteria_hash="a" * 64, planning_context_hash="b" * 64,
        )
        pure = GovernedEffectivenessPlan(**common, assessment_method="human_review")
        EffectivenessCheckCommandService._validate_plan(pure)
        measured = GovernedEffectivenessPlan(
            **common, assessment_method="measurement_derived",
            measurement_definition_id=UUID("aaaaaaaa-0000-4000-8000-000000000004"),
        )
        EffectivenessCheckCommandService._validate_plan(measured)
        with self.assertRaises(ValueError):
            EffectivenessCheckCommandService._validate_plan(
                GovernedEffectivenessPlan(**common, assessment_method="measurement_derived")
            )

    def test_evidence_is_finite_nonempty_exact_and_duplicate_free(self):
        reference = ExactEvidenceReference(
            evidence_id=UUID("aaaaaaaa-0000-4000-8000-000000000001"),
            lineage_id=UUID("aaaaaaaa-0000-4000-8000-000000000002"),
            revision=1, content_hash="a" * 64, criterion_role="interval activity log",
        )
        self.assertEqual(EffectivenessCheckCommandService._validate_evidence([reference]), (reference,))
        with self.assertRaises(ValueError):
            EffectivenessCheckCommandService._validate_evidence([])
        with self.assertRaises(ValueError):
            EffectivenessCheckCommandService._validate_evidence([reference, reference])

    def test_policy_event_and_no_effect_driven_execution_surface_are_closed(self):
        self.assertEqual(EFFECTIVENESS_POLICY_ID, "effectiveness-check-policy/v1")
        source = Path(__file__).with_name("effectiveness.py").read_text(encoding="utf-8")
        self.assertIn('event_type="effectiveness_check.recorded"', source)
        for forbidden in (
            "resume_evaluation(", "defer_evaluation(", "ActionPreparationService(",
            "ModelPolicy.objects", "KnowledgeLayerRule.objects", "Recommendation.objects",
            "import requests", "import httpx", "import subprocess", "os.system", "Popen(",
        ):
            self.assertNotIn(forbidden, source)


class Phase20EffectivenessOperationalBoundaryTests(SimpleTestCase):
    def test_review_queue_categories_are_closed_and_queue_is_not_authority(self):
        self.assertEqual({item.value for item in EffectivenessReviewCategory}, {
            "due", "overdue", "unknown", "inconclusive",
        })
        parameters = set(inspect.signature(
            EffectivenessReviewQueueService.requiring_attention).parameters)
        self.assertEqual(parameters, {
            "self", "identity", "organization_id", "plans", "as_of",
        })
        self.assertNotIn("permissions", parameters)

    def test_phase21_governed_learning_runtime_is_narrow_and_additive(self):
        model_names = {model.__name__ for model in apps.get_models()}
        self.assertTrue({
            "LearningSignal", "LearningSignalEffectiveness",
            "LearningProposal", "LearningProposalSignal",
        }.issubset(model_names))
        migration_names = {path.name for path in
                           Path(__file__).with_name("migrations").glob("*.py")}
        self.assertEqual(len([name for name in migration_names if name.startswith("0018")]), 1)

    def test_no_automatic_learning_or_second_action_surface(self):
        source = Path(__file__).with_name("effectiveness.py").read_text(encoding="utf-8")
        for forbidden in (
            "LearningSignal.objects", "LearningProposal.objects", "ModelPolicy.objects",
            "AgentDefinition.objects", "KnowledgeLayerRule.objects", "confidence =",
            "autonomy_max =", "resume_evaluation(", "defer_evaluation(",
        ):
            self.assertNotIn(forbidden, source)
        controlled = Path(__file__).with_name("controlled_opportunity.py").read_text(encoding="utf-8")
        self.assertEqual(controlled.count('FORWARD_ACTION = "opportunity.defer_evaluation"'), 1)
        self.assertEqual(controlled.count('COMPENSATION_ACTION = "opportunity.resume_evaluation"'), 1)


class Phase21BlockingHardeningTests(SimpleTestCase):
    def test_proposal_has_only_governance_pending_semantics(self):
        self.assertEqual(LearningProposal.Status.values, ["governance_pending"])
        source = Path(__file__).with_name("governed_learning.py").read_text(encoding="utf-8")
        for forbidden in (
            "approved_for_application", "learning_proposal.approved",
            "learning_proposal.applied", "model.updated", "policy.updated",
            "autonomy.changed", "status=\"applied\"", "status=\"executed\"",
        ):
            self.assertNotIn(forbidden, source)

    def test_categorical_outcomes_have_no_numeric_mapping_or_aggregation(self):
        source = Path(__file__).with_name("governed_learning.py").read_text(encoding="utf-8")
        for forbidden in (
            "outcome_score", "outcome_weight", "weighted_average", "average_outcome",
            '"effective": 1', '"ineffective": -1', "Sum(", "Avg(",
        ):
            self.assertNotIn(forbidden, source)
        self.assertFalse(any(
            field.name in {"score", "weight", "numeric_value"}
            for model in (LearningSignal, LearningSignalEffectiveness)
            for field in model._meta.fields
        ))

    def test_signal_and_proposal_freeze_required_provenance(self):
        signal_fields = {field.name for field in LearningSignal._meta.fields}
        self.assertTrue({
            "selected_effectiveness_check", "effectiveness_lineage_id",
            "selected_revision", "selected_predecessor_id_snapshot",
            "selected_was_current_leaf", "derivation_timestamp",
            "derivation_policy_id", "derivation_policy_version", "provenance_hash",
        }.issubset(signal_fields))
        proposal_fields = {field.name for field in LearningProposal._meta.fields}
        self.assertTrue({
            "target_id", "target_lineage_id", "target_version",
            "target_snapshot", "target_hash", "status",
        }.issubset(proposal_fields))

    def test_learning_commands_have_no_target_or_runtime_mutation_surface(self):
        source = Path(__file__).with_name("governed_learning.py").read_text(encoding="utf-8")
        for forbidden in (
            "ModelPolicy.objects", "AgentDefinition.objects", "KnowledgeLayerRule.objects",
            "Recommendation.objects", "ActionExecution.objects", "Opportunity.objects",
            ".update(", ".delete(", "bulk_update(", "resume_evaluation(",
            "defer_evaluation(", "import requests", "import httpx", "Popen(",
        ):
            self.assertNotIn(forbidden, source)

    def test_authority_api_does_not_accept_request_claims(self):
        from foundation.governed_learning import (
            LearningProposalCommandService, LearningSignalCommandService,
            TrustedLearningGovernanceAuthority,
        )
        authority_fields = set(TrustedLearningGovernanceAuthority.__dataclass_fields__)
        self.assertTrue({"identity", "permissions", "mfa_verified", "access_active"}.issubset(authority_fields))
        self.assertTrue({"headers", "body", "query", "role"}.isdisjoint(authority_fields))
        for method in (
            LearningSignalCommandService.create_signal,
            LearningProposalCommandService.create_proposal,
        ):
            self.assertTrue({"headers", "body", "query", "role"}.isdisjoint(
                inspect.signature(method).parameters
            ))


class Phase23LearningProposalGovernanceTests(SimpleTestCase):
    def test_phase23_models_are_inert_exact_and_immutable_by_contract(self):
        self.assertEqual(set(LearningProposalDecision.Outcome.values), {
            "approved_for_application", "rejected", "changes_requested",
        })
        self.assertEqual(LearningApplicationAuthorization.Status.values, ["authorized"])
        self.assertEqual(set(LearningProposalReview.TargetStatus.values), {"valid", "stale"})
        review_fields = {field.name for field in LearningProposalReview._meta.fields}
        decision_fields = {field.name for field in LearningProposalDecision._meta.fields}
        authorization_fields = {field.name for field in LearningApplicationAuthorization._meta.fields}
        exact = {
            "proposal_revision_snapshot", "proposal_material_hash", "target_type",
            "target_id", "target_lineage_id", "target_version", "target_hash",
        }
        self.assertTrue(exact.issubset(review_fields))
        self.assertTrue(exact.issubset(decision_fields))
        self.assertTrue(exact.issubset(authorization_fields))
        self.assertTrue({"capability_id", "idempotency_key", "idempotency_hash"}.issubset(
            authorization_fields
        ))

    def test_authorities_and_commands_accept_no_client_authority_claims(self):
        from foundation.learning_proposal_governance import (
            LearningApplicationAuthorizationCommandService,
            LearningProposalDecisionCommandService,
            LearningProposalReviewCommandService,
            TrustedLearningApplicationAuthority,
            TrustedLearningDecisionAuthority,
            TrustedLearningReviewAuthority,
        )
        for authority in (
            TrustedLearningReviewAuthority,
            TrustedLearningDecisionAuthority,
            TrustedLearningApplicationAuthority,
        ):
            fields = set(authority.__dataclass_fields__)
            self.assertTrue({"identity", "permissions", "mfa_verified", "access_active"}.issubset(fields))
            self.assertTrue({"headers", "body", "query", "role", "tenant_id"}.isdisjoint(fields))
        for method in (
            LearningProposalReviewCommandService.record_learning_proposal_review,
            LearningProposalDecisionCommandService.record_learning_proposal_decision,
            LearningApplicationAuthorizationCommandService.authorize_learning_proposal_application,
        ):
            self.assertTrue({"headers", "body", "query", "role", "tenant_id"}.isdisjoint(
                inspect.signature(method).parameters
            ))

    def test_phase23_event_and_capability_allowlists_are_exact(self):
        from foundation.learning_proposal_governance import CAPABILITY_BY_TARGET, EVENT_CONTRACTS
        self.assertEqual(EVENT_CONTRACTS, {
            "learning_proposal.reviewed": 1,
            "learning_proposal.decision_recorded": 1,
            "learning_application.authorized": 1,
        })
        self.assertEqual(CAPABILITY_BY_TARGET, {
            "ModelPolicy": "revise_model_policy",
            "AgentDefinition": "revise_agent_definition",
            "KnowledgeLayerRule": "revise_knowledge_layer_rule",
        })

    def test_no_application_executor_target_writer_or_external_effect_surface(self):
        source = Path(__file__).with_name("learning_proposal_governance.py").read_text(encoding="utf-8")
        for forbidden in (
            "learning_proposal.applied", "learning_application.completed", "model.updated",
            "agent_definition.updated", "knowledge_layer_rule.updated", "autonomy.changed",
            "ModelPolicy.objects", "AgentDefinition.objects", "KnowledgeLayerRule.objects",
            ".update(", ".delete(", "bulk_update(", "create_target_successor",
            "mutate_learning_target", "execute_learning_application", "import requests",
            "import httpx", "import subprocess", "os.system", "Popen(",
        ):
            self.assertNotIn(forbidden, source)

    def test_migration_evolution_is_0019_only(self):
        migration_names = {path.name for path in Path(__file__).with_name("migrations").glob("*.py")}
        self.assertEqual(len([name for name in migration_names if name.startswith("0019")]), 1)


class Phase26KnowledgeRuleApplicationContractTests(SimpleTestCase):
    def test_public_capability_is_exact_and_non_generic(self):
        from foundation.governed_learning_application import (
            APPLICATION_PERMISSION,
            KnowledgeLayerRuleGovernedApplicationService,
        )
        from foundation.learning_delta import KNOWLEDGE_RULE_OPERATION

        method = KnowledgeLayerRuleGovernedApplicationService.apply_validated_knowledge_layer_rule_source_reference_correction_v1
        parameters = set(inspect.signature(method).parameters)
        self.assertEqual(KNOWLEDGE_RULE_OPERATION, "learning.knowledge_layer_rule.source_reference.correct")
        self.assertEqual(APPLICATION_PERMISSION, "qms.learning_target.knowledge_rule_source_reference.apply")
        self.assertTrue({"authority", "authorization_id", "expected_delta_hash", "trace_id", "forward_receipt_id"}.issubset(parameters))
        self.assertTrue({"target_type", "field", "operation", "payload", "status", "publish", "activate"}.isdisjoint(parameters))

    def test_application_authority_accepts_no_request_claims(self):
        from foundation.governed_learning_application import TrustedKnowledgeRuleApplicationAuthority

        fields = set(TrustedKnowledgeRuleApplicationAuthority.__dataclass_fields__)
        self.assertTrue({"identity", "organization_id", "permissions", "mfa_verified", "access_active", "global_governance"}.issubset(fields))
        self.assertTrue({"headers", "body", "query", "role", "target_id", "payload"}.isdisjoint(fields))

    def test_phase26_migration_and_harness_are_single_and_explicit(self):
        root = Path(__file__).parent
        migrations = list((root / "migrations").glob("0021*.py"))
        self.assertEqual(len(migrations), 1)
        migration_text = migrations[0].read_text(encoding="utf-8")
        harness_text = (root / "postgres_phase26_harness.py").read_text(encoding="utf-8")
        self.assertIn("knowledge_layer_rule.source_reference_corrected", migration_text)
        self.assertIn("compensation must restore the exact pre-forward source reference", migration_text)
        self.assertIn("REVOKE ALL ON FUNCTION normative.apply_validated", migration_text)
        self.assertEqual(harness_text.count('"after_claim"'), 1)
        self.assertIn('"before_commit"', harness_text)
