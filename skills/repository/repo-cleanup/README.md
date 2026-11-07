# Repository cleanup

Version 0.1.0, checked 2026-11-06. Turn a repository audit into small, safe, reviewable changes, and leave guards that stop the mess coming back. The skill covers stale branches, ignore rules, line endings, CI hardening, PR and issue templates, community health files, repository settings and history rewrites.

The two Python scripts only read. `branch_triage.py` classifies branches and never deletes one. `validate_forms.py` reads issue forms. Everything else is guidance that an agent follows, with force pushes, deletions, setting changes and public actions waiting for the owner's yes.

## Installation

Use Python 3.10 or later. No packages are required. Install only this skill into a project with the official skills CLI:

```text
pnpm dlx skills@1.7.0 add The-Little-AI-Company/skills --skill repo-cleanup --agent codex
```

Run that command from the project where you want the skill. Omit `--agent codex` to choose another supported agent interactively. Alternatively, copy this entire folder into the agent's existing skill directory. Git is required, and `gh` is optional.

Pair it with `repo-audit`, which produces the `audit.json` this skill starts from.

## Try it

Run these commands from this folder. The first checks a shipped form set. The second classifies the branches of a local clone and writes a ledger outside it.

```text
python scripts/validate_forms.py assets/issue-forms/medium
python scripts/branch_triage.py path/to/clone --output ../branches.tsv
```

The first prints warnings for the `OWNER/REPO` placeholders and exits 0. The second prints verdict counts to stderr and says nothing was deleted.

## What is here

| Path | What it holds |
|---|---|
| [SKILL.md](SKILL.md) | The eight-step cleanup an agent follows |
| [references/hygiene.md](references/hygiene.md) | A recipe per mechanical fix, split by language |
| [references/health-files.md](references/health-files.md) | Which community files fit each of 18 repository types |
| [references/pr-templates.md](references/pr-templates.md) | Eight PR styles, two add-ons, and what the research says |
| [references/settings.md](references/settings.md) | `gh` commands and rulesets for the owner to run |
| [references/branches.md](references/branches.md) | Verdict meanings and rules that never lose work |
| [references/history-rewrite.md](references/history-rewrite.md) | The rewrite playbook, rotation first |
| [references/guards.md](references/guards.md) | Checks that keep it clean, and where failures show |
| `assets/pr/` | One template per style. Routed Set is a small tree, since it has three files |
| `assets/issue-forms/` | Small, medium and large sets as `.github/ISSUE_TEMPLATE/` trees |

## Branch triage output

The TSV has `verdict`, `sha`, `date` and `name`. `ANCESTOR` and `CANDIDATE-merged-pr-tip` can be proposed for deletion. `SQUASH-EQUIVALENT` and `PATCHES-ALL-APPLIED` go to a human, because reverted work can read as applied. Every `KEEP` verdict stays.

Exit 0 means every branch is a keep. Exit 1 means attention is needed, or PR data was missing. Exit 2 means bad input. Shallow and partial clones exit 2, since the proofs need every object. The tool refuses an output path inside the audited repository, and it refuses to overwrite an old ledger.

The synthetic squash runs in a temporary object directory, so the audited clone gains no objects. The tests compare every metadata file before and after.

## Form validator output

Each problem prints as `file:line: error: message`. Exit 0 means no errors, 1 means errors found, 2 means bad input. The parser reads the YAML subset that forms use, and it reports anything else, such as an anchor or a flow list across lines, as an error. A tab in indentation or bad indentation fails.

It checks required keys, field types, unique ids, field labels, dropdown rules and `config.yml` keys. Top-level `labels` are optional in GitHub's schema, so a form without them gets a warning. It cannot see which labels exist in a repository, and only GitHub can give the final answer.

## Checks and limits

```text
python -m unittest discover -s tests -p "test_*.py" -v
```

The tests build fixture repositories in temporary folders with hermetic git configuration, including the nine branch shapes from the research. They need no network. The `gh` paths are tested with substituted data.

Not verified:

- The history rewrite playbook was not run end to end. Nothing was force pushed.
- No `gh` write command in `settings.md` was run. Endpoints and fields were checked against GitHub's OpenAPI description. Read-backs were run.
- Branch deletion and the restore command were not run.
- The scheduled workflow, the pre-commit config and the gitleaks, actionlint and zizmor commands were not run.
- Forms were validated by this parser, not by GitHub.
- Effects on agent behavior or repository outcomes were not measured.

## Sources and license

Facts come from the sources linked in each reference, read on 2026-11-06. Template and form text was written fresh for this skill. The Contributor Covenant and the Developer Certificate of Origin are linked and never restated, since their terms do not fit MIT text. github/gitignore templates are CC0.

Authored material uses the [MIT license](LICENSE). Source authors retain their rights.
