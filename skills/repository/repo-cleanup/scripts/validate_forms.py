#!/usr/bin/env python3
"""Validate GitHub issue forms and config.yml without third-party packages.

usage: validate_forms.py PATH [PATH ...]

PATH is a checkout, an ISSUE_TEMPLATE folder, or one YAML file. A checkout means
every .yml and .yaml file under .github/ISSUE_TEMPLATE. Markdown templates are
skipped. Each problem prints as file:line: error: message.

The parser reads the block YAML subset that issue forms use. A construct it does
not support, such as an anchor or a flow list that spans lines, is reported as an
error, so a pass means this parser read the whole file. GitHub remains the final
check, because only it knows the full rules.

Exit 0 means no errors, 1 means errors found, 2 means bad input.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.dont_write_bytecode = True

FIELD_TYPES = {"markdown", "textarea", "input", "dropdown", "checkboxes", "upload"}
TOP_KEYS = {"name", "description", "title", "labels", "assignees", "projects", "type", "body"}
ELEMENT_KEYS = {"type", "id", "attributes", "validations"}
CONFIG_KEYS = {"blank_issues_enabled", "contact_links"}
CONTACT_KEYS = {"name", "url", "about"}
BOOL_WORDS = {"y", "yes", "n", "no", "true", "false", "on", "off"}
FORBIDDEN_KEYS = {"y", "yes", "no", "true", "false", "on", "off"}
RESERVED_OPTIONS = {"none"}
FORBIDDEN_LABEL_WORDS = ("password",)
ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
KEY_RE = re.compile(r"""^("(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[^\s#"'\[\]{}&*!|>%@`-][^#]*?|-[^\s#][^#]*?)\s*:(?:\s+(.*))?$""")
BLOCK_RE = re.compile(r"^[|>][+-]?[1-9]?[+-]?$")


class YamlError(Exception):
    def __init__(self, line: int, message: str):
        super().__init__(message)
        self.line = line
        self.message = message


@dataclass
class Scalar:
    value: str
    line: int
    quoted: bool = False


@dataclass
class Seq:
    items: list
    line: int


@dataclass
class Map:
    entries: dict = field(default_factory=dict)  # key -> (key line, node)
    line: int = 1

    def get(self, key):
        found = self.entries.get(key)
        return found[1] if found else None

    def line_of(self, key):
        found = self.entries.get(key)
        return found[0] if found else self.line


def strip_comment(text: str) -> str:
    """Drop a trailing comment. A hash starts one only at the start or after a space."""
    quote = None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote == '"' and ch == "\\":
            i += 2
            continue
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'" and (i == 0 or text[i - 1] in " \t[,:"):
            quote = ch
        elif ch == "#" and (i == 0 or text[i - 1] in " \t"):
            return text[:i].rstrip()
        i += 1
    return text.rstrip()


def unquote(token: str, line: int) -> Scalar:
    if token[0] == '"':
        if len(token) < 2 or not token.endswith('"') or token.endswith('\\"') and not token.endswith('\\\\"'):
            raise YamlError(line, "unterminated double quote")
        body = token[1:-1]
        if re.search(r'(?<!\\)(?:\\\\)*"', body):
            raise YamlError(line, "text after a closing quote")
        return Scalar(re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), body), line, True)
    if len(token) < 2 or not token.endswith("'"):
        raise YamlError(line, "unterminated single quote")
    body = token[1:-1]
    if "'" in body.replace("''", ""):
        raise YamlError(line, "text after a closing quote")
    return Scalar(body.replace("''", "'"), line, True)


def plain(token: str, line: int) -> Scalar:
    if token[0] in "&*!%@`":
        raise YamlError(line, f"unsupported YAML starting with {token[0]!r}")
    if token[0] in "{}]":
        raise YamlError(line, "flow mappings are not supported")
    if ": " in token or token.endswith(":"):
        raise YamlError(line, "a colon in plain text must be quoted")
    return Scalar(token, line)


def split_flow(text: str, line: int) -> list:
    parts, current, quote, i = [], "", None, 0
    while i < len(text):
        ch = text[i]
        if quote == '"' and ch == "\\":
            current += text[i:i + 2]
            i += 2
            continue
        if quote:
            quote = None if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif ch in "[]{}":
            raise YamlError(line, "nested flow collections are not supported")
        elif ch == ",":
            parts.append(current.strip())
            current = ""
            i += 1
            continue
        current += ch
        i += 1
    if quote:
        raise YamlError(line, "unterminated quote in a flow list")
    if current.strip():
        parts.append(current.strip())
    return parts


def inline_value(text: str, line: int):
    if text[0] in "\"'":
        return unquote(text, line)
    if text[0] == "[":
        if not text.endswith("]"):
            raise YamlError(line, "unterminated flow list, or one that spans lines")
        return Seq([inline_value(p, line) for p in split_flow(text[1:-1], line)], line)
    return plain(text, line)


class Parser:
    def __init__(self, text: str):
        self.raw = text.splitlines()
        self.lines = [None] * len(self.raw)  # (indent, text) overrides for "- key: value"
        self.i = 0

    def peek(self):
        """Move to the next content line and return (indent, text), or None at the end."""
        while self.i < len(self.raw):
            raw = self.raw[self.i]
            if self.lines[self.i] is not None:
                return self.lines[self.i]
            stripped = raw.lstrip(" ")
            if not raw.strip() or stripped.startswith("#"):
                self.i += 1
                continue
            if stripped[0] == "\t":
                raise YamlError(self.i + 1, "tab in indentation")
            return len(raw) - len(stripped), strip_comment(stripped)
        return None

    @property
    def no(self) -> int:
        return self.i + 1

    def document(self):
        current = self.peek()
        if current and current[1] == "---":
            self.i += 1
            current = self.peek()
        if current is None:
            raise YamlError(1, "empty document")
        node = self.node(current[0])
        rest = self.peek()
        if rest is not None:
            if rest[1] in ("---", "..."):
                raise YamlError(self.no, "more than one YAML document")
            raise YamlError(self.no, "bad indentation")
        return node

    def node(self, indent: int):
        _, text = self.peek()
        if text == "-" or text.startswith("- "):
            return self.sequence(indent)
        if KEY_RE.match(text):
            return self.mapping(indent)
        node = inline_value(text, self.no)
        self.i += 1
        return node

    def sequence(self, indent: int) -> Seq:
        seq = Seq([], self.no)
        while True:
            current = self.peek()
            if current is None or current[0] < indent:
                return seq
            if current[0] > indent:
                raise YamlError(self.no, "bad indentation")
            text = current[1]
            if not (text == "-" or text.startswith("- ")):
                return seq
            rest = text[1:].lstrip(" ")
            if not rest:
                line = self.no
                self.i += 1
                nested = self.peek()
                if nested is None or nested[0] <= indent:
                    seq.items.append(Scalar("", line))
                else:
                    seq.items.append(self.node(nested[0]))
                continue
            if rest.startswith("- "):
                raise YamlError(self.no, "nested sequences on one line are not supported")
            column = indent + len(text) - len(rest)
            if rest[0] not in "\"'[" and KEY_RE.match(rest) or (rest[0] in "\"'" and self.quoted_key(rest)):
                self.lines[self.i] = (column, rest)
                seq.items.append(self.mapping(column))
            else:
                seq.items.append(inline_value(rest, self.no))
                self.i += 1

    @staticmethod
    def quoted_key(text: str) -> bool:
        match = KEY_RE.match(text)
        return bool(match) and match.group(1)[0] in "\"'"

    def mapping(self, indent: int) -> Map:
        result = Map(line=self.no)
        while True:
            current = self.peek()
            if current is None or current[0] < indent:
                return result
            if current[0] > indent:
                raise YamlError(self.no, "bad indentation")
            text = current[1]
            if text in ("---", "..."):
                return result
            if text == "-" or text.startswith("- "):
                raise YamlError(self.no, "a list item where a key was expected")
            match = KEY_RE.match(text)
            if not match:
                raise YamlError(self.no, "expected key: value")
            line = self.no
            key = match.group(1)
            key = unquote(key, line).value if key[0] in "\"'" else key
            if key in result.entries:
                raise YamlError(line, f"duplicate key {key!r}")
            self.lines[self.i] = None
            value = (match.group(2) or "").strip()
            self.i += 1
            result.entries[key] = (line, self.value(value, indent, line))

    def value(self, value: str, indent: int, line: int):
        if value and BLOCK_RE.match(value):
            return self.block_scalar(indent, line)
        if value:
            node = inline_value(value, line)
            if isinstance(node, Scalar) and not node.quoted:
                node.value = self.continuation(node.value, indent)
            return node
        following = self.peek()
        if following is not None and following[0] > indent:
            return self.node(following[0])
        if following is not None and following[0] == indent and (following[1] == "-" or following[1].startswith("- ")):
            return self.sequence(indent)
        return Scalar("", line)

    def continuation(self, value: str, indent: int) -> str:
        while True:
            following = self.peek()
            if following is None or following[0] <= indent:
                return value
            text = following[1]
            if KEY_RE.match(text) or text == "-" or text.startswith("- "):
                raise YamlError(self.no, "bad indentation")
            value = f"{value} {plain(text, self.no).value}"
            self.i += 1

    def block_scalar(self, indent: int, line: int) -> Scalar:
        collected = []
        while self.i < len(self.raw):
            raw = self.raw[self.i]
            if not raw.strip():
                collected.append("")
                self.i += 1
                continue
            if len(raw) - len(raw.lstrip(" ")) <= indent:
                break
            collected.append(raw.strip())
            self.i += 1
        return Scalar("\n".join(collected).strip("\n"), line, True)


