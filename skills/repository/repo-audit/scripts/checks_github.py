"""Checks that read GitHub through gh, plus workflow checks that read the local tree."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath

from engine import Ctx, NotApplicable, Unknown, bad, check, note, ok

NO_CI = ("awesome-list", "profile")
NO_DEPS = ("awesome-list", "profile", "docs", "dotfiles", "data")
NO_RELEASES = ("profile", "awesome-list", "dotfiles", "docs", "webapp", "data", "template")
USES = re.compile(r"^\s*-?\s*uses:\s*['\"]?([^'\"\s#]+)['\"]?\s*(#.*)?$")
UNTRUSTED = re.compile(r"\$\{\{[^}]*github\.(event\.(pull_request|issue|comment|review|discussion|head_commit|pages|workflow_run)\b|head_ref)")
FORKED_REF = re.compile(r"github\.event\.pull_request\.head|github\.head_ref|refs/pull/")


def workflows(ctx: Ctx) -> dict[str, str]:
    def make():
        out = {}
        for f in ctx.tracked():
            if re.fullmatch(r"\.github/workflows/[^/]+\.ya?ml", f):
                out[f] = ctx.read(f) or ""
        return out
    return ctx.memo("workflows", make)


def needs_workflows(ctx: Ctx):
    return None if workflows(ctx) else "no GitHub Actions workflows"


def rules(ctx: Ctx) -> list:
    return ctx.api(f"repos/{ctx.slug}/rules/branches/{ctx.default_branch}", missing_ok=True) or []


def solo_skip(ctx: Ctx):
    return "one active committer, so required review is not feasible" if ctx.solo() else None


def private_skip(ctx: Ctx):
    return "private repository" if ctx.public is False else None


def run_lines(text: str) -> list[tuple[int, str]]:
    """Lines that sit inside a `run:` value, found by indentation. Good enough without a YAML parser."""
    lines, out, in_run, indent = text.splitlines(), [], False, 0
    for n, line in enumerate(lines, 1):
        stripped = line.lstrip()
        here = len(line) - len(stripped)
        if not stripped or stripped.startswith("#"):
            continue
        m = re.match(r"(-\s+)?run:\s*(.*)$", stripped)
        if m:
            in_run, indent = bool(m.group(2).strip() in ("|", ">", "|-", ">-", "|+", ">+")), here + (2 if m.group(1) else 0)
            if m.group(2).strip():
                out.append((n, m.group(2)))
            continue
        if in_run:
            if here > indent:
                out.append((n, line))
            else:
                in_run = False
    return out


# Branches

@check("BRN-002", "branches", "Force push and deletion are blocked on the default branch", "high", "setting", "github", "OpenSSF Scorecard Branch-Protection tier 1", skip=NO_CI)
def brn002(ctx):
    types = {r.get("type") for r in rules(ctx)}
    if {"deletion", "non_fast_forward"} <= types:
        return ok()
    if ctx.meta().get("permissions", {}).get("admin"):
        p = ctx.api(f"repos/{ctx.slug}/branches/{ctx.default_branch}/protection", missing_ok=True)
        if p and not p.get("allow_force_pushes", {}).get("enabled") and not p.get("allow_deletions", {}).get("enabled"):
            return ok("classic protection")
        return bad("the default branch allows force push or deletion")
    raise Unknown("no active ruleset is visible, and classic protection needs admin access to read")


@check("BRN-003", "branches", "Pull request with approval required", "high", "setting", "github", "OpenSSF Scorecard Branch-Protection tier 2", skip=NO_CI, when=solo_skip)
def brn003(ctx):
    for r in rules(ctx):
        if r.get("type") == "pull_request" and (r.get("parameters") or {}).get("required_approving_review_count", 0) >= 1:
            return ok()
    if ctx.meta().get("permissions", {}).get("admin"):
        p = ctx.api(f"repos/{ctx.slug}/branches/{ctx.default_branch}/protection", missing_ok=True)
        if p and (p.get("required_pull_request_reviews") or {}).get("required_approving_review_count", 0) >= 1:
            return ok("classic protection")
        return bad("no rule requires an approving review")
    raise Unknown("no matching ruleset is visible, and classic protection needs admin access to read")


@check("BRN-004", "branches", "At least one required status check", "high", "setting", "github", "OpenSSF Scorecard Branch-Protection tier 3", skip=NO_CI, when=needs_workflows)
def brn004(ctx):
    if any(r.get("type") == "required_status_checks" for r in rules(ctx)):
        return ok()
    if ctx.meta().get("permissions", {}).get("admin"):
        p = ctx.api(f"repos/{ctx.slug}/branches/{ctx.default_branch}/protection", missing_ok=True)
        if p and p.get("required_status_checks"):
            return ok("classic protection")
        return bad("CI exists but no check is required before merge")
    raise Unknown("no matching ruleset is visible, and classic protection needs admin access to read")


@check("BRN-007", "branches", "Rulesets are enforcing", "medium", "setting", "github", "GitHub rulesets docs")
def brn007(ctx):
    sets = ctx.api(f"repos/{ctx.slug}/rulesets", missing_ok=True) or []
    idle = [s.get("name") for s in sets if s.get("enforcement") != "active"]
    return bad(f"{len(idle)} rulesets are not enforcing", idle) if idle else ok()


@check("BRN-009", "branches", "Head branches delete on merge", "low", "setting", "github", "GitHub setting. The target is an opinion", opinion=True)
def brn009(ctx):
    d = ctx.graphql("query($o:String!,$n:String!){repository(owner:$o,name:$n){deleteBranchOnMerge}}")
    return ok() if d["repository"]["deleteBranchOnMerge"] else bad("merged head branches stay behind until someone deletes them")


LEFTOVER_QUERY = """query($o:String!,$n:String!){repository(owner:$o,name:$n){
refs(refPrefix:"refs/heads/",first:50){totalCount nodes{name target{oid}
associatedPullRequests(first:10,states:[OPEN,MERGED]){nodes{state headRefOid}}}}}}"""


@check("BRN-010", "branches", "No leftover branches from merged pull requests", "low", "pr", "github", "Merged PR head equals branch tip. git branch --merged misses squash merges", opinion=True)
def brn010(ctx):
    refs = ctx.graphql(LEFTOVER_QUERY)["repository"]["refs"]
    gone = []
    for r in refs["nodes"]:
        prs = r["associatedPullRequests"]["nodes"]
        if r["name"] != ctx.default_branch and not any(p["state"] == "OPEN" for p in prs) and any(p["state"] == "MERGED" and p["headRefOid"] == r["target"]["oid"] for p in prs):
            gone.append(r["name"])
    suffix = f", first 50 of {refs['totalCount']} branches read" if refs["totalCount"] > 50 else ""
    return bad(f"{len(gone)} branches match a merged PR tip{suffix}", gone) if gone else ok(suffix.lstrip(", "))


@check("BRN-011", "branches", "Open pull requests with no recent update", "low", "report", "github", "No source sets the 180 day line", opinion=True)
def brn011(ctx):
    rows = ctx.api(f"repos/{ctx.slug}/pulls?state=open&per_page=100&sort=updated&direction=asc")
    cut = (datetime.now(timezone.utc) - timedelta(days=180)).isoformat()
    old = [f"#{p['number']} {p['title'][:60]}" for p in rows if p["updated_at"] < cut]
    return note(f"{len(old)} open PRs idle for over 180 days", old)


@check("BRN-012", "branches", "Merge methods match the policy", "low", "setting", "github", "Owner policy parameter", opinion=True)
def brn012(ctx):
    want = ctx.policy.get("merge_methods")
    if not want:
        raise NotApplicable("no merge method policy set")
    m = ctx.meta()
    if "allow_squash_merge" not in m:
        raise Unknown("merge settings need write access to read")
    have = {k for k, f in (("squash", "allow_squash_merge"), ("merge", "allow_merge_commit"), ("rebase", "allow_rebase_merge")) if m.get(f)}
    return ok() if have == set(want) else bad(f"allowed {sorted(have)}, policy says {sorted(want)}")


# History seen from the server

@check("HIS-001", "history", "Repository size on the server", "medium", "report", "github", "GitHub: under 1 GB ideal, under 5 GB strongly", skip=("data",))
def his001(ctx):
    kb = ctx.meta().get("size", 0)
    gib = kb / (1024 * 1024)
    return bad(f"{gib:.1f} GiB on the server") if gib >= 1 else ok(f"{kb // 1024} MiB")


@check("HIS-006", "history", "Force pushes to the default branch", "medium", "setting", "github", "Scorecard treats force push as a risk. The zero target is an opinion", opinion=True)
def his006(ctx):
    rows = ctx.api(f"repos/{ctx.slug}/activity?activity_type=force_push&ref={ctx.default_branch}&per_page=100")
    return bad(f"{len(rows)} force pushes in the retained window") if rows else ok()


@check("HIS-011", "history", "Share of recent default branch commits with verified signatures", "low", "report", "github", "GitHub commit signature docs. Any percentage is an opinion", opinion=True)
def his011(ctx):
    rows = ctx.api(f"repos/{ctx.slug}/commits?sha={ctx.default_branch}&per_page=100")
    yes = sum(1 for c in rows if c["commit"]["verification"]["verified"])
    if ctx.policy.get("require_signing") and yes < len(rows):
        return bad(f"{yes} of {len(rows)} commits verified, and the policy requires signing")
    return note(f"{yes} of {len(rows)} recent commits verified")


# Tags and releases

@check("TAG-003", "tags", "A release in the last year", "low", "report", "github", "CNCF CLOMonitor recent_release", skip=NO_RELEASES)
def tag003(ctx):
    rows = ctx.api(f"repos/{ctx.slug}/releases?per_page=1", missing_ok=True) or []
    if not rows:
        return note("no GitHub releases")
    age = datetime.now(timezone.utc) - datetime.fromisoformat(rows[0]["published_at"].replace("Z", "+00:00"))
    return ok(rows[0]["tag_name"]) if age.days <= 365 else note(f"latest release {rows[0]['tag_name']} is {age.days} days old")


@check("TAG-004", "tags", "A ruleset guards version tags", "medium", "setting", "github", "Tag protection through rulesets. The target is an opinion", skip=NO_RELEASES, opinion=True)
def tag004(ctx):
    if not ctx.api(f"repos/{ctx.slug}/releases?per_page=1", missing_ok=True):
        raise NotApplicable("no releases")
    sets = ctx.api(f"repos/{ctx.slug}/rulesets", missing_ok=True) or []
    return ok() if any(s.get("target") == "tag" for s in sets) else bad("nothing stops a release tag from being moved or deleted")


@check("TAG-005", "tags", "Immutable releases are on", "medium", "setting", "admin", "GitHub immutable releases docs. Action repos that move major tags are exempt", skip=NO_RELEASES + ("action",), opinion=True)
def tag005(ctx):
    d = ctx.api(f"repos/{ctx.slug}/immutable-releases")
    return ok() if d.get("enabled") else bad("immutable releases are off")


@check("TAG-007", "tags", "Binary releases carry signatures or provenance", "medium", "pr", "github", "OpenSSF Scorecard Signed-Releases")
def tag007(ctx):
    rows = ctx.api(f"repos/{ctx.slug}/releases?per_page=5", missing_ok=True) or []
    with_assets = [r for r in rows if r.get("assets")]
    if not with_assets:
        raise NotApplicable("no release assets")
    names = [a["name"] for a in with_assets[0]["assets"]]
    signed = [n for n in names if re.search(r"\.(sig|asc|intoto\.jsonl|sigstore|sigstore\.json|pem)$|sha256|checksums?", n, re.I)]
    return ok() if signed else bad(f"{with_assets[0]['tag_name']} ships {len(names)} assets with no signature, provenance or checksums")


# Secrets

def security(ctx: Ctx, name: str):
    s = (ctx.meta().get("security_and_analysis") or {}).get(name)
    if s is None:
        raise Unknown("visible to admins only")
    return s.get("status")


@check("SEC-001", "secrets", "Secret scanning is on", "high", "setting", "admin", "GitHub: automatic and free on public repos")
def sec001(ctx):
    return ok() if security(ctx, "secret_scanning") == "enabled" else bad("secret scanning is off")


@check("SEC-002", "secrets", "Push protection is on", "high", "setting", "admin", "GitHub push protection docs")
def sec002(ctx):
    return ok() if security(ctx, "secret_scanning_push_protection") == "enabled" else bad("push protection is off")


@check("SEC-003", "secrets", "No open secret alerts", "critical", "report", "admin", "GitHub: rotate at once")
def sec003(ctx):
    rows = ctx.api(f"repos/{ctx.slug}/secret-scanning/alerts?state=open&per_page=100")
    return bad(f"{len(rows)} open alerts. Rotate each secret", [f"alert {a['number']}" for a in rows]) if rows else ok()


@check("SEC-010", "secrets", "No deploy keys with write access", "medium", "setting", "admin", "Least privilege. The target is an opinion", opinion=True)
def sec010(ctx):
    rows = ctx.api(f"repos/{ctx.slug}/keys")
    w = [k.get("title") for k in rows if not k.get("read_only")]
    return bad(f"{len(w)} deploy keys can write", w) if w else ok()


# CI

@check("CI-001", "ci", "Workflows exist", "medium", "pr", "tree", "OpenSSF Scorecard CI-Tests", skip=NO_CI + ("docs", "data", "dotfiles"))
def ci001(ctx):
    return ok(f"{len(workflows(ctx))} workflows") if workflows(ctx) else bad("no CI workflows, so nothing checks a change before it lands")


@check("CI-002", "ci", "Default branch run health", "high", "report", "github", "The 90 percent line is an opinion", when=needs_workflows, opinion=True)
def ci002(ctx):
    data = ctx.api(f"repos/{ctx.slug}/actions/runs?branch={ctx.default_branch}&status=completed&per_page=30")
    done = [r["conclusion"] for r in data.get("workflow_runs", []) if r["conclusion"] not in ("skipped", "cancelled", "neutral")]
    if not done:
        raise Unknown("no finished runs on the default branch to measure")
    good = sum(c == "success" for c in done)
    return ok(f"{good} of {len(done)}") if good * 10 >= len(done) * 9 else bad(f"{good} of {len(done)} recent runs succeeded")


@check("CI-003", "ci", "No workflow disabled", "medium", "setting", "github", "GitHub disables schedules after 60 idle days", when=needs_workflows)
def ci003(ctx):
    rows = ctx.api(f"repos/{ctx.slug}/actions/workflows?per_page=100")["workflows"]
    off = [f"{w['name']}: {w['state']}" for w in rows if w["state"] != "active"]
    return bad(f"{len(off)} workflows are disabled", off) if off else ok()


@check("CI-004", "ci", "Workflows set least-privilege permissions", "high", "pr", "tree", "OpenSSF Scorecard Token-Permissions", when=needs_workflows)
def ci004(ctx):
    miss = []
    for f, text in workflows(ctx).items():
        if re.search(r"^permissions:", text, re.M):
            continue
        body = text.split("\njobs:", 1)[-1]
        jobs = re.split(r"(?m)^  (?=[\w-]+:\s*$)", body)[1:]
        if not jobs or not all(re.search(r"(?m)^ {4}permissions:", j) for j in jobs):
            miss.append(f)
    return bad(f"{len(miss)} workflows run with the default token scope", miss) if miss else ok()


@check("CI-005", "ci", "Default workflow token is read-only", "high", "setting", "admin", "OpenSSF Scorecard Token-Permissions goal")
def ci005(ctx):
    v = ctx.api(f"repos/{ctx.slug}/actions/permissions/workflow")
    return ok() if v.get("default_workflow_permissions") == "read" else bad("the default workflow token can write")


@check("CI-006", "ci", "Workflows cannot approve pull requests", "high", "setting", "admin", "GitHub Actions hardening guide")
def ci006(ctx):
    v = ctx.api(f"repos/{ctx.slug}/actions/permissions/workflow")
    return bad("workflows can approve pull requests") if v.get("can_approve_pull_request_reviews") else ok()


@check("CI-007", "ci", "No privileged trigger checks out pull request code", "critical", "pr", "tree", "OpenSSF Scorecard Dangerous-Workflow", when=needs_workflows)
def ci007(ctx):
    hits = [f for f, t in workflows(ctx).items()
            if re.search(r"\b(pull_request_target|workflow_run)\b", t) and "actions/checkout" in t and FORKED_REF.search(t)]
    return bad(f"{len(hits)} workflows run untrusted code with a privileged token", hits) if hits else ok()


@check("CI-008", "ci", "No untrusted context inside run steps", "critical", "pr", "tree", "GitHub script injection guidance", when=needs_workflows)
def ci008(ctx):
    hits = [f"{f}:{n}" for f, t in workflows(ctx).items() for n, line in run_lines(t) if UNTRUSTED.search(line)]
    return bad(f"{len(hits)} run lines expand untrusted input into a shell", hits) if hits else ok()


@check("CI-010", "ci", "No self-hosted runners on a public repository", "high", "pr", "tree", "GitHub Actions hardening guide", when=lambda c: needs_workflows(c) or private_skip(c))
def ci010(ctx):
    hits = [f for f, t in workflows(ctx).items() if re.search(r"runs-on:.*self-hosted", t)]
    return bad(f"{len(hits)} workflows use self-hosted runners", hits) if hits else ok()


@check("CI-011", "ci", "Redundant runs cancel", "info", "pr", "tree", "sp-repo-review GH102", when=needs_workflows, opinion=True)
def ci011(ctx):
    return ok() if any("cancel-in-progress" in t for t in workflows(ctx).values()) else note("no workflow cancels superseded runs")


@check("CI-014", "ci", "Workflows set timeouts", "low", "pr", "tree", "The GitHub default is 6 hours. Setting one is an opinion", when=needs_workflows, opinion=True)
def ci014(ctx):
    miss = [f for f, t in workflows(ctx).items() if "timeout-minutes" not in t]
    return note(f"{len(miss)} workflows rely on the 6 hour default", miss) if miss else ok()


# Supply chain

@check("SUP-001", "supply-chain", "Actions pinned to a full commit SHA", "high", "pr", "tree", "GitHub hardening guide, OpenSSF Scorecard Pinned-Dependencies", when=needs_workflows)
def sup001(ctx):
    loose = set()
    for t in workflows(ctx).values():
        for line in t.splitlines():
            m = USES.match(line)
            if not m:
                continue
            ref = m.group(1)
            if ref.startswith(("./", "docker://")) or "/.github/workflows/" in ref:
                continue
            if not re.search(r"@[0-9a-f]{40}$", ref):
                loose.add(ref)
    return bad(f"{len(loose)} actions float on a tag or branch", sorted(loose)) if loose else ok()


@check("SUP-004", "supply-chain", "SHA pins carry a version comment", "low", "pr", "tree", "Helps review. The target is an opinion", when=needs_workflows, opinion=True)
def sup004(ctx):
    miss = [m.group(1) for t in workflows(ctx).values() for m in (USES.match(x) for x in t.splitlines())
            if m and re.search(r"@[0-9a-f]{40}$", m.group(1)) and not m.group(2)]
    return bad(f"{len(miss)} SHA pins have no version comment", sorted(set(miss))) if miss else ok()


def update_tool(ctx: Ctx):
    names = (".github/dependabot.yml", ".github/dependabot.yaml", "renovate.json", "renovate.json5", ".renovaterc", ".renovaterc.json", ".github/renovate.json", ".github/renovate.json5")
    return next((n for n in names if n in ctx.tracked()), None)


def has_dep_manifest(ctx: Ctx) -> bool:
    return bool(workflows(ctx)) or bool({PurePosixPath(f).name for f in ctx.tracked()} & {"package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod", "Gemfile", "composer.json", "pom.xml", "build.gradle", "Dockerfile"})


@check("SUP-005", "supply-chain", "Update tool configured", "high", "auto", "tree", "OpenSSF Scorecard Dependency-Update-Tool", skip=NO_DEPS, when=lambda c: None if has_dep_manifest(c) else "no dependencies")
def sup005(ctx):
    found = update_tool(ctx)
    return ok(found) if found else bad("no Dependabot or Renovate config, so dependencies age silently")


@check("SUP-006", "supply-chain", "Update tool covers Actions", "medium", "pr", "tree", "sp-repo-review GH210", when=lambda c: needs_workflows(c) or (None if (update_tool(c) or "").find("dependabot") >= 0 else "not using Dependabot"))
def sup006(ctx):
    return ok() if "github-actions" in (ctx.read(update_tool(ctx)) or "") else bad("Dependabot does not watch workflow actions")


@check("SUP-007", "supply-chain", "Updates are grouped", "low", "pr", "tree", "sp-repo-review GH212. Dependabot stops at 5 open PRs", when=lambda c: None if (update_tool(c) or "").find("dependabot") >= 0 else "not using Dependabot", opinion=True)
def sup007(ctx):
    return ok() if "groups:" in (ctx.read(update_tool(ctx)) or "") else note("Dependabot opens one PR per dependency")


@check("SUP-008", "supply-chain", "Dependabot alerts are on", "high", "setting", "github", "GraphQL answers readers. The target is an opinion", skip=NO_DEPS, opinion=True)
def sup008(ctx):
    d = ctx.graphql("query($o:String!,$n:String!){repository(owner:$o,name:$n){hasVulnerabilityAlertsEnabled}}")
    return ok() if d["repository"]["hasVulnerabilityAlertsEnabled"] else bad("Dependabot alerts are off")


@check("SUP-010", "supply-chain", "No old high or critical dependency alerts", "high", "pr", "admin", "OpenSSF vulnerabilities_fixed_60_days")
def sup010(ctx):
    rows = ctx.api(f"repos/{ctx.slug}/dependabot/alerts?state=open&severity=critical,high&per_page=100")
    cut = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    old = [a["security_advisory"]["summary"][:70] for a in rows if a["created_at"] < cut]
    return bad(f"{len(old)} high or critical alerts are over 60 days old", old) if old else ok(f"{len(rows)} open, none past 60 days")


@check("SUP-011", "supply-chain", "Static analysis configured", "medium", "setting", "tree", "OpenSSF Scorecard SAST", skip=NO_DEPS + ("infra", "action"))
def sup011(ctx):
    if any("codeql" in t.lower() or "semgrep" in t.lower() or "bandit" in t.lower() or "gosec" in t.lower() for t in workflows(ctx).values()):
        return ok("workflow")
    d = ctx.api(f"repos/{ctx.slug}/code-scanning/default-setup")
    return ok("default setup") if d.get("state") == "configured" else bad("no code scanning configured")


# Governance

def community(ctx: Ctx):
    return ctx.api(f"repos/{ctx.slug}/community/profile")


def owner_default(ctx: Ctx, names: tuple) -> bool:
    """Health files inherited from the owner's .github repository do not appear in the tree."""
    owner = ctx.slug.split("/")[0]
    for n in names:
        if ctx.api(f"repos/{owner}/.github/contents/{n}", missing_ok=True):
            return True
    return False


