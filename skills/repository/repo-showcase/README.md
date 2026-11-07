# Repository showcase

Version 0.1.0, checked 2026-11-06. Make a repository's front page as good as the best repositories of its type. The skill covers the README, badges, screenshots, demos, banners, social preview and GitHub profile pages, in a style the owner chooses.

The skill keeps two jobs apart. The pitch earns attention on the first screen. The proof earns trust in linked sections below it. Both stay accurate.

## Installation

Use Python 3.10 or later and an authenticated [GitHub CLI](https://cli.github.com/). No Python packages are required. Install only this skill into a project with the skills CLI. Replace `owner/repo` with the repository that hosts this collection:

```text
pnpm dlx skills@1.7.0 add owner/repo --skill repo-showcase --agent codex
```

Omit `--agent codex` to choose another supported agent interactively. Alternatively, copy this entire folder into the agent's skill directory.

## Try it

Ask your agent: "Make this repository's front page as good as the best CLI tools." The agent asks who the page is for, offers presets with real examples, and works through the steps in [SKILL.md](SKILL.md).

Run these commands from this folder to use the scripts directly:

```text
python scripts/exemplars.py --type cli --language go --limit 5
python scripts/render_readme.py path/to/README.md --out preview --repo owner/repo --ref main
```

## What it produces

- A first-screen plan with one sentence, one visual and one next step.
- A README in one of seven presets: `router`, `standard`, `reference`, `showcase`, `pitch`, `paper` or `generated`.
- Captured visuals, compressed, with alt text.
- Exact values and commands for the owner's settings.
- Light and dark renders scored against three exemplars.

| Reference | Use it for |
|---|---|
| [presets.md](references/presets.md) | The seven styles and the default per type |
| [archetypes.md](references/archetypes.md) | 69 measured exemplars across 20 types |
| [visuals.md](references/visuals.md) | Choosing and capturing each kind of visual, with size limits |
| [badges.md](references/badges.md) | `none`, `signal` and `full` policies, and URL forms |
| [profile.md](references/profile.md) | Personal and organization profile pages |
| [surfaces.md](references/surfaces.md) | Description, topics, social preview, releases and registries |
| [rubric.md](references/rubric.md) | Scoring a rendered first screen in 8 categories |

## exemplars.py

| Flag | Meaning |
|---|---|
| `--type` | Repository type, using the names from `repo-audit`. `profile` cannot be searched and exits 2. |
| `--language` | Primary language |
| `--topic` | One GitHub topic. It replaces the search terms of `--type`. |
| `--min-stars` | Lowest star count. Default 500. |
| `--limit` | Repositories to measure, 1 to 30. Default 10. |
| `--output` | Also write the report to this file |

The script uses read-only `gh search repos` and `gh api` calls. It drops forks, archived repositories and those with no push in 18 months. For each README it measures lines, header badges, images, GIFs, `<picture>` elements, alt coverage, section order and first-screen elements. It prints a Markdown table and medians.

Search results are candidates. A broad type such as `library` can return lists and applications, so open them before you trust a median. reStructuredText READMEs are measured on a best-effort basis, and a badge defined as a substitution there counts where it is defined.

## render_readme.py

| Flag | Meaning |
|---|---|
| `--out` | Output folder. Default `preview`. |
| `--repo` | `owner/repo`. Sets reference context and resolves relative paths. |
| `--ref` | Branch, tag or commit for relative paths. Default `HEAD`. |
| `--base` | Folder of the file inside the repository, for a README not at the root |

The script sends the file's text to GitHub's Markdown API in `gfm` mode, then writes `light.html` and `dark.html` with [github-markdown-css](https://github.com/sindresorhus/github-markdown-css) 5.9.0 from jsDelivr. The pages use a fixed 1012 pixel column on `#ffffff` and `#0d1117`.

- **Relative images need `--repo`.** The API returns relative paths unchanged. With `--repo`, images point at `raw.githubusercontent.com` at `--ref` and links point at the blob view. Without it, the script writes the pages and exits 1 with a note.
- **A private repository needs a decision first.** The script sends the README to GitHub. Raw image URLs for a private repository do not load in a local page.
- **Each page picks its theme image.** A browser would otherwise follow the operating system's theme.
- **Diagrams stay as source.** GitHub draws Mermaid and similar blocks only on its own pages, so the script exits 1 with a note.
- **External images load through GitHub's proxy,** as on a real page, so an oversized image fails here too.
- **The CSS approximates GitHub.** The package is a copy of GitHub's Markdown styles, not the live page. Check the final page on GitHub.

## Outputs and exit codes

Both scripts exit 0 when all is well and 2 on bad input. Exit 1 needs attention. For `exemplars.py`, the search failed or fewer than 3 repositories were measured. For `render_readme.py`, GitHub could not be reached or a page differs from what GitHub shows, and stderr says how.

Neither script changes a repository. Both treat README text as data.

## Checks and limits

```text
python -m unittest discover -s tests -p "test_*.py"
```

The 56 tests stub every network call. Both scripts also ran once against live GitHub on 2026-11-06.

- First-screen order is a token sequence from the source, not a browser render. The rendered page and the rubric cover that.
- The rubric's scales are opinion. No study validates them.
- The 69 exemplars were picked by hand and are mostly high star. They show what strong projects do, not what made them strong.
- The image proxy limit is measured, undocumented and could change.
- The npm and PyPI handling of relative images, and several store rules, were not verified. [surfaces.md](references/surfaces.md) lists them.

## Sources and license

Facts in the references link to their sources, including [GitHub's documentation](https://docs.github.com/), [Standard Readme](https://github.com/RichardLitt/standard-readme), [Make a README](https://www.makeareadme.com/), [awesome-readme](https://github.com/matiassingers/awesome-readme) and [Trockman et al.](https://par.nsf.gov/servlets/purl/10063054). Exemplar repositories are cited as patterns, and no text was copied from them.

Authored material uses the [MIT license](LICENSE). Source authors retain their rights.
