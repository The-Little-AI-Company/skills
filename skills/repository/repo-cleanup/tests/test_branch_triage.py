"""Run with: python -m unittest discover -s tests -p "test_*.py" -v"""

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "branch_triage.py"
sys.path.insert(0, str(SKILL / "scripts"))
sys.dont_write_bytecode = True

import branch_triage as bt  # noqa: E402

os.environ["GIT_CONFIG_GLOBAL"] = os.devnull
os.environ["GIT_CONFIG_NOSYSTEM"] = "1"

ENV = dict(
    os.environ,
    GIT_AUTHOR_NAME="A",
    GIT_AUTHOR_EMAIL="a@noreply.test",
    GIT_AUTHOR_DATE="2026-01-01T00:00:00+0000",
    GIT_COMMITTER_NAME="A",
    GIT_COMMITTER_EMAIL="a@noreply.test",
    GIT_COMMITTER_DATE="2026-01-01T00:00:00+0000",
    MSYS_NO_PATHCONV="1",
)
# No user identity reaches the script, so commit-tree must bring its own.
SCRIPT_ENV = {k: v for k, v in ENV.items() if not k.startswith(("GIT_AUTHOR", "GIT_COMMITTER"))}

EXPECTED = {
    "ff-merged": "ANCESTOR",
    "same-tip": "ANCESTOR",
    "squash-two": "SQUASH-EQUIVALENT",
    "squash-rewritten": "SQUASH-EQUIVALENT",
    "rebase-merged": "PATCHES-ALL-APPLIED",
    "squash-conflict": "KEEP-UNIQUE-WORK",
    "squash-reverted": "PATCHES-ALL-APPLIED",
    "squash-more-work": "KEEP-UNIQUE-WORK",
    "never-merged": "KEEP-UNIQUE-WORK",
}


def git(path, *args, check=True):
    done = subprocess.run(["git", "-c", "core.autocrlf=false", "-C", str(path), *args], capture_output=True, text=True, env=ENV)
    if check and done.returncode != 0:
        raise AssertionError(f"git {args}: {done.stderr}")
    return done.stdout.strip()


def commit(path, name, body, message):
    (path / name).write_text(body, encoding="utf-8", newline="\n")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", message)


def squash(path, branch, message):
    git(path, "merge", "-q", "--squash", branch)
    git(path, "commit", "-q", "-m", message)


def lines(*items):
    return "".join(f"{item}\n" for item in items)


def nine_shapes(path):
    """Build the nine branch shapes from the research fixture on main."""
    git(path, "init", "-q", "-b", "main")
    commit(path, "base.txt", lines("one", "two", "three"), "base")
    commit(path, "conflict.txt", lines("original"), "conflict file")

    git(path, "switch", "-q", "-c", "ff-merged")
    commit(path, "ff.txt", "ff\n", "ff work")
    git(path, "switch", "-q", "main")
    git(path, "merge", "-q", "--ff-only", "ff-merged")

    git(path, "branch", "same-tip")

    git(path, "switch", "-q", "-c", "squash-two")
    commit(path, "s2.txt", "one\n", "s2 first")
    commit(path, "s2.txt", "one\ntwo\n", "s2 second")
    git(path, "switch", "-q", "main")
    squash(path, "squash-two", "squash two")

    git(path, "switch", "-q", "-c", "squash-rewritten")
    commit(path, "r.txt", "one\n", "r first")
    commit(path, "r.txt", "one\ntwo\n", "r second")
    git(path, "switch", "-q", "main")
    squash(path, "squash-rewritten", "squash rewritten")
    commit(path, "r.txt", "rewritten\ntwo\n", "main rewrites the line")

    git(path, "switch", "-q", "-c", "rebase-merged")
    commit(path, "rb1.txt", "one\n", "rebase first")
    commit(path, "rb2.txt", "two\n", "rebase second")
    first, second = git(path, "rev-list", "--reverse", "main..rebase-merged").split()
    git(path, "switch", "-q", "main")
    commit(path, "moved.txt", "moved\n", "main moves")
    git(path, "cherry-pick", first, second)

    git(path, "switch", "-q", "-c", "squash-conflict")
    commit(path, "conflict.txt", lines("branch"), "branch side")
    git(path, "switch", "-q", "main")
    commit(path, "conflict.txt", lines("main"), "main side")
    git(path, "merge", "--squash", "squash-conflict", check=False)
    commit(path, "conflict.txt", lines("resolved"), "squash with conflict resolved")

    git(path, "switch", "-q", "-c", "squash-reverted")
    commit(path, "reverted.txt", "gone\n", "will be reverted")
    git(path, "switch", "-q", "main")
    squash(path, "squash-reverted", "squash then revert")
    git(path, "revert", "--no-edit", "HEAD")

    git(path, "switch", "-q", "-c", "squash-more-work")
    commit(path, "more.txt", "one\n", "merged part")
    git(path, "switch", "-q", "main")
    squash(path, "squash-more-work", "squash partial")
    git(path, "switch", "-q", "squash-more-work")
    commit(path, "more2.txt", "two\n", "pushed after the squash")

    git(path, "switch", "-q", "main")
    git(path, "switch", "-q", "-c", "never-merged")
    commit(path, "never.txt", "never\n", "never merged")
    git(path, "switch", "-q", "main")