def present(ctx: Ctx, names: tuple) -> bool:
    tracked = {t.lower() for t in ctx.tracked()}
    return any(n.lower() in tracked for n in names)


@check("GOV-001", "governance", "License detected", "high", "pr", "tree", "OpenSSF Scorecard License", skip=(), when=private_skip)
def gov001(ctx):
    lic = [f for f in ctx.tracked() if re.match(r"(LICEN[SC]E|COPYING|UNLICENSE)(\.|-|$)", f.rsplit("/", 1)[-1], re.I) and "/" not in f]
    if not lic:
        return bad("no license file, so nobody may legally reuse this code")
    if ctx.online and ctx.slug:
        try:
            spdx = (ctx.api(f"repos/{ctx.slug}/license", missing_ok=True) or {}).get("license", {}).get("spdx_id")
            if spdx == "NOASSERTION":
                return note("GitHub could not classify the license text. Read it")
        except Unknown:
            pass
    return ok(lic[0])


@check("GOV-002", "governance", "Security policy visible", "medium", "pr", "tree", "OpenSSF Scorecard Security-Policy", skip=("awesome-list", "profile", "dotfiles", "docs", "data"), when=private_skip)
def gov002(ctx):
    names = ("SECURITY.md", ".github/SECURITY.md", "docs/SECURITY.md")
    if present(ctx, names):
        return ok()
    if ctx.online and ctx.slug and owner_default(ctx, ("SECURITY.md",)):
        return ok("inherited from the owner's .github repository")
    return bad("no SECURITY.md, so a reporter has no private route")


