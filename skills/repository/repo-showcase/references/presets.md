# Presets

Read this in step 1 to offer styles, and in step 5 to write. A preset is the owner's choice. The type sets only the default. Report which preset the repository already resembles before proposing a change.

The seven names match `readme_preset` in `.github/repo-standards.json` and the PRS-015 check in `repo-audit`.

Line and badge caps in this file are opinion, drawn from the ranges measured on 2026-11-06. No source sets them. Length is bimodal by audience: routers ran 18 to 124 lines, SDK references 735 to 1,267, and other self-contained manuals started near 400. One length target would be wrong.

The pitch stays on the first screen in every preset. Proof goes in linked sections lower down.

## router

**Use when** a docs site exists and is the real manual. This fits frameworks, monorepo roots and design systems.

**Includes** logo or title, one-sentence purpose, at most 4 status badges, a getting-started command or link, and links to docs, community, contributing and security. Under about 120 lines.

**Exemplars** [vercel/next.js](https://github.com/vercel/next.js) (51 lines) and [shadcn-ui/ui](https://github.com/shadcn-ui/ui) (18 lines).

## standard

**Use when** a library has no docs site, or a team wants a checkable contract.

**Includes** the [Standard Readme](https://github.com/RichardLitt/standard-readme/blob/main/spec.md) order: title, optional banner and badges, short description, contents past 100 lines, install, usage, API, contributing, license. The spec keeps the short description under 120 characters, matches it to the package manager and GitHub descriptions, and puts License last.

**Exemplar** [RichardLitt/standard-readme](https://github.com/RichardLitt/standard-readme) (129 lines).

## reference

**Use when** the README is the manual. This fits SDKs, GitHub Actions and CLIs.

**Includes** purpose, requirements, install, then one section per task with runnable code, navigation, and a support policy. Few images. Keep well below the 500 KiB truncation limit.

**Exemplars** [actions/checkout](https://github.com/actions/checkout) (389 lines), [stripe/stripe-node](https://github.com/stripe/stripe-node) (735 lines) and [BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep) (542 lines).

## showcase

**Use when** seeing the product sells it. This fits desktop apps, TUIs, UI kits and games.

**Includes** a hero image or demo within the first screen, theme variants through `<picture>`, one demo per major feature, and small committed assets.

**Exemplars** [charmbracelet/gum](https://github.com/charmbracelet/gum) (one VHS GIF per command) and [microsoft/PowerToys](https://github.com/microsoft/PowerToys) (utility table).

## pitch

**Use when** a product competes for adoption. This fits self-hosted apps and open core SaaS.

**Includes** tagline, link bar (demo, docs, hosted), why it differs, one screenshot or architecture diagram, a self-hosting path, and license and trademark notes. Every claim links to evidence.

**Exemplars** [plausible/analytics](https://github.com/plausible/analytics) (zero badges) and [supabase/supabase](https://github.com/supabase/supabase) (feature checklist with docs links).

## paper

**Use when** code accompanies a publication or model.

**Includes** paper title and authors, one link line (paper, demo, weights, Colab), key figure, install, reproduce steps, model or data licenses, citation block, and a pointer to any successor. No status badges by default. For a hosted model, add the [model card](https://huggingface.co/docs/hub/model-cards) fields.

**Exemplars** [openai/CLIP](https://github.com/openai/CLIP) and [facebookresearch/segment-anything](https://github.com/facebookresearch/segment-anything).

## generated

**Use when** the facts live in code or metadata. This fits Terraform modules, generated SDKs and data-driven lists.

**Includes** a hand-written head (purpose and usage), generated regions between markers, and a CI check that fails on drift. If the whole file is generated, add a do-not-edit notice.

**Exemplars** [terraform-aws-modules/terraform-aws-vpc](https://github.com/terraform-aws-modules/terraform-aws-vpc) (`BEGIN_TF_DOCS` region) and [cloudposse/terraform-aws-ecs-web-app](https://github.com/cloudposse/terraform-aws-ecs-web-app) (generated from README.yaml). [terraform-docs](https://terraform-docs.io/) generates module docs.

## Default per type

Type names match `repo-audit`. The Also offer column is opinion, so step 1 can name two or three real choices. In the Default column, `short` is a length hint and not part of the preset name.

| Type | Default | Also offer | Lead visual | Badge default | Specific rule |
|---|---|---|---|---|---|
| `library` | standard | reference, router | Code sample | CI, version, license only if useful | Sample runs as written. Comparison table if alternatives exist. |
| `cli` | reference | showcase | Terminal GIF or screenshot | CI, version, packaging | Show install per platform. Prefer VHS tapes kept in the repo. |
| `webapp` | pitch | showcase, router | Screenshot | 0 to 3 | Separate hosted and self-hosted paths. State license and trademark. |
| `framework` | router | pitch | Logo with theme support | Up to 4 | Link a single getting-started path. |
| `sdk` | reference | router | None | Version, CI | State requirements, versions and support. Say if generated. |
| `ml` | paper | showcase | Key result or figure | Version, CI, DOI | Add intended use, limits, data and metrics, as model cards ask. |
| `research` | paper | none | Paper figure | None, or DOI | Citation block, exact reproduce steps, status, successor pointer. |
| `monorepo` | router | pitch | Logo | Up to 5 | Root routes. Each package owns its README. |
| `infra` | generated | reference | None, or architecture | None required | [Registry rules](surfaces.md#terraform-registry) apply only to public modules. |
| `mobile` | showcase, short | pitch | Screenshots | Store badges, CI | Reuse store images after compressing. |
| `desktop` | showcase | pitch | Screenshot or GIF | Version, downloads if real | Downloads per platform. Code signing note if any. |
| `game` | showcase | pitch | Gameplay screenshot | CI at most | State status and how to play before build steps. |
| `action` | reference | none | None | Version | Pinned `uses:` example first. One recipe per scenario. Inputs and outputs. |
| `plugin` | reference, short | showcase | Demo | Store or version | Check [Marketplace limits](surfaces.md#vs-code-marketplace). Requirements first. |
| `design-system` | router | showcase | Component preview | Up to 4 | Link Storybook or docs. |
| `docs` | router | standard | Cover or none | CI at most | Separate reader path from contributor path. Install and usage are optional in Standard Readme. |
| `dotfiles` | standard, short | none | Prompt screenshot | None | Warn readers to review before running. State OS and how to customize. |
| `awesome-list` | standard | none | Logo optional | Awesome badge if eligible | The [listing rules](https://github.com/sindresorhus/awesome/blob/main/pull_request_template.md) apply only to entries in sindresorhus/awesome: a `Contents` section, no license section, no CI badge, CC0 or a CC license, and 30 days old. |
| `profile` | own choice | any | Banner or none | None needed | Follow [profile.md](profile.md). |
| `template` | standard, short | reference | Feature list | CI | Say what the user replaces. State constraints. A repository [made from a template](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template) starts with a single commit. |

`repo-audit` falls back to `standard` for the types `data` and `unknown`. No exemplars were measured for them.

## Rules that hold in every preset

Report these as defects:

- An external image over the proxy limit in [visuals.md](visuals.md#size-limits).
- An image or badge that returns 404 after an encoded, repeated, spaced recheck. Treat 429, 502 and 509 as unknown until repeated later.
- A README near 500 KiB. Warn at 400 KiB. GitHub truncates past 500 KiB.
- `<picture>` with no `<img>` fallback or no alt text.
- Non-allowlisted SVG in a VS Code extension README, or a non-HTTPS image there.
- Relative images in a README that publishes to a surface where they will not resolve.

Report these as warnings with evidence:

- A non-badge image with no alt text.
- More than 2 alerts, or consecutive alerts. GitHub says to use one or two per article, and not to place them consecutively or nest them.
- Purpose not stated before sponsors or notices.
- Numbers with no date, method or link.

Offer these and never fail on them:

- Removing star, fork or license badges.
- Adding a table of contents past 100 lines. No exemplar under 100 lines has one. 12 of 19 READMEs over 400 lines have navigation near the top, and GitHub builds an Outline from headings.
- Adding a hero image, GIF or diagram.
- Switching preset.