def snapshot(git_dir):
    """Every file under the repository metadata, with size and modified time."""
    seen = {}
    for root, _, names in os.walk(git_dir):
        for name in names:
            path = Path(root) / name
            stat = path.stat()
            seen[str(path.relative_to(git_dir))] = (stat.st_size, stat.st_mtime_ns)
    return seen


def run_script(*args, env=None):
    return subprocess.run([sys.executable, "-B", str(SCRIPT), *map(str, args)], capture_output=True, text=True, env=env or SCRIPT_ENV)


def parse(tsv):
    rows = [line.split("\t") for line in tsv.strip().splitlines()]
    return rows[0], {row[3]: row for row in rows[1:]}


def setUpModule():
    tmp = tempfile.TemporaryDirectory()
    unittest.addModuleCleanup(tmp.cleanup)
    Fixture.root = Path(tmp.name)
    Fixture.repo = Fixture.root / "repo"
    Fixture.repo.mkdir()
    nine_shapes(Fixture.repo)
    Fixture.mirror = Fixture.root / "mirror.git"
    git(Fixture.root, "clone", "-q", "--mirror", str(Fixture.repo), str(Fixture.mirror))
    Fixture.clone = Fixture.root / "clone"
    git(Fixture.root, "clone", "-q", str(Fixture.repo), str(Fixture.clone))


class Fixture(unittest.TestCase):

    def out_path(self, name):
        return self.root / f"{self.id().rsplit('.', 1)[-1]}-{name}.tsv"


class NineShapes(Fixture):
    def assert_shapes(self, path, default="main"):
        done = run_script(path, "--offline")
        self.assertEqual(done.returncode, 1, done.stderr)
        header, rows = parse(done.stdout)
        self.assertEqual(header, ["verdict", "sha", "date", "name"])
        for name, verdict in EXPECTED.items():
            self.assertEqual(rows[name][0], verdict, name)
        self.assertEqual(rows[default][0], "KEEP-default")
        self.assertEqual(len(rows), len(EXPECTED) + 1)

    def test_plain_repository(self):
        self.assert_shapes(self.repo)

    def test_mirror(self):
        self.assert_shapes(self.mirror)

    def test_normal_clone_reads_remote_refs(self):
        self.assert_shapes(self.clone)

    def test_row_fields(self):
        _, rows = parse(run_script(self.repo, "--offline").stdout)
        verdict, sha, date, name = rows["never-merged"]
        self.assertEqual(sha, git(self.repo, "rev-parse", "never-merged"))
        self.assertEqual(date, "2026-01-01")
        self.assertEqual(name, "never-merged")

    def test_unsafe_branches_never_get_a_delete_signal(self):
        _, rows = parse(run_script(self.repo, "--offline").stdout)
        for name in ("squash-more-work", "never-merged", "squash-conflict"):
            self.assertTrue(rows[name][0].startswith("KEEP"), name)


