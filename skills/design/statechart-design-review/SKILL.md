---
name: statechart-design-review
description: Design, explain, implement, and review complex event-driven lifecycles with hierarchical statecharts grounded in Harel (1987). Use for event/guard/action models, nested states, orthogonal regions, history, cancellation, recovery, determinism, state versus context, lifecycle diagrams, race analysis, and model-derived tests. Apply to the requested project scope without automatically rewriting an application or installing a state-machine library.
---

# Statechart Design and Review

Turn lifecycle requirements into an explicit behavioral model, map it to the chosen implementation, and verify the mapping. Scale the output to the question; a small lifecycle can use a transition table without an elaborate diagram.

## Establish the contract

1. Read the requested artifact and project conventions. Identify the system boundary, event producers, observable outcomes, current defects, and implementation/runtime/version if one exists. Preserve unrelated behavior. Ask only about missing choices that materially affect correctness; label other assumptions.
2. Separate facts, proposed design choices, and unresolved requirements. Define invariants before proposing transitions, such as “a canceled job cannot publish a successful result.” Specify which observations can establish each invariant.
3. Read [Harel foundations](references/harel-foundations.md) for source claims. Read [execution and review](references/execution-review.md) for ordering, concurrency, implementation, or recovery work. Use [worked examples](references/examples.md) to structure a model and tests without copying their domain assumptions.

## Model behavior

4. Inventory events, payloads, guards, actions, and longer-running work. Give events occurrence-oriented names and guards side-effect-free predicates. Separate intent, acknowledgment, success, failure, timeout, cancellation request, and cancellation confirmation when they differ operationally.
5. Choose states by differences in permitted events, obligations, or behavior. Keep unbounded values, identities, counts, and timestamps in context. Avoid one Boolean per lifecycle phase. Avoid forcing unrelated data into states or hiding a meaningful lifecycle in context flags.
6. Introduce XOR nesting for mutually exclusive substates and shared transitions. Name default entry for every composite state. Introduce orthogonal regions only for genuinely simultaneous aspects; list the active configuration across regions. Logical concurrency alone creates no threads or distributed consistency guarantees.
7. For every transition record source, trigger, guard, target, actions, and effect on active descendants/other regions. Define entry, exit, self-transition, internal transition, completion, and no-handler behavior only as supported by the selected semantics. Distinguish transition actions from activities that continue over time.
8. Use history only when resuming prior control configuration is required. Specify shallow or deep restoration, first-entry fallback, validity conditions, reset rules, and what happens to activities. Treat restoring context, persistence across restart, and recovering external work as separate contracts.

## Resolve ambiguity before implementation

9. Write an execution profile: event admission and queue order; guard evaluation snapshot; conflicting-transition selection and tie handling; parent/child priority; compatible transitions across regions; action/exit/entry order; generated-event scheduling; completion processing; and stabilization limits. Do not claim that statecharts are inherently deterministic or that Harel specifies universal child-first priority.
10. Exercise simultaneous events, overlapping guards, cross-region dependencies, reentrancy, repeated/late events, stale asynchronous completions, timeout races, cancellation, and interrupted recovery. If multiple outcomes remain permitted, either preserve and label that nondeterminism or obtain a product decision. Never conceal it behind diagram layout or transition-list order.
11. Decide the authority for irreversible effects. Specify idempotency, correlation/generation IDs, cancellation ownership, retries, compensation, and durable reconciliation where needed. An in-memory transition cannot undo an external action. Keep guards pure and avoid dependent cross-region writes whose result changes with iteration order.

## Map and verify

12. Map states, context, events, effects, and lifecycle ownership to existing code or pseudocode. For a real runtime, consult its current official documentation and pin/version the semantics used. Record where it differs from the conceptual model. Do not install libraries, rewrite architecture, or touch production merely because the model suggests a change.
13. Produce the smallest useful package: assumptions and open decisions; state/event/context inventory; transition table; execution profile; invariants; representative traces and tests; implementation mapping and unresolved risks. Add a diagram when useful, with a legend and explicit unsupported features. A rendered picture is not proof of executable semantics.
14. Derive tests from invariants and transitions: default entry, nested exit, regional coordination, first and subsequent history entry, history reset, guard boundaries/overlap, unhandled events, duplicate and stale events, cancellation races, recovery, and eventual progress under stated fairness assumptions. Show initial configuration/context, input sequence, expected configurations/effects, and forbidden outcomes. State which tests actually ran and which are proposed.
15. Optionally encode a compact review inventory using the format in [execution and review](references/execution-review.md) and run `python3 scripts/check_inventory.py inventory.json`. Treat this as deterministic structural lint only: it does not execute statecharts, prove guard exclusivity, or validate runtime semantics. Use runtime integration tests or a suitable formal model checker for stronger evidence.

## Review output

Lead with consequential findings and concrete counterexample traces. For each finding give the artifact location, violated requirement or invariant, minimal reproducing trace, impact, and targeted remedy. Separate verified defects from semantic ambiguities and optional improvements. End with remaining decisions and precise validation limits. Cite source pages when explaining historical concepts; label modern engineering guidance and runtime-specific choices separately.
