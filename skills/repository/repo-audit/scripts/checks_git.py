"""Checks that need only git and the working tree. These run offline."""

from __future__ import annotations

import re
import time
from collections import Counter

from engine import Ctx, NotApplicable, Unknown, bad, check, is_fixture, note, ok

MiB = 1024 * 1024
ASSET_HEAVY = ("data", "game", "ml")
NO_CODE = ("docs", "awesome-list", "profile", "dotfiles", "data")
KEY_SHAPES = re.compile(
    r"AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}|glpat-[A-Za-z0-9_-]{20}"
    r"|xox[baprs]-[A-Za-z0-9-]{10,}|sk_live_[A-Za-z0-9]{16,}|rk_live_[A-Za-z0-9]{16,}|AIza[0-9A-Za-z_-]{35}"
    r"|npm_[A-Za-z0-9]{36}|pypi-[A-Za-z0-9_-]{50,}|sk-ant-[A-Za-z0-9_-]{20,}|sk-proj-[A-Za-z0-9_-]{20,}"
    r"|-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY"
)
PICKAXE = (r"(AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}|xox[baprs]-[A-Za-z0-9-]{10,}"
           r"|sk_live_[A-Za-z0-9]{16,}|sk-ant-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY)")
PLACEHOLDER = re.compile(r"example|sample|fake|dummy|redacted|your_|xxxx|AKIAIOSFODNN7EXAMPLE", re.I)


def match_tracked(ctx: Ctx, pattern: str, exempt=None) -> list[str]:
    rx = re.compile(pattern, re.I)
    return [f for f in ctx.tracked() if rx.search(f) and not (exempt and exempt(f))]


def blobs(ctx: Ctx) -> list[tuple[int, str]]:
    """Every reachable blob as (size, path), largest first."""
    def make():
        _, listing = ctx.reader.git("rev-list", "--objects", "--all", check_rc=True)
        paths = {}
        for line in listing.splitlines():
            sha, _, path = line.partition(" ")
            if path:
                paths.setdefault(sha, path)
        # batch-all reads the object store once, which is faster than feeding every sha.
        _, out = ctx.reader.git("cat-file", "--batch-check=%(objecttype) %(objectsize) %(objectname)",
                                "--batch-all-objects", check_rc=True)
        rows = []
        for line in out.splitlines():
            parts = line.split()
            if len(parts) == 3 and parts[0] == "blob" and parts[2] in paths:
                rows.append((int(parts[1]), paths[parts[2]]))
        return sorted(rows, reverse=True)
    return ctx.memo("blobs", make)


@check("HIS-002", "history", "No blob over 50 MiB anywhere in history", "high", "rewrite", "history", "GitHub large files docs: warns at 50 MiB, blocks at 100 MiB", skip=ASSET_HEAVY)
def his002(ctx):
    big = [(s, p) for s, p in blobs(ctx) if s >= 50 * MiB]
    return bad(f"{len(big)} blobs at or over 50 MiB", [f"{s // MiB} MiB {p}" for s, p in big]) if big else ok()


@check("HIS-018", "history", "History is not bloated by deleted large files", "medium", "rewrite", "history", "git-sizer guidance on large blobs. The 5 MiB line is an opinion", skip=ASSET_HEAVY, opinion=True)
def his018(ctx):
    current = set(ctx.tracked())
    gone = [(s, p) for s, p in blobs(ctx) if s >= 5 * MiB and p not in current]
    if gone:
        total = sum(s for s, _ in gone)
        return bad(f"{len(gone)} blobs of 5 MiB or more exist only in history, {total // MiB} MiB in all",
                   [f"{s // MiB} MiB {p}" for s, p in gone[:10]])
    return ok()


@check("HIS-003", "history", "No large files at HEAD", "low", "pr", "tree", "GitHub says a few MB is fine. The 1 MiB line is an opinion", skip=ASSET_HEAVY, opinion=True)
def his003(ctx):
    big = []
    for f in ctx.tracked():
        try:
            p = ctx.path / f
            size = p.stat().st_size if p.is_file() and not p.is_symlink() else 0
        except OSError:
            continue
        if size >= MiB and not is_fixture(f):
            big.append((size, f))
    big.sort(reverse=True)
    return bad(f"{len(big)} files of 1 MiB or more at HEAD", [f"{s / MiB:.1f} MiB {f}" for s, f in big]) if big else ok()


