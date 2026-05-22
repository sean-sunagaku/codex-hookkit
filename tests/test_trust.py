from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from codex_hookkit.trust import HookTrustEntry, hook_trust_entries, upsert_hook_trust_state

ROOT = Path(__file__).resolve().parents[1]


def test_project_hooks_hashes_match_codex_current_hashes() -> None:
    entries = {
        entry.event_name: entry for entry in hook_trust_entries(ROOT / ".codex" / "hooks.json")
    }

    assert entries["PreToolUse"].current_hash == (
        "sha256:64d432b8f99e62c43b0e1bc5d96f908bec5a0705fea78da7fd89b82ce3287ca3"
    )
    assert entries["PermissionRequest"].current_hash == (
        "sha256:849fb1a20cd327e07a47542bf0700297c973eb825787964290427edd1fdb70a3"
    )
    assert entries["PostToolUse"].current_hash == (
        "sha256:5142199abb5ecf88354783e514ba4d159482ffb118b719e23d6e6b2ddfebe93c"
    )
    assert entries["Stop"].current_hash == (
        "sha256:d5b744943bf9720188e0b4e0dbd43897a6c997e9b268f01f9aff835f764f1136"
    )


def test_upsert_hook_trust_state_appends_and_updates() -> None:
    entry = HookTrustEntry(
        key="/tmp/project/.codex/hooks.json:pre_tool_use:0:0",
        current_hash="sha256:new",
        event_name="PreToolUse",
        group_index=0,
        handler_index=0,
        command="pwd",
    )

    inserted = upsert_hook_trust_state('model = "gpt-5"\n', entry)
    assert '[hooks.state."/tmp/project/.codex/hooks.json:pre_tool_use:0:0"]' in inserted
    assert 'trusted_hash = "sha256:new"' in inserted

    updated = upsert_hook_trust_state(inserted.replace("sha256:new", "sha256:old"), entry)
    assert 'trusted_hash = "sha256:new"' in updated
    assert "sha256:old" not in updated


def test_trust_hooks_cli_writes_all_entries(tmp_path: Path) -> None:
    hooks_path = tmp_path / "hooks.json"
    config_path = tmp_path / "config.toml"
    hooks_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "*",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "pwd",
                                    "timeout": 10,
                                }
                            ],
                        }
                    ],
                    "Stop": [
                        {
                            "matcher": "*",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "uv run python -m codex_hookkit.cli run-review",
                                    "timeout": 300,
                                }
                            ],
                        }
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "codex_hookkit.cli",
            "trust-hooks",
            "--hooks-path",
            str(hooks_path),
            "--config",
            str(config_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "wrote 2 hook trust entries" in result.stdout
    config = config_path.read_text(encoding="utf-8")
    assert f'[hooks.state."{hooks_path}:pre_tool_use:0:0"]' in config
    assert f'[hooks.state."{hooks_path}:stop:0:0"]' in config
