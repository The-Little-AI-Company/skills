"""Run with: python -m unittest discover -s tests -p "test_*.py" -v"""

import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

import checks_readme  # noqa: E402
import repo_audit  # noqa: E402
from engine import NA, PASS, FAIL, UNKNOWN, WAIVED, REGISTRY, Ctx, Reader, WriteRefused, active_waiver, load_policy, run_check  # noqa: E402

FAKE_KEY = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"


def git(path, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="A", GIT_AUTHOR_EMAIL="a@noreply.test", GIT_COMMITTER_NAME="A", GIT_COMMITTER_EMAIL="a@noreply.test",
               GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, env=env)


class Repo:
    def __init__(self, files):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)
        git(self.path, "init", "-q", "-b", "main")
        self.write(files)

    def write(self, files, message="add"):
        for name, body in files.items():
            p = self.path / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(body if isinstance(body, bytes) else body.encode())
        git(self.path, "add", "-A")
        git(self.path, "commit", "-q", "-m", message)

    def audit(self, policy=None):
        report = repo_audit.build(self.path, None, False, policy)
        return report, {r["id"]: r for r in report["checks"]}

    def close(self):
        self.tmp.cleanup()


class Gate(unittest.TestCase):
    def test_git_writes_are_refused(self):
        r = Reader(Path("."))
        for args in (("commit", "-m", "x"), ("push",), ("config", "user.name", "x"), ("remote", "add", "a", "b"), ("gc",)):
            with self.assertRaises(WriteRefused):
                r.git(*args)

    def test_gh_writes_are_refused(self):
        r = Reader(Path("."))
        for args in (("api", "-X", "POST", "repos/a/b/issues"), ("api", "repos/a/b", "-f", "x=1"), ("pr", "create"), ("repo", "edit"),
                     ("api", "graphql", "-f", "query=mutation { x }"), ("api", "graphql", "-X", "POST", "-f", "query=query { x }")):
            with self.assertRaises(WriteRefused):
                r.gh_allowed(args)

    def test_gh_reads_pass(self):
        r = Reader(Path("."))
        r.gh_allowed(("api", "repos/a/b"))
        r.gh_allowed(("api", "graphql", "-F", "o=a", "-f", "query=query { x }"))

    def test_audit_does_not_touch_the_repository(self):
        repo = Repo({"README.md": "# Thing\n\nSays what it does here in words.\n"})
        hook = repo.path / ".git" / "hooks" / "post-checkout"
        before = sorted(str(p.relative_to(repo.path)) for p in repo.path.rglob("*"))
        repo.audit()
        after = sorted(str(p.relative_to(repo.path)) for p in repo.path.rglob("*"))
        self.assertEqual(before, after)
        self.assertFalse(hook.exists())
        repo.close()

    def test_hostile_fsmonitor_config_does_not_run(self):
        repo = Repo({"README.md": "# Thing\n"})
        marker = repo.path / "pwned"
        git(repo.path, "config", "core.fsmonitor", f"touch {marker.as_posix()} #")
        repo.audit()
        self.assertFalse(marker.exists())
        repo.close()


class Outcomes(unittest.TestCase):
    def test_online_only_checks_are_unknown_not_failed(self):
        repo = Repo({"README.md": "# T\n"})
        _, rows = repo.audit()
        for cid in ("BRN-002", "SEC-001", "MET-001"):
            self.assertEqual(rows[cid]["status"], UNKNOWN, cid)
        repo.close()

    def test_shallow_clone_is_unknown(self):
        repo = Repo({"README.md": "# T\n"})
        repo.write({"a.txt": "a"})
        with tempfile.TemporaryDirectory() as d:
            git(Path(d), "init", "-q")
            subprocess.run(["git", "clone", "-q", "--depth", "1", repo.path.as_uri(), d + "/c"], check=True, capture_output=True)
            report = repo_audit.build(Path(d) / "c", None, False)
            self.assertEqual({r["id"]: r for r in report["checks"]}["SEC-005"]["status"], UNKNOWN)
        repo.close()

    def test_every_check_has_metadata(self):
        self.assertGreater(len(REGISTRY), 100)
        for c in REGISTRY.values():
            self.assertTrue(c.title and c.source, c.id)


class Secrets(unittest.TestCase):
    def test_values_never_reach_the_report(self):
        repo = Repo({"config.py": f"TOKEN = '{FAKE_KEY}'\n"})
        repo.write({"config.py": "TOKEN = ''\n"}, "remove")
        report, rows = repo.audit()
        self.assertEqual(rows["SEC-005"]["status"], FAIL)
        self.assertNotIn(FAKE_KEY, json.dumps(report))
        self.assertNotIn(FAKE_KEY, repo_audit.render(report))
        repo.close()

    def test_fixture_keys_do_not_fail(self):
        repo = Repo({"testdata/key.pem": "-----BEGIN PRIVATE KEY-----\n", "tests/.env": "A=1\n"})
        _, rows = repo.audit()
        self.assertEqual(rows["SEC-008"]["status"], PASS)
        self.assertEqual(rows["SEC-009"]["status"], PASS)
        repo.close()

    def test_env_example_passes_and_env_fails(self):
        repo = Repo({".env.example": "A=\n"})
        self.assertEqual(repo.audit()[1]["SEC-009"]["status"], PASS)
        repo.write({".env": "A=b\n"})
        self.assertEqual(repo.audit()[1]["SEC-009"]["status"], FAIL)
        repo.close()


