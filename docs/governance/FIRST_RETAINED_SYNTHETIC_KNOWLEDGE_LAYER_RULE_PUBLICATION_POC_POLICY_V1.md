# First Retained Synthetic KnowledgeLayerRule Publication POC Policy v1

- Policy ID: `first-retained-synthetic-klr-publication-poc-policy/v1`
- Version: `v1`
- Date: 2026-09-03 (`America/Costa_Rica`)
- Status: **APPROVED FOR EXACTLY ONE EPHEMERAL SYNTHETIC PUBLICATION POC**
- Nature: ISO Smart Product Policy; non-normative; test-only; non-production

## Exact authorization

This policy authorizes one native publication transaction for retained
candidate `01a0682b-dfc8-7b49-a601-f9bda29a70a5`, lineage and predecessor
`da72872a-3f3c-5fcd-86f7-0ed33e453522`, version `sN+1`, full material hash
`caa24592b509334af4cd60fd7d3f3c43989d864d3f1c6e6d0d3bf83a81871f81`,
semantic fingerprint
`8465956c1daf27a9838bc1bfb468af3f518ae255b4662b2df40e7b8648516192`
and lifecycle hash
`0adfd8075cc720140c6e1f0393d286799edac8f352efd9f1969816be83c51e52`.

The transaction is authorized only after exact offline verification of source
manifest `cf92c267439f94f302e67888665dbf99392592341a808f5fc00f4c32ef23dc24`,
creation manifest `9ab80f4b0208e7dac971a0759df0bdb5c28392aa423ae11cbc0d483abb739a75`,
creation disposition `964b632537323764de35f9132bf7e63966df29dc89d70c1166e432d4e6436b5c`,
the complete retained governance graph and Receipt
`01a0682b-dfa3-779c-89cd-1814e9209527`.

## Required controls

Publication requires a fresh, active, MFA-verified, server-resolved AdminApps
global publication authority; exact actor-level separation of duties; an
append-only capability decision; the singleton current leaf; exact retained
import comparison; claim/idempotency binding; immediate precommit authority,
capability and target revalidation; and an atomic Publication, compatibility
status, event, outbox and immutable-audit graph.

The retained synthetic root's compatibility `status=published` is not native
publication evidence and must never receive a synthesized Publication record.

## Explicit exclusions

This policy does not authorize Activation, RuntimeAdoption, runtime selection
or cutover, another candidate/lineage/operation, generic retained import,
production/staging/shared databases, deployment, normative or licensed
content, ModelPolicy or AgentDefinition mutation, automatic/cross-tenant
learning, compensation, external providers, notifications, DNS or any external
business effect.

Publication success means only that the exact synthetic revision completed
publication governance. It does not mean activated, adopted, deployed,
runtime-effective, learning-successful or normatively certified.

## Retention and teardown

Before teardown, the complete live publication graph must be exported to an
immutable content-addressed manifest. The database, scoped roles, container,
volume, temporary files and secrets must then be destroyed and their absence
verified. A separate append-only disposition must bind teardown and a
repository-only release-state query. Missing evidence is not reconstructed.

