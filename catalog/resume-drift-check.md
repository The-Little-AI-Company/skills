# Resume drift check

Id: resume-drift-check. Category: Recovery checks. Status: Published. Version 0.2.0.

## What

This skill compares claims in a saved checkpoint against separately collected observations before an agent resumes work. It prints an advisory report.

It creates no checkpoint store and collects no live data. The operator supplies the evidence. That evidence can be wrong or stale. Time and source labels are not authentication.

The skill is at skills/operations/resume-drift-check.

Claim kinds:

- head: the saved repository HEAD.
- tree: a digest of selected paths and file bytes, including relevant untracked content.
- test: a result bound to head, tree and command.
- action: an operation identity and its outcome.
- process: a PID, a start token and an owner.
- approval: an artifact hash.
- capability: an operation and a model successful-call receipt.

Missing evidence is never a match. For a test, its exact subject defines a source scope. Supply exactly one valid, timely current head and tree observation for that subject, collected separately from the historical test receipt. Missing, invalid or ambiguous current source gives UNKNOWN. A receipt that does not cover the current source gives STALE. HEAD alone cannot validate a test run on changed uncommitted bytes.

Labels are MATCH, DRIFT, STALE, UNKNOWN and DO_NOT_REPEAT. A completed or uncertain action stays on hold. An observation for a different subject cannot establish its outcome.

## When to use

Use it for a bounded resume decision when evidence is available.

Avoid it for trivial disposable tasks. Do not use it as automatic recovery, as exactly-once execution or as a security guarantee. Never use it to justify replaying an action with an uncertain outcome.

## Installation

Install this skill only with the official CLI:

```text
pnpm dlx skills@1.7.0 add The-Little-AI-Company/skills --skill resume-drift-check --agent codex
```

Run from the target project. You can also copy the complete skill folder into the agent's existing skill directory.

The tool needs Python 3.10 or later and the standard library only:

```
python scripts/drift_check.py checkpoint.json observed.json --format md
```

Inputs must be local regular JSON files. FIFO, directory and device inputs are rejected with exit 2. There is no hard filesystem latency guarantee. On Windows 11 with Python 3.14.3, 47 suite tests passed and the two POSIX FIFO tests were skipped. Thirteen additional Windows CLI checks passed. No path-replacement race or hard filesystem latency guarantee was tested. It reads only those two files and prints a report. It performs no mutation, subprocess, network call, cleanup, restart or action replay.

Exit code 0 means every listed claim matched. Exit code 1 means at least one claim did not match. Exit code 2 means invalid input. An example that exits with 1 can be working as intended. An all-match result is advisory and is never permission to act.

The operator must collect the observations by hand. That manual collection cost is unmeasured.

## Example

This example is synthetic.

A saved checkpoint records one HEAD. The observed HEAD is different. The checkpoint also records an action that may have completed before the interruption.

The report shows DRIFT for the head claim and DO_NOT_REPEAT for the action. The advice is STOP_AND_VERIFY_OUTCOME. The operator verifies the outcome through an authorized read-only observation. The agent does not repeat the action automatically.

## Limits

- It trusts the files the operator supplies.
- It cannot detect false evidence.
- It does not authenticate time labels or source labels.
- It does not store checkpoints or gather observations.
- Adoption effort is unmeasured.
- Overlap exists with other tools. Context Continuity already has evidence-file hash checks, bound reviews, checkpoint chains and writer-lock liveness. The narrow hypothesis here is comparing task claims with supplied task observations. Three tools were compared. This is not an exhaustive market map.

## Evaluations

Actual Paperclip recovery work motivated the procedure. No with-skill and without-skill evaluation exists. Marketability and collection effort remain unmeasured.

Version 0.1.0: 25 contract tests passed. Initial held-out variations passed 7 of 8 and found an oversized-integer input error. After repair all 33 passed. The reused eight are regression evidence.

Independent review of 0.1.0 passed 33 suite tests and 20 independent CLI cases, then found a source-binding gap and FIFO hang through exploratory probes. That review held the candidate.

Version 0.2.0: 49 tests passed on 2026-10-03, comprising 25 contract, 8 earlier regression and 16 review regression tests. Both original review inputs now exit 1. With current head supplied, changed bytes mark the test STALE. The same reviewer passed the bounded recheck with 13 independent checks and 16 focused regressions.

The 11 bundled cases are synthetic. No agent-effectiveness, savings or market validation exists. Evidence-collection effort and real-world benefit remain unmeasured.

Public issue requests are problem signals. They are not purchase intent.

## Sources

- Context Continuity: https://github.com/wangyuqin378-cpu/context-continuity
- Context checkpoint skill: https://github.com/jdmnk/context-checkpoint-skill
- Handoff skill: https://github.com/mattpocock/skills/tree/main/skills/productivity/handoff
- Problem signal: https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/issues/93
- Problem signal: https://github.com/CherryHQ/cherry-studio/issues/16658

## Version

0.2.0, published on 2026-10-03.

## License

Authored code and documentation use the MIT license, matching the collection. The same independent reviewer passed the bounded P2/P3 recheck: 13 independent checks and 16 focused regression tests. The owner approved publication on 2026-10-03. No agent-effectiveness or market-benefit claim follows from that approval. See the [change history](../skills/operations/resume-drift-check/CHANGELOG.md).
