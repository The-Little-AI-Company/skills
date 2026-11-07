"""Repository type detection. The type decides which checks and presets apply."""

from __future__ import annotations

import json
import re

from engine import Ctx, Unknown

TYPES = ("profile", "awesome-list", "action", "infra", "dotfiles", "docs", "game", "mobile", "desktop", "plugin",
         "design-system", "template", "monorepo", "research", "ml", "webapp", "sdk", "cli", "framework", "library",
         "data", "unknown")

WEB_DEPS = {"next", "nuxt", "vite", "react-dom", "@sveltejs/kit", "astro", "remix", "express", "fastify", "django",
            "flask", "rails", "laravel/framework"}
DOT_FILES = {".zshrc", ".bashrc", ".vimrc", ".tmux.conf", ".gitconfig", ".aliases", ".bash_profile", "init.vim"}


def _pkg(ctx: Ctx) -> dict:
    try:
        data = json.loads(ctx.read("package.json") or "{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _deps(pkg: dict) -> set:
    return {k for key in ("dependencies", "devDependencies", "peerDependencies") for k in (pkg.get(key) or {})}


def detect(ctx: Ctx) -> dict:
    """Return the type, a confidence and the signals. The first rule that fires wins, others are listed."""
    declared = ctx.policy.get("type")
    if declared in TYPES:
        return {"name": declared, "confidence": "declared", "signals": ["policy file"], "also": []}
    try:
        files = ctx.tracked()
    except Unknown:
        files = []
    top = {f.split("/")[0] for f in files}
    lower = {f.lower() for f in files}
    bases = {f.rsplit("/", 1)[-1].lower() for f in files}
    name = (ctx.slug or (ctx.path.name if ctx.path else "")).split("/")[-1].lower()
    owner = (ctx.slug or "/").split("/")[0].lower()
    pkg = _pkg(ctx)
    deps = _deps(pkg)
    py = (ctx.read("pyproject.toml") or "") + (ctx.read("requirements.txt") or "")
    cargo = ctx.read("Cargo.toml") or ""
    readme = ctx.read("README.md") or ""
    md_share = sum(f.lower().endswith((".md", ".mdx", ".rst")) for f in files) / max(len(files), 1)
    ipynb = sum(f.endswith(".ipynb") for f in files)
    meta = {}
    if ctx.online and ctx.slug:
        try:
            meta = ctx.meta()
        except Unknown:
            pass
    topics = {t.lower() for t in meta.get("topics") or []}

    rules = [
        ("profile", name == owner and bool(owner), "repository name equals the owner"),
        ("awesome-list", name.startswith("awesome") or "awesome-list" in topics or bool(re.match(r"#\s*awesome\b", readme, re.I)), "awesome list naming"),
        ("action", {"action.yml", "action.yaml"} & lower != set(), "action.yml at the root"),
        ("infra", any(f.endswith(".tf") and "/" not in f for f in files) or name.startswith("terraform-") or "chart.yaml" in lower, "Terraform or Helm files at the root"),
        ("dotfiles", name in ("dotfiles", ".dotfiles") or len(DOT_FILES & bases) >= 2, "shell or editor config files"),
        ("game", {"project.godot", "projectsettings/projectversion.txt"} & lower != set() or any(f.endswith(".uproject") for f in files) or bool({"phaser", "pixi.js", "three"} & deps and "game" in name), "game engine project files"),
        ("mobile", "pubspec.yaml" in lower or any(f.endswith(".xcodeproj/project.pbxproj") for f in files) or "react-native" in deps or "android/app/build.gradle" in lower or "app/src/main/androidmanifest.xml" in lower, "mobile project files"),
        ("desktop", "electron" in deps or "src-tauri/tauri.conf.json" in lower or "@tauri-apps/api" in deps, "Electron or Tauri project"),
        ("plugin", ".claude-plugin/plugin.json" in lower or ".claude-plugin/marketplace.json" in lower or "skill.md" in bases or bool((pkg.get("engines") or {}).get("vscode")) or '"manifest_version"' in (ctx.read("manifest.json") or ""), "editor, browser or agent plugin manifest"),
        ("design-system", ".storybook/main.ts" in lower or ".storybook/main.js" in lower, "Storybook configuration"),
        ("template", bool(meta.get("is_template")) or bool(re.search(r"(template|starter|boilerplate|scaffold)$", name)) or "cookiecutter.json" in lower, "template naming or flag"),
        ("monorepo", bool({"pnpm-workspace.yaml", "turbo.json", "nx.json", "lerna.json", "go.work"} & lower) or bool(pkg.get("workspaces")) or "[workspace]" in cargo, "workspace configuration"),
        ("docs", bool({"mkdocs.yml", "book.toml", "docusaurus.config.js", "docusaurus.config.ts"} & lower) or (md_share > 0.7 and len(files) >= 5), "documentation site or mostly Markdown"),
        ("research", "citation.cff" in lower and bool(re.search(r"\b(paper|arxiv|doi\.org)\b", readme, re.I)), "citation file and paper links"),
        ("ml", ipynb >= 3 or bool(re.search(r"^(torch|tensorflow|jax|transformers|scikit-learn)\b", py, re.M)) or bool(re.search(r"\b(torch|tensorflow|transformers)\b", py)), "notebooks or ML dependencies"),
        ("webapp", bool(WEB_DEPS & deps) or "manage.py" in lower or "gemfile" in lower and "config/routes.rb" in lower, "web framework dependency"),
        ("sdk", bool(re.search(r"(-sdk|-client|-api)$", name)), "SDK or client naming"),
        ("cli", bool(pkg.get("bin")) or "[project.scripts]" in py or "[[bin]]" in cargo or "src/main.rs" in lower or "main.go" in lower or any(f.startswith("cmd/") for f in lower), "binary entry point"),
        ("library", bool(pkg.get("main") or pkg.get("exports")) or "[project]" in py or "[lib]" in cargo or "src/lib.rs" in lower or "go.mod" in lower or "setup.py" in lower or "gemspec" in " ".join(lower), "package manifest"),
        ("data", sum(f.lower().endswith((".csv", ".parquet", ".jsonl")) for f in files) >= 5, "data files"),
    ]
    hits = [(k, why) for k, fired, why in rules if fired]
    if not hits:
        return {"name": "unknown", "confidence": "low", "signals": [], "also": []}
    kind, why = hits[0]
    strong = {"profile", "action", "plugin", "mobile", "game", "desktop", "infra", "monorepo"}
    confidence = "high" if kind in strong else ("medium" if len(hits) <= 2 else "low")
    return {"name": kind, "confidence": confidence, "signals": [why], "also": [k for k, _ in hits[1:]]}


def modifiers(ctx: Ctx) -> tuple:
    mods = []
    if ctx.online and ctx.slug:
        try:
            m = ctx.meta()
            mods += [k for k, f in (("archived", "archived"), ("fork", "fork"), ("template", "is_template")) if m.get(f)]
            mods.append("private" if m.get("private") else "public")
        except Unknown:
            pass
    try:
        if not ctx.tracked():
            mods.append("empty")
    except Unknown:
        pass
    return tuple(mods)