@check("GOV-003", "governance", "Private vulnerability reporting is on", "medium", "setting", "github", "OpenSSF vulnerability_report_private", skip=("awesome-list", "profile", "dotfiles", "docs", "data"), when=private_skip)
def gov003(ctx):
    d = ctx.api(f"repos/{ctx.slug}/private-vulnerability-reporting")
    return ok() if d.get("enabled") else bad("private vulnerability reporting is off")


@check("GOV-004", "governance", "Code of conduct", "low", "pr", "tree", "CNCF CLOMonitor. Small repos may skip it", skip=("profile", "dotfiles", "awesome-list", "data"), when=lambda c: solo_skip(c) or private_skip(c), opinion=True)
def gov004(ctx):
    names = ("CODE_OF_CONDUCT.md", ".github/CODE_OF_CONDUCT.md", "docs/CODE_OF_CONDUCT.md")
    if present(ctx, names) or (ctx.online and ctx.slug and owner_default(ctx, ("CODE_OF_CONDUCT.md",))):
        return ok()
    return bad("multiple contributors and no code of conduct")


@check("GOV-005", "governance", "Contributing guide", "low", "pr", "tree", "CNCF CLOMonitor", skip=("profile", "dotfiles"), when=private_skip)
def gov005(ctx):
    names = ("CONTRIBUTING.md", ".github/CONTRIBUTING.md", "docs/CONTRIBUTING.md")
    if present(ctx, names) or (ctx.online and ctx.slug and owner_default(ctx, ("CONTRIBUTING.md",))):
        return ok()
    return bad("no CONTRIBUTING.md, so a would-be contributor has to guess")


