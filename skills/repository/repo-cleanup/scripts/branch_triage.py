#!/usr/bin/env python3
"""Classify branches for cleanup. This tool never deletes anything.

usage: branch_triage.py CHECKOUT [--output FILE] [--base BRANCH] [--repo OWNER/NAME]
                        [--remote NAME] [--keep GLOB] [--offline]

CHECKOUT is a local full clone or mirror. The tool writes a TSV of verdict, sha,
date and name to stdout or FILE. PR data comes from gh when the remote is GitHub
and gh works. Without it, open pull requests are invisible, so the run says so
and exits 1.

The synthetic squash needs git commit-tree, which writes an object. That write
goes to a temporary object directory, so the audited clone gains nothing.

Exit 0 means every branch is a KEEP verdict and the data was complete. Exit 1
means at least one branch needs a human, or a data source was missing. Exit 2
means bad input.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

sys.dont_write_bytecode = True

GIT_TIMEOUT = 300
GH_TIMEOUT = 120
OPEN_PR_LIMIT = 10000
MANAGED_GLOBS = ("gh-readonly-queue/*", "dependabot/*", "renovate/*", "release*", "hotfix*")
READ_ONLY_GIT = {"cherry", "config", "for-each-ref", "merge-base", "rev-list", "rev-parse", "symbolic-ref"}
PROPOSABLE = {"CANDIDATE-merged-pr-tip", "ANCESTOR", "SQUASH-EQUIVALENT"}
HUMAN_ONLY = {"PATCHES-ALL-APPLIED"}
SYNTHETIC_IDENTITY = {
    "GIT_AUTHOR_NAME": "branch-triage",
    "GIT_AUTHOR_EMAIL": "branch-triage@invalid",
    "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+0000",
    "GIT_COMMITTER_NAME": "branch-triage",
    "GIT_COMMITTER_EMAIL": "branch-triage@invalid",
    "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+0000",
}
REPO_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*/[A-Za-z0-9_.][A-Za-z0-9_.-]*$")
GITHUB_REMOTE_RE = re.compile(r"[/@]github\.com[:/]+([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")
BRANCH_QUERY = """
query($o:String!,$n:String!,$endCursor:String){repository(owner:$o,name:$n){
 refs(refPrefix:"refs/heads/",first:50,after:$endCursor){pageInfo{hasNextPage endCursor}
  nodes{name target{oid}
   associatedPullRequests(first:10,states:[OPEN,MERGED]){nodes{state headRefOid baseRefName}}}}}}
