# Shared fixes

Read this at step 3, before planning any per-repository pull request. A shared fix replaces many pull requests, so check here first.

Sources were read on 2026-11-06. Plan gates come from GitHub's docs source, not from tests on each plan. Confirm a gate on the owner's plan before you promise it.

## Choose the fix

| Problem | Shared fix | If that is not available |
|---|---|---|
| Unprotected default branches | Organization ruleset | One ruleset per repository, through settings |
| Missing `SECURITY.md`, `CONTRIBUTING.md`, code of conduct or support file | Default in the owner's `.github` repository | Per-repository pull request |
| Missing issue or pull request templates | Default in `.github`, after the override check below | Per-repository pull request |
| Same CI steps copied across repositories | Reusable workflow, with one thin caller per repository | Per-repository pull request |
| New repositories start without CI | Workflow template in `.github` | Document the workflow |
| Settings drift, such as merge options | safe-settings | Per-repository settings change |
| Missing `LICENSE` | None. It must be in each repository | Per-repository pull request |
| Missing `CODEOWNERS`, `.github/release.yml`, `CITATION.cff` | None. Not a supported default | Per-repository pull request |
| Missing `dependabot.yml` | None. Not on the supported list (inference) | Per-repository pull request |

Settings changes wait for the operator's yes, and one yes covers one change.

## Organization rulesets

