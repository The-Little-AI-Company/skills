"""Registry, outcomes and the read-only gate every check goes through."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Optional

VERSION = "0.1.0"

PASS, FAIL, UNKNOWN, NA, INFO, WAIVED = "pass", "fail", "unknown", "na", "info", "waived"
SEVERITIES = ("critical", "high", "medium", "low", "info")
FIX_CLASSES = ("auto", "pr", "setting", "rewrite", "report")
NEEDS = ("tree", "history", "github", "admin")

GIT_READ = {
    "cat-file", "check-ignore", "config", "for-each-ref", "fsck", "grep", "log", "ls-files",
    "merge-base", "remote", "rev-list", "rev-parse", "shortlog", "show", "var", "ls-tree",
}
GIT_SAFE_FLAGS = [
    "-c", "core.fsmonitor=false",
    "-c", "core.hooksPath=" + os.devnull,
    "-c", "core.sshCommand=false",
    "-c", "diff.external=",
    "-c", "protocol.ext.allow=never",
]
GH_READ = {("api",), ("repo", "view"), ("pr", "list"), ("release", "list"), ("release", "view"), ("auth", "status")}
GH_WRITE_FLAGS = {"-X", "--method", "-f", "--raw-field", "--input"}


class Unknown(Exception):
    """The check could not be measured. Never a pass, never a fail."""


class NotApplicable(Exception):
    """The check does not apply to this repository."""


class WriteRefused(RuntimeError):
    """A write reached the gate. This is a bug in a check, so it stops the run."""


@dataclass(frozen=True)
class Result:
    status: str
    detail: str = ""
    items: tuple = ()


def ok(detail: str = "") -> Result:
    return Result(PASS, detail)


def bad(detail: str, items=()) -> Result:
    return Result(FAIL, detail, tuple(str(i) for i in items)[:25])


def note(detail: str, items=()) -> Result:
    return Result(INFO, detail, tuple(str(i) for i in items)[:25])


@dataclass(frozen=True)
class Check:
    id: str
    category: str
    title: str
    severity: str
    fix: str
    needs: str
    source: str
    fn: Callable
    skip: frozenset = frozenset()
    when: Optional[Callable] = None
    opinion: bool = False


REGISTRY: dict[str, Check] = {}


def check(id, category, title, severity, fix, needs, source, skip=(), when=None, opinion=False):
    """Register a check. Metadata sits on the function so the two cannot drift."""
    if severity not in SEVERITIES or fix not in FIX_CLASSES or needs not in NEEDS:
        raise ValueError(f"bad metadata on {id}")

    def wrap(fn):
        if id in REGISTRY:
            raise ValueError(f"duplicate check {id}")
        REGISTRY[id] = Check(id, category, title, severity, fix, needs, source, fn, frozenset(skip), when, opinion)
        return fn

    return wrap


class Reader:
    """Runs git and gh for checks and refuses anything that could change state."""

    def __init__(self, path: Optional[Path], timeout: int = 120):
        self.path = path
        self.timeout = timeout
        self.last_stderr = ""
        self.env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", MSYS_NO_PATHCONV="1", GIT_TERMINAL_PROMPT="0",
                        GH_PROMPT_DISABLED="1", GH_NO_UPDATE_NOTIFIER="1", NO_COLOR="1")

    def git(self, *args: str, check_rc: bool = False) -> tuple[int, str]:
        if not args or args[0] not in GIT_READ:
            raise WriteRefused(f"git {args[:1]} is outside the read list")
        if args[0] == "config" and not ({"--get", "--get-regexp", "--list", "-l"} & set(args)):
            raise WriteRefused("git config without a read flag")
        if args[0] == "remote" and args[1:2] != ("get-url",):
            raise WriteRefused("git remote without get-url")
        if self.path is None:
            raise Unknown("needs a local checkout")
        try:
            p = subprocess.run(["git", *GIT_SAFE_FLAGS, "-C", str(self.path), *args], capture_output=True,
                               env=self.env, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            raise Unknown(f"git {args[0]} timed out")
        except FileNotFoundError:
            raise Unknown("git is not installed")
        out = p.stdout.decode("utf-8", "replace")
        self.last_stderr = p.stderr.decode("utf-8", "replace")
        if check_rc and p.returncode != 0:
            raise Unknown(f"git {args[0]} exit {p.returncode}: {self.last_stderr.strip()[:160]}")
        return p.returncode, out

    def gh_allowed(self, args: tuple) -> None:
        if not any(args[: len(k)] == k for k in GH_READ):
            raise WriteRefused(f"gh {args[:2]} is outside the read list")
        if args[0] == "api":
            target = next((a for a in args[1:] if not a.startswith("-")), "")
            if target == "graphql":
                query = next((a[6:] for a in args if a.startswith("query=")), "")
                if not query or re.match(r"\s*mutation\b", query) or {"-X", "--method", "--input"} & set(args):
                    raise WriteRefused("graphql write")
            elif GH_WRITE_FLAGS & set(args):
                raise WriteRefused("gh api with a write flag")

    def gh(self, *args: str) -> str:
        self.gh_allowed(args)
        if shutil.which("gh") is None:
            raise Unknown("gh is not installed")
        cmd = ["gh", *args]
        try:
            p = subprocess.run(cmd, capture_output=True, env=self.env, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            raise Unknown("gh timed out")
        err = p.stderr.decode("utf-8", "replace")
        if p.returncode != 0:
            code = re.search(r"HTTP (\d{3})", err)
            raise GhError(int(code.group(1)) if code else 0, err.strip()[:160])
        return p.stdout.decode("utf-8", "replace")


class GhError(Unknown):
    def __init__(self, code: int, message: str):
        super().__init__(f"GitHub answered {code or 'with an error'}: {message}")
        self.code = code


@dataclass
class Ctx:
    reader: Reader
    path: Optional[Path]
    slug: Optional[str]
    online: bool
    policy: dict = field(default_factory=dict)
    kind: str = "unknown"
    modifiers: tuple = ()
    _cache: dict = field(default_factory=dict)

    def memo(self, key: str, make: Callable):
        if key not in self._cache:
            try:
                self._cache[key] = (True, make())
            except Unknown as e:
                self._cache[key] = (False, e)
        good, value = self._cache[key]
        if not good:
            raise value
        return value

    def tracked(self) -> list[str]:
        def make():
            _, out = self.reader.git("ls-files", "-z", check_rc=True)
            return [p for p in out.split("\0") if p]
        return self.memo("tracked", make)

    def read(self, rel: str) -> Optional[str]:
        """Text of a tracked file, or None. Never follows a link out of the repository."""
        if self.path is None:
            return None
        p = self.path / rel
        try:
            if p.is_symlink() or not p.is_file():
                return None
            return p.read_bytes().decode("utf-8", "replace").lstrip("﻿").replace("\r\n", "\n")
        except OSError:
            return None

    def api(self, endpoint: str, missing_ok: bool = False):
        """GET through gh. A 403 or 404 is Unknown unless the caller says 404 means absent."""
        if not self.online or not self.slug:
            raise Unknown("needs GitHub access")

        def make():
            try:
                return json.loads(self.reader.gh("api", endpoint) or "null")
            except GhError as e:
                if e.code == 404 and missing_ok:
                    return None
                raise
        return self.memo("api:" + endpoint, make)

    def graphql(self, query: str):
        """Run a read query with $o and $n bound to this repository."""
        if not self.online or not self.slug:
            raise Unknown("needs GitHub access")
        owner, name = self.slug.split("/", 1)

        def make():
            out = self.reader.gh("api", "graphql", "-F", f"o={owner}", "-F", f"n={name}", "-f", "query=" + query)
            return json.loads(out)["data"]
        return self.memo("gql:" + query, make)

    def meta(self) -> dict:
        return self.api(f"repos/{self.slug}")

    @property
    def public(self) -> Optional[bool]:
        if not self.online or not self.slug:
            return self.policy.get("public")
        try:
            return not self.meta().get("private", True)
        except Unknown:
            return self.policy.get("public")

    @property
    def default_branch(self) -> str:
        def make():
            if self.online and self.slug:
                try:
                    return self.meta()["default_branch"]
                except Unknown:
                    pass
            rc, out = self.reader.git("rev-parse", "--abbrev-ref", "origin/HEAD")
            if rc == 0 and out.strip().startswith("origin/"):
                return out.strip()[7:]
            _, out = self.reader.git("rev-parse", "--abbrev-ref", "HEAD", check_rc=True)
            return out.strip()
        return self.memo("default_branch", make)

    def shallow(self) -> bool:
        def make():
            _, out = self.reader.git("rev-parse", "--is-shallow-repository")
            return out.strip() == "true"
        return self.memo("shallow", make)

    def solo(self) -> bool:
        """True when one person made the recent human commits. The policy file can override this."""
        if "solo" in self.policy:
            return bool(self.policy["solo"])

        def make():
            _, out = self.reader.git("log", "--since=1.year", "--no-merges", "--format=%aE")
            people = {e.lower() for e in out.split() if "[bot]" not in e and "bot@" not in e}
            return len(people) <= 1
        return self.memo("solo", make)


def load_policy(path: Optional[Path], explicit: Optional[Path]) -> tuple[dict, list[str]]:
    """Read the owner's policy file. It is data, and only known keys take effect."""
    known = {"type", "audience", "goal", "readme_preset", "badge_policy", "pr_style", "issue_set", "default_branch",
             "merge_methods", "commit_convention", "require_signing", "solo", "public", "waivers", "lockfile", "bar"}
    target = explicit or (path / ".github" / "repo-standards.json" if path else None)
    if target is None or not target.is_file():
        return {}, []
    try:
        raw = json.loads(target.read_text("utf-8-sig"))
    except (OSError, ValueError) as e:
        return {}, [f"policy file ignored: {e}"]
    if not isinstance(raw, dict):
        return {}, ["policy file ignored: not an object"]
    notes = [f"unknown policy key ignored: {k}" for k in raw if k not in known]
    return {k: v for k, v in raw.items() if k in known}, notes


