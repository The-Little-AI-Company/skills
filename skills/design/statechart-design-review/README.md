# Statechart design and review

A reusable agent skill for designing and reviewing complex event-driven lifecycles. It turns requirements into an explicit behavioral model, maps that model to an implementation, and derives traces and tests.

Made by The Little AI Company. Grounded in David Harel's 1987 statecharts paper, with modern reliability advice clearly separated from the paper's semantics.

## What it helps with

- Events, guards, actions, and activities that continue over time
- Nested states, orthogonal regions, and shallow or deep history
- State versus application data and context
- Event ordering, overlapping guards, cancellation, retries, and recovery
- Invariants, concrete counterexample traces, and model-derived tests
- Differences between a conceptual model, a runtime's semantics, and a diagram renderer

Statecharts are not inherently deterministic. The skill requires an explicit execution contract before making that claim. It does not automatically rewrite applications or install a state-machine library.

## Use the skill

This skill lives at `skills/design/statechart-design-review` in [The Little AI Company skills collection](../../../README.md). Give your agent this directory's `SKILL.md` and ask it to follow the referenced files.

For an agent that supports folder-based skills, copy this directory into its documented skill location as `statechart-design-review`. Follow your agent's current installation documentation. Keep the directory's full contents together, including `references/`, `scripts/`, `examples/`, and `tests/`.

For an existing project, use a prompt such as:

> Use Statechart Design and Review to inspect our document export lifecycle. Users can edit while an export runs, go offline, cancel, and retry. Identify stale-result and publication risks, propose a state model, and derive tests. Do not change application code yet.

For a focused review:

> Use Statechart Design and Review to check this controller's shallow-history restoration, parent/child transition conflicts, and shared writes across parallel regions. Give minimal counterexample traces and distinguish verified defects from missing semantic decisions.

No service, API key, or network access is required by the bundled code. Python 3.10 or newer is required for the examples and tests. An agent may need to consult current official documentation when targeting a particular runtime.

## Files

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Procedural design, implementation-mapping, and review workflow |
| `references/harel-foundations.md` | Page-specific source map and semantic boundaries |
| `references/execution-review.md` | Execution contract, recovery guidance, and inventory format |
| `references/examples.md` | Original worked lifecycle examples and review obligations |
| `scripts/check_inventory.py` | Structural JSON inventory linter |
| `examples/minimal-inventory.json` | Small valid input for the linter |
| `tests/test_inventory.py` | Structural linter regression tests |
| `tests/export_safety_test.py` | Reduced synthetic export safety model and bounded exploration |

## Run the checks

From this skill's directory:

```sh
python3 scripts/check_inventory.py examples/minimal-inventory.json
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tests/export_safety_test.py
```

The linter checks declared references, identifiers, hierarchy, and composite-state structure. It warns when same-source/same-event transitions require guard and priority review. It does not interpret statecharts, prove guard exclusivity, check history semantics, or establish determinism.

The export example runs 14 named safety traces and explores 262,144 sequences of six events over a fixed eight-event alphabet. It checks its displayed-revision and revocation invariant. It is a teaching model, not production code or proof of a full export system. It excludes persistence, outbox durability, networking, restart, real timing, runtime priority, and liveness.

Failure and pending notifications do not carry generation IDs in this reduced model. Stale notifications of those types can affect a later operation, so the example does not establish correct handling of every stale event. Production implementations must correlate all asynchronous results as described in [execution and review](references/execution-review.md).

## Source and attribution

David Harel, [Statecharts: A Visual Formalism for Complex Systems](https://www.state-machine.com/doc/Harel87.pdf), *Science of Computer Programming* 8 (1987), pp. 231–274.

The skill contains original paraphrases, procedural guidance, and synthetic examples. It does not include the paper PDF, scanned figures, or reproduced article text. Page references help readers check the source. Modern mechanisms such as idempotency keys and generation IDs are engineering recommendations, not claims attributed to that paper.

Mermaid or another renderer can help communicate a model. Rendering a diagram alone does not define executable event ordering, guard snapshots, transition priority, or activity lifetime.

## License

MIT. See [LICENSE](LICENSE). The license applies to this repository's authored material, not to the linked paper or other third-party sources.
