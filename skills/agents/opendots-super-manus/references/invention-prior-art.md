# Prior-art lenses for Super Manus invention

Checked October 4, 2026 UTC. These sources ground mechanisms and limitations. Proposed product combinations and interfaces remain hypotheses. Refresh current competitors and APIs when selecting a candidate.

| Lens | Primary source and established ingredient | Original question to test |
| --- | --- | --- |
| Live objects and inspectable environments | [Squeak/Smalltalk](https://squeak.org/) describes a modifiable system with live graphical objects, browsing, debugging, and versioning tools. | Can a model repair one inspectable object and let a human compare the effect without reconstructing the whole task context? |
| Runtime code replacement | [Erlang code loading](https://www.erlang.org/doc/system/code_loading.html) supports old/current module code; transitions and purging have specific semantics. Compilation still exists. | Is the smallest safe change an actor behavior or operation graph instead of a whole application release? |
| Upgrade and migration | [OTP release handling](https://www.erlang.org/doc/system/release_handling.html) supports runtime release changes, with state transformation and ordering concerns; some updates require restart. | Can an agent propose a bounded migration that a runtime checks before activation? |
| Failure containment | [OTP supervisors](https://www.erlang.org/doc/system/sup_princ.html) document restart strategies and supervision. | Which smallest failed component can be repaired or replaced while useful work remains available? |
| Agent-oriented interfaces | [SWE-agent, 2024](https://arxiv.org/abs/2405.15793) studies interfaces designed for language-model agents performing software tasks. | Do typed edits, bounded observations, or counterexample feedback reduce failed corrections for this workload? |
| Incremental computation | [Differential Dataflow](https://github.com/TimelyDataflow/differential-dataflow) provides incremental data-parallel computation over changing collections. | Can an agent propagate a changed assumption through only affected computations and retain an inspectable result lineage? |
| Local ownership and collaboration | [Ink & Switch: Local-first software](https://www.inkandswitch.com/essay/local-first/) explores offline operation, ownership, and collaboration. | Can a useful agent-made workspace remain inspectable and editable through disconnection, then reconcile changes? |

## What these sources do not establish

They do not prove that the entire compile/restart/deploy loop disappears, that live repair is always cheaper, that containers are obsolete, that programming languages are equivalent, or that a particular economic cause explains present tooling. A mechanism can be old while a combination, interface, use case, or distribution model is worth testing. State the proposed difference and compare it to actual alternatives.

## Candidate research record

Record each query, retrieval date, closest matching source, overlapping behavior, remaining difference, and unresolved question. Include at least one search intended to falsify novelty. Inspect code or a real demo when a marketing page cannot establish behavior. Keep novelty confidence separate from usefulness and feasibility.

## Adoption questions

Who experiences the changed behavior? What must they install or trust? What happens to their existing files and team practices? Can they export their work? Does a maintained existing system already offer the advantage? Could a small extension deliver the same value without a new platform?