@check("GOV-006", "governance", "CODEOWNERS parses", "medium", "pr", "github", "GitHub codeowners errors API")
def gov006(ctx):
    d = ctx.api(f"repos/{ctx.slug}/codeowners/errors", missing_ok=True)
    if d is None:
        raise NotApplicable("no CODEOWNERS file")
    errs = d.get("errors") or []
    return bad(f"{len(errs)} CODEOWNERS errors", [e.get("message", "")[:80] for e in errs]) if errs else ok()


@check("GOV-010", "governance", "Merged pull requests had review", "high", "report", "github", "OpenSSF Scorecard Code-Review", when=solo_skip)
def gov010(ctx):
    d = ctx.graphql("query($o:String!,$n:String!){repository(owner:$o,name:$n){pullRequests(states:MERGED,last:30){nodes{reviewDecision author{__typename}}}}}")
    rows = [p for p in d["repository"]["pullRequests"]["nodes"] if (p.get("author") or {}).get("__typename") != "Bot"]
    if not rows:
        raise NotApplicable("no merged human pull requests")
    reviewed = sum(p["reviewDecision"] == "APPROVED" for p in rows)
    return note(f"{reviewed} of the latest {len(rows)} human PRs were approved")


@check("GOV-013", "governance", "Dormant repository is archived", "low", "setting", "github", "Archiving is reversible and read-only. The 2 year line is an opinion", opinion=True)
def gov013(ctx):
    m = ctx.meta()
    age = datetime.now(timezone.utc) - datetime.fromisoformat(m["pushed_at"].replace("Z", "+00:00"))
    if age.days > 730 and not m.get("archived"):
        return note(f"no push for {age.days} days and not archived")
    return ok()


