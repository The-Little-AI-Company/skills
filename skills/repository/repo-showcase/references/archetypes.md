# Archetypes

Read this when `exemplars.py` comes back thin, or to see what strong repositories of a type do. Each entry gives the type name used by `repo-audit`, the default preset from [presets.md](presets.md), and the measured exemplars.

All rows were measured on 2026-11-06 from each repository's default-branch README. These facts age. Rerun `exemplars.py` before relying on a number.

- The 69 exemplars were picked by hand and most are high star. They show what strong projects do, not what made them strong. No layout here is proven to cause success.
- Exemplars are patterns only. Copy no text from them.
- Lines, badges, images and first-screen order were measured by script. The Move column is judgment, except where it states a measured fact.
- Header badges are badges before the first `##`, or in the first 40 lines if there is none.
- First screen is a token sequence from the source, not a browser render. `H1` is a heading, `text` is prose, `links` is a link row, and `image:N` and `badges:N` count those items.
- `terraform-provider-aws`, `create-t3-app` and `developer-roadmap` are contrast cases, kept to show what a neighboring type does.
- `repo-audit` also reports the types `data` and `unknown`. Neither has measured exemplars. Pick the closest type here and say so.

Dead assets in these rows were dead on the measurement date and may recover. Treat them as examples of the failure, not as current defects.

## Library or package

Type `library`. Default preset `standard`. 71 to 2,814 lines, 2 to 11 header badges, 1 to 20 images, 1 to 106 code fences.

