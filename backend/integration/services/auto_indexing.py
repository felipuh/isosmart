import logging


logger = logging.getLogger(__name__)


def _queue_text_index(
    org_id,
    document_id,
    text,
    source_title='',
    module='',
    standard_code='ISO 9001',
    clause_reference='',
):
    if not org_id or not document_id or not text or not str(text).strip():
        return

    from integration.tasks import index_text_as_chunks

    try:
        index_text_as_chunks.delay(
            org_id=org_id,
            document_id=document_id,
            text=str(text).strip(),
            source_title=source_title,
            module=module,
            standard_code=standard_code,
            clause_reference=clause_reference,
            version=1,
        )
    except Exception as exc:
        logger.warning('No se pudo encolar indexacion %s para org=%s: %s', document_id, org_id, exc)


def remove_indexed_artifact(org_id, document_id):
    if not org_id or not document_id:
        return 0

    from integration.models import AssistantDocumentChunk
    from integration.services.vector_store import VectorIndexService

    try:
        removed_vectors = VectorIndexService.delete_document(org_id, document_id)
        AssistantDocumentChunk.objects.filter(
            organization_id=org_id,
            document_id=document_id,
        ).delete()
        return removed_vectors
    except Exception as exc:
        logger.warning('No se pudo limpiar indice %s para org=%s: %s', document_id, org_id, exc)
        return 0


def queue_core_document_index(document):
    doc_type = (document.document_type or '').strip()
    module_map = {
        'politica': ('leadership', '5.2'),
        'procedimiento': ('operations', '8.1'),
        'acta': ('leadership', '9.3'),
        'reporte': ('performance', '9.1'),
        'otro': ('general', ''),
    }
    module, clause = module_map.get(doc_type, ('general', ''))
    text = '\n'.join([
        f'Titulo: {document.title}',
        f'Tipo: {doc_type}',
        f'Fuente: {document.source}',
        document.content or '',
    ]).strip()
    _queue_text_index(
        org_id=document.organization_id,
        document_id=f'core_document_{document.id}',
        text=text,
        source_title=document.title,
        module=module,
        standard_code='ISO 9001',
        clause_reference=clause,
    )


def queue_quality_policy_index(policy):
    text = '\n'.join([
        f'Titulo: {policy.title}',
        f'Version: {policy.version}',
        f'Estado: {policy.status}',
        f'Contenido: {policy.content}',
        f'Enfoque al cliente: {policy.customer_focus}',
        f'Marco para objetivos: {policy.framework_for_objectives}',
        f'Compromiso con requisitos: {policy.commitment_requirements}',
        f'Compromiso con mejora continua: {policy.commitment_improvement}',
    ]).strip()
    _queue_text_index(
        org_id=policy.organization_id,
        document_id=f'leadership_policy_{policy.id}',
        text=text,
        source_title=policy.title,
        module='leadership',
        standard_code='ISO 9001',
        clause_reference='5.2',
    )


def queue_leadership_commitment_index(commitment):
    text = '\n'.join([
        f'Titulo: {commitment.title}',
        f'Tipo de compromiso: {commitment.commitment_type}',
        f'Tipo de evidencia: {commitment.evidence_type}',
        f'Estado: {commitment.status}',
        f'Descripcion: {commitment.description}',
    ]).strip()
    _queue_text_index(
        org_id=commitment.organization_id,
        document_id=f'leadership_commitment_{commitment.id}',
        text=text,
        source_title=commitment.title,
        module='leadership',
        standard_code='ISO 9001',
        clause_reference='5.1',
    )


def queue_customer_focus_index(evidence):
    text = '\n'.join([
        f'Titulo: {evidence.title}',
        f'Tipo de enfoque: {evidence.focus_type}',
        f'Descripcion: {evidence.description}',
        f'Accion tomada: {evidence.action_taken}',
        f'Resultados: {evidence.results}',
    ]).strip()
    _queue_text_index(
        org_id=evidence.organization_id,
        document_id=f'customer_focus_{evidence.id}',
        text=text,
        source_title=evidence.title,
        module='leadership',
        standard_code='ISO 9001',
        clause_reference='5.1.2',
    )


def queue_memory_item_index(memory_item):
    from integration.tasks import index_memory_item

    if not memory_item or not memory_item.id:
        return
    try:
        index_memory_item.delay(memory_item.id)
    except Exception as exc:
        logger.warning('No se pudo encolar memoria %s para org=%s: %s', memory_item.id, memory_item.organization_id, exc)