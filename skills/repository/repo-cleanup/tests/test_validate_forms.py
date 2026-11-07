"""Run with: python -m unittest discover -s tests -p "test_*.py" -v"""

import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))
sys.dont_write_bytecode = True

import validate_forms as vf  # noqa: E402

GOOD = """name: Bug report
description: Something broke.
labels: ["bug"]
body:
  - type: textarea
    id: observed
    attributes:
      label: What happened
    validations:
      required: true
  - type: dropdown
    id: history
    attributes:
      label: Did this work before
      options:
        - "Yes"
        - Not sure
"""


def run(path):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = vf.main([str(path)])
    return code, out.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name) / ".github" / "ISSUE_TEMPLATE"
        self.folder.mkdir(parents=True)

    def form(self, text, name="bug.yml"):
        path = self.folder / name
        path.write_bytes(text.encode("utf-8"))
        return path

    def assert_fails(self, text, needle, line=None, name="bug.yml"):
        self.form(text, name)
        code, out = run(Path(self.tmp.name))
        self.assertEqual(code, 1, out)
        self.assertIn(needle, out)
        if line is not None:
            self.assertIn(f"{name}:{line}: error", out)


class ShippedAssets(unittest.TestCase):
    def test_every_set_passes(self):
        for size in ("small", "medium", "large"):
            with self.subTest(size=size):
                code, out = run(SKILL / "assets" / "issue-forms" / size)
                self.assertEqual(code, 0, out)
                self.assertIn(" 0 errors", out)

    def test_each_set_is_a_real_tree(self):
        for size, count in (("small", 3), ("medium", 3), ("large", 3)):
            files = list((SKILL / "assets" / "issue-forms" / size / ".github" / "ISSUE_TEMPLATE").iterdir())
            self.assertEqual(len(files), count)

    def test_mutated_copy_of_a_shipped_form_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "large"
            shutil.copytree(SKILL / "assets" / "issue-forms" / "large", target)
            path = target / ".github" / "ISSUE_TEMPLATE" / "01-bug.yml"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("    id: steps", "    id: logs"), encoding="utf-8")
            code, out = run(target)
            self.assertEqual(code, 1, out)
            self.assertIn("duplicate id", out)

    def test_parser_reads_the_values_that_trap_simple_parsers(self):
        folder = SKILL / "assets" / "issue-forms" / "large" / ".github" / "ISSUE_TEMPLATE"
        config = vf.parse((folder / "config.yml").read_text(encoding="utf-8"))
        urls = [item.get("url").value for item in config.get("contact_links").items]
        self.assertIn("https://github.com/OWNER/REPO#readme", urls)
        form = vf.parse((folder / "01-bug.yml").read_text(encoding="utf-8"))
        self.assertEqual(form.get("title").value, "<area>: <short summary>")
        self.assertEqual([i.value for i in form.get("labels").items], ["bug"])
        last = form.get("body").items[-1]
        options = last.get("attributes").get("options").items
        self.assertEqual(options[0].get("required").value, "true")
        self.assertEqual(last.line, 103)