"""


class BadInput(Exception):
    pass


def child_env(extra=None) -> dict:
    env = dict(os.environ, MSYS_NO_PATHCONV="1", GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", GIT_NO_LAZY_FETCH="1")
    env.update(extra or {})
    return env


class Git:
    """Runs only read commands. commit-tree goes through synthetic_squash."""

    def __init__(self, path: Path):
        self.path = path

    def _run(self, args, env=None):
        argv = ["git", "-c", "core.fsmonitor=false", "-C", str(self.path), *args]
        return subprocess.run(argv, capture_output=True, encoding="utf-8", errors="surrogateescape",
                              timeout=GIT_TIMEOUT, env=child_env(env), stdin=subprocess.DEVNULL)

    def run(self, *args, env=None):
        if args[0] not in READ_ONLY_GIT:
            raise ValueError(f"git {args[0]} is not a read command")
        return self._run(args, env)

    def out(self, *args, env=None) -> str:
        done = self.run(*args, env=env)
        if done.returncode != 0:
            raise subprocess.CalledProcessError(done.returncode, args[0])
        return done.stdout.strip()

    def synthetic_squash(self, tree: str, parent: str, env: dict) -> str:
        if "GIT_OBJECT_DIRECTORY" not in env:
            raise ValueError("commit-tree needs a temporary object directory")
        done = self._run(["commit-tree", tree, "-p", parent, "-m", "synthetic squash"], {**SYNTHETIC_IDENTITY, **env})
        if done.returncode != 0:
            raise subprocess.CalledProcessError(done.returncode, "commit-tree")
        return done.stdout.strip()


def gh_lines(args) -> list:
    done = subprocess.run(["gh", *args], capture_output=True, encoding="utf-8", errors="replace",
                          timeout=GH_TIMEOUT, env=child_env(), stdin=subprocess.DEVNULL)
    if done.returncode != 0:
        raise subprocess.CalledProcessError(done.returncode, "gh")
    return [line for line in done.stdout.splitlines() if line.strip()]


@dataclass
class PrData:
    default: str = ""
    open_heads: set = field(default_factory=set)
    open_bases: set = field(default_factory=set)
    merged_heads: dict = field(default_factory=dict)  # branch -> merged head SHAs into the default branch
    protected: set = field(default_factory=set)
    truncated: bool = False


def fetch_pr_data(repo: str) -> PrData:
    owner, name = repo.split("/", 1)
    data = PrData()
    data.default = json.loads("".join(gh_lines(["api", f"repos/{repo}"])))["default_branch"]
    pulls = json.loads("".join(gh_lines(["pr", "list", "-R", repo, "--state", "open", "--limit", str(OPEN_PR_LIMIT),
                                         "--json", "baseRefName,headRefName,isCrossRepository"])))
    data.truncated = len(pulls) >= OPEN_PR_LIMIT
    for pull in pulls:
        data.open_bases.add(pull["baseRefName"])
        if not pull["isCrossRepository"]:
            data.open_heads.add(pull["headRefName"])
    lines = gh_lines(["api", "graphql", "--paginate", "-F", f"o={owner}", "-F", f"n={name}", "-f", f"query={BRANCH_QUERY}",
                      "--jq", ".data.repository.refs.nodes[]"])
    for line in lines:
        node = json.loads(line)
        for pull in node["associatedPullRequests"]["nodes"]:
            if pull["state"] == "OPEN":
                data.open_heads.add(node["name"])
            elif pull["baseRefName"] == data.default:
                data.merged_heads.setdefault(node["name"], set()).add(pull["headRefOid"])
    data.protected = set(gh_lines(["api", "--paginate", f"repos/{repo}/branches?protected=true&per_page=100", "--jq", ".[].name"]))
    return data


def ruleset_blocks_deletion(repo: str, branch: str) -> bool:
    quoted = urllib.parse.quote(branch, safe="")
    lines = gh_lines(["api", "--paginate", f"repos/{repo}/rules/branches/{quoted}", "--jq", ".[].type"])
    return "deletion" in lines


def quote_alternate(path: str) -> str:
    if os.pathsep in path or path.startswith('"'):
        return '"' + path.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return path


def git_verdict(git: Git, tip: str, base: str, isolated: dict) -> str:
    """Prove a tip against the base. Any failed read ends in the keep verdict."""
    if git.run("merge-base", "--is-ancestor", tip, base).returncode == 0:
        return "ANCESTOR"
    try:
        merges = int(git.out("rev-list", "--merges", "--count", f"{base}..{tip}"))
        cherry = git.out("cherry", base, tip).splitlines()
        if not merges and cherry and not any(line.startswith("+") for line in cherry):
            return "PATCHES-ALL-APPLIED"
        ancestor = git.out("merge-base", base, tip)
        tree = git.out("rev-parse", f"{tip}^{{tree}}")
        synthetic = git.synthetic_squash(tree, ancestor, isolated)
        result = git.out("cherry", base, synthetic, env=isolated)
    except (subprocess.CalledProcessError, ValueError):
        return "KEEP-UNIQUE-WORK"
    return "SQUASH-EQUIVALENT" if result.startswith("-") else "KEEP-UNIQUE-WORK"


def classify(name, tip, default, base, git, isolated, pr, keep_globs) -> str:
    if name == default:
        return "KEEP-default"
    if any(fnmatch.fnmatchcase(name, glob) for glob in (*MANAGED_GLOBS, *keep_globs)):
        return "KEEP-managed"
    if pr is not None:
        if name in pr.protected:
            return "KEEP-managed"
        if name in pr.open_heads:
            return "KEEP-open-pr"
        if name in pr.open_bases:
            return "KEEP-open-pr-base"
        merged = pr.merged_heads.get(name, set())
        if tip in merged:
            return "CANDIDATE-merged-pr-tip"
        if merged:
            return "KEEP-work-after-merge"
    return git_verdict(git, tip, base, isolated)


def list_branches(git: Git, remote: str) -> dict:
    """Return name -> {sha: date}. A clone can hold the same name locally and on the remote."""
    prefix = f"refs/remotes/{remote}/"
    text = git.out("for-each-ref", "--format=%(objectname)%09%(committerdate:short)%09%(symref)%09%(refname)", "refs/heads", prefix)
    branches: dict = {}
    for line in text.splitlines():
        sha, date, symref, ref = line.split("\t")
        if symref:
            continue
        name = ref[len(prefix):] if ref.startswith(prefix) else ref[len("refs/heads/"):]
        branches.setdefault(name, {})[sha] = date
    return branches


def find_default(git: Git, remote: str, known: str) -> str:
    if known:
        return known
    refs = [f"refs/remotes/{remote}/HEAD"]
    # A checked-out HEAD names the default branch only in a mirror or a repository with no remote.
    if git.out("rev-parse", "--is-bare-repository") == "true" or git.run("config", "--get", f"remote.{remote}.url").returncode != 0:
        refs.append("HEAD")
    for ref in refs:
        done = git.run("symbolic-ref", "-q", ref)
        if done.returncode == 0:
            target = done.stdout.strip()
            for prefix in (f"refs/remotes/{remote}/", "refs/heads/"):
                if target.startswith(prefix):
                    return target[len(prefix):]
    raise BadInput("cannot find the default branch, pass --base")


def base_ref(git: Git, remote: str, default: str) -> str:
    for ref in (f"refs/remotes/{remote}/{default}", f"refs/heads/{default}"):
        if git.run("rev-parse", "-q", "--verify", f"{ref}^{{commit}}").returncode == 0:
            return ref
    raise BadInput(f"base branch {default!r} is not in this clone")


def detect_repo(git: Git, remote: str) -> str:
    """Return owner/name from the remote. The URL itself is never printed, since it can hold a token."""
    done = git.run("config", "--get", f"remote.{remote}.url")
    match = GITHUB_REMOTE_RE.search(done.stdout.strip()) if done.returncode == 0 else None
    return f"{match.group(1)}/{match.group(2)}" if match else ""


def open_checkout(path: Path) -> tuple:
    if not path.is_dir():
        raise BadInput(f"not a folder: {path}")
    git = Git(path)
    try:
        git_dir = Path(git.out("rev-parse", "--absolute-git-dir"))
        objects = Path(git.out("rev-parse", "--git-path", "objects"))
        shallow = git.out("rev-parse", "--is-shallow-repository")
    except (subprocess.CalledProcessError, OSError) as exc:
        raise BadInput(f"not a readable git repository: {path}") from exc
    if shallow == "true":
        raise BadInput("this is a shallow clone, the proofs need full history")
    promisors = git.run("config", "--get-regexp", r"^(remote\..*\.promisor|extensions\.partialclone)$")
    if promisors.stdout.strip():
        raise BadInput("this is a partial clone, the proofs need every object")
    if not objects.is_absolute():
        objects = (path / objects).resolve()
    return git, git_dir, objects


def check_output(output: Path, checkout: Path, git_dir: Path) -> None:
    target = output.resolve()
    for root in (checkout.resolve(), git_dir.resolve()):
        if target == root or root in target.parents:
            raise BadInput("--output must sit outside the audited repository")
    if target.exists():
        raise BadInput(f"{output} exists, and a ledger is never overwritten. Pick a new name")


def triage(args) -> tuple:
    checkout = Path(args.checkout)
    git, git_dir, objects = open_checkout(checkout)
    if args.output:
        check_output(Path(args.output), checkout, git_dir)
    warnings = []
    pr = None
    repo = "" if args.offline else (args.repo or detect_repo(git, args.remote))
    if repo:
        if not REPO_RE.match(repo):
            raise BadInput("--repo must look like owner/name")
        try:
            pr = fetch_pr_data(repo)
            if pr.truncated:
                warnings.append("the open pull request list hit its limit, so an open pull request may be missing")
        except (subprocess.SubprocessError, OSError, ValueError, KeyError, IndexError) as exc:
            pr = None
            warnings.append(f"gh gave no pull request data ({type(exc).__name__})")
    if pr is None:
        warnings.append("no pull request data, so open pull request heads and bases are invisible. Check them before any delete")
    default = args.base or find_default(git, args.remote, pr.default if pr else "")
    base = base_ref(git, args.remote, default)
    branches = list_branches(git, args.remote)
    rows = []
    with tempfile.TemporaryDirectory(prefix="branch-triage-", ignore_cleanup_errors=True) as tmp:
        scratch = Path(tmp) / "objects"
        scratch.mkdir()
        isolated = {"GIT_OBJECT_DIRECTORY": str(scratch), "GIT_ALTERNATE_OBJECT_DIRECTORIES": quote_alternate(str(objects))}
        for name, tips in branches.items():
            results = [(classify(name, sha, default, base, git, isolated, pr, args.keep), sha, date) for sha, date in tips.items()]
            # Two tips under one name: a keep verdict on either one wins.
            results.sort(key=lambda row: (not row[0].startswith("KEEP"), row[1]))
            verdict, sha, date = results[0]
            rows.append((verdict, sha, date, name))
    if pr is not None:
        for index, (verdict, sha, date, name) in enumerate(rows):
            if verdict in PROPOSABLE | HUMAN_ONLY:
                try:
                    if ruleset_blocks_deletion(repo, name):
                        rows[index] = ("KEEP-managed", sha, date, name)
                except (subprocess.SubprocessError, OSError):
                    warnings.append(f"could not read rulesets for {name}. Check them before any delete")
    rows.sort(key=lambda row: (row[2], row[3]))
    return rows, warnings


def render(rows) -> str:
    lines = ["verdict\tsha\tdate\tname"]
    lines += ["\t".join(row) for row in rows]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("checkout", help="local full clone or mirror")
    ap.add_argument("--output", help="write the TSV here, outside the repository. An existing file is refused")
    ap.add_argument("--base", help="default branch name, when it cannot be detected")
    ap.add_argument("--repo", help="owner/name for gh, when the remote does not show it")
    ap.add_argument("--remote", default="origin", help="remote name in a normal clone, default origin")
    ap.add_argument("--keep", action="append", default=[], metavar="GLOB", help="extra branch names to keep, repeatable")
    ap.add_argument("--offline", action="store_true", help="skip gh and use git proofs only")
    args = ap.parse_args(argv)
    try:
        rows, warnings = triage(args)
    except BadInput as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError:
        print("error: git was not found", file=sys.stderr)
        return 2
    except (subprocess.SubprocessError, OSError) as exc:
        print(f"error: git read failed ({type(exc).__name__})", file=sys.stderr)
        return 2
    text = render(rows)
    if args.output:
        with open(args.output, "x", encoding="utf-8", errors="surrogateescape", newline="\n") as handle:
            handle.write(text)
    else:
        sys.stdout.buffer.write(text.encode("utf-8", "surrogateescape"))
        sys.stdout.buffer.flush()
    counts: dict = {}
    for row in rows:
        counts[row[0]] = counts.get(row[0], 0) + 1
    for verdict in sorted(counts):
        print(f"{counts[verdict]:>5} {verdict}", file=sys.stderr)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    review = sum(counts.get(v, 0) for v in PROPOSABLE | HUMAN_ONLY)
    print(f"{review} branches need a human. Nothing was deleted.", file=sys.stderr)
    return 1 if review or warnings else 0


if __name__ == "__main__":
    sys.exit(main())