def parse(text: str):
    return Parser(text).document()


class Report:
    def __init__(self):
        self.errors: list = []
        self.warnings: list = []

    def error(self, path, line, message):
        self.errors.append((str(path), line, message))

    def warn(self, path, line, message):
        self.warnings.append((str(path), line, message))


def walk_keys(node, path, report):
    if isinstance(node, Map):
        for key, (line, child) in node.entries.items():
            if key.lower() in FORBIDDEN_KEYS:
                report.error(path, line, f"key {key!r} is read as a boolean, which GitHub rejects")
            walk_keys(child, path, report)
    elif isinstance(node, Seq):
        for item in node.items:
            walk_keys(item, path, report)


def text_of(node) -> str:
    return node.value.strip() if isinstance(node, Scalar) else ""


def normalize(label: str) -> str:
    return re.sub(r"[^a-z0-9]", "", label.lower())


def is_bool(node) -> bool:
    return isinstance(node, Scalar) and not node.quoted and node.value.lower() in {"true", "false"}


def check_field_label(attrs, kind, path, report, seen, element_line):
    label = attrs.get("label")
    if not text_of(label):
        report.error(path, attrs.line_of("label") if label else element_line, f"{kind} field has no label")
        return
    value = text_of(label)
    if kind in ("input", "textarea") and any(word in value.lower() for word in FORBIDDEN_LABEL_WORDS):
        report.error(path, label.line, f"label {value!r} holds a word GitHub blocks")
    key = normalize(value)
    if key in seen:
        report.error(path, label.line, f"label {value!r} duplicates or normalizes to the label on line {seen[key]}")
    seen.setdefault(key, label.line)


