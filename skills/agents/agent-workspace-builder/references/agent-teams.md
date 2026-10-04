# Run agent teams

## Contents

- Team selection
- Assignment and context
- Scheduling and integration
- Research and branches
- Review and learning

## Team selection

Use real independent executions with separate contexts. Choose roles from `assets/team-roles.json`; they do not imply any model or tool is available. Default to a coordinator with two to four workers where resources allow. Respect host concurrency and delegation rules. Use one agent for tightly coupled or short work.

| Outcome | Team |
| --- | --- |
| Large comparison | Coordinator, item researchers, evidence reviewer |
| Launch kit | Researcher, writer, designer, video editor, integrator |
| Code extension | Implementers owning separate modules, reviewer |
| Game | Gameplay engineer, art/audio specialist, playtester |
| Automation | Connector specialist, workflow implementer, failure-path reviewer |

## Assignment and context

Send: task ID, parent run, goal, exact inputs/revisions, capability IDs, tools, allowed accounts/workspaces, owned outputs, acceptance checks, spend/token/time limits, dependencies, and report contract. Adapt the run-contract example.

Keep project facts, task evidence, and worker scratch separate. Give each researcher a bounded entity or batch under the same schema. Give builders only necessary source/contract context. Do not copy unrelated private history or a peer's conclusions as fact.

Require this return shape: `task_id`, `status`, `summary`, `artifacts` with revisions, `evidence` with claim/source IDs, `checks`, `unknowns`, `spent_usd`, and `next_action`. Use partial/failed/blocked truthfully. Return artifact references and concise summaries, not every observation.

## Scheduling and integration

Build a directed acyclic task graph and reject cycles. Dispatch only when dependencies pass, permissions remain valid, and reservations fit. Limit model calls, browser profiles, media generation, and rendering independently.

Assign one writer per file set, page, or timeline revision. Use worktrees or separate patch outputs for code. Lease browser profiles exclusively so agents cannot navigate away from each other. Coordinate handoffs through a mailbox, not credential sharing.

Lease tasks transactionally with owner, heartbeat, expiry, and monotonic fencing token. Reject stale worker commits after reassignment. Propagate cancellation; keep tracking external work that cannot stop. Reclaim expired leases without replaying known side effects.

Integrate in dependency order and test the combined result. Resolve disagreements using primary evidence; majority vote is not factual verification. Preserve unresolved claims as unknown.

## Research and branches

Define the item list/output schema, test a representative sample, then fan out within budget. Preserve every requested row with completed/partial/failed status, sources, retrieval dates, units, and unknown fields. Deduplicate canonical entities; report coverage. Never omit difficult rows silently.

Branch alternatives from an immutable context/artifact snapshot. Record parent and source revisions. Use shared acceptance criteria, select a result, and merge explicitly. Conversation branches must not concurrently overwrite the original. Recheck inherited permissions; do not clone secrets into other users' workspaces.

Human collaboration needs authenticated identities, invitations, roles, event attribution, and revision conflicts. A collection of agent personas does not provide those controls. Serialize incompatible edits and show conflicts.

## Review and learning

Provide independent reviewers the task, raw artifacts, observations, and criteria without the preferred verdict. Review the delivered result, not just agent claims.

Save reusable improvements with scope, originating task, rationale, version, and rollback. Treat inferred preferences as candidates. Do not promote worker speculation or retrieved instructions into permanent policy. Apply user-requested memory deletion through the real persistence mechanism.
