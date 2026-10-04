"""Application services for the original source-artifact API contracts."""

from dataclasses import dataclass
from uuid import UUID, uuid4

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import OperationalError, connections
from django.db.models import Max, Q
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash, canonical_json
from .document_evidence import DocumentEvidenceCommandService
from .foundation_gate import FoundationGateCommandService, FoundationGateError
from .human_decision import (
    AuthorizedHumanContext,
    HumanDecisionGateService,
)
from .models import (
    AgentDecision,
    Approval,
    ConceptMastery,
    DomainEvent,
    LearningPath,
    QuestionBank,
    QuizAttempt,
    Recommendation,
    RecommendationBasis,
    TenantProjection,
    TransactionalOutbox,
    UserProjection,
)
from .onboarding import onboarding_steps
from .tenant_context import TrustedTenantIdentity, trusted_tenant_context


class SourceArtifactAPIError(Exception):
    def __init__(self, code, detail, status_code=400):
        super().__init__(detail)
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True)
class SourceArtifactPrincipal:
    identity: TrustedTenantIdentity
    tenant_id: UUID
    user_projection_id: UUID
    actor_id: UUID
    roles: tuple[str, ...]
    role_code: str | None
    industry_code: str | None
    client_id: str
    scopes: frozenset[str]


def foundation_database_alias(alias):
    if alias in settings.DATABASES:
        return alias
    default_engine = settings.DATABASES["default"]["ENGINE"]
    if settings.IS_DEVELOPMENT and default_engine.endswith("sqlite3"):
        return "default"
    raise SourceArtifactAPIError(
        "FOUNDATION_DATABASE_UNAVAILABLE",
        f"the configured PostgreSQL role alias '{alias}' is unavailable",
        503,
    )


def _uuid(value, *, code="AUTHORITY_INVALID"):
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise SourceArtifactAPIError(code, "authenticated identity claims are incomplete", 403) from exc


def _public_options(options):
    if not isinstance(options, list):
        return []
    return [
        {"id": option["id"], "label": option.get("label") or option.get("text") or ""}
        for option in options
        if isinstance(option, dict) and isinstance(option.get("id"), str)
    ]


def _resolve_tenant_projection_id(external_tenant_id, *, using):
    if settings.IS_DEVELOPMENT and connections[using].vendor == "sqlite":
        tenant = TenantProjection.objects.using(using).get(
            adminapps_tenant_id=external_tenant_id,
            lifecycle_status=TenantProjection.LifecycleStatus.ACTIVE,
            provisioning_status=TenantProjection.ProvisioningStatus.COMPLETE,
            reconciliation_status=TenantProjection.ReconciliationStatus.IN_SYNC,
        )
        return tenant.id
    with connections[using].cursor() as cursor:
        cursor.execute(
            "SELECT qms.foundation_0025_resolve_tenant_projection(%s)",
            [str(external_tenant_id)],
        )
        row = cursor.fetchone()
    return row[0] if row else None


