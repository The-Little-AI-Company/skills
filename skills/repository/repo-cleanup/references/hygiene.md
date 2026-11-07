# Mechanical hygiene recipes

Read this in step 3, before you change ignore rules, line endings, identity files, workflow pins, permissions or update tooling.

Each recipe names the `repo-audit` check it targets. Sources were read on 2026-11-06. Set `R=owner/repo`. Run the audit again after each pull request. Open one pull request per recipe, and keep a renormalize alone.

Any threshold marked opinion is a default for you to adjust, not a fact.

## Remove tracked junk

Targets IGN-002, IGN-003, IGN-004, HIS-007, HIS-008.

Find it:

```bash
git ls-files -ci --exclude-standard
git ls-files | grep -Ei '(^|/)(\.DS_Store|Thumbs\.db|desktop\.ini|\.idea/|.*\.swp$|.*\.log$)'
git ls-files | grep -E '(^|/)(node_modules|__pycache__|\.venv|venv|target|\.next|coverage)/'
git ls-files | grep -Ei '\.(exe|dll|so|dylib|jar|war|class|pyc|o|a)$'
git ls-files | grep -Ei '\.(zip|tar|tgz|gz|7z|rar|bz2|xz)$'
```

Pass is 0 for each. The zero target is opinion for junk and archives. [Scorecard Binary-Artifacts](https://github.com/ossf/scorecard/blob/main/docs/checks.md) backs it for binaries.

Leave these alone, and say why in the pull request:

| Looks like junk | Why it stays | How to tell |
|---|---|---|
| Binary under `testdata`, `fixtures`, `__snapshots__` | Test input | Its path |
| `dist/` in a JavaScript action | Consumers run it | `action.yml` points at `dist` |
| `vendor/` in Go | Committed by design | `vendor/modules.txt` exists |
| Force-added file that matches an ignore rule | Deliberate exception | A negated rule or a clear path |
| Shared editor settings | Kept on purpose | The project says so |

Fix it:

```bash
git rm -r --cached -- path/to/junk
```

`--cached` keeps the local copy. Add the matching ignore rule in the same pull request, then confirm with `git check-ignore -v path/to/junk`.

This fixes the tip only. The blob stays in history, and that is usually fine. If the file holds a secret, stop and go to step 2. If it is huge, weigh [history-rewrite.md](history-rewrite.md) before you touch it.

## Ignore rules

Targets IGN-001.

Copy from [github/gitignore](https://github.com/github/gitignore). Its templates are CC0, so they can ship without notice. Never write a language template from memory.

```bash
gh api repos/github/gitignore/contents/Python.gitignore -H 'Accept: application/vnd.github.raw' >> .gitignore
```

Add only the language files this repository uses, from the table under [Split by language](#split-by-language). Operating system and editor rules live under `Global/` in that repository, for example `Global/macOS.gitignore`. Add them only if the junk shows up, since each person can also set a global ignore.

Check that a new rule does not hide a tracked file that should stay: `git ls-files -ci --exclude-standard` must not list it.

## Renormalize line endings

Targets IGN-005, IGN-006.

`.gitattributes` overrides `core.autocrlf` for the repository, and `text=auto` is the [documented good default](https://docs.github.com/en/get-started/git-basics/configuring-git-to-handle-line-endings).

```gitattributes
* text=auto

*.sh  text eol=lf
*.bat text eol=crlf
*.cmd text eol=crlf
*.sln text eol=crlf

*.png binary
*.jpg binary
*.ico binary
```

Keep only the lines that match files in this repository. Do this first, with no open work in the tree:

```bash
git add .gitattributes
git commit -m "Add line ending policy"
git add --renormalize .
git ls-files --eol | awk '$1=="i/mixed"'
git commit -m "Normalize line endings"
```

The last check before commit must print nothing, except fixtures named in `.gitattributes`. Fixtures that test line endings need `-text`. The zero target for mixed files is opinion.

A renormalize touches many lines, so ship it alone. If the project uses `git blame`, add the commit to `.git-blame-ignore-revs` after it lands (inferred). Pull requests open at that moment get conflicts, so land it when few are open.

## EditorConfig

Targets IGN-009. Having one is opinion. The format comes from the [EditorConfig specification](https://github.com/editorconfig/specification). Skip it when a formatter owns style.

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
```

Match what the code already does. Read a sample of files first, and add `indent_style` and `indent_size` only for what the repository uses. `root = true` stops the search for parent files. The audit looks for that line.

## Mailmap

Targets HIS-010. The target is opinion, and the format comes from [gitmailmap](https://git-scm.com/docs/gitmailmap).

```bash
git log --all --format='%aN <%aE>' | sort -u
```

Each `.mailmap` line maps a commit identity to the proper one:

```text
Proper Name <proper@example.com> <old@example.com>
Proper Name <proper@example.com> Old Name <old@example.com>
```

Verify with `git check-mailmap 'Old Name <old@example.com>'` and `git shortlog -sne`.

Ask each person first. A mailmap is public, and it publishes both addresses side by side. It changes display in git tools and leaves commits unchanged, so it cannot hide an address. Report exposed personal addresses (HIS-009) and let the owner decide.

## Pin actions to a verified SHA

Targets SUP-001, SUP-004.

GitHub says to [pin to a full commit SHA and verify that it comes from the action's repository, not a fork](https://docs.github.com/en/actions/reference/security/secure-use). A SHA alone does not prove origin, because fork networks share objects. `gh api repos/OWNER/ACTION/commits/SHA` can answer 200 for a commit that only a fork holds, so it is not a proof (inferred from shared fork objects).

The proof is a ref in the action's own repository:

1. List the references.

   ```bash
   grep -rhE '^\s*-?\s*uses:' .github/workflows | sed -E 's/^\s*-?\s*uses:\s*//' | awk '{print $1}' | sort -u
   ```

2. Skip `./local` actions and `docker://` references. For `owner/repo/path@ref`, resolve `owner/repo`.
3. Choose an exact version tag, not a moving major tag. On 2026-11-06, `actions/checkout` `v4` resolved to `11d5960a326750d5838078e36cf38b85af677262` and `v4.2.2` to `11bd71901bbe5b1630ceea73d27597364c9af683`, so the two differ. Check the tag exists before you pick it.
4. Resolve it from the action's repository:

   ```bash
   git ls-remote https://github.com/actions/checkout 'refs/tags/v4.2.2' 'refs/tags/v4.2.2^{}'
   ```

   An annotated tag prints two lines. Use the `^{}` line, which is the commit. A lightweight tag prints one line.
5. Confirm by a second route:

   ```bash
   gh api repos/actions/checkout/git/ref/tags/v4.2.2 --jq '.object|[.type,.sha]|@tsv'
   ```

   If the type is `tag`, peel it with `gh api repos/actions/checkout/git/tags/SHA --jq .object.sha`.
6. Write the pin with the version as a comment:

   ```yaml
   - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
   ```

The comment is opinion, and the audit expects it. Dependabot respects SHA pins, per [sp-repo-review](https://learn.scientific-python.org/development/guides/gha-basic/). Add `github-actions` to the update tool in the same pull request, or the pins go stale.

Exceptions the audit should not fail: reusable workflows pinned by policy, and tags backed by an immutable release, which [Scorecard counts as pinned](https://github.com/ossf/scorecard/blob/main/docs/checks.md).

A verified SHA proves what the repository published. It does not prove the code is safe.

## Workflow permissions

Targets CI-004. Scorecard's Token-Permissions check sets the goal: read-only at the top, write per job.

```yaml
permissions:
  contents: read

jobs:
  comment:
    permissions:
      pull-requests: write
```

Add the top block to every workflow, then run the workflow on the branch. A job that needs more fails with a permission error, and that error names the scope to grant on that job. Do not widen the top block to fix one job.

The repository default is an owner setting, in [settings.md](settings.md).

## Privileged triggers and script injection

Targets CI-007, CI-008. Both need a reader, so do not fix them by pattern.

- `pull_request_target` or `workflow_run` fails only when the job checks out pull request code. A labeler with no checkout is fine. Scorecard rates Dangerous-Workflow as Critical.
- `${{ github.event.pull_request.title }}` and similar values inside a `run:` script are injection. [GitHub's guidance](https://docs.github.com/en/actions/reference/security/secure-use) applies: pass the value through `env:` and quote the variable.

```yaml
- env:
    TITLE: ${{ github.event.pull_request.title }}
  run: printf '%s\n' "$TITLE"
```

## Dependabot

Targets SUP-005, SUP-006, SUP-007, SUP-015. Scorecard's Dependency-Update-Tool wants one update tool, and the [options reference](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference) gives the keys.

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    groups:
      actions:
        patterns:
          - "*"
  - package-ecosystem: npm
    directory: /
    schedule:
      interval: weekly
    groups:
      minor-and-patch:
        update-types:
          - minor
          - patch
```

Weekly is opinion. Replace `npm` with the ecosystem from the table below, and add one entry per package manager. Use `directories` for a monorepo.

Limits:

- 5 open version pull requests by default, set with `open-pull-requests-limit`.
- A separate fixed limit of 10 for security pull requests.
- A documented default cooldown of 3 days on version updates. The docs source gates that text behind a version flag, so confirm it on your plan. `cooldown` does not apply to security updates.
- sp-repo-review GH212 recommends grouping Actions updates.

Run Dependabot checks only on Dependabot repositories. The audit rows for grouping and cooldown read as zero on a Renovate repository.

## Renovate

Targets SUP-005. Use it when the owner wants more control than Dependabot gives. Renovate is AGPL-3.0, so use it as a service or an external tool and do not vendor it.

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended", "helpers:pinGitHubActionDigests"],
  "minimumReleaseAge": "3 days"
}
```

`config:recommended` and `helpers:pinGitHubActionDigests` are presets in Renovate's source, read 2026-11-06. Three days is opinion, chosen to match the Dependabot default.

[Defaults](https://docs.renovatebot.com/configuration-options/) from its source file, which can change: `prHourlyLimit` 2, `prConcurrentLimit` 10, `pinDigests` false, `minimumReleaseAge` null.

Pick one tool. Two update tools open duplicate pull requests (inferred).

## Split by language

`.gitignore` names were checked against github/gitignore and ecosystem ids against the Dependabot options reference on 2026-11-06. Lockfile rules are opinion: commit them for apps, and follow project policy for libraries.

| Stack | gitignore template | Dependabot ecosystem | Lockfile | Typical junk |
|---|---|---|---|---|
| Node with npm, pnpm or Yarn | `Node.gitignore` | `npm` | `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock` | `node_modules/`, `.next/`, `coverage/` |
| Bun | `Node.gitignore` | `bun` | `bun.lock`, `bun.lockb` | `node_modules/` |
| Python with pip, Poetry or pipenv | `Python.gitignore` | `pip` | `poetry.lock` | `__pycache__/`, `.venv/`, `*.pyc` |
| Python with uv | `Python.gitignore` | `uv` | `uv.lock` | `__pycache__/`, `.venv/` |
| Go | `Go.gitignore` | `gomod` | `go.sum` | Built binaries. Keep `vendor/` |
| Rust | `Rust.gitignore` | `cargo` | `Cargo.lock` | `target/` |
| Java or Kotlin with Maven | `Java.gitignore`, `Kotlin.gitignore` | `maven` | None | `target/`, `*.class`, `*.jar` |
| Java or Kotlin with Gradle | `Java.gitignore`, `Kotlin.gitignore` | `gradle` | None | `build/`, `.gradle/`, `*.class` |
| Ruby | `Ruby.gitignore` | `bundler` | `Gemfile.lock` | `.bundle/`, `*.gem` |
| PHP | Pick by framework | `composer` | `composer.lock` | `vendor/` |
| .NET | `Dotnet.gitignore`, `VisualStudio.gitignore` | `nuget` | None | `bin/`, `obj/` |
| Swift | `Swift.gitignore` | `swift` | `Package.resolved` | `.build/` |
| Terraform | `Terraform.gitignore` | `terraform` | `.terraform.lock.hcl` | `.terraform/`, `*.tfstate` |
| Elixir | Pick by framework | `mix` | `mix.lock` | `_build/`, `deps/` |
| Containers | None | `docker` | None | None |
| GitHub Actions | None | `github-actions` | None | None |
| Git submodules | None | `gitsubmodule` | None | None |

`*.tfstate` can hold secrets. Treat a tracked state file as a secret finding, not as junk (inferred).

## Files that do not belong on a default branch

This table is opinion, grounded in [GitHub's large file guidance](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) and the [git-sizer README](https://github.com/github/git-sizer).

| Belongs | Conditional | Does not belong |
|---|---|---|
| Source, tests, docs | `dist/` for JavaScript actions | Secrets, keys, real `.env` files |
| Build and CI config | `vendor/` where the ecosystem expects it | `node_modules`, virtual environments, compiler output |
| Lockfiles for apps | Lockfiles for libraries, by policy | Large media without LFS |
| Small test fixtures | Generated code that consumers need, marked generated | Archives, database dumps, logs |
| License, README, health files | Shared editor settings | Personal editor state and machine paths |
| `.gitattributes`, `.gitignore` | Binary fixtures under a clear path | Work-in-progress notes, one-time scripts |

Sourced limits: GitHub warns at 50 MiB and blocks at 100 MiB per file, and advises repositories under 1 GB and strongly under 5 GB.

## Sources

All read 2026-11-06. SHA resolution for `actions/checkout` was measured the same day.

- [About large files on GitHub](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github), [git-sizer](https://github.com/github/git-sizer)
- [Scorecard checks](https://github.com/ossf/scorecard/blob/main/docs/checks.md), [sp-repo-review Development Guide](https://learn.scientific-python.org/development/guides/gha-basic/)
- [github/gitignore](https://github.com/github/gitignore), [gitignore](https://git-scm.com/docs/gitignore), [gitmailmap](https://git-scm.com/docs/gitmailmap), [EditorConfig specification](https://github.com/editorconfig/specification)
- [Line endings](https://docs.github.com/en/get-started/git-basics/configuring-git-to-handle-line-endings), [Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use)
- [Dependabot options](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference), [Renovate options](https://docs.renovatebot.com/configuration-options/), [Renovate defaults source](https://github.com/renovatebot/renovate/blob/main/lib/config/options/index.ts), [config presets](https://github.com/renovatebot/renovate/blob/main/lib/config/presets/internal/config.preset.ts), [helper presets](https://github.com/renovatebot/renovate/blob/main/lib/config/presets/internal/helpers.preset.ts)
