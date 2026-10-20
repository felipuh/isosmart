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
        parser.add_argument("--recover-exhausted-outbox-id")
        parser.add_argument("--reason")

    def handle(self, *args, **options):
        try:
            identity = TrustedTenantIdentity(
                subject="ai-usage-delivery-worker", tenant_id=UUID(options["tenant_id"])
            )
        except (TypeError, ValueError) as exc:
            raise CommandError("--tenant-id must be a UUID") from exc
        dispatcher = AIUsageDelivery()
        try:
            recovery_id = options["recover_exhausted_outbox_id"]
            if recovery_id:
                if not options["reason"]:
                    raise CommandError("--reason is required with --recover-exhausted-outbox-id")
                recovered = dispatcher.recover_exhausted(
                    identity=identity,
                    outbox_id=UUID(recovery_id),
                    actor_id=options["worker_id"],
                    trace_id=uuid4(),
                    reason=options["reason"],
                )
                self.stdout.write(f"AI usage delivery recovery scheduled outbox={recovered}")
                return
            result = dispatcher.deliver_next(
                identity=identity, worker_id=options["worker_id"], trace_id=uuid4()
            )
        except (RuntimeError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        if result is None:
            self.stdout.write("no eligible AI usage delivery")
            return
        self.stdout.write(f"AI usage delivery {result.state} outbox={result.outbox_id}")
