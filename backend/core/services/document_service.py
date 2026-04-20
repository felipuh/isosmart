"""Document domain services for core module."""

from __future__ import annotations

import logging

from django.db import DatabaseError, transaction

from core.models import Document
from integration.services.auto_indexing import queue_core_document_index

logger = logging.getLogger(__name__)


class DocumentCreationError(Exception):
    """Raised when document creation workflow fails."""


def create_document_from_upload(*, organization_id: int, validated_data: dict, uploaded_by=None) -> Document:
    """Create and enqueue indexing for a document using validated upload payload."""
    try:
        with transaction.atomic():
            document = Document.objects.create(
                organization_id=organization_id,
                title=validated_data["title"],
                content=validated_data.get("content", ""),
                document_type=validated_data["document_type"],
                file_path=validated_data["file"],
                source=validated_data.get("source", "Sistema"),
                uploaded_by=uploaded_by,
            )

        queue_core_document_index(document)
        return document
    except DatabaseError as exc:
        logger.error("Database error creating document", exc_info=True)
        raise DocumentCreationError("No se pudo guardar el documento en base de datos") from exc
    except Exception as exc:
        logger.error("Unexpected error creating document", exc_info=True)
        raise DocumentCreationError("No se pudo completar el procesamiento del documento") from exc
