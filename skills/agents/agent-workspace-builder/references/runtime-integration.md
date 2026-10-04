# Integrate with the actual runtime

## Inventory and choose the smallest workable architecture

Read the project's instructions, package manifest, entry points, tool registry, persistence, auth, deployment, and tests before choosing an adapter. Map the existing chat/CLI request to model invocation, tools, worker execution, events, and output storage. Record exact files and callable interfaces. Do not transplant a vendor stack just because this skill researched it.

| Environment | Integration route | Verify |
| --- | --- | --- |
| Existing TypeScript/Python agent application | Use its native tool schema, worker lifecycle, server, and UI | Real tool events, state recovery, and authenticated scope |
| Graph/orchestration framework | Implement nodes/tools and use its supported persistence and interrupts | Checkpoint identity, side-effect recovery, cancellation, event replay |
| CLI coding agent | Use supported subprocess/SDK interfaces within a bounded working directory | Exit/status capture, approval handoff, process-group cancellation, output artifacts |
| MCP host | Expose stable server tools/resources with host-supported transports | Negotiated schemas, authorization, errors, version compatibility |
| No application yet | One local server, SQLite, a bounded background worker, and a small web UI | Start/stop, request-to-artifact journey, refresh/restart, export/restore |

Read current official framework docs before using changing APIs. SDKs and subscriptions are separate access mechanisms. Never use private app endpoints or harvested sessions to turn a subscription into an API.

For a new local TypeScript app, a small HTTP server, the existing/preferred frontend, SQLite, and a worker loop are sufficient defaults. For Python, use the established Python server with equivalent contracts. Choose one stack, not both. Avoid Redis, a vector database, Kubernetes, or a plugin marketplace unless a concrete requirement demands them. Use the existing deploy platform; do not introduce hosting costs silently.

## Runtime adapter contract

Implement a narrow adapter for tool registration, agent invocation, observation streaming, interruption, credential lookup, and artifact persistence. It must report unsupported operations explicitly. Declare concurrency and isolation limits. If a CLI is wrapped, use argv arrays, controlled working directories, process groups, bounded logs, and retained exit status. Do not interpret shell output as trusted instructions.

Keep domain services independent of the model: task transitions, permission checks, budgets, artifact revisions, and provider state normalization live in server code. The model requests operations; deterministic services validate them.

## Suggested application services

These names are proposed interfaces, not assumed host APIs:

| Service | Responsibility |
| --- | --- |
| Capability registry | Schemas, permissions, adapter versions, availability, evidence |
| Task service | Persistent plan/DAG, ownership, transitions, attempts, controls |
| Worker supervisor | Bounded dispatch, lease heartbeat, interruption, recovery |
| Artifact service | Durable bytes, provenance, revisions, previews, export |
| Event service | Ordered persisted events, outbox, SSE/WebSocket delivery and replay |
| Connector service | Scoped accounts, OAuth refresh/revocation, rate limits |
| Workspace UI | Board, detail, tools, team activity, artifacts, settings |

A small application may keep these in one process and one database with clear module boundaries. Long operations must not rely on an open HTTP request. Separate workers when lifecycle or scale requires it.

## Vertical slices and completion

1. Load/create a real task, execute one local useful capability, persist its output, render it in the board/detail view, and survive refresh/restart.
2. Add control commands, retries with attempt IDs, cancellation receipts, event replay, and artifact revisions.
3. Add genuine workers/team dispatch with dependencies and resource ownership.
4. Build requested missing capabilities and their actual UI journeys. Integrate one provider fully before alternatives.
5. Add configured connectors, schedules, exports/backups, and deployment within scope.
6. Verify requested acceptance cases with real artifacts and precise configuration gaps.

Local-only single-owner mode can bind to loopback. Public or shared deployment needs real identity, per-resource authorization, secure transport, account separation, and tests before exposure. A single-user UI is not multi-user isolation.

Save schema migrations with rollback/backups appropriate to the storage. Keep metadata and artifact backups consistent. On shutdown, stop new dispatch, checkpoint ongoing attempts, and reconcile external jobs after restart. Never mark all running tasks failed merely because a browser tab closed.