class Syntax(Base):
    def test_good_form_passes(self):
        self.form(GOOD)
        self.assertEqual(run(Path(self.tmp.name))[0], 0)

    def test_tab_in_indentation(self):
        self.assert_fails(GOOD.replace("    id: observed", "\tid: observed"), "tab in indentation", 6)

    def test_tab_after_spaces_in_indentation(self):
        self.assert_fails(GOOD.replace("    id: observed", "  \tid: observed"), "tab in indentation", 6)

    def test_indent_too_deep(self):
        self.assert_fails(GOOD.replace("    id: observed", "     id: observed"), "bad indentation", 6)

    def test_key_deeper_than_a_scalar(self):
        self.assert_fails(GOOD.replace("    attributes:\n      label: What", "      attributes:\n      label: What"), "bad indentation")

    def test_dedent_to_no_open_level(self):
        self.assert_fails(GOOD.replace("    id: observed", "   id: observed"), "bad indentation", 6)

    def test_unterminated_quote(self):
        self.assert_fails(GOOD.replace('- "Yes"', '- "Yes'), "unterminated")

    def test_unquoted_colon_in_value(self):
        self.assert_fails(GOOD.replace("description: Something broke.", "description: Note: it broke."), "must be quoted", 2)

    def test_duplicate_key(self):
        self.assert_fails(GOOD.replace("labels:", "name: Other\nlabels:"), "duplicate key", 3)

    def test_anchor_is_refused(self):
        self.assert_fails(GOOD.replace("description: Something broke.", "description: *anchor"), "unsupported")

    def test_flow_list_across_lines_is_refused(self):
        self.assert_fails(GOOD.replace('labels: ["bug"]', 'labels: ["bug",\n  "x"]'), "flow list")

    def test_second_document_is_refused(self):
        self.assert_fails(GOOD + "---\nname: Two\n", "more than one")

    def test_empty_file(self):
        self.assert_fails("", "empty document", 1)

    def test_not_utf8(self):
        (self.folder / "bug.yml").write_bytes(b"name: \xff\xfe\n")
        self.assertEqual(run(Path(self.tmp.name))[0], 1)

    def test_list_at_key_indent_and_comments_and_crlf(self):
        text = GOOD.replace("  - type", "- type").replace("    id:", "  id:").replace("    attributes:", "  attributes:")
        text = text.replace("      label:", "    label:").replace("    validations:", "  validations:")
        text = text.replace("      required:", "    required:").replace("      options:", "    options:")
        text = text.replace("        - ", "    - ")
        text = "# leading comment\n" + text.replace("\n", "  # note\n").replace("\n", "\r\n")
        self.form(text)
        code, out = run(Path(self.tmp.name))
        self.assertEqual(code, 0, out)

    def test_multi_line_plain_scalar_and_folded_block(self):
        text = GOOD.replace("description: Something broke.", "description: Something\n  broke badly.\ntitle: >-\n  folded: text is fine\n\n  here")
        self.form(text)
        code, out = run(Path(self.tmp.name))
        self.assertEqual(code, 0, out)
        self.assertEqual(vf.parse(text).get("description").value, "Something broke badly.")


class FormRules(Base):
    def test_missing_name(self):
        self.assert_fails(GOOD.replace("name: Bug report\n", ""), "name is required")

    def test_short_name(self):
        self.assert_fails(GOOD.replace("name: Bug report", "name: Bug"), "more than 3 characters", 1)

    def test_missing_description(self):
        self.assert_fails(GOOD.replace("description: Something broke.\n", ""), "description is required")

    def test_body_not_a_list(self):
        self.assert_fails("name: Bug report\ndescription: x y\nbody: nothing\n", "nonempty list", 3)

    def test_body_only_markdown(self):
        text = "name: Bug report\ndescription: x y\nbody:\n  - type: markdown\n    attributes:\n      value: hello\n"
        self.assert_fails(text, "not markdown", 3)

    def test_unknown_type(self):
        self.assert_fails(GOOD.replace("type: textarea", "type: slider"), "unknown or missing type", 5)

    def test_unknown_top_key(self):
        self.assert_fails(GOOD.replace("labels:", "label:"), "unknown top-level key")

    def test_duplicate_id(self):
        self.assert_fails(GOOD.replace("id: history", "id: observed"), "duplicate id", 12)

    def test_bad_id_characters(self):
        self.assert_fails(GOOD.replace("id: observed", "id: has.dot"), "may hold only")

    def test_missing_field_label(self):
        self.assert_fails(GOOD.replace("      label: What happened\n", "      description: x\n"), "has no label")

    def test_checkbox_option_without_label(self):
        text = GOOD + "  - type: checkboxes\n    id: c\n    attributes:\n      label: Confirm\n      options:\n        - required: true\n"
        self.assert_fails(text, "checkbox option has no label", 23)

    def test_duplicate_field_label_after_normalizing(self):
        self.assert_fails(GOOD.replace("label: Did this work before", "label: what happened?"), "duplicates or normalizes")

    def test_top_level_labels_are_optional_with_a_warning(self):
        self.form(GOOD.replace('labels: ["bug"]\n', ""))
        code, out = run(Path(self.tmp.name))
        self.assertEqual(code, 0, out)
        self.assertIn("warning: no top-level labels", out)

    def test_duplicate_top_level_label(self):
        self.assert_fails(GOOD.replace('["bug"]', '["bug", bug]'), "duplicate")

    def test_none_option(self):
        self.assert_fails(GOOD.replace("- Not sure", "- None"), "reserved")

    def test_unquoted_yes_option(self):
        self.assert_fails(GOOD.replace('- "Yes"', "- Yes"), "quote it", 16)

    def test_duplicate_option(self):
        self.assert_fails(GOOD.replace("- Not sure", '- "Yes"'), "duplicate option")

    def test_boolean_key(self):
        self.assert_fails(GOOD.replace("      label: What happened", "      label: What happened\n      on: x"), "read as a boolean")

    def test_blocked_label_word(self):
        self.assert_fails(GOOD.replace("label: What happened", "label: Your password"), "GitHub blocks")

    def test_required_must_be_boolean(self):
        self.assert_fails(GOOD.replace("required: true", "required: sure"), "true or false")

    def test_render_only_on_textarea(self):
        text = GOOD.replace("      label: Did this work before", "      label: Did this work before\n      render: text")
        self.assert_fails(text, "only to textarea")

    def test_default_with_none_like_option(self):
        text = GOOD.replace("- Not sure", "- n/a").replace("      options:", "      default: 0\n      options:")
        self.assert_fails(text, "cannot combine")

    def test_duplicate_name_across_forms(self):
        self.form(GOOD, "a.yml")
        self.form(GOOD, "b.yml")
        code, out = run(Path(self.tmp.name))
        self.assertEqual(code, 1)
        self.assertIn("also used by a.yml", out)


