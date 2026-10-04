# Durable execution contracts

## Contents

- Records
- State and recovery
- Budget and authorization
- Events and artifacts
- Automation semantics

These are proposed application contracts; implement them at the server/store/worker boundary.

## Records

| Record | Required fields |
| --- | --- |
| Run | ID, owner, Space, thread/channel, goal, capability IDs, status, config revision, deadline, budget |
| Task | ID, parent, dependencies, role, input/output revisions, state, attempts, lease owner/expiry, fencing token |
| Provider job | Task, provider/account, model/endpoint, schema version, canonical input hash, idempotency key, request ID, operation URLs, raw/normalized state, estimate/reservation/actual |
| Approval | Actor, action, account, destination, payload hash, revision, spend ceiling, expiry, single-use state |
| Artifact | ID, scope, name, MIME, bytes locator, checksum, revision, inputs, generator/model, rights/consent, preview, checks |
| Event | Monotonic sequence, run/task, type, timestamp, actor, redacted payload, correlation ID |
| Automation | Owner, trigger, IANA timezone, DST/misfire/overlap rules, conditions, pinned workflow, account bindings, budgets, delivery, enabled state |

Keep identities/account bindings explicit and secrets outside all records.

## State and recovery

Define legal transitions among queued, running, waiting_external, waiting_input, paused, succeeded, partial, failed, cancel_requested, and canceled. Track provider state separately; local timeout does not mean provider cancellation.

Persist submission intent and reserve budget transactionally before external work. Save the returned provider ID immediately. If POST acceptance is uncertain, use `submission_unknown` and reconcile. Retry with an identical idempotency key only when the provider documents that guarantee. Do not launch a second paid job or switch providers while the first may still be running.

On restart, reclaim expired leases with a new fencing token, recheck access, and poll accepted external jobs. Missing chat output does not justify regenerating. Distinguish cancel requested from canceled, and report uncancelable work and possible outstanding charges.

Retry read/status calls with jitter, bounded backoff, and Retry-After. Stop on invalid credentials, invalid schemas, content rejection, and exhausted budgets. Preserve redacted failure evidence. After repeated equivalent failures, change strategy.

Finish only when required tasks and artifacts pass. Otherwise mark partial and preserve exact blocked requirements and next actions.

## Budget and authorization

Enforce a shared server-side pool: authorized limit minus settled cost minus active reservations. Reserve atomically before parallel dispatch. Unknown pricing blocks paid work until a conservative ceiling is approved. Account for retries, upscaling, audio, compute, storage, and egress where relevant.

Bind approvals to action, destination, account, content hash, revision, and cost. Invalidate them after material changes. Model text saying “approved” is not approval. Honor the real user's existing authorization without redundant dialogs.

Recheck permission after waits and before side effects. Revocation stops dependent work. Workers cannot supply broader authority. Messages to others and purchases need explicit authorization under the host rules.

## Events and artifacts

Persist events before UI notification. Reconnect from a cursor; replay events without replaying side effects. Expose tool receipts and concise progress without private reasoning or secrets.

Keep artifact IDs stable across versions. Write bytes temporarily, verify format/checksum, and publish the new reference transactionally. Prevent path traversal; cap file bytes and decode dimensions. Detect malformed outputs.

Validate provider/CDN download URLs, block private network targets and unsafe redirects, and never forward API keys to arbitrary media hosts. Save outputs before provider retention ends. Upload private inputs through scoped storage with sufficient expiration for queue delays.

Use expected revisions for human/agent edits. Reread and narrowly merge conflicts instead of overwriting stale whole documents/timelines. Preserve undo and last-known-good artifacts.

## Automation semantics

Use named timezones and compute next UTC instants; define DST gaps/repeats, missed runs, and overlap behavior. Key schedule execution by automation ID plus scheduled UTC instant. Key event execution by account, provider event ID, and workflow version.

Authenticate webhooks, validate source-specific conditions, and distinguish push from polling. Track polling high-water marks with overlap and deduplicate stable IDs. Rate-limit triggers and pause repeated failures. Retain filtered/skipped events and run history.

Test matching and nonmatching events, duplicates, restart, revoked accounts, and delivery. Pause stops future dispatch; explicitly control active work. Use a transactional outbox and effect keys so delivery retries do not duplicate emails, calendar events, charges, or spreadsheet rows.