Lead with a runnable sample. Add a comparison table if alternatives exist. A full API reference in the README is what pushed axios to 2,814 lines, so link it out.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [psf/requests](https://github.com/psf/requests) | 77 | 5 (version 3, downloads 1, stars_social 1) | logo. Images 2, GIF 0, picture 0 | H1 > badges:5 > text > H2 > text > H2 > text | One-sentence tagline followed at once by a runnable code sample. Copy the order. |
| [sindresorhus/got](https://github.com/sindresorhus/got) | 365 | 2 (downloads 1, size 1) | sponsor logos, then logo. Images 8, GIF 0, picture 1 | image:1 > text > image:5 > text > badges:2 > text > links | Comparison table against named alternatives is useful. Avoid its sponsor block before the description, and note its live table badges failed on read (packagephobia 429, badgen 502). |
| [pydantic/pydantic](https://github.com/pydantic/pydantic) | 71 | 8 (version 3, ci 1, downloads 1, license 1, docs 1, static_label 1) | none. Images 1, GIF 0, picture 0 | H1 > badges:1 > image:1 > badges:7 > text > H2 | States the version split (V1.10 vs V2) in its own section near the top. |
| [axios/axios](https://github.com/axios/axios) | 2814 | 11 (other 3, size 2, version 1, ci 1, static_label 1, downloads 1, community 1, stars_social 1) | sponsor logos. Images 20, GIF 0, picture 0 | text | Weak model at 2,814 lines. The first screen is a notice and sponsors, and the table of contents sits below them. Shows what a full API reference does to a README. |

## CLI tool

Type `cli`. Default preset `reference`. 488 to 1,161 lines, 2 to 6 header badges, 1 to 18 images, 31 to 57 code fences.

Show the tool running in the first screen, then install per platform. Keep VHS tapes in the repository so demos can be rebuilt.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep) | 542 | 3 (ci 1, version 1, packaging 1) | terminal screenshot. Images 1, GIF 0, picture 0 | text > badges:3 > text > H3 | Benchmarks show the corpus, exact commands and a link to a longer analysis. Best sourced-number example in the sample. |
| [sharkdp/bat](https://github.com/sharkdp/bat) | 948 | 3 (ci 1, license 1, version 1) | logo plus demo screenshots. Images 4, GIF 0, picture 0 | image:1 > badges:3 > text | Centered logo, one-line purpose, inline link bar. Eight alerts exceed GitHub's guidance. |
| [junegunn/fzf](https://github.com/junegunn/fzf) | 1161 | 6 (stars_social 2, ci 1, version 1, license 1, funding 1) | logo plus preview screenshots. Images 10, GIF 0, picture 1 | image:1 > badges:6 > image:1 > text > image:2 > text > image:1 | Long manual with navigation. Twelve alerts exceed GitHub's guidance. |
| [charmbracelet/gum](https://github.com/charmbracelet/gum) | 488 | 2 (version 1, ci 1) | banner plus 12 VHS GIFs. Images 18, GIF 12, picture 0 | H1 > image:1 > badges:1 > image:1 > badges:1 > text > image:1 | One demo GIF per command, recorded with VHS. Largest is 2.6 MiB. Copy the per-command demo. |

## Web app or SaaS

Type `webapp`. Default preset `pitch`. 127 to 838 lines, 0 to 6 header badges, 3 to 10 images, 0 to 49 code fences.

Tagline, link bar, one screenshot, then why it differs. Separate the hosted and self-hosted paths, and state license and trademark.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [calcom/cal.com](https://github.com/calcom/cal.com) | 838 | 6 (static_label 2, license 1, stars_social 1, activity 1, docs 1) | banner plus GIF. Images 10, GIF 0, picture 0 | text > image:1 > text > badges:3 | Puts a warning about product scope first. Its 4.4 MiB GIF is under the proxy limit but still heavy. |
| [immich-app/immich](https://github.com/immich-app/immich) | 127 | 2 (license 1, community 1) | logo and screenshot collage. Images 5, GIF 0, picture 0 | badges:2 > image:1 > text > image:1 > text | Tagline, screenshot, then translated-README links. Uses Repobeats and contrib.rocks. Its 1.8 MiB collage is an alpha PNG. |
| [plausible/analytics](https://github.com/plausible/analytics) | 144 | 0 | icon. Images 3, GIF 0, picture 0 | H1 > image:1 > text > links > text > image:1 > H2 | Zero badges. Link bar plus differentiators under Why. Its 7.3 MiB contributors SVG fails on GitHub. |
| [supabase/supabase](https://github.com/supabase/supabase) | 289 | 0 | logo plus architecture diagram. Images 5, GIF 1, picture 0 | image:2 > H1 > text | Checklist of features, each with a docs link. How it works diagram. Uses the older theme fragments. |

## Framework

Type `framework`. Default preset `router`. 51 to 536 lines, 0 to 4 header badges, 0 to 26 images, 0 to 12 code fences.

Route to one getting-started path. The docs site is the manual.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [vercel/next.js](https://github.com/vercel/next.js) | 51 | 4 (static_label 2, version 1, license 1) | logo via picture. Images 2, GIF 0, picture 1 | image:2 > text > badges:4 > H2 > text > H2 > text | 51 lines, then all links outward. Good router. |
| [fastapi/fastapi](https://github.com/fastapi/fastapi) | 536 | 3 (version 2, ci 1) | logo plus sponsor logos. Images 26, GIF 0, picture 0 | image:1 > text > badges:1 > image:1 > badges:2 > text | Discloses its numbers come from an internal team estimate. Disclosure is better than none, but 16 images lack alt text. |
| [django/django](https://github.com/django/django) | 55 | 0 | none. Images 0, GIF 0, picture 0 | text | reStructuredText, zero images, zero badges. An ordered reading path through the docs. |
| [vuejs/core](https://github.com/vuejs/core) | 61 | 3 (version 1, ci 1, downloads 1) | sponsor images. Images 3, GIF 0, picture 0 | badges:3 > H2 > text > H2 > links > text > image:2 | Sends readers straight to the site. Its 3.3 MiB contributors SVG is page weight. |

## API or SDK client

Type `sdk`. Default preset `reference`. 735 to 1,267 lines, 0 to 3 header badges, 0 to 1 images, 38 to 50 code fences.

State requirements and supported versions before install. Frame reference content by task. Say if the code is generated.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [stripe/stripe-node](https://github.com/stripe/stripe-node) | 735 | 3 (version 1, ci 1, downloads 1) | none. Images 0, GIF 0, picture 0 | H1 > badges:3 > text > H2 > text > H2 > text | Requirements before installation. Reference content is framed by task. |
| [openai/openai-python](https://github.com/openai/openai-python) | 1267 | 1 (version 1) | none. Images 0, GIF 0, picture 0 | H1 > badges:1 > text > H2 > links > H2 > text | States the code is generated from an OpenAPI spec. One section per capability. |
| [octokit/octokit.js](https://github.com/octokit/octokit.js) | 978 | 0 | none. Images 1, GIF 0, picture 0 | H1 > text > H2 > text | Tagline as blockquote, then three numbered parts naming the package's composition. |

## ML model or data science

Type `ml`. Default preset `paper`. 135 to 340 lines, 6 to 9 header badges, 3 to 32 images, 2 to 9 code fences.

Lead with a key result. State intended use and limits, as the model card fields ask. A section on when not to use it is rare and worth copying.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [huggingface/transformers](https://github.com/huggingface/transformers) | 340 | 7 (other 1, ci 1, license 1, docs 1, version 1, static_label 1, doi 1) | logo via picture. Images 7, GIF 0, picture 1 | image:3 > badges:7 > text | A section titled When shouldn't I use it. Rare and worth copying. |
| [ultralytics/ultralytics](https://github.com/ultralytics/ultralytics) | 303 | 9 (community 3, other 3, ci 1, downloads 1, stars_social 1) | banner plus icon rows. Images 32, GIF 0, picture 0 | image:1 > links > badges:7 > image:1 > badges:2 > links | Nine header badges and repeated social icons. Example of load, not a model. |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | 135 | 6 (ci 3, version 2, license 1) | cover image, broken. Images 3, GIF 0, picture 0 | H1 > image:1 > text > badges:6 > links > H2 > text | Quick start comes before description. Hero image returns 404 because its asset repo moved the file. |

## Research or academic code

Type `research`. Default preset `paper`. 184 to 235 lines, 0 header badges, 1 to 7 images, 5 to 15 code fences.

One link line for paper, demo, weights and notebook. Then exact reproduce steps, a citation block and a pointer to any successor.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [openai/CLIP](https://github.com/openai/CLIP) | 200 | 0 | model diagram. Images 1, GIF 0, picture 0 | H1 > links > text > H2 > image:1 > H2 > text | One link line for blog, paper, model card and Colab, then a short approach section. |
| [CompVis/stable-diffusion](https://github.com/CompVis/stable-diffusion) | 216 | 0 | sample image grids. Images 7, GIF 0, picture 0 | H1 > links > text > links > image:1 > text > links | Paper title and author list first, BibTeX last. All images relative and committed. |
| [karpathy/nanoGPT](https://github.com/karpathy/nanoGPT) | 235 | 0 | illustration and loss curve. Images 2, GIF 0, picture 0 | H1 > image:1 > text > image:1 > text > H2 > text | Update note names the successor project. Its Discord badge host returns 404. |
| [facebookresearch/segment-anything](https://github.com/facebookresearch/segment-anything) | 184 | 0 | mask results and model diagram. Images 6, GIF 0, picture 0 | H2 > text > image:1 > text > H1 > text > links | Top section sends readers to the successor. Ends with a citation section. |

## Monorepo

Type `monorepo`. Default preset `router`. 49 to 124 lines, 4 to 10 header badges, 0 to 22 images, 0 to 2 code fences.

The root routes and each package owns its README. The four measured roots run 49 to 124 lines.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [babel/babel](https://github.com/babel/babel) | 124 | 8 (static_label 2, funding 2, downloads 1, ci 1, coverage 1, community 1) | logo plus sponsor logos. Images 16, GIF 0, picture 0 | image:1 > text > badges:5 > text > badges:3 > links | Short root. 15 sponsor images lack alt text. |
| [facebook/react](https://github.com/facebook/react) | 79 | 5 (ci 2, license 1, version 1, activity 1) | none. Images 0, GIF 0, picture 0 | badges:5 > text > links > text > H2 > text > H2 | Badges, one sentence, three value bullets, then links. Root stays at 79 lines in a large monorepo. |
| [vercel/turborepo](https://github.com/vercel/turborepo) | 49 | 4 (static_label 2, version 1, license 1) | logo via picture. Images 2, GIF 0, picture 1 | image:2 > text > badges:4 > text > H2 > text > H2 | 49 lines. Same shell as next.js. |
| [nrwl/nx](https://github.com/nrwl/nx) | 82 | 10 (other 5, version 1, stars_social 1, license 1, community 1, static_label 1) | logo via picture plus logo row. Images 22, GIF 0, picture 1 | image:2 > text > badges:10 > links | Quick Start then Why. Ten header badges is heavy. |

## Infrastructure or Terraform module

Type `infra`. Default preset `generated`. 29 to 762 lines, 0 to 4 header badges.

Usage first with a real source block. Generate inputs and outputs between markers, and fail CI on drift.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [terraform-aws-modules/terraform-aws-vpc](https://github.com/terraform-aws-modules/terraform-aws-vpc) | 762 | 0 | campaign banner only. Images 1, GIF 0, picture 0 | H1 > text > image:1 > H2 > text > H2 > text | Usage first with a real source block. Inputs and outputs live between BEGIN_TF_DOCS markers. |
| [cloudposse/terraform-aws-ecs-web-app](https://github.com/cloudposse/terraform-aws-ecs-web-app) | 592 | 4 (version 1, activity 1, other 1, static_label 1) | banner plus 9.8 MiB GIF. Images 6, GIF 1, picture 0 | image:1 > badges:4 > text > links > text > image:1 > links | README is generated from README.yaml. Fixed section set. The GIF is GitHub hosted, so it loads but is heavy. |
| [hashicorp/terraform-provider-aws](https://github.com/hashicorp/terraform-provider-aws) | 29 | 1 (static_label 1) | logo via picture. Images 3, GIF 0, picture 1 | image:3 > H1 > badges:1 > links > text | Not a module, listed for contrast. 29 lines that route to the Registry docs. |

## Mobile app

Type `mobile`. Default preset `showcase`. 36 to 71 lines, 1 to 8 header badges, 0 to 6 images, 0 code fences.

Short. Store links near the top. Reuse store listing images after compressing them.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [signalapp/Signal-Android](https://github.com/signalapp/Signal-Android) | 71 | 1 (store 1) | none. Images 0, GIF 0, picture 0 | H1 > text > links > badges:1 > links > H2 > text | Three sentences then store link. Keeps a cryptography notice. Mostly contributor guidance. |
| [AntennaPod/AntennaPod](https://github.com/AntennaPod/AntennaPod) | 45 | 8 (other 2, store 2, ci 1, license 1, version 1, activity 1) | six store screenshots. Images 6, GIF 0, picture 0 | H1 > badges:6 > text | Reuses store listing images, up to 1.7 MiB each. F-Droid and Play badges near the top. |
| [bitwarden/ios](https://github.com/bitwarden/ios) | 36 | 4 (ci 4) | logo via picture. Images 3, GIF 0, picture 1 | image:3 > badges:4 > H1 > links > H2 > text > H1 | 36 lines. Four CI badges are the whole status story. |

## Desktop app

Type `desktop`. Default preset `showcase`. 49 to 616 lines, 0 to 11 header badges.

Show the app before listing features. Give downloads per platform.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [flameshot-org/flameshot](https://github.com/flameshot-org/flameshot) | 616 | 11 (ci 3, other 2, version 2, store 2, downloads 1, license 1) | logo plus preview GIF. Images 2, GIF 1, picture 0 | image:1 > text > badges:11 | Preview section before features. Eleven header badges is too many. |
| [rustdesk/rustdesk](https://github.com/rustdesk/rustdesk) | 183 | 3 (store 2, static_label 1) | logo plus screenshots. Images 6, GIF 0, picture 0 | image:1 > text > links > text > links > badges:1 > links | Caution alert about misuse. Screenshots section at the end. |
| [zed-industries/zed](https://github.com/zed-industries/zed) | 49 | 2 (other 1, ci 1) | none. Images 0, GIF 0, picture 0 | H1 > badges:2 > links > H3 > links > text > H3 | 49 lines. Platform install links are the first content. |
| [microsoft/PowerToys](https://github.com/microsoft/PowerToys) | 122 | 0 | logo plus 30 utility icons. Images 36, GIF 0, picture 2 | image:2 > text > H2 > text | Table of utilities with relative icons. Zero badges. Two picture elements. |

## Game

Type `game`. Default preset `showcase`. 81 to 209 lines, 0 to 4 header badges.

State status and how to play before build steps. A gameplay image is the gap most of these leave open.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [ppy/osu](https://github.com/ppy/osu) | 148 | 4 (ci 1, version 1, other 1, community 1) | logo. Images 2, GIF 0, picture 0 | image:1 > H1 > badges:4 > image:1 > text > H2 > text | A Status section says how finished the project is. Copy for any early project. |
| [Anuken/Mindustry](https://github.com/Anuken/Mindustry) | 81 | 2 (ci 1, community 1) | logo. Images 1, GIF 0, picture 0 | image:1 > badges:2 > text > H2 > text > H2 > text | Short. Store badges come last under Downloads. |
| [OpenTTD/OpenTTD](https://github.com/OpenTTD/OpenTTD) | 209 | 0 | none. Images 0, GIF 0, picture 0 | H1 > H2 > text | Plain numbered contents and a licensing section. No images in a visual product, a gap for discovery. |

## GitHub Action

Type `action`. Default preset `reference`. 310 to 1,267 lines, 1 to 6 header badges.

Pinned `uses:` example first, one recipe per scenario, then inputs and outputs.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [actions/checkout](https://github.com/actions/checkout) | 389 | 1 (ci 1) | none. Images 0, GIF 0, picture 0 | badges:1 > H1 > H2 > text > H1 > H2 > text | Version in title, What's new, then one recipe per scenario. Best pattern for Actions. |
| [softprops/action-gh-release](https://github.com/softprops/action-gh-release) | 310 | 1 (ci 1) | demo screenshot. Images 1, GIF 0, picture 0 | text > image:1 > badges:1 > text | Good contents list. Its single badge uses a legacy URL that returns 404. |
| [peaceiris/actions-gh-pages](https://github.com/peaceiris/actions-gh-pages) | 1267 | 6 (version 2, ci 2, license 1, other 1) | logo plus workflow screenshots. Images 14, GIF 0, picture 0 | text > image:1 > badges:6 > text | Thorough, at 1,267 lines. A long list of options and examples. |

## Editor or browser plugin

Type `plugin`. Default preset `reference`. 69 to 432 lines, 5 to 7 header badges.

Requirements first. Test the README on the store page, where image rules differ.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [folke/lazy.nvim](https://github.com/folke/lazy.nvim) | 69 | 7 (activity 2, stars_social 2, version 1, license 1, other 1) | screenshot. Images 1, GIF 0, picture 0 | text > badges:7 > text > image:1 | Link bar then badges, then features and requirements, and docs live elsewhere. |
| [darkreader/darkreader](https://github.com/darkreader/darkreader) | 226 | 5 (static_label 5) | logo plus sponsor images. Images 14, GIF 0, picture 0 | image:1 > text > badges:5 > text > H2 > text > H2 | Two contributor and backer SVGs near 3.7 MiB are page weight. |
| [gorhill/uBlock](https://github.com/gorhill/uBlock) | 190 | 7 (activity 2, other 2, license 1, version 1, static_label 1) | logo plus store buttons. Images 11, GIF 0, picture 0 | badges:2 > image:1 > badges:5 > text > image:1 > text > image:1 | Reference-style badge definitions keep the source readable. Four images lack alt text. |
| [prettier/prettier-vscode](https://github.com/prettier/prettier-vscode) | 432 | 5 (other 2, static_label 2, ci 1) | none. Images 0, GIF 0, picture 0 | H1 > text | Zero non-badge images, which also avoids Marketplace SVG limits. |

## Design system or UI kit

Type `design-system`. Default preset `router`. 18 to 163 lines, 0 to 11 header badges.

Short root, a component preview and a link to Storybook or docs.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | 18 | 0 | Open Graph image. Images 1, GIF 0, picture 0 | H1 > text > image:1 > H2 > text > H2 > text | 18 lines, three sections. Smallest README in the sample outside profiles. |
| [primer/react](https://github.com/primer/react) | 54 | 4 (version 1, stars_social 1, activity 1, license 1) | logo. Images 1, GIF 0, picture 0 | image:1 > text > badges:2 > text > badges:1 > H2 > text | Short root with a component-proposal section. |
| [mui/material-ui](https://github.com/mui/material-ui) | 163 | 11 (version 2, license 1, downloads 1, ci 1, coverage 1, stars_social 1, static_label 1, other 1, funding 1, security_quality 1) | logo via picture. Images 11, GIF 0, picture 2 | image:1 > text > badges:11 > links | Doc routing is good. Eleven header badges are not. |

## Docs or book

Type `docs`. Default preset `router`. 70 to 192 lines, 0 to 4 header badges.

Split the reader path from the contributor path. Send readers to the rendered book.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [rust-lang/book](https://github.com/rust-lang/book) | 108 | 1 (ci 1) | none. Images 0, GIF 0, picture 0 | H1 > badges:1 > text > H2 > text > H2 > text | Addresses contributors, not readers. Sends readers to the rendered book. |
| [getify/You-Dont-Know-JS](https://github.com/getify/You-Dont-Know-JS) | 70 | 0 | book covers. Images 7, GIF 0, picture 0 | H1 > text > image:3 > text > H2 > text > links | Covers link to titles. Uses the older theme fragments. |
| [kamranahmedse/developer-roadmap](https://github.com/kamranahmedse/developer-roadmap) | 192 | 4 (static_label 4) | logo plus roadmap thumbnails. Images 5, GIF 0, picture 0 | image:1 > text > badges:4 > image:1 > text > H3 > image:1 | Educational content site, not a book, listed as docs-adjacent. Share badges are static labels. |

## Dotfiles or config

Type `dotfiles`. Default preset `standard`. 88 to 289 lines, 0 header badges, 0 to 2 images, 1 to 8 code fences.

Warn readers to review before running. State the OS and how to customize. Explain the organizing idea.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [mathiasbynens/dotfiles](https://github.com/mathiasbynens/dotfiles) | 112 | 0 | shell screenshot. Images 2, GIF 0, picture 0 | H1 > image:1 > H2 > text > H3 > text > H3 | Warns readers to fork and review before running. Copy that warning. |
| [thoughtbot/dotfiles](https://github.com/thoughtbot/dotfiles) | 289 | 0 | prompt screenshot. Images 2, GIF 0, picture 0 | H1 > image:1 > H2 > text > H2 > text | Requirements, install, update, then customization. Written for reuse. |
| [holman/dotfiles](https://github.com/holman/dotfiles) | 88 | 0 | none. Images 0, GIF 0, picture 0 | H1 > text > H2 > text | Explains the organizing idea before the install. |

## Awesome list

Type `awesome-list`. Default preset `standard`. 867 to 4,158 lines, 0 to 6 header badges.

Terse entries under a `Contents` section. Watch the 500 KiB truncation limit as the list grows.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [sindresorhus/awesome](https://github.com/sindresorhus/awesome) | 867 | 0 | logo via picture. Images 5, GIF 0, picture 1 | image:1 > text > image:3 > text | Sponsors precede content. Contents list and terse entries define the genre. |
| [vinta/awesome-python](https://github.com/vinta/awesome-python) | 1244 | 0 | none. Images 0, GIF 0, picture 0 | H1 > text > H2 > text > H2 > text | Points to a searchable website for browsing. |
| [avelino/awesome-go](https://github.com/avelino/awesome-go) | 4158 | 6 (other 2, ci 1, awesome 1, community 1, activity 1) | logo. Images 3, GIF 0, picture 0 | H1 > image:1 > badges:6 > links > image:1 > text > image:1 | 415 KiB, 83 percent of GitHub's truncation limit. The clearest risk case. |

## Profile README

Type `profile`. Default preset `own choice`. 9 to 286 lines, 0 to 1 header badges.

Link to work. Pick from [profile.md](profile.md). `exemplars.py` cannot search this type, so start from the rows below.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [simonw/simonw](https://github.com/simonw/simonw) | 61 | 0 | none. Images 0, GIF 0, picture 0 | links > H3 > text > H3 > text | A scheduled workflow rewrites marked blocks with recent releases and posts. Live content, no stat cards. |
| [sindresorhus/sindresorhus](https://github.com/sindresorhus/sindresorhus) | 27 | 0 | 14 relative GIFs. Images 15, GIF 14, picture 0 | image:15 | All images local, but 14 lack alt text. |
| [kentcdodds/kentcdodds](https://github.com/kentcdodds/kentcdodds) | 9 | 0 | single banner. Images 1, GIF 0, picture 0 | text | Nine lines. One image with descriptive alt text and one link. |
| [DenverCoder1/DenverCoder1](https://github.com/DenverCoder1/DenverCoder1) | 286 | 1 (stars_social 1) | banners, stat cards, 82 label badges. Images 38, GIF 0, picture 0 | image:3 > text > image:1 > text > image:1 > text > image:1 | Maximalist, 128 images. Runs its own stats instance, as the stats project advises. |

## Template or starter

Type `template`. Default preset `standard`. 142 to 637 lines, 0 to 6 header badges.

Say what the user replaces and what constraints they accept.

| Repository | Lines | Header badges | Visual | First screen | Move |
|---|---|---|---|---|---|
| [t3-oss/create-t3-app](https://github.com/t3-oss/create-t3-app) | 142 | 4 (community 1, activity 1, version 1, downloads 1) | logo via picture. Images 5, GIF 0, picture 1 | image:2 > text > badges:4 > image:1 > text > H2 > text | A generator CLI, not a template repo, so it is contrast. Run command in the first screen. |
| [cookiecutter/cookiecutter-django](https://github.com/cookiecutter/cookiecutter-django) | 271 | 6 (other 2, ci 1, version 1, static_label 1, community 1) | no hero, book cover lower down. Images 4, GIF 0, picture 0 | H1 > badges:4 > image:1 > badges:2 > text | Features, Optional Integrations, and a Constraints section state what you give up. |
| [ixartz/Next-js-Boilerplate](https://github.com/ixartz/Next-js-Boilerplate) | 637 | 0 | banner plus 14 picture icon pairs. Images 50, GIF 0, picture 14 | H1 > text > links > text > H2 > image:5 | Full theme support for icon rows. Two H2s over 637 lines is a weak outline. |