@check("HIS-004", "history", "Object database is connected", "critical", "report", "tree", "git fsck")
def his004(ctx):
    rc, _ = ctx.reader.git("fsck", "--connectivity-only", "--no-dangling", "--no-progress")
    if rc == 0:
        return ok()
    errors = [line.strip() for line in ctx.reader.last_stderr.splitlines() if line.strip()]
    if errors and all(re.match(r"error: refs/remotes/\S+: invalid sha1 pointer", e) for e in errors):
        return note("this local clone holds a broken remote-tracking ref. The repository itself is fine. Run git remote set-head origin --auto", errors)
    return bad(f"git fsck exited {rc}, so objects are missing or damaged", errors)


@check("HIS-005", "history", "Reference count is manageable", "low", "report", "tree", "git-sizer: a few tens of thousands at most", opinion=True)
def his005(ctx):
    _, out = ctx.reader.git("for-each-ref", "--format=%(refname)")
    n = len(out.splitlines())
    return bad(f"{n} references") if n > 10000 else ok(f"{n} references")


@check("HIS-007", "history", "No compiled binaries tracked", "high", "pr", "tree", "OpenSSF Scorecard Binary-Artifacts")
def his007(ctx):
    hits = match_tracked(ctx, r"\.(exe|dll|so|dylib|jar|war|class|pyc|pyo|o|a|obj|lib|whl)$", is_fixture)
    return bad(f"{len(hits)} compiled binaries tracked", hits) if hits else ok()


@check("HIS-008", "history", "No archives tracked", "low", "pr", "tree", "GitHub advises against archives in git. The zero target is an opinion", skip=("data",), opinion=True)
def his008(ctx):
    hits = match_tracked(ctx, r"\.(zip|tar|tgz|gz|7z|rar|bz2|xz)$", is_fixture)
    return bad(f"{len(hits)} archives tracked", hits) if hits else ok()


@check("HIS-009", "history", "Personal emails in commits", "info", "report", "history", "Reported for the owner to judge", opinion=True)
def his009(ctx):
    _, out = ctx.reader.git("log", "--all", "--format=%ae")
    mail = {e.lower() for e in out.split()}
    personal = [e for e in mail if "noreply" not in e and "[bot]" not in e]
    return note(f"{len(personal)} addresses without noreply. Addresses are withheld from this report")


@check("HIS-010", "history", "One person, one identity", "low", "pr", "history", "gitmailmap documents the fix", opinion=True)
def his010(ctx):
    if ".mailmap" in ctx.tracked():
        _, out = ctx.reader.git("log", "--all", "--use-mailmap", "--format=%aN%x09%aE")
    else:
        _, out = ctx.reader.git("log", "--all", "--format=%aN%x09%aE")
    by_mail = {}
    for line in set(out.splitlines()):
        name, _, mail = line.partition("\t")
        by_mail.setdefault(mail.lower(), set()).add(name)
    names = [sorted(v) for v in by_mail.values() if len(v) > 1 and "[bot]" not in " ".join(v)]
    if names:
        return bad(f"{len(names)} addresses appear under several names, so a .mailmap would merge them", ["; ".join(n)[:80] for n in names])
    return ok()


@check("HIS-012", "history", "Commit subjects match the declared convention", "low", "pr", "history", "Conventional Commits, only where the repository declares it", opinion=True)
def his012(ctx):
    tracked = set(ctx.tracked())
    declared = ctx.policy.get("commit_convention") == "conventional" or bool(
        tracked & {"commitlint.config.js", "commitlint.config.ts", ".commitlintrc", ".commitlintrc.json", ".commitlintrc.yml", "release-please-config.json", ".releaserc", ".releaserc.json"})
    if not declared:
        raise NotApplicable("no commit convention declared")
    _, out = ctx.reader.git("log", "-100", "--no-merges", "--format=%s")
    rx = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?: ")
    miss = [s for s in out.splitlines() if not rx.match(s)]
    return bad(f"{len(miss)} of the latest 100 subjects miss the convention", miss) if miss else ok()


