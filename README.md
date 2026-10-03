# The Little AI Company skills

Reusable agent skills, organized by category. Each skill has a `SKILL.md` entrypoint and keeps its references, examples, and scripts together.

## Catalog

| Category | Skill | Use it for |
| --- | --- | --- |
| Design | [Statechart Design and Review](skills/design/statechart-design-review/) | Model and review event-driven lifecycles, cancellation, recovery, and concurrency |

## Install a skill

Clone the collection:

```sh
git clone https://github.com/The-Little-AI-Company/skills.git
```

Copy the selected skill directory into your agent's documented skill location. For Statechart Design and Review, copy `skills/design/statechart-design-review` from inside the cloned repository. Keep the folder name and all its contents. Do not copy the collection root as a single skill.

If you already use the [skills CLI](https://github.com/vercel-labs/skills), you can select this skill by name:

```sh
skills add The-Little-AI-Company/skills --skill statechart-design-review
```

The category layout follows the CLI's documented [skill discovery rules](https://github.com/vercel-labs/skills#skill-discovery). Installation locations and discovery rules vary by agent. Consult your agent's current documentation before replacing an existing skill.

## Use and validate

Start with the selected skill's README for example prompts, prerequisites, local checks, and validation limits. The Statechart Design and Review scripts use Python 3.10 or newer and the standard library.

From this repository's root:

```sh
cd skills/design/statechart-design-review
python3 scripts/check_inventory.py examples/minimal-inventory.json
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tests/export_safety_test.py
```

The inventory linter checks structure. It does not prove statechart behavior or determinism. The synthetic export model checks a bounded safety invariant, with its limits documented beside the skill.

## Layout and license

Skills live at `skills/<category>/<skill-name>/SKILL.md`. Add a category when a published skill needs it, and link the skill in the catalog.

The authored material uses the [MIT license](LICENSE). Linked third-party sources retain their own rights and licenses. Source attribution appears with each skill.
