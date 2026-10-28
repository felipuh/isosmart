"""
Celery tasks for assistant vector indexing.

Usage:
    from integration.tasks import index_text_as_chunks
    index_text_as_chunks.delay(
        org_id=1,
        document_id='policy-sg-001',
        text='Contenido del documento ...',
        source_title='Política SG-001',
        module='leadership',
        standard_code='ISO 9001',
        clause_reference='5.2',
    )
"""

import logging
import re

from celery import shared_task

logger = logging.getLogger(__name__)

# ── Chunking parameters ──────────────────────────────────────────
_CHUNK_SIZE = 400       # target chars per chunk
_CHUNK_OVERLAP = 60    # overlap chars between consecutive chunks


def _split_into_chunks(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP):
    """
    Simple sentence-aware chunker.
    Splits on sentence boundaries (.  !  ?) and merges into chunks of
    approximately `chunk_size` characters with `overlap` carried over.
    """
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return []

    # Split on sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ''

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= chunk_size:
            current = (current + ' ' + sentence).strip()
        else:
            if current:
                chunks.append(current)
            # Start new chunk with overlap from end of previous
            if len(current) >= overlap and overlap > 0:
                tail = current[-overlap:]
                current = (tail + ' ' + sentence).strip()
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def index_text_as_chunks(
    self,
    org_id: int,
    document_id: str,
    text: str,
    source_title: str = '',
    module: str = '',
    standard_code: str = '',
    clause_reference: str = '',
    version: int = 1,
):
    """
    Chunk raw text and index it into Chroma + persist chunk records in MySQL.
    Idempotent: deletes previous vectors for document_id before re-indexing.
    """
    from integration.models import AssistantDocumentChunk
    from integration.services.vector_store import VectorIndexService

    try:
        logger.info(
            'index_text_as_chunks start org=%s doc=%s chars=%s',
            org_id, document_id, len(text),
        )

        chunks = _split_into_chunks(text)
        if not chunks:
            logger.warning('index_text_as_chunks: no chunks for doc=%s', document_id)
            return {'status': 'empty', 'chunks': 0}

        # 1. Remove old vectors and DB records for this document
        VectorIndexService.delete_document(org_id, document_id)
        AssistantDocumentChunk.objects.filter(
            organization_id=org_id,
            document_id=document_id,
        ).delete()

        # 2. Index into Chroma and persist to MySQL
        vector_ids = VectorIndexService.index_chunks(
            org_id=org_id,
            document_id=document_id,
            chunks=chunks,
            source_title=source_title,
            module=module,
            standard_code=standard_code,
            clause_reference=clause_reference,
        )

        db_objs = [
            AssistantDocumentChunk(
                organization_id=org_id,
                document_id=document_id,
                chunk_index=idx,
                chunk_text=chunk,
                source_title=source_title,
                module=module,
                standard_code=standard_code,
                clause_reference=clause_reference,
                vector_id=vid,
                is_active=True,
                version=version,
            )
            for idx, (chunk, vid) in enumerate(zip(chunks, vector_ids))
        ]
        AssistantDocumentChunk.objects.bulk_create(db_objs)

        logger.info(
            'index_text_as_chunks done org=%s doc=%s chunks=%s',
            org_id, document_id, len(chunks),
        )
        return {'status': 'ok', 'chunks': len(chunks), 'document_id': document_id}

    except Exception as exc:
        logger.error('index_text_as_chunks error org=%s doc=%s: %s', org_id, document_id, exc)
        raise self.retry(exc=exc)


@shared_task
def index_memory_item(memory_item_id: int):
    """
    Index an AssistantMemoryItem into Chroma so it can be retrieved via RAG.
    Call this after creating/updating an AssistantMemoryItem.
    """
    from integration.models import AssistantMemoryItem

    try:
        item = AssistantMemoryItem.objects.get(id=memory_item_id, is_active=True)
    except AssistantMemoryItem.DoesNotExist:
        return {'status': 'not_found', 'id': memory_item_id}

    document_id = f'memory_item_{item.id}'
    text = f'{item.title}\n{item.content}'

    result = index_text_as_chunks.run(
        org_id=item.organization_id,
        document_id=document_id,
        text=text,
        source_title=item.title,
        module=item.module,
        standard_code=item.standard_code,
        clause_reference=item.clause_reference,
        version=1,
    )
    return {'status': 'ok', 'id': memory_item_id, 'document_id': document_id, 'index_result': result}
