"""README and presentation checks. Defects, conventions and preferences stay separate on purpose."""

from __future__ import annotations

import ipaddress
import re
import socket
import struct
import urllib.error
import urllib.parse
import urllib.request
import zlib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional

from engine import Ctx, NotApplicable, Unknown, bad, check, note, ok

KiB, MiB = 1024, 1024 * 1024
BADGE = re.compile(r"img\.shields\.io|badge\.fury\.io|badgen\.net|/badge\.svg|/badges?/|codecov\.io/.*/graph/badge|api\.netlify\.com/.*badge|snyk\.io/.*badge|coveralls\.io/repos", re.I)
VISUAL_TYPES = {"desktop", "mobile", "game", "webapp", "design-system"}
PRESET_FOR = {
    "library": "standard", "cli": "reference", "webapp": "pitch", "framework": "router", "sdk": "reference", "ml": "paper",
    "research": "paper", "monorepo": "router", "infra": "generated", "mobile": "showcase", "desktop": "showcase",
    "game": "showcase", "action": "reference", "plugin": "reference", "design-system": "router", "docs": "router",
    "dotfiles": "standard", "awesome-list": "standard", "profile": "own choice", "template": "standard",
}
PROCESS_NOTE = re.compile(r"\b(untested|not (?:been )?tested|image from|captured (?:on|20\d\d)|screenshot (?:taken|from)|as of 20\d\d|last verified|verified on|receipt|work in progress note|todo:|fixme)\b|\b20\d\d-\d\d-\d\d\b", re.I)
HOME_PATH = re.compile(r"(?:[A-Za-z]:[\\/]Users[\\/]|/Users/|/home/)(?!user\b|username\b|you\b|your|me\b|name\b|runner\b|example|<|\{|\$|\*)([\w.-]+)")
NUMBER_CLAIM = re.compile(r"\b(trusted by|used by|loved by|thousands of|millions of|\d[\d,.]*\s*(?:k|m|\+)?\s*(?:x faster|times faster|users|customers|companies|developers|downloads|installs))\b", re.I)


@dataclass(frozen=True)
class Image:
    src: str
    alt: Optional[str]
    line: int
    in_picture: bool
    badge: bool


def readme_path(ctx: Ctx) -> str:
    def make():
        for f in ctx.tracked():
            if re.fullmatch(r"(\.github/)?readme(\.(md|markdown|mdx))?", f, re.I):
                return f
        for f in ctx.tracked():
            if re.fullmatch(r"readme\.(rst|txt|adoc|org)", f, re.I):
                raise NotApplicable("README is not Markdown")
        raise NotApplicable("no README to inspect")
    return ctx.memo("readme_path", make)


def plain(text: str) -> str:
    """Blank out fenced code and comments, keeping line numbers."""
    blank = lambda m: re.sub(r"[^\n]", " ", m.group(0))
    text = re.sub(r"^( {0,3})(`{3,}|~{3,})[^\n]*\n.*?^ {0,3}\2[`~]*\s*$", blank, text, flags=re.M | re.S)
    return re.sub(r"<!--.*?-->", blank, text, flags=re.S)


def readme(ctx: Ctx) -> str:
    text = ctx.read(readme_path(ctx))
    if text is None:
        raise Unknown("README could not be read")
    return text


def images(text: str) -> list[Image]:
    body = plain(text)
    refs = dict(re.findall(r"^ {0,3}\[([^\]]+)\]:\s*<?([^\s>]+)", body, re.M))
    spans = [(m.start(), m.end()) for m in re.finditer(r"<picture\b.*?</picture>", body, re.I | re.S)]
    found = []

    def add(src, alt, at):
        line = body.count("\n", 0, at) + 1
        found.append(Image(src, alt, line, any(a <= at < b for a, b in spans), bool(BADGE.search(src))))

    for m in re.finditer(r"!\[([^\]]*)\]\(\s*<?([^)\s>]+)", body):
        add(m.group(2), m.group(1), m.start())
    for m in re.finditer(r"!\[([^\]]*)\]\[([^\]]*)\]", body):
        target = refs.get(m.group(2) or m.group(1))
        if target:
            add(target, m.group(1), m.start())
    for m in re.finditer(r"<img\b[^>]*>", body, re.I):
        tag = m.group(0)
        src = re.search(r"\bsrc\s*=\s*[\"']([^\"']+)", tag, re.I)
        alt = re.search(r"\balt\s*=\s*[\"']([^\"']*)", tag, re.I)
        if src:
            add(src.group(1), alt.group(1) if alt else None, m.start())
    return sorted(found, key=lambda i: i.line)


