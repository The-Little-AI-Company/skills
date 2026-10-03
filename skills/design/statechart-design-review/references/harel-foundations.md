# Harel foundations

Primary source: David Harel, “Statecharts: A Visual Formalism for Complex Systems,” *Science of Computer Programming* 8 (1987), 231–274. [Original paper](https://www.state-machine.com/doc/Harel87.pdf). Page numbers below are printed journal pages; PDF page number is printed page minus 230. Use brief original paraphrases; consult the paper for its figures and detailed argument.

## Source map

- **Hierarchy, XOR, default entry, pp. 234–238:** Nested state structure expresses refinement and shared behavior without repeating every transition at each leaf. Describe which substate becomes active on entry. A superstate is not merely decorative grouping.
- **History, pp. 238–240:** H and H* distinguish history at one level from deeper remembered configurations. State exactly which depth is restored. History retains control configuration, not arbitrary application data or durable execution.
- **Parent/child conflict, p. 241 and Fig. 18 on p. 242:** Enabled transitions at different nesting levels can introduce nondeterminism. Do not retroactively apply a modern interpreter’s deepest-state priority to this paper.
- **Orthogonality, pp. 242–243, Figs. 19–20:** AND decomposition permits simultaneous component states without drawing every Cartesian-product combination. The diagram shrinks; possible global configurations and interactions still require reasoning.
- **History invalidation, p. 247:** The watch discussion includes clearing history at a state or through deeper structure when the remembered configuration is no longer valid. Model reset and invalidation explicitly.
- **Control and values, p. 250:** Control-state structure does not replace the separate representation of numerical values. Use this distinction to avoid both state explosion and context flags that conceal control behavior.
- **Actions and activities, pp. 256–258, Fig. 37:** Transition labels relate events, conditions, and actions. Actions are idealized as instantaneous; activities may continue over an interval. Detailed specification of activities is outside the paper’s scope. Do not implement a network request as a blocking instantaneous action merely because its start appears on an edge.
- **Possible extensions, pp. 258–264:** Treat these as proposals in the source rather than silently promoting every extension to a mandatory core feature.
- **Semantics, pp. 264–267:** Broadcast, generated events, loops, simultaneous occurrences, and condition evaluation pose substantive semantic issues. Figs. 47–48 on p. 265 illustrate hazards; p. 266 sketches configurations and next-step reasoning. The article is foundational, not a complete interchangeable execution specification for all modern libraries.

## Keep three layers separate

1. **Historical concepts:** Attribute hierarchy, orthogonality, and history to the source and cite the relevant pages.
2. **Chosen execution semantics:** State the interpreter’s rules for priority, queues, macrosteps/microsteps, guard snapshots, effect ordering, and termination. Verify them against the specific runtime/version or define them explicitly for a conceptual model. Run-to-completion, actor isolation, durable checkpoints, and exactly-once external effects are not consequences of drawing a statechart.
3. **Renderer capabilities:** Check what a diagram language actually expresses. A renderer might draw nested/parallel states while omitting history depth, transition priority, event processing, or activity lifetime. Preserve those semantics in prose or a table, and label approximations. Do not claim every diagram can be compiled or executed.

Use modern reliability mechanisms such as idempotency keys and generation IDs as engineering recommendations, not quotations or claims from Harel’s 1987 paper.
