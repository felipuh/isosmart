"""
Pipeline controlado y auditable de señales externas para SCA.
Conecta fuentes confiables (ONU/IPCC/ISO) y persiste señales por organización.
"""

from __future__ import annotations

import hashlib
import json
import logging
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List

from core.models import AIAuditLog, ExternalContextSignal

logger = logging.getLogger(__name__)


class ExternalContextPipeline:
    """Recolecta señales externas para contexto ISO 4.1 con trazabilidad."""

    TRUSTED_SOURCES = [
        {
            'source_type': 'un',
            'source_name': 'UN Climate News',
            'url': 'https://news.un.org/feed/subscribe/en/news/topic/climate-change/feed/rss.xml',
            'tag_hints': ['climate', 'regulatorio', 'sustainability'],
        },
        {
            'source_type': 'ipcc',
            'source_name': 'IPCC News',
            'url': 'https://www.ipcc.ch/feed/',
            'tag_hints': ['climate', 'science', 'risk'],
        },
        {
            'source_type': 'iso',
            'source_name': 'ISO News',
            'url': 'https://www.iso.org/contents/news.rss',
            'tag_hints': ['iso', 'quality', 'regulatorio'],
        },
    ]

    def __init__(self, organization_id: int, timeout_seconds: int = 8):
        self.organization_id = organization_id
        self.timeout_seconds = timeout_seconds

    def collect_signals(self, max_items_per_source: int = 5) -> List[Dict[str, Any]]:
        """Descarga, clasifica y persiste señales externas."""
        all_signals: List[Dict[str, Any]] = []
        started_at = datetime.utcnow()

        for source in self.TRUSTED_SOURCES:
            try:
                xml_content = self._fetch_url(source['url'])
                parsed = self._parse_rss(xml_content)
                for item in parsed[:max_items_per_source]:
                    signal = self._normalize_signal(source, item)
                    if not signal:
                        continue
                    persisted = self._persist_signal(signal)
                    if persisted:
                        all_signals.append(signal)
            except Exception as exc:
                logger.warning('External source fetch failed (%s): %s', source['source_name'], exc)

        self._audit_run(started_at, all_signals)
        return all_signals

    def _fetch_url(self, url: str) -> str:
        req = urllib.request.Request(url, headers={'User-Agent': 'ISO-Smart/1.0'})
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
            return response.read().decode('utf-8', errors='replace')

    def _parse_rss(self, xml_content: str) -> List[Dict[str, str]]:
        root = ET.fromstring(xml_content)
        items = []
        for item in root.findall('.//item'):
            items.append({
                'title': (item.findtext('title') or '').strip(),
                'link': (item.findtext('link') or '').strip(),
                'description': (item.findtext('description') or '').strip(),
                'pubDate': (item.findtext('pubDate') or '').strip(),
            })
        return items

    def _normalize_signal(self, source: Dict[str, Any], item: Dict[str, str]) -> Dict[str, Any] | None:
        title = item.get('title') or ''
        summary = item.get('description') or ''
        if not title:
            return None

        normalized_text = f"{title} {summary}".lower()
        tags = list(source.get('tag_hints', []))
        impact_level = self._infer_impact_level(normalized_text)

        signal_hash = hashlib.sha256(
            f"{source['source_name']}|{title}|{item.get('link','')}".encode('utf-8')
        ).hexdigest()

        published_at = None
        if item.get('pubDate'):
            try:
                published_at = parsedate_to_datetime(item['pubDate'])
            except Exception:
                published_at = None

        return {
            'organization_id': self.organization_id,
            'source_type': source['source_type'],
            'source_name': source['source_name'],
            'source_url': item.get('link') or source['url'],
            'title': title[:300],
            'summary': summary[:3000],
            'signal_hash': signal_hash,
            'published_at': published_at,
            'impact_level': impact_level,
            'tags': tags,
            'raw_payload': item,
        }

    def _infer_impact_level(self, text: str) -> str:
        high_tokens = ['critical', 'mandatory', 'emergency', 'severe', 'catastrophic', 'urgent']
        medium_tokens = ['risk', 'climate', 'regulation', 'esg', 'compliance', 'supply chain']

        if any(token in text for token in high_tokens):
            return 'critical'
        if any(token in text for token in medium_tokens):
            return 'high'
        return 'medium'

    def _persist_signal(self, signal: Dict[str, Any]) -> bool:
        _, created = ExternalContextSignal.objects.get_or_create(
            organization_id=signal['organization_id'],
            source_name=signal['source_name'],
            signal_hash=signal['signal_hash'],
            defaults={
                'source_type': signal['source_type'],
                'source_url': signal['source_url'],
                'title': signal['title'],
                'summary': signal['summary'],
                'published_at': signal['published_at'],
                'impact_level': signal['impact_level'],
                'tags': signal['tags'],
                'raw_payload': signal['raw_payload'],
            },
        )
        return created

    def _audit_run(self, started_at: datetime, signals: List[Dict[str, Any]]) -> None:
        payload = {
            'organization_id': self.organization_id,
            'signals_count': len(signals),
            'sources': sorted(list({s['source_name'] for s in signals})) if signals else [],
        }
        payload_str = json.dumps(payload, sort_keys=True)
        payload_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
        elapsed_ms = max((datetime.utcnow() - started_at).total_seconds() * 1000, 0)

        AIAuditLog.objects.create(
            model_name='external_context_pipeline',
            model_version='1.0',
            input_hash=payload_hash,
            output_hash=payload_hash,
            inference_time_ms=elapsed_ms,
            confidence_score=0.8 if signals else 0.4,
            user_id=f'org:{self.organization_id}',
            compliance_flags={
                'traceable': True,
                'sources_whitelisted': True,
                'signals_detected': len(signals),
            },
        )