def active_waiver(policy: dict, check_id: str, today: Optional[date] = None) -> Optional[str]:
    today = today or date.today()
    for w in policy.get("waivers") or []:
        if not isinstance(w, dict) or w.get("check") != check_id or not str(w.get("reason", "")).strip():
            continue
        expires = w.get("expires")
        if expires:
            try:
                if date.fromisoformat(str(expires)) < today:
                    continue
            except ValueError:
                continue
        return str(w["reason"])
    return None


def run_check(c: Check, ctx: Ctx) -> Result:
    if ctx.kind in c.skip:
        return Result(NA, f"does not apply to a {ctx.kind} repository")
    if c.needs in ("github", "admin") and (not ctx.online or not ctx.slug):
        return Result(UNKNOWN, "needs GitHub access: rerun with a GitHub remote and a signed-in gh")
    if c.needs in ("tree", "history") and ctx.path is None:
        return Result(UNKNOWN, "needs a local checkout")
    try:
        if c.when:
            reason = c.when(ctx)
            if reason:
                return Result(NA, reason)
        if c.needs == "history" and ctx.shallow():
            return Result(UNKNOWN, "shallow clone: rerun on a full clone or a mirror")
        result = c.fn(ctx)
    except NotApplicable as e:
        return Result(NA, str(e))
    except Unknown as e:
        return Result(UNKNOWN, str(e))
    except (KeyError, TypeError, AttributeError, ValueError, IndexError, OSError) as e:
        return Result(UNKNOWN, f"the check could not read this data: {type(e).__name__}")
    if result.status == FAIL:
        reason = active_waiver(ctx.policy, c.id)
        if reason:
            return Result(WAIVED, f"waived by owner: {reason}. Measured: {result.detail}", result.items)
    return result


def run_all(ctx: Ctx) -> list[dict]:
    rows = []
    for c in sorted(REGISTRY.values(), key=lambda x: x.id):
        r = run_check(c, ctx)
        rows.append({"id": c.id, "category": c.category, "title": c.title, "severity": c.severity, "fix": c.fix,
                     "needs": c.needs, "source": c.source, "opinion": c.opinion, "status": r.status,
                     "detail": r.detail, "items": list(r.items)})
    return rows


FIXTURE_PATH = re.compile(r"(^|/)(test|tests|testdata|test_data|fixtures?|__fixtures__|__snapshots__|spec|examples?|samples?)/", re.I)


def is_fixture(path: str) -> bool:
    return bool(FIXTURE_PATH.search(path))


def rel(p: str) -> str:
    return Path(p).as_posix()
