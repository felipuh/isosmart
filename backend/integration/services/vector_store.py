"""
Vector store service for assistant RAG.

Uses Chroma (local persistent) with its built-in ONNX all-MiniLM-L6-v2
embedding function — no extra dependencies beyond what's already installed.

pysqlite3-binary must be installed (already done) to provide sqlite3 >= 3.35.
The __init__ of this module applies the sqlite3 shim so Chroma can start.
"""

# ──────────────────────────────────────────────────────────────────
# sqlite3 shim — must be the very first thing before chromadb import
# ──────────────────────────────────────────────────────────────────
try:
    import pysqlite3 as _pysqlite3  # noqa: F401
    import sys as _sys
    _sys.modules['sqlite3'] = _sys.modules.pop('pysqlite3')
except ImportError:
    pass  # system sqlite3 may be recent enough

import logging
import os
import uuid
from typing import List, Optional

import chromadb
from django.conf import settings

logger = logging.getLogger(__name__)

_CHROMA_PATH = getattr(
    settings,
    'CHROMA_PERSIST_DIRECTORY',
    os.path.join(settings.BASE_DIR, '..', '..', 'data', 'chromadb'),
)

_client: Optional[chromadb.PersistentClient] = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        os.makedirs(_CHROMA_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=_CHROMA_PATH)
    return _client


def _collection_name(org_id: int) -> str:
    return f'isosmart_org_{org_id}'


# ──────────────────────────────────────────────────────────────────
# VectorIndexService
# ──────────────────────────────────────────────────────────────────

class VectorIndexService:
    """Index text chunks into Chroma for a given organization."""

    @staticmethod
    def _get_collection(org_id: int):
        client = _get_client()
        return client.get_or_create_collection(
            name=_collection_name(org_id),
            metadata={'hnsw:space': 'cosine'},
        )

    @classmethod
    def upsert_chunk(
        cls,
        org_id: int,
        document_id: str,
        chunk_index: int,
        chunk_text: str,
        source_title: str = '',
        module: str = '',
        standard_code: str = '',
        clause_reference: str = '',
    ) -> str:
        """Upsert one chunk into the org collection. Returns the vector_id."""
        vector_id = f'{org_id}_{document_id}_{chunk_index}'
        collection = cls._get_collection(org_id)
        collection.upsert(
            ids=[vector_id],
            documents=[chunk_text],
            metadatas=[{
                'org_id': org_id,
                'document_id': document_id,
                'chunk_index': chunk_index,
                'source_title': source_title[:255],
                'module': module[:60],
                'standard_code': standard_code[:40],
                'clause_reference': clause_reference[:40],
            }],
        )
        return vector_id

    @classmethod
    def delete_document(cls, org_id: int, document_id: str) -> int:
        """Remove all chunks for a document. Returns count deleted."""
        collection = cls._get_collection(org_id)
        results = collection.get(
            where={'document_id': document_id},
            include=[],
        )
        ids_to_delete = results.get('ids') or []
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
        return len(ids_to_delete)

    @classmethod
    def index_chunks(
        cls,
        org_id: int,
        document_id: str,
        chunks: List[str],
        source_title: str = '',
        module: str = '',
        standard_code: str = '',
        clause_reference: str = '',
    ) -> List[str]:
        """Index a list of text chunks. Returns list of vector_ids."""
        vector_ids = []
        for idx, chunk_text in enumerate(chunks):
            if not chunk_text.strip():
                continue
            vid = cls.upsert_chunk(
                org_id=org_id,
                document_id=document_id,
                chunk_index=idx,
                chunk_text=chunk_text,
                source_title=source_title,
                module=module,
                standard_code=standard_code,
                clause_reference=clause_reference,
            )
            vector_ids.append(vid)
        return vector_ids


# ──────────────────────────────────────────────────────────────────
# AssistantVectorSearchService
# ──────────────────────────────────────────────────────────────────

class AssistantVectorSearchService:
    """
    Semantic search over indexed document chunks for a given org.

    Filters are optional — pass module/standard_code/clause_reference
    to narrow results to the current screen context.
    """

    @classmethod
    def search(
        cls,
        org_id: int,
        query_text: str,
        n_results: int = 3,
        module: Optional[str] = None,
        standard_code: Optional[str] = None,
        clause_reference: Optional[str] = None,
    ) -> List[dict]:
        """
        Returns up to n_results chunks as dicts with keys:
            chunk_text, source_title, module, standard_code,
            clause_reference, document_id, chunk_index, distance
        """
        if not query_text or not query_text.strip():
            return []

        try:
            client = _get_client()
            col_name = _collection_name(org_id)

            # If collection doesn't exist yet, return empty
            existing = [c.name for c in client.list_collections()]
            if col_name not in existing:
                return []

            collection = client.get_collection(col_name)

            # Build optional metadata filter
            where_clause = None
            filters = {}
            if module:
                filters['module'] = module
            if standard_code:
                filters['standard_code'] = standard_code
            if clause_reference:
                filters['clause_reference'] = clause_reference

            if len(filters) == 1:
                key, val = next(iter(filters.items()))
                where_clause = {key: val}
            elif len(filters) > 1:
                where_clause = {'$and': [{k: v} for k, v in filters.items()]}

            query_kwargs = {
                'query_texts': [query_text],
                'n_results': min(n_results, max(collection.count(), 1)),
                'include': ['documents', 'metadatas', 'distances'],
            }
            if where_clause:
                query_kwargs['where'] = where_clause

            results = collection.query(**query_kwargs)

            chunks = []
            docs = (results.get('documents') or [[]])[0]
            metas = (results.get('metadatas') or [[]])[0]
            dists = (results.get('distances') or [[]])[0]

            for doc, meta, dist in zip(docs, metas, dists):
                chunks.append({
                    'chunk_text': doc,
                    'source_title': meta.get('source_title', ''),
                    'module': meta.get('module', ''),
                    'standard_code': meta.get('standard_code', ''),
                    'clause_reference': meta.get('clause_reference', ''),
                    'document_id': meta.get('document_id', ''),
                    'chunk_index': meta.get('chunk_index', 0),
                    'distance': round(float(dist), 4),
                })

            # Filter by relevance: cosine distance < 0.7 (similarity > 0.3)
            return [c for c in chunks if c['distance'] < 0.70]

        except Exception as exc:
            logger.warning('VectorSearch error org=%s: %s', org_id, exc)
            return []
