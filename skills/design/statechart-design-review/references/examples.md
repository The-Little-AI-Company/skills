# Worked examples

These are original teaching models, not figures or examples reproduced from Harel. Their execution rules are explicit design choices, not universal statechart rules.

## Upload with cancellation and retry

**Boundary:** One upload controller; the remote service may finish work after local cancellation.

**States:** `Idle`; compound `Running` with `Sending` (default), `WaitingRetry`, and `Reconciling`; `Canceling`; `Succeeded`; `Canceled`; `Failed`.

**Context:** operation ID, attempt generation, retry count/limit, remote object ID. Keep these values out of the state name.

**Events:** START, SEND_OK(id,generation), SEND_FAILED(id,generation), RETRY_DUE, CANCEL, CANCEL_ACK(id), RECONCILE_RESULT(id,status).

**Proposed semantics:** Process one admitted event at a time in queue order. Evaluate guards against pre-step context. Require mutually exclusive outgoing guards. Record the selected transition and context update before dispatching its external effect. Drop stale completions by operation ID/generation. Do not assume cancellation erases remote side effects.

| Source | Input and condition | Target | Effect |
| --- | --- | --- | --- |
| Idle | START | Running.Sending | Allocate operation/generation; issue upload |
| Running.Sending | SEND_FAILED matches, retries remain | Running.WaitingRetry | Record error; schedule retry |
| Running.WaitingRetry | RETRY_DUE | Running.Sending | Increment generation/retry count; issue attempt |
| Running.Sending | SEND_OK matches | Succeeded | Record authoritative result |
| Running | CANCEL | Canceling | Invalidate local generation; request remote cancellation |
| Canceling | SEND_OK for operation | Canceling | Record evidence for reconciliation; do not publish success |
| Canceling | CANCEL_ACK confirms no remote commit | Canceled | Record terminal cancellation |
| Canceling | ambiguous remote status | Running.Reconciling | Query remote authority; keep publication suppressed in context |

This partial table exposes an important review obligation: `Reconciling` under `Running` must not accidentally restore permission to publish success. Either model a dedicated canceled-intent reconciliation branch, or define and test that permission explicitly. Also decide what CANCEL after Succeeded means; it might require a separate deletion workflow, not retroactive cancellation. Complete missing timeout, retry-exhaustion, and reconciliation-result transitions before implementation.

**Counterexample trace:** START → CANCEL → late SEND_OK. An implementation accepting every SEND_OK as success violates “no successful publication after cancellation intent is accepted.”

**Tests:** Both SEND_OK/CANCEL orderings; duplicate CANCEL; old-generation failure after retry starts; cancellation during retry wait; acknowledgment loss; restart after remote commit but before local acknowledgment. State which ordering is authoritative and which external outcomes are irreversible.

## Editor with orthogonal concerns and resumable tools

**Control:** `Closed` or `Open`. Inside Open, orthogonal regions `Document` (Clean, Dirty, Saving) and `Connection` (Online, Offline). Within a separate `ToolMode` composite, Drawing may contain Line and Curve.

**Context:** document revision, content, save request ID, connectivity observations. Independence is conditional: connection changes gate save dispatch, but do not automatically erase dirty content.

**Invariant:** Only an acknowledgment matching the saved revision can mark the current document clean. A newer edit during Saving remains dirty after the older acknowledgment.

**Coordination choice:** Evaluate guards using the pre-event configuration. Let one coordinator own save scheduling; do not rely on which parallel region executes first. On a simultaneous disconnect/save request, define the admitted order or a deterministic arbitration policy.

**History choice:** A shallow history return to ToolMode recalls Drawing but uses Drawing’s default child; deep history can restore Curve. Define a fallback for first entry. Invalidate tool history when changing document types if the remembered tool is unavailable. Neither form restores document bytes, socket connections, nor an unfinished save transaction.

**Tests:** edit during save; acknowledgment for old revision; reconnect after queued edits; tool first-entry fallback; shallow versus deep resume; reset history; changed document compatibility. Pair each trace with the complete regional configuration, not one selected leaf.