@check("HIS-013", "history", "No fixup commits on the default branch", "low", "report", "history", "No source sets this", opinion=True)
def his013(ctx):
    _, out = ctx.reader.git("log", "-200", "--format=%s")
    hits = [s for s in out.splitlines() if re.match(r"(fixup|squash|amend)! ", s)]
    return bad(f"{len(hits)} fixup commits reached the default branch", hits) if hits else ok()


@check("HIS-019", "history", "Recent commit subjects carry meaning", "low", "report", "history", "No source sets the 20 percent line", opinion=True)
def his019(ctx):
    _, out = ctx.reader.git("log", "-100", "--no-merges", "--format=%s")
    subjects = out.splitlines()
    vague = re.compile(r"^(wip|fix|fixes|fixed|update|updates|updated|changes|misc|stuff|test|tmp|temp|asdf|\.+|commit|minor|cleanup)\.?$", re.I)
    hits = [s for s in subjects if vague.match(s.strip())]
    if subjects and len(hits) * 5 > len(subjects):
        return bad(f"{len(hits)} of the latest {len(subjects)} subjects say nothing", hits)
    return ok()


@check("HIS-014", "history", "No paths that collide on case-insensitive filesystems", "medium", "pr", "tree", "Windows and macOS default filesystem behavior", opinion=True)
def his014(ctx):
    seen = Counter(f.lower() for f in ctx.tracked())
    hits = [f for f, n in seen.items() if n > 1]
    return bad(f"{len(hits)} paths differ only by case", hits) if hits else ok()


@check("HIS-015", "history", "No very long paths", "low", "pr", "tree", "git-sizer: one or two hundred characters should be enough")
def his015(ctx):
    hits = [f for f in ctx.tracked() if len(f) > 200]
    return bad(f"{len(hits)} paths over 200 characters", hits) if hits else ok()


@check("HIS-016", "history", "No Windows reserved file names", "medium", "pr", "tree", "Windows naming rules", opinion=True)
def his016(ctx):
    hits = match_tracked(ctx, r"(^|/)(con|prn|aux|nul|com[1-9]|lpt[1-9])(\.|/|$)")
    return bad(f"{len(hits)} reserved names break checkouts on Windows", hits) if hits else ok()


@check("HIS-017", "history", "Symlinks tracked at HEAD", "info", "report", "tree", "Symlinks need extra setup on Windows", opinion=True)
def his017(ctx):
    _, out = ctx.reader.git("ls-files", "-s")
    n = sum(line.startswith("120000 ") for line in out.splitlines())
    return note(f"{n} symlinks")


@check("HIS-020", "history", "No tracked file with broken Git LFS state", "medium", "pr", "tree", "Git LFS pointer format")
def his020(ctx):
    attrs = ctx.read(".gitattributes") or ""
    if "filter=lfs" not in attrs:
        raise NotApplicable("repository does not use Git LFS")
    _, out = ctx.reader.git("ls-files", "-z", ":(attr:filter=lfs)")
    bad_paths = []
    for p in [x for x in out.split("\0") if x][:500]:
        rc, head = ctx.reader.git("cat-file", "blob", ":" + p)
        if rc == 0 and not head.startswith("version https://git-lfs.github.com/spec/v1"):
            bad_paths.append(p)
    return bad(f"{len(bad_paths)} LFS paths hold real content, not pointers", bad_paths) if bad_paths else ok()


@check("BRN-008", "branches", "Branches idle past three months", "low", "report", "tree", "GitHub calls a branch stale after three months", opinion=True)
def brn008(ctx):
    _, out = ctx.reader.git("for-each-ref", "--format=%(committerdate:unix) %(refname:short)", "refs/heads", "refs/remotes/origin")
    cutoff = time.time() - 90 * 86400
    keep = re.compile(r"(^|/)(HEAD|main|master|prod|dev|develop|release.*)$")
    hits = [line.split(" ", 1)[1] for line in out.splitlines() if " " in line and int(line.split(" ", 1)[0]) < cutoff and not keep.search(line)]
    return note(f"{len(hits)} branches idle for over 90 days. Age alone never justifies deletion", hits)


