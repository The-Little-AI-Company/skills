# Resume drift check

Version 0.2.0, checked 2026-10-03. Compare a saved task claim with separately supplied observations. The Python script reads two files and prints advice. It performs no network call, process launch or mutation.

## Installation

Use Python 3.10 or later. No packages are required. Install only this skill into a project with the official skills CLI:

```text
pnpm dlx skills@1.7.0 add The-Little-AI-Company/skills --skill resume-drift-check --agent codex
```

Run that command from the project where you want the skill. Omit `--agent codex` to choose another supported agent interactively. Alternatively, copy this entire folder into the agent's existing skill directory. The comparator itself needs no third-party Python packages.

## Try the synthetic example

Run these commands from this folder. The helper creates two synthetic example input files in the current directory and refuses to overwrite existing files. The comparator itself does not write files.

```text
python examples/make_demo.py
python scripts/drift_check.py checkpoint.json observed.json --format md
```

The example combines a changed commit with an uncertain action. Expected labels are DRIFT and DO_NOT_REPEAT. Expected advice is STOP_AND_VERIFY_OUTCOME. Exit 1 is the expected result. Verify the outcome through an authorized read instead of repeating the action.

## Input contract

`checkpoint.json` has schema_version 1, saved_at in UTC ISO8601 ending Z, and a nonempty claims array. `observed.json` has schema_version 1, an as_of time and an observations array. An empty observations array is valid missing evidence. An empty file or object is invalid input. The packet schema stays at version 1 in release 0.2.0 because no field was added.

Every item has id, kind, subject, value and binding. Observations also have a nonempty source label, observed_at and evidence set to receipt or metadata. Match IDs and subjects exactly. The examples in [cases.json](examples/cases.json) show complete packets.

| Kind | Value | Binding |
| --- | --- | --- |
| head | 40 or 64 lowercase hex commit ID | Empty object |
| tree | 64 lowercase hex digest of relevant paths and bytes | Empty object |
| test | passed or failed | head, tree, command |
| action | outcome and idempotent | operation_id |
| process | state | pid, start_token, owner |
| approval | granted or denied | artifact_sha256 |
| capability | success or failure | operation, model |

Action outcomes are done, not_started or uncertain. Idempotent is true, false or null. Process states are running, starting or missing. A missing process uses an empty binding. Do not infer process ownership from its name.

Test, action, approval and capability observations require receipt evidence. Receipt is a supplied label, not authenticated proof. Tree digests must cover the selected file paths and contents, including relevant untracked files. A list of dirty paths alone is insufficient.

Files must be regular local UTF-8 JSON files, at most 1 MiB each, with no duplicate keys. Each array has at most 100 items. Missing evidence becomes UNKNOWN. Unknown fields produce diagnostic rows. Malformed required IDs, packet timestamps and schema versions are input errors.

### File reading

The comparator opens each input with nonblocking os.open where the platform provides O_NONBLOCK. It calls fstat on the open descriptor before it reads. A FIFO, directory or device is rejected with exit 2. A symlink that points to a FIFO is also rejected. Where O_NONBLOCK is missing, the comparator checks that the path is a regular file first and still calls fstat. That path has a race between the path check and the open. There is no hard latency guarantee for filesystem I/O. On Windows 11 with Python 3.14.3, 47 suite tests passed and the two POSIX FIFO tests were skipped. Thirteen additional Windows CLI checks passed. No path-replacement race or hard filesystem latency guarantee was tested.

## Source scope contract

This contract applies to test claims. It was added in 0.2.0.

1. The exact subject string of a test claim defines its source scope. The comparator applies no normalization. Case, spacing, slashes and trailing characters all count.
2. For a test claim to MATCH, the observations must hold exactly one head observation and exactly one tree observation for that exact subject.
3. Both must be valid and timely under the existing supplied-time rules.
4. Duplicates give UNKNOWN, even when the duplicates are identical. An absent, invalid or stale head or tree also gives UNKNOWN.
5. Only then is the receipt binding compared with those current source values. A mismatch gives STALE.
6. Only then do the prior receipt checks apply: the result value, the other binding fields and the command.
7. A packet with only test observations can never MATCH.
8. A source observation for an unrelated subject stays independent. It neither helps nor blocks a test claim for another subject.
9. A head-only or tree-only claim keeps its earlier meaning.

Receipt fields are historical assertions. Never edit them to agree with current source. Source labels and time labels are unauthenticated. Collect the current head and tree observations separately. Do not copy them from the receipt to obtain a MATCH.

A missing current source is UNKNOWN. It is not a file error and it does not give exit 2.

## Time and outputs

The default age limit is 300 seconds relative to the supplied as_of time. Override it with `--max-age-seconds N`, where N is positive. The script does not use the current clock. Supply current observations and stop if they become stale before action.

Exit 0 means all listed claims matched. Exit 1 means attention is needed. Exit 2 means invalid input or usage. Use `--format json` for a deterministic structured report. Both formats state that matching claims do not authorize an action.

DO_NOT_REPEAT is a conservative hold for completed or uncertain actions. It does not prove completion. No report recommends replay, restart, termination, overwrite or publication.

## Checks and limits

```text
python -m unittest discover -s tests -p "test_*.py" -v
```

Execution results are recorded in [TESTING.md](TESTING.md). Release history is in [CHANGELOG.md](CHANGELOG.md). The fixtures are synthetic. Tests measure this comparator's outputs, not whether an agent collects correct evidence or makes better decisions. No with/without-skill evaluation, savings measurement or market validation exists. The same independent reviewer passed the bounded P2/P3 recheck: 13 independent checks and 16 focused regression tests. The owner approved publication on 2026-10-03. No agent-effectiveness or market-benefit claim follows from that approval.

The production comparator is read-only. It has no network call, no subprocess and no write. This procedure cannot guarantee durable or exactly-once execution. It relies on the operator's evidence, scope and authority. It does not replace a checkpoint store.

## Sources and license

The comparison considered [Context Continuity](https://github.com/wangyuqin378-cpu/context-continuity), [Context Checkpoint](https://github.com/jdmnk/context-checkpoint-skill) and [handoff](https://github.com/mattpocock/skills/tree/main/skills/productivity/handoff). Context Continuity already checks evidence-file hashes, review binding and writer-lock liveness. This candidate's narrower function is task-claim comparison. Three sources do not establish an exhaustive market map.

Authored material uses the [MIT license](LICENSE). Source authors retain their rights.