class ReadOnly(Fixture):
    def test_audited_clone_gains_nothing(self):
        for path, meta in ((self.repo, self.repo / ".git"), (self.mirror, self.mirror)):
            with self.subTest(path=path.name):
                before = snapshot(meta)
                refs = git(path, "for-each-ref")
                count = git(path, "count-objects", "-v")
                dangling = git(path, "fsck", "--dangling", "--connectivity-only")
                done = run_script(path, "--offline")
                self.assertIn("SQUASH-EQUIVALENT", done.stdout)
                self.assertEqual(snapshot(meta), before)
                self.assertEqual(git(path, "for-each-ref"), refs)
                self.assertEqual(git(path, "count-objects", "-v"), count)
                self.assertEqual(git(path, "fsck", "--dangling", "--connectivity-only"), dangling)

    def test_temporary_object_directory_is_removed(self):
        scratch = self.root / "scratch-tmp"
        scratch.mkdir()
        env = dict(SCRIPT_ENV, TMP=str(scratch), TEMP=str(scratch), TMPDIR=str(scratch))
        run_script(self.repo, "--offline", env=env)
        self.assertEqual(list(scratch.iterdir()), [])

    def test_commit_tree_refuses_to_run_without_isolation(self):
        with self.assertRaises(ValueError):
            bt.Git(self.repo).synthetic_squash("0" * 40, "0" * 40, {})

    def test_write_commands_are_refused(self):
        wrapped = bt.Git(self.repo)
        for command in ("branch", "push", "update-ref", "commit-tree", "gc", "fetch"):
            with self.assertRaises(ValueError):
                wrapped.run(command, "-d", "x")

    def test_source_names_no_delete_command(self):
        text = SCRIPT.read_text(encoding="utf-8")
        for token in ('"push"', '"branch"', '"update-ref"', '"DELETE"', "--delete"):
            self.assertNotIn(token, text)

    def test_repository_path_holding_the_path_separator(self):
        odd = self.root / f"odd{os.pathsep}name"
        git(self.root, "clone", "-q", "--mirror", str(self.repo), str(odd))
        done = run_script(odd, "--offline")
        _, rows = parse(done.stdout)
        self.assertEqual(rows["squash-two"][0], "SQUASH-EQUIVALENT", done.stderr)


class Output(Fixture):
    def test_output_file(self):
        target = self.out_path("ledger")
        done = run_script(self.repo, "--offline", "--output", target)
        self.assertEqual(done.stdout, "")
        self.assertIn("Nothing was deleted.", done.stderr)
        _, rows = parse(target.read_text(encoding="utf-8"))
        self.assertIn("never-merged", rows)

    def test_existing_ledger_is_never_overwritten(self):
        target = self.out_path("ledger")
        target.write_text("old", encoding="utf-8")
        self.assertEqual(run_script(self.repo, "--offline", "--output", target).returncode, 2)
        self.assertEqual(target.read_text(encoding="utf-8"), "old")

    def test_output_inside_the_repository_is_refused(self):
        target = self.repo / "branches.tsv"
        self.assertEqual(run_script(self.repo, "--offline", "--output", target).returncode, 2)
        self.assertFalse(target.exists())

    def test_keep_glob(self):
        _, rows = parse(run_script(self.repo, "--offline", "--keep", "same-*").stdout)
        self.assertEqual(rows["same-tip"][0], "KEEP-managed")

    def test_offline_warns_about_open_pull_requests(self):
        self.assertIn("open pull request heads and bases are invisible", run_script(self.repo, "--offline").stderr)


