"""Concrete source adapters; policy semantics come from the governed runtime.

SOURCE: source agents[Autonomy Policy Engine], ADR-0005.
DERIVATION: AgentRun.effective_autonomy_ceiling and
AgentDecisionCommandService enforce the published ModelPolicy and human gate.
This adapter never authorizes or performs a material action.
"""

from django.utils import timezone

from .agent_execution_contract import AgentExecutionResult, ExecutionStatus, Finding
from .human_decision import AgentDecisionCommandService
from .models import (
    AgentRun, ChangeProcess, Evidence, MeasurementDefinition, Objective, Opportunity,
    Process, QmsScope, QmsScopeProcess, Risk, Stakeholder, StakeholderRequirement,
)
from .tenant_context import trusted_tenant_context


class AutonomyPolicyAdapter:
    capability = "source.autonomy_policy_engine"

    def __init__(self, *, identity, run_id, using="worker"):
        self.identity, self.run_id, self.using = identity, run_id, using

    def execute(self, request):
        if request.capability != self.capability or str(request.tenant_id) != str(self.identity.tenant_id):
            raise ValueError("autonomy adapter request binding mismatch")
        with trusted_tenant_context(
            self.identity, actor_id=request.actor_id, trace_id=request.trace_id, using=self.using,
        ):
            run = AgentRun.objects.using(self.using).get(
                id=self.run_id, organization_id=request.organization_id,
                agent_definition_id=request.agent_definition_id,
                model_policy_id=request.model_policy_id, status=AgentRun.Status.RUNNING,
            )
        decision = AgentDecisionCommandService(using=self.using).record_agent_decision(
            identity=self.identity, agent_run_id=run.id,
            decision_type="autonomy_policy_evaluation",
            payload={"effective_autonomy_ceiling": run.effective_autonomy_ceiling,
                     "execution_authorized": False},
            confidence="1.0000", explainability={
                "source": "AgentRunCommandService.start_agent_run / human_decision._human_gate_required",
                "model_policy_id": str(run.model_policy_id),
                "confidence_semantics": "deterministic_policy_evaluation_not_probability",
            }, decision_autonomy=request.requested_autonomy, actor_id=request.actor_id,
        )
        return AgentExecutionResult(
            run_id=run.id, agent_definition_id=run.agent_definition_id,
            status=ExecutionStatus.COMPLETED, started_at=run.started_at, completed_at=timezone.now(),
            evaluated_references=request.requirement_references,
            findings=(Finding("AUTONOMY_POLICY", f"A{run.effective_autonomy_ceiling}; human_gate_required={decision.human_gate_required}"),),
            evidence_consumed=request.evidence_references,
            recommendation_basis=request.inputs,
            deterministic_rule_results=({
                "effective_autonomy_ceiling": str(run.effective_autonomy_ceiling),
                "human_gate_required": str(decision.human_gate_required).lower(),
                "execution_authorized": "false",
                "decision_id": str(decision.decision_id),
            },),
            provenance={**request.provenance_context, "request_id": str(request.request_id),
                        "model_policy_id": str(run.model_policy_id), "trace_id": str(run.trace_id)},
            audit_references=(str(decision.audit_id),), emitted_events=(str(decision.event_id),),
        )


