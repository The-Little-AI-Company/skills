"""Tests for scripts/render_readme.py. Every gh call is stubbed, so nothing reaches the network."""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import render_readme  # noqa: E402

# The shapes below were captured from POST /markdown on 2026-11-06.
API_PAGE = """<h1 dir="auto">Hi</h1>
<p dir="auto"><a target="_blank" rel="noopener noreferrer" href="docs/a.png"><img src="docs/a.png" alt="rel" style="max-width: 100%;"></a></p>
<p dir="auto"><themed-picture data-catalyst-inline="true"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/d.png"><source media="(prefers-color-scheme: light)" srcset="https://camo.githubusercontent.com/abc" data-canonical-src="https://example.com/l.png"><img alt="x" src="docs/l.png"></picture></themed-picture></p>
<p dir="auto"><a href="docs/x.md">doc</a> <a href="#hi">anc</a> <a href="mailto:a@example.com">mail</a> <a href="https://example.com/y">out</a></p>
"""
MERMAID = '<section data-type="mermaid"><pre lang="mermaid">graph TD</pre></section>'


class Rewrite(unittest.TestCase):
    def rewrite(self, page=API_PAGE, repo="o/r", ref="v1", base=""):
        return render_readme.rewrite_urls(page, repo, ref, base)

    def test_relative_images_become_raw_urls(self):
        page, left = self.rewrite()
        self.assertEqual(left, [])
        self.assertIn('<img src="https://raw.githubusercontent.com/o/r/v1/docs/a.png"', page)
        self.assertIn('srcset="https://raw.githubusercontent.com/o/r/v1/docs/d.png"', page)

    def test_relative_links_become_blob_urls(self):
        self.assertIn('<a href="https://github.com/o/r/blob/v1/docs/x.md">', self.rewrite()[0])

    def test_absolute_anchor_and_mail_stay(self):
        page = self.rewrite()[0]
        for kept in ('href="#hi"', 'href="mailto:a@example.com"', 'href="https://example.com/y"', 'srcset="https://camo.githubusercontent.com/abc"'):
            self.assertIn(kept, page)

    def test_base_folder_and_parent_paths(self):
        page, _ = self.rewrite('<img src="../assets/a.png">', base="docs/guide")
        self.assertIn("/o/r/v1/docs/assets/a.png", page)

    def test_root_relative_path(self):
        self.assertIn("/o/r/v1/assets/a.png", self.rewrite('<img src="/assets/a.png">', base="docs")[0])

    def test_query_and_fragment_survive(self):
        self.assertIn("/o/r/v1/a.png#gh-dark-mode-only", self.rewrite('<img src="a.png#gh-dark-mode-only">')[0])

    def test_path_outside_the_repository_is_reported(self):
        self.assertEqual(self.rewrite('<img src="../../x.png">')[1], ["../../x.png"])

    def test_without_repo_nothing_changes_and_paths_are_reported(self):
        page, left = self.rewrite(repo=None)
        self.assertEqual(page, API_PAGE)
        self.assertIn("docs/a.png", left)
        self.assertIn("docs/x.md", left)

    def test_every_url_attribute_in_a_tag_is_rewritten(self):
        page, _ = self.rewrite('<img src="a.png" srcset="b.png 2x">')
        self.assertIn('src="https://raw.githubusercontent.com/o/r/v1/a.png"', page)
        self.assertIn('srcset="https://raw.githubusercontent.com/o/r/v1/b.png 2x"', page)

    def test_lookalike_attributes_and_text_stay(self):
        page = '<img data-canonical-src="a.png" src="https://example.com/a.png"><p>src="b.png"</p>'
        self.assertEqual(self.rewrite(page), (page, []))

    def test_srcset_keeps_descriptors(self):
        page, _ = self.rewrite('<source srcset="a.png 1x, b.png 2x">')
        self.assertIn("/o/r/v1/a.png 1x, https://raw.githubusercontent.com/o/r/v1/b.png 2x", page)


