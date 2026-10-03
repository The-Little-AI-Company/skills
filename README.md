# The Little AI Company skills

Reusable agent skills organized by category. Each skill includes its instructions, examples, limits and validation record.

| Skill | Category | Purpose | Details |
| --- | --- | --- | --- |
| Statechart Design and Review | Design review | Review event-driven lifecycles with explicit states, guards, invariants and traces | [Catalog](catalog/statechart-design-review.md) |
| Resume drift check 0.2.0 | Recovery checks | Compare saved claims with current observations before resuming work | [Catalog](catalog/resume-drift-check.md) |

Open [the visual catalog](docs/index.html) from a downloaded copy in your browser. It works offline without scripts, external fonts or tracking. This repository does not require a hosted website.

## Install one skill

Use the official [skills CLI](https://github.com/vercel-labs/skills) from the project where you want the skill:

```text
pnpm dlx skills@1.7.0 add The-Little-AI-Company/skills --skill resume-drift-check --agent codex
```

For the existing design skill, replace the skill name with `statechart-design-review`. Omit `--agent codex` to choose another supported agent interactively. To inspect the collection before installing:

```text
pnpm dlx skills@1.7.0 add The-Little-AI-Company/skills --list
```

You can also copy the complete chosen folder into your agent's existing skill directory. Do not copy the collection root as one skill. The bundled Python tools require Python 3.10 or later and use only the standard library.

## Evidence and limits

Resume drift check 0.2.0 passed 49 tests on Linux. Independent review reproduced closure of its source-binding and FIFO findings. The Windows 11 check passed 47 suite tests with two POSIX-only skips and 13 additional CLI cases on Python 3.14.3. See [the testing record](skills/operations/resume-drift-check/TESTING.md) and [change history](skills/operations/resume-drift-check/CHANGELOG.md).

All 13 Statechart skill files are unchanged from the previously published source commit `06d9ea5c4ed5e6d4856c5838fbb9b2bd80c4eea8`.

These are bounded code and artifact checks. Neither skill has a measured evaluation of agent effectiveness, time savings or market demand. A matching report grants no authority to act. Review each skill's scope and limitations before use.

## License

MIT for authored text and code. Cited sources retain their rights.