class BadInputs(Fixture):
    def test_missing_folder(self):
        self.assertEqual(run_script(self.root / "nope").returncode, 2)

    def test_not_a_repository(self):
        folder = self.root / "plain-folder"
        folder.mkdir(exist_ok=True)
        ceiling = dict(SCRIPT_ENV, GIT_CEILING_DIRECTORIES=str(self.root))
        self.assertEqual(run_script(folder, env=ceiling).returncode, 2)

    def test_unknown_base(self):
        self.assertEqual(run_script(self.repo, "--offline", "--base", "nope").returncode, 2)

    def test_bad_repo_value(self):
        self.assertEqual(run_script(self.repo, "--repo", "--flag/x").returncode, 2)

    def test_shallow_clone_is_refused(self):
        shallow = self.root / "shallow"
        git(self.root, "clone", "-q", "--depth", "1", f"file://{self.repo.as_posix()}", str(shallow))
        done = run_script(shallow, "--offline")
        self.assertEqual(done.returncode, 2)
        self.assertIn("shallow", done.stderr)

    def test_partial_clone_is_refused(self):
        partial = self.root / "partial"
        git(self.root, "clone", "-q", str(self.repo), str(partial))
        git(partial, "config", "remote.origin.promisor", "true")
        done = run_script(partial, "--offline")
        self.assertEqual(done.returncode, 2)
        self.assertIn("partial", done.stderr)

    def test_clone_with_unknown_default_does_not_trust_checked_out_head(self):
        clone = self.root / "no-origin-head"
        git(self.root, "clone", "-q", str(self.repo), str(clone))
        git(clone, "switch", "-q", "-c", "local-work")
        git(clone, "symbolic-ref", "-d", "refs/remotes/origin/HEAD")
        self.assertEqual(run_script(clone, "--offline").returncode, 2)
        self.assertEqual(run_script(clone, "--offline", "--base", "main").returncode, 1)


class Proofs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q", "-b", "main")
        commit(self.repo, "base.txt", "base\n", "base")

    def verdicts(self, *extra):
        return parse(run_script(self.repo, "--offline", *extra).stdout)[1]

    def test_branch_with_only_a_merge_commit_is_not_read_as_applied(self):
        git(self.repo, "switch", "-q", "-c", "side")
        commit(self.repo, "side.txt", "side\n", "side")
        git(self.repo, "switch", "-q", "main")
        squash(self.repo, "side", "squash side")
        git(self.repo, "switch", "-q", "-c", "evil", "side")
        commit(self.repo, "evil.txt", "evil\n", "evil")
        git(self.repo, "switch", "-q", "-c", "with-merge", "main")
        git(self.repo, "merge", "-q", "--no-commit", "--no-ff", "evil", check=False)
        commit(self.repo, "hidden.txt", "hidden work in the merge\n", "evil merge")
        git(self.repo, "switch", "-q", "main")
        rows = self.verdicts()
        self.assertEqual(rows["with-merge"][0], "KEEP-UNIQUE-WORK")

    def test_failed_cherry_is_not_read_as_applied(self):
        git(self.repo, "switch", "-q", "-c", "work")
        commit(self.repo, "w.txt", "w\n", "work")
        git(self.repo, "switch", "-q", "main")
        wrapped = bt.Git(self.repo)
        real = wrapped.run

        def failing(*args, env=None):
            if args[0] == "cherry":
                return subprocess.CompletedProcess(args, 128, "", "")
            return real(*args, env=env)

        with mock.patch.object(wrapped, "run", side_effect=failing):
            verdict = bt.git_verdict(wrapped, git(self.repo, "rev-parse", "work"), "refs/heads/main", {"GIT_OBJECT_DIRECTORY": "x"})
        self.assertEqual(verdict, "KEEP-UNIQUE-WORK")

    def test_local_and_remote_tips_differ_keep_wins(self):
        git(self.repo, "switch", "-q", "-c", "topic")
        commit(self.repo, "t.txt", "t\n", "topic")
        git(self.repo, "switch", "-q", "main")
        git(self.repo, "merge", "-q", "--ff-only", "topic")
        clone = self.repo.parent / (self.repo.name + "-clone")
        git(self.repo.parent, "clone", "-q", str(self.repo), str(clone))
        self.addCleanup(lambda: subprocess.run(["git", "-C", str(clone), "gc", "-q"], env=ENV))
        git(clone, "switch", "-q", "topic")
        commit(clone, "unpushed.txt", "local only\n", "unpushed work")
        git(clone, "switch", "-q", "main")
        done = run_script(clone, "--offline")
        _, rows = parse(done.stdout)
        self.assertEqual(rows["topic"][0], "KEEP-UNIQUE-WORK")
        self.assertEqual(rows["topic"][1], git(clone, "rev-parse", "refs/heads/topic"))