@check("GOV-014", "governance", "Moderation reporting is on", "info", "setting", "github", "Separate from file presence. It decides 87 versus 100 on the community profile", when=lambda c: None if c.slug and c.meta().get("owner", {}).get("type") == "Organization" else "organization repositories only", opinion=True)
def gov014(ctx):
    return ok() if community(ctx).get("content_reports_enabled") else note("content reports are off")


# Metadata

@check("MET-001", "metadata", "Description present", "medium", "setting", "github", "Shown in search and link previews. The target is an opinion", opinion=True)
def met001(ctx):
    d = ctx.meta().get("description") or ""
    return ok() if d.strip() else bad("no description, so search results and link previews are blank")


@check("MET-002", "metadata", "Homepage set when a site exists", "info", "setting", "github", "Reported for the owner", opinion=True)
def met002(ctx):
    m = ctx.meta()
    if m.get("homepage"):
        return ok(m["homepage"])
    readme = ctx.read("README.md") or ""
    site = re.search(r"https://[\w.-]+\.(?:dev|app|io|xyz|com|org|ai)\b", readme)
    return note("no homepage set") if site and "github" not in site.group(0) else ok()


@check("MET-003", "metadata", "Topics set", "medium", "setting", "github", "GitHub allows 1 to 20. The minimum is an opinion", when=private_skip, opinion=True)
def met003(ctx):
    n = ctx.meta().get("topics") or []
    return ok(f"{len(n)} topics") if 1 <= len(n) <= 20 else bad("no topics, so GitHub topic pages and search cannot find this repository")


