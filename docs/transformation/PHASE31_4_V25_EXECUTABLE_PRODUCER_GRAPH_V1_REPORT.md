# Phase 31.4 V2.5 Executable Producer Graph V1

## Verdict

Offline executable graph remediation is complete. The fail-closed gate reports `EXECUTABLE_PRODUCER_GRAPH = PASS`.

## Broken graph edges

Six historical edges were incomplete in the Retry 14 registry and are recorded as `REMEDIATED` in the machine-readable artifact:

1. Opportunity -> AgentDefinition (`Opportunity.id`)
2. AgentDefinition -> AgentRun (`AgentDefinition.id`)
3. AgentRun -> Recommendation (`AgentRun.id`)
4. Recommendation -> AgentDecision (`Recommendation.id`)
5. AgentDecision -> ActionPlan (`AgentDecision.id`)
6. ActionPlan -> Authorization (`ActionPlan.id`)

The current graph has zero invalid ordering edges and zero missing producers. No unrelated phase resolves to Opportunity execution.

## Agent chain topology

`Opportunity -> AgentDefinition -> AgentRun -> Recommendation -> AgentDecision -> ActionPlan -> Authorization`

The order is backed by `RiskOpportunityObjectiveCommandService.create_opportunity`, `AgentCatalogCommandService.create_agent_definition`, `AgentRunCommandService.start_agent_run`, `AgentRunCommandService.complete_agent_run_with_recommendation`, `AgentDecisionCommandService.record_agent_decision`, `ActionPreparationService.prepare_action_plan`, and `ExecutionAuthorizationService.evaluate_execution_authorization`.

## Recommendation semantics

Recommendation is a standalone persisted `Recommendation` aggregate. It is created by `AgentRunCommandService.complete_agent_run_with_recommendation` through `RecommendationCommandService._create_recommendation_in_current_transaction` and linked by `AgentRunRecommendation`. It is not an embedded Decision payload or a deterministic fallback.

## Authorization semantics

ExecutionAuthorization is produced by `ExecutionAuthorizationService.evaluate_execution_authorization` after ActionPlan and its dry run. The native service loads the exact ActionPlan, AgentDecision, AgentRun, ModelPolicy, and effective approval before authorizing.

## 33-phase reachability

Expected/reachable: `33/33`. The deterministic topological order is persisted in `PHASE31_4_V25_EXECUTABLE_PRODUCER_GRAPH_V1.json`.

## Capture reachability

Expected/reachable: `565/565`. Every `CAPTURE_NATIVE_OUTPUT` has a source-backed producer phase, selector, and output contract.

## Pre-execution assertion

`PASS` for the executable producer graph. The assertion runs before `run_clean_retry` executes any phase.

## Tests

The five new executable-graph tests pass. The existing offline suites require the repository's `backend/.venv` with Django 4.2.22; the alternate `.venv312` is Django 6.0.6 and is incompatible. Migration 0024 integrity is closed: the semantic validator verifies its presence and protected V2.5 hash, and the Retry5 operational manifest test passes. It still reports the two intentionally frozen V2.4 semantic contradictions below; resolving either would require changing V2.4 material.

## P0/P1

Graph remediation: P0=0 and executable-graph P1=0. Overall offline promotion remains blocked by the two frozen V2.4 semantic P1s.

## Retry 14 blocker

`P1-RETRY14-V25-EXECUTABLE-PRODUCER-GRAPH-INCOMPLETE`: `CODE_REMEDIATED / LIVE_CLOSURE_PENDING`.

## Retry 12 blocker

`P1-RETRY12-V25-ACTIONPLAN-AGENT-DECISION-LIVE-BINDING-MISSING`: `OPEN_NOT_REACHED_RETRY14`.

## Retry 15

`NOT_AUTHORIZED`. No live resources were created and no Retry 15 was allocated.

## Independent semantic blockers

- `P1-FROZEN-ACTION-PLAN-PRECONDITIONS`: the frozen V2.4 ActionPlan value is text, while the native service requires object preconditions.
- `P1-FROZEN-CONTROLLED-OPPORTUNITY-GOVERNANCE`: the frozen V2.4 A0/opportunity material contradicts the unchanged A3 governance SQL guard.

These remain outside the V2.5 graph remediation and are not modified here.