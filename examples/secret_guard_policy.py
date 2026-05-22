from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from codex_hookkit import Decision, allow, deny


@dataclass(frozen=True)
class SecretGuardPolicy:
    """Example policy for blocking direct secret file and token access."""

    blocked_path_fragments: tuple[str, ...] = (
        "." + "env",
        "." + "pypirc",
        "." + "npmrc",
        "." + "netrc",
        "." + "ssh",
        "id_" + "rsa",
        "id_" + "ed25519",
    )
    blocked_env_names: tuple[str, ...] = (
        "PYPI" + "_API" + "_TOKEN",
        "TWINE" + "_PASSWORD",
        "CLOUDFLARE" + "_API" + "_TOKEN",
        "GITHUB" + "_TOKEN",
        "OPENAI" + "_API" + "_KEY",
    )
    blocked_command_patterns: tuple[re.Pattern[str], ...] = field(default_factory=tuple)

    @classmethod
    def default(cls) -> SecretGuardPolicy:
        sensitive_files = r"\.(env|pypirc|npmrc)"
        sensitive_words = "TOKEN|SECRET|PASSWORD|KEY"
        return cls(
            blocked_command_patterns=(
                re.compile(rf"\b(printenv|env)\b.*\b({sensitive_words})\b", re.I),
                re.compile(rf"\b(cat|less|more|tail|head|sed|awk|rg|grep)\b.*{sensitive_files}\b"),
            )
        )

    def evaluate(self, payload: object) -> Decision:
        command = command_text(payload)
        if not command:
            return allow.decision()

        env_match = self.blocked_env_name(command)
        if env_match:
            return deny.decision(f"Blocked direct secret environment access: {env_match}.")

        path_match = self.blocked_path(command)
        if path_match:
            return deny.decision(f"Blocked direct secret file access: {path_match}.")

        for pattern in self.blocked_command_patterns:
            if pattern.search(command):
                return deny.decision("Blocked command that appears to read secrets.")

        return allow.decision()

    def blocked_env_name(self, command: str) -> str:
        for name in self.blocked_env_names:
            if re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", command):
                return name
        return ""

    def blocked_path(self, command: str) -> str:
        for token in split_command(command):
            normalized = token.replace("\\", "/")
            path = PurePosixPath(normalized)
            parts = set(path.parts)
            for fragment in self.blocked_path_fragments:
                if fragment in normalized or fragment in parts:
                    return token
        return ""


def split_command(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def command_text(payload: object) -> str:
    tool_input = getattr(payload, "tool_input", None)
    if isinstance(tool_input, dict):
        for key in ("cmd", "command", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    if isinstance(tool_input, str):
        return tool_input
    return ""