def links(text: str) -> list[str]:
    body = plain(text)
    return re.findall(r"(?<!!)\[[^\]]*\]\(\s*<?([^)\s>]+)", body) + re.findall(r"\bhref\s*=\s*[\"']([^\"']+)", body, re.I)


def first_screen(text: str) -> str:
    """The head of the README, up to the second heading or 40 lines. Approximates what a visitor sees."""
    lines = plain(text).split("\n")
    out, seen = [], 0
    for line in lines[:40]:
        if re.match(r"\s*##\s", line) or re.match(r"\s*<h2\b", line, re.I):
            seen += 1
            if seen > 1 or len(out) > 12:
                break
        out.append(line)
    return "\n".join(out)


def visible(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"[#*_`|>]+", " ", text)


def first_prose(text: str) -> str:
    for line in visible(plain(text)).split("\n"):
        words = line.split()
        if len(words) >= 4:
            return line.strip()
    return ""


def slugify(heading: str) -> str:
    heading = re.sub(r"!\[[^\]]*\]\([^)]*\)|<[^>]+>", "", heading)
    heading = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading).strip().lower()
    return re.sub(r"[^\w\- ]", "", heading, flags=re.U).replace(" ", "-")


def anchors(text: str) -> set[str]:
    seen, out = {}, set()
    body = plain(text)
    for m in re.finditer(r"^#{1,6}\s+(.+?)\s*#*\s*$", body, re.M):
        base = slugify(m.group(1))
        n = seen.get(base, 0)
        seen[base] = n + 1
        out.add(f"{base}-{n}" if n else base)
    out.update(re.findall(r"\b(?:id|name)\s*=\s*[\"']([^\"']+)", body))
    return out


def local_target(ctx: Ctx, base: str, src: str) -> Optional[str]:
    """Repo-relative path for a relative URL, or None when the URL is not local."""
    if re.match(r"[a-z][a-z0-9+.-]*:|//|#", src, re.I):
        return None
    path = urllib.parse.unquote(src.split("#")[0].split("?")[0])
    if path.startswith("/"):
        return path.lstrip("/")
    prefix = base.rsplit("/", 1)[0] + "/" if "/" in base else ""
    parts = []
    for bit in (prefix + path).split("/"):
        if bit == "..":
            if parts:
                parts.pop()
        elif bit not in (".", ""):
            parts.append(bit)
    return "/".join(parts)


@check("PRS-001", "presentation", "README is within the render limit", "high", "pr", "tree", "GitHub truncates a README past 500 KiB")
def prs001(ctx):
    n = len(readme(ctx).encode())
    if n > 500 * KiB:
        return bad(f"{n // KiB} KiB, so GitHub cuts it off")
    return bad(f"{n // KiB} KiB, close to the 500 KiB cut off") if n > 400 * KiB else ok(f"{n // KiB} KiB")


@check("PRS-002", "presentation", "Images have alt text", "medium", "pr", "tree", "111 of 425 exemplar images lacked it. WCAG 1.1.1")
def prs002(ctx):
    miss = [f"line {i.line}: {i.src[:70]}" for i in images(readme(ctx)) if not i.badge and not (i.alt or "").strip()]
    return bad(f"{len(miss)} images have no alt text", miss) if miss else ok()


@check("PRS-003", "presentation", "Relative images and links resolve", "high", "pr", "tree", "A broken hero is the first thing a visitor sees")
def prs003(ctx):
    base, text = readme_path(ctx), readme(ctx)
    tracked = set(ctx.tracked())
    dirs = {"/".join(f.split("/")[:n]) for f in tracked for n in range(1, f.count("/") + 1)}
    miss = []
    for src in [i.src for i in images(text)] + links(text):
        target = local_target(ctx, base, src)
        if target and target not in tracked and target.rstrip("/") not in dirs and target != "":
            miss.append(src)
    return bad(f"{len(miss)} relative targets are missing", sorted(set(miss))) if miss else ok()