def check_dropdown(attrs, path, report, element_line):
    options = attrs.get("options")
    if not isinstance(options, Seq) or not options.items:
        report.error(path, attrs.line_of("options") if options else element_line, "dropdown needs a nonempty options list")
        return
    seen = set()
    words = set()
    for option in options.items:
        if not isinstance(option, Scalar) or not option.value.strip():
            report.error(path, getattr(option, "line", element_line), "dropdown option must be text")
            continue
        value = option.value.strip()
        if not option.quoted and value.lower() in BOOL_WORDS:
            report.error(path, option.line, f"option {value!r} is read as a boolean, quote it")
        if value.lower() in RESERVED_OPTIONS:
            report.error(path, option.line, f"option {value!r} is reserved")
        if value in seen:
            report.error(path, option.line, f"duplicate option {value!r}")
        seen.add(value)
        words.add(value.lower())
    default = attrs.get("default")
    if default is not None:
        if not re.fullmatch(r"\d+", text_of(default)) or int(text_of(default)) >= len(options.items):
            report.error(path, default.line if isinstance(default, Scalar) else element_line, "default must be an option index")
        if words & {"none", "n/a"}:
            report.error(path, attrs.line_of("default"), "default cannot combine with a None or n/a option")


def check_checkboxes(attrs, path, report, element_line):
    options = attrs.get("options")
    if not isinstance(options, Seq) or not options.items:
        report.error(path, attrs.line_of("options") if options else element_line, "checkboxes need a nonempty options list")
        return
    seen = set()
    for option in options.items:
        if not isinstance(option, Map) or not text_of(option.get("label")):
            report.error(path, getattr(option, "line", element_line), "checkbox option has no label")
            continue
        value = text_of(option.get("label"))
        if value in seen:
            report.error(path, option.line, f"duplicate option {value!r}")
        seen.add(value)
        required = option.get("required")
        if required is not None and not is_bool(required):
            report.error(path, option.line_of("required"), "required must be true or false")


def check_element(element, path, report, ids, labels):
    if not isinstance(element, Map):
        report.error(path, getattr(element, "line", 1), "body item must be a mapping")
        return None
    for key, (line, _) in element.entries.items():
        if key not in ELEMENT_KEYS:
            report.error(path, line, f"unknown key {key!r} in a body item")
    kind = text_of(element.get("type"))
    if kind not in FIELD_TYPES:
        report.error(path, element.line_of("type"), f"unknown or missing type {kind!r}")
        return None
    identifier = element.get("id")
    if identifier is not None:
        value = text_of(identifier)
        if not ID_RE.match(value):
            report.error(path, element.line_of("id"), f"id {value!r} may hold only letters, numbers, - and _")
        elif value in ids:
            report.error(path, element.line_of("id"), f"duplicate id {value!r}, first used on line {ids[value]}")
        else:
            ids[value] = element.line_of("id")
    attrs = element.get("attributes")
    if not isinstance(attrs, Map):
        report.error(path, element.line, f"{kind} field needs attributes")
        return kind
    if kind == "markdown":
        if not text_of(attrs.get("value")):
            report.error(path, element.line, "markdown field needs attributes.value")
        if element.get("validations") is not None:
            report.error(path, element.line_of("validations"), "markdown field cannot have validations")
        return kind
    check_field_label(attrs, kind, path, report, labels, element.line)
    if attrs.get("render") is not None and kind != "textarea":
        report.error(path, attrs.line_of("render"), "render applies only to textarea")
    if kind == "dropdown":
        check_dropdown(attrs, path, report, element.line)
    if kind == "checkboxes":
        check_checkboxes(attrs, path, report, element.line)
    validations = element.get("validations")
    if validations is not None:
        required = validations.get("required") if isinstance(validations, Map) else None
        if required is not None and not is_bool(required):
            report.error(path, validations.line_of("required"), "required must be true or false")
    return kind