- Available on Team and Enterprise ([about rulesets][rulesets], [organization rulesets][org-rulesets]). A personal account has no organization rulesets, so it uses repository rulesets.
- Rulesets aggregate, and the strictest rule wins ([about rulesets][rulesets]). A new organization ruleset can tighten a repository that already has its own.
- A repository can have up to 75 rulesets, plus 75 organization-wide rulesets ([about rulesets][rulesets]).
- Anyone with read access can view active rulesets ([about rulesets][rulesets]). Bypass actors are not returned to readers (measured). Read `rulesets` as an admin before you report on bypass.
- An organization ruleset that targets branches can block a repository admin from renaming a branch unless the owner allows it ([renaming a branch][rename]).
- A "require signed commits" rule requires a verified signature. Contributors who pushed unsigned commits must rebase and force push their own branch ([available rules][rules]). Warn them first.
- Evaluate mode tests a ruleset without enforcing it. It is an Enterprise feature ([enforcement statuses][evaluate]). Whether Team has it is unverified, because the docs flag is imprecise on organization rulesets. Without it, target a small set of repositories first, then widen (opinion).
- `rules/branches/{branch}` hides rulesets in evaluate mode ([repository rules][rest-rules]). Use `rulesets` to see them.
- [github/ruleset-recipes](https://github.com/github/ruleset-recipes) offers importable rulesets under MIT.

Whether a ruleset can require a shared workflow to pass is unverified. Do not promise it without checking the owner's ruleset settings.

## Defaults in the `.github` repository

All of this comes from [default community health files][defaults] unless marked.

- The repository is named `.github` and must be public. An Enterprise Managed Users organization uses an internal one.
- Defaults apply to every repository the account owns that lacks that file type, whatever its visibility.
- Lookup order is `.github/`, then the root, then `docs/`, inside each repository and inside the `.github` repository.
- Supported types are `ACCESSIBILITY.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, discussion category forms, `FUNDING.yml`, issue and pull request templates with `config.yml`, `SECURITY.md`, `SUPPORT.md` and `VULNERABILITY_REPORT.yml`.
- A license cannot be a default. It must travel with clones and packages.
- Defaults do not appear in clones, packages or downloads.

Check these before you add a default:

- **Issue templates override as a whole.** A repository with valid templates or config in its own `.github/ISSUE_TEMPLATE` folder uses none of the default folder. Adding one template to a repository cuts it off from all the defaults.
- **Labels must exist.** If a template sets a label, the label must exist in `.github` and in every repository that uses the template.
- **A new default changes nothing where a file exists.** It reaches only the repositories that lack that type.

When you audit, count inherited files as present:

- `fleet.json` says a file is absent from the repository, not missing. The community profile API reports inherited files, and `sindresorhus/ky` returns `contributing` and `code_of_conduct_file` URLs that point at `sindresorhus/.github` ([community profile][profile]).
- That same API field does not see issue forms. `files.issue_template` was non-null in 5 of 46 sampled repositories, and react, rust and nixpkgs have forms but report null. Read the `.github/ISSUE_TEMPLATE` folder instead.

## Shared workflows

These facts come from a fetched summary of GitHub's docs on 2026-11-06. They sit outside the research behind the rest of this file, so confirm one on the linked page before you rely on it.

Reusable workflows ([reuse workflows][reuse]):

- The file sits directly in `.github/workflows`. Subfolders are not supported. Its `on` key includes `workflow_call`.
- A caller uses `{owner}/{repo}/.github/workflows/{filename}@{ref}` in a job-level `uses`. Contexts and expressions cannot appear in `uses`.
- Pin `{ref}` to a full commit SHA. GitHub calls this the safest option. A tag or branch lets one push change CI across the fleet.
- A chain can be 10 workflows deep, counting the top-level caller. Loops are not allowed.
- Secrets reach only the workflow called directly. Pass named secrets, not `secrets: inherit`, unless the called workflow needs them all (opinion).
- An unpassed secret that is not `required: true` resolves to an empty string with no error. Mark the secrets you need as required.
- The docs page did not give a full visibility matrix. Check that a private shared workflow is reachable from each caller before the pilot.

A reusable workflow still needs a caller in each repository, so count it as one pull request per repository. Later changes then land in one place.

Workflow templates ([create workflow templates][templates]):

- They live in `workflow-templates` in the organization's `.github` repository, each with a `.properties.json` metadata file of the same name. `name` and `description` are required.
- They help people add a workflow by hand. The page does not say they change existing repositories, so they fix nothing already in the fleet (inference).
- The page does not state a plan or visibility requirement. Treat both as unverified.

## safe-settings

safe-settings is a GitHub App that you host. It keeps organization settings as code and enforces them against drift. See [references/tools.md](tools.md).

- Use it when settings must stay consistent over time, and when someone will own the deployment.
- It needs hosting, and it applies to the whole organization once deployed. Limit it with `restrictedRepos` before the first run.
- Preview in `nop` mode on a pull request against the admin repository.

## Plan gates

| Feature | Available on | Source |
|---|---|---|
| Protected branches and rulesets | Public repositories on Free. Private repositories on Pro, Team and above | [Ruleset availability][availability], [protected branches][protected] |
| Push rulesets | Team, on internal and private repositories | [Ruleset availability][availability] |
| Organization rulesets | Team and Enterprise | [About rulesets][rulesets], [organization rulesets][org-rulesets] |
| Enterprise-level rulesets, commit metadata rules | Enterprise | [About rulesets][rulesets], [available rules][rules] |
| Evaluate mode | Enterprise. The docs flag is not an exact plan map | [Enforcement statuses][evaluate], [feature flag][flag] |
| Default health files | Need a public `.github` repository for most accounts | [Default health files][defaults] |
| Merge queue | Public organization repositories, and private organization repositories on Enterprise Cloud. Not personal accounts | [Merge queue][queue] |

[rulesets]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets
[org-rulesets]: https://docs.github.com/en/organizations/managing-organization-settings/creating-rulesets-for-repositories-in-your-organization
[rules]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
[evaluate]: https://github.com/github/docs/blob/main/data/reusables/repositories/rulesets-about-enforcement-statuses.md
[flag]: https://github.com/github/docs/blob/main/data/features/repo-rules-enterprise.yml
[availability]: https://github.com/github/docs/blob/main/data/reusables/gated-features/repo-rules.md
[protected]: https://github.com/github/docs/blob/main/data/reusables/gated-features/protected-branches.md
[rest-rules]: https://docs.github.com/en/rest/repos/rules#get-rules-for-a-branch
[rename]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/renaming-a-branch
[queue]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
[defaults]: https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file
[profile]: https://docs.github.com/en/rest/metrics/community
[reuse]: https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows
[templates]: https://docs.github.com/en/actions/how-tos/reuse-automations/create-workflow-templates
