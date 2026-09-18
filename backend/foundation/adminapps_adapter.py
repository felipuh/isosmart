"""Transport-free adapter boundary for a future authenticated AdminApps ingress."""

from typing import Mapping, Protocol, Any

from .projection_contract import ProjectionEvent, validate_projection_event
from .projection_writer import ProjectionResult, ProjectionWriterService


class AdminAppsProjectionAdapter(Protocol):
    def translate(self, envelope: Mapping[str, Any]) -> ProjectionEvent: ...

    def receive(self, envelope: Mapping[str, Any]) -> ProjectionResult: ...


class ContractOnlyAdminAppsAdapter:
    """Phase 2 implementation: validation + DTO translation, with no transport."""

    def __init__(self, writer: ProjectionWriterService | None = None):
        self.writer = writer or ProjectionWriterService()

    def translate(self, envelope: Mapping[str, Any]) -> ProjectionEvent:
        return validate_projection_event(envelope)

    def receive(self, envelope: Mapping[str, Any]) -> ProjectionResult:
        return self.writer.apply(self.translate(envelope))