class PrVerdicts(Fixture):
    def run_with(self, data, rules=None, extra=()):
        out, err = io.StringIO(), io.StringIO()
        target = self.root / f"pr-{self.id().rsplit('.', 1)[-1]}.tsv"
        rules = rules if rules is not None else (lambda repo, name: False)
        with mock.patch.object(bt, "fetch_pr_data", side_effect=data if callable(data) else (lambda repo: data)), \
                mock.patch.object(bt, "ruleset_blocks_deletion", side_effect=rules), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = bt.main([str(self.repo), "--repo", "owner/repo", "--output", str(target), *extra])
        rows = parse(target.read_text(encoding="utf-8"))[1] if target.exists() else {}
        return code, rows, err.getvalue()

    def sha(self, name):
        return git(self.repo, "rev-parse", name)

    def test_default_and_managed_names(self):
        git(self.repo, "branch", "dependabot/npm/x", "main")
        git(self.repo, "branch", "renovate/x", "main")
        git(self.repo, "branch", "gh-readonly-queue/main/pr-1", "main")
        git(self.repo, "branch", "release-1.0", "main")
        git(self.repo, "branch", "hotfix-1", "main")
        self.addCleanup(git, self.repo, "branch", "-q", "-D", "dependabot/npm/x", "renovate/x", "gh-readonly-queue/main/pr-1", "release-1.0", "hotfix-1")
        _, rows, _ = self.run_with(bt.PrData(default="main"))
        self.assertEqual(rows["main"][0], "KEEP-default")
        for name in ("dependabot/npm/x", "renovate/x", "gh-readonly-queue/main/pr-1", "release-1.0", "hotfix-1"):
            self.assertEqual(rows[name][0], "KEEP-managed", name)

    def test_open_pr_head_beats_every_git_proof(self):
        _, rows, _ = self.run_with(bt.PrData(default="main", open_heads={"ff-merged"}))
        self.assertEqual(rows["ff-merged"][0], "KEEP-open-pr")

    def test_open_pr_base(self):
        _, rows, _ = self.run_with(bt.PrData(default="main", open_bases={"same-tip"}))
        self.assertEqual(rows["same-tip"][0], "KEEP-open-pr-base")

    def test_merged_tip_is_a_candidate_even_after_a_conflict_squash(self):
        data = bt.PrData(default="main", merged_heads={"squash-conflict": {self.sha("squash-conflict")}})
        _, rows, _ = self.run_with(data)
        self.assertEqual(rows["squash-conflict"][0], "CANDIDATE-merged-pr-tip")

    def test_tip_moved_after_merge_is_kept(self):
        data = bt.PrData(default="main", merged_heads={"squash-two": {"f" * 40}})
        _, rows, _ = self.run_with(data)
        self.assertEqual(rows["squash-two"][0], "KEEP-work-after-merge")

    def test_order_open_before_merged(self):
        sha = self.sha("squash-two")
        data = bt.PrData(default="main", open_heads={"squash-two"}, merged_heads={"squash-two": {sha}})
        _, rows, _ = self.run_with(data)
        self.assertEqual(rows["squash-two"][0], "KEEP-open-pr")

    def test_protected_branch_is_kept(self):
        _, rows, _ = self.run_with(bt.PrData(default="main", protected={"ff-merged"}))
        self.assertEqual(rows["ff-merged"][0], "KEEP-managed")

    def test_ruleset_deletion_rule_keeps_a_delete_signal(self):
        _, rows, _ = self.run_with(bt.PrData(default="main"), rules=lambda repo, name: name == "same-tip")
        self.assertEqual(rows["same-tip"][0], "KEEP-managed")
        self.assertEqual(rows["ff-merged"][0], "ANCESTOR")

    def test_ruleset_read_failure_warns(self):
        def broken(repo, name):
            raise subprocess.CalledProcessError(1, "gh")

        code, _, err = self.run_with(bt.PrData(default="main"), rules=broken)
        self.assertEqual(code, 1)
        self.assertIn("could not read rulesets", err)

    def test_gh_failure_falls_back_and_warns_without_detail(self):
        def broken(repo):
            raise subprocess.CalledProcessError(1, "gh")

        code, rows, err = self.run_with(broken)
        self.assertEqual(code, 1)
        self.assertEqual(rows["ff-merged"][0], "ANCESTOR")
        self.assertIn("no pull request data", err)
        self.assertIn("CalledProcessError", err)

    def test_truncated_open_pr_list_warns(self):
        _, _, err = self.run_with(bt.PrData(default="main", truncated=True))
        self.assertIn("hit its limit", err)

    def test_all_keep_exits_zero(self):
        names = {line.split()[-1] for line in git(self.repo, "for-each-ref", "--format=%(refname:short)").splitlines()}
        code, rows, _ = self.run_with(bt.PrData(default="main", open_heads=names - {"main"}))
        self.assertEqual(code, 0)
        self.assertTrue(all(row[0].startswith("KEEP") for row in rows.values()))