def resolve_source_artifact_principal(request, *, using="app"):
    using = foundation_database_alias(using)
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        raise SourceArtifactAPIError("AUTHENTICATION_REQUIRED", "authentication is required", 401)
    claims = request.auth
    if claims is None or not hasattr(claims, "get"):
        raise SourceArtifactAPIError("TRUSTED_AUTHORITY_REQUIRED", "a validated AdminApps bearer identity is required", 403)

    organization_external_id = None
    profile = getattr(request, "user_profile", None)
    organization = getattr(profile, "organization", None)
    if organization is not None:
        organization_external_id = getattr(organization, "external_id", None)
    organization_external_id = organization_external_id or claims.get("organization_id")
    tenant_external_id = _uuid(organization_external_id)
    actor_id = _uuid(claims.get("user_id") or claims.get("sub") or getattr(request.user, "pk", None))

    try:
        tenant_id = _resolve_tenant_projection_id(tenant_external_id, using=using)
    except TenantProjection.DoesNotExist as exc:
        raise SourceArtifactAPIError("TENANT_NOT_READY", "tenant is not provisioned and reconciled", 403) from exc
    except OperationalError as exc:
        raise SourceArtifactAPIError("AUTHORITY_UNAVAILABLE", "tenant authority is unavailable", 503) from exc
    if tenant_id is None:
        raise SourceArtifactAPIError("TENANT_NOT_READY", "tenant is not provisioned and reconciled", 403)

    identity = TrustedTenantIdentity(subject=str(actor_id), tenant_id=tenant_id)
    try:
        with trusted_tenant_context(
            identity, actor_id=actor_id, trace_id=uuid4(), using=using,
        ):
            tenant = TenantProjection.objects.using(using).get(
                id=tenant_id,
                adminapps_tenant_id=tenant_external_id,
                lifecycle_status=TenantProjection.LifecycleStatus.ACTIVE,
                provisioning_status=TenantProjection.ProvisioningStatus.COMPLETE,
                reconciliation_status=TenantProjection.ReconciliationStatus.IN_SYNC,
            )
            projection = UserProjection.objects.using(using).get(
                adminapps_user_id=actor_id,
                tenant_id=tenant.id,
                lifecycle_status=UserProjection.LifecycleStatus.ACTIVE,
            )
    except TenantProjection.DoesNotExist as exc:
        raise SourceArtifactAPIError("TENANT_NOT_READY", "tenant changed during authority resolution", 403) from exc
    except UserProjection.DoesNotExist as exc:
        raise SourceArtifactAPIError("USER_NOT_PROVISIONED", "user has no active tenant projection", 403) from exc
    except OperationalError as exc:
        raise SourceArtifactAPIError("AUTHORITY_UNAVAILABLE", "tenant authority is unavailable", 503) from exc

    role = str(claims.get("role") or "").strip()
    scope_claim = claims.get("scope") or ""
    if isinstance(scope_claim, str):
        scopes = frozenset(scope_claim.split())
    elif isinstance(scope_claim, (list, tuple, set)):
        scopes = frozenset(str(item) for item in scope_claim)
    else:
        scopes = frozenset()
    return SourceArtifactPrincipal(
        identity=identity,
        tenant_id=tenant.id,
        user_projection_id=projection.id,
        actor_id=actor_id,
        roles=(role,) if role else (),
        role_code=role or None,
        industry_code=str(claims.get("industry_code") or "").strip() or None,
        client_id=str(claims.get("client_id") or "adminapps-sso"),
        scopes=scopes,
    )


