# The Little AI Company skills

Reusable agent skills organized by category. Each skill includes its instructions, examples, limits and validation record.

## Build your Super Manus

**Make your agent build its own command center.**

Super Manus Builder gives your coding agent instructions for building tools, a persistent Kanban workspace, agent teams, and results you can edit. Start with a real task; have the agent build the missing capability and use it.

```sh
npx skills add The-Little-AI-Company/skills --skill agent-workspace-builder
```

[Get the first-build prompt](skills/agents/agent-workspace-builder/README.md) · [Find it on skills.sh](https://skills.sh/the-little-ai-company/skills/agent-workspace-builder)

Already using CopilotKit OpenDots? [Use the OpenDots edition](skills/agents/opendots-super-manus/README.md).

These packages contain skills and local helpers. Your agent must implement and verify the workspace. Model access and paid services are configured separately.

## The collection

| Skill | Category | Purpose | Details |
| --- | --- | --- | --- |
| Statechart Design and Review | Design review | Review event-driven lifecycles with explicit states, guards, invariants and traces | [Catalog](catalog/statechart-design-review.md) |
| Resume drift check 0.2.0 | Recovery checks | Compare saved claims with current observations before resuming work | [Catalog](catalog/resume-drift-check.md) |
| Super Manus Builder 0.2.0 | Agent workspaces | Extend any agent with reusable capabilities, GUI, Kanban, artifacts, and teams | [Catalog](catalog/agent-workspace-builder.md) |
| Super Manus for OpenDots 0.2.0 | Agent workspaces | Build Manus-style workflows, agent teams, and editable image/video production on OpenDots | [Catalog](catalog/opendots-super-manus.md) |

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

Install Super Manus for OpenDots:

```sh
npx skills add The-Little-AI-Company/skills --skill opendots-super-manus
```

See its [usage examples and requirements](skills/agents/opendots-super-manus/README.md).

For other agent runtimes, install the generic version:

```sh
npx skills add The-Little-AI-Company/skills --skill agent-workspace-builder
```

See [its examples and GUI/Kanban scope](skills/agents/agent-workspace-builder/README.md).

## Evidence and limits

Resume drift check 0.2.0 passed 49 tests on Linux. Independent review reproduced closure of its source-binding and FIFO findings. The Windows 11 check passed 47 suite tests with two POSIX-only skips and 13 additional CLI cases on Python 3.14.3. See [the testing record](skills/operations/resume-drift-check/TESTING.md) and [change history](skills/operations/resume-drift-check/CHANGELOG.md).

All 13 Statechart skill files are unchanged from the previously published source commit `06d9ea5c4ed5e6d4856c5838fbb9b2bd80c4eea8`.

The OpenDots skill passed 22 offline queue tests and two independent workflow checks. Its 60-capability map is an implementation guide; live providers and a complete OpenDots deployment were not verified.

The generic skill passed the same 22 media fixture tests plus 14 workspace snapshot checks. It guides implementation of the GUI and capabilities; it does not bundle a finished application.

These are bounded code and artifact checks. No skill in this collection has a measured evaluation of agent effectiveness, time savings or market demand. A matching report grants no authority to act. Review each skill's scope and limitations before use.

[Demo and launch drafts](docs/super-manus-launch.md) are available for promotion. They describe the published skill and distinguish intended builds from observed results.

## License

MIT for authored text and code. Cited sources retain their rights.
