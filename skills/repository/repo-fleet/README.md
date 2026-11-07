# Repository fleet

Version 0.1.0, checked 2026-11-06. Audit and improve many repositories at once, with one typed inventory, shared fixes first, pilots, ringed rollouts and stop rules. Two Python scripts read GitHub through `gh`. Neither one changes anything on GitHub.

## Installation

Use Python 3.10 or later and an authenticated [GitHub CLI](https://cli.github.com/). No Python packages are required. Install only this skill into a project with the official skills CLI:

```text
pnpm dlx skills@1.7.0 add <owner>/<repo> --skill repo-fleet --agent codex
```

Replace `<owner>/<repo>` with the repository that hosts this skill. Omit `--agent codex` to choose another supported agent interactively. Alternatively, copy this entire folder into the agent's existing skill directory.

## Try it

Run these commands from this folder. The first one reads a public organization and writes one local file.

```text
python scripts/fleet_scan.py ossf --output fleet.json
python scripts/fleet_track.py campaign.tsv --output campaign.tsv
```

On a fleet you cannot write to, every repository is out of scope with the reason `no_write_access`. That is the expected result. To try the tracker, make a TSV with the header below and one row whose `pr_url` is any public pull request.

## fleet_scan.py

```text
python scripts/fleet_scan.py <owner> [--output fleet.json] [--include-archived] [--include-forks] [--limit N]
```

It sends one constant GraphQL query, built from constants at import. The owner, page size and cursor travel as variables. The script refuses to load if that query is not a read query, and it has no way to accept another. The owner must look like a GitHub login.

`fleet.json` holds every repository the scan read, in scope or not. `schema_version` is 1. The top level has `owner`, `scanned_at`, `complete`, `stop_reason`, `limited`, `warnings`, `reported_total`, `read_total`, `in_scope_total`, `page_sizes_used`, `graphql_points`, `rate_limit_events`, `owner_defaults_repository` and `repositories`.

Each repository has these fields:

| Field | Meaning |
| --- | --- |
| `name`, `visibility`, `default_branch`, `pushed_at` | As GitHub reports them |
| `archived`, `fork`, `mirror`, `template`, `empty` | Booleans |
| `disk_usage_kb`, `stars`, `topics_count` | Numbers |
| `license`, `primary_language` | SPDX ID and language name, or null |
| `description_present` | Boolean. The description text is not stored |
| `viewer_permission` | `ADMIN`, `MAINTAIN`, `WRITE`, `TRIAGE`, `READ` or null |
| `files` | Path found for each key, null if absent, or null for the whole object on an empty repository |
| `in_scope`, `out_of_scope_reasons` | Reasons are `archived`, `fork`, `mirror` and `no_write_access` |

File keys are `readme`, `license`, `security`, `contributing`, `codeowners`, `dependabot`, `gitignore`, `gitattributes`, `workflows`, `issue_templates` and `pr_template`.

A null file means absent from the repository, not missing. `security`, `contributing`, `issue_templates` and `pr_template` can be inherited from the owner's public `.github` repository, and `owner_defaults_repository` says whether one exists. It is `public`, `not public`, `absent` or `unknown`.

Exit 0 means a finished scan, or one that stopped cleanly at `--limit`. Exit 1 means a partial scan, and `fleet.json` still holds what was read. Exit 2 means bad input, an unknown owner or an unusable `gh`.

## fleet_track.py

```text
python scripts/fleet_track.py <campaign.tsv> [--output path] [--damage RING] [--secondary-hits RING=COUNT]
```

The TSV is tab separated with no quoting. It needs these columns, in any order, and keeps any others you add:

```text
repo	finding	change	risk	ring	plan_hash	pr_url	state	ci	last_check
```

For each row with a `pr_url`, the script calls `gh pr view` and updates `state`, `ci` and `last_check`. It writes the file atomically. A `pr_url` must be a `https://github.com/` pull request URL. Any other value never reaches `gh`, and the row is reported.

| Column | Values the script writes |
| --- | --- |
| `state` | `draft`, `open`, `merged`, `closed` or `unknown` |
| `ci` | `passing`, `failing`, `pending`, `none` or `unknown` |

Set `state` to `declined` or `explained` on a closed pull request and the script keeps it. `declined` still counts as closed unmerged. `explained` does not, which clears a closure you have accounted for.

| Stop rule | How it is evaluated |
| --- | --- |
| More than 10 percent of a ring failed CI | Measured from the TSV. Exactly 10 percent does not stop |
| Pull requests closed unmerged | Measured. Two or more in a ring stops. The number is opinion, because the skill gives none |
| Secondary limit twice in a ring | Counts limits seen during this run plus `--secondary-hits`. It cannot see limits your campaign tool hit |
| Anyone reports damage | Only from `--damage` |

The report never says a ring passed. It says no measured rule fired, and it lists the manual checks.

Exit 0 means no rule fired and every row refreshed. Exit 1 means a rule fired or a row could not be refreshed. Exit 2 means bad input or an unusable `gh`, and the file stays as it was.

## Checks and limits

```text
python -m unittest discover -s tests -p "test_*.py" -v
```

All 79 tests passed on Windows 11 with Python 3.15.1. They stub `gh` with a fake runner. They were not run on Linux.

Both scripts also ran once against public GitHub with `gh` 2.102.1. `fleet_scan.py` read all 85 `ossf` repositories in 14 seconds for 2 GraphQL points, at page size 50. It also read 120 of the 1,148 `sindresorhus` repositories with `--limit`. `fleet_track.py` refreshed one merged `ossf/scorecard` pull request. An earlier run with one lookup per path hit real HTTP 502 replies and stepped through page sizes 50, 25 and 10 with this retry code. No real rate limit was hit, so that handling rests on the tests and on GitHub's documented error shapes.

The scan looks in the root, `.github` and `docs` folders only. It reads folder listings and matches names, because one `object()` lookup per path returned HTTP 502 at page size 50. See [references/limits.md](references/limits.md). The folder lookups measure presence, not whether a file is any good. Mirrors have no include flag, so they stay out of scope. Their records remain in `fleet.json`.

Thresholds in the tracker are opinion. This skill has no with-and-without evaluation, and nothing here measures whether a campaign improves a fleet.

## Sources and license

GitHub's limits, ruleset and default file behavior come from GitHub's documentation, linked from [references/limits.md](references/limits.md) and [references/shared-fixes.md](references/shared-fixes.md). Tool facts link to each project in [references/tools.md](references/tools.md).

Authored material uses the [MIT license](LICENSE). Source authors retain their rights.
