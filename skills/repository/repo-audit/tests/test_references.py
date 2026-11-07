"""Holds the reference files to the tool they describe. Run with: python -m unittest discover -s tests -p "test_*.py" -v"""

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.dont_write_bytecode = True

import checks_git  # noqa: E402
import checks_github  # noqa: E402,F401
import checks_readme  # noqa: E402
from detect import TYPES  # noqa: E402
from engine import REGISTRY, load_policy  # noqa: E402

REFERENCES = sorted((ROOT / "references").glob("*.md"))
WRITTEN = REFERENCES + [ROOT / "README.md"]
POLICY = (ROOT / "references" / "policy.md").read_text("utf-8")
CHECK_ID = re.compile(r"\b(?:HIS|BRN|TAG|IGN|SEC|CI|SUP|GOV|MET|DOC|PRS)-\d{3}\b")


def prose(text: str) -> str:
    text = re.sub(r"^```.*?^```\s*$", "", text, flags=re.M | re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def policy_example() -> str:
    return re.search(r"```json\n(.*?)```", POLICY, re.S).group(1)


class Policy(unittest.TestCase):
    def test_every_key_the_tool_knows_is_documented(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.json"
            path.write_text(policy_example(), "utf-8")
            loaded, notes = load_policy(None, path)
        self.assertEqual(notes, [])
        for key in loaded:
            self.assertIn(f"`{key}`", POLICY)
        self.assertEqual(len(loaded), 15)

    def test_example_values_are_real(self):
        data = json.loads(policy_example())
        self.assertIn(data["type"], TYPES)
        for waiver in data["waivers"]:
            self.assertIn(waiver["check"], REGISTRY)
            self.assertRegex(waiver["expires"], r"^\d{4}-\d{2}-\d{2}$")

    def test_every_type_is_listed(self):
        for kind in TYPES:
            self.assertIn(f"`{kind}`", POLICY)


class Text(unittest.TestCase):
    def test_every_check_id_exists(self):
        for path in WRITTEN:
            for found in CHECK_ID.findall(path.read_text("utf-8")):
                self.assertIn(found, REGISTRY, f"{path.name} names {found}")

    def test_style_rules(self):
        for path in WRITTEN:
            text = path.read_text("utf-8")
            self.assertNotIn("—", text, path.name)
            self.assertNotIn(";", prose(text), path.name)

    def test_no_file_trips_the_audit_it_documents(self):
        for path in WRITTEN:
            for n, line in enumerate(path.read_text("utf-8").split("\n"), 1):
                self.assertIsNone(checks_git.KEY_SHAPES.search(line), f"{path.name}:{n}")
                self.assertIsNone(checks_readme.HOME_PATH.search(line), f"{path.name}:{n}")

    def test_relative_links_resolve(self):
        for path in WRITTEN:
            for target in re.findall(r"\]\((?!https?:|#)([^)#]+)", path.read_text("utf-8")):
                if target.endswith("report.md") and not (ROOT / "references" / "report.md").exists():
                    continue
                self.assertTrue((path.parent / target).exists(), f"{path.name} links {target}")


if __name__ == "__main__":
    unittest.main()