@check("BRN-014", "branches", "Local default branch name matches the owner's policy", "low", "setting", "tree", "Owner policy parameter", opinion=True)
def brn014(ctx):
    want = ctx.policy.get("default_branch")
    if not want:
        raise NotApplicable("no default branch policy set")
    have = ctx.default_branch
    return ok() if have == want else bad(f"default branch is {have}, policy says {want}")


@check("TAG-006", "tags", "Tags carry signatures", "low", "report", "tree", "OpenSSF Best Practices version_tags_signed")
def tag006(ctx):
    _, out = ctx.reader.git("for-each-ref", "refs/tags", "--format=%(objecttype) %(contents:signature)")
    rows = [line for line in out.splitlines() if line.startswith(("tag", "commit"))]
    if not rows:
        raise NotApplicable("no tags")
    signed = sum("BEGIN" in line for line in out.split("\n"))
    return note(f"{signed} of {len(rows)} tags signed")


@check("TAG-001", "tags", "Release tags are annotated", "low", "report", "tree", "Annotated tags carry author and date", opinion=True)
def tag001(ctx):
    _, out = ctx.reader.git("for-each-ref", "refs/tags", "--format=%(objecttype) %(refname:short)")
    rows = [line.split(" ", 1) for line in out.splitlines() if " " in line]
    if not rows:
        raise NotApplicable("no tags")
    light = [n for t, n in rows if t == "commit"]
    return note(f"{len(light)} of {len(rows)} tags are lightweight", light)


@check("TAG-002", "tags", "Tags follow a version format", "low", "report", "tree", "OpenSSF Best Practices version_tags")
def tag002(ctx):
    _, out = ctx.reader.git("for-each-ref", "refs/tags", "--format=%(refname:short)")
    tags = out.split()
    if not tags:
        raise NotApplicable("no tags")
    odd = [t for t in tags if not re.search(r"(^|[-/@])v?\d+\.\d+", t)]
    return note(f"{len(odd)} of {len(tags)} tags are not versions", odd)


@check("IGN-001", "ignore", ".gitignore exists", "low", "auto", "tree", "github/gitignore templates", skip=("awesome-list", "profile"))
def ign001(ctx):
    return ok() if ".gitignore" in ctx.tracked() else bad("no .gitignore at the root")


@check("IGN-002", "ignore", "No tracked file matches an ignore rule", "low", "pr", "tree", "git check-ignore semantics", opinion=True)
def ign002(ctx):
    _, out = ctx.reader.git("ls-files", "-ci", "--exclude-standard")
    hits = [f for f in out.splitlines() if not is_fixture(f)]
    return bad(f"{len(hits)} tracked files match ignore rules", hits) if hits else ok()


@check("IGN-003", "ignore", "No operating system or editor junk", "low", "pr", "tree", "github/gitignore templates", opinion=True)
def ign003(ctx):
    hits = match_tracked(ctx, r"(^|/)(\.DS_Store|Thumbs\.db|desktop\.ini|\.idea/|.*\.swp$|.*\.swo$|.*~$|.*\.log$|\.vs/|.*\.bak$|.*\.orig$|.*\.rej$|npm-debug\.log)", is_fixture)
    return bad(f"{len(hits)} junk files tracked", hits) if hits else ok()


@check("IGN-004", "ignore", "No dependencies or build output tracked", "medium", "pr", "tree", "GitHub and git-sizer advise against this")
def ign004(ctx):
    hits = match_tracked(ctx, r"(^|/)(node_modules|__pycache__|\.venv|venv|\.next|\.nuxt|coverage|\.pytest_cache|\.mypy_cache|\.gradle|\.terraform|\.tox)/", is_fixture)
    if ctx.kind != "action" and not any(f.startswith("vendor/modules.txt") for f in ctx.tracked()):
        hits += match_tracked(ctx, r"^(dist|build|out|target)/.+\.(js|map|css|class|o|exe)$", is_fixture)
    return bad(f"{len(hits)} dependency or build files tracked", hits) if hits else ok()


@check("IGN-005", "ignore", ".gitattributes sets a line ending policy", "low", "pr", "tree", "GitHub: text=auto is a good default", skip=("profile", "awesome-list"))
def ign005(ctx):
    text = ctx.read(".gitattributes")
    if text is None:
        return bad("no .gitattributes, so line endings depend on each contributor's machine")
    return ok() if re.search(r"text=auto|\beol=|\btext\b", text) else bad(".gitattributes sets no line ending rule")