@check("PRS-004", "presentation", "Picture elements have a fallback with alt text", "high", "pr", "tree", "GitHub theme image docs")
def prs004(ctx):
    body = plain(readme(ctx))
    wrong = [m.group(0)[:70].replace("\n", " ") for m in re.finditer(r"<picture\b.*?</picture>", body, re.I | re.S)
             if not re.search(r"<img\b[^>]*\balt\s*=\s*[\"'][^\"']+", m.group(0), re.I)]
    return bad(f"{len(wrong)} picture elements have no img fallback with alt text", wrong) if wrong else ok()


@check("PRS-005", "presentation", "Header badge count fits the owner's policy", "low", "pr", "tree", "Trockman 2018 npm study: correlation only, inflection near 5 in popular packages", opinion=True)
def prs005(ctx):
    head = [i for i in images(first_screen(readme(ctx))) if i.badge]
    limit = {"none": 0, "signal": 5, "full": 10}.get(ctx.policy.get("badge_policy", "signal"), 5)
    return bad(f"{len(head)} header badges, the limit under this policy is {limit}") if len(head) > limit else ok(f"{len(head)} header badges")


@check("PRS-006", "presentation", "No legacy workflow badge URLs", "medium", "pr", "tree", "The old workflows/<name>/badge.svg form returned 404 on softprops/action-gh-release")
def prs006(ctx):
    hits = [i.src for i in images(readme(ctx)) if re.search(r"github\.com/[^/]+/[^/]+/workflows/", i.src)]
    return bad(f"{len(hits)} badges use the retired URL form", hits) if hits else ok()


@check("PRS-007", "presentation", "No hardcoded version in a static badge", "low", "pr", "tree", "A static badge cannot update itself", opinion=True)
def prs007(ctx):
    hits = [i.src for i in images(readme(ctx)) if re.search(r"shields\.io/badge/[^?]*\bv?\d+\.\d+", i.src) and not re.search(r"contributor|covenant|apache|license|licence|python|node", i.src, re.I)]
    return bad(f"{len(hits)} static badges pin a version", hits) if hits else ok()


@check("PRS-008", "presentation", "Theme images use picture, not URL fragments", "low", "pr", "tree", "GitHub deprecated the fragments in favor of picture", opinion=True)
def prs008(ctx):
    hits = [i.src for i in images(readme(ctx)) if "#gh-dark-mode-only" in i.src or "#gh-light-mode-only" in i.src]
    return bad(f"{len(hits)} images use the older fragments", hits) if hits else ok()


@check("PRS-009", "presentation", "Alerts stay rare", "low", "pr", "tree", "GitHub advises limiting alerts to one or two per article")
def prs009(ctx):
    n = len(re.findall(r"^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]", plain(readme(ctx)), re.M))
    return bad(f"{n} alert blocks") if n > 2 else ok()


@check("PRS-010", "presentation", "Purpose comes before sponsors and notices", "medium", "pr", "tree", "got, axios and awesome lead with sponsors and bury the point", opinion=True)
def prs010(ctx):
    body = plain(readme(ctx))
    sponsor = re.search(r"sponsor|backers|supported by|powered by", body, re.I)
    if not sponsor:
        return ok()
    prose = first_prose(body)
    at = body.find(prose.split()[0]) if prose else len(body)
    return bad("a sponsor block appears before the project says what it is") if sponsor.start() < at else ok()


@check("PRS-011", "presentation", "A strong visual on the first screen for visual products", "high", "pr", "tree", "Showcase exemplars: gum, PowerToys", when=lambda c: None if c.kind in VISUAL_TYPES | {"cli"} else "the type does not need a hero visual")
def prs011(ctx):
    screen = first_screen(readme(ctx))
    shown = [i for i in images(screen) if not i.badge]
    if shown or (ctx.kind == "cli" and re.search(r"^(```|~~~)", readme(ctx)[:3000], re.M)):
        return ok()
    return bad(f"a {ctx.kind} sells by being seen, and the first screen shows no image")


