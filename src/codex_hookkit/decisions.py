"""Decision helpers for Codex hook outputs."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, TextIO

from .outputs import PermissionRequestOutput, PreToolUseOutput


@dataclass(frozen=True)
class Decision:
    """A policy decision."""

    allowed: bool
    reason: str = ""

    @property
    def denied(self) -> bool:
        return not self.allowed


class allow:
    """Allow-output builders."""

    @staticmethod
    def decision(reason: str = "") -> Decision:
        return Decision(allowed=True, reason=reason)

    @staticmethod
    def pre_tool_use_json(additional_context: str | None = None) -> dict[str, Any]:
        return PreToolUseOutput.allow(additional_context).validated()

    @staticmethod
    def permission_request_json(message: str | None = None) -> dict[str, Any]:
        return PermissionRequestOutput.allow(message).validated()


class deny:
    """Deny-output builders."""

    @staticmethod
    def decision(reason: str) -> Decision:
        return Decision(allowed=False, reason=reason)

    @staticmethod
    def stderr_exit(reason: str, stream: TextIO = sys.stderr) -> int:
        print(reason, file=stream)
        return 2

    @staticmethod
    def pre_tool_use_json(reason: str) -> dict[str, Any]:
        return PreToolUseOutput.deny(reason).validated()

    @staticmethod
    def permission_request_json(reason: str) -> dict[str, Any]:
        return PermissionRequestOutput.deny(reason).validated()


def dump_json(output: dict[str, Any], stream: TextIO = sys.stdout) -> None:
    json.dump(output, stream, separators=(",", ":"))
    stream.write("\n")
