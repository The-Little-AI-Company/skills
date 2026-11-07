#!/usr/bin/env python3
"""Read-only repository audit. Writes a report and changes nothing in the audited repository.

Exit 0 when no critical or high check failed. Exit 1 when one did. Exit 2 on bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import checks_git  # noqa: E402,F401  registers checks
import checks_github  # noqa: E402,F401  registers checks
import checks_readme  # noqa: E402,F401  registers checks
from detect import detect, modifiers  # noqa: E402
from engine import FAIL, INFO, NA, PASS, REGISTRY, SEVERITIES, UNKNOWN, VERSION, WAIVED, Ctx, Reader, Unknown, load_policy, run_all  # noqa: E402

FIX_LABEL = {"auto": "Safe to apply", "pr": "Reviewable PR", "setting": "Owner setting", "rewrite": "History rewrite, destructive", "report": "Report only"}
SLUG = re.compile(r"github\.com[:/]+([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")


def slug_from_remote(reader: Reader):
    try:
        rc, out = reader.git("remote", "get-url", "origin")
    except Unknown:
        return None
    m = SLUG.search(out.strip()) if rc == 0 else None
    return f"{m.group(1)}/{m.group(2)}" if m else None


def build(path, slug, online, policy_file=None) -> dict:
    reader = Reader(path)
    if path is not None and reader.git("rev-parse", "--git-dir")[0] != 0:
        raise SystemExit(_usage(f"{path} is not a git repository"))
    slug = slug or (slug_from_remote(reader) if path else None)
    policy, notes = load_policy(path, policy_file)
    ctx = Ctx(reader, path, slug, online and bool(slug), policy)
    kind = detect(ctx)
    ctx.kind = kind["name"]
    ctx.modifiers = modifiers(ctx)
    rows = run_all(ctx)
    try:
        head = reader.git("rev-parse", "HEAD")[1].strip() if path else None
    except Unknown:
        head = None
    counts = Counter(r["status"] for r in rows)
    measured = counts[PASS] + counts[FAIL] + counts[INFO] + counts[WAIVED]
    return {
        "schema_version": 1,
        "tool": {"name": "repo-audit", "version": VERSION},
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo": {"slug": slug, "head": head, "default_branch": _safe(lambda: ctx.default_branch), "online": ctx.online},
        "type": kind,
        "modifiers": list(ctx.modifiers),
        "solo": _safe(ctx.solo),
        "policy": {k: v for k, v in policy.items() if k != "waivers"},
        "notes": notes,
        "summary": {"pass": counts[PASS], "fail": counts[FAIL], "info": counts[INFO], "unknown": counts[UNKNOWN], "not_applicable": counts[NA],
                    "waived": counts[WAIVED], "measured": measured, "applicable": measured + counts[UNKNOWN]},
        "bar": bar(rows, policy.get("bar")),
        "checks": rows,
    }


def bar(rows: list, wanted=None) -> dict:
    """The highest bar these rows reach before verification. Judgment can only lower immaculate."""
    fails = [r for r in rows if r["status"] == FAIL]
    high = sum(r["severity"] in ("critical", "high") for r in fails)
    medium = sum(r["severity"] == "medium" for r in fails)
    unknown = sum(r["status"] == UNKNOWN for r in rows)
    if high:
        reached = "below presentable"
    elif medium:
        reached = "presentable"
    elif fails or unknown:
        reached = "strong"
    else:
        reached = "immaculate, pending the judgment list"
    return {"reached": reached, "wanted": wanted or "not set", "high_or_critical_failures": high, "medium_failures": medium, "other_failures": len(fails) - high - medium, "unknown": unknown}


def _safe(fn):
    try:
        return fn()
    except Unknown:
        return None


def _usage(message: str) -> str:
    print(f"repo-audit: {message}", file=sys.stderr)
    return 2


def table_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render(report: dict) -> str:
    s, rows = report["summary"], report["checks"]
    t = report["type"]
    out = [f"# Repository audit: {report['repo']['slug'] or 'local checkout'}", ""]
    out.append(f"Head `{(report['repo']['head'] or 'unknown')[:12]}`. Type **{t['name']}** ({t['confidence']} confidence: {'; '.join(t['signals']) or 'no signals'}).")
    if t["also"]:
        out.append(f"It also matched {', '.join(t['also'])}. Set `type` in `.github/repo-standards.json` if the detection is wrong.")
    if report["modifiers"]:
        out.append(f"State: {', '.join(report['modifiers'])}.")
    if "archived" in report["modifiers"]:
        out.append("This repository is archived, so GitHub refuses writes. Treat fixes as advice.")
    b = report["bar"]
    out += ["", f"Measured bar: **{b['reached']}** (wanted: {b['wanted']}). {b['high_or_critical_failures']} critical or high failures, {b['medium_failures']} medium, {b['other_failures']} lower, {b['unknown']} unknown."]
    out += ["", f"Measured {s['measured']} of {s['applicable']} applicable checks: {s['pass']} passed, {s['fail']} failed, {s['info']} noted, {s['waived']} waived. {s['unknown']} could not be measured, and {s['not_applicable']} do not apply.", ""]
    for n in report["notes"]:
        out.append(f"Note: {n}")
    fails = sorted((r for r in rows if r["status"] == FAIL), key=lambda r: (SEVERITIES.index(r["severity"]), r["id"]))
    out += ["## Findings", ""]
    if not fails:
        out += ["No check failed.", ""]
    for r in fails:
        tag = " Opinion." if r["opinion"] else ""
        out.append(f"- **{r['id']}** ({r['severity']}, {FIX_LABEL[r['fix']]}) {r['title']}. {r['detail']}.{tag} Basis: {r['source']}.")
        out += [f"  - `{i}`" for i in r["items"][:10]]
    out += ["", "## Worth a look", ""]
    notes = [r for r in rows if r["status"] == INFO]
    out += [f"- **{r['id']}** {r['title']}. {r['detail']}." for r in notes] or ["Nothing."]
    out += ["", "## Could not measure", ""]
    unknown = [r for r in rows if r["status"] == UNKNOWN]
    out += [f"- **{r['id']}** {r['title']}. {r['detail']}." for r in unknown] or ["Nothing."]
    waived = [r for r in rows if r["status"] == WAIVED]
    if waived:
        out += ["", "## Waived by the owner", ""] + [f"- **{r['id']}** {r['detail']}" for r in waived]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default=".", help="local checkout to audit")
    ap.add_argument("--repo", help="owner/name, when the remote is not GitHub origin")
    ap.add_argument("--offline", action="store_true", help="use git and the tree only")
    ap.add_argument("--policy", type=Path, help="policy file, default .github/repo-standards.json in the target")
    ap.add_argument("--format", choices=("md", "json"), default="md")
    ap.add_argument("--output", type=Path, help="write here instead of stdout")
    ap.add_argument("--list-checks", action="store_true", help="print the catalog and exit")
    a = ap.parse_args(argv)
    if a.list_checks:
        for c in sorted(REGISTRY.values(), key=lambda x: x.id):
            print(f"{c.id}\t{c.category}\t{c.severity}\t{c.fix}\t{c.needs}\t{c.title}")
        return 0
    path = Path(a.path).resolve()
    if not path.is_dir():
        return _usage(f"{a.path} is not a directory")
    report = build(path, a.repo, not a.offline, a.policy)
    text = json.dumps(report, indent=2) if a.format == "json" else render(report)
    if a.output:
        a.output.write_text(text + "\n", "utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)
    return 1 if any(r["status"] == FAIL and r["severity"] in ("critical", "high") for r in report["checks"]) else 0


if __name__ == "__main__":
    sys.exit(main())
