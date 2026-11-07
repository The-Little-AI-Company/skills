# Branch triage

Read this in step 6, before you propose any branch for deletion.

`scripts/branch_triage.py` classifies and never deletes. Deletion is the owner's call, in small batches, after a yes.

```text
python scripts/branch_triage.py <checkout> --output ledger.tsv
```

The checkout must be a full clone or a mirror. Shallow and partial clones exit 2, because the proofs need every object. A mirror is best: `git clone --mirror`. Put `--output` outside the repository. The tool refuses a path inside it, and refuses to overwrite an old ledger.

Output is a TSV of `verdict`, `sha`, `date`, `name`, oldest first. Exit 0 means every branch is a keep. Exit 1 means at least one needs a human, or a data source was missing. Exit 2 means bad input.

Without `gh`, or with `--offline`, the tool cannot see open pull requests. A branch with an open PR can then read `ANCESTOR`. The run warns and exits 1. Check open pull requests yourself before you act on an offline ledger.

Flags: `--base` names the default branch, `--repo` names `owner/name` for `gh`, `--remote` names the remote, and `--keep GLOB` protects more names, such as long-lived branches. The tool reads each branch's tip from `refs/heads` and from the remote. If the two differ, a keep verdict on either tip wins.

## Verdicts

The tool applies these in this order and stops at the first match. The first six need PR data, except the name rules.

| Verdict | Meaning | What you do |
|---|---|---|
| `KEEP-default` | The default branch | Never touch |
| `KEEP-managed` | Queue, bot or release naming, a `--keep` match, a protected branch, or a ruleset that blocks deletion | Never touch. Rulesets are read only for branches that would otherwise be proposed |
| `KEEP-open-pr` | Head of an open pull request | Never touch |
| `KEEP-open-pr-base` | Base of an open pull request | Never touch |
| `CANDIDATE-merged-pr-tip` | A PR merged into the default branch, and its head SHA equals this tip | Best signal. Propose |
| `KEEP-work-after-merge` | A PR merged, but the tip moved after that | The tip holds newer work. Keep it and tell the owner |
| `ANCESTOR` | The tip is an ancestor of the default branch | The only git proof with no caveat. Propose, once you have checked open PRs |
| `PATCHES-ALL-APPLIED` | Every commit has a patch equivalent on the base | **Never a delete signal on its own.** Reverted work reads as applied. Show a human |
| `SQUASH-EQUIVALENT` | A synthetic squash of the branch matches a commit on the base | The change was on the base at some point, and it may have been reverted since. Show a human, then propose |
| `KEEP-UNIQUE-WORK` | Nothing proves it merged | Keep. This includes a squash that needed conflict resolution, because only PR data can prove that one |

Each of the last four comes from a local proof. Any failed read falls to `KEEP-UNIQUE-WORK`, which is the safe direction.

## Why these proofs

Nine branch shapes were built on git 2.56.0. The tool's tests build the same nine.

| Branch shape | `--merged` | Truth | Verdict without PR data |
|---|---|---|---|
| Fast-forward merged | yes | merged | `ANCESTOR` |
| Same tip as main | yes | nothing unique | `ANCESTOR` |
| Squash-merged, 2 commits | no | merged | `SQUASH-EQUIVALENT` |
| Squash-merged, main later rewrote the line | no | merged | `SQUASH-EQUIVALENT` |
| Rebase-merged, 2 commits, main moved | no | merged | `PATCHES-ALL-APPLIED` |
| Squash-merged, conflict resolved at merge | no | merged | `KEEP-UNIQUE-WORK` |
| Squash-merged, then reverted | no | merged then undone | `PATCHES-ALL-APPLIED` |
| Squash-merged, then more commits pushed | no | has unmerged work | `KEEP-UNIQUE-WORK` |
| Never merged | no | unmerged | `KEEP-UNIQUE-WORK` |

