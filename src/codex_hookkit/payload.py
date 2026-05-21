"""Codex hook payload parsing."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, TextIO

from .schemas import validate


@dataclass(frozen=True)
class HookPayload:
    """A parsed Codex hook payload."""

    raw: dict[str, Any]
    schema: str

    @classmethod
    def from_stdin(
        cls, schema: str = "pre-tool-use", *, validate_schema: bool = True
    ) -> HookPayload:
        return cls.from_stream(sys.stdin, schema=schema, validate_schema=validate_schema)

    @classmethod
    def from_stream(
        cls,
        stream: TextIO,
        schema: str = "pre-tool-use",
        *,
        validate_schema: bool = True,
    ) -> HookPayload:
        try:
            data = json.load(stream)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid hook JSON: {exc}") from exc
        return cls.from_dict(data, schema=schema, validate_schema=validate_schema)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        schema: str = "pre-tool-use",
        *,
        validate_schema: bool = True,
    ) -> HookPayload:
        if not isinstance(data, dict):
            raise TypeError("hook payload must be a JSON object")
        if validate_schema:
            validate(data, schema, direction="input")
        return cls(raw=data, schema=schema)

    @property
    def hook_event_name(self) -> str:
        return str(self.raw.get("hook_event_name", ""))

    @property
    def tool_name(self) -> str:
        return str(self.raw.get("tool_name", ""))

    @property
    def tool_input(self) -> Any:
        return self.raw.get("tool_input")

    @property
    def cwd(self) -> str:
        return str(self.raw.get("cwd", ""))

    def command_text(self) -> str:
        """Best-effort extraction of a shell command from common Codex tool inputs."""

        tool_input = self.tool_input
        if isinstance(tool_input, dict):
            for key in ("cmd", "command", "script"):
                value = tool_input.get(key)
                if isinstance(value, str):
                    return value
        if isinstance(tool_input, str):
            return tool_input
        return ""
