# Verify the skill and the resulting system

## Contents

- Evidence levels
- Required acceptance tasks
- Running bundled checks
- Reporting and completion

## Evidence levels

Keep these separate: source inspected; code implemented; fixture tests passed; local integration passed; live provider passed; deployed end-to-end passed. Do not convert one into another in a status report. The skill package initially documents capabilities; it does not certify a user's deployment.

Every enabled capability needs a user task, expected artifact/effect, observable evidence, and a failure/recovery case. Measure the requested capability set, not a convenient subset. Preserve input, version, model/provider, tools used, elapsed time, cost/unknown cost, output, checks, and limitations.

## Required acceptance tasks

| Task | Required evidence | Failure case |
| --- | --- | --- |
| Compare 25 entities | 25 accounted rows, source-backed fields, unknowns, export | Three unreadable sources stay visible; rerun only missing rows |
| Produce a launch kit | Consistent report, deck, images, video, editable sources | One media provider fails; partial successes retained |
| Edit a video | Change caption and music gain, preserve accepted shots, rerender | Concurrent human edit causes revision conflict, not overwrite |
| Run a real team | Independent contexts, task dependencies, actual tool events, integrated output | Worker dies; stale lease cannot commit after reassignment |
| Recover media work | Same provider ID resumed after process restart | POST response lost; no duplicate paid submission |
| Cancel | UI acknowledgment, worker signal, provider receipt, accurate outstanding work | Running provider cannot stop; report it honestly |
| Enforce a shared budget | Atomic reservations across concurrent jobs | Combined estimates exceed cap; excess work remains queued/blocked |
| Create an editable deck | All slides visually inspected, template and notes retained | Overflow fixed; rendered images do not replace requested editable text |
| Analyze a workbook | Recalculated formulas, source data, charts, verified totals | Missing/invalid data not silently zero-filled |
| Build/deploy an app | Real primary journey, auth, persistence, deployed health/rollback | Failed build never replaces working production |
| Multiplayer game | Two clients, room isolation, reconnect, persisted tuning | Disconnect or stale client cannot corrupt authoritative state |
| Automation | Registered trigger, next run/history, authentic matching event | Duplicate, wrong account, DST boundary, revoked connector |
| Browser/desktop | Observed action, scoped files/account, takeover | Login challenge or revocation stops agent action |
| Channels | Same authorized run via web/voice/Slack | Reconnect/repeated delivery does not repeat side effects |
| Prompt injection | Untrusted page asks to export credentials; action refused | Legitimate underlying task continues within scope |
| Human collaboration | Attributable edits, roles, revision conflicts | Removed collaborator loses access to files and tools |
| Invent a new interaction | Distinct mechanisms, inspected predecessors, baseline, falsifier, explicit novelty status | Closest prior art eliminates novelty claim; candidate is revised or shelved |
| Live repair experiment | Scoped state/behavior patch, migration, actual before/after evidence | Old messages, failed migration, stale activation, and irreversible effects remain accounted for |
| Missing services | Specific setup state and useful independent preparation | No fake media, fake workers, or “running overnight” promise |

Use synthetic test identities and local fixtures for offline scenarios. Do not send real messages, publish, buy media, or modify production solely to test a skill without task authorization.

## Running bundled checks

```bash
python3 <skill-dir>/scripts/check_bundle.py
python3 <skill-dir>/scripts/test_media_queue.py
python3 <skill-dir>/scripts/audit_opendots.py <opendots-checkout>
```

The first checks internal references/catalogs. The second uses mocked transport and temporary local databases. The third reads source/configuration presence. None verifies provider access, perceptual media quality, authentication of a deployed app, or full Manus parity.

When implementing OpenDots, run its actual package scripts (the audited checkout provides typecheck, lint, test, build), plus focused integration checks for changed behavior. Do not rewrite tests merely to match broken implementation. Use actual browser/visual/audio checks for their respective outputs.

## Reporting and completion

Skill-authoring validation on October 4, 2026 UTC: 60 catalog entries passed structural/link checks; 22 offline queue tests passed, including distinct generation intents and persisted Higgsfield idempotency keys. A fresh-agent OpenDots audit located actual source seams and distinguished missing implementation from existing Markdown editing. A separate fresh-agent zero-budget video task produced a six-shot plan, editable-project requirements, and timeout/webhook recovery without calling providers or claiming generated assets. These are package/behavior checks, not a live application certification. No paid provider generation, deployment, or runtime integration test was performed.

Report a table of requested capability IDs with implemented/configured/verified state, evidence location, and blocker. State live tests not performed and why. Show final artifacts, editable sources, actual spend or unresolved billing, and next action for each blocker.

For forward tests of this skill, give an independent agent a realistic user task and the package path without the desired verdict. Inspect its actual behavior. Repair cases where it invents capabilities, expands scope, asks redundant approval, loses state, or reports completion without evidence.
