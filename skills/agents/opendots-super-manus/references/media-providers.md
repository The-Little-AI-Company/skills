# Connect media providers

## Contents

- Routing and capability discovery
- Codex and OpenAI images
- fal
- Higgsfield
- Other providers
- Local queue client
- Production integration

## Routing and capability discovery

Choose by the task's required edit/control, account access, cost, latency, privacy, rights, and delivery format. A brand name or benchmark ranking is insufficient. Distinguish provider from model: fal and Higgsfield expose multiple model families with different schemas.

Before paying, store a model card: provider/account, exact endpoint/model version, documentation URL and retrieval date, input schema, output schema, supported aspect ratios/durations/resolutions, reference/mask/frame/audio support, costs and pricing basis, rate/concurrency limits, data retention, and cancellation/idempotency behavior. Validate inputs against that card. Never send a generic field bundle to every provider.

Use native tools or connected MCP where supported; otherwise implement a server-side API adapter. Discover actual MCP tool names/schemas through initialization and tools/list. Do not guess names from marketing. Missing access is a blocked capability, not a reason to fabricate output.

## Codex and OpenAI images

Inside Codex, prefer the available native image-generation tool. Follow its live schema and imagegen skill: generation versus editing, transparent background, supplied image references, and how results are displayed/persisted. Read local references before editing; preserve intended invariants. Do not set unsupported API parameters on the native tool or ask for an API key it does not need.

A deployed OpenDots server has no automatic access to Codex's private image tool. For unattended work, use a documented image API under the user's server-side credentials. A Codex-assisted asset handoff can import the resulting image into OpenDots when the host exposes a supported export; it is not a callable production bridge. Never extract subscription tokens, automate private app endpoints, or promise subscription-funded server inference.

For the OpenAI API, inspect installed SDK/examples first, then current official image API documentation. Confirm the selected model's generation/editing/transparency limits. Use the official SDK's image generation or edit operation with explicit model and validated input. Decode returned image bytes/base64 or fetch permitted outputs according to the documented response. Store original bytes and an artifact receipt. Keep built-in-tool behavior separate from API billing and model support.

## fal

Primary guide: https://fal.ai/docs/documentation/model-apis/inference/queue . Use server-side `@fal-ai/client` for a Node integration, or the bundled conservative HTTP client for local jobs.

The documented queue supports submit, status, result, and cancel. Persist its request ID and returned operation URLs. Status uses `IN_QUEUE`, `IN_PROGRESS`, and `COMPLETED`; completion can contain `error`/`error_type`. Check failure fields and retrieve the actual result before success. Queue cancellation is best-effort after processing begins. Webhook envelopes use `OK`/`ERROR`, not queue status names.

Minimal SDK lifecycle, with values taken from a validated model card:

```typescript
import { fal } from '@fal-ai/client';
fal.config({ credentials: process.env.FAL_KEY });
const accepted = await fal.queue.submit(modelId, { input: validatedInput });
// Persist accepted.request_id before returning the job receipt.
const status = await fal.queue.status(modelId, {
  requestId: accepted.request_id,
  logs: false,
});
// Persist status. Once terminal, check errors and fetch the result:
const result = await fal.queue.result(modelId, { requestId: accepted.request_id });
// Normalize against the model's output schema, then save/inspect its assets.
```

Use `fal.queue.cancel` for cancellation and preserve the actual response. Webhooks need raw-body signature verification using current fal guidance, timestamp validation, account/request matching, and duplicate suppression. Retain polling as recovery. Use model-specific output parsing and store media before expiration.

## Higgsfield

Discover models at the Higgsfield Console and open each model's API page. Its docs index explicitly makes model-specific docs authoritative over the supplementary OpenAPI catalog. Distinguish production from preview and documented availability from verified account access.

HTTP authentication is `Authorization: Key <key-id>:<key-secret>` against `https://api.higgsfield.ai`. Submit JSON to the exact model endpoint. Save `request_id`, `status_url`, and `cancel_url`; follow returned URLs instead of constructing them. The shared states are `queued`, `in_progress`, `completed`, `failed`, `nsfw`, and `canceled`. `nsfw` is terminal rejection, never a prompt to circumvent moderation.

