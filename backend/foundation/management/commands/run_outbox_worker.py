"""Operate the existing transactional-outbox dispatcher without external delivery."""

import logging
import os
import signal
import time
from uuid import UUID, uuid4

from django.core.management.base import BaseCommand, CommandError

from foundation.eventing import FoundationCompletionDelivery
from foundation.tenant_context import TrustedTenantIdentity

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the isolated Foundation transactional-outbox worker for one trusted tenant.'

    def add_arguments(self, parser):
        parser.add_argument('--tenant-id', required=True)
        parser.add_argument('--once', action='store_true')
        parser.add_argument('--poll-seconds', type=float, default=2.0)
        parser.add_argument('--worker-id', default='foundation-outbox-worker')

    def handle(self, *args, **options):
        configured_tenant = os.getenv('WORKER_TENANT_ID')
        if os.getenv('INTERNAL_OUTBOX_WORKER_ENABLED') != 'True' or not configured_tenant:
            raise CommandError('internal outbox worker is not enabled by deployment configuration')
        if options['tenant_id'] != configured_tenant:
            raise CommandError('--tenant-id must match deployment-configured WORKER_TENANT_ID')
        try:
            identity = TrustedTenantIdentity(
                subject='internal-outbox-worker', tenant_id=UUID(options['tenant_id'])
            )
        except (TypeError, ValueError) as exc:
            raise CommandError('--tenant-id must be a UUID') from exc
        if options['poll_seconds'] <= 0:
            raise CommandError('--poll-seconds must be positive')

        stopping = False

        def stop(*_):
            nonlocal stopping
            stopping = True
            logger.info('outbox_worker_shutdown_requested tenant=%s', identity.tenant_id)

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        self.stdout.write('outbox worker started (local consumer only; no external delivery)')
        while not stopping:
            try:
                result = FoundationCompletionDelivery().deliver_next(
                    identity=identity, worker_id=options['worker_id'], trace_id=uuid4(),
                )
                if result is not None:
                    logger.info('outbox_delivery_processed tenant=%s result=%s', identity.tenant_id, result.kind.value)
                elif options['once']:
                    break
            except Exception:
                # The delivery service records a retryable FAILED transition.
                logger.exception('outbox_delivery_failed tenant=%s', identity.tenant_id)
                if options['once']:
                    raise
            if not options['once'] and not stopping:
                time.sleep(options['poll_seconds'])
        self.stdout.write('outbox worker stopped cleanly')
