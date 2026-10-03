---
name: resume-drift-check
description: Compare a saved task claim with separately supplied observations before resuming interrupted work. Use when scope, tested bytes, process identity, action outcomes or approval identity may have changed. Do not use for automatic recovery or ordinary checkpoint writing.
---

# Resume drift check

Version 0.2.0. Agent effectiveness has not been evaluated.

Use this skill for one bounded resume decision. The user or agent supplies observations collected through already authorized, read-only tools. The comparator does not collect live state or authenticate evidence. It performs no network call or mutation.

## Bound the decision

1. Read the current user scope and the saved handoff. Preserve exclusions and existing permissions.
2. Identify the claims that affect the next action. Use a stable subject and claim ID. Do not turn omitted state into an assumption.
3. Collect relevant observations without changing the target. If the needed read is denied, record missing evidence. Do not request wider access merely to fill the packet.
4. Build the two JSON packets described in [README.md](README.md). Record where each observation came from and when it was collected. Exclude secrets and personal data.
5. Run the comparator once on those packets. Read every non-match and the notice before deciding what to do next.

```text
python scripts/drift_check.py checkpoint.json observed.json --format md
```

Exit 0 means the listed claims match the supplied evidence. It grants no permission. Exit 1 means at least one claim needs attention. Exit 2 means the input or command is invalid.

## Collect evidence that fits the claim

- A commit ID does not describe uncommitted bytes. A tree digest must cover the selected paths and contents, including relevant untracked files. Define that scope in the subject.
- For a test claim, collect a current head observation and a current tree observation as separate reads, using the exact same subject string as the test claim. Provide exactly one of each. Do not copy the head or tree from the test receipt. Do not edit the receipt to agree with current source. A missing, duplicate, invalid or stale source gives UNKNOWN, so record the missing read instead of filling it in.
- Bind a test result to its command, commit and relevant-source digest. A log's own hash does not prove the tested files stayed unchanged.
- Identify a process with PID, start token and owner. A reused PID or similar process name cannot establish ownership. A starting process is unresolved, not a reason to launch another.
- Bind an approval to the exact artifact hash. A changed artifact needs review of the new bytes.
- A connected label does not prove a successful model call. Record a bounded successful-call receipt only if the current authorization permits that call.
- Record external action outcomes as uncertain when completion cannot be verified. Do not repeat an action to discover whether it completed.

## Interpret the report

MATCH covers the listed claim and supplied bindings. DRIFT marks a changed value. STALE marks a test or approval whose binding changed. For a test, STALE also marks a receipt binding that differs from the current head or tree. UNKNOWN means the available evidence cannot support a match. That includes a test with no usable current source. DO_NOT_REPEAT puts a completed or uncertain action on hold.

A hold is not proof that an action completed. Verify its present effects through an authorized read. A reverted effect, missing receipt or changed operation identity needs a fresh decision from the owner of that action. The report does not authorize execution, retries, cleanup or publication.

Timestamp checks only compare supplied times. Source labels and time labels are unauthenticated. They do not establish that the observations are fresh now. Stop if the packets have become stale during the decision.

## Limits and alternatives

This skill cannot guarantee durable execution, exactly-once effects or incident prevention. It does not restore processes, manage checkpoints or preserve files. Use the existing checkpoint system for those tasks.

[Context Continuity](https://github.com/wangyuqin378-cpu/context-continuity) already checks checkpoint integrity, cited evidence files and writer locks. This candidate compares explicit task claims with supplied observations. The overlap and the effort of collecting observations must be considered before adoption. No with/without-skill evaluation or measured savings exists.
