#!/usr/bin/env python3
"""Validate repository-bundled Codex skills without external dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKILLS_DIR = Path("skills")
NAME_PATTERN = re.compile(r"^[a-z0-9-]{1,63}$")


def main() -> int:
    if not SKILLS_DIR.exists():
        return 0

    errors: list[str] = []
    for skill_dir in sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir()):
        errors.extend(validate_skill(skill_dir))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return [f"{skill_dir}: missing SKILL.md"]

    text = skill_file.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    if frontmatter is None:
        errors.append(f"{skill_file}: missing YAML frontmatter")
        return errors

    name = frontmatter.get("name")
    description = frontmatter.get("description")
    if not name:
        errors.append(f"{skill_file}: missing frontmatter name")
    elif not NAME_PATTERN.fullmatch(name):
        errors.append(f"{skill_file}: invalid skill name {name!r}")
    elif name != skill_dir.name:
        errors.append(f"{skill_file}: name {name!r} does not match directory {skill_dir.name!r}")

    if not description:
        errors.append(f"{skill_file}: missing frontmatter description")
    elif "TODO" in description:
        errors.append(f"{skill_file}: description still contains TODO")

    if "TODO" in text:
        errors.append(f"{skill_file}: body still contains TODO")

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if openai_yaml.exists() and "TODO" in openai_yaml.read_text(encoding="utf-8"):
        errors.append(f"{openai_yaml}: still contains TODO")

    return errors


def parse_frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None

    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator:
            continue
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


if __name__ == "__main__":
    raise SystemExit(main())