@check("MET-004", "metadata", "Custom social preview", "medium", "setting", "github", "1280 by 640, under 1 MB. Having one is an opinion", skip=("dotfiles", "profile"), when=private_skip, opinion=True)
def met004(ctx):
    d = ctx.graphql("query($o:String!,$n:String!){repository(owner:$o,name:$n){usesCustomOpenGraphImage}}")
    return ok() if d["repository"]["usesCustomOpenGraphImage"] else bad("links to this repository unfurl with a generated card")


@check("MET-005", "metadata", "Unused features turned off", "low", "setting", "github", "Empty tabs read as abandoned. The target is an opinion", opinion=True)
def met005(ctx):
    m = ctx.meta()
    idle = []
    if m.get("has_wiki"):
        idle.append("wiki")
    if m.get("has_projects"):
        d = ctx.graphql("query($o:String!,$n:String!){repository(owner:$o,name:$n){projectsV2{totalCount}}}")
        if not d["repository"]["projectsV2"]["totalCount"]:
            idle.append("projects")
    return note("enabled, possibly empty: " + ", ".join(idle)) if idle else ok()


@check("MET-008", "metadata", "Citation file on research software", "medium", "pr", "tree", "GitHub CITATION.cff support", when=lambda c: None if c.kind in ("research", "ml") else "not research software")
def met008(ctx):
    return ok() if "CITATION.cff" in ctx.tracked() else bad("no CITATION.cff, so GitHub shows no citation button")


