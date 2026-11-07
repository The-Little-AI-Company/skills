#!/usr/bin/env python3
"""Render a README through GitHub's Markdown API into light and dark pages.

The file's text is sent to GitHub. GitHub returns relative paths unchanged, so pass --repo to point
them at raw.githubusercontent.com at --ref. Raw URLs load only for a public repository.

Prints the two page paths. Exit 0 when the pages match what GitHub shows. Exit 1 when GitHub could not
be reached or a page differs from GitHub, and the notes on stderr say how. Exit 2 on bad input.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import posixpath
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

sys.dont_write_bytecode = True

CSS_VERSION = "5.9.0"
CSS_URL = "https://cdn.jsdelivr.net/npm/github-markdown-css@" + CSS_VERSION + "/github-markdown-{theme}.css"
COLUMN_PX = 1012
THEMES = {"light": "#ffffff", "dark": "#0d1117"}
SLUG = re.compile(r"^[\w.-]+/[\w.-]+$")
REF = re.compile(r"^(?!.*\.\.)[\w./-]+$")
SECRET = re.compile(r"gh[pousr]_\w{20,}|github_pat_\w+")
ABSOLUTE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", re.I)
TAG = re.compile(r"<[a-z][\w-]*\b[^>]*>", re.I)
URL_ATTR = re.compile(r"(\s)(src|href|srcset)=\"([^\"]*)\"", re.I)
PICTURE = re.compile(r"<picture>.*?</picture>", re.I | re.S)
SOURCE = re.compile(r"<source\b[^>]*>", re.I)
SCHEME = re.compile(r"\s*media=\"\(prefers-color-scheme:\s*(light|dark)\)\"", re.I)
ENRICHED = re.compile(r"data-type=\"(mermaid|geojson|topojson|stl)\"", re.I)


class GhError(Exception):
    """A gh call failed. The message is safe to print."""


def run_gh(argv: list[str], stdin: str) -> str:
    env = dict(os.environ, MSYS_NO_PATHCONV="1")
    try:
        done = subprocess.run(["gh", *argv], input=stdin, capture_output=True, encoding="utf-8", errors="replace", env=env, timeout=120)
    except FileNotFoundError as exc:
        raise GhError("gh is not on PATH. Install the GitHub CLI and run gh auth login.") from exc
    except subprocess.TimeoutExpired as exc:
        raise GhError("gh timed out") from exc
    if done.returncode != 0:
        first = (done.stderr or "gh failed").strip().splitlines() or ["gh failed"]
        raise GhError(SECRET.sub("[redacted]", first[0])[:200])
    return done.stdout


def render(text: str, repo: Optional[str]) -> str:
    payload: dict = {"text": text, "mode": "gfm"}
    if repo:
        payload["context"] = repo
    return run_gh(["api", "markdown", "--method", "POST", "--input", "-"], json.dumps(payload))


def resolve(value: str, base: str, prefix: str) -> Optional[str]:
    """Turn one relative path into an absolute URL. None means the path leaves the repository."""
    match = re.match(r"([^#?]*)(.*)", value, re.S)
    path, tail = match.group(1), match.group(2)
    joined = path.lstrip("/") if path.startswith("/") else posixpath.join(base, path)
    clean = posixpath.normpath(joined)
    if clean == ".." or clean.startswith("../"):
        return None
    return f"{prefix}/{'' if clean == '.' else clean}{tail}"


def rewrite_urls(page: str, repo: Optional[str], ref: str, base: str) -> tuple[str, list[str]]:
    """Point relative src, srcset and href at the repository. Return the page and any paths left relative."""
    raw = f"https://raw.githubusercontent.com/{repo}/{ref}"
    blob = f"https://github.com/{repo}/blob/{ref}"
    left: list[str] = []

    def one(value: str, attr: str) -> str:
        if not value or ABSOLUTE.match(value):
            return value
        url = resolve(value, base, blob if attr == "href" else raw) if repo else None
        if url is None:
            left.append(value)
            return value
        return url

    def swap(match: re.Match) -> str:
        lead, attr, value = match.group(1), match.group(2).lower(), match.group(3)
        if attr == "srcset":
            parts = [p.strip().split(None, 1) for p in value.split(",") if p.strip()]
            value = ", ".join(" ".join([one(p[0], attr), *p[1:]]) for p in parts)
        else:
            value = one(value, attr)
        return f'{lead}{match.group(2)}="{value}"'

    return TAG.sub(lambda tag: URL_ATTR.sub(swap, tag.group(0)), page), left


def apply_theme(page: str, theme: str) -> str:
    """Pick each picture's source for this page. A browser would otherwise follow the OS, not the page."""

    def source(match: re.Match) -> str:
        scheme = SCHEME.search(match.group(0))
        if not scheme:
            return match.group(0)
        return SCHEME.sub("", match.group(0)) if scheme.group(1).lower() == theme else ""

    return PICTURE.sub(lambda m: SOURCE.sub(source, m.group(0)), page)


