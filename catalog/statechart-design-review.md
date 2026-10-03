# Statechart Design and Review

Id: statechart-design-review. Category: Design review. Status: Published source.

## What

This skill helps an agent review the behavior of a system as a statechart. It makes the review explicit. The agent lists events, guards and actions. It separates state from data. It states invariants, builds a transition table, writes counterexample traces and proposes tests.

A Mermaid diagram shows structure only. It does not execute semantics, so a diagram alone does not prove behavior.

The skill is at skills/design/statechart-design-review. Its frontmatter name is statechart-design-review. The README, references, scripts and tests are part of the skill.

## When to use

Use it for complex event-driven lifecycles. These have nesting, concurrency, cancellation, recovery or stale completions.

Do not use it for trivial flags that have no lifecycle complexity.

## Installation

Copy the whole folder skills/design/statechart-design-review into your agent's existing skill directory. Do not copy the collection root as one skill. Do not install dependencies.

The existing skills command line tool may support this command:

```
skills add The-Little-AI-Company/skills --skill statechart-design-review
```

No new tool install is needed. The manual folder copy is the documented path.

The bundled tools need Python 3.10 or later and the standard library only. Run these commands from within the skill folder:

```
python scripts/check_inventory.py examples/minimal-inventory.json
python -m unittest discover -s tests -p "test_*.py" -v
python tests/export_safety_test.py
```

## Example

This is a synthetic teaching scenario. It is not a verified defect in any real product.

An export is cancelled before a late completion arrives. Ask the agent for three things. First, the forbidden trace in which the late completion publishes the cancelled export. Second, the guard that blocks that publication. Third, a regression test that replays the trace and expects no publication.

## Limits

- The structural inventory linter checks structure. It is not proof of behavior or determinism.
- The synthetic model excludes persistence, a durable outbox, networks, restart, real timing, runtime priority and liveness.
- Some failure and pending events lack generation IDs.
- There is no claim that every stale event is safe.
- No agent effectiveness has been measured.
- No benefit to any real project has been measured.

## Evaluations

Recorded in the published README: 14 named safety traces, and 262144 sequences of six events drawn from an eight-event alphabet. These are bounded synthetic checks.

This review copy passed 5 inventory tests, the minimal inventory check, 14 named safety traces and 262144 length-six sequences on 2026-10-03.

There is no with-skill and without-skill comparison.

## Sources

- Published repository and SKILL.md: https://github.com/The-Little-AI-Company/skills
- The skill's own README in skills/design/statechart-design-review
- David Harel, Statecharts: A Visual Formalism for Complex Systems, 1987: https://www.state-machine.com/doc/Harel87.pdf

## Version

Source commit 06d9ea5c4ed5e6d4856c5838fbb9b2bd80c4eea8, short form 06d9ea5. This is a commit reference. It is not a semantic release number.

## License

MIT for the authored text and code. Cited sources keep their own rights.
