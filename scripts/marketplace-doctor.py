#!/usr/bin/env python3
"""
Marketplace Doctor - audits the AxENR marketplace integrity.

Usage:
    python3 scripts/marketplace-doctor.py [--strict] [--json]

Exit codes:
    0 - no issue (or only INFO in lax mode)
    1 - WARN/CRITICAL detected in strict mode, CRITICAL in lax mode
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E0-\U0001F1FF"
    "]+",
    flags=re.UNICODE,
)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
TOP_LEVEL_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")

PARTNER_PLUGIN = "axelor"
# Each plugin belongs to the family of its users, so that nobody gets lost:
# socle = everyone, technique = developers, fonctionnel = ERP/GMAO consultants,
# support = project management and marketing.
PLUGIN_FAMILIES = {"socle", "technique", "fonctionnel", "support"}
# Only these SKILL.md frontmatter keys are accepted by the claude.ai organization sync.
CLAUDE_AI_SKILL_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SKILL_NAME_MAX = 64
SKILL_DESCRIPTION_MAX = 1024

SECRET_PATTERNS = {
    "GitHub token": re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{30,}"),
    "Anthropic/OpenAI key": re.compile(r"\bsk-(ant-)?[A-Za-z0-9_-]{30,}"),
    "Brevo key": re.compile(r"\bxkeysib-[A-Za-z0-9-]{30,}"),
    "AWS key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Atlassian token": re.compile(r"\bATATT[A-Za-z0-9_=-]{30,}"),
    "URL with credentials": re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s:/@]+:[^\s:/@<>{}]{6,}@"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}
TEXT_SUFFIXES = {".md", ".py", ".sh", ".sql", ".json", ".yml", ".yaml", ".txt", ".js", ".ts", ".xml", ".csv"}


class Check:
    def __init__(self, check_id: str, severity: str, message: str, fix: str = ""):
        self.id = check_id
        self.severity = severity
        self.message = message
        self.fix = fix

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "severity": self.severity,
            "message": self.message,
            "fix": self.fix,
        }


def load_json(path: Path) -> Any:
    with path.open() as fh:
        return json.load(fh)


def parse_frontmatter(text: str) -> dict[str, str] | None:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    fm: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()
    return fm


def top_level_frontmatter(text: str) -> dict[str, str] | None:
    """Top-level keys only; a folded or multi-line value is joined into one string."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    fm: dict[str, str] = {}
    current = None
    for line in match.group(1).splitlines():
        key_match = TOP_LEVEL_KEY_RE.match(line)
        if key_match:
            current = key_match.group(1)
            fm[current] = key_match.group(2).strip()
        elif current is not None:
            fm[current] = (fm[current] + " " + line.strip()).strip()
    for key, value in fm.items():
        fm[key] = re.sub(r"^[>|][+-]?\s*", "", value).strip().strip('"').strip("'")
    return fm


def check_skill(skill_dir: Path, checks: list[Check]) -> str | None:
    rel = skill_dir.relative_to(ROOT)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        checks.append(
            Check(
                "SKILL-FILE",
                "CRITICAL",
                f"{rel} has no SKILL.md (the skill is never loaded)",
                fix=f"git mv {rel}/<file>.md {rel}/SKILL.md",
            )
        )
        return None
    fm = top_level_frontmatter(skill_md.read_text(encoding="utf-8"))
    if fm is None or "name" not in fm or "description" not in fm:
        checks.append(Check("FRONTMATTER", "CRITICAL", f"Missing name/description in {rel}/SKILL.md"))
        return None
    name = fm["name"]
    if name != skill_dir.name:
        checks.append(
            Check("SKILL-NAME", "CRITICAL", f"{rel}: name '{name}' differs from folder '{skill_dir.name}'")
        )
    if not SKILL_NAME_RE.match(name) or len(name) > SKILL_NAME_MAX:
        checks.append(
            Check("SKILL-NAME", "CRITICAL", f"{rel}: name must be lowercase-hyphenated, max {SKILL_NAME_MAX} chars")
        )
    if len(fm["description"]) > SKILL_DESCRIPTION_MAX:
        checks.append(
            Check(
                "SKILL-DESCRIPTION",
                "CRITICAL",
                f"{rel}: description is {len(fm['description'])} chars (max {SKILL_DESCRIPTION_MAX})",
                fix="Shorten the description; move details into the body",
            )
        )
    extra = sorted(set(fm) - CLAUDE_AI_SKILL_KEYS)
    if extra:
        checks.append(
            Check(
                "CLAUDE-AI-FRONTMATTER",
                "CRITICAL",
                f"{rel}/SKILL.md has keys rejected by claude.ai sync: {', '.join(extra)}",
                fix="Move them under 'metadata:' or remove them",
            )
        )
    return name


