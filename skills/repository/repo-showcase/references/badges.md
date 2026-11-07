# Badges

Read this in step 1 to offer a policy, and in step 5 to choose badges. Every badge reports something live. A badge with nothing to say comes out.

## Policies

| Policy | Includes | Limit | Use when |
|---|---|---|---|
| `none` | Nothing | 0 | The project is a pitch, paper, dotfiles or book, or the owner wants a clean head |
| `signal` | CI, version, coverage, and dependency or security checks that test something | 5 | Default |
| `full` | `signal`, plus downloads, community and social | Owner's choice. The inflection near 5 below still applies as a caution | The audience reads adoption numbers, as with a popular package |

The default and the limit of 5 are opinion, informed by the study below. Measured practice supports restraint: across 69 exemplars on 2026-11-06, the median was 3 header badges and 22 repositories had none. All four research repositories and all three dotfiles repositories had zero.

The header badge distribution was 0: 22, 1: 7, 2: 5, 3: 6, 4: 8, 5: 4, and more than 5: 17 repositories.

## The evidence

[Trockman et al., ICSE 2018](https://par.nsf.gov/servlets/purl/10063054) mined 294,941 npm packages, and 46 percent had at least one badge. This is correlation from npm in 2018, not a law.

- Badges that test a property, which the paper calls assessment signals, correlated most strongly with outcomes.
- Build and coverage badges went with larger test suites.
- Dependency-manager badges went with fresher dependencies.
- A model of badge count found a predicted inflection at 5 badges in popular packages. The effect was negligible in less popular packages.
- Some survey respondents read many badges as clutter.
- The authors call non-trivial badges "mostly reliable signals" and note that effects do not always persist.

Cite it this way when explaining a badge limit. Never say that badges cause quality or adoption.

## Which badges test something

| Kind | Tests something | Keep under `signal` | Note |
|---|---|---|---|
| CI status | Yes, for the branch it names | Yes | One badge per purpose. flameshot shows 3 CI badges in its header and bitwarden/ios shows 4. |
| Coverage | Yes | Yes | Only 2 of 220 measured header badges |
| Dependency freshness or security score | Yes | Yes | |
| Version from a registry | Reports a live fact | Yes | |
| Downloads | Reports a live number, not quality | `full` only | Keep it only if the number is real and useful |
| License | No. GitHub shows it in the sidebar | No | Preference, offer only |
| Stars, forks, watchers | No. The repository header shows them | No | Suspected fake stars exist [at scale](https://arxiv.org/abs/2412.13459), so a star count is a weak claim |
| Chat or community | No | `full` only | A link in the link bar does the same job |
| Static label such as "built with X" | No | No | Cannot update itself |
| Visitor counter | No | No | Appeared in 0 of 73 fetched READMEs |

Measured kinds across 220 header badges: CI 37, version 37, other 30, static label 29, license 18, stars or social 12, community 12, downloads 11, activity 11, store 7. Coverage 2. These kinds come from URL patterns, and `other` and `static_label` are loose buckets.

## Dead and vanity patterns

Each row was observed on 2026-11-06.

| Pattern | Example | Fix |
|---|---|---|
| Legacy workflow URL | softprops/action-gh-release used `workflows/Main/badge.svg`, which returned 404. The form below returned success. | Use `actions/workflows/<file>.yml/badge.svg` |
| Dead host | The dcbadge URL in karpathy/nanoGPT returned 404 on all rechecks | Remove it, or use a host that answers |
| Unstable host | A badgen dependents badge returned 502 on every read. Packagephobia returned 429, which the measurement itself may have caused. | Recheck later. Treat 429, 502 and 509 as unknown, not dead |
| Duplicate by purpose | llama.cpp and flameshot reference the same release badge path twice | Keep one |
| Static version | A `/badge/` URL holding a version number cannot update. No hardcoded package version appeared in this sample, so this is a rule without a failing case | Use a registry badge |
| Too many | ultralytics 9, mui/material-ui 11, flameshot 11, nx 10 | Cut to the policy |
| Badges before purpose | react and immich open with badges | Put the sentence first unless the preset says otherwise |

Any badge is a runtime dependency on a third-party host. [Standard Readme](https://github.com/RichardLitt/standard-readme/blob/main/spec.md) suggests local hosting for static badges, because external requests can track readers. [Shields can be self-hosted](https://github.com/badges/shields).

The Awesome list [rules](https://github.com/sindresorhus/awesome/blob/main/pull_request_template.md) reject a CI badge as having no value in the readme, and say not to put license text in the readme. Those rules apply only to entries on that list.

## URL forms

Each URL returned 200 on 2026-11-06, using the public repository shown. Replace the names. Shields rate limits are not stated in [its docs](https://shields.io/badges), so do not assume one.

| Badge | URL |
|---|---|
| Workflow, from GitHub | `https://github.com/cli/cli/actions/workflows/go.yml/badge.svg` |
| Workflow, from Shields | `https://img.shields.io/github/actions/workflow/status/cli/cli/go.yml?branch=trunk` |
| Latest release | `https://img.shields.io/github/v/release/cli/cli` |
| npm version | `https://img.shields.io/npm/v/express` |
| PyPI version | `https://img.shields.io/pypi/v/requests` |
| PyPI downloads | `https://img.shields.io/pypi/dm/requests` |
| Coverage from Codecov | `https://img.shields.io/codecov/c/github/psf/requests` |
| OpenSSF Scorecard | `https://img.shields.io/ossf-scorecard/github.com/ossf/scorecard` |
| License | `https://img.shields.io/github/license/cli/cli` |
| Static label | `https://img.shields.io/badge/style-flat-blue` |
| Endpoint, your own JSON | `https://img.shields.io/endpoint?url=<url-of-json>` |

Shields [styles](https://shields.io/badges) are flat (default), flat-square, plastic, for-the-badge and social. `logo` takes a simple-icons slug. `cacheSeconds` can only raise the cache time above each badge's default. Dynamic JSON, XML, YAML, TOML, Regex and Endpoint badges exist.

[Badgen](https://badgen.net/) offers classic and flat styles. Its page says nothing on caching.

## Writing them

- Link each badge to the thing it reports, such as the workflow runs or the package page.
- Give each badge alt text that names the fact, such as `CI status` or `npm version`.
- Keep long READMEs readable with reference-style definitions at the end of the file, as [gorhill/uBlock](https://github.com/gorhill/uBlock) does.
- Keep one style across the row.
- Load the row in both themes. A badge is a third-party image, so check that it returned, not only that it looks right in source.
