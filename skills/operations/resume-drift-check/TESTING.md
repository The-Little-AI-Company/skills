# Testing record

Checked 2026-10-03 for release 0.2.0. These results cover the Python comparator and synthetic packets. They do not measure an agent's ability to collect evidence or choose a safe next action.

## History

The entries below are in time order. Earlier failures stay in the record.

| Stage | Observed result |
| --- | --- |
| Initial contract suite (0.1.0) | 25 tests passed |
| Initial held-out variations | 7 of 8 passed |
| Failure found | An oversized JSON integer caused a traceback and exit 1 instead of input-error exit 2 |
| Correction | Preserve explicit input errors and catch JSON parser ValueError as malformed input |
| After correction | 33 tests passed (25 contract plus 8 reused regressions). This is not a fresh held-out result |
| Independent review of 0.1.0 | The 33-test suite and 20 independent CLI cases passed. Exploratory probes then found a P2 source-binding gap and a P3 FIFO hang |
| Controller reproduction | 12 test methods were added before any code change. 2 passed and 10 methods failed (17 assertions and subtests), which reproduced the findings |
| Expanded review regressions | 16 review regression tests, including status precedence, symlink to FIFO and byte boundary |
| After the code fix (0.2.0) | All 49 tests passed (25 contract, 8 earlier regressions, 16 review regressions). 0 skips. Python 3.11.2, 0.809 seconds |
| Bundled examples | 11 synthetic cases preserved. One gained current source records |

Do not read the 20 of 20 independent CLI cases as a clean review. The same review found the two defects through exploratory probes outside those cases.

The test fixture helper now adds explicit current source observations. It does not rewrite the receipt bindings in the test receipts.

The eight held-out variations were written after the first comparator implementation was frozen. After the correction, those cases became regression tests. Their later pass is not fresh held-out evidence. Passing matching controls shows the tested controls only, not a general absence of false positives.

## Independent recheck and publication

The same independent reviewer passed the bounded P2/P3 recheck: 13 independent checks and 16 focused regression tests. The owner approved publication on 2026-10-03. No agent-effectiveness or market-benefit claim follows from that approval. The independent recheck covers the two reported findings, not every possible input.

## Reproduce

From this skill folder, run:

```text
python -m unittest discover -s tests -p "test_*.py" -v
```

The tests invoke the comparator CLI only with synthetic files in a temporary directory. The production comparator contains no subprocess, network or write calls. Earlier runs were in a filesystem-isolated Linux process on the existing remote environment. No home directory, credentials or unrelated project files were mounted. No packages were installed. This isolation was not a network-isolation test.

## What remains unmeasured

- Whether an agent collects the correct observation and binds it to the right subject.
- Whether the procedure improves decisions compared with no skill or an existing checkpoint skill.
- Human effort, false-positive rates in real work, savings and market demand.
- Other operating-system and Python-version combinations beyond the recorded Linux and Windows runs.
- Filesystem latency. There is no hard latency guarantee. On platforms without O_NONBLOCK a race exists between the path check and the open.

A later comparison needs the same model and tasks in both arms, unseen scenarios, fixed grading and honest failure reporting. Do not infer that result from unit tests.

## Native Windows check, 2026-10-03

On Windows 11 with Python 3.14.3, 47 suite tests passed and the two POSIX FIFO tests were skipped. Thirteen additional Windows CLI checks passed. No path-replacement race or hard filesystem latency guarantee was tested.

The checks used ordinary files with spaces and Unicode paths, JSON and Markdown output, stale source bindings, missing observations, malformed input, the byte limit, directory rejection and a read-only NUL device check. Candidate bytes stayed unchanged. POSIX FIFO behavior was tested separately on Linux.