def wrap(body: str, theme: str, title: str) -> str:
    other = "dark" if theme == "light" else "light"
    return f"""<!doctype html>
<html lang="en" data-theme="{theme}">
<head>
<meta charset="utf-8">
<meta name="color-scheme" content="{theme}">
<title>{html.escape(title)} ({theme})</title>
<link rel="stylesheet" href="{CSS_URL.format(theme=theme)}">
<style>
html, body {{ margin: 0; background: {THEMES[theme]}; }}
body {{ min-width: {COLUMN_PX}px; }}
.markdown-body {{ box-sizing: border-box; width: {COLUMN_PX}px; margin: 0 auto; padding: 32px; }}
img[src$="#gh-{other}-mode-only"] {{ display: none; }}
.js-render-enrichment-loader {{ display: none; }}
</style>
</head>
<body>
<article class="markdown-body">
{body}
</article>
</body>
</html>
"""


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Render a README into light.html and dark.html the way GitHub shows it.")
    p.add_argument("readme", type=Path, help="Markdown file to render. Its text is sent to GitHub")
    p.add_argument("--out", type=Path, default=Path("preview"), help="output folder (default preview)")
    p.add_argument("--repo", help="owner/repo. Sets reference context and resolves relative images to raw URLs")
    p.add_argument("--ref", default="HEAD", help="branch, tag or commit for relative paths (default HEAD)")
    p.add_argument("--base", default="", help="folder of the file inside the repository, for a README not at the root")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = parser()
    args = p.parse_args(argv)
    if args.repo and not SLUG.match(args.repo):
        p.error("--repo takes owner/repo")
    if not REF.match(args.ref):
        p.error("--ref has unexpected characters")
    if args.base and not REF.match(args.base):
        p.error("--base has unexpected characters")
    if args.out.exists() and not args.out.is_dir():
        p.error(f"--out is not a folder: {args.out}")
    try:
        text = args.readme.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        p.error(f"cannot read {args.readme}: {type(exc).__name__}")

    try:
        page = render(text, args.repo)
    except GhError as exc:
        print(f"Render failed: {exc}", file=sys.stderr)
        return 1

    page, left = rewrite_urls(page, args.repo, args.ref, args.base.strip("/"))
    notes = []
    if left:
        fix = "They point outside the repository." if args.repo else "Pass --repo owner/repo and --ref to resolve them."
        notes.append(f"{len(left)} relative links or images are unresolved. {fix} First: {left[0]}")
    kinds = sorted({m.lower() for m in ENRICHED.findall(page)})
    if kinds:
        notes.append(f"{', '.join(kinds)} blocks show as source here. GitHub draws them only on its own pages.")

    args.out.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        path = args.out / f"{theme}.html"
        path.write_text(wrap(apply_theme(page, theme), theme, args.readme.name), encoding="utf-8")
        print(path)
    for note in notes:
        print(f"Note: {note}", file=sys.stderr)
    return 1 if notes else 0


if __name__ == "__main__":
    sys.exit(main())
