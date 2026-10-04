# Integrate with OpenDots

## Contents

- Baseline and existing seams
- Skill delivery and tools
- Build sequence
- Application surfaces
- Persistence and deployment

## Baseline and existing seams

Inspect the user's revision before editing. This audit used CopilotKit/OpenDots commit `c2569bb6a13a22e565cf3eb791c62267d06babb1`. These paths and limits are observations at that revision.

The template uses React/Vite, Node, SQLite application state, CopilotKit runtime and Threads, TanStack AI, AG-UI, Channels for Slack, a voice compute bridge, and optional OpenBot computer services. Preserve its stack and package lock unless evidence warrants a change. The audited Node requirement is 24 or newer.

| Observed file | Responsibility | Extension seam |
| --- | --- | --- |
| `src/server/dot-agent.ts` | Prompt, tools, model loop, abort | Scoped tools, compact skill catalog, durable-work dispatch |
| `src/server/tanstack-tools.ts` | Tool conversion and learned skills | Validated snapshot-bound loading |
| `src/server/headless.ts` | Server turns through Intelligence | Scoped worker-to-agent bridge |
| `src/server/runner.ts` | Background execution | Team leases and media polling |
| `src/server/store.ts` | Tasks, runs, events, memories | Additive migrations and transactional coordination |
| `src/server/workspace.ts` | Spaces, Dots, thread bindings | Authenticated resource scope |
| `src/server/page-tools.ts`, `page-service.ts`, `pages.ts` | Page access and revision checks | Artifact receipts and project references |
| `src/server/computer-service.ts`, `computer-tools.ts` | Isolated computer access | Exclusive browser leases, bounded shell work |
| `src/server/parallel.ts` | Search/fetch MCP | Batched evidence collection |
| `src/server/voice.ts`, `slack-channel.ts` | Channel bridges | Same permission/run model across channels |
| `src/server/learning.ts` | Learning integration | Scoped skill versions |
| `src/shared/`, `src/client/` | Contracts/UI | Trace actual renderers before adding surfaces |

Observed constraints: the Dot has a 90,000 ms timeout, five iterations or ten with learned skills, and a 2,200 completion-token setting. `Runner.tick()` returns when one local task is active. The store issues 180,000 ms leases. The search adapter handles at most five sources per call and truncates excerpts. Extend durable execution rather than merely raising these limits indefinitely. Source inspection does not establish deployed behavior.

Preserve existing strengths: task claims are transactional and completion checks ownership; page updates check expected revisions. `src/client/PageDocument.tsx` supplies rich/source editing, autosave, conflict handling, and Markdown download. Generalize these seams for teams and artifacts instead of replacing them with weaker duplicate mechanisms. Existing retry reruns task execution; it does not establish provider-job resumption.

The template's `SECURITY.md` identifies a single-owner prototype and further work needed for connected multi-user enforcement. Agent teams and human teams are separate requirements. Keep the deployment single-owner until identity and resource boundaries pass tests.

## Skill delivery and tools

1. Preserve existing Dot instructions and append a short relevant role. Avoid loading the entire reference corpus into every prompt.
2. Inspect learned-skill delivery. The audited executors expose `copilotkit_load_skill` and `copilotkit_read_skill_file` through verified snapshots. Use supported learning containers when configured. Copying `SKILL.md` into the repository does not automatically load it.
3. For local skill delivery, implement a server-owned catalog: parse frontmatter, expose metadata, load instructions on invocation, and confine reference reads to the resolved skill root. Reject traversal and escaping symlinks. Version skills and review scripts before execution.
4. Register schema-validated server tools. Derive owner and allowed Spaces from the authenticated run, not client-supplied IDs. Recheck permissions before actual execution.
5. Reuse the TanStack conversion and installed SDK's documented AG-UI events. Give custom event payloads a shared versioned schema and renderer; do not invent built-in AG-UI types.

The following are proposed tools to implement, not existing OpenDots APIs:

| Tool | Input | Output |
| --- | --- | --- |
| `work_create` | Goal, capability IDs, artifact specs, budget | Persistent run/status |
| `work_status` | Run ID | Tasks, evidence, blockers, spend |
| `work_control` | Run ID, pause/resume/cancel | Control receipt and outstanding jobs |
| `team_assign` | Parent, task contract, role | Child ID with restricted inherited scope |
| `media_submit` | Catalog key, validated input, reservation | Durable job ID |
| `media_status` | Job ID | Provider state and artifact receipts |
| `artifact_read`, `artifact_patch` | ID, expected revision, operation | Authorized content or version conflict |
| `automation_create` | Trigger, condition, task, timezone, delivery | Schedule/event registration and test receipt |

Reuse existing page/computer tools where sufficient. Keep provider adapters replaceable. Do not create a second page database or conversation history accidentally.

## Build sequence

For a full build, complete all requested phases with evidence and explicit remaining gaps.

1. Inventory source, storage, tools, limits, budget, and capability statuses. Back up data before migrations.
2. Prove one run: request → durable task → actual tool → persisted artifact → preview → cancel/resume. Restart the server and recover it.
3. Add bounded teams: dependencies, leases, heartbeats, fencing tokens, separate contexts/output ownership, reviewer integration.
4. Add one real image and video adapter, request reconciliation, durable downloads, preview, editable source timeline, final rendering. Then add alternatives required by the user.
5. Add research and office workflows: ingestion, provenance, computation, rendered output, export/edit round trips.
6. Add web/game/app tools: isolated build previews, test execution, deploy/rollback, infrastructure and usage accounting.
7. Add schedules, event ingress, outbox delivery, timezone semantics, account mapping, and operational history.
8. Execute acceptance checks for every requested capability; repair in-scope gaps and name external blocks.

## Application surfaces

Show task phases, responsible Dots, dependencies, status, last activity, and actionable errors. Render real events. Make work navigable from chat, Space, and artifact.

Separate code installed, account configured, last live verification, and current health. Hide secrets. Display estimates, reservations, actual charges, and pricing retrieval dates.

Provide artifact versions, source links, download, preview, editing, and reuse. Media needs an asset bin, storyboard, separate tracks, captions, sound controls, region edits, and before/after review. JSON plus a renderer gives reproducible source editing; it does not establish a functioning visual timeline UI.

Keep pause/cancel/resume keyboard-accessible. Preserve focus, save/conflict states, mobile usability, reduced motion, and useful progress announcements. Load relevant frontend/UX skills when actually implementing UI.

## Persistence and deployment

Use existing server-side configuration for Intelligence, models, computers, speech, and channels. Add media secrets in a server environment or secret store. A ChatGPT subscription is not an API credential; never copy its sessions into OpenDots.

Use loopback for local work. Computer execution requires separately configured services from `docs/COMPUTERS.md`. Do not expose supervisors or Docker sockets publicly. Use an always-available worker for schedules and long jobs; a request handler cannot promise work after its process ends.

SQLite can support a small single-server team with short transactions and a bounded pool. Multiple hosts need shared transactional coordination. Back up metadata and artifact bytes together and test restoration. Distinguish preview from production and follow the user's authorization for publishing, domains, spending, and external delivery.