class GhParsing(unittest.TestCase):
    def test_fetch_builds_sets_from_gh_output(self):
        pr_json = '[{"baseRefName":"main","headRefName":"a","isCrossRepository":false},' \
                  '{"baseRefName":"stack","headRefName":"main","isCrossRepository":true}]'
        nodes = [
            '{"name":"m","target":{"oid":"1"},"associatedPullRequests":{"nodes":[{"state":"MERGED","headRefOid":"1","baseRefName":"main"}]}}',
            '{"name":"o","target":{"oid":"2"},"associatedPullRequests":{"nodes":[{"state":"MERGED","headRefOid":"2","baseRefName":"other"}]}}',
            '{"name":"p","target":{"oid":"3"},"associatedPullRequests":{"nodes":[{"state":"OPEN","headRefOid":"3","baseRefName":"main"}]}}',
        ]
        replies = [['{"default_branch":"main"}'], [pr_json], nodes, ["guarded"]]
        with mock.patch.object(bt, "gh_lines", side_effect=replies) as gh:
            data = bt.fetch_pr_data("owner/repo")
        self.assertEqual(data.default, "main")
        self.assertEqual(data.open_heads, {"a", "p"})
        self.assertEqual(data.open_bases, {"main", "stack"})
        self.assertEqual(data.merged_heads, {"m": {"1"}})
        self.assertEqual(data.protected, {"guarded"})
        self.assertIn("first:50", " ".join(gh.call_args_list[2].args[0]))

    def test_rules_path_is_encoded(self):
        with mock.patch.object(bt, "gh_lines", return_value=["deletion", "pull_request"]) as gh:
            self.assertTrue(bt.ruleset_blocks_deletion("owner/repo", "feat/a{b}"))
        self.assertIn("rules/branches/feat%2Fa%7Bb%7D", gh.call_args.args[0][2])

    def test_remote_detection_never_returns_the_credential(self):
        cases = {
            "https://x-token:secret@github.com/owner/repo.git": "owner/repo",
            "git@github.com:owner/repo.git": "owner/repo",
            "ssh://git@github.com/owner/repo": "owner/repo",
            "https://github.com/owner/repo/": "owner/repo",
            "https://gitlab.com/owner/repo.git": "",
            "https://notgithub.com/owner/repo.git": "",
        }
        for url, expected in cases.items():
            wrapped = mock.Mock()
            wrapped.run.return_value = subprocess.CompletedProcess([], 0, url + "\n", "")
            self.assertEqual(bt.detect_repo(wrapped, "origin"), expected, url)


if __name__ == "__main__":
    unittest.main()