@check("PRS-012", "presentation", "Local images are a sensible weight", "medium", "pr", "tree", "Author's limit of 2 MiB for GIFs, the gum exemplar's heaviest is 2.6 MiB", opinion=True)
def prs012(ctx):
    heavy = []
    base = readme_path(ctx)
    for i in images(readme(ctx)):
        target = local_target(ctx, base, i.src)
        if target and target in set(ctx.tracked()):
            size = (ctx.path / target).stat().st_size
            limit = 2 * MiB if target.lower().endswith((".gif", ".webm", ".mp4")) else 1 * MiB
            if size > limit:
                heavy.append(f"{size / MiB:.1f} MiB {target}")
    return bad(f"{len(heavy)} README images are heavy for a first visit", heavy) if heavy else ok()


def png_contrast(raw: bytes) -> Optional[tuple[float, float]]:
    """Share of opaque pixels readable on GitHub dark and light backgrounds, or None when not assessable."""
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    at, idat, head = 8, [], None
    while at + 8 <= len(raw):
        size = struct.unpack(">I", raw[at:at + 4])[0]
        kind = raw[at + 4:at + 8]
        if kind == b"IHDR":
            head = struct.unpack(">IIBBBBB", raw[at + 8:at + 21])
        elif kind == b"IDAT":
            idat.append(raw[at + 8:at + 8 + size])
        elif kind == b"IEND":
            break
        at += size + 12
    if not head or not idat:
        return None
    w, h, depth, color, _, _, interlace = head
    if depth != 8 or color != 6 or interlace or w * h > 4_000_000:
        return None
    data = zlib.decompress(b"".join(idat))
    stride, prev, visible_px, ok_dark, ok_light, translucent = w * 4, bytearray(w * 4), 0, 0, 0, 0
    pos = 0
    for y in range(h):
        kind = data[pos]
        row = bytearray(data[pos + 1:pos + 1 + stride])
        pos += stride + 1
        for i in range(stride):
            a = row[i - 4] if i >= 4 else 0
            b = prev[i]
            c = prev[i - 4] if i >= 4 else 0
            if kind == 1:
                row[i] = (row[i] + a) & 255
            elif kind == 2:
                row[i] = (row[i] + b) & 255
            elif kind == 3:
                row[i] = (row[i] + (a + b) // 2) & 255
            elif kind == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                row[i] = (row[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = row
        if y % 4 == 0:
            for x in range(0, stride, 16):
                if row[x + 3] < 128:
                    translucent += 1
                    continue
                visible_px += 1
                lum = (0.2126 * row[x] + 0.7152 * row[x + 1] + 0.0722 * row[x + 2]) / 255
                ok_dark += lum > 0.25
                ok_light += lum < 0.75
    if not visible_px or not translucent:
        return None
    return ok_dark / visible_px, ok_light / visible_px


@check("PRS-013", "presentation", "Transparent images stay readable in both themes", "medium", "pr", "tree", "Composite against GitHub dark and light backgrounds. Exemplars rarely test this")
def prs013(ctx):
    base, hits = readme_path(ctx), []
    tracked = set(ctx.tracked())
    for i in images(readme(ctx)):
        target = local_target(ctx, base, i.src)
        if i.in_picture or not target or target not in tracked or not target.lower().endswith(".png"):
            continue
        try:
            shares = png_contrast((ctx.path / target).read_bytes())
        except (OSError, zlib.error, struct.error, IndexError):
            continue
        if shares and min(shares) < 0.3:
            hits.append(f"{target}: mostly {'dark' if shares[0] < shares[1] else 'light'} ink on a transparent background")
    return bad(f"{len(hits)} images fade in one theme. Use picture with two variants", hits) if hits else ok()


@check("PRS-014", "presentation", "Contents list earns its place", "info", "report", "tree", "No exemplar under 100 lines has one, GitHub builds an outline automatically", opinion=True)
def prs014(ctx):
    text = readme(ctx)
    n = text.count("\n")
    toc = re.search(r"^#{2,3}\s*(table of contents|contents|toc)\b", text, re.I | re.M)
    return note(f"{n} lines with a hand-kept contents list. GitHub already builds an outline") if toc and n < 100 else ok()


def resembles(text: str) -> str:
    n = text.count("\n")
    heads = [h.lower() for h in re.findall(r"^##\s+(.+)$", plain(text), re.M)]
    imgs = [i for i in images(text) if not i.badge]
    if re.search(r"begin_tf_docs|generated by|do not edit", text, re.I):
        return "generated"
    if re.search(r"citation|bibtex|arxiv", text, re.I) and n < 400:
        return "paper"
    if n <= 124 and re.search(r"\bdocs?\b|documentation", text, re.I) and len(heads) <= 6:
        return "router"
    if len(imgs) >= 3:
        return "showcase"
    if any(re.search(r"\bwhy\b|features|self.?host", h) for h in heads) and imgs:
        return "pitch"
    if n >= 300:
        return "reference"
    return "standard"


@check("PRS-015", "presentation", "README style compared with the default for this type", "info", "report", "tree", "69 exemplars across 20 types", opinion=True)
def prs015(ctx):
    have = resembles(readme(ctx))
    want = ctx.policy.get("readme_preset") or PRESET_FOR.get(ctx.kind, "standard")
    if have == want or want == "own choice":
        return ok(f"resembles {have}")
    return note(f"resembles {have}, the {'owner policy' if ctx.policy.get('readme_preset') else 'default for a ' + ctx.kind} is {want}")


@check("PRS-016", "presentation", "Claims about adoption carry a source", "low", "report", "tree", "ripgrep shows corpus, commands and analysis. Undated numbers age silently", opinion=True)
def prs016(ctx):
    hits = []
    for n, line in enumerate(plain(readme(ctx)).split("\n"), 1):
        m = NUMBER_CLAIM.search(visible(line))
        if m and "http" not in line and "](" not in line:
            hits.append(f"line {n}: {m.group(0)}")
    return note(f"{len(hits)} adoption or speed claims with no link", hits) if hits else ok()


@check("PRS-017", "presentation", "First screen sells, process notes live lower down", "medium", "pr", "tree", "A README is a pitch before it is a record. Dates and test status belong in Status or Known limits", skip=("research", "awesome-list", "docs"), opinion=True)
def prs017(ctx):
    screen = visible(first_screen(readme(ctx)))
    hits = [m.group(0) for m in PROCESS_NOTE.finditer(screen)]
    return bad(f"the first screen reads like a status record: {', '.join(sorted(set(hits))[:5])}", hits) if hits else ok()


@check("PRS-018", "presentation", "A reader can start from the first two screens", "medium", "pr", "tree", "Quick start near the top across library, CLI and app exemplars", skip=("profile", "awesome-list", "docs", "dotfiles", "data", "research"))
def prs018(ctx):
    text = readme(ctx)
    head = "\n".join(text.split("\n")[:120])
    if re.search(r"^(```|~~~)", head, re.M) or re.search(r"(install|get started|quick ?start|download|usage)", head, re.I):
        return ok()
    return bad("no install, download or usage step in the first 120 lines")


@check("PRS-019", "presentation", "README opens with a title and a plain purpose", "medium", "pr", "tree", "standard-readme: title, then short description")
def prs019(ctx):
    body = plain(readme(ctx))
    has_title = re.search(r"^#\s+\S|<h1\b", body, re.M) or re.match(r"\s*(<picture|<p\b|<div\b|!\[|<img|<a\b)", body, re.I)
    prose = first_prose("\n".join(body.split("\n")[:40]))
    if not has_title:
        return bad("no title")
    return ok() if prose else bad("no sentence in the first 40 lines says what this is")


@check("PRS-020", "presentation", "In-page links land on a heading", "medium", "pr", "tree", "Broken anchors read as neglect")
def prs020(ctx):
    text = readme(ctx)
    have = anchors(text)
    miss = sorted({l for l in links(text) if l.startswith("#") and len(l) > 1 and urllib.parse.unquote(l[1:]).lower() not in {a.lower() for a in have}})
    return bad(f"{len(miss)} anchors point nowhere", miss) if miss else ok()


@check("PRS-021", "presentation", "No duplicate badges", "low", "pr", "tree", "flameshot shows 3 CI badges in its header, bitwarden/ios shows 4", opinion=True)
def prs021(ctx):
    badges = [i.src.split("?")[0] for i in images(first_screen(readme(ctx))) if i.badge]
    dup = sorted({b for b in badges if badges.count(b) > 1})
    return bad(f"{len(dup)} badges repeat", dup) if dup else ok()


@check("PRS-022", "presentation", "No personal machine paths in public docs", "high", "pr", "tree", "A home path leaks a username and shows the docs only work on one machine", when=lambda c: "private repository" if c.public is False else None)
def prs022(ctx):
    hits = []
    for f in ctx.tracked():
        if not f.lower().endswith((".md", ".mdx", ".rst", ".txt")):
            continue
        text = ctx.read(f)
        for n, line in enumerate((text or "").split("\n"), 1):
            m = HOME_PATH.search(line)
            if m:
                hits.append(f"{f}:{n}")
                break
    return bad(f"{len(hits)} files show a personal path", hits) if hits else ok()


@check("PRS-023", "presentation", "No unfilled placeholders or template leftovers", "high", "pr", "tree", "Best-README-Template style leftovers read as abandoned")
def prs023(ctx):
    text = plain(readme(ctx))
    hits = re.findall(r"\{\{[^}\n]+\}\}|\bTODO\b|\bTBD\b|\bLorem ipsum\b|your[-_]username|your[-_]repo|<your [^>]+>", text)
    return bad(f"{len(hits)} placeholders remain", sorted(set(hits))) if hits else ok()


def public_host(url: str) -> bool:
    """Only fetch public https hosts. README URLs are untrusted."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or not parts.hostname:
        return False
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(parts.hostname, 443, proto=socket.IPPROTO_TCP)}
    except OSError:
        return False
    return all(ipaddress.ip_address(a).is_global for a in addresses)


def probe(url: str) -> tuple[str, Optional[str]]:
    """Return (url, problem). Rate limits and server errors read as None, because they prove nothing."""
    if not public_host(url):
        return url, None
    req = urllib.request.Request(url, headers={"User-Agent": "repo-audit", "Range": "bytes=0-65535"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            total = r.headers.get("Content-Range", "").split("/")[-1]
            size = int(total) if total.isdigit() else int(r.headers.get("Content-Length") or 0)
            head = r.read(65536)
    except urllib.error.HTTPError as e:
        return url, f"HTTP {e.code}" if e.code in (404, 410) else None
    except (OSError, ValueError):
        return url, None
    if size > 5 * MiB:
        return url, f"{size / MiB:.1f} MiB, over the GitHub image proxy limit"
    if BADGE.search(url) and re.search(rb">[^<]*\b(invalid|not found|inaccessible|no status|unknown|error)\b[^<]*<", head, re.I):
        return url, "the badge renders an error"
    return url, None


def proxied(src: str) -> bool:
    return bool(re.match(r"https?://", src)) and not re.match(r"https?://(raw\.githubusercontent\.com|github\.com/[^/]+/[^/]+/raw/)", src)


@check("PRS-024", "presentation", "Remote images and badges load", "high", "pr", "github", "llama.cpp, nanoGPT and plausible all ship dead or dropped images. GitHub's proxy returned 404 at 5.04 MiB")
def prs024(ctx):
    urls = sorted({i.src for i in images(readme(ctx)) if proxied(i.src)})[:60]
    if not urls:
        return ok("no remote images")
    with ThreadPoolExecutor(8) as pool:
        rows = [f"{u[:90]}: {p}" for u, p in pool.map(probe, urls) if p]
    return bad(f"{len(rows)} of {len(urls)} remote images fail", rows) if rows else ok(f"{len(urls)} remote images load")


@check("PRS-025", "presentation", "Repository front page is not cluttered", "low", "report", "tree", "A root with dozens of loose files pushes the README below the fold", opinion=True)
def prs025(ctx):
    top = {f.split("/")[0] for f in ctx.tracked()}
    return note(f"{len(top)} entries at the root push the README down the page") if len(top) > 30 else ok(f"{len(top)} entries at the root")
