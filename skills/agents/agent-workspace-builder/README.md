# Super Manus Builder

**Make your agent build its own command center.**

Give your coding agent a job: build the tools and workspace it needs to finish the next one.

Super Manus Builder is an open-source skill from The Little AI Company. It directs an agent to add missing capabilities, register real tools, and build a GUI where you can assign work, watch tasks move, inspect results, and make changes.

## Try it in your project

Use a coding agent with access to your project and permission to edit it. Run:

```sh
npx skills add The-Little-AI-Company/skills --skill agent-workspace-builder
```

Then give the agent this prompt:

```text
Use agent-workspace-builder to build my Super Manus.

Inspect this project and keep the stack that already works. Build a persistent
GUI with Kanban, task details, pause/resume/cancel controls, editable artifacts,
and a capability catalog. Use independent agent workers where the runtime
supports them, and show their real activity.

Start with a CSV-analysis workflow. When a required tool is missing, implement
it, test it, register it, and resume the task. Let me open and revise the result.
Keep tasks and outputs across refresh and restart. Label sample data synthetic.

Use existing model access. My external-spend ceiling is $0. Finish the local
workflow, and report any provider-dependent features that need configuration.
```

The install command adds the skill. Your agent then builds the application in your environment. Model usage and external providers can have separate costs. Append `--agent codex` to the install command to select Codex directly; omit it to choose interactively.

## The part worth showing

Ask for an analysis tool your agent does not have yet. Watch it create the tool, connect it to a real task, produce an output, and let you edit that output from the workspace.

That is the first demonstration to build and verify. [The demo playbook](references/show-and-share.md) explains what to record, how to make it reproducible, and what evidence supports each claim.

## Where you can take it

| Build goal | What the skill directs the agent to implement |
| --- | --- |
| Research desk | Source-backed research, task assignments, reports, and editable tables |
| Creative studio | Images, storyboards, video, narration, captions, and editable source tracks |
| Agent command center | Kanban, dependencies, real worker activity, controls, and restart recovery |
| Working tool collection | Discover, implement, test, register, and reuse missing capabilities |
| Delivery workspace | Documents, decks, spreadsheets, code, previews, downloads, and revisions |
| Connected workflows | Configured APIs/MCP, schedules, account scope, and spending limits |

The bundle maps 60 researched capability families to implementation paths and acceptance checks. It includes fal/Higgsfield queue helpers, task/team contracts, and a board snapshot checker. Its Python scripts require Python 3.10 or later and the standard library.

[Read the skill](SKILL.md) · [Inspect the capability map](references/manus-capabilities.md) · [See the GUI/Kanban contract](references/gui-kanban.md)

Building on CopilotKit? Use [Super Manus for OpenDots](https://skills.sh/the-little-ai-company/skills/opendots-super-manus).

## Checks

```sh
python scripts/check_bundle.py
python scripts/test_workspace_check.py
python scripts/workspace_check.py assets/workspace.example.json
python scripts/test_media_queue.py
```

The board checker inspects supplied snapshots only. It cannot authenticate evidence, inspect live workers, establish security, or authorize an action. Its example is synthetic. The media helper is a local single-operator fal/Higgsfield client, not a production scheduler or shared-budget service.

## Limits

This package is a skill and helper collection, not a prebuilt dashboard application. The agent must implement and verify the requested app in its actual environment. Instructions cannot create missing accounts, bypass host limits, turn one context into independent agents, or grant native Codex tools to another runtime.

22 media fixture tests and 14 workspace snapshot tests passed before this presentation update. Live providers, deployed GUI behavior, and comparative agent effectiveness were not tested. A successful structural check is advisory. See [acceptance](references/acceptance.md).

MIT for authored text and code. External sources retain their rights. This is independent work from The Little AI Company, with no affiliation with the cited vendors.
