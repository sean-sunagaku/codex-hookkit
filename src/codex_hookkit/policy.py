"""Small default policies for Codex hook guards."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from .decisions import Decision, allow, deny
from .payload import HookPayload


@dataclass(frozen=True)
class SecretPolicy:
    """Block common direct secret and environment-file access patterns."""

    blocked_path_fragments: tuple[str, ...] = (
        ".env",
        ".pypirc",
        ".npmrc",
        ".netrc",
        ".ssh",
        "id_rsa",
        "id_ed25519",
    )
    blocked_env_names: tuple[str, ...] = (
        "PYPI_API_TOKEN",
        "TWINE_PASSWORD",
        "CLOUDFLARE_API_TOKEN",
        "GITHUB_TOKEN",
        "OPENAI_API_KEY",
    )
    blocked_command_patterns: tuple[re.Pattern[str], ...] = field(default_factory=tuple)

    @classmethod
    def default(cls) -> SecretPolicy:
        return cls(
            blocked_command_patterns=(
                re.compile(r"\b(printenv|env)\b.*\b(TOKEN|SECRET|PASSWORD|KEY)\b", re.IGNORECASE),
                re.compile(
                    r"\b(cat|less|more|tail|head|sed|awk|rg|grep)\b.*\.(env|pypirc|npmrc)\b"
                ),
            )
        )

    def evaluate(self, payload: HookPayload) -> Decision:
        command = payload.command_text()
        if not command:
            return allow.decision()

        env_match = self._blocked_env_name(command)
        if env_match:
            return deny.decision(f"Blocked direct secret environment access: {env_match}.")

        path_match = self._blocked_path(command)
        if path_match:
            return deny.decision(f"Blocked direct secret file access: {path_match}.")

        for pattern in self.blocked_command_patterns:
            if pattern.search(command):
                return deny.decision("Blocked command that appears to read secrets.")

        return allow.decision()

    def _blocked_env_name(self, command: str) -> str:
        for name in self.blocked_env_names:
            if re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", command):
                return name
        return ""

    def _blocked_path(self, command: str) -> str:
        for token in _split_command(command):
            normalized = token.replace("\\", "/")
            path = PurePosixPath(normalized)
            parts = set(path.parts)
            for fragment in self.blocked_path_fragments:
                if fragment in normalized or fragment in parts:
                    return token
        return ""


def _split_command(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()