- `git branch --merged` finds only the two trivial cases. It misses every squash and rebase merge.
- [`git cherry`](https://git-scm.com/docs/git-cherry) works by patch equivalence, so a reverted squash reads as applied, and a squash that needed conflict resolution will not match.
- Patch ids ignore some whitespace (inferred), so read the diff before you trust either patch verdict on a whitespace-sensitive file.
- [`git merge-tree --write-tree`](https://git-scm.com/docs/git-merge-tree) is a useful second opinion, since a no-op means merging would change nothing. It reports conflicts for branches that were merged and later changed, so it cannot stand alone.
- Branch age proves nothing. GitHub [labels a branch stale after three months](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/viewing-branches-in-your-repository) with no commits. Age alone never justifies deletion.

The tool tightens the report's method in three ways. A merged PR counts only if it merged into the default branch. A branch that holds a merge commit skips `PATCHES-ALL-APPLIED`, because `git cherry` ignores merges. An empty or failed `git cherry` never reads as applied.

The synthetic squash needs `git commit-tree`, which writes an object. The tool writes it to a temporary object directory through `GIT_OBJECT_DIRECTORY` and reads the real objects through `GIT_ALTERNATE_OBJECT_DIRECTORIES`, so the audited clone gains nothing.

## Rules that never lose work

1. Never delete from a single signal.
2. Never delete a default, protected, ruleset-covered or release branch, an open PR's head or base, or anything under `gh-readonly-queue/`, `dependabot/` or `renovate/`.
3. Require a merged PR whose head SHA equals the current tip, or a clean local proof. If the tip differs from the merged head, the branch has newer work, so keep it.
4. Save the ledger outside the repository before any delete. The SHA is what makes a deleted branch recoverable.
5. Delete in small batches with the owner's approval. Print the plan and stop.
6. Recheck each tip right before deletion. If the SHA differs from the ledger, the branch moved, so skip it.

## Limits of the data

- PRs opened from forks are not associated with branches in the base repository. A cross-repository PR's head name is ignored, because a fork can use any name.
- The query reads 10 PRs per branch. A missed merged PR can only make a branch keep longer. Open PRs also come from a separate list, so a busy branch is still seen.
- That list stops at 10,000 open PRs, and the run warns if it hits the limit.
- If a ruleset read fails, the run warns and exits 1. Check `repos/$R/rules/branches/NAME` by hand.
- PR data reflects the moment of the run, so rerun before a delete that comes days later.

## Deleting, after the owner's yes

Offer the plan as commands for the owner, or run them only on an explicit yes for those names. Delete one batch, then check for damage.

```bash
git push origin --delete branch-name
```

## Restoring

A deleted branch comes back from its SHA in the ledger:

```bash
gh api -X POST repos/$R/git/refs -f ref=refs/heads/NAME -f sha=SHA
```

**Not run.** Neither deletion nor this restore call was tested. The commits may stay available only until GitHub collects them, and no source gives a time limit (inferred). Restore soon, or keep a mirror.

[GitHub can restore the head branch of a closed PR](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/deleting-and-restoring-branches-in-a-pull-request). That covers branches attached to PRs. Branches with no PR rely on the ledger.

## Tags

Never move a published tag. Consumers and pins rely on it. To audit tags, read TAG-001 to TAG-007 from `repo-audit`. To protect them, use the tag ruleset in [settings.md](settings.md).

## Stop it recurring

Turn on delete-branch-on-merge, in [settings.md](settings.md). It removes the problem for same-repository branches. GitHub warns that [continuing work on a head branch after a squash merge](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/about-merge-methods-on-github) leads to confusing later PRs.

## Sources

All read 2026-11-06. The nine-shape table was measured with git 2.56.0 on Windows, and the tool's tests rebuild it. A live run of the method on `ossf/scorecard` covered 40 branches and gave 0 delete candidates.

- [Merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue), for the `gh-readonly-queue/` prefix
- [Automatic branch deletion](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-the-automatic-deletion-of-branches)
- [Rules for a branch](https://docs.github.com/en/rest/repos/rules#get-rules-for-a-branch)