class StakeholderIntelligenceAdapter:
    """Execute the existing SIE graph algorithm on organization-scoped rows.

    This is a graph-analysis slice, not a normative compliance assessment.
    No legacy relevance score is relabelled as influence or satisfaction.
    """

    capability = "source.stakeholder_intelligence_agent"

    def __init__(self, *, identity, run_id, using="worker"):
        self.identity, self.run_id, self.using = identity, run_id, using

    def execute(self, request):
        from ai_modules.sie.services.stakeholder_intelligence import StakeholderIntelligenceEngine
        from .canonical import canonical_hash, canonical_json

        if request.capability != self.capability or str(request.tenant_id) != str(self.identity.tenant_id):
            raise ValueError("stakeholder adapter request binding mismatch")
        with trusted_tenant_context(self.identity, actor_id=request.actor_id, trace_id=request.trace_id, using=self.using):
            run = AgentRun.objects.using(self.using).get(
                id=self.run_id, organization_id=request.organization_id,
                agent_definition_id=request.agent_definition_id, status=AgentRun.Status.RUNNING,
            )
            rows = [{"id": str(row.id), "name": row.name, "stakeholder_type": row.stakeholder_type}
                    for row in Stakeholder.objects.using(self.using).filter(
                        tenant_id=self.identity.tenant_id, organization_id=request.organization_id,
                    ).order_by("id")]
        if not rows:
            raise ValueError("no organization-scoped stakeholders to analyze")
        engine = StakeholderIntelligenceEngine()
        graph = engine.build_stakeholder_network(rows)
        metrics = engine.calculate_influence_metrics()
        return AgentExecutionResult(
            run_id=run.id, agent_definition_id=run.agent_definition_id,
            status=ExecutionStatus.COMPLETED, started_at=run.started_at, completed_at=timezone.now(),
            evaluated_references=request.requirement_references,
            findings=(Finding("STAKEHOLDER_NETWORK", f"{len(graph.nodes)} stakeholders; {len(graph.edges)} inferred relationships"),),
            evidence_consumed=request.evidence_references, recommendation_basis=request.inputs,
            deterministic_rule_results=({"algorithm": "StakeholderIntelligenceEngine.calculate_influence_metrics",
                                         "metrics": canonical_json(metrics), "input_snapshot": canonical_json(rows)},),
            warnings=("Heuristic network analysis; normative rules and requirement assessment remain unimplemented.",),
            provenance={**request.provenance_context, "request_id": str(request.request_id),
                        "stakeholder_snapshot_hash": canonical_hash(rows), "trace_id": str(run.trace_id)},
        )


class ContextTwinMetadataAdapter:
    """Run only the deterministic legacy keyword scan against Evidence metadata."""

    capability = "source.context_twin_orchestrator"
    result_scope = "heuristic_metadata_analysis_only"

    def __init__(self, *, identity, run_id, using="worker"):
        self.identity, self.run_id, self.using = identity, run_id, using

    def execute(self, request):
        from ai_modules.sca.services.internal_context_metadata import analyze_internal_factors
        from .canonical import canonical_hash, canonical_json

        if request.capability != self.capability or str(request.tenant_id) != str(self.identity.tenant_id):
            raise ValueError("context adapter request binding mismatch")
        evidence_ids = tuple(dict.fromkeys(str(item.evidence_id) for item in request.evidence_references))
        if not evidence_ids:
            raise ValueError("context metadata analysis requires Evidence")

        with trusted_tenant_context(
            self.identity, actor_id=request.actor_id, trace_id=request.trace_id, using=self.using,
        ):
            run = AgentRun.objects.using(self.using).get(
                id=self.run_id, tenant_id=self.identity.tenant_id,
                organization_id=request.organization_id,
                agent_definition_id=request.agent_definition_id,
                capability=self.capability, status=AgentRun.Status.RUNNING,
            )
            evidence_rows = list(Evidence.objects.using(self.using).filter(
                id__in=evidence_ids, tenant_id=self.identity.tenant_id,
                organization_id=request.organization_id,
            ).order_by("id"))
        if len(evidence_rows) != len(evidence_ids):
            raise ValueError("requested Evidence is missing or outside the tenant/organization")

        snapshot = {
            "schema": "context-twin-evidence-metadata-v1",
            "tenant_id": str(self.identity.tenant_id),
            "organization_id": str(request.organization_id),
            "evidence": [{
                "evidence_id": str(row.id),
                "lineage_id": str(row.lineage_id),
                "revision": row.revision,
                "source_type": row.source_type,
                "source_uri": row.source_uri,
            } for row in evidence_rows],
        }
        snapshot_json = canonical_json(snapshot)
        snapshot_hash = canonical_hash(snapshot)
        legacy_input = [{
            "title": "",
            "source": row["source_uri"] or "",
            "type": row["source_type"],
            "content": "",
        } for row in snapshot["evidence"]]
        analysis = analyze_internal_factors(legacy_input)
        semantic_result = {
            "digital_metadata_keywords": analysis["tendencias_digitales"],
            "esg_metadata_keywords": analysis["factores_esg_detectados"],
        }
        summary = canonical_json(semantic_result)
        return AgentExecutionResult(
            run_id=run.id, agent_definition_id=run.agent_definition_id,
            status=ExecutionStatus.COMPLETED, started_at=run.started_at,
            completed_at=timezone.now(), evidence_consumed=tuple(
                item for item in request.evidence_references
                if str(item.evidence_id) in evidence_ids
            ),
            findings=(Finding("METADATA_KEYWORD_SCAN", summary),),
            deterministic_rule_results=({
                "algorithm": "ContextAnalyzer.analyze_internal_context",
                "input_snapshot_hash": snapshot_hash,
            },),
            warnings=("Heuristic metadata analysis only; no normative assessment or assertion.",),
            provenance={
                **request.provenance_context,
                "request_id": str(request.request_id),
                "tenant_id": str(self.identity.tenant_id),
                "organization_id": str(request.organization_id),
                "evidence_ids": canonical_json(evidence_ids),
                "input_snapshot": snapshot_json,
                "input_snapshot_hash": snapshot_hash,
                "adapter": self.__class__.__name__,
                "capability": self.capability,
                "agent_definition_id": str(run.agent_definition_id),
                "agent_run_id": str(run.id),
                "trace_id": str(run.trace_id),
            },
            result_scope=self.result_scope,
            not_normative_assessment=True,
            semantic_result=semantic_result,
        )


