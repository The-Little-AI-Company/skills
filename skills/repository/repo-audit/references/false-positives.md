# False positives and false passes

Read this file in step 3, before you confirm any critical or high finding or any finding you plan to lead with.

The tool matches patterns. It cannot read intent. Open the evidence for each finding, then keep it, downgrade it or drop it, and record why. A pass needs the same care where this file says it is weak.

Labels on each trap:

- **[F]** Reproduced on a fixture repository with this tool on 2026-11-06.
- **[C]** Read from the check's code, not reproduced.
- **[S]** Stated by the linked source or measured by the research behind it, read 2026-11-06.

Checks not listed here have no recorded trap. That is not proof they have none.

## Before you read any row

These faults change many results at once.

| Trap | Effect | What to do |
|---|---|---|
| Checkout is not the default branch [F] | HIS-012, HIS-013, HIS-019, GOV-008 and GOV-009 read `HEAD`. A topic branch produced a HIS-019 failure from its own `wip` commit | Check out the default branch, then rerun |
| Dirty working tree [C] | The file list comes from the index, and file text comes from the working tree | Audit a clean checkout |
| Offline run [F] | GOV-002 and DOC-003 fail because inherited files and GitHub releases are invisible. GOV-004, GOV-005, DOC-004 and DOC-005 share the blind spot [C] | Rerun online, or mark each as not confirmed |
| Offline run on private code [C] | Private-only skips do not fire, so GOV-001, GOV-002, CI-010 and PRS-022 can fail on proprietary code | Set `"public": false` |
| Auditor's global ignore file [F] | IGN-002 reads `core.excludesFile` from the machine running the tool | Run `git check-ignore -v --no-index <path>` to see which file holds the rule |
| Wrong type [F] | One `SKILL.md` anywhere makes a web app a `plugin`, a Go service named `billing-api` reads as `sdk`, and a `main.go` reads as `cli` | Read `type` and `also`. Set `type` in the policy file and rerun |
| Fork or archive [S] | The tool has no fork logic. [Archives are read-only](https://docs.github.com/en/repositories/archiving-a-github-repository/archiving-repositories) | On a fork, report only what differs from upstream. On an archive, treat fixes as advice |
| Reader token [S] | A reader gets 403 or 404 from many endpoints, which the tool reports as unknown. `branches/{b}/protection` returned 404 on a protected repository | Keep it unknown. Never turn it into a fail |
| Plan gates [S] | [Rulesets on private repositories need Pro, Team or above](https://github.com/github/docs/blob/main/data/reusables/gated-features/repo-rules.md). [Secret scanning on private organization repositories needs Secret Protection](https://github.com/github/docs/blob/main/data/reusables/gated-features/secret-scanning.md). BRN-002, SEC-001, SEC-002 and SUP-011 can fail for an admin who cannot buy the feature on this plan | Say the feature is gated, and offer a waiver. These gates come from docs, not from tests on each plan |

## Secrets

Treat every secret finding as real until you have looked. A wrong dismissal costs more than a wrong alarm. Keep the value out of your context: read the path, the commit and the surrounding lines with the matched run masked. A value in your transcript counts as written down.

| Check | Trap | How to tell |
|---|---|---|
| SEC-005 | A vendor's published sample key fails as critical. The placeholder filter runs only in SEC-012 [F] | Compare the masked prefix and suffix with the vendor's documented sample. Waive with the reason |
| SEC-005 | A PEM private key header in code that parses PEM, or in a scanner's rule file, matches [C] | The match is a header with no key body after it |
| SEC-005 | The search matches added and removed lines, so a commit that deleted a key is listed too [C] | Count distinct paths, not rows |
| SEC-005, SEC-012 | Fake keys in docs and samples outside fixture folders [S] | Use path and value entropy. Check liveness only through the provider or the alert's validity field, and never print the value |
| SEC-003 | Alerts on revoked tokens stay open [S] | Close with a resolution after rotation evidence |
| SEC-008 | A tracked `.npmrc` with only a registry line fails as critical [F] | Look for an auth key name in the file, masked. Without one, drop to a note |
| SEC-008 | Public CA bundles and test certificates end in `.pem`. Keynote files end in `.key` [C] | The file holds a public certificate, or is not key material at all |
| SEC-009 | `.env.development` and `.env.test` hold public defaults and fail [F] | [OpenSSF notes these may not hold real secrets](https://www.bestpractices.dev/en/criteria/0). Read key names. Downgrade when no value is sensitive |
| SEC-010 | Deploy bots must push [S] | Named bot, one repository. Waive |
| SEC-013 | Always unknown, because the tool never runs a scanner [C] | Report it unknown until a scanner runs. See false passes below |

## History

| Check | Trap | How to tell |
|---|---|---|
| HIS-001 | Fails at 1 GiB, while GitHub's guidance is [under 1 GB ideally and under 5 GB strongly](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) [S] | State the number. Between 1 and 5 GiB is a warning in substance. Game and model repositories exceed it by purpose |
| HIS-002, HIS-003 | Data, game or model files in a repository not typed that way [S] | Size matches the purpose. Ask for LFS, not removal |
| HIS-006 | A rewrite before the first release, or an approved cleanup [S] | Compare the date with the first release. Retention of the `activity` endpoint is unverified, so zero proves little |
| HIS-007 | `gradle-wrapper.jar` fails [F] | Build tool wrappers are committed on purpose. Keep it as a note, and say what verifies the jar |
| HIS-007 | Wavefront `.obj` meshes and `.lib` files match the compiled pattern [C] | Open the file type |
| HIS-007, HIS-008 | Installer and archive repositories, and fixtures outside the recognized folder names [S] | The purpose of the repository explains the file |
| HIS-012 | Default Dependabot subjects and git's `Revert "..."` subjects miss the pattern [F] | Exclude bot and revert subjects before you report the count |
| HIS-012 | Project-specific commit types miss the pattern [C] | Read the commitlint config. [angular](https://github.com/angular/angular) uses a close variant of [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) |
| HIS-014, HIS-016 | Linux-only repositories [S] | Harm from these is general knowledge, unverified by the research. `aux.c` and `con.py` match by design [C] |
| HIS-010 | A shared build or team address carries several names [C] | Read the names. It also misses one person with several addresses |

## Branches and tags

| Check | Trap | How to tell |
|---|---|---|
| BRN-002 | Fails for an admin on a private repository whose plan has no rules [S] | See plan gates |
| BRN-003 | Two addresses for one person defeat the solo rule [C] | Compare names. Set `solo` |
| BRN-004 | With no GitHub workflows the check reads not applicable, even when outside CI exists and nothing requires it [C] | Report the real CI in judgment |
| BRN-007 | Rulesets in a declared trial [S] | Owner note. [`rules/branches` hides evaluate-mode rules](https://docs.github.com/en/rest/repos/rules#get-rules-for-a-branch) |
| BRN-009 | Fork-based projects, where the contributor's fork setting applies [S] | Most PRs come from forks |
| BRN-010 | A long-lived branch whose tip equals a merged PR head reads as leftover [C] | Read the names. Age or a merge alone never justifies deletion |
| TAG-001 | Repositories that tag only through GitHub Releases get lightweight tags [S] | It is a note. Leave it there |
| TAG-003 | Finished libraries, rolling apps and sites [S] | [CLOMonitor's check suits active libraries](https://github.com/cncf/clomonitor/blob/main/docs/checks.md). Low issue volume and recent fixes mean it is fine |
| TAG-005 | Protects future releases only [S] | A pass says nothing about older tags |

## CI

| Check | Trap | How to tell |
|---|---|---|
| CI-001 | CircleCI, Jenkins or other outside CI fails [F] | Look for `.circleci/`, `Jenkinsfile`, `.travis.yml`, `.gitlab-ci.yml` and the like. Drop the finding, and check the real CI in judgment |
| CI-002 | Skipped runs. Scorecard's last 20 runs were 15 skipped and 5 success [S] | The tool excludes skipped, cancelled and neutral. One flaky scheduled workflow can still sink the share, so read which workflow failed |
| CI-003 | Workflows retired on purpose. [Forks disable schedules by default](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows) [S] | Owner note, or fork |
| CI-004 | Job-level `permissions` in a file with 4-space YAML indent reads as missing [F] | Read the file. Jobs with a trailing comment on the ID line can also miss [C] |
| CI-007 | Fires when trigger, checkout and a head reference all appear anywhere in the file. A file with `pull_request_target`, a plain checkout in one job and `github.head_ref` in another fails [F] | Read the job. Fail only when one job with the privileged trigger checks out the head. Labelers with no head checkout are safe [S] |
| CI-008 | Numeric or hash fields fail as critical. `github.event.pull_request.number` fails [F] | Keep it for free text such as a title, body, branch name or commit message. Which fields are free text is your reading of the event payload, so say so. [GitHub's guidance](https://docs.github.com/en/actions/reference/security/secure-use) |
| CI-010 | A private repository on an offline run [C] | Set `public` |
| CI-012 | Inline Rust tests and folders such as `t/` are not seen, so the check fails [C] | Read the tree |

## Supply chain

| Check | Trap | How to tell |
|---|---|---|
| SUP-001 | Tags backed by an immutable release [S] | [Scorecard counts those as pinned](https://github.com/ossf/scorecard/blob/main/docs/checks.md). Check the release |
| SUP-005 | Renovate config in `package.json` fails [F] | Read the manifest. Org-level presets are invisible too [C] |
| SUP-006, SUP-007 | Skipped on Renovate [C] | Read the Renovate config in judgment |
| SUP-010 | Measures from the alert's creation, while [OpenSSF measures from public knowledge](https://www.bestpractices.dev/en/criteria/0) [C] | Read the advisory date |
| SUP-011 | Scanners other than CodeQL, Semgrep, bandit and gosec, and languages with no analyzer [S] | Read the workflows |
| SUP-013 | `deno.lock` is not in the list, so a Deno project fails [F] | Look for any lockfile the ecosystem uses |
| SUP-013 | A Go module with no dependencies has no `go.sum` and fails [F] | Read `go.mod` |
| SUP-014 | SSH submodule URLs fail. The HTTPS rule is opinion [S] | Owner's choice |

## Governance and metadata

| Check | Trap | How to tell |
|---|---|---|
| GOV-001 | A REUSE `LICENSES/` folder with no root file reads as no license [F] | List the folder. [REUSE tutorial](https://reuse.software/tutorial/) |
| GOV-001 | `NOASSERTION` on dual or mixed licenses. [git-filter-repo](https://github.com/newren/git-filter-repo) returns it [S] | Read the license file. The tool reports a note |
| GOV-002, GOV-004, GOV-005, DOC-004, DOC-005 | [Files inherited from the owner's `.github` repository](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file) are not in the tree [S] | Run online. DOC-005 looks at one inherited path only [C] |
| GOV-005 | Personal and internal repositories fail, because solo does not skip it [C] | Waive for a personal project |
| GOV-006 | "Unknown owner" for a team that exists but is hidden from the caller [S] | Confirm with an organization member. An outsider cannot tell |
| GOV-006 | A 404 reads as not applicable, though it also means no access [S] | Check the tree for the file |
| GOV-007 | A directory rule such as `/.github/` covers the file and fails [F] | Read the file. A catch-all `*` passes, as it should |
| GOV-009 | Finished small libraries. [Scorecard says low scores need no fix](https://github.com/ossf/scorecard/blob/main/docs/checks.md) [S] | Low issue volume with recent releases |
| GOV-010 | Merge queue and rebase flows [S] | Bots are excluded. The share is a note, so do not state it as a failure |
| MET-001, MET-003, MET-004 | These carry medium severity in the tool, while the research rated them low, low and info. Each target is opinion [S] | Under `strong`, one of these can decide the verdict. Say so in the report, and offer a waiver |
| MET-008 | An app that depends on `torch` reads as `ml` and fails [C] | Set `type`. The file suits research software only |
| DOC-001 | Router READMEs can sit under 500 bytes. [shadcn-ui/ui runs 18 lines](https://github.com/shadcn-ui/ui) [S] | The README links to real docs. The 500 byte line is opinion |
| DOC-002 | `README.rst` is never read, so the check fails on any README that is not named `README.md`, `README` or `readme.md` [F] | Read the README |
| DOC-003 | `docs/CHANGELOG.md` or per-package changelogs fail, because only the root is read [F] | List the tree |
| DOC-007 | A score of 100 with no security policy [S] | Never a gate. [The community API also misses issue forms](https://docs.github.com/en/rest/metrics/community) |

## Ignore rules

| Check | Trap | How to tell |
|---|---|---|
| IGN-002 | Force-added fixtures and examples [S] | A clear path, or a negated rule |
| IGN-003 | Shared `.idea/` config, and sample logs outside fixture folders [S] | Kept on purpose, with a reader |
| IGN-004 | `src/coverage/` and hand-written `build/*.js` config fail [F] | Read a file. Source code is not output |
| IGN-004 | `dist/` and `vendor/` committed on purpose. Only an `action` type and a root `vendor/modules.txt` are exempt [S] | `action.yml` points at `dist`, or the project is consumed by git URL |
| IGN-005 | Single-platform repositories [S] | Low cost to add. Keep it, but do not press it |
| IGN-006 | `.bat` and `.sln` files that need CRLF, and fixtures that test line endings [S] | `.gitattributes` names `eol=crlf` or `-text` for them |

## README and presentation

Most of these match text. A fenced block is blanked, and inline code is not.

| Check | Trap | How to tell |
|---|---|---|
| PRS-002 | `alt=""` on a decorative image fails [F] | The image carries no meaning. WCAG allows empty alt there |
| PRS-003 | GitHub-relative links such as `../../issues` read as missing files [F] | The link works on GitHub. Drop it, and say a tool may still stumble on it |
| PRS-021 | Same badge path for two branches counts as a duplicate, because the query is dropped [F] | Compare full URLs |
| PRS-007 | A requirement badge such as `java-17.0` fails [F] | A language or standard version is a declaration, not a package version |
| PRS-010 | A `Sponsor` link above the title fails [F] | A nav link is not a sponsor block. [got and axios](https://github.com/axios/axios) show the real pattern |
| PRS-011 | A bare `user-attachments` video link is not seen as a visual [F] | Open the rendered page |
| PRS-011 | Research files "adding a hero image" under preference, while the tool fails it as high [S] | Keep the failure only when the effective preset is `showcase`. Otherwise move it to preference and record why |
| PRS-013 | Alpha alone proves nothing. Bright or outlined art stays readable, as on [Babel](https://github.com/babel/babel) and [Mindustry](https://github.com/Anuken/Mindustry) [S] | Open the image on a dark background. No true disappearance was confirmed by the research, so keep this unverified until you see one |
| PRS-015 | The resemblance is a rough rule of thumb [C] | Note only. Never present it as a defect |
| PRS-017 | A product about receipts fails on the word `receipt` [F] | Read the match. A dated deprecation banner can also be correct [C] |
| PRS-020 | Setext headings and plain `<h2>` headings are not seen as anchors [F] | Open the rendered page |
| PRS-022 | `/home/<user>` paths with a container user such as `node` or `ubuntu` fail [F] | A conventional service account leaks nothing |
| PRS-023 | `{{ }}` in inline code fails as high, which hits Actions, Helm, Jinja and Go template docs [F] | Read the match. Inline code is documentation |
| PRS-023 | The word TODO in "a TODO app" fails [F] | Read the sentence |
| PRS-024 | 429, 502 and 509 are transient, not dead [S] | The tool treats these as loaded. Recheck slowly before you cite any host as down |

## False passes

A pass from these checks proves less than it says.

| Check | Why a pass is weak | Do this |
|---|---|---|
| SEC-005, SEC-012, HIS-007, HIS-003 | Any path under `examples/`, `samples/`, `test/`, `fixtures/` or `spec/` is exempt. A real key under `examples/` passed both [F] | List exempted paths with matching names and open any that look live |
| SEC-012 | Any line with a word like `sample` or `example` is exempt, and a key there passed [F]. Files over 2 MiB are skipped, and a file reports its first match only [C] | SEC-005 caught the same key outside fixture paths. Never cite SEC-012 alone |
| SEC-005 | A pattern floor. It covers few key shapes and no generic password [C] | Run gitleaks in `--redact` mode for a real answer. Run [trufflehog](https://github.com/trufflesecurity/trufflehog) verification only with owner consent, since it sends found values to providers [S] |
| SUP-001 | Skips cross-repository reusable workflows, and reads only `.github/workflows`, not composite actions [C] | Read those refs |
| CI-010 | Reads literal `self-hosted`, so `runs-on` through a matrix variable passes [C] | Read the matrix |
| CI-008 | Reads `run` lines only, so `script:` inputs of `actions/github-script` pass [C] | Read them |
| CI-002 | Green runs do not prove testing | Work the CI item in [judgment.md](judgment.md) |
| PRS-013 | Returns pass for anything other than a plain 8-bit RGBA PNG, and never reads SVG [C] | View transparent art in both themes |
| PRS-024 | Skips `raw.githubusercontent.com` and `github.com/.../raw/` URLs, so the broken cross-repository hero on [llama.cpp](https://github.com/ggml-org/llama.cpp) would not be probed [F]. Also skips non-public hosts, and reads only the first 60 images [C] | Open raw URLs yourself. Pin cross-repository images to a commit |
| PRS-018 | Any code fence or the word `usage` in 120 lines passes [C] | Apply the commands item in [judgment.md](judgment.md) |
| TAG-007 | Accepts a checksum file as signed, and reads the 5 latest releases. [Scorecard reads 30](https://github.com/ossf/scorecard/blob/main/docs/checks.md) [C] | A checksum is integrity, not provenance. Say which you found |
| HIS-018 | Misses old versions of a path that still exists [C] | List blobs with `git rev-list --objects --all` if size matters |
| HIS-020 | Reads the root `.gitattributes` and the first 500 LFS paths. Its failure branch was not exercised by the research, because Git for Windows converted the seed [S] | Treat a pass as unproven on large LFS sets |
| GOV-007 | A comment that names CODEOWNERS passes [C] | Read the file |