class ConfigRules(Base):
    GOOD = "blank_issues_enabled: false\ncontact_links:\n  - name: Help\n    url: https://example.test/help#top\n    about: Ask here.\n"

    def test_good(self):
        self.form(self.GOOD, "config.yml")
        self.assertEqual(run(Path(self.tmp.name))[0], 0)

    def test_unknown_key(self):
        self.assert_fails("blank_issues: false\n", "unknown key", 1, "config.yml")

    def test_blank_must_be_boolean(self):
        self.assert_fails("blank_issues_enabled: maybe\n", "true or false", 1, "config.yml")

    def test_contact_without_url(self):
        self.assert_fails(self.GOOD.replace("    url: https://example.test/help#top\n", ""), "needs url", 3, "config.yml")

    def test_contact_without_about(self):
        self.assert_fails(self.GOOD.replace("    about: Ask here.\n", ""), "needs about", 3, "config.yml")

    def test_contact_unknown_key(self):
        self.assert_fails(self.GOOD + "    link: x\n", "unknown key", 6, "config.yml")

    def test_placeholder_warns(self):
        self.form(self.GOOD.replace("https://example.test/help#top", "https://github.com/OWNER/REPO/issues"), "config.yml")
        code, out = run(Path(self.tmp.name))
        self.assertEqual(code, 0)
        self.assertIn("placeholder", out)


class Inputs(unittest.TestCase):
    def test_missing_path_is_bad_input(self):
        self.assertEqual(run(Path("no-such-path-here"))[0], 2)

    def test_checkout_without_forms_is_bad_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "mkdocs.yml").write_text("site_name: x\n", encoding="utf-8")
            self.assertEqual(run(Path(tmp))[0], 2)

    def test_markdown_templates_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "ISSUE_TEMPLATE"
            folder.mkdir()
            (folder / "bug.md").write_text("---\nname: x\n---\n", encoding="utf-8")
            (folder / "bug.yml").write_text(GOOD, encoding="utf-8")
            code, out = run(folder)
            self.assertEqual(code, 0, out)
            self.assertIn("1 files", out)

    def test_single_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bug.yml"
            path.write_text(GOOD, encoding="utf-8")
            self.assertEqual(run(path)[0], 0)


if __name__ == "__main__":
    unittest.main()
