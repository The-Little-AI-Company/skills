# Repository settings commands

Read this in step 5, before you hand the owner any setting change.

Settings belong to the owner. Print these commands, say what each one changes and what could break, and let the owner run them.

**No write command here was run by this skill's authors.** The read-backs were run with GET calls on 2026-11-06. Write endpoints and fields were checked against [GitHub's OpenAPI description](https://github.com/github/rest-api-description) and `gh repo edit --help` from gh 2.102.1. Run one on a test repository first if the owner is unsure.

Set these first. `export MSYS_NO_PATHCONV=1` is needed under Git for Windows, because it rewrites arguments that hold a slash. Write `repos/...` without a leading slash.

```bash
R=owner/repo
B=$(gh api repos/$R --jq .default_branch)
```

## Read before you write

A 404 is not a fail. Status codes below are from a non-admin reader on a public repository and an admin on their own.

| Read | Reader | Admin | Meaning for a reader |
|---|---|---|---|
| `repos/$R/rules/branches/$B` | 200 | 200 | Effective rules. Hides rulesets in evaluate mode |
| `repos/$R/rulesets` | 200 | 200 | Works. Bypass actors are not returned |
| `repos/$R/branches/$B/protection` | 404 | 200 | UNKNOWN, not unprotected |
| `repos/$R/vulnerability-alerts` | 404 | 204 | UNKNOWN. GraphQL `hasVulnerabilityAlertsEnabled` works |
| `repos/$R/automated-security-fixes` | 404 | 200 | UNKNOWN |
| `repos/$R/immutable-releases` | 404 | 200 | UNKNOWN |
| `repos/$R/private-vulnerability-reporting` | 200 | 200 | Works |
| `repos/$R/actions/permissions/workflow` | 403 | 200 | UNKNOWN |
| `repos/$R/code-scanning/default-setup` | 403 | 200 | UNKNOWN |

Scorecard's docs say [no API reveals the read-only token default](https://github.com/ossf/scorecard/blob/main/docs/checks.md). `actions/permissions/workflow` returned it to an admin, so that note is out of date.

`gh repo view $R --json deleteBranchOnMerge` gives real values to a reader through GraphQL, where REST gives null.

## Plan gates

From GitHub docs source, not tested on each plan.

| Feature | Available on |
|---|---|
| Protected branches and rulesets | Public repositories on Free. Private repositories on Pro, Team and above |
| Push rulesets | Team, on internal and private repositories |
| Org rulesets | Team and Enterprise |
| Commit metadata rules, enterprise rulesets | Enterprise |
| Evaluate enforcement mode | Enterprise. Behavior on Team is unverified |
| Code scanning | Public repositories. Org repositories on Team or Enterprise with Code Security |
| Merge queue | Public org repositories, and private org repositories on Enterprise Cloud. Not personal accounts |
| Secret scanning | Automatic and free on public repositories. Private org repositories need Secret Protection |
| User push protection | On by default for public repositories |
| Immutable releases | Repository or org setting, future releases only |

If a command fails on plan, report it as not available and move on.

## Solo or team

Check with `git shortlog -sn --no-merges --since=1.year HEAD`. One active person means solo.

| Setting | Solo | Small team | Larger team |
|---|---|---|---|
| Block force push and deletion | Yes | Yes | Yes |
| Require a pull request | Owner's choice | Yes | Yes |
| Required approvals | 0. [Scorecard](https://github.com/ossf/scorecard/blob/main/docs/checks.md) says review is infeasible with one active participant | 1 | 2 with code owners, Scorecard tier 4 |
| Required status checks | Yes, if CI exists | Yes | Yes |
| Merge queue | No | Rarely | When volume needs it, and only with `merge_group` in CI |
| Delete branch on merge | Yes | Yes | Yes |

Scorecard tiers are sourced. Applying a tier to a team size is opinion.

## Branch ruleset

Save as `ruleset-branch.json`. Rulesets are visible to readers and layer with classic protection, per [about rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets).

Solo:

```json
{
  "name": "default-branch",
  "target": "branch",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"}
  ]
}
```

Team. Replace `test` with real check names:

```json
{
  "name": "default-branch",
  "target": "branch",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": false,
        "required_status_checks": [{"context": "test"}]
      }
    }
  ]
}
```

For a larger team, set `required_approving_review_count` to 2 and `require_code_owner_review` to true.

```bash
gh api -X POST repos/$R/rulesets --input ruleset-branch.json
gh api repos/$R/rules/branches/$B --jq 'map(.type)'
```

What could break:

- A `context` that matches no real check blocks every merge. Copy names from a recent run: `gh pr checks <number> -R $R` (inferred).
- Required approvals block the sole maintainer, who cannot approve their own pull request.
- `strict_required_status_checks_policy: true` forces branches up to date, which multiplies CI runs.
- Each `bypass_actors` entry costs admin enforcement in Scorecard. Leave it empty or name and justify each one.
- A merge bot may need a bypass. Add it after a failed merge shows you need it.
- Up to 75 rulesets per repository, plus 75 org-wide.

To undo, list ids with `gh api repos/$R/rulesets --jq '.[]|[.id,.name]|@tsv'`, then `gh api -X DELETE repos/$R/rulesets/ID`.

## Tag ruleset

Targets TAG-004. Having one is opinion. The legacy `tags/protection` path returned 404 for reader and admin.

```json
{
  "name": "version-tags",
  "target": "tag",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": {"ref_name": {"include": ["refs/tags/v*"], "exclude": []}},
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {"type": "update"}
  ]
}
```

```bash
gh api -X POST repos/$R/rulesets --input ruleset-tags.json
```

This breaks action repositories that move a `v1` tag. Exclude those major tags in `conditions`, or skip the `update` and `non_fast_forward` rules.

## Merge settings

```bash
gh repo edit $R --delete-branch-on-merge
gh repo edit $R --enable-squash-merge --enable-merge-commit=false --enable-rebase-merge=false
gh repo view $R --json deleteBranchOnMerge,squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed
```

- Delete on merge is opinion, and it removes most leftover branches. For fork PRs, [the fork's setting applies](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-the-automatic-deletion-of-branches).
- The merge method is the owner's policy. Set what the project already does. [The tradeoffs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/about-merge-methods-on-github) include confusing later PRs when work continues on a head branch after a squash merge.

## Actions

```bash
gh api -X PUT repos/$R/actions/permissions/workflow -f default_workflow_permissions=read -F can_approve_pull_request_reviews=false
gh api repos/$R/actions/permissions/workflow
```

Sets the default token to read-only and stops workflows approving pull requests. A workflow that relied on a write default now fails. Add `permissions:` blocks first, from [hygiene.md](hygiene.md). New repositories in personal accounts already refuse PR creation and approval by default.

```bash
gh api -X PUT repos/$R/actions/permissions -F enabled=true -f allowed_actions=all -F sha_pinning_required=true
gh api repos/$R/actions/permissions
```

Requires SHA pins. Run this only after the audit shows 0 unpinned references, or unpinned workflows stop working (inferred). `allowed_actions=selected` or `local_only` is stricter. Having a restriction is opinion, and solo repositories can skip it.

## Security features

```bash
gh repo edit $R --enable-secret-scanning
gh repo edit $R --enable-secret-scanning-push-protection
gh api repos/$R --jq '.security_and_analysis'

gh api -X PUT repos/$R/private-vulnerability-reporting
gh api repos/$R/private-vulnerability-reporting --jq .enabled

gh api -X PUT repos/$R/vulnerability-alerts
gh api -X PUT repos/$R/automated-security-fixes
gh api repos/$R/automated-security-fixes --jq .enabled

gh api -X PATCH repos/$R/code-scanning/default-setup -f state=configured
gh api repos/$R/code-scanning/default-setup --jq .state
```

- Push protection stops a push with a secret. [Writers can bypass it by default](https://docs.github.com/en/code-security/concepts/secret-security/push-protection).
- `automated-security-fixes` opens pull requests, up to the separate limit of 10.
- `default-setup` runs a new workflow on each push. A language with no analyzer has nothing to scan.

## Immutable releases

```bash
gh api -X PUT repos/$R/immutable-releases
gh api repos/$R/immutable-releases --jq .enabled
```

[Immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases) lock assets and the tag, and apply to future releases only. Action repositories that move major tags must not create a release for those tags, per [GitHub's action guidance](https://docs.github.com/en/actions/how-tos/create-and-publish-actions/using-immutable-releases-and-tags-to-manage-your-actions-releases).

A tag tied to an immutable release can later block a history rewrite. See [history-rewrite.md](history-rewrite.md).

## Sign-off

```bash
gh api -X PATCH repos/$R -F web_commit_signoff_required=true
```

Set this only if the project requires a DCO.

## Metadata

```bash
gh repo edit $R --description "One plain sentence." --homepage https://example.com
gh repo edit $R --add-topic cli --add-topic python
gh repo edit $R --enable-wiki=false --enable-projects=false
```

- A repository takes [up to 20 topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics), lowercase with hyphens, 50 characters each.
- Disabling a wiki or projects with content hides that content. Check first with `gh repo view $R --json hasWikiEnabled,hasProjectsEnabled,hasDiscussionsEnabled`. Turning off an unused feature is opinion.
- No write API for the social preview image was found (unverified). Set it in the web settings, at [1280 by 640 and under 1 MB](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview).

## Default branch rename

```bash
gh api -X POST repos/$R/branches/$B/rename -f new_name=main
```

Renaming the default branch needs admin or owner, and the API returns before the work finishes. [GitHub](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/renaming-a-branch):

- Redirects URLs with the old name, except raw file URLs.
- Updates branch protection, the base of open PRs and draft releases.
- Does not redirect `git pull` for the old name.
- Does not redirect Actions, so `uses: owner/action@old-name` breaks. If you publish an action, keep a branch at the old name with a notice commit.
- Org rulesets can block a repository admin from renaming.

Collaborators must update local clones.

## Archive

Archiving is reversible and read-only, per [GitHub](https://docs.github.com/en/repositories/archiving-a-github-repository/archiving-repositories). Skip all write suggestions on an archived repository.

```bash
gh repo archive $R --yes
```

## Merge queue

Workflows must trigger on `merge_group`, and third-party CI must watch `gh-readonly-queue/{base}` branches, per [merge queue docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue). Without that trigger, the queue waits on checks that never run. Add the trigger first, then add the queue rule in the web settings or a ruleset.

## Sources

All read 2026-11-06. Status codes were measured that day on `ossf/scorecard` as a reader and on an owned repository as an admin. Plan gates come from these docs source files: [repository rules](https://github.com/github/docs/blob/main/data/reusables/gated-features/repo-rules.md), [protected branches](https://github.com/github/docs/blob/main/data/reusables/gated-features/protected-branches.md), [code scanning](https://github.com/github/docs/blob/main/data/reusables/gated-features/code-scanning.md), [secret scanning](https://github.com/github/docs/blob/main/data/reusables/gated-features/secret-scanning.md), [enforcement statuses](https://github.com/github/docs/blob/main/data/reusables/repositories/rulesets-about-enforcement-statuses.md), [enterprise flag](https://github.com/github/docs/blob/main/data/features/repo-rules-enterprise.yml).

- [Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets), [rules REST](https://docs.github.com/en/rest/repos/rules#get-rules-for-a-branch), [rename REST](https://docs.github.com/en/rest/branches/branches#rename-a-branch)
- [Actions settings for a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)
