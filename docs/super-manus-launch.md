# Super Manus launch kit

Drafts for The Little AI Company. No social posts have been sent. These describe the published skill; add real application footage only after implementing and verifying it.

## Main pitch

Make your agent build its own command center.

Super Manus Builder is an open-source skill that directs a coding agent to build tools, a GUI with Kanban, real team workflows, and outputs you can edit. Give it a project and a useful first task. It inspects the runtime, builds the missing capability, registers it, and works toward a complete request-to-result workflow.

Install the skill, then use the first-build prompt in the README. Your agent still needs to implement and verify the application. Model usage and external services may cost money.

https://skills.sh/the-little-ai-company/skills/agent-workspace-builder

## Short post

I gave our agent-building skill a very specific job: build the tools AND the workspace.

Super Manus Builder covers Kanban, agent teams, task controls, and results you can edit. It’s open source. Your coding agent does the implementation.

https://skills.sh/the-little-ai-company/skills/agent-workspace-builder

## Builder-community post

I published Super Manus Builder, a skill for asking a coding agent to build its own working environment.

The first-build prompt asks for a CSV-analysis workspace. The agent should inspect the project, build and register a missing analysis tool, connect it to a real task board, and produce a report you can revise. Tasks and outputs should survive refresh and restart.

The package includes instructions for extending that into research, documents, images, video, connectors, and agent teams. There are 60 researched capability mappings, provider helpers, and explicit implementation checks.

The current evidence covers the skill and helper tests. A finished application still has to be built and verified in your environment. I’m interested in where that process gets stuck: missing tools, confusing setup, or work the agent cannot finish.

Install:
`npx skills add The-Little-AI-Company/skills --skill agent-workspace-builder`

First-build prompt and source:
https://github.com/The-Little-AI-Company/skills/tree/main/skills/agents/agent-workspace-builder

## A demo to build and record

Title: “I asked my agent to build the tool it was missing.”

Show an actual missing CSV-analysis capability, its construction task, the registered tool running, the resulting chart/report, and one edit. Refresh the workspace and show the retained result. Capture real events and label synthetic input. A 30–60 second edit can work; disclose time-lapses and avoid implying that the build took the clip’s duration.

If the application has not been built, record a walkthrough of the published skill and installation instead. Do not use generated UI footage as proof that the product runs.

End card: “Build your own Super Manus” plus the skill URL or install command. Captions should remain readable on a phone.

## Variant for OpenDots builders

Building with CopilotKit OpenDots? Super Manus for OpenDots maps the existing project to agent teams, durable work, editable deliverables, and image/video providers. It includes concrete integration points and checks for each requested capability.

`npx skills add The-Little-AI-Company/skills --skill opendots-super-manus`

https://skills.sh/the-little-ai-company/skills/opendots-super-manus

## Evidence behind the copy

- Generic helper suite: 22 offline media tests and 14 workspace snapshot tests previously passed.
- Both public install commands were verified during the initial publication.
- Independent workflow checks exercised the instructions; they did not build or certify a deployed application.
- No comparative effectiveness, measured savings, adoption, or virality result is claimed.
- Independent skills from The Little AI Company; no affiliation with Manus, CopilotKit, or the named media providers.
