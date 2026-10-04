# Super Manus Builder

Make your agent build its own command center.

Category: Agent workspaces. Version: 0.2.0. Published October 4, 2026 UTC.

Direct an agent to extend its own tools and build a persistent GUI with Kanban, task controls, artifact editing, capability status, and real team activity. Adapts to the existing runtime and stack.

```sh
npx skills add The-Little-AI-Company/skills --skill agent-workspace-builder
```

- [Examples and requirements](../skills/agents/agent-workspace-builder/README.md)
- [Instructions](../skills/agents/agent-workspace-builder/SKILL.md)
- [Capability construction](../skills/agents/agent-workspace-builder/references/capability-construction.md)
- [GUI and Kanban](../skills/agents/agent-workspace-builder/references/gui-kanban.md)
- [Acceptance checks](../skills/agents/agent-workspace-builder/references/acceptance.md)

Includes a 60-capability reference map, framework adapter contracts, durable task/team patterns, editable media workflows, provider helpers, and an advisory board snapshot checker. No OpenDots dependency.

Validation: 22 offline media tests and 14 workspace snapshot tests passed. The skill is not a prebuilt application; live provider access, deployed GUI behavior, and comparative effectiveness are unverified. Python helpers require Python 3.10 or later with no third-party packages.

MIT for authored material. Referenced vendors and sources retain their rights.

The existing install ID stays unchanged. Version 0.2.0 adds clearer positioning, a first-use workflow, and an evidence-based demo and sharing playbook; it does not claim new production integrations.
