#!/usr/bin/env python3
"""Inventory one owner's repositories through paged, read-only GraphQL.

The only request this script can send is the QUERY constant below. The owner,
page size and cursor travel as GraphQL variables. Exit 0 is a finished scan,
1 is a partial scan that needs attention, 2 is bad input or an unusable gh.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
import json
import os
import re
import subprocess
import tempfile
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

SCHEMA_VERSION = 1
PAGE_SIZES = (50, 25, 10)
MAX_ATTEMPTS = 5
MAX_WAIT_SECONDS = 900
FIRST_WAIT_SECONDS = 60
RETRY_WAIT_SECONDS = 10
LOW_BUDGET_POINTS = 100
REQUEST_TIMEOUT_SECONDS = 60

# Three tree lookups answer every file question below. Separate object() lookups
# per path returned HTTP 502 at page size 50, see references/limits.md.
TREES = (("root", ""), ("dotgithub", ".github"), ("docs", "docs"))
LOOKUP_ORDER = ("dotgithub", "root", "docs")
BLOB, TREE = "blob", "tree"

# key, folders in GitHub's lookup order, name pattern, entry types. Names match without case.
FILE_RULES: tuple[tuple[str, tuple[str, ...], str, tuple[str, ...]], ...] = (
    ("readme", LOOKUP_ORDER, r"readme(\.[\w.-]+)?", (BLOB,)),
    ("license", ("root",), r"(licen[cs]e|copying)([.-][\w.-]+)?", (BLOB,)),
    ("security", LOOKUP_ORDER, r"security(\.\w+)?", (BLOB,)),
    ("contributing", LOOKUP_ORDER, r"contributing(\.\w+)?", (BLOB,)),
    ("codeowners", LOOKUP_ORDER, r"codeowners", (BLOB,)),
    ("dependabot", ("dotgithub",), r"dependabot\.ya?ml", (BLOB,)),
    ("gitignore", ("root",), r"\.gitignore", (BLOB,)),
    ("gitattributes", ("root",), r"\.gitattributes", (BLOB,)),
    ("workflows", ("dotgithub",), r"workflows", (TREE,)),
    ("issue_templates", LOOKUP_ORDER, r"issue_template(\.md)?", (BLOB, TREE)),
    ("pr_template", LOOKUP_ORDER, r"pull_request_template(\.md)?", (BLOB, TREE)),
)
# A default in the owner's public .github repository covers these when a repository has none.
INHERITABLE = ("security", "contributing", "issue_templates", "pr_template")


def _build_query() -> str:
    lookups = " ".join(f'{alias}: object(expression: "HEAD:{path}") {{ ... on Tree {{ entries {{ name type }} }} }}' for alias, path in TREES)
    return (
        "query FleetScan($owner: String!, $first: Int!, $cursor: String) { "
        "rateLimit { cost remaining resetAt } "
        "repositoryOwner(login: $owner) { "
        "repositories(first: $first, after: $cursor, ownerAffiliations: [OWNER], "
        "orderBy: {field: NAME, direction: ASC}) { "
        "totalCount pageInfo { hasNextPage endCursor } "
        "nodes { nameWithOwner visibility isArchived isFork isMirror isTemplate isEmpty "
        "defaultBranchRef { name } pushedAt diskUsage stargazerCount "
        "licenseInfo { spdxId } primaryLanguage { name } repositoryTopics(first: 1) { totalCount } "
        f"description viewerPermission {lookups} }} }} }} }}"
    )


def _require_read_only(query: str) -> str:
    if not re.match(r"\s*query\b", query) or re.search(r"\b(mutation|subscription)\b", query, re.IGNORECASE):
        raise RuntimeError("fleet_scan only sends read queries")
    return query


QUERY = _require_read_only(_build_query())

OWNER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,38}")
SECRET = re.compile(r"\b(gh[pousr]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,})")
CAN_WRITE = ("ADMIN", "MAINTAIN", "WRITE")

Runner = Callable[[list[str]], "tuple[int, str, str]"]


class BadInput(Exception):
    """Input or environment problem that maps to exit 2."""


def run_gh(argv: list[str]) -> tuple[int, str, str]:
    env = dict(os.environ, MSYS_NO_PATHCONV="1", GH_PROMPT_DISABLED="1")
    try:
        proc = subprocess.run(
            argv, capture_output=True, encoding="utf-8", errors="replace", env=env, timeout=REQUEST_TIMEOUT_SECONDS
        )
    except FileNotFoundError:
        return 127, "", "gh was not found on PATH"
    except subprocess.TimeoutExpired:
        return 124, "", "request timeout"
    return proc.returncode, proc.stdout, proc.stderr


def page_argv(owner: str, first: int, cursor: str | None) -> list[str]:
    argv = ["gh", "api", "graphql", "--include", "-f", f"query={QUERY}", "-f", f"owner={owner}", "-F", f"first={first}"]
    if cursor:
        argv += ["-f", f"cursor={cursor}"]
    return argv


def safe(text: object) -> str:
    line = next((part for part in str(text).splitlines() if part.strip()), "")
    return SECRET.sub("[redacted]", line)[:200]


@dataclass
class Reply:
    rc: int
    status: int | None
    headers: dict[str, str]
    body: dict | None
    stderr: str


def parse_reply(rc: int, out: str, err: str) -> Reply:
    status, headers, text = None, {}, out
    if out.startswith("HTTP/"):
        head, _, text = out.replace("\r\n", "\n").partition("\n\n")
        lines = head.split("\n")
        match = re.match(r"HTTP/\S+\s+(\d{3})", lines[0])
        status = int(match.group(1)) if match else None
        for line in lines[1:]:
            name, _, value = line.partition(":")
            headers[name.strip().lower()] = value.strip()
    if status is None:
        match = re.search(r"\bHTTP (\d{3})\b", err)
        status = int(match.group(1)) if match else None
    try:
        body = json.loads(text) if text.strip() else None
    except ValueError:
        body = None
    return Reply(rc, status, headers, body if isinstance(body, dict) else None, err)


def error_text(reply: Reply) -> str:
    parts = [reply.stderr]
    if reply.body:
        parts.append(str(reply.body.get("message", "")))
        parts += [str(item.get("message", "")) for item in reply.body.get("errors") or [] if isinstance(item, dict)]
    return " ".join(part for part in parts if part)


def classify(reply: Reply) -> str:
    """Return one of rate, auth, shrink, ok, retry or fatal."""
    text = error_text(reply).lower()
    types = [item.get("type") for item in (reply.body or {}).get("errors") or [] if isinstance(item, dict)]
    if "RATE_LIMITED" in types or "rate limit" in text or "abuse detection" in text:
        return "rate"
    if reply.status in (403, 429) and ("retry-after" in reply.headers or reply.headers.get("x-ratelimit-remaining") == "0"):
        return "rate"
    if reply.rc == 127 or reply.status == 401 or "gh auth login" in text:
        return "auth"
    has_data = bool(reply.body and reply.body.get("data"))
    if reply.status in (502, 503, 504) or reply.rc == 124:
        return "shrink"
    if not has_data and ("timeout" in text or "timed out" in text or "in time" in text):
        return "shrink"
    if has_data:
        return "ok"
    if reply.status and 400 <= reply.status < 500:
        return "fatal"
    return "retry" if reply.rc != 0 else "fatal"


def rate_wait(reply: Reply, attempt: int, now: float) -> float:
    retry_after = reply.headers.get("retry-after", "")
    if retry_after.isdigit():
        return max(int(retry_after), 1)
    reset = reply.headers.get("x-ratelimit-reset", "")
    if reply.headers.get("x-ratelimit-remaining") == "0" and reset.isdigit():
        return max(int(reset) - now, 1)
    return min(FIRST_WAIT_SECONDS * 2 ** (attempt - 1), MAX_WAIT_SECONDS)


def find_files(node: dict) -> dict[str, str | None]:
    found: dict[str, str | None] = {}
    folders = dict(TREES)
    for key, places, pattern, kinds in FILE_RULES:
        found[key] = None
        for place in places:
            entries = (node.get(place) or {}).get("entries") or []
            match = next((e for e in entries if e.get("type") in kinds and re.fullmatch(pattern, str(e.get("name")), re.IGNORECASE)), None)
            if match:
                found[key] = f"{folders[place]}/{match['name']}".lstrip("/")
                break
    return found


def record_of(node: dict) -> dict:
    # An empty repository has no HEAD, so nothing can be said about its files.
    files = None if node.get("isEmpty") else find_files(node)
    return {
        "name": node.get("nameWithOwner"),
        "visibility": node.get("visibility"),
        "archived": bool(node.get("isArchived")),
        "fork": bool(node.get("isFork")),
        "mirror": bool(node.get("isMirror")),
        "template": bool(node.get("isTemplate")),
        "empty": bool(node.get("isEmpty")),
        "default_branch": (node.get("defaultBranchRef") or {}).get("name"),
        "pushed_at": node.get("pushedAt"),
        "disk_usage_kb": node.get("diskUsage"),
        "stars": node.get("stargazerCount"),
        "license": (node.get("licenseInfo") or {}).get("spdxId"),
        "primary_language": (node.get("primaryLanguage") or {}).get("name"),
        "topics_count": (node.get("repositoryTopics") or {}).get("totalCount", 0),
        "description_present": bool((node.get("description") or "").strip()),
        "viewer_permission": node.get("viewerPermission"),
        "files": files,
    }


def apply_scope(record: dict, include_archived: bool, include_forks: bool) -> dict:
    reasons = []
    if record["archived"] and not include_archived:
        reasons.append("archived")
    if record["fork"] and not include_forks:
        reasons.append("fork")
    if record["mirror"]:
        reasons.append("mirror")
    if record["viewer_permission"] not in CAN_WRITE:
        reasons.append("no_write_access")
    record["in_scope"] = not reasons
    record["out_of_scope_reasons"] = reasons
    return record


@dataclass
class Scan:
    records: list[dict] = field(default_factory=list)
    total: int | None = None
    page_sizes: list[int] = field(default_factory=list)
    cost: int = 0
    rate_limit_events: int = 0
    stop_reason: str | None = None
    warnings: list[str] = field(default_factory=list)
    limited: bool = False


def scan(owner: str, limit: int | None, runner: Runner, sleep: Callable[[float], None], clock: Callable[[], float]) -> Scan:
    result = Scan(page_sizes=[PAGE_SIZES[0]])
    sizes, seen = list(PAGE_SIZES), set()
    cursor, failures = None, 0

    def pause(seconds: float, why: str) -> bool:
        if seconds > MAX_WAIT_SECONDS:
            result.stop_reason = f"{why}: wait of {int(seconds)} seconds is past the {MAX_WAIT_SECONDS} second cap"
            return False
        print(f"{why}: waiting {int(seconds)} seconds", file=sys.stderr)
        sleep(seconds)
        return True

    while True:
        first = sizes[0] if limit is None else min(sizes[0], limit - len(result.records))
        reply = parse_reply(*runner(page_argv(owner, first, cursor)))
        kind = classify(reply)

        if kind == "auth":
            raise BadInput(f"gh cannot read GitHub: {safe(error_text(reply))}")
        if kind == "fatal":
            if not result.records:
                raise BadInput(f"GitHub refused the query: {safe(error_text(reply))}")
            result.stop_reason = f"GitHub refused a page: {safe(error_text(reply))}"
            return result
        if kind != "ok":
            failures += 1
            if kind == "rate":
                result.rate_limit_events += 1
            if kind == "shrink" and len(sizes) > 1:
                sizes.pop(0)
                result.page_sizes.append(sizes[0])
                print(f"page failed, retrying at page size {sizes[0]}", file=sys.stderr)
                continue
            if failures > MAX_ATTEMPTS:
                result.stop_reason = f"gave up after {MAX_ATTEMPTS} retries: {safe(error_text(reply))}"
                return result
            wait = rate_wait(reply, failures, clock()) if kind == "rate" else RETRY_WAIT_SECONDS
            if not pause(wait, "rate limit" if kind == "rate" else "request failed"):
                return result
            continue

        failures = 0
        data = reply.body["data"]
        owner_node = data.get("repositoryOwner")
        if owner_node is None:
            detail = safe(error_text(reply))
            raise BadInput(f"owner {owner} not found or not visible" + (f": {detail}" if detail else ""))
        connection = owner_node.get("repositories")
        if connection is None:
            result.stop_reason = f"no repository data returned: {safe(error_text(reply))}"
            return result
        if reply.body.get("errors"):
            result.warnings.append(f"partial page: {safe(error_text(reply))}")
        budget = data.get("rateLimit") or {}
        result.cost += budget.get("cost") or 0
        result.total = connection.get("totalCount")
        for node in connection.get("nodes") or []:
            if not node:
                result.warnings.append("a repository came back null")
            elif node.get("nameWithOwner") not in seen:
                seen.add(node.get("nameWithOwner"))
                result.records.append(record_of(node))
        info = connection.get("pageInfo") or {}
        if not info.get("hasNextPage"):
            return result
        if limit is not None and len(result.records) >= limit:
            result.limited = True
            return result
        cursor = info.get("endCursor")
        remaining = budget.get("remaining")
        if remaining is not None and remaining < LOW_BUDGET_POINTS:
            try:
                reset = datetime.fromisoformat(str(budget.get("resetAt")).replace("Z", "+00:00")).timestamp()
            except ValueError:
                reset = clock() + FIRST_WAIT_SECONDS
            if not pause(max(reset - clock(), 1), "hourly budget is low"):
                return result


def owner_defaults(records: list[dict], owner: str) -> str:
    match = next((r for r in records if str(r["name"]).lower() == f"{owner}/.github".lower()), None)
    if match is None:
        return "absent"
    return "public" if match["visibility"] == "PUBLIC" else "not public"


def build_report(owner: str, result: Scan, stamp: str, include_archived: bool, include_forks: bool) -> dict:
    records = [apply_scope(r, include_archived, include_forks) for r in result.records]
    short = result.total is not None and len(records) < result.total
    return {
        "schema_version": SCHEMA_VERSION,
        "owner": owner,
        "scanned_at": stamp,
        "complete": not (result.limited or result.stop_reason or result.warnings or short),
        "stop_reason": result.stop_reason,
        "limited": result.limited,
        "warnings": result.warnings,
        "reported_total": result.total,
        "read_total": len(records),
        "in_scope_total": sum(r["in_scope"] for r in records),
        "page_sizes_used": result.page_sizes,
        "graphql_points": result.cost,
        "rate_limit_events": result.rate_limit_events,
        "owner_defaults_repository": "unknown" if result.limited or result.stop_reason else owner_defaults(records, owner),
        "repositories": records,
    }


def table(title: str, rows: list[tuple]) -> list[str]:
    width = max(len(str(row[0])) for row in rows) if rows else 0
    return [title] + [f"  {str(row[0]).ljust(width)}  " + "  ".join(str(cell).rjust(5) for cell in row[1:]) for row in rows]


def summary(report: dict) -> str:
    records = report["repositories"]
    in_scope = [r for r in records if r["in_scope"]]
    state = "complete" if report["complete"] else "PARTIAL"
    lines = [f"Fleet scan of {report['owner']}: read {report['read_total']} of {report['reported_total']}, {state}"]
    if report["stop_reason"]:
        lines.append(f"Stopped: {report['stop_reason']}")
    if report["limited"]:
        lines.append("Stopped at --limit, so counts cover part of the fleet.")
    reasons = Counter(reason for r in records for reason in r["out_of_scope_reasons"])
    lines += table("Scope", [("in scope", len(in_scope))] + sorted(reasons.items()))
    lines += table("Visibility", sorted(Counter(str(r["visibility"]) for r in records).items()))
    lines += table("Viewer permission", sorted(Counter(str(r["viewer_permission"]) for r in records).items()))
    lines += table(
        "Traits, all read",
        [
            ("template", sum(r["template"] for r in records)),
            ("empty", sum(r["empty"] for r in records)),
            ("no license detected", sum(r["license"] is None for r in records)),
            ("no description", sum(not r["description_present"] for r in records)),
            ("no topics", sum(not r["topics_count"] for r in records)),
        ],
    )
    base = [r for r in in_scope if r["files"] is not None]
    rows = []
    for key, *_ in FILE_RULES:
        present = sum(r["files"][key] is not None for r in base)
        rows.append((key + (" *" if key in INHERITABLE else ""), present, len(base) - present))
    lines += table(f"Files in {len(base)} in-scope, non-empty repositories (present, absent)", rows)
    lines.append(f"* Absent here can still be inherited. Owner .github repository: {report['owner_defaults_repository']}.")
    lines.append(
        f"GraphQL points {report['graphql_points']}, page sizes {report['page_sizes_used']}, "
        f"rate limit events {report['rate_limit_events']}."
    )
    return "\n".join(lines)


def write_atomic(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.resolve().parent), prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be 1 or more")
    return number


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only inventory of one owner's repositories.")
    parser.add_argument("owner", help="organization or user login")
    parser.add_argument("--output", default="fleet.json", help="JSON path, default fleet.json")
    parser.add_argument("--include-archived", action="store_true", help="count archived repositories as in scope")
    parser.add_argument("--include-forks", action="store_true", help="count forks as in scope")
    parser.add_argument("--limit", type=positive, help="stop after reading this many repositories")
    return parser.parse_args(argv)


def main(
    argv: list[str] | None = None,
    runner: Runner = run_gh,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.time,
) -> int:
    args = parse_args(argv)
    output = Path(args.output)
    try:
        if not OWNER.fullmatch(args.owner):
            raise BadInput(f"not a GitHub login: {safe(args.owner)}")
        if output.is_dir() or not output.resolve().parent.is_dir():
            raise BadInput(f"cannot write {output}")
        result = scan(args.owner, args.limit, runner, sleep, clock)
    except BadInput as problem:
        print(f"error: {problem}", file=sys.stderr)
        return 2
    stamp = datetime.fromtimestamp(clock(), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report = build_report(args.owner, result, stamp, args.include_archived, args.include_forks)
    write_atomic(output, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(summary(report))
    print(f"Wrote {output}")
    clean_limit = report["limited"] and not report["stop_reason"] and not report["warnings"]
    return 0 if report["complete"] or clean_limit else 1


if __name__ == "__main__":
    sys.exit(main())