# Docs

@check("DOC-001", "docs", "README exists with substance", "high", "pr", "tree", "CNCF CLOMonitor. The 500 byte line is an opinion", opinion=True)
def doc001(ctx):
    names = [f for f in ctx.tracked() if re.fullmatch(r"(\.github/|docs/)?readme(\.\w+)?", f, re.I)]
    if not names:
        return bad("no README")
    size = len(ctx.read(names[0]) or "")
    return ok() if size > 500 else bad(f"README is {size} bytes")


@check("DOC-003", "docs", "Changelog or release notes", "medium", "pr", "tree", "Keep a Changelog, OpenSSF release_notes", skip=NO_RELEASES)
def doc003(ctx):
    if {f.lower() for f in ctx.tracked()} & {"changelog.md", "changes.md", "history.md", "news.md", "changelog.rst", "changelog"}:
        return ok()
    if ctx.online and ctx.slug and ctx.api(f"repos/{ctx.slug}/releases?per_page=1", missing_ok=True):
        return ok("GitHub releases")
    return bad("no changelog and no releases, so users cannot see what changed")


def issue_forms(ctx: Ctx) -> list[str]:
    return [f for f in ctx.tracked() if re.match(r"\.github/ISSUE_TEMPLATE/.+\.(ya?ml|md)$", f) and not f.endswith("config.yml")] + \
        [f for f in ctx.tracked() if f.lower() in (".github/issue_template.md", "issue_template.md")]


