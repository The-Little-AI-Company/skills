# Execution and review

## Contents
- Execution profile
- Implementation and recovery
- Trace review
- Inventory lint format

## Execution profile

Answer each item, or mark it unresolved before promising determinism:

| Decision | Questions |
| --- | --- |
| Event admission | Which actor owns the model? How are concurrent producers serialized? What determines ties? Which events can be dropped, deferred, coalesced, or rejected? |
| Enabledness | Which configuration and context snapshot do guards see? Can guards call nondeterministic functions? |
| Conflict | Can two transitions exit overlapping states? Do descendants take priority? Are overlapping guards rejected, ordered, or nondeterministically selected? |
| Regional execution | Which enabled transitions can fire together? Can one region read another’s pre-step or post-step state? Who owns shared writes? |
| Effects | In which order do exit actions, edge actions, context writes, and entry actions occur? Are external effects recorded before dispatch? |
| Generated events | Do internal events run immediately, in the next microstep, or through a queue? When are external events admitted again? |
| Termination | Can eventless transitions or event generation cycle? What guarantees stabilization? What happens if a processing limit is reached? |
| Lifetime | Which activities start/stop on entry/exit? Is cancellation advisory? How are stale results rejected? |
| Restart | What is persisted, what is reconstructed, and what must be reconciled against an external authority? |

For a conceptual proposal, choose a coherent profile and label it a proposal. For existing code, discover rather than assume the profile. A deterministic transition function still depends on a defined input order and controlled external observations. A reproducible test schedule does not prove all schedules safe.

## Implementation and recovery

- Map the model to actual handlers, reducers, effect workers, storage, and event sources. Keep one clear lifecycle owner. Identify when the implementation skips modeled states or accepts events forbidden by the model.
- Tie each asynchronous result to an operation ID and, where necessary, a generation. Define what happens when cancellation and completion both arrive. Distinguish suppressing a stale UI update from undoing already committed external work.
- Bound retries with policy in context; model retry-waiting as a state if it changes accepted events or obligations. Include retry exhaustion, backoff interruption, and manual recovery.
- For durable workflows, specify the write/effect ordering, deduplication scope, recovery source of truth, and compensation. Avoid unsupported exactly-once promises.
- For history, separate remembered control configuration, persisted domain context, and live resources. Re-entering an old state can restart activities unless the runtime says otherwise. Decide whether the history remains valid after disconnect, logout, version migration, or changed external state.
- Label liveness assumptions: a service eventually responds, a retry is eventually scheduled, a user eventually acts. An invariant checks safety; a progress claim needs these additional assumptions.

## Trace review

Represent a step as:

`before configuration + relevant context → input/guard outcomes → selected transitions → actions/effects → after configuration + context`

For each proposed bug, supply a short concrete trace rather than a generic “race condition” label. Include both event orderings if their outcomes differ. Check state reachability and impossible/dead-end configurations. Review transition coverage separately from condition/guard and interaction coverage.

A diagram is a communication view. Pair it with stable state and transition IDs and a legend for XOR, orthogonality, history depth, and omitted behavior. Where the renderer lacks a construct, use an annotated conceptual node and retain the full semantics in the transition contract.

## Inventory lint format

The bundled `scripts/check_inventory.py` accepts JSON with this deliberately limited shape:

```json
{
  "states": [
    {"id": "Root", "kind": "compound", "initial": "Idle"},
    {"id": "Idle", "kind": "atomic", "parent": "Root"},
    {"id": "Busy", "kind": "atomic", "parent": "Root"}
  ],
  "events": ["START", "DONE"],
  "transitions": [
    {"id": "start", "source": "Idle", "event": "START", "target": "Busy"},
    {"id": "done", "source": "Busy", "event": "DONE", "target": "Idle"}
  ]
}
```

Use globally unique state IDs. Use kinds `atomic`, `compound`, `parallel`, or `final`. A compound state requires a direct-child initial target; a parallel state has child regions (normally compound states), with no single initial target. Exactly one root is required. Set event to null for an eventless transition, and target to null for a targetless transition. Optional guard is a descriptive string; the tool never evaluates it. Put history, actions, context, scheduling, and full semantics in the review contract outside this compact inventory.

Run `python3 scripts/check_inventory.py path/to/inventory.json`. Exit 0 means structural checks passed, exit 1 means invalid structure or input. The script checks duplicate IDs, declared references, parent cycles, root count, valid kinds, and compound/parallel child structure. It warns about same-source/same-event transition groups requiring guard/priority review. It does not execute a machine, check reachability, validate history, resolve ancestor/descendant conflicts, or prove safety/determinism. Never present its passing result as any of those stronger claims.