def check_secrets(plugin_dir: Path, checks: list[Check]) -> None:
    for path in plugin_dir.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                checks.append(
                    Check(
                        "SECRET",
                        "CRITICAL",
                        f"Possible {label} in {path.relative_to(ROOT)}",
                        fix="Remove it, revoke it, and read it from an environment variable",
                    )
                )


def run_checks() -> list[Check]:
    checks: list[Check] = []

    marketplace_json_path = ROOT / ".claude-plugin" / "marketplace.json"
    if not marketplace_json_path.exists():
        checks.append(Check("JSON-VALID", "CRITICAL", "marketplace.json missing"))
        return checks

    try:
        marketplace = load_json(marketplace_json_path)
    except json.JSONDecodeError as exc:
        checks.append(Check("JSON-VALID", "CRITICAL", f"marketplace.json invalid: {exc}"))
        return checks

    plugins_declared = marketplace.get("plugins", [])
    for plugin in plugins_declared:
        source_rel = plugin["source"].lstrip("./")
        plugin_dir = ROOT / source_rel
        plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"

        if not plugin_dir.exists():
            checks.append(
                Check(
                    "PLUGIN-REF",
                    "CRITICAL",
                    f"Plugin source not found: {plugin['source']}",
                    fix=f"Create directory {plugin_dir} or remove plugin from marketplace.json",
                )
            )
            continue

        if not plugin_json_path.exists():
            checks.append(
                Check(
                    "PLUGIN-REF",
                    "CRITICAL",
                    f"plugin.json missing for {plugin['name']}",
                    fix=f"Create {plugin_json_path}",
                )
            )
            continue

        try:
            plugin_json = load_json(plugin_json_path)
        except json.JSONDecodeError as exc:
            checks.append(
                Check(
                    "JSON-VALID",
                    "CRITICAL",
                    f"{plugin_json_path} invalid: {exc}",
                )
            )
            continue

        if plugin.get("category") not in PLUGIN_FAMILIES:
            checks.append(
                Check(
                    "PLUGIN-FAMILY",
                    "CRITICAL",
                    f"Plugin {plugin['name']} has category {plugin.get('category')!r}",
                    fix="Set category to one of: " + ", ".join(sorted(PLUGIN_FAMILIES)),
                )
            )

        declared_version = plugin["version"]
        actual_version = plugin_json.get("version")
        if declared_version != actual_version:
            checks.append(
                Check(
                    "VER-SYNC",
                    "CRITICAL",
                    f"Version mismatch for {plugin['name']}: "
                    f"marketplace.json={declared_version} plugin.json={actual_version}",
                    fix="Run ./scripts/bump-version.sh or /axenr-dev:bump-version",
                )
            )

    owned_dirs = [
        ROOT / plugin["source"].lstrip("./")
        for plugin in plugins_declared
        if plugin["name"] != PARTNER_PLUGIN and (ROOT / plugin["source"].lstrip("./")).exists()
    ]
    declared = {d.resolve() for d in owned_dirs} | {(ROOT / "plugins" / PARTNER_PLUGIN).resolve()}
    for plugin_dir in sorted((ROOT / "plugins").iterdir()):
        if plugin_dir.is_dir() and plugin_dir.resolve() not in declared:
            checks.append(
                Check(
                    "PLUGIN-UNDECLARED",
                    "WARN",
                    f"{plugin_dir.relative_to(ROOT)} is not declared in marketplace.json",
                    fix="Declare it in .claude-plugin/marketplace.json or remove the folder",
                )
            )

    names: dict[str, list[Path]] = {}
    for plugin_dir in owned_dirs:
        check_secrets(plugin_dir, checks)

        skills_dir = plugin_dir / "skills"
        if skills_dir.exists():
            for skill_dir in sorted(d for d in skills_dir.iterdir() if d.is_dir()):
                name = check_skill(skill_dir, checks)
                if name:
                    names.setdefault(name, []).append(skill_dir / "SKILL.md")

        for kind in ("agents", "commands"):
            folder = plugin_dir / kind
            if not folder.exists():
                continue
            for nested in (d for d in folder.iterdir() if d.is_dir()):
                checks.append(
                    Check(
                        "NESTED-COMPONENT",
                        "WARN",
                        f"{nested.relative_to(ROOT)} is loaded as {kind}; move resources to {plugin_dir.name}/resources/",
                    )
                )
            for md_path in sorted(folder.glob("*.md")):
                text = md_path.read_text(encoding="utf-8")
                line_count = len(text.splitlines())
                if kind == "agents" and line_count > 800:
                    checks.append(
                        Check(
                            "LARGE-AGENT",
                            "WARN",
                            f"{md_path.relative_to(ROOT)} has {line_count} lines (>800)",
                            fix="Consider splitting into multiple sub-agents or external includes",
                        )
                    )
                if kind == "agents":
                    fm = parse_frontmatter(text)
                    if fm is None or "name" not in fm or "description" not in fm:
                        checks.append(
                            Check(
                                "FRONTMATTER",
                                "CRITICAL",
                                f"Missing or invalid frontmatter in {md_path.relative_to(ROOT)}",
                                fix="Add YAML frontmatter with 'name' and 'description'",
                            )
                        )
                    else:
                        names.setdefault(fm["name"], []).append(md_path)

        for md_path in plugin_dir.rglob("*.md"):
            if EMOJI_PATTERN.search(md_path.read_text(encoding="utf-8")):
                checks.append(
                    Check(
                        "EMOJI-DETECTED",
                        "WARN",
                        f"Emoji in {md_path.relative_to(ROOT)}",
                        fix="Remove emojis (AxENR rule: NO EMOJIS)",
                    )
                )

    for name, paths in names.items():
        if len(paths) > 1:
            checks.append(
                Check(
                    "DUPLICATE-NAME",
                    "CRITICAL",
                    f"Duplicate name '{name}' in: " + ", ".join(str(p.relative_to(ROOT)) for p in paths),
                    fix="Rename one of the components",
                )
            )

    lessons_file = ROOT / "plugins" / "axenr-dev" / "docs" / "lessons" / "LESSONS-LEARNED.md"
    if lessons_file.exists():
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ct", str(lessons_file)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                import time

                last_ts = int(result.stdout.strip())
                age_days = (time.time() - last_ts) / 86400
                if age_days > 30:
                    checks.append(
                        Check(
                            "STALE-LESSONS",
                            "WARN",
                            f"LESSONS-LEARNED.md not updated since {age_days:.0f} days",
                            fix="Run /axenr-dev:consolidate-lessons or resolve tickets",
                        )
                    )
        except Exception:
            pass

    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN too")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    checks = run_checks()

    summary = {"CRITICAL": 0, "WARN": 0, "INFO": 0}
    for check in checks:
        summary[check.severity] = summary.get(check.severity, 0) + 1

    if summary["CRITICAL"] > 0:
        status = "critical"
    elif summary["WARN"] > 0:
        status = "warnings"
    else:
        status = "ok"

    exit_code = 0
    if summary["CRITICAL"] > 0:
        exit_code = 1
    elif args.strict and summary["WARN"] > 0:
        exit_code = 1

    if args.json:
        print(
            json.dumps(
                {
                    "status": status,
                    "exit_code": exit_code,
                    "summary": summary,
                    "checks": [c.to_dict() for c in checks],
                },
                indent=2,
            )
        )
    else:
        print(f"Marketplace Doctor - status: {status}")
        print(
            f"  CRITICAL: {summary['CRITICAL']}  WARN: {summary['WARN']}  INFO: {summary['INFO']}"
        )
        for severity in ("CRITICAL", "WARN", "INFO"):
            items = [c for c in checks if c.severity == severity]
            if not items:
                continue
            print(f"\n{severity}:")
            for check in items:
                print(f"  [{check.id}] {check.message}")
                if check.fix:
                    print(f"    Fix: {check.fix}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
