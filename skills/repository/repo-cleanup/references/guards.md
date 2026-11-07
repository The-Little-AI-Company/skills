# Guards that keep a repository clean

Read this in step 8, before you add any check that outlives the cleanup.

A guard nobody reads is noise. Before you add one, name where its failure shows up and who sees it. If you cannot, skip it. Each guard is the owner's choice.

## What shows failures where

Rows marked inferred were not observed firing.

| Guard | Runs | Failure shows | Who sees it | Can be skipped by |
|---|---|---|---|---|
| Pre-commit hook | Author's machine, on commit | Terminal | Author only | `--no-verify`, or `SKIP=gitleaks`. Absent until each clone installs it |
| Required CI check | Pull request | PR merge box | Author and reviewers | A ruleset bypass actor |
| Optional CI check | Pull request | PR checks list | Whoever looks | Anyone can merge past it |
| [Push protection](https://docs.github.com/en/code-security/concepts/secret-security/push-protection) | GitHub, on push | Rejected push | The pusher. Bypasses raise alerts | Writers, by default |
| [Secret scanning](https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning) | GitHub, all history on all branches | Security tab | Admins and security managers | Off on private repositories without Secret Protection |
| Dependabot or Renovate | Schedule | A pull request | Reviewers | Unmerged PRs pile up to the limit |
| Scheduled audit | Schedule | Actions tab only, unless the job reports elsewhere | Nobody by default (inferred) | Disabled after inactivity |
| Ruleset | GitHub, on push or merge | Rejected push, PR merge box | The pusher or author | Bypass actors |
| Delete on merge | GitHub, on merge | Nothing, it acts | Nobody needs to | Fork PRs follow the fork's setting |
| CODEOWNERS errors | On request | `codeowners/errors` API | Nobody unless polled | Invalid lines are skipped silently |

Prefer a guard higher in the delivery path. A pre-commit hook is a courtesy to the author. A required check or push protection is the guarantee.

## Pre-commit secret scan

[gitleaks](https://github.com/gitleaks/gitleaks) ships hooks for [pre-commit](https://pre-commit.com/). Hook ids `gitleaks`, `gitleaks-docker` and `gitleaks-system` were read from its `.pre-commit-hooks.yaml` on 2026-11-06. Its entry runs `gitleaks git --pre-commit --redact --staged --verbose`.

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks
```

`v8.30.1` was the newest release on 2026-11-06. Pin the current one. Every contributor runs `pre-commit install`, so state that in CONTRIBUTING.md.

## CI checks

Add these as jobs in one workflow, then make them required once they are green.

| Check | Command | Catches | Source |
|---|---|---|---|
| Secret scan | `gitleaks git --redact --report-path gitleaks.json .` | Secrets in history | [gitleaks](https://github.com/gitleaks/gitleaks) |
| Workflow lint | `actionlint` | Workflow syntax and type errors | [actionlint](https://github.com/rhysd/actionlint) |
| Workflow security | `zizmor .github/workflows` | Injection and unsafe triggers | [zizmor](https://github.com/zizmorcore/zizmor) |
| Issue forms | `python scripts/validate_forms.py .` | Form errors before they reach users. Add it only where forms exist, since no forms exits 2 | This skill |
| Repository bar | `repo-audit` | Regressions against the chosen bar | The `repo-audit` skill |

gitleaks, actionlint and zizmor are MIT. None of the three commands was run by this skill's authors, so run each once by hand first. Triage the first findings before you make a check required.

Do not use trufflehog in CI without the owner's consent. Its verification sends found values to their providers. Treat unverified findings as unresolved, not as safe.

Pin every action in these jobs, by the recipe in [hygiene.md](hygiene.md).

## Scheduled audit

A schedule needs an objective, a place for results, and someone who reads them. Without those, do not add it.

```yaml
name: repository-audit
on:
  schedule:
    - cron: "17 6 * * 1"
  workflow_dispatch:
permissions:
  contents: read
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@FULL_SHA # exact version
        with:
          fetch-depth: 0
      - run: python path/to/repo_audit.py . --offline --format md >> "$GITHUB_STEP_SUMMARY"
```

Weekly is opinion. Replace `FULL_SHA` and the script path. The default token cannot see admin-only settings, so those checks read UNKNOWN. This workflow was not run.

Know these limits:

- On public repositories, [60 days with no activity disables scheduled workflows](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows). A quiet repository loses its audit silently. CI-003 in `repo-audit` catches a disabled workflow.
- Forks have schedules disabled by default.
- A failed schedule shows in the Actions tab. Decide who gets told, and say so in the pull request that adds it. A job that files an issue needs `issues: write`, and it creates one more thing to triage.

## Update tooling

Recipes are in [hygiene.md](hygiene.md). Each update tool makes pull requests that someone must review. Grouping keeps volume down. Without review, the limit of 5 open Dependabot PRs fills and updates stop (inferred from the default limit).

## Merge time guards

- Delete branch on merge removes leftover branches.
- A ruleset blocks force pushes and deletion.
- Required checks stop regressions.

Commands are in [settings.md](settings.md).

## Final check

1. Run `repo-audit` on the final head.
2. Compare it with the bar the owner chose.
3. Plant one mess on a throwaway branch, such as a fake key that passes for a real shape, and watch the guard fail. A suppressed example string can pass, so use a random value of the right shape, never a real credential.
4. Report what passed, what stayed open and what waits on the owner.

## Sources

All read 2026-11-06.

- [gitleaks](https://github.com/gitleaks/gitleaks), [its hook definitions](https://github.com/gitleaks/gitleaks/blob/master/.pre-commit-hooks.yaml), [trufflehog](https://github.com/trufflesecurity/trufflehog)
- [Disable and enable workflows](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows), [secret scanning availability](https://github.com/github/docs/blob/main/data/reusables/gated-features/secret-scanning.md), [Dependabot options](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference)
