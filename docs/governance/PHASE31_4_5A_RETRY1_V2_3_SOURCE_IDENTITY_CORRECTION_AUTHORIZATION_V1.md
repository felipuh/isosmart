# Phase 31.4.5A Retry 1 V2.3 source-identity correction authorization

Status: narrowly authorized offline contract successor; no execution authority.

V2.2 remains immutable historical evidence. Before producer implementation or
database creation, complete source reading proved that its two declared
AgentRun DomainEvent rows used protocol identities and payloads the selected
native producer cannot emit. V2.3 supersedes V2.2 operationally only for the
documented AgentRun DomainEvent, linked Outbox, and same-operation immutable
Audit field bindings.

This authorization separates synthetic business/test classification from the
native protocol. The fixture remains nonproduction, non-normative, synthetic,
and test-only in its governance envelope. Its persisted event type, aggregate
type, aggregate identity relationship, source, payload, Outbox creation state,
and Audit linkage follow `AgentRunCommandService._event_outbox_audit` exactly.

The enumerated ADR-0018 identity-only fixture exceptions continue to cover the
fixed AgentRun, DomainEvent, and TransactionalOutbox identities. No exception
is expanded. Immutable Audit identity remains native UUIDv7 output.

The corrected stream is `(agent_run, AgentRun.id)`. Parent identity serializes
creation before start-event allocation; completion and failure lock that same
parent before allocation. No new lock, producer, transaction ownership rule,
security rule, architecture rule, migration, lifecycle execution, or
RuntimeAdoption is authorized. Allocation remains native; retention may use
the already-authorized read-only persisted reread.

No PostgreSQL instance, database, role, container, migration, event write,
Application, Publication, Activation, RuntimeAdoption, resolver, external
system, production, or staging effect is authorized by this document.
