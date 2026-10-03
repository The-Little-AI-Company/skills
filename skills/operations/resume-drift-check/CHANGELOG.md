# Changelog

## 0.2.0 (2026-10-03)

Published for bounded trials. Packet schema stays at version 1 because no field was added.

### Why

An independent review of 0.1.0 passed the 33-test suite and 20 independent CLI cases. Exploratory probes then found two defects. Do not read the 20 of 20 result as a clean review.

- P2: a test could MATCH without any check of the current head and tree. Its receipt binding was never compared with current source.
- P3: a FIFO given as an input path could hang the comparator.

### Changed: source scope for test claims

The exact subject string defines a source scope with no normalization. A test claim can MATCH only when the observations hold exactly one valid, timely head and exactly one valid, timely tree for that subject. Duplicates, even identical ones, give UNKNOWN. An absent, invalid or stale source gives UNKNOWN. Then the receipt binding is compared with those current values, and a mismatch gives STALE. Then the earlier receipt result, binding and command checks apply. A packet with only test observations cannot MATCH. A source for an unrelated subject stays independent. Head-only and tree-only claims keep their old meaning.

### The two review cases

Case 1. The current head is present. The saved tree is A. The current tree is B. The test receipt binds to A.

- 0.2.0 result: tree DRIFT and test STALE.

Case 2. The current head is present. Both packets hold tree B. The test receipt binds to A.

- 0.2.0 result: tree MATCH and test STALE, exit 1.
- Before 0.2.0 the result was tree MATCH and test MATCH, exit 0.

Case 3. The original review inputs have no current head observation.

- 0.2.0 result: test UNKNOWN, exit 1.

This is a behavior change. A packet that earlier gave a test MATCH without current source now gives UNKNOWN or STALE. A historical receipt did not become invalid input. A missing current source is UNKNOWN and is not a file error.

### Changed: input reading

- Inputs must be regular local UTF-8 JSON files of at most 1 MiB.
- The comparator uses nonblocking os.open where available and calls fstat on the descriptor before it reads.
- A FIFO, directory or device is rejected with exit 2. This includes a symlink to a FIFO.
- Where O_NONBLOCK is missing, the comparator checks regularity first and still calls fstat. A race remains between the path check and the open.
- There is no hard latency guarantee for filesystem I/O.
- On Windows 11 with Python 3.14.3, 47 suite tests passed and the two POSIX FIFO tests were skipped. Thirteen additional Windows CLI checks passed. No path-replacement race or hard filesystem latency guarantee was tested.

### Unchanged

- The production comparator is read-only. It has no network call, subprocess or write.
- The demo helper writes synthetic files and refuses to overwrite.
- No new package and no global install.
- Matching claims grant no authority to act.

### Notes for users

Receipt fields are historical assertions. Never edit them to agree with current source. Source labels and time labels are unauthenticated. Collect current head and tree observations separately and do not copy them from the receipt.

### Tests

All 49 tests passed (25 contract, 8 earlier regressions, 16 review regressions) with 0 skips on Python 3.11.2 in 0.809 seconds. Eleven synthetic example cases are preserved and one gained current source records. The test fixture helper adds explicit current source observations without rewriting test receipt bindings. See [TESTING.md](TESTING.md) for the full failure history.

### Status

The same independent reviewer passed the bounded P2/P3 recheck: 13 independent checks and 16 focused regression tests. The owner approved publication on 2026-10-03. No agent-effectiveness or market-benefit claim follows from that approval. No claim is made about agent effectiveness, marketability or savings.

## 0.1.0 (2026-10-03)

First private candidate. 25 contract tests passed. One held-out failure, an oversized JSON integer, was corrected and then 33 tests passed.