class ScopeAssuranceProcessCountAdapter:
    """Count canonical process links without interpreting free-form scope text."""

    capability = "source.scope_assurance_agent"
    result_scope = "structural_scope_process_count_only"

    def __init__(self, *, identity, run_id, using="worker"):
        self.identity, self.run_id, self.using = identity, run_id, using

    def execute(self, request):
        from ai_modules.asb.services.scope_builder import ScopeBuilderEngine
        from .canonical import canonical_hash, canonical_json

        if request.capability != self.capability or str(request.tenant_id) != str(self.identity.tenant_id):
            raise ValueError("scope adapter request binding mismatch")
        scope_ids = tuple(dict.fromkeys(
            str(item.get("qms_scope_id", "")) for item in request.inputs
            if item.get("qms_scope_id")
        ))
        if len(scope_ids) != 1:
            raise ValueError("scope analysis requires exactly one canonical QmsScope revision")

        with trusted_tenant_context(
            self.identity, actor_id=request.actor_id, trace_id=request.trace_id, using=self.using,
        ):
            run = AgentRun.objects.using(self.using).get(
                id=self.run_id, tenant_id=self.identity.tenant_id,
                organization_id=request.organization_id,
                agent_definition_id=request.agent_definition_id,
                capability=self.capability, status=AgentRun.Status.RUNNING,
            )
            scope = QmsScope.objects.using(self.using).get(
                id=scope_ids[0], tenant_id=self.identity.tenant_id,
                organization_id=request.organization_id,
            )
            links = list(QmsScopeProcess.objects.using(self.using).filter(
                scope_revision_id=scope.id, tenant_id=self.identity.tenant_id,
                organization_id=request.organization_id,
            ).select_related("process").order_by("process_id"))

        snapshot = {
            "schema": "scope-assurance-process-links-v1",
            "tenant_id": str(self.identity.tenant_id),
            "organization_id": str(request.organization_id),
            "scope_id": str(scope.id),
            "lineage_id": str(scope.lineage_id),
            "revision": scope.revision,
            "process_ids": [str(link.process_id) for link in links],
        }
        snapshot_json = canonical_json(snapshot)
        snapshot_hash = canonical_hash(snapshot)
        process_rows = [{"name": link.process.name} for link in links]
        legacy_coverage = ScopeBuilderEngine()._analyze_process_coverage({"processes": process_rows})
        semantic_result = {"linked_process_count": legacy_coverage["total_processes"]}
        return AgentExecutionResult(
            run_id=run.id, agent_definition_id=run.agent_definition_id,
            status=ExecutionStatus.COMPLETED, started_at=run.started_at,
            completed_at=timezone.now(),
            findings=(Finding("SCOPE_PROCESS_LINK_COUNT", canonical_json(semantic_result)),),
            deterministic_rule_results=({
                "algorithm": "ScopeBuilderEngine._analyze_process_coverage",
                "input_snapshot_hash": snapshot_hash,
            },),
            warnings=("Structural process-link count only; no boundary or normative assessment.",),
            provenance={
                **request.provenance_context,
                "request_id": str(request.request_id),
                "tenant_id": str(self.identity.tenant_id),
                "organization_id": str(request.organization_id),
                "scope_id": str(scope.id),
                "scope_snapshot": snapshot_json,
                "input_snapshot_hash": snapshot_hash,
                "adapter": self.__class__.__name__,
                "capability": self.capability,
                "agent_definition_id": str(run.agent_definition_id),
                "agent_run_id": str(run.id),
                "trace_id": str(run.trace_id),
            },
            result_scope=self.result_scope,
            not_normative_assessment=True,
            semantic_result=semantic_result,
        )


