# OpenDots Super Manus

A researched skill for building and operating a Manus-style workspace on [CopilotKit OpenDots](https://github.com/CopilotKit/OpenDots), with agent teams and image/video production.

## Install

Run this from the project where you want the skill:

```sh
npx skills add The-Little-AI-Company/skills --skill opendots-super-manus
```

Choose your agent interactively, or append `--agent codex` for Codex. Installing instructions does not install an OpenDots application or provision provider accounts. The complete folder is also usable with agents that load the SKILL.md format.

## Use

Ask your agent:

> Use opendots-super-manus to audit this OpenDots checkout. Map the requested capabilities to actual source, then implement agent teams and durable media jobs through a complete vertical slice. Preserve existing behavior and distinguish implemented, configured, and verified capabilities.

Or:

> Use opendots-super-manus to prepare a 30-second product video with generated stills, narration, captions, and an editable timeline. Inspect the available tools and provider access first, preserve individual shots for later editing, and stay within my stated budget.

## Included

- 60 capability mappings with Manus usage, OpenDots implementation paths, and acceptance gates.
- Nine focused references covering integration, agent teams, runtime contracts, media providers, production, general workflows, source research, and verification.
- Research across 44 indexed Manus documentation pages plus release and provider sources, retrieved October 4, 2026 UTC.
- A read-only OpenDots source audit and a local fal/Higgsfield queue client with persistent request receipts.
- Machine-readable capabilities, team roles, a run-contract example, and an editable timeline example.

Read [SKILL.md](SKILL.md) for the entry point and [the source register](references/sources.md) for provenance and refresh instructions.

## Checks

Python 3.10 or later; standard library only. Run from this skill folder:

```sh
python scripts/check_bundle.py
python scripts/test_media_queue.py
python scripts/audit_opendots.py /path/to/OpenDots
```

The package passed 22 offline queue tests and two bounded independent-agent workflow checks. No paid provider generation or deployed OpenDots integration was tested. See [acceptance and evidence limits](references/acceptance.md).

## Limits and costs

The skill supplies procedures, reference contracts, and local helpers. Implement the production adapters, scheduler, editable UI, storage, authorization, and shared budget enforcement in the target app. The local queue client is for a single operator; it is not a production service.

Codex's native image tool is usable only where the host actually exposes it. A separate OpenDots deployment needs its own supported API or MCP integration. Provider keys stay server-side; paid generation needs existing spending authorization. No credentials are bundled.

This is an independent project from The Little AI Company, unaffiliated with Manus, CopilotKit, fal, or Higgsfield. Product names identify the researched platforms. Authored material is MIT-licensed; cited sources retain their rights.
