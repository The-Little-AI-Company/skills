# Invent through mechanisms and experiments

## Contents

- Operating stance
- Find the assumption worth breaking
- Generate structurally different ideas
- Search for the closest existing work
- Select and test
- Design for an LLM programmer
- Explore live repair
- Teams, interface, and output

## Operating stance

Use this workflow for requests for original ideas, unusual interactions, new capabilities, product invention, or alternative computing architectures. Follow the requested mode: **invent** produces researched candidates and experiments; **build** implements the selected authorized experiment. Do not turn a request for ideas into a deployment or a full platform rewrite.

Aim for an observable change in what someone can do. Prefer an interesting mechanism with a useful consequence over a familiar app with a new name. Preserve one surprising candidate while developing practical candidates. Resist the default of another chat panel over an API.

Treat provocative claims as hypotheses. The supplied inspiration questions rebuild/restart/deploy conventions, revisits actors and live images, and asks what changes when LLMs program. It does not establish that venture capital caused those conventions, that all languages are equivalent, that Go cannot succeed, or that any successor will win. Do not build those claims into the agent's worldview.

A language choice is an implementation option. Identify which operation, representation, state boundary, feedback loop, or distribution model must change before picking a language. Existing runtimes may be the cheapest way to test a new interaction.

## Find the assumption worth breaking

1. Identify a concrete person, recurring job, current workaround, and observed frustration. Separate reported facts from inferred needs. Use the user's constraints, including budget, device, connectivity, energy, and deployment authority.
2. Trace the actual loop: intent → representation → edit → check → activation → observation → correction. Measure or label unknown the time, attention, resets, context, and cost at each step.
3. List assumptions inherited from tools, teams, distribution, or human editing habits. Ask which protect a real invariant and which are conventions.
4. Choose one assumption to relax while naming the invariant that must survive. For example: replace whole-process restart while preserving accepted work and state identity.
5. State a design question: “If an agent could inspect and modify this unit directly, what useful interaction becomes possible?” Keep the answer open.

Examples of productive questions: Can only the affected object or computation change? Can the environment return a counterexample instead of a stack trace? Can a user demonstrate the desired behavior and compare it against a retained state? Can an agent operate a structured intermediate representation while a human sees a clear semantic diff? Can a local workspace carry useful computation through a network outage?

## Generate structurally different ideas

For an open-ended ideation request, start with about 12 concise candidates across at least four mechanisms; adapt to the user's requested count. Combine one real friction, one mechanism, one changed assumption, and one visible payoff. Read [the prior-art lenses](invention-prior-art.md). Treat [the seed set](../assets/invention-seeds.json) as examples, not a fixed menu.

Vary meaningful dimensions:

| Dimension | Options to explore |
| --- | --- |
| Unit of change | File, function, actor behavior, state transition, dataflow node, document object |
| Programmer interface | Text patch, typed operation, example/counterexample, constrained graph transformation |
| Feedback | Compiler error, local state diff, replay trace, invariant violation, visible behavior |
| Activation | Rebuild/restart, staged hot replacement, snapshot branch, isolated worker swap |
| User interaction | Describe, demonstrate, directly manipulate, compare branches, repair selected object |
| Persistence | Source plus migrations, event history, state image, portable local project |

Include candidates in more than one product domain when the prompt is broad: creative tools, games, offline utilities, research, and developer workflows. The same primitive can produce very different experiences.

Write the mechanism before the name. Discard superficial variants and recombinations whose components do not interact. A candidate must change behavior, economics, reliability, or the interaction itself. Familiar branding, new model choice, or a language rewrite alone is insufficient.

## Search for the closest existing work

For the strongest candidates, search current products, open-source implementations, papers, and historical systems. Use primary sources for technical claims. Search the mechanism and user outcome, not only the invented product name. Look actively for work that would make your candidate redundant.

Record the closest predecessor, what it already does, the proposed difference, source/date, and uncertainty. Separate historical mechanism, current competing implementation, proposed combination, and experimentally demonstrated difference. If browsing is unavailable, mark novelty unverified and continue only with that label.

Use “a proposed difference from the inspected examples,” not “nobody has built this.” A few searches do not establish patent novelty or market uniqueness. If an existing tool solves the problem, recommend it or state the remaining gap precisely.

## Select and test

Compare a short list on user value, mechanism difference, visible demonstration, affordable implementation, reversibility, distribution/adoption effort, and the risk of being wrong. Use reasons and evidence confidence; numeric scores are optional planning aids, not measurements.

Keep a feasible candidate, a surprising candidate, and the strongest conventional baseline until a discriminating experiment resolves the choice. The baseline gets the same inputs, invariants, operating conditions, model/access, and reporting standards.