class ProcessGraphAdapter:
    """Project explicit canonical foreign-key relationships into a tenant graph."""

    capability = "source.process_graph_agent"
    result_scope = "canonical_process_relationship_graph_only"

    def __init__(self, *, identity, run_id, using="worker"):
        self.identity, self.run_id, self.using = identity, run_id, using

    def execute(self, request):
        from ai_modules.spm.services.process_mapper import ProcessMapperEngine
        from .canonical import canonical_hash, canonical_json

        if request.capability != self.capability or str(request.tenant_id) != str(self.identity.tenant_id):
            raise ValueError("process graph adapter request binding mismatch")
        with trusted_tenant_context(
            self.identity, actor_id=request.actor_id, trace_id=request.trace_id, using=self.using,
        ):
            run = AgentRun.objects.using(self.using).get(
                id=self.run_id, tenant_id=self.identity.tenant_id,
                organization_id=request.organization_id,
                agent_definition_id=request.agent_definition_id,
                capability=self.capability, status=AgentRun.Status.RUNNING,
            )
            process_rows = list(Process.objects.using(self.using).filter(
                tenant_id=self.identity.tenant_id, organization_id=request.organization_id,
            ).order_by("id"))
            if not process_rows:
                raise ValueError("no canonical organization processes to graph")
            process_ids = [row.id for row in process_rows]
            measurements = list(MeasurementDefinition.objects.using(self.using).filter(
                tenant_id=self.identity.tenant_id, organization_id=request.organization_id,
                process_id__in=process_ids,
            ).order_by("id"))
            risks = list(Risk.objects.using(self.using).filter(
                tenant_id=self.identity.tenant_id, organization_id=request.organization_id,
                process_id__in=process_ids,
            ).order_by("id"))
            opportunities = list(Opportunity.objects.using(self.using).filter(
                tenant_id=self.identity.tenant_id, organization_id=request.organization_id,
                process_id__in=process_ids,
            ).order_by("id"))
            objectives = list(Objective.objects.using(self.using).filter(
                tenant_id=self.identity.tenant_id, organization_id=request.organization_id,
                metric_id__in=[row.id for row in measurements],
            ).order_by("id"))
            stakeholder_requirements = list(StakeholderRequirement.objects.using(self.using).filter(
                tenant_id=self.identity.tenant_id, organization_id=request.organization_id,
                owner_process_id__in=process_ids,
            ).order_by("id"))
            scope_links = list(QmsScopeProcess.objects.using(self.using).filter(
                tenant_id=self.identity.tenant_id, organization_id=request.organization_id,
                process_id__in=process_ids,
            ).select_related("scope_revision").order_by("id"))
            change_links = list(ChangeProcess.objects.using(self.using).filter(
                tenant_id=self.identity.tenant_id, organization_id=request.organization_id,
                process_id__in=process_ids,
            ).select_related("change_revision").order_by("id"))

        graph = ProcessMapperEngine().process_graph
        nodes = []
        edges = []

        def add_node(kind, entity_id, **attributes):
            reference = f"{kind}:{entity_id}"
            node = {"id": reference, "kind": kind, **attributes}
            nodes.append(node)
            graph.add_node(reference, **attributes, kind=kind)
            return reference

        def add_edge(source, target, relation):
            edge = {"from": source, "to": target, "relation": relation}
            edges.append(edge)
            graph.add_edge(source, target, relation=relation)

        process_refs = {}
        for row in process_rows:
            process_refs[row.id] = add_node(
                "process", row.id, name=row.name, process_type=row.process_type,
                status=row.status, owner_id=str(row.owner_id) if row.owner_id else None,
            )
        measurement_refs = {}
        for row in measurements:
            measurement_refs[row.id] = add_node(
                "measurement_definition", row.id, lineage_id=str(row.lineage_id),
                revision=row.revision, what_is_measured=row.what_is_measured,
                method=row.method, measurement_timing=row.measurement_timing,
            )
            add_edge(process_refs[row.process_id], measurement_refs[row.id], "measured_by")
        for row in risks:
            reference = add_node("risk", row.id, lineage_id=str(row.lineage_id), revision=row.revision)
            add_edge(process_refs[row.process_id], reference, "has_risk")
        for row in opportunities:
            reference = add_node("opportunity", row.id, lineage_id=str(row.lineage_id), revision=row.revision)
            add_edge(process_refs[row.process_id], reference, "has_opportunity")
        for row in objectives:
            reference = add_node(
                "objective", row.id, lineage_id=str(row.lineage_id), revision=row.revision,
                status=row.status, owner_id=str(row.owner_id) if row.owner_id else None,
            )
            add_edge(reference, measurement_refs[row.metric_id], "tracks_measurement")
        for row in stakeholder_requirements:
            reference = add_node(
                "stakeholder_requirement", row.id, stakeholder_id=str(row.stakeholder_id),
                lineage_id=str(row.lineage_id), revision=row.revision,
                qms_addressed=row.qms_addressed,
            )
            add_edge(process_refs[row.owner_process_id], reference, "owns_requirement")
        for link in scope_links:
            reference = f"scope:{link.scope_revision_id}"
            if not graph.has_node(reference):
                add_node("scope", link.scope_revision_id,
                         lineage_id=str(link.scope_revision.lineage_id),
                         revision=link.scope_revision.revision)
            add_edge(process_refs[link.process_id], reference, "included_in_scope")
        for link in change_links:
            change = link.change_revision
            reference = f"change:{change.id}"
            if not graph.has_node(reference):
                add_node("change", change.id, lineage_id=str(change.lineage_id),
                         revision=change.revision, change_type=change.change_type,
                         status=change.status)
            add_edge(process_refs[link.process_id], reference, "affected_by_change")

        nodes.sort(key=lambda node: node["id"])
        edges.sort(key=lambda edge: (edge["from"], edge["relation"], edge["to"]))
        snapshot = {
            "schema": "process-graph-canonical-relations-v1",
            "tenant_id": str(self.identity.tenant_id),
            "organization_id": str(request.organization_id),
            "nodes": nodes,
            "edges": edges,
        }
        snapshot_json = canonical_json(snapshot)
        snapshot_hash = canonical_hash(snapshot)
        semantic_result = {"nodes": nodes, "edges": edges}
        return AgentExecutionResult(
            run_id=run.id, agent_definition_id=run.agent_definition_id,
            status=ExecutionStatus.COMPLETED, started_at=run.started_at,
            completed_at=timezone.now(),
            findings=(Finding("CANONICAL_PROCESS_GRAPH", canonical_json({
                "node_count": len(nodes), "edge_count": len(edges),
            })),),
            deterministic_rule_results=({
                "algorithm": "ProcessMapperEngine.process_graph_with_canonical_foreign_keys",
                "input_snapshot_hash": snapshot_hash,
            },),
            warnings=(
                "Canonical relationship graph only; no inferred process interactions, KPI evaluation, or normative assessment.",
                "Evidence references are not linked to Process by a source-defined canonical relation.",
            ),
            provenance={
                **request.provenance_context,
                "request_id": str(request.request_id),
                "tenant_id": str(self.identity.tenant_id),
                "organization_id": str(request.organization_id),
                "canonical_graph_snapshot": snapshot_json,
                "input_snapshot_hash": snapshot_hash,
                "adapter": self.__class__.__name__,
                "capability": self.capability,
                "agent_definition_id": str(run.agent_definition_id),
                "agent_run_id": str(run.id),
                "trace_id": str(run.trace_id),
                "unlinked_evidence_ids": canonical_json(
                    tuple(str(item.evidence_id) for item in request.evidence_references)
                ),
            },
            result_scope=self.result_scope,
            not_normative_assessment=True,
            semantic_result=semantic_result,
        )


SOURCE_ADAPTERS = {adapter.capability: adapter for adapter in (
    AutonomyPolicyAdapter, StakeholderIntelligenceAdapter, ContextTwinMetadataAdapter,
    ScopeAssuranceProcessCountAdapter, ProcessGraphAdapter,
)}
