"""Run with: python -m unittest discover -s tests -p "test_*.py" -v"""

import json
import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
PR = SKILL / "assets" / "pr"
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
STYLES = ("plain-note", "comment-only", "gated-checklist", "release-line", "evidence-first", "commit-draft", "sign-off")


def fence_problems(text):
    """Pair fences the CommonMark way: a closer has the same character, at least the same length, and no info string."""
    opener = None
    for number, line in enumerate(text.splitlines(), 1):
        match = FENCE.match(line)
        if not match:
            continue
        run, info = match.groups()
        if opener is None:
            opener = (run, number)
        elif run[0] == opener[0][0] and len(run) >= len(opener[0]) and not info.strip():
            opener = None
    return [] if opener is None else [f"fence opened on line {opener[1]} never closes"]


class Fences(unittest.TestCase):
    def test_checker_catches_an_unbalanced_fence(self):
        self.assertTrue(fence_problems("```text\nx\n"))
        self.assertTrue(fence_problems("````markdown\n```\n"))
        self.assertFalse(fence_problems("```release-note\n\n```\n"))

    def test_every_markdown_asset_and_reference_is_balanced(self):
        files = list(SKILL.glob("assets/**/*.md")) + list(SKILL.glob("references/*.md")) + [SKILL / "README.md"]
        self.assertGreaterEqual(len(files), 12)
        for path in files:
            with self.subTest(path=path.name):
                self.assertEqual(fence_problems(path.read_text(encoding="utf-8")), [])


class Layout(unittest.TestCase):
    def test_seven_single_file_styles(self):
        for style in STYLES:
            self.assertTrue((PR / f"{style}.md").is_file(), style)

    def test_routed_set_is_a_tree(self):
        root = PR / "routed-set" / ".github"
        self.assertTrue((root / "PULL_REQUEST_TEMPLATE.md").is_file())
        for name in ("code.md", "docs.md"):
            self.assertTrue((root / "PULL_REQUEST_TEMPLATE" / name).is_file())

    def test_two_addons(self):
        self.assertEqual(sorted(p.name for p in (PR / "addons").iterdir()), ["ai-use.md", "stack-position.md"])

    def test_release_line_keeps_the_functional_fence(self):
        self.assertIn("```release-note", (PR / "release-line.md").read_text(encoding="utf-8"))

    def test_sign_off_links_and_does_not_restate_the_dco(self):
        text = (PR / "sign-off.md").read_text(encoding="utf-8")
        self.assertIn("https://developercertificate.org/", text)
        self.assertNotIn("Developer's Certificate of Origin 1.1", text)

    def test_every_reference_opens_with_when_to_read_it(self):
        names = {"hygiene", "health-files", "pr-templates", "settings", "branches", "history-rewrite", "guards"}
        self.assertEqual({p.stem for p in (SKILL / "references").glob("*.md")}, names)
        for path in (SKILL / "references").glob("*.md"):
            lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertTrue(lines[0].startswith("# "), path.name)
            self.assertTrue(lines[1].startswith("Read this "), path.name)
            self.assertIn("## Sources", lines, path.name)

    def test_ruleset_examples_are_valid_json(self):
        text = (SKILL / "references" / "settings.md").read_text(encoding="utf-8")
        blocks = re.findall(r"^```json$(.*?)^```$", text, re.MULTILINE | re.DOTALL)
        self.assertEqual(len(blocks), 3)
        for block in blocks:
            ruleset = json.loads(block)
            self.assertEqual(ruleset["enforcement"], "active")
            self.assertEqual(ruleset["bypass_actors"], [])

    def test_license_matches_the_repository_root(self):
        self.assertEqual((SKILL / "LICENSE").read_bytes(), (SKILL.parents[2] / "LICENSE").read_bytes())


if __name__ == "__main__":
    unittest.main()
