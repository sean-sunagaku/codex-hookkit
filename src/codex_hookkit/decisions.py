"""Decision helpers for Codex hook outputs."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, Optional, TextIO

from .schemas import validate


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
    def pre_tool_use_json(additional_context: Optional[str] = None) -> dict[str, Any]:
        output: dict[str, Any] = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
            }
        }
        if additional_context:
            output["hookSpecificOutput"]["additionalContext"] = additional_context
        validate(output, "pre-tool-use", direction="output")
        return output

    @staticmethod
    def permission_request_json(message: Optional[str] = None) -> dict[str, Any]:
        decision: dict[str, Any] = {"behavior": "allow"}
        if message:
            decision["message"] = message
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": decision,
            }
        }
        validate(output, "permission-request", direction="output")
        return output


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
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
        validate(output, "pre-tool-use", direction="output")
        return output

    @staticmethod
    def permission_request_json(reason: str) -> dict[str, Any]:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {
                    "behavior": "deny",
                    "message": reason,
                },
            }
        }
        validate(output, "permission-request", direction="output")
        return output


def dump_json(output: dict[str, Any], stream: TextIO = sys.stdout) -> None:
    json.dump(output, stream, separators=(",", ":"))
    stream.write("\n")
