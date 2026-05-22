"""Helpers for writing Codex hook trust state."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EVENT_LABELS = {
    "PreToolUse": "pre_tool_use",
    "PermissionRequest": "permission_request",
    "PostToolUse": "post_tool_use",
    "PreCompact": "pre_compact",
    "PostCompact": "post_compact",
    "SessionStart": "session_start",
    "UserPromptSubmit": "user_prompt_submit",
    "SubagentStart": "subagent_start",
    "SubagentStop": "subagent_stop",
    "Stop": "stop",
}


@dataclass(frozen=True)
class HookTrustEntry:
    """One persisted Codex hook trust-state entry."""

    key: str
    current_hash: str
    event_name: str
    group_index: int
    handler_index: int
    command: str


@dataclass(frozen=True)
class HookTrustWriteResult:
    """Summary of a hook trust-state write."""

    config_path: Path
    entries: tuple[HookTrustEntry, ...]

    @property
    def count(self) -> int:
        return len(self.entries)


def hook_trust_entries(hooks_path: str | Path) -> list[HookTrustEntry]:
    """Return Codex hook trust entries for command hooks in a hooks.json file."""

    source_path = Path(hooks_path).expanduser().resolve()
    data = json.loads(source_path.read_text(encoding="utf-8"))
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        raise TypeError("hooks config must contain a JSON object at 'hooks'")

    entries: list[HookTrustEntry] = []
    for event_name, groups in hooks.items():
        event_label = EVENT_LABELS.get(event_name)
        if event_label is None:
            continue
        if not isinstance(groups, list):
            continue
        for group_index, group in enumerate(groups):
            if not isinstance(group, dict):
                continue
            handlers = group.get("hooks", [])
            if not isinstance(handlers, list):
                continue
            for handler_index, handler in enumerate(handlers):
                if not isinstance(handler, dict) or handler.get("type") != "command":
                    continue
                command = handler.get("command")
                if not isinstance(command, str) or not command.strip():
                    continue
                if bool(handler.get("async", False)):
                    continue
                current_hash = command_hook_hash(event_label, group, handler)
                key = f"{source_path}:{event_label}:{group_index}:{handler_index}"
                entries.append(
                    HookTrustEntry(
                        key=key,
                        current_hash=current_hash,
                        event_name=event_name,
                        group_index=group_index,
                        handler_index=handler_index,
                        command=command,
                    )
                )
    return entries


def command_hook_hash(event_label: str, group: dict[str, Any], handler: dict[str, Any]) -> str:
    """Hash a command hook using Codex's normalized hook identity shape."""

    timeout = handler.get("timeout", handler.get("timeout_sec", 600))
    if not isinstance(timeout, int):
        timeout = 600
    normalized_handler: dict[str, Any] = {
        "type": "command",
        "command": handler["command"],
        "timeout": max(timeout, 1),
        "async": bool(handler.get("async", False)),
    }

    status_message = handler.get("statusMessage", handler.get("status_message"))
    if isinstance(status_message, str):
        normalized_handler["statusMessage"] = status_message

    identity: dict[str, Any] = {
        "event_name": event_label,
        "hooks": [normalized_handler],
    }
    if "matcher" in group and group["matcher"] is not None:
        identity["matcher"] = group["matcher"]

    serialized = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(serialized).hexdigest()}"


def write_hook_trusts(
    hooks_path: str | Path,
    *,
    config_path: str | Path | None = None,
) -> HookTrustWriteResult:
    """Write all command hook trust entries from hooks_path into config.toml."""

    entries = tuple(hook_trust_entries(hooks_path))
    destination = (
        Path(config_path).expanduser()
        if config_path is not None
        else Path.home() / ".codex" / "config.toml"
    )
    existing = destination.read_text(encoding="utf-8") if destination.exists() else ""
    updated = existing
    for entry in entries:
        updated = upsert_hook_trust_state(updated, entry)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(updated, encoding="utf-8")
    return HookTrustWriteResult(config_path=destination, entries=entries)


def upsert_hook_trust_state(text: str, entry: HookTrustEntry) -> str:
    """Return config.toml text with one hooks.state trusted_hash inserted or replaced."""

    header = f'[hooks.state."{toml_basic_string(entry.key)}"]'
    lines = text.splitlines()
    if not lines and not text:
        return f'{header}\ntrusted_hash = "{entry.current_hash}"\n'

    for index, line in enumerate(lines):
        if line.strip() != header:
            continue
        end = index + 1
        while end < len(lines) and not lines[end].startswith("["):
            end += 1
        body = lines[index + 1 : end]
        for body_index, body_line in enumerate(body):
            if body_line.strip().startswith("trusted_hash"):
                body[body_index] = f'trusted_hash = "{entry.current_hash}"'
                break
        else:
            body.append(f'trusted_hash = "{entry.current_hash}"')
        updated_lines = [*lines[: index + 1], *body, *lines[end:]]
        return "\n".join(updated_lines).rstrip() + "\n"

    prefix = "\n\n" if text.strip() else ""
    return text.rstrip() + prefix + f'{header}\ntrusted_hash = "{entry.current_hash}"\n'


def toml_basic_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