def onboarding_status(principal, *, using="app"):
    using = foundation_database_alias(using)
    with trusted_tenant_context(
        principal.identity, actor_id=principal.actor_id, trace_id=uuid4(), using=using,
    ):
        paths = list(LearningPath.objects.using(using).select_related(
            "standard_edition__standard",
        ).filter(
            active=True,
            standard_edition__status="published",
            standard_edition__standard__code__icontains="9000",
            standard_edition__edition__icontains="2026",
        ).filter(
            Q(role_code__isnull=True) | Q(role_code=principal.role_code),
        ).filter(
            Q(industry_code__isnull=True) | Q(industry_code=principal.industry_code),
        ).order_by("industry_code", "role_code", "id"))
        path_data = []
        for path in paths:
            questions = QuestionBank.objects.using(using).filter(
                learning_path_id=path.id,
                publication_state=QuestionBank.PublicationState.PUBLISHED,
            ).filter(
                Q(industry_code__isnull=True) | Q(industry_code=principal.industry_code),
            ).order_by("-version", "difficulty", "id")
            selected_questions = list(questions)
            bank_version = selected_questions[0].version if selected_questions else None
            if bank_version is not None:
                selected_questions = [
                    question for question in selected_questions if question.version == bank_version
                ]
            path_data.append({
                "id": str(path.id),
                "edition_id": str(path.standard_edition_id),
                "edition": path.standard_edition.edition,
                "standard_code": path.standard_edition.standard.code,
                "role_code": path.role_code,
                "industry_code": path.industry_code,
                "required_score": str(path.required_score),
                "question_bank_version": bank_version,
                "questions": [
                    {
                        "id": str(question.id),
                        "concept_key": question.concept_key,
                        "difficulty": question.difficulty,
                        "scenario": question.scenario,
                        "options": _public_options(question.options_json),
                    }
                    for question in selected_questions
                ],
            })
        path_ids = [path["id"] for path in path_data if path["questions"]]
        attempts = QuizAttempt.objects.using(using).filter(
            tenant_id=principal.tenant_id,
            user_id=principal.user_projection_id,
        ).order_by("-completed_at", "-started_at")
        latest = attempts.first()
        completed_attempt = attempts.filter(
            learning_path_id__in=path_ids,
            passed=True,
        ).first()
        latest_data = None
        if latest:
            latest_data = {
                "id": str(latest.id),
                "learning_path_id": str(latest.learning_path_id),
                "score": str(latest.score) if latest.score is not None else None,
                "passed": latest.passed,
                "question_bank_version": latest.question_bank_version,
                "weak_concepts": latest.weak_concepts,
                "provenance_hash": latest.provenance_hash,
                "completed_at": latest.completed_at.isoformat() if latest.completed_at else None,
            }
        completed = completed_attempt is not None
        mastery = ConceptMastery.objects.using(using).filter(
            tenant_id=principal.tenant_id,
            user_id=principal.user_projection_id,
        ).order_by("retraining_due_at", "concept_key")
        if not path_ids:
            gate_status = "content_unavailable"
        elif completed:
            gate_status = "passed"
        elif latest:
            gate_status = "retraining_required"
        else:
            gate_status = "not_started"
        steps = onboarding_steps(principal, using=using)
        return {
            "foundation_gate": {
                "required": True,
                "status": gate_status,
                "unlocks_quality_baseline": completed,
                "paths": path_data,
                "latest_attempt": latest_data,
                "completion_attempt_id": str(completed_attempt.id) if completed_attempt else None,
                "concept_mastery": [
                    {
                        "concept_key": item.concept_key,
                        "score": str(item.score) if item.score is not None else None,
                        "last_assessed_at": item.last_assessed_at.isoformat() if item.last_assessed_at else None,
                        "retraining_due_at": item.retraining_due_at.isoformat() if item.retraining_due_at else None,
                    }
                    for item in mastery
                ],
            },
            "steps": steps,
            "step_count": len(steps),
        }


