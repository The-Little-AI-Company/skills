# Agent Workspace Builder

A runtime-independent skill that directs an agent to build reusable tools and a persistent workspace GUI with Kanban, task controls, editable artifacts, and agent teams.

## Install

```sh
npx skills add The-Little-AI-Company/skills --skill agent-workspace-builder
```

Run from your target project and choose an agent. Append `--agent codex` to select Codex. Python 3.10 or later is required for the bundled standard-library scripts.

## Use

> Use agent-workspace-builder to inspect this agent runtime, build its missing capabilities, and create a GUI with Kanban, task details, real progress, artifact editing, team activity, and settings. Implement a complete request-to-artifact slice first, then finish the requested features. Preserve the existing stack and stay within my budget.

For a narrower first slice:

> Give this Python CLI agent a local workspace GUI. Implement a CSV-analysis capability, register it as a real tool, and let me create, run, inspect, and revise analysis tasks from the board. Preserve tasks and outputs across refresh and restart.

## What it builds

- A capability construction loop: discover, implement, test, register, configure, verify, expose, and resume the original task.
- A durable board with Backlog, Ready, Running, Blocked, Review, Done, and Canceled columns; explicit paused and pending-cancellation states.
- Task details with dependencies, attempts, actual events, costs, controls, evidence, and artifact links.
- Capability catalog, artifact workspace, agent-team visibility, connectors, settings, and schedules.
- Integration contracts that adapt to the actual agent runtime; no OpenDots requirement.
- Research, office files, code/apps/games, image/video/audio, browser work, and automations through 60 researched reference capabilities.

Read [SKILL.md](SKILL.md), [capability construction](references/capability-construction.md), [runtime integration](references/runtime-integration.md), and [GUI/Kanban behavior](references/gui-kanban.md).

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

22 media fixture tests and 14 workspace snapshot tests passed. Live providers, deployed GUI behavior, and comparative agent effectiveness were not tested. A successful structural check is advisory. See [acceptance](references/acceptance.md).

MIT for authored text and code. External sources retain their rights. This is independent work from The Little AI Company, with no affiliation with the cited vendors.
