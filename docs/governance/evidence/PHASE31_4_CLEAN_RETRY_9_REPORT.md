# Phase 31.4 V2.5 Clean Retry 9 — live report

## Verdict and retry ID

**NOT_PROMOTED** — Phase 31.4 V2.5 Clean Retry 9 (`CLEAN_RETRY_9`, `LIVE_NATIVE_EXECUTION`). The full ISO Smart migration chain failed at `foundation.0001_foundation_tenant_projection`. No V2.5 phase was executed or marked PASS.

## Pre-live gates and historical closure

Stage A, Stage EXT, runtime composition, 16/16 native operation bindings, 33/33 native phase composition, 509/509 capture producer coverage, and pre-live P0=0/P1=0 passed. Retry 8's original `teardown=PENDING` and historical teardown `false` remain unchanged. Its present resource hygiene closure `CLOSED_BY_EXHAUSTIVE_ABSENCE_EVIDENCE` was accepted.

## V2.4 SHA

`a102d278bf2e5ca6e9b8bf282f5402a54f52d4690beed2ecbed5145c56539387` — PASS against the required digest. V2.4 was not changed. V2.5 contract SHA-256: `12f048fcada1a36d02d26ff0e4efaa247d04687161c7d1dcb6cbc196ae69001b`.

## Runtime resources and migrations

Two fresh isolated PostgreSQL 18.6 containers were created: `phase31_4_retry9_adminapps` and `phase31_4_retry9_isosmart`. Their exact image digest, IDs, volumes, networks, ports and lifecycle are in the resource manifest. AdminApps applied 61 migrations normally. ISO Smart applied 49 migrations, then failed at `foundation.0001`: `foundation runtime roles were not supplied by cluster bootstrap`. No migrations were faked and no schema patch was applied. The migration gate failed.

## AdminApps upstream, ISO Smart projection, QMS Organization, Process and Opportunity

Not executed after the mandatory migration failure. No fresh tenant or upstream product identity was created.

## Native phases and captures

0/33 executed, 0 passed, 0 failed. Captures: 509 expected, 0 resolved, 509 unresolved because execution stopped before Phase 1.

## Authority/A3, ActionPlan, controlled revision, references/invariants

Not evaluated live. No authorization, ActionPlan, revision, reference or invariant result is claimed.

## Transactions and event/outbox/audit

Only normal migration transactions ran. Native domain transactions and persisted event/outbox/audit consistency were not evaluated.

## Graph and exact comparison

0/118 live members and 0/1664 live fields materialized. Exact comparison and mismatch count: not computed. No resolved graph hash exists.

## P0/P1 and blocker

Current P0=0, P1=1. New blocker: `P1-RETRY9-ISOSMART-MIGRATION-BOOTSTRAP-ROLES-MISSING`. The required remediation is to bootstrap the isolated PostgreSQL roles and connection settings before the complete migration chain in a new clean retry.

## Retry 9 teardown and final promotion decision

**PASS.** Scoped containers, their databases, volumes and dedicated networks were removed; the final Podman inventory showed no Retry 9 resource. Promotion: **NOT_PROMOTED**.

## Evidence artifacts

See `PHASE31_4_CLEAN_RETRY_9_SHA256.json` for paths and SHA-256 values. The allocation, pre-live gate, resource manifest, both migration logs, migration verdict, blocker, and closure are retained.