@check("IGN-006", "ignore", "No mixed line endings in the index", "low", "pr", "tree", "git add --renormalize", opinion=True)
def ign006(ctx):
    _, out = ctx.reader.git("ls-files", "--eol")
    hits = [line.split("\t")[-1] for line in out.splitlines() if line.startswith("i/mixed") and not is_fixture(line.split("\t")[-1])]
    return bad(f"{len(hits)} files mix line endings", hits) if hits else ok()


@check("IGN-009", "ignore", ".editorconfig present", "info", "pr", "tree", "EditorConfig. Having one is an opinion", skip=NO_CODE, opinion=True)
def ign009(ctx):
    text = ctx.read(".editorconfig")
    has_formatter = set(ctx.tracked()) & {".prettierrc", ".prettierrc.json", "biome.json", "rustfmt.toml", ".clang-format", "ruff.toml"}
    if text is None and not has_formatter:
        return note("no .editorconfig and no formatter config found")
    return ok()


@check("SEC-005", "secrets", "No known key shapes in history", "critical", "rewrite", "history", "Pattern floor under gitleaks. Reports commit and path, never the value")
def sec005(ctx):
    _, out = ctx.reader.git("log", "--all", "--format=%h", "--name-only", "--no-textconv", "--no-ext-diff", "-G" + PICKAXE)
    commit, hits = None, []
    for line in out.splitlines():
        if re.fullmatch(r"[0-9a-f]{7,40}", line.strip()):
            commit = line.strip()
        elif line.strip() and not is_fixture(line):
            hits.append(f"{commit} {line.strip()}")
    return bad(f"{len(hits)} commit and path pairs match a key shape. Rotate first, then rewrite", hits) if hits else ok()


@check("SEC-012", "secrets", "No known key shapes at HEAD", "critical", "rewrite", "tree", "Pattern floor. Reports path and line, never the value")
def sec012(ctx):
    hits = []
    for f in ctx.tracked():
        if is_fixture(f) or f.lower().endswith((".lock", ".png", ".jpg", ".gif", ".pdf", ".zip", ".woff2")):
            continue
        text = ctx.read(f)
        if text is None or len(text) > 2 * MiB:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            m = KEY_SHAPES.search(line)
            if m and not PLACEHOLDER.search(line):
                hits.append(f"{f}:{n}")
                break
    return bad(f"{len(hits)} files hold a live-looking key shape. Treat each as exposed", hits) if hits else ok()


@check("SEC-008", "secrets", "No key material tracked", "critical", "rewrite", "tree", "OpenSSF Best Practices no_leaked_credentials")
def sec008(ctx):
    hits = match_tracked(ctx, r"(\.(pem|p12|pfx|key|keystore|jks|ppk)$|(^|/)id_(rsa|dsa|ecdsa|ed25519)$|(^|/)\.?credentials(\.json)?$|(^|/)\.netrc$|(^|/)\.npmrc$|(^|/)\.pypirc$)", is_fixture)
    return bad(f"{len(hits)} key or credential files tracked", hits) if hits else ok()


@check("SEC-009", "secrets", "No environment files tracked", "high", "rewrite", "tree", "Env files often hold real values")
def sec009(ctx):
    hits = [f for f in match_tracked(ctx, r"(^|/)\.env(\.[^/]+)?$", is_fixture) if not re.search(r"example|sample|schema|template|defaults?$", f, re.I)]
    return bad(f"{len(hits)} environment files tracked", hits) if hits else ok()


@check("SEC-013", "secrets", "Secrets scanner history pass", "high", "report", "tree", "gitleaks. Optional tool")
def sec013(ctx):
    raise Unknown("not run by this tool. Run gitleaks or trufflehog if you need a full scan, then record the result")


def tests_present(ctx):
    return match_tracked(ctx, r"(^|/)(tests?|specs?|__tests__)/|(_test\.|\.test\.|\.spec\.)|(^|/)test_[^/]+\.py$")


@check("CI-012", "ci", "Tests exist in the tree", "medium", "report", "tree", "repolinter test-directory-exists, sp-repo-review PY005", skip=NO_CODE + ("template", "infra"))
def ci012(ctx):
    return ok() if tests_present(ctx) else bad("no test files found")


