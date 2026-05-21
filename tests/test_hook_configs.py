from __future__ import annotations

import json
from pathlib import Path

from codex_hookkit import codex_review_hooks

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def test_codex_hook_config_is_valid_json() -> None:
    config = load_json(ROOT / ".codex" / "hooks.json")
    assert isinstance(config, dict)
    assert "hooks" in config


def test_codex_review_hook_example_is_valid_json() -> None:
    config = load_json(ROOT / "examples" / "codex_review_hooks.json")
    assert isinstance(config, dict)
    assert set(config["hooks"]) == {"PostToolUse", "Stop"}


def test_codex_review_hook_scaffold_is_valid_json() -> None:
    config = json.loads(codex_review_hooks())
    assert set(config["hooks"]) == {"PostToolUse", "Stop"}
