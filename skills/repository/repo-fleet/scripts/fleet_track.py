#!/usr/bin/env python3
"""Refresh a campaign TSV from gh pr view and evaluate the ring stop rules.

Only state, ci and last_check change. Every other column, including columns
this script does not know, stays as it was. Exit 0 means no rule fired and
every row refreshed, 1 needs attention, 2 is bad input or an unusable gh.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

COLUMNS = ("repo", "finding", "change", "risk", "ring", "plan_hash", "pr_url", "state", "ci", "last_check")
PR_URL = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/[0-9]+")
SECRET = re.compile(r"\b(gh[pousr]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,})")

CHECK_PASS = {"SUCCESS", "NEUTRAL", "SKIPPED"}
CHECK_FAIL = {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE"}

# Stop rules. The 10 percent line comes from SKILL.md and is opinion.
# SKILL.md gives no number for closed pull requests. Two is opinion, from "repeated".
CI_FAIL_PERCENT = 10
CLOSED_STOP = 2
SECONDARY_STOP = 2

# Operator states. A closed pull request keeps one of these across refreshes.
# "explained" also leaves the closed count, so an operator can clear a known closure.
KEPT_WHEN_CLOSED = ("declined", "explained")

MAX_RATE_RETRIES = 3
FIRST_WAIT_SECONDS = 60
REQUEST_TIMEOUT_SECONDS = 60

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


def safe(text: object) -> str:
    line = next((part for part in str(text).splitlines() if part.strip()), "")
    return SECRET.sub("[redacted]", line)[:200]


def read_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with open(path, encoding="utf-8-sig", newline="") as handle:
            lines = re.split(r"\r?\n", handle.read())
    except (OSError, UnicodeDecodeError) as problem:
        raise BadInput(f"cannot read {path}: {safe(problem)}") from problem
    if not lines[0].strip():
        raise BadInput(f"{path} has no header")
    header = lines[0].split("\t")
    missing = [name for name in COLUMNS if name not in header]
    if missing:
        raise BadInput(f"missing columns: {', '.join(missing)}")
    if len(set(header)) != len(header):
        raise BadInput("duplicate column names")
    rows = []
    for number, line in enumerate(lines[1:], 2):
        if not line.strip():
            continue
        cells = line.split("\t")
        if len(cells) != len(header):
            raise BadInput(f"line {number} has {len(cells)} cells, expected {len(header)}")
        rows.append(dict(zip(header, cells)))
    return header, rows


def render_table(header: list[str], rows: list[dict[str, str]]) -> str:
    lines = ["\t".join(header)] + ["\t".join(row[name] for name in header) for row in rows]
    return "\n".join(lines) + "\n"


def write_atomic(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.resolve().parent), prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def ci_from_rollup(rollup: list[dict] | None) -> str:
    """Map check runs and commit statuses to passing, failing, pending or none."""
    if not rollup:
        return "none"
    verdicts = set()
    for item in rollup:
        if "conclusion" in item or item.get("__typename") == "CheckRun":
            value = item.get("conclusion") if item.get("status") == "COMPLETED" else None
        else:
            value = item.get("state")
        if value in CHECK_FAIL:
            verdicts.add("failing")
        elif value in CHECK_PASS:
            verdicts.add("passing")
        else:
            verdicts.add("pending")
    for verdict in ("failing", "pending"):
        if verdict in verdicts:
            return verdict
    return "passing"


def state_from_view(view: dict, previous: str) -> str:
    state = str(view.get("state", "")).upper()
    if state == "CLOSED":
        return previous if previous in KEPT_WHEN_CLOSED else "closed"
    if state == "OPEN" and view.get("isDraft"):
        return "draft"
    return state.lower() or "unknown"


def lookup(url: str, runner: Runner) -> tuple[str, dict | str]:
    """Return ok, rate, secondary, gone, auth or failed, with the view or a message."""
    rc, out, err = runner(["gh", "pr", "view", url, "--json", "state,isDraft,statusCheckRollup"])
    text = err.lower()
    if rc == 0:
        try:
            view = json.loads(out)
        except ValueError:
            return "failed", "gh returned text that is not JSON"
        return ("ok", view) if isinstance(view, dict) else ("failed", "gh returned an unexpected shape")
    if rc == 127 or "gh auth login" in text or "http 401" in text:
        return "auth", safe(err)
    if "secondary rate limit" in text or "abuse detection" in text:
        return "secondary", safe(err)
    if "rate limit" in text:
        return "rate", safe(err)
    if "could not resolve" in text or "not found" in text or "http 404" in text:
        return "gone", safe(err)
    return "failed", safe(err)


def lookup_with_backoff(url: str, row: dict[str, str], runner: Runner, sleep, hits: Counter) -> tuple[str, dict | str]:
    for attempt in range(MAX_RATE_RETRIES + 1):
        kind, value = lookup(url, runner)
        if kind == "secondary":
            hits[row["ring"]] += 1
        if kind not in ("secondary", "rate"):
            break
        if attempt < MAX_RATE_RETRIES:
            sleep(FIRST_WAIT_SECONDS * 2**attempt)
    return kind, value


def refresh(rows, runner, sleep, stamp, hits: Counter) -> tuple[list[str], int]:
    """Update rows in place. Return problem lines and the refreshed count."""
    problems: list[str] = []
    results: dict[str, tuple[str, dict | str]] = {}
    refreshed = 0
    for row in rows:
        url = row["pr_url"].strip()
        if not url:
            continue
        if not PR_URL.fullmatch(url):
            problems.append(f"{row['repo']}: pr_url is not a GitHub pull request URL")
            continue
        if url not in results:
            results[url] = lookup_with_backoff(url, row, runner, sleep, hits)
        kind, value = results[url]
        if kind == "auth":
            raise BadInput(f"gh cannot read GitHub: {value}")
        if kind in ("secondary", "rate"):
            problems.append(f"rate limited after {MAX_RATE_RETRIES} retries, remaining rows were not refreshed")
            break
        if kind == "ok":
            row["state"] = state_from_view(value, row["state"])
            row["ci"] = ci_from_rollup(value.get("statusCheckRollup"))
            row["last_check"] = stamp
            refreshed += 1
        elif kind == "gone":
            row["state"], row["ci"], row["last_check"] = "unknown", "unknown", stamp
            problems.append(f"{row['repo']}: pull request could not be resolved: {value}")
        else:
            problems.append(f"{row['repo']}: lookup failed, row kept as it was: {value}")
    return problems, refreshed


def ring_pull_requests(rows: list[dict[str, str]], ring: str) -> list[dict[str, str]]:
    unique: dict[str, dict[str, str]] = {}
    for row in rows:
        if row["ring"] == ring and row["pr_url"].strip():
            unique.setdefault(row["pr_url"].strip(), row)
    return list(unique.values())


def evaluate_ring(prs: list[dict[str, str]], secondary_hits: int, damage: bool) -> list[str]:
    reasons = []
    failing = sum(row["ci"] == "failing" for row in prs)
    if failing * 100 > CI_FAIL_PERCENT * len(prs):
        reasons.append(f"CI failed on {failing} of {len(prs)} pull requests")
    closed = sum(row["state"] in ("closed", "declined") for row in prs)
    if closed >= CLOSED_STOP:
        reasons.append(f"{closed} pull requests closed unmerged")
    if secondary_hits >= SECONDARY_STOP:
        reasons.append(f"{secondary_hits} secondary rate limits")
    if damage:
        reasons.append("damage reported")
    return reasons


def report(rows, problems, refreshed, hits: Counter, damage: set[str], supplied: set[str]) -> tuple[str, bool]:
    with_pr = sum(bool(row["pr_url"].strip()) for row in rows)
    lines = [f"Campaign: {len(rows)} rows, {with_pr} with a pull request, {refreshed} refreshed", "State"]
    for state, count in sorted(Counter(row["state"] or "(none)" for row in rows).items()):
        lines.append(f"  {state}: {count}")
    lines.append("Rings")
    stopped = False
    for ring in dict.fromkeys(row["ring"] for row in rows):
        prs = ring_pull_requests(rows, ring)
        reasons = evaluate_ring(prs, hits[ring], ring in damage)
        stopped = stopped or bool(reasons)
        failing = sum(row["ci"] == "failing" for row in prs)
        closed = sum(row["state"] in ("closed", "declined") for row in prs)
        unset = sum(not row["state"] for row in rows if row["ring"] == ring)
        secondary = f"{hits[ring]}" + ("" if ring in supplied else " seen by this script")
        reported = "yes" if ring in damage else "not reported to this script"
        lines.append(
            f"  {ring or '(none)'}: {len(prs)} pull requests, {failing} failing CI, {closed} closed unmerged, "
            f"{unset} rows without a state, secondary limits {secondary}, damage {reported}"
        )
        lines.append("    STOP: " + ", ".join(reasons) if reasons else "    no measured rule fired")
    lines.append("Manual checks: ask whether anyone reported damage and read the campaign tool's log for secondary limits.")
    lines.append("This script sees neither on its own. Pass --damage and --secondary-hits with what you find.")
    if problems:
        lines.append("Problems")
        lines += [f"  {problem}" for problem in problems]
    return "\n".join(lines), stopped


def hit_argument(value: str) -> tuple[str, int]:
    ring, sep, count = value.rpartition("=")
    if not sep or not count.isdigit():
        raise argparse.ArgumentTypeError("use RING=COUNT")
    return ring, int(count)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh a campaign TSV and evaluate ring stop rules.")
    parser.add_argument("table", help="campaign TSV")
    parser.add_argument("--output", help="path to write, default the input path")
    parser.add_argument("--damage", action="append", default=[], metavar="RING", help="record a damage report for a ring")
    parser.add_argument(
        "--secondary-hits",
        action="append",
        default=[],
        type=hit_argument,
        metavar="RING=COUNT",
        help="secondary limits the campaign tool hit in a ring",
    )
    return parser.parse_args(argv)


def main(
    argv: list[str] | None = None,
    runner: Runner = run_gh,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> int:
    args = parse_args(argv)
    source = Path(args.table)
    output = Path(args.output) if args.output else source
    try:
        header, rows = read_table(source)
        if output.is_dir() or not output.resolve().parent.is_dir():
            raise BadInput(f"cannot write {output}")
        unknown = (set(args.damage) | {ring for ring, _ in args.secondary_hits}) - {row["ring"] for row in rows}
        if unknown:
            raise BadInput(f"no such ring: {', '.join(sorted(unknown))}")
        hits: Counter = Counter()
        for ring, count in args.secondary_hits:
            hits[ring] += count
        stamp = now().strftime("%Y-%m-%dT%H:%M:%SZ")
        problems, refreshed = refresh(rows, runner, sleep, stamp, hits)
    except BadInput as problem:
        print(f"error: {problem}", file=sys.stderr)
        return 2
    write_atomic(output, render_table(header, rows))
    text, stopped = report(rows, problems, refreshed, hits, set(args.damage), {ring for ring, _ in args.secondary_hits})
    print(text)
    return 1 if stopped or problems else 0


if __name__ == "__main__":
    sys.exit(main())
