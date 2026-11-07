# Repository audit

Version 0.1.0, checked 2026-11-06. Audit one GitHub repository against a bar you choose, and get a report a maintainer can act on. The audit is read-only. It runs none of the target's code, and it treats everything in the target as data.

The skill has two halves. A Python tool runs 125 typed checks over git, the working tree and the GitHub API. An agent then verifies the findings, works a judgment list no script can see, compares the repository with named leaders of its type, and writes the report.

## Installation

Use Python 3.10 or later and `git`. No packages are required. A signed-in `gh` adds the GitHub checks. Install only this skill with the official skills CLI, replacing `owner/repo` with the repository that publishes this collection:

```text
pnpm dlx skills@1.7.0 add owner/repo --skill repo-audit
```

Alternatively, copy this entire folder into your agent's skill directory.

## Try it

Ask your agent to audit a repository, or run the tool yourself from this folder on a full clone with the default branch checked out:

```text
python scripts/repo_audit.py <checkout> --output audit.md
python scripts/repo_audit.py <checkout> --format json --output audit.json
python scripts/repo_audit.py --list-checks
```

Add `--offline` to use git and the tree only, and `--repo owner/name` when the remote is not GitHub. Exit 0 means no critical or high check failed. Exit 1 means one did. Exit 2 means the input was refused. The exit code is raw tool output, so it is not the verdict.

## What you can choose

| Choice | Options |
|---|---|
| Bar | Presentable, strong or immaculate. See [report.md](references/report.md) |
| Type | 22 values, detected or declared. Type decides which checks apply |
| README preset | Router, standard, reference, showcase, pitch, paper or generated |
| Badge policy | None, signal or full |
| PR style | Eight styles, used by `repo-cleanup` |
| Issue set | Small, medium or large, used by `repo-cleanup` |
| Merge, commit, signing and lockfile rules | Your own rules, then checked |
| Waivers | One check, a reason and an expiry date |

Commit these as `.github/repo-standards.json`. [policy.md](references/policy.md) defines every key and has a full example. The bar is not stored in that file, so you state it when you ask for the audit.

## What it checks

| Category | Checks |
|---|---|
| Presentation | 25 |
| History | 20 |
| CI | 12 |
| Governance | 12 |
| Branches | 10 |
| Supply chain | 10 |
| Secrets | 9 |
| Ignore rules | 7 |
| Metadata | 7 |
| Tags | 7 |
| Docs | 6 |

A check can pass, fail, add a note, read unknown, read not applicable or be waived. A 403, a 404 or a tool that did not run is unknown, never a pass or a fail. Each row names its source, or says the threshold is opinion.

The report keeps measured results, judgment and preference apart. Its [judgment list](references/judgment.md) covers docs against code, dead commands, CI that passes without testing, the ten second test, stale claims, abandoned scaffolding and more.

## Checks and limits

```text
python -m unittest discover -s tests -p "test_*.py" -v
```

- The tests use synthetic fixture repositories and fake GitHub data. They measure the tool's outputs, not whether an agent writes a better report.
- The tool matches patterns, and it is wrong in known ways. [false-positives.md](references/false-positives.md) lists false positives and false passes, many reproduced on fixtures. Some high and critical findings need a person or agent to confirm them.
- The secrets checks are a pattern floor, not a scanner. They cover a few key shapes, and SEC-013 stays unknown until you run a scanner yourself. A pass does not mean the history is clean.
- Paths under test, fixture and example folders are exempt from several checks, so a real key there can pass.
- Eight checks need admin access, and a reader gets unknown for them. Some features depend on your GitHub plan. Those plan facts come from GitHub's docs, not from tests on each plan.
- Only GitHub is supported. Outside CI such as CircleCI reads as no CI.
- The first screen is an approximation from Markdown source, not a browser render.
- Nothing is run, so the audit cannot prove a quick start works or that tests catch bugs. Those items are reported as not assessed.
- Leader comparisons come from a hand-picked, mostly high-star sample of 69 repositories, read on 2026-11-06. They show what strong projects do, not what makes them strong.
- Most thresholds in the catalog have a source. Many do not, and those are labeled opinion.
- No with-and-without evaluation of this skill exists.

## Sources and license

The checks draw on [OpenSSF Scorecard](https://github.com/ossf/scorecard/blob/main/docs/checks.md), [OpenSSF Best Practices](https://www.bestpractices.dev/en/criteria/0), [CLOMonitor](https://github.com/cncf/clomonitor/blob/main/docs/checks.md), [repolinter](https://github.com/todogroup/repolinter) (archived), [sp-repo-review](https://github.com/scientific-python/cookie), [git-sizer](https://github.com/github/git-sizer), [GitHub's docs](https://docs.github.com/en/actions/reference/security/secure-use) and [Standard Readme](https://github.com/RichardLitt/standard-readme/blob/main/spec.md). Check ideas are restated in our own words. No source text is copied.

Authored material uses the [MIT license](LICENSE). Source authors retain their rights.