def list_recommendations(principal, *, clause=None, using="app"):
    using = foundation_database_alias(using)
    with trusted_tenant_context(
        principal.identity, actor_id=principal.actor_id, trace_id=uuid4(), using=using,
    ):
        queryset = Recommendation.objects.using(using).filter(
            tenant_id=principal.tenant_id,
            status=Recommendation.Status.PROPOSED,
        )
        if clause:
            queryset = queryset.filter(
                basis_rows__requirement_control__clause__code=clause,
            )
        rows = queryset.order_by("-created_at", "id").distinct()[:100]
        return [
            {
                "id": str(row.id),
                "title": row.title,
                "body": row.body,
                "confidence": str(row.confidence),
                "assumptions": row.assumptions,
                "impact": row.impact,
                "status": row.status,
                "intended_autonomy": f"A{row.intended_autonomy}",
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]


def recommendation_basis(principal, recommendation_id, *, using="app"):
    using = foundation_database_alias(using)
    with trusted_tenant_context(
        principal.identity, actor_id=principal.actor_id, trace_id=uuid4(), using=using,
    ):
        try:
            recommendation = Recommendation.objects.using(using).get(
                id=recommendation_id, tenant_id=principal.tenant_id,
            )
        except Recommendation.DoesNotExist as exc:
            raise SourceArtifactAPIError("NOT_FOUND", "recommendation was not found", 404) from exc
        basis_rows = RecommendationBasis.objects.using(using).filter(
            recommendation_id=recommendation.id,
            tenant_id=principal.tenant_id,
        ).select_related(
            "standard_edition__standard",
            "requirement_control__clause",
            "knowledge_layer_rule",
            "evidence",
        ).order_by("created_at", "id")
        return {
            "recommendation_id": str(recommendation.id),
            "basis": [
                {
                    "id": str(item.id),
                    "standard": item.standard_edition.standard.code,
                    "edition": item.standard_edition.edition,
                    "requirement_code": item.requirement_control.clause.code,
                    "requirement_text": item.requirement_control.paraphrase,
                    "rule_id": str(item.knowledge_layer_rule_id),
                    "rule_version": item.knowledge_layer_rule.version,
                    "evidence_id": str(item.evidence_id),
                    "evidence_hash": item.evidence.content_hash,
                    "evidence_revision": item.evidence.revision,
                    "rationale": item.rationale,
                    "model": {
                        "provider": item.model_provider,
                        "identifier": item.model_identifier,
                        "version": item.model_version,
                        "prompt_version": item.prompt_version,
                        "rule_bundle_version": item.rule_bundle_version,
                        "dataset_version_reference": item.dataset_version_reference,
                        "embedding_namespace": item.embedding_namespace,
                    },
                    "trace_id": str(item.trace_id),
                    "created_at": item.created_at.isoformat(),
                }
                for item in basis_rows
            ],
        }


def record_approval_decision(principal, decision_id, *, decision, comments, trace_id, using="human_approver"):
    using = foundation_database_alias(using)
    if not principal.roles:
        raise SourceArtifactAPIError("APPROVAL_ROLE_REQUIRED", "an authorized approval role is required", 403)
    authority = AuthorizedHumanContext(
        identity=principal.identity,
        user_projection_id=principal.user_projection_id,
        adminapps_user_id=principal.actor_id,
        authorized_roles=principal.roles,
        authority_source="adminapps_contract",
    )
    service = HumanDecisionGateService(using=using)
    try:
        if decision == Approval.Decision.APPROVE:
            result = service.record_human_approval(
                authority=authority, agent_decision_id=decision_id,
                comments=comments, trace_id=trace_id,
            )
        elif decision == Approval.Decision.REJECT:
            result = service.record_human_rejection(
                authority=authority, agent_decision_id=decision_id,
                comments=comments, trace_id=trace_id,
            )
        else:
            result = service.request_human_changes(
                authority=authority, agent_decision_id=decision_id,
                comments=comments, trace_id=trace_id,
            )
    except AgentDecision.DoesNotExist as exc:
        raise SourceArtifactAPIError("NOT_FOUND", "approval decision was not found", 404) from exc
    except PermissionError as exc:
        raise SourceArtifactAPIError("FORBIDDEN", str(exc), 403) from exc
    except ValueError as exc:
        raise SourceArtifactAPIError("DECISION_INVALID", str(exc), 409) from exc
    return result


def create_evidence(principal, data, *, trace_id, using="app"):
    using = foundation_database_alias(using)
    try:
        return DocumentEvidenceCommandService(using=using).create_evidence(
            identity=principal.identity,
            organization_id=data["organization_id"],
            source_type=data["source_type"],
            source_uri=data.get("source_uri"),
            content_hash=data.get("content_hash"),
            captured_at=data["captured_at"],
            trust_score=data.get("trust_score"),
            document_version_id=data.get("document_version_id"),
            change_reason=data.get("change_reason"),
            actor_id=principal.actor_id,
            trace_id=trace_id,
        )
    except ObjectDoesNotExist as exc:
        raise SourceArtifactAPIError("REFERENCE_NOT_FOUND", "evidence organization or document version was not found", 404) from exc
    except ValueError as exc:
        raise SourceArtifactAPIError("EVIDENCE_INVALID", str(exc), 422) from exc


def publish_domain_event(principal, data, *, using="app"):
    using = foundation_database_alias(using)
    if "domain:events:publish" not in principal.scopes:
        raise SourceArtifactAPIError("EVENT_PUBLISH_FORBIDDEN", "the validated principal lacks domain:events:publish", 403)
    event_type = data["event_type"]
    occurred_at = data["occurred_at"]
    if timezone.is_naive(occurred_at):
        raise SourceArtifactAPIError("EVENT_INVALID", "occurred_at must include a timezone", 422)
    payload = __import__("json").loads(canonical_json(data["payload"]))["value"]
    payload_hash = canonical_hash(payload)
    trace_id = data["trace_id"]
    with trusted_tenant_context(
        principal.identity, actor_id=principal.actor_id, trace_id=trace_id, using=using,
    ):
        existing = DomainEvent.objects.using(using).filter(
            event_id=data["event_id"], tenant_id=principal.tenant_id,
        ).first()
        if existing:
            same_event = (
                existing.event_type == event_type
                and existing.payload_hash == payload_hash
                and existing.aggregate_type == data["aggregate_type"]
                and existing.aggregate_id == data["aggregate_id"]
                and existing.aggregate_version == data["aggregate_version"]
                and existing.occurred_at == occurred_at
                and existing.trace_id == trace_id
                and existing.correlation_id == data.get("correlation_id")
                and existing.causation_id == data.get("causation_id")
                and existing.source == principal.client_id
            )
            if not same_event:
                raise SourceArtifactAPIError("IDEMPOTENCY_CONFLICT", "event_id was already used with different content", 409)
            return {"event_id": str(existing.event_id), "duplicate": True}
        current_version = DomainEvent.objects.using(using).filter(
            tenant_id=principal.tenant_id,
            aggregate_type=data["aggregate_type"],
            aggregate_id=data["aggregate_id"],
        ).aggregate(value=Max("aggregate_version"))["value"] or 0
        if data["aggregate_version"] != current_version + 1:
            raise SourceArtifactAPIError("AGGREGATE_VERSION_CONFLICT", "aggregate_version must advance exactly once", 409)
        DomainEvent.objects.using(using).create(
            event_id=data["event_id"],
            tenant_id=principal.tenant_id,
            event_type=event_type,
            schema_version=1,
            aggregate_type=data["aggregate_type"],
            aggregate_id=data["aggregate_id"],
            aggregate_version=data["aggregate_version"],
            occurred_at=occurred_at,
            trace_id=trace_id,
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id"),
            source=principal.client_id,
            payload=payload,
            payload_hash=payload_hash,
        )
        outbox = TransactionalOutbox.objects.using(using).create(
            tenant_id=principal.tenant_id,
            domain_event_id=data["event_id"],
            status=TransactionalOutbox.Status.PENDING,
            publish_attempts=0,
            available_at=timezone.now(),
        )
        audit_id = AuditWriterService(using=using).append(AuditAppend(
            tenant_id=principal.tenant_id,
            stream_type=data["aggregate_type"],
            stream_id=data["aggregate_id"],
            actor_type="integration",
            actor_id=str(principal.actor_id),
            action=event_type,
            entity_type=data["aggregate_type"],
            entity_id=data["aggregate_id"],
            trace_id=trace_id,
            occurred_at=occurred_at,
            after_hash=payload_hash,
            metadata={"event_id": str(data["event_id"]), "outbox_id": str(outbox.id), "schema_version": 1},
        ))
        return {"event_id": str(data["event_id"]), "outbox_id": str(outbox.id), "audit_id": str(audit_id), "duplicate": False}


def submit_foundation_attempt(principal, data, *, trace_id, using="app"):
    using = foundation_database_alias(using)
    try:
        result = FoundationGateCommandService(using=using).submit_attempt(
            identity=principal.identity,
            user_projection_id=principal.user_projection_id,
            learning_path_id=data["learning_path_id"],
            answers=data["answers"],
            actor_id=principal.actor_id,
            trace_id=trace_id,
            role_code=principal.role_code,
            industry_code=principal.industry_code,
        )
    except LearningPath.DoesNotExist as exc:
        raise SourceArtifactAPIError("LEARNING_PATH_NOT_FOUND", "no active published ISO 9000:2026 path matches", 404) from exc
    except FoundationGateError as exc:
        raise SourceArtifactAPIError(exc.code, str(exc), exc.status_code) from exc
    return result


def request_trace_id(request):
    value = getattr(request, "request_id", None) or request.headers.get("X-Trace-ID")
    if not value:
        return uuid4()
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise SourceArtifactAPIError("TRACE_ID_INVALID", "X-Trace-ID must be a UUID", 400) from exc