"""Run the explicitly enabled AdminApps AI-usage dispatcher for one tenant."""

from uuid import UUID, uuid4

from django.core.management.base import BaseCommand, CommandError

from foundation.ai_usage_delivery import AIUsageDelivery
from foundation.tenant_context import TrustedTenantIdentity


class Command(BaseCommand):
    help = "Deliver pending AI-usage records through the configured AdminApps boundary."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", required=True)
        parser.add_argument("--worker-id", default="ai-usage-delivery-worker")
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        try:
            identity = TrustedTenantIdentity(
                subject="ai-usage-delivery-worker", tenant_id=UUID(options["tenant_id"])
            )
        except (TypeError, ValueError) as exc:
            raise CommandError("--tenant-id must be a UUID") from exc
        dispatcher = AIUsageDelivery()
        try:
            result = dispatcher.deliver_next(
                identity=identity, worker_id=options["worker_id"], trace_id=uuid4()
            )
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc
        if result is None:
            self.stdout.write("no eligible AI usage delivery")
            return
        self.stdout.write(f"AI usage delivery {result.state} outbox={result.outbox_id}")