@check("DOC-004", "docs", "Issue templates", "low", "pr", "tree", "Read the tree. The community profile API misses issue forms", skip=("profile", "dotfiles", "data"), when=lambda c: "one active committer" if c.solo() and c.kind not in ("library", "cli", "framework", "sdk", "action", "plugin", "webapp", "desktop") else None)
def doc004(ctx):
    if issue_forms(ctx):
        return ok()
    if ctx.online and ctx.slug:
        owner = ctx.slug.split("/")[0]
        if ctx.api(f"repos/{owner}/.github/contents/.github/ISSUE_TEMPLATE", missing_ok=True):
            return ok("inherited from the owner's .github repository")
    return bad("no issue forms, so reports arrive without the facts a maintainer needs")


@check("DOC-005", "docs", "Pull request template", "low", "pr", "tree", "GitHub template locations", skip=("profile", "dotfiles", "data"))
def doc005(ctx):
    tracked = {f.lower() for f in ctx.tracked()}
    if tracked & {".github/pull_request_template.md", "pull_request_template.md", "docs/pull_request_template.md"} or any(f.startswith(".github/pull_request_template/") for f in tracked):
        return ok()
    if ctx.online and ctx.slug:
        owner = ctx.slug.split("/")[0]
        if ctx.api(f"repos/{owner}/.github/contents/.github/PULL_REQUEST_TEMPLATE.md", missing_ok=True):
            return ok("inherited from the owner's .github repository")
    return bad("no pull request template")


@check("DOC-007", "docs", "Community profile score", "info", "report", "github", "Reported only. It tracks a moderation setting and ignores issue forms", opinion=True)
def doc007(ctx):
    return note(f"health_percentage {community(ctx).get('health_percentage')}. Never used as a gate")