class Policy(unittest.TestCase):
    def test_waiver_needs_a_reason_and_a_future_date(self):
        policy = {"waivers": [{"check": "A", "reason": "because"}, {"check": "B", "reason": ""}, {"check": "C", "reason": "x", "expires": "2020-01-01"}]}
        self.assertEqual(active_waiver(policy, "A"), "because")
        self.assertIsNone(active_waiver(policy, "B"))
        self.assertIsNone(active_waiver(policy, "C", date(2026, 1, 1)))

    def test_waiver_moves_a_fail_to_waived(self):
        repo = Repo({".env": "A=b\n", ".github/repo-standards.json": json.dumps({"waivers": [{"check": "SEC-009", "reason": "public defaults only"}]})})
        self.assertEqual(repo.audit()[1]["SEC-009"]["status"], WAIVED)
        repo.close()

    def test_unknown_policy_keys_are_ignored_and_noted(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p.json"
            p.write_text(json.dumps({"type": "cli", "run_this": "rm -rf /"}))
            policy, notes = load_policy(None, p)
            self.assertEqual(policy, {"type": "cli"})
            self.assertTrue(notes)

    def test_declared_type_wins(self):
        repo = Repo({"package.json": '{"bin":"x"}', ".github/repo-standards.json": '{"type":"library"}'})
        self.assertEqual(repo.audit()[0]["type"]["name"], "library")
        repo.close()


class Readme(unittest.TestCase):
    def test_images_in_code_blocks_are_ignored(self):
        self.assertEqual(checks_readme.images("```\n![](a.png)\n```\n"), [])

    def test_reference_style_image_is_found(self):
        found = checks_readme.images("![logo][l]\n\n[l]: a.png\n")
        self.assertEqual(found[0].src, "a.png")

    def test_anchor_slugs_match_github(self):
        self.assertIn("whats-new-in-v2", checks_readme.anchors("## What's new in v2?\n"))
        self.assertIn("a-1", checks_readme.anchors("## A\n## A\n"))

    def test_broken_hero_and_process_note(self):
        repo = Repo({"README.md": "# App\n\n![Hero shot of the app](docs/hero.png)\n\nUntested on a clean machine.\n\n## Install\n"})
        _, rows = repo.audit()
        self.assertEqual(rows["PRS-003"]["status"], FAIL)
        self.assertEqual(rows["PRS-017"]["status"], FAIL)
        repo.close()

    def test_home_path_placeholder_passes(self):
        repo = Repo({"README.md": "Use /home/user/app or /home/alice/app.\n"})
        rows = repo.audit()[1]
        self.assertEqual(rows["PRS-022"]["status"], FAIL)
        repo.write({"README.md": "Use /home/user/app.\n"})
        self.assertEqual(repo.audit()[1]["PRS-022"]["status"], PASS)
        repo.close()

    def test_dark_ink_on_transparency_is_flagged(self):
        def png(rgba):
            w, h = 40, 40
            row = b"\0" + bytes(rgba) * (w // 2) + bytes((0, 0, 0, 0)) * (w // 2)
            def chunk(k, d):
                return struct.pack(">I", len(d)) + k + d + struct.pack(">I", zlib.crc32(k + d))
            return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(row * h)) + chunk(b"IEND", b"")
        self.assertLess(checks_readme.png_contrast(png((10, 10, 10, 255)))[0], 0.3)
        self.assertGreater(checks_readme.png_contrast(png((128, 128, 128, 255)))[0], 0.9)

    def test_private_hosts_are_not_fetched(self):
        for url in ("http://example.com/a.png", "https://127.0.0.1/a.png", "https://localhost/a.png", "file:///etc/passwd"):
            self.assertFalse(checks_readme.public_host(url), url)


class Types(unittest.TestCase):
    def cases(self):
        return [({"action.yml": "name: x"}, "action"), ({"main.tf": ""}, "infra"), ({"pnpm-workspace.yaml": ""}, "monorepo"),
                ({"project.godot": ""}, "game"), ({"package.json": '{"dependencies":{"electron":"1"}}'}, "desktop"),
                ({"mkdocs.yml": ""}, "docs"), ({"src/main.rs": "", "Cargo.toml": ""}, "cli"), ({"go.mod": ""}, "library")]

    def test_detection(self):
        for files, want in self.cases():
            repo = Repo(files)
            self.assertEqual(repo.audit()[0]["type"]["name"], want)
            repo.close()

    def test_action_dist_is_exempt(self):
        repo = Repo({"action.yml": "name: x", "dist/index.js": "x", "README.md": "# A"})
        self.assertEqual(repo.audit()[1]["IGN-004"]["status"], PASS)
        repo.close()


class Cli(unittest.TestCase):
    def test_refuses_a_non_repository(self):
        with tempfile.TemporaryDirectory() as d:
            p = subprocess.run([sys.executable, str(HERE / "repo_audit.py"), d, "--offline"], capture_output=True)
            self.assertEqual(p.returncode, 2)

    def test_json_contract(self):
        repo = Repo({"README.md": "# T\n"})
        p = subprocess.run([sys.executable, str(HERE / "repo_audit.py"), str(repo.path), "--offline", "--format", "json"], capture_output=True)
        data = json.loads(p.stdout)
        self.assertEqual(data["schema_version"], 1)
        self.assertTrue({"id", "status", "severity", "title", "detail", "items"} <= set(data["checks"][0]))
        repo.close()


if __name__ == "__main__":
    unittest.main()
