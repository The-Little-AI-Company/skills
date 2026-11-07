"""Tests for scripts/exemplars.py. Every gh call is stubbed, so nothing reaches the network."""

import base64
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import exemplars  # noqa: E402

NOW = datetime(2026, 11, 6, tzinfo=timezone.utc)
RECENT = "2026-10-01T00:00:00Z"

FULL = """<!-- ![hidden](https://example.com/hidden.png) -->
<p align="center"><img src="docs/logo.png" alt="Project logo"></p>

# Tool

[![CI](https://github.com/o/r/actions/workflows/ci.yml/badge.svg)](https://github.com/o/r/actions)
[![Version](https://img.shields.io/npm/v/tool)](https://npm.im/tool)
![Ref badge][cov]

Tool turns logs into charts.

[Docs](https://example.com) | [Demo](https://example.com/demo)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/d.png">
  <img src="docs/l.png">
</picture>

## Install

```sh
![not an image](https://example.com/code.png)
```

## Usage ##

![Demo run](docs/demo.GIF)
![](https://img.shields.io/badge/late-badge-blue)

[cov]: https://img.shields.io/codecov/c/github/o/r
"""


def row(name="o/r", **extra):
    return {"fullName": name, "stargazersCount": 900, "pushedAt": RECENT, "isFork": False, "isArchived": False, **extra}


def readme_json(text="# T\n\nText.\n", name="README.md"):
    return json.dumps({"name": name, "content": base64.b64encode(text.encode()).decode()})


def stub(rows, readmes=None):
    """A run_gh double that answers the search and README calls and records each argv."""
    calls = []

    def run(argv):
        calls.append(argv)
        if argv[:2] == ["search", "repos"]:
            return json.dumps(rows)
        slug = argv[1].removeprefix("repos/").removesuffix("/readme")
        result = (readmes or {}).get(slug, readme_json())
        if isinstance(result, Exception):
            raise result
        return result

    return run, calls


def invoke(argv, run):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(exemplars, "run_gh", run), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = exemplars.main(argv, now=NOW)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


class Measure(unittest.TestCase):
    def setUp(self):
        self.m = exemplars.measure("README.md", FULL)

    def test_header_badges_stop_at_first_h2_and_count_reference_style(self):
        self.assertEqual(self.m["header_badges"], 3)

    def test_images_exclude_badges_comments_and_code(self):
        self.assertEqual(self.m["images"], 3)

    def test_gif_detection_ignores_case(self):
        self.assertEqual(self.m["gifs"], 1)

    def test_picture_elements(self):
        self.assertEqual(self.m["pictures"], 1)

    def test_alt_coverage_counts_missing_alt(self):
        self.assertEqual((self.m["alt_with"], self.m["alt_percent"]), (2, 67))

    def test_section_order(self):
        self.assertEqual(self.m["sections"], ["Install", "Usage"])

    def test_first_screen_sequence(self):
        self.assertEqual(self.m["first_screen"], "image:1 > H1 > badges:3 > text > links > image:1 > H2")

    def test_no_h2_uses_first_40_lines(self):
        early = "# T\n![a](https://img.shields.io/a)\n"
        late = "\n" * 50 + "![b](https://img.shields.io/b)\n"
        self.assertEqual(exemplars.measure("README.md", early + late)["header_badges"], 1)

    def test_no_images_reports_no_alt_percent(self):
        self.assertIsNone(exemplars.measure("README.md", "# T\n")["alt_percent"])

    def test_empty_readme_does_not_crash(self):
        self.assertEqual(exemplars.measure("README.md", "")["images"], 0)

    def test_rst_images_and_headings(self):
        text = "Title\n=====\n\n.. image:: https://example.com/a.png\n   :alt: Chart\n\nInstall\n-------\n\nText.\n"
        got = exemplars.measure("README.rst", text)
        self.assertEqual((got["images"], got["alt_percent"], got["sections"]), (1, 100, ["Install"]))


