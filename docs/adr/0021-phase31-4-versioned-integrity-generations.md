# ADR-0021: Versioned Phase 31.4 integrity generations

- Status: Accepted
- Date: 2026-09-21

## Context

The V2.4 validators froze migrations `0001` through `0023` and their hashes, but also inspected repository HEAD and rejected any `0024_*` file. That converted historical immutability into repository immobility. The approved Stage EXT remediation later introduced `0024_adminapps_ingress_receipt.py`, so 22 offline tests failed without any V2.4 byte changing. A separate V2.4-era protected-source hash for `backend/backend/settings.py` predates the Retry 10 `DB_SESSION_OPTIONS` bootstrap remediation approved by ADR-0020.

## Decision

Integrity protection is generation-scoped:

- V2.4 historical integrity requires the exact V2.4 contract SHA-256 and the exact names, order, and bytes of migrations `0001` through `0023`. It does not make claims about successor filenames.
- Historical manifests retain their original source hashes as provenance and are never rewritten to current hashes.
- V2.5 current operational integrity separately protects the approved current migration set and material identity, Stage EXT, PostgreSQL bootstrap, runtime composition, authority, native execution, and binding sources.
- A changed historical protected source is accepted as a successor only when the current generation records both its current hash and the predecessor hash and cites existing approval evidence.

Migration `0024` remains outside the V2.4 manifest and inside the V2.5 current manifest. The old settings hash remains in historical evidence; the current settings hash is linked to it through ADR-0020 and Retry 10 blocker closure evidence.

## Consequences

Changing a frozen V2.4 artifact still fails. Adding an approved successor migration does not alter V2.4 history. Changing a current protected source without a separately reviewed manifest update fails closed. Historical and current manifests use different schemas and cannot substitute for each other.