@check("SUP-013", "supply-chain", "Lockfile committed where the type needs one", "medium", "pr", "tree", "Pinned installs for applications", skip=NO_CODE + ("action", "infra", "research"), opinion=True)
def sup013(ctx):
    files = set(ctx.tracked())
    has_manifest = {"package.json", "pyproject.toml", "Cargo.toml", "Gemfile", "composer.json", "go.mod"} & files
    if not has_manifest:
        raise NotApplicable("no package manifest at the root")
    if ctx.kind == "library" and ctx.policy.get("lockfile") != "required":
        raise NotApplicable("libraries may choose not to commit a lockfile")
    locks = {"pnpm-lock.yaml", "package-lock.json", "yarn.lock", "bun.lockb", "bun.lock", "poetry.lock", "uv.lock", "Cargo.lock", "go.sum", "Gemfile.lock", "composer.lock", "pdm.lock"}
    return ok() if locks & files else bad(f"{sorted(has_manifest)[0]} has no lockfile")


@check("SUP-014", "supply-chain", "Submodules match their declarations", "medium", "pr", "tree", "git submodule model")
def sup014(ctx):
    _, out = ctx.reader.git("ls-files", "-s")
    links = {line.split("\t")[-1] for line in out.splitlines() if line.startswith("160000 ")}
    text = ctx.read(".gitmodules") or ""
    declared = set(re.findall(r"^\s*path\s*=\s*(.+?)\s*$", text, re.M))
    if not links and not declared:
        raise NotApplicable("no submodules")
    diff = links ^ declared
    insecure = [u for u in re.findall(r"^\s*url\s*=\s*(.+?)\s*$", text, re.M) if not u.startswith(("https://", "../", "./"))]
    if diff or insecure:
        return bad("gitlinks and .gitmodules disagree or a URL is not https", sorted(diff) + insecure)
    return ok()


@check("GOV-007", "governance", "CODEOWNERS covers itself", "medium", "pr", "tree", "GitHub recommends owning the file")
def gov007(ctx):
    text = next((t for t in (ctx.read(p) for p in ("CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS")) if t), None)
    if text is None:
        raise NotApplicable("no CODEOWNERS file")
    return ok() if re.search(r"^(\*\s|.*CODEOWNERS)", text, re.M) else bad("no rule covers the CODEOWNERS file")


@check("GOV-008", "governance", "Authorship concentration", "info", "report", "history", "OpenSSF bus_factor is a SHOULD", opinion=True)
def gov008(ctx):
    _, out = ctx.reader.git("log", "--since=1.year", "--no-merges", "--format=%aN")
    who = Counter(n for n in out.splitlines() if "[bot]" not in n)
    if not who:
        return note("no human commits in the last year")
    top = who.most_common(1)[0][1]
    return note(f"top author wrote {top * 100 // sum(who.values())} percent of {sum(who.values())} commits across {len(who)} people")


@check("GOV-009", "governance", "Recent activity", "info", "report", "history", "OpenSSF Scorecard Maintained. Low scores need no fix", opinion=True)
def gov009(ctx):
    _, out = ctx.reader.git("rev-list", "--count", "--since=90.days", "HEAD")
    return note(f"{out.strip()} commits in the last 90 days")


@check("MET-006", "metadata", "Language stats reflect the code", "info", "pr", "tree", "linguist attributes. Reported for the owner to judge", opinion=True)
def met006(ctx):
    generated = match_tracked(ctx, r"(^|/)(vendor|third_party|dist|generated)/.+\.(js|css|py|go|c|h)$", is_fixture)
    attrs = ctx.read(".gitattributes") or ""
    if len(generated) > 20 and "linguist-" not in attrs:
        return note(f"{len(generated)} vendored or generated files may skew language stats. Mark them linguist-vendored")
    return ok()


@check("DOC-002", "docs", "README names the license", "low", "pr", "tree", "repolinter readme-references-license", skip=("awesome-list", "profile"))
def doc002(ctx):
    text = ctx.read("README.md") or ctx.read("README") or ctx.read("readme.md") or ""
    return ok() if re.search(r"licen[sc]e", text, re.I) else bad("the README does not mention the license")
