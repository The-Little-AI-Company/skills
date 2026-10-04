# Build a GUI and Kanban that control real work

## Contents

- Core screens and user journeys
- Board and task semantics
- Task controls and conflicts
- Events and persistence
- Artifact and capability workspaces
- Accessibility and acceptance

## Core screens and user journeys

Use existing UI/design conventions and relevant frontend/UX skills. A useful first version has a board, task detail panel/page, artifact viewer, capability catalog, team activity, and settings. Small screens use one primary view with clear navigation; avoid shrinking every desktop panel into columns.

The primary journey is create a task → inspect the plan → run authorized work → observe actual progress → inspect/edit output → accept or request a bounded revision. A second journey adds a missing capability → implements/tests/registers it → resumes the blocked task. Show useful empty states, loading, reconnecting, validation errors, blocked configuration, and partial success.

## Board and task semantics

Recommended columns: **Backlog**, **Ready**, **Running**, **Blocked**, **Review**, **Done**, **Canceled**. Keep Paused as an explicit execution state visible on the card/detail rather than silently pretending the task is blocked. Map execution states to columns centrally in server code. Kanban is a projection of durable task state.

| State | Entry requirement | Exit behavior |
| --- | --- | --- |
| Backlog | Defined goal; may lack prerequisites | Ready after inputs/dependencies/authority validated |
| Ready | Runnable inputs, dependencies satisfied, required scope available | Running only after a worker claims an attempt |
| Running | Actual claimed worker or external job | Review with artifact/checks; Blocked on actionable obstacle; pause/cancel through control commands |
| Blocked | Reason, owner, and next action | Ready only after blocker resolution; preserve attempt history |
| Review | Output plus verification evidence | Done when acceptance passes; new revision task/attempt if changes requested |
| Done | Acceptance evidence and artifact/effect receipt | Reopen through an explicit revision; preserve completed attempt |
| Canceled | Confirmed terminal cancellation or no outstanding work | New explicit attempt; never silently revive an uncertain operation |

Cards show title, assignee, priority, dependencies/blockers, latest activity, artifact count, and real execution phase. Show progress fractions only when measurable (for example 4/6 shots); otherwise show status and last event. Never animate invented percentages.

Model tasks separately from attempts and subtasks. Keep stable task IDs and a revision. Use dependency IDs and prevent cycles. A child completion does not automatically complete its parent until integration and acceptance pass.

## Task controls and conflicts

Drag-and-drop requests a validated transition; it cannot move arbitrary work into Running or Done. Provide a keyboard-accessible Move menu with the same rules. Reordering Ready tasks changes priority only; it does not change active worker ownership.

Task detail includes input/brief, plan/dependencies, output links, observed action timeline, checks, errors, budget/charges, and next action. Display concise reasons and tool events, not hidden chain-of-thought. Use attributable edits and expected-revision writes; on conflict, preserve drafts and show reload/compare options.

- Start/enqueue validates configuration, scope, dependencies, and budget before dispatch.
- Pause stops new dispatch and checkpoints where supported. Show any in-flight external operation.
- Cancel records `cancel_requested`, stops future dispatch, signals workers/providers, then reports confirmed cancellations and outstanding jobs separately.
- Retry creates a new attempt only after prior side effects are reconciled. It is not an unconditional replay button.
- Resume uses the persisted attempt/provider ID when supported. Revalidate any changed inputs or permissions.
- Approve binds the exact action, account, destination, revision, and cost. Prior user authorization remains effective; do not add redundant approval gates.

## Events and persistence

Persist tasks, attempts, artifacts, capability versions, reviews, and ordered events. Fetch a snapshot plus cursor, then subscribe using SSE/WebSockets supported by the stack. Reconnect from the last cursor; deduplicate event IDs. Apply updates monotonically per task revision and refetch on gaps. A late event from a fenced worker cannot overwrite newer state.

Optimistic UI is appropriate for reversible metadata edits with rollback. Execution, cost reservation, external completion, and acceptance require server acknowledgment. Reconcile after refresh, restart, and reconnect. Debounce autosave without losing drafts. Do not equate websocket delivery with database commitment.

## Artifact and capability workspaces

Artifacts need stable IDs, MIME type, size, durable source bytes, checksum, producer attempt, revision, provenance, preview, download, and appropriate source editing. Sandbox HTML previews and sanitize untrusted Markdown. Do not expose credentials through logs, signed URLs, or rendered source.

For video, implement source bin, storyboard, independent visual/audio/caption tracks, trim/reorder, preview, render progress, and revisions that preserve manual edits. A JSON timeline with reproducible rendering is a useful intermediate deliverable; label the visual editor missing until its controls work.

Capability cards show what the tool does, dependencies, supported inputs/outputs, implemented/configured/verified status, last check, costs, and setup action. Secret input is write-only/masked and stored server-side. A disabled operation explains the actual missing requirement.

Team activity shows real worker IDs, roles, assignments, dependencies, heartbeat/activity, outputs, and errors. Do not display multiple personas from one conversation as independent agents.

## Accessibility and acceptance

Keep a logical heading structure, labeled controls, visible keyboard focus, sufficient contrast, status text beyond color, and reduced-motion support. Announce important status changes without flooding screen readers. Retain focus when cards move. On mobile, use a column selector or stacked task list with full detail navigation and accessible move controls.

Verify with actual UI and backend behavior: create/edit a task; keyboard move; rejected invalid Done transition; real tool result appears; blocked setup resolves; pause/cancel/resume; refresh and worker restart retain state; reconnect deduplicates events; simultaneous human/agent edits conflict safely; artifact downloads open; mobile layout and keyboard navigation work. Record unavailable runtime/browser checks honestly.