class Theme(unittest.TestCase):
    def test_each_page_keeps_only_its_own_source(self):
        dark = render_readme.apply_theme(API_PAGE, "dark")
        light = render_readme.apply_theme(API_PAGE, "light")
        self.assertIn('<source srcset="docs/d.png">', dark)
        self.assertNotIn("camo.githubusercontent.com/abc", dark)
        self.assertNotIn("docs/d.png", light)
        self.assertNotIn("prefers-color-scheme", dark + light)

    def test_other_media_queries_stay(self):
        page = '<picture><source media="(min-width: 600px)" srcset="w.png"><img src="n.png"></picture>'
        self.assertEqual(render_readme.apply_theme(page, "dark"), page)

    def test_text_outside_a_picture_is_untouched(self):
        page = '<p><code>media="(prefers-color-scheme: dark)"</code></p>'
        self.assertEqual(render_readme.apply_theme(page, "light"), page)

    def test_wrap_sets_background_column_and_pinned_css(self):
        for theme, color in (("light", "#ffffff"), ("dark", "#0d1117")):
            page = render_readme.wrap("<p>x</p>", theme, "README.md")
            self.assertIn(f"background: {color}", page)
            self.assertIn("width: 1012px", page)
            self.assertIn(f"github-markdown-css@5.9.0/github-markdown-{theme}.css", page)

    def test_wrap_hides_the_other_theme_fragment(self):
        self.assertIn('img[src$="#gh-light-mode-only"]', render_readme.wrap("", "dark", "x"))
        self.assertIn('img[src$="#gh-dark-mode-only"]', render_readme.wrap("", "light", "x"))

    def test_title_is_escaped(self):
        self.assertIn("&lt;b&gt;", render_readme.wrap("", "dark", "<b>"))


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.readme = self.dir / "README.md"
        self.readme.write_text("# Hi\n", encoding="utf-8")

    def invoke(self, argv, reply=API_PAGE):
        calls = []

        def run(args, stdin):
            calls.append((args, stdin))
            if isinstance(reply, Exception):
                raise reply
            return reply

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(render_readme, "run_gh", run), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = render_readme.main(argv)
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue(), calls

    def test_writes_both_pages_and_prints_paths(self):
        out = self.dir / "preview"
        code, stdout, stderr, _ = self.invoke([str(self.readme), "--out", str(out), "--repo", "o/r"])
        self.assertEqual((code, stderr), (0, ""))
        self.assertEqual(stdout.split(), [str(out / "light.html"), str(out / "dark.html")])
        self.assertIn("raw.githubusercontent.com/o/r/HEAD/docs/a.png", (out / "dark.html").read_text(encoding="utf-8"))

    def test_request_uses_gfm_on_stdin_with_context(self):
        _, _, _, calls = self.invoke([str(self.readme), "--out", str(self.dir / "p"), "--repo", "o/r"])
        args, stdin = calls[0]
        self.assertEqual(args, ["api", "markdown", "--method", "POST", "--input", "-"])
        self.assertEqual(json.loads(stdin), {"text": "# Hi\n", "mode": "gfm", "context": "o/r"})

    def test_no_context_without_repo(self):
        _, _, _, calls = self.invoke([str(self.readme), "--out", str(self.dir / "p")])
        self.assertNotIn("context", json.loads(calls[0][1]))

    def test_relative_paths_without_repo_exit_1_and_say_why(self):
        code, _, stderr, _ = self.invoke([str(self.readme), "--out", str(self.dir / "p")])
        self.assertEqual(code, 1)
        self.assertIn("Pass --repo owner/repo", stderr)
        self.assertTrue((self.dir / "p" / "light.html").exists())

    def test_mermaid_is_flagged(self):
        code, _, stderr, _ = self.invoke([str(self.readme), "--out", str(self.dir / "p"), "--repo", "o/r"], API_PAGE + MERMAID)
        self.assertEqual(code, 1)
        self.assertIn("mermaid blocks show as source", stderr)

    def test_api_failure_exits_1_and_writes_nothing(self):
        out = self.dir / "p"
        code, _, stderr, _ = self.invoke([str(self.readme), "--out", str(out)], render_readme.GhError("HTTP 401"))
        self.assertEqual(code, 1)
        self.assertIn("HTTP 401", stderr)
        self.assertFalse(out.exists())

    def test_bad_input_exits_2_before_any_call(self):
        cases = [
            [str(self.dir / "missing.md")],
            [str(self.readme), "--repo", "not a slug"],
            [str(self.readme), "--ref", "../../evil"],
            [str(self.readme), "--ref", 'x" onerror="y'],
            [str(self.readme), "--base", "../up"],
            [str(self.readme), "--out", str(self.readme)],
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                code, _, _, calls = self.invoke(argv)
                self.assertEqual((code, calls), (2, []))

    def test_non_utf8_input_exits_2(self):
        self.readme.write_bytes(b"\xff\xfe\x00")
        self.assertEqual(self.invoke([str(self.readme)])[0], 2)


class RunGh(unittest.TestCase):
    def test_argv_stdin_and_environment(self):
        done = subprocess.CompletedProcess([], 0, stdout="<p>x</p>", stderr="")
        with mock.patch.object(render_readme.subprocess, "run", return_value=done) as run:
            self.assertEqual(render_readme.run_gh(["api", "markdown"], "{}"), "<p>x</p>")
        self.assertEqual(run.call_args.args[0], ["gh", "api", "markdown"])
        self.assertEqual(run.call_args.kwargs["input"], "{}")
        self.assertEqual(run.call_args.kwargs["env"]["MSYS_NO_PATHCONV"], "1")

    def test_errors_never_carry_a_token(self):
        token = "github_pat_" + "a" * 30
        done = subprocess.CompletedProcess([], 1, stdout="", stderr=f"failed {token}")
        with mock.patch.object(render_readme.subprocess, "run", return_value=done):
            with self.assertRaises(render_readme.GhError) as caught:
                render_readme.run_gh(["api"], "")
        self.assertNotIn(token, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