def check_form(root, path, report):
    if not isinstance(root, Map):
        report.error(path, getattr(root, "line", 1), "a form must be a mapping")
        return None
    for key, (line, _) in root.entries.items():
        if key not in TOP_KEYS:
            report.error(path, line, f"unknown top-level key {key!r}")
    walk_keys(root, path, report)
    name = text_of(root.get("name"))
    if not name:
        report.error(path, root.line_of("name"), "name is required")
    elif len(name) <= 3:
        report.error(path, root.line_of("name"), "name must be more than 3 characters or the template does not show")
    if not text_of(root.get("description")):
        report.error(path, root.line_of("description"), "description is required")
    labels = root.get("labels")
    if labels is None:
        report.warn(path, root.line, "no top-level labels, so issues from this form arrive unlabeled")
    elif isinstance(labels, Seq):
        names = [text_of(item) for item in labels.items]
        if not names or not all(names):
            report.error(path, root.line_of("labels"), "labels must list label names")
        if len(set(names)) != len(names):
            report.error(path, root.line_of("labels"), "labels holds a duplicate")
    elif not text_of(labels):
        report.error(path, root.line_of("labels"), "labels is empty")
    body = root.get("body")
    if not isinstance(body, Seq) or not body.items:
        report.error(path, root.line_of("body"), "body must be a nonempty list")
        return name
    ids: dict = {}
    seen_labels: dict = {}
    kinds = [check_element(item, path, report, ids, seen_labels) for item in body.items]
    if all(kind == "markdown" for kind in kinds):
        report.error(path, root.line_of("body"), "body needs at least one field that is not markdown")
    return name


def check_config(root, path, report):
    if not isinstance(root, Map):
        report.error(path, getattr(root, "line", 1), "config must be a mapping")
        return
    for key, (line, _) in root.entries.items():
        if key not in CONFIG_KEYS:
            report.error(path, line, f"unknown key {key!r} in config")
    blank = root.get("blank_issues_enabled")
    if blank is not None and not is_bool(blank):
        report.error(path, root.line_of("blank_issues_enabled"), "blank_issues_enabled must be true or false")
    links = root.get("contact_links")
    if links is None:
        return
    if not isinstance(links, Seq):
        report.error(path, root.line_of("contact_links"), "contact_links must be a list")
        return
    for link in links.items:
        if not isinstance(link, Map):
            report.error(path, getattr(link, "line", 1), "contact link must be a mapping")
            continue
        for key, (line, _) in link.entries.items():
            if key not in CONTACT_KEYS:
                report.error(path, line, f"unknown key {key!r} in a contact link")
        for key in sorted(CONTACT_KEYS):
            if not text_of(link.get(key)):
                report.error(path, link.line, f"contact link needs {key}")
        url = text_of(link.get("url"))
        if url and not url.lower().startswith(("https://", "http://", "mailto:")):
            report.error(path, link.line_of("url"), "contact link url needs a scheme")
        if "OWNER/REPO" in url:
            report.warn(path, link.line_of("url"), "OWNER/REPO placeholder is still here")


def validate_file(path: Path, report: Report, names: dict) -> None:
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError:
        report.error(path, 1, "file is not UTF-8")
        return
    try:
        root = parse(text)
    except YamlError as exc:
        report.error(path, exc.line, exc.message)
        return
    if path.stem.lower() == "config":
        check_config(root, path, report)
        return
    name = check_form(root, path, report)
    if name:
        if name in names:
            report.error(path, root.line_of("name"), f"name {name!r} is also used by {names[name]}")
        names.setdefault(name, path.name)


def collect(target: Path) -> list:
    if target.is_file():
        return [target]
    folder = target / ".github" / "ISSUE_TEMPLATE"
    if not folder.is_dir():
        if target.name != "ISSUE_TEMPLATE":
            return []
        folder = target
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in (".yml", ".yaml"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", type=Path, help="checkout, ISSUE_TEMPLATE folder or YAML file")
    args = ap.parse_args(argv)
    report = Report()
    count = 0
    for target in args.paths:
        if not target.exists():
            print(f"path not found: {target}", file=sys.stderr)
            return 2
        files = collect(target)
        if not files:
            print(f"no issue forms found under {target}", file=sys.stderr)
            return 2
        names: dict = {}
        for path in files:
            validate_file(path, report, names)
            count += 1
    for path, line, message in report.warnings:
        print(f"{path}:{line}: warning: {message}")
    for path, line, message in report.errors:
        print(f"{path}:{line}: error: {message}")
    print(f"{count} files, {len(report.errors)} errors, {len(report.warnings)} warnings")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