The current [idempotency policy](https://docs.higgsfield.ai/docs/concepts/idempotency) binds a key to one generation intent in an account. Use a new random key for a deliberately new generation, even with identical inputs. Persist the key before POST. Recovery reuses the same key, endpoint, body, and webhook configuration; a 422 mismatch requires reconciliation, not an automatic new key. No retention window was stated in the reviewed policy. Cancellation uses POST to the returned cancel URL, succeeds with HTTP 202 and an empty body, and is unavailable after work starts. A local canceled UI must not falsely imply a running provider job stopped.

Official SDKs are `higgsfield-client` for Python and `@higgsfield/client/v2` for TypeScript. Their environment naming differs (`HF_KEY` versus `HF_CREDENTIALS`); configure the actual SDK, not an invented common variable. For the bundled HTTP client, use `HF_API_KEY_ID` and `HF_API_KEY_SECRET`.

Higgsfield webhooks use the `hf_webhook` query parameter; output sits inside `payload`, while status polling exposes output fields on the response. Do not use fal's webhook parser. The reviewed webhook page did not document a signature scheme. Until verified authentication is available, use webhook arrivals only to wake authenticated status polling; never trust the posted output as authority. Save terminal assets to your own storage; current docs promise at least seven days of output availability, not permanent storage.

## Other providers

Treat these as documented integration routes to implement and verify, not included live adapters.

| Provider | Route | Integration details to verify |
| --- | --- | --- |
| Replicate | Official client or predictions HTTP API | Official/community/deployment endpoints differ; persist prediction ID, poll or use verified webhooks, handle terminal failure/cancel, save expiring outputs |
| Runway | Official SDK/task APIs | Select text/image/video endpoint, required API version and current model; persist task ID, retrieve status, cancel where supported, save output |
| Google | Current Gemini video/image APIs | The reviewed video overview distinguishes conversational video generation from Veo-specific controls; use the selected model's current guide and operation contract |
| ElevenLabs | Official speech, sound, music, transcription APIs | Discover available voice/model IDs, preserve consent, timestamp alignment, pronunciation, format, and commercial-use limits |
| Local inference | Existing ComfyUI or other authorized local service | Discover installed model/workflow schema, GPU memory, queue/cancel behavior, licenses, and file roots; mark unsupported without adequate hardware |

Never route around a safety rejection using another provider. A technical outage fallback may use an equivalent provider only within authorized privacy and spending scope, after reconciling the first submission.

## Local queue client

The bundled `scripts/media_queue.py` supports fal/Higgsfield submit, one-shot status, cancel, and inspect with a private local SQLite ledger. Use it as a single-operator helper; concurrent status/cancel updates lack production fencing. It does not upload files, download outputs, estimate provider prices, verify webhooks, enforce team-wide budgets, or inspect creative quality. Integrate those separately before production use. Fixtures test HTTP behavior; live account access was not tested during skill creation.

1. Choose a documented endpoint and write its validated input JSON in a private working directory.
2. Configure credentials on the server, never in chat or arguments.
3. Supply an already authorized conservative upper bound in USD. Zero is allowed only for a documented free operation.
4. Use a unique operation key for this creative attempt. Reuse that key only for the identical job.

```bash
python3 <skill-dir>/scripts/media_queue.py --db ./private-media/jobs.sqlite submit \
  --provider fal --model <verified-model-path> --input ./input.json \
  --operation launch-shot-01-v1 --max-usd <authorized-upper-bound> --authorized
python3 <skill-dir>/scripts/media_queue.py --db ./private-media/jobs.sqlite status --operation launch-shot-01-v1
python3 <skill-dir>/scripts/media_queue.py --db ./private-media/jobs.sqlite inspect --operation launch-shot-01-v1
python3 <skill-dir>/scripts/media_queue.py --db ./private-media/jobs.sqlite cancel --operation launch-shot-01-v1
```

Use `--provider higgsfield` for that provider. The authorization flag is a local operator acknowledgment, not a security boundary; do not expose this CLI directly to untrusted users. `inspect` returns the provider receipt, which may include private URLs; keep it out of public logs. `submission_unknown` requires provider-side reconciliation and must not be blindly resubmitted. The helper conservatively blocks repeated POSTs even where provider idempotency could support a careful recovery path.

## Production integration

Wrap adapters in the runtime contracts. Add input uploads, persistent asset downloads, model catalog validation, shared budget reservation, user authentication, leases, event delivery, and provider account binding. Respect rate limits. Cap response bodies and media sizes. Validate all provider operation URLs before attaching credentials and reject redirects to unexpected hosts.

Perform one inexpensive authorized live generation per enabled path, then test status, persisted output, restart recovery, and cancellation behavior. Expose implemented/configured/verified separately. A successful HTTP submission alone does not pass the image or video capability.