For each finalist, fill [the invention card](../assets/invention-card.template.json): claim, mechanism, prior art, counterargument, smallest specimen, comparison, success condition, failure condition, budget, and next action. Build the smallest specimen that can disprove the premise. Do not require a production dashboard before testing the central interaction.

Measure time from intent to verified changed behavior, successful corrections, state loss, stale outputs, number of model/tool round trips, token or monetary cost, human interventions, and recovery. Select metrics relevant to the claim. Preserve failed attempts; do not compare a tuned candidate with an intentionally weak baseline. Repeat representative cases within the authorized budget and report the sample size and limits. One appealing screen recording is not broad performance evidence.

Stop or revise if the mechanism adds more operational work than it removes, fails the invariant, reproduces an existing solution without a meaningful difference, or depends on unavailable resources. Save the failed hypothesis and what would change the decision. Do not force a positive conclusion.

## Design for an LLM programmer

Treat the LLM as an error-prone tool user with different strengths and costs from a human. Explore agent interfaces deliberately; keep them comprehensible and controllable by people.

- Expose stable object IDs, typed operations, bounded observations, explicit preconditions, affected dependencies, and reversible diffs.
- Return structured errors with the violated invariant and a minimal reproduction/counterexample where possible.
- Let an agent inspect state and trace a dependency without repeatedly dumping the entire project into context.
- Preserve readable source, export, audit history, manual override, and an explanation of what an operation changes.
- Benchmark typed operations or a small intermediate representation against ordinary text patches before claiming superiority. Structured syntax alone guarantees neither valid semantics nor model competence.
- Use deterministic validation outside the model. The model proposes; the runtime checks versions, scope, resource access, invariants, and authority.

These are design candidates, not proof that a new programming language is required. SWE-agent provides historical evidence that the agent-computer interface matters; its findings do not certify this skill's proposed interfaces.

## Explore live repair

Define **image** explicitly as a live runtime state or persisted object snapshot when that is intended; distinguish it from a container image and a generated bitmap. Distinguish actors, live images, code replacement, reactive recomputation, and browser hot-module replacement. They are related design ingredients, not interchangeable guarantees.

For an actor/state repair specimen, use a proposed protocol such as `inspect_state`, `propose_patch`, `check_patch`, `trial_patch`, `activate_patch`, and `revert_patch`. These names require implementation; they are not host tools already available.

1. Capture behavior version, state schema, object identity, in-flight work, mailbox/message versions, and effect ledger.
2. Stage a bounded patch plus any forward state migration against an isolated snapshot. Identify incompatible messages and dependencies.
3. Run invariant checks and replay a synthetic or approved trace with external side effects suppressed. Compare with the baseline and original state.
4. Reach the runtime's supported safe point: drain, suspend, route, or version-pin the affected work. Preserve unrelated execution only if the runtime actually supports it.
5. Activate through an atomic version/ownership check; reject a stale patch. Record the transition and observable result.
6. On failure, restore code and state only through a tested compatible rollback. A code rollback may not reverse a state migration. Restoring an image cannot unsend email, reverse a charge, or undo external writes. Reconcile those separately.

Test delayed old messages, mixed versions, lost acknowledgments, migration failure, concurrent edits, repeated activation, worker death, and irreversible effects. Some changes still require restart or a normal deployment. Live mutation should not quietly bypass isolation, authorization, testing, reproducible export, or recovery.

Optimize the edit/feedback loop where evidence supports it. Containers and CI can still provide isolation, packaging, reproducibility, distribution, and independent checking around a live environment. Delete a phase only when its responsibility is covered elsewhere and the experiment demonstrates the benefit.

## Teams, interface, and output

If real delegation is available, let independent inventors develop candidates before seeing each other's preferred ideas. Assign a prior-art scout to find predecessors, a skeptic to attack the premise, and an experimental builder to implement a small comparison. Rotate perspectives; do not mistake agreeable role-play for independent evidence. One coordinator integrates the decision. Work sequentially when delegation is unavailable.

For an invention-workspace request, add hypothesis cards, predecessor links, mechanism sketches, experiment runs, cost/evidence, and Keep/Revise/Shelve decisions to the existing GUI. Keep this research decision separate from operational task state: a successful experiment can legitimately reject an idea. Use a dependency map and actual run/artifact links. Do not mark an idea proven merely because an implementation task is Done.

Deliver a compact ranked set, the strongest counterargument to each, the most promising experiment, and an explicit novelty/evidence status. For an implementation request, also deliver the runnable specimen, setup, actual comparison results, and the decision it supports. When sharing is requested, show the strange useful behavior in [the demo playbook](show-and-share.md) without pretending the concept is already proven.