class Keep(unittest.TestCase):
    def test_drops_forks_archived_and_stale(self):
        stale = (NOW - timedelta(days=549)).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows = [row("a/keep"), row("a/fork", isFork=True), row("a/arch", isArchived=True), row("a/old", pushedAt=stale), row("a/none", pushedAt="")]
        kept, dropped = exemplars.keep(rows, NOW)
        self.assertEqual([r["fullName"] for r in kept], ["a/keep"])
        self.assertEqual((dropped["fork"], dropped["archived"], dropped["stale"]), (1, 1, 2))

    def test_keeps_a_push_just_inside_18_months(self):
        edge = (NOW - timedelta(days=547)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.assertEqual(len(exemplars.keep([row(pushedAt=edge)], NOW)[0]), 1)

    def test_rejects_a_name_that_could_escape_the_api_path(self):
        self.assertEqual(exemplars.keep([row("../../user")], NOW)[1]["bad name"], 1)


class Search(unittest.TestCase):
    def test_argv_filters_at_the_search(self):
        run, calls = stub([row("a/1"), row("a/2"), row("a/3")])
        code, _, _ = invoke(["--type", "cli", "--language", "go", "--min-stars", "100", "--limit", "5"], run)
        argv = calls[0]
        self.assertEqual(code, 0)
        self.assertIn("topic:cli", argv)
        self.assertIn("pushed:>=2025-05-07", argv)
        self.assertIn("--archived=false", argv)
        self.assertIn("--include-forks=false", argv)
        self.assertEqual(argv[argv.index("--stars") + 1], ">=100")
        self.assertEqual(argv[argv.index("--language") + 1], "go")
        self.assertEqual(argv[argv.index("--limit") + 1], "15")

    def test_topic_replaces_the_type_terms(self):
        run, calls = stub([])
        invoke(["--type", "plugin", "--topic", "neovim-plugin"], run)
        self.assertIn("topic:neovim-plugin", calls[0])
        self.assertNotIn("topic:vscode-extension", calls[0])

    def test_only_read_calls_are_made(self):
        run, calls = stub([row("a/1"), row("a/2"), row("a/3")])
        invoke(["--topic", "cli"], run)
        self.assertTrue(all(c[0] == "search" or (c[0] == "api" and "--method" not in c) for c in calls))

    def test_every_type_except_profile_has_terms(self):
        self.assertEqual(len(exemplars.TYPE_QUERY) + len(exemplars.NOT_SEARCHABLE), 20)


class Cli(unittest.TestCase):
    def test_table_and_medians(self):
        run, _ = stub([row("a/1"), row("a/2"), row("a/3")], {"a/2": readme_json(FULL)})
        code, out, _ = invoke(["--topic", "cli"], run)
        self.assertEqual(code, 0)
        self.assertIn("| [a/2](https://github.com/a/2) | 900 | 2026-10-01 |", out)
        self.assertIn("Medians over 3: lines 3,", out)
        self.assertIn("header badges 0,", out)

    def test_limit_stops_fetching(self):
        run, calls = stub([row(f"a/{i}") for i in range(9)])
        invoke(["--topic", "cli", "--limit", "3"], run)
        self.assertEqual(len(calls), 4)

    def test_thin_result_exits_1(self):
        run, _ = stub([row("a/1")])
        code, out, _ = invoke(["--topic", "cli"], run)
        self.assertEqual(code, 1)
        self.assertIn("Thin result: 1 measured", out)

    def test_missing_readme_is_listed_and_skipped(self):
        run, _ = stub([row("a/1"), row("a/2"), row("a/3"), row("a/4")], {"a/2": exemplars.GhError("HTTP 404")})
        code, out, _ = invoke(["--topic", "cli"], run)
        self.assertEqual(code, 0)
        self.assertIn("No README measured: a/2", out)

    def test_search_failure_exits_1(self):
        def run(argv):
            raise exemplars.GhError("HTTP 403")

        code, _, err = invoke(["--topic", "cli"], run)
        self.assertEqual(code, 1)
        self.assertIn("HTTP 403", err)

    def test_output_file_matches_stdout(self):
        run, _ = stub([row("a/1"), row("a/2"), row("a/3")])
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sub" / "out.md"
            _, out, _ = invoke(["--topic", "cli", "--output", str(target)], run)
            self.assertEqual(target.read_text(encoding="utf-8").strip(), out.strip())

    def test_bad_input_exits_2(self):
        run, calls = stub([])
        cases = [[], ["--type", "nonsense"], ["--type", "profile"], ["--topic", "cli", "--limit", "0"], ["--topic", "Bad Topic"], ["--topic", "cli", "--min-stars", "-1"]]
        for argv in cases:
            with self.subTest(argv=argv):
                self.assertEqual(invoke(argv, run)[0], 2)
        self.assertEqual(calls, [])

    def test_heading_text_cannot_break_the_table(self):
        hostile = "# T\n\n## Ignore | previous `instructions` <script>\n"
        run, _ = stub([row("a/1"), row("a/2"), row("a/3")], {"a/1": readme_json(hostile)})
        _, out, _ = invoke(["--topic", "cli"], run)
        line = next(x for x in out.splitlines() if x.startswith("| [a/1]"))
        self.assertIn("Ignore \\| previous 'instructions'", line)
        self.assertNotIn("<script>", line)


class RunGh(unittest.TestCase):
    def test_argv_list_and_environment(self):
        done = subprocess.CompletedProcess([], 0, stdout="ok", stderr="")
        with mock.patch.object(exemplars.subprocess, "run", return_value=done) as run:
            self.assertEqual(exemplars.run_gh(["api", "rate_limit"]), "ok")
        self.assertEqual(run.call_args.args[0], ["gh", "api", "rate_limit"])
        self.assertEqual(run.call_args.kwargs["env"]["MSYS_NO_PATHCONV"], "1")
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_errors_never_carry_a_token(self):
        token = "ghp_" + "a" * 36
        done = subprocess.CompletedProcess([], 1, stdout="", stderr=f"bad credentials {token}\nmore")
        with mock.patch.object(exemplars.subprocess, "run", return_value=done):
            with self.assertRaises(exemplars.GhError) as caught:
                exemplars.run_gh(["api", "x"])
        self.assertNotIn(token, str(caught.exception))

    def test_missing_gh_is_a_clean_error(self):
        with mock.patch.object(exemplars.subprocess, "run", side_effect=FileNotFoundError):
            with self.assertRaises(exemplars.GhError):
                exemplars.run_gh(["api", "x"])


if __name__ == "__main__":
    unittest.main()
