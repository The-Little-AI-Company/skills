# Community health files by repository type

Read this in step 4, before you add or remove a community file.

The matrix is inferred from observed projects. It says what to recommend, not what GitHub requires. Only a license has a legal basis, because [code without one stays under exclusive copyright](https://choosealicense.com/no-permission/). That is not legal advice, so offer choices and let the owner decide.

## Matrix

Codes:

- **R** required for this type
- **r** recommended
- **o** optional, offer it
- **x** harmful here. Offer to remove or parameterize it, and never delete without review

Columns: LIC license, RM readme, CONT contributing, COC code of conduct, SEC security policy, SUP support, PRT PR template, FORM issue forms, CFG config.yml, OWN CODEOWNERS, FUND funding, CITE CITATION.cff, CHG changelog, REL release.yml, DISC discussion forms.

| Type | LIC | RM | CONT | COC | SEC | SUP | PRT | FORM | CFG | OWN | FUND | CITE | CHG | REL | DISC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Library | R | R | R | r | R | o | r | r | r | o | o | o | R | r | o |
| CLI | R | R | R | r | R | o | r | r | r | o | o | o | R | r | o |
| Web app | R | R | r | r | R | r | r | r | r | r | o | o | r | r | o |
| Framework | R | R | R | R | R | R | R | R | R | R | o | o | R | r | r |
| API client | R | R | r | r | R | o | r | r | r | o | o | o | R | r | o |
| ML or data | R | R | r | r | r | r | r | r | r | o | o | R | R | o | r |
| Research code | R | R | o | o | o | o | o | o | o | o | o | R | o | o | o |
| Monorepo | R | R | R | R | R | r | R | R | R | R | o | o | R | r | r |
| Infrastructure module | R | R | r | o | R | o | r | r | r | o | o | o | R | r | o |
| Mobile or desktop app | R | R | r | r | R | R | r | R | R | r | o | o | R | r | o |
| Game | R | R | o | r | o | r | o | r | r | o | r | o | r | o | r |
| GitHub Action | R | R | r | o | R | o | r | r | r | r | o | o | R | r | o |
| Plugin or extension | R | R | r | o | R | o | o | r | r | o | o | o | R | r | o |
| Docs or book | R | R | R | r | o | o | r | o | r | o | o | o | o | o | o |
| Dotfiles | o | R | o | o | o | o | o | o | o | o | o | o | o | o | o |
| Awesome list | R | R | R | r | o | o | R | o | o | o | o | o | o | o | o |
| Template or starter | R | R | r | o | r | o | o | o | o | x | x | x | o | o | o |
| Internal or private | o | R | R | o | r | R | r | r | r | R | o | o | r | r | o |

## Why each row looks that way

- **Library.** Consumers reason about versions, so a changelog and semantic versioning matter.
- **CLI.** Same as a library. Behavior changes reach scripts.
- **Web app.** The product is the deployment. A security contact matters more than a citation. The Evidence First PR style fits.
- **Framework.** A large contributor pool and a downstream ecosystem. react, angular and next.js show the full set, including routing in config.yml.
- **API client.** Often generated. CONTRIBUTING must say which files are generated, so nobody edits output by hand.
- **ML or data.** Code license and weight or data license can differ. Forms need versions and hardware. tensorflow asks for 15 fields, and pytorch collects them through a script in 2. Flag missing model or dataset cards.
- **Research code.** Citation is the priority. A heavy process signals a project that does not exist. A maintenance note in the README does more.
- **Monorepo.** CODEOWNERS matters most, since routing fails without it. The Routed Set PR style fits. CODEOWNERS and `release.yml` are per repository, not org defaults.
- **Infrastructure module.** Consumers pin versions and fear destructive change. Forms ask for tool version, provider version and plan output with secrets removed. hashicorp/terraform's PR template asks for rollback.
- **Mobile or desktop app.** End users are not developers, so SUPPORT and config routing come first. Forms need the OS and device.
- **Game.** Asset licenses often differ from code, so [REUSE](https://reuse.software/tutorial/) fits. A security policy depends on online features. Funding matters more than for most.
- **GitHub Action.** It runs in other people's CI with their token, so a security policy is required. Put pin and tag guidance in the README.
- **Plugin or extension.** Host version matters, so forms must ask for it.
- **Docs or book.** A code license is the wrong default. Use a content license such as CC BY, as kubernetes/website does. A page link field is enough, so forms are overkill. Add SECURITY only if the site runs code.
- **Dotfiles.** Personal, not a contribution target. Nothing beyond a README should be pushed. Disabling issues is a valid outcome. A license is needed only if others should reuse the files.
- **Awesome list.** The PR template is the quality gate. sindresorhus/awesome has 35 boxes. CC0 is the norm.
- **Template or starter.** Files are copied into every generated repository. CODEOWNERS sends reviews to the template's owner, FUNDING advertises that owner on every copy, and CITATION.cff gives the wrong citation. Treat all three as parameters, and check that the license suits derivatives.
- **Internal or private.** An open source license may be wrong, so ask, and never delete an existing license file. CODEOWNERS and SUPPORT carry the most value. Do not put internal names or links in a public `.github` repository.

## Before you call a file missing

- `files.issue_template` in the community profile API does not see issue forms. It was non-null in 5 of 46 sampled repositories, and react, rust and nixpkgs have forms and report null. Read the tree.
- Never score a repository by `health_percentage`. Every sampled repository at 100 had `content_reports_enabled: true`. The formula is undocumented, and a tested model matched 16 of 25.
- Report `content_reports_enabled` as a moderation setting. It is often the difference between 87 and 100.
- Files can come from the owner's public `.github` repository. They do not appear in the tree or in clones. sindresorhus/ky returns inherited `contributing` and `code_of_conduct_file` URLs. Read the [community profile API](https://docs.github.com/en/rest/metrics/community), then the owner's `.github`, before you report a gap.

## Where each file goes

Source: [default community health files](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file).

- Lookup order is `.github/`, root, `docs/`. The same order applies inside the `.github` repository.
- The `.github` repository must be public. An Enterprise Managed Users organization uses an internal one.
- Defaults apply to every repository the account owns that lacks that file type, whatever its visibility.
- Supported as defaults: `ACCESSIBILITY.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, discussion category forms, `FUNDING.yml`, issue and PR templates with `config.yml`, `SECURITY.md`, `SUPPORT.md`, `VULNERABILITY_REPORT.yml`.
- A license cannot be a default. It must travel with clones and packages.
- `CODEOWNERS`, `.github/release.yml` and `CITATION.cff` are not supported as defaults. Each needs a per-repository change.
- A repository with valid forms in its own `.github/ISSUE_TEMPLATE` uses none of the default folder. The override is all or nothing for that folder.
- A label set by a default template must exist in the `.github` repository and in every repository that uses it.

| File | Rules |
|---|---|
| [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) | `.github/`, root or `docs/`, on the PR's base branch, under 3 MB. Last match wins. Owners need write access, and teams must be visible. Paths are case sensitive. `!`, `[ ]` and `\#` do not work. Multiple owners share one line. Add a line that covers the file itself. Check with `gh api repos/$R/codeowners/errors --jq '.errors\|length'`. A 404 means no file or no access. |
| [FUNDING.yml](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/displaying-a-sponsor-button-in-your-repository) | `.github/` on the default branch. Up to 4 sponsored developers, 1 organization, 4 custom URLs. |
| SECURITY.md | Shows under the Security tab. Gives supported versions and how to report. `VULNERABILITY_REPORT.yml` customizes the private report form, as cli/cli does. |
| [SUPPORT.md](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-support-resources-to-your-project) | Root, `docs/` or `.github/`. A link appears when someone creates an issue. |
| [ACCESSIBILITY.md](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-an-accessibility-page-to-your-repository) | New tab and About link. Inherits from `.github`. |
| [CITATION.cff](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files) | Root. Required keys are `authors`, `cff-version`, `message`, `title`, per the [schema guide](https://github.com/citation-file-format/citation-file-format/blob/main/schema-guide.md). |
| [Discussion forms](https://docs.github.com/en/discussions/managing-discussions-for-your-community/syntax-for-discussion-category-forms) | `.github/DISCUSSION_TEMPLATE/`. The file name matches a category slug. Keys are `body`, `labels`, `title`. Not for polls. |
| [release.yml](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes) | `.github/release.yml`. Sorts PRs by label, so unlabeled PRs land in the `*` category. |
| [Labels](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels) | New repositories get defaults. A label missing from the repository is dropped from a form with no error. |

## Issue form rules

`scripts/validate_forms.py` checks these. Sources: [form syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms), [schema](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-githubs-form-schema), [validation errors](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/common-validation-errors-when-creating-issue-forms), [config.yml](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository).

- Forms live in `.github/ISSUE_TEMPLATE/`. Required keys are `name`, `description` and `body`. `name` must be more than 3 characters and unique.
- Field types are `markdown`, `textarea`, `input`, `dropdown`, `checkboxes` and `upload`. A body of only `markdown` fails.
- Ids hold letters, numbers, `-` and `_`, and are unique. Labels are unique after normalizing.
- Keys read as booleans fail: `y`, `yes`, `no`, `true`, `false`, `on`, `off`.
- A dropdown cannot have duplicate options, the reserved option `None`, or an unquoted boolean. `default` cannot combine with `None` or `n/a`.
- GitHub blocks some words in labels. `password` is the documented example, and the docs give no full list.
- Forms sort alphanumerically, with YAML before Markdown. Use zero padding at 10 or more.
- Forms and the schema were still labeled public preview in the docs source.

`scripts/validate_forms.py` does not know the repository's labels, and it does not check names across Markdown templates. Its pass is not a GitHub pass, so open one test issue after rollout if the owner agrees.

## Issue form sets

Assets are in `assets/issue-forms/`, as real `.github/ISSUE_TEMPLATE/` trees. Required counts exclude confirmation boxes.

| Set | Bug fields | Bug required | Feature fields | Feature required | Fits |
|---|---:|---:|---:|---:|---|
| small | 3 | 3 | 2 | 1 | Solo or small library, CLI, plugin |
| medium | 7 | 5 | 4 | 2 | Team library, framework, API client |
| large | 12 | 7 | 6 | 3 | App, platform, monorepo |

Across 14 sampled forms, the median was 7 fields with 5 required, and the range was 1 to 15. A form earns its fields by naming a command that produces the data, such as `go env` or `next info` (inferred).

Before rollout:

1. Replace `OWNER/REPO` in `config.yml`.
2. Confirm Discussions and private vulnerability reporting are on, or remove those links. A link to a feature that is off leads nowhere (inferred).
3. Verify the Q&A category slug in the large config. It is an assumption.
4. Replace the dropdown options in the large bug form with real components.
5. The `title` in the large bug form is a prefill, and a reporter can leave it as is. Drop it if that bothers maintainers.
6. The sets use only the default labels `bug` and `enhancement`. They leave out `type`, which needs organization issue types, `projects`, which needs reporter write access, and `assignees`, which names people.

## Starter files

Written fresh, owner-neutral and safe to ship. Replace every placeholder.

`.github/release.yml`:

```yaml
changelog:
  exclude:
    labels:
      - invalid
      - duplicate
      - wontfix
  categories:
    - title: Added
      labels:
        - enhancement
    - title: Fixed
      labels:
        - bug
    - title: Documentation
      labels:
        - documentation
    - title: Other changes
      labels:
        - "*"
```

`.github/CODEOWNERS`. Keep the fallback first, because the last match wins:

```text
# Replace these with real users or teams that have write access.
*        @OWNER/maintainers
/docs/   @OWNER/docs
```

`SUPPORT.md`:

```markdown
# Getting help

- Questions: use Discussions.
- Bugs: open an issue using the form.
- Security problems: follow SECURITY.md. Do not open a public issue.

This project is maintained by volunteers. Replies may take some time.
```

`SECURITY.md`:

```markdown
# Security policy

## Supported versions

Security fixes go to the newest release. Older versions are not patched.

## Reporting a vulnerability

Use the private report form under the Security tab. Do not open a public issue.
Include the affected version, steps to reproduce, and the impact you expect.
```

## Standards to check

| Standard | Rule | Note |
|---|---|---|
| [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) | `fix` is PATCH, `feat` is MINOR, `!` or `BREAKING CHANGE` is MAJOR | Offer it only if a release tool reads it (inferred) |
| [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) | Added, Changed, Deprecated, Removed, Fixed, Security, with `Unreleased` on top | A raw commit dump fails it |
| [SemVer 2.0.0](https://semver.org/) | A public API must be declared. `0.y.z` means anything can change | A CLI, config format or module input counts as public API (inferred) |
| [Contributor Covenant 3.0](https://www.contributor-covenant.org/version/3/0/code_of_conduct/) | The reporting section needs a real contact | CC BY-SA 4.0. Link it or ship it unmodified as its own file under that license. Adopting it with no contact is worse than none (inferred) |
| [REUSE](https://reuse.software/tutorial/) | `LICENSES/` folder, SPDX tags, `reuse lint` | `REUSE.toml` and the current spec version are unverified |
| [DCO 1.1](https://developercertificate.org/) | `Signed-off-by` trailer, `git commit -s` | Its text cannot be modified, so link to it |
| [choosealicense](https://choosealicense.com/no-permission/) | No license means exclusive copyright. Forking on GitHub is not a broad grant | Offer choices |

## Audit findings that fail silently

Report these. All are inferred from the observed material.

- Labels used in forms or `release.yml` that are missing from the repository.
- `blank_issues_enabled: false` with no route for questions or security reports.
- Required fields that apply to under half of issues.
- A logs field with no warning about secrets and personal data.
- Links in templates to moved domains or deleted form files. vercel/next.js linked a form file missing from its folder on 2026-11-06.
- A `contact_links` entry with no `url`. fastapi/fastapi has one, and how GitHub renders it is unverified.

## Sources

All read 2026-11-06. The 46-repository community profile sample, the health model test and the form field counts were measured that day through the GitHub API.

- Files: [cli/cli VULNERABILITY_REPORT.yml](https://github.com/cli/cli/blob/trunk/.github/VULNERABILITY_REPORT.yml), [fastapi/fastapi .github](https://github.com/fastapi/fastapi/tree/master/.github), [sindresorhus/ky .github](https://github.com/sindresorhus/ky/tree/main/.github), [vercel/next.js .github](https://github.com/vercel/next.js/tree/canary/.github), [pytorch/pytorch .github](https://github.com/pytorch/pytorch/tree/main/.github), [tensorflow/tensorflow .github](https://github.com/tensorflow/tensorflow/tree/master/.github), [hashicorp/terraform .github](https://github.com/hashicorp/terraform/tree/main/.github), [react/react .github](https://github.com/react/react/tree/main/.github), [angular/angular .github](https://github.com/angular/angular/tree/main/.github)
- GitHub: [community profiles](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories), [community metrics API](https://docs.github.com/en/rest/metrics/community), [default community health files](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file)
