"""Small helpers for building Codex hook guards."""

from .decisions import Decision, allow, deny, dump_json
from .outputs import (
    PermissionRequestDecision,
    PermissionRequestHookSpecificOutput,
    PermissionRequestOutput,
    PostCompactOutput,
    PostToolUseHookSpecificOutput,
    PostToolUseOutput,
    PreCompactOutput,
    PreToolUseHookSpecificOutput,
    PreToolUseOutput,
    SessionStartHookSpecificOutput,
    SessionStartOutput,
    StopOutput,
    StructuredOutput,
    SubagentStartHookSpecificOutput,
    SubagentStartOutput,
    SubagentStopOutput,
    UserPromptSubmitHookSpecificOutput,
    UserPromptSubmitOutput,
)
from .payload import HookPayload
from .policy import SecretPolicy
from .review import ReviewMarker, request_review, run_review
from .scaffold import codex_review_hooks, secret_guard_hook
from .schemas import SchemaName, available_schemas, load_schema, schema_path, validate
from .upstream import SchemaSnapshot, download_schema_snapshot

__version__ = "0.0.3"

__all__ = [
    "Decision",
    "HookPayload",
    "PermissionRequestDecision",
    "PermissionRequestHookSpecificOutput",
    "PermissionRequestOutput",
    "PostCompactOutput",
    "PostToolUseHookSpecificOutput",
    "PostToolUseOutput",
    "PreCompactOutput",
    "PreToolUseHookSpecificOutput",
    "PreToolUseOutput",
    "SchemaName",
    "SecretPolicy",
    "SchemaSnapshot",
    "SessionStartHookSpecificOutput",
    "SessionStartOutput",
    "StopOutput",
    "StructuredOutput",
    "SubagentStartHookSpecificOutput",
    "SubagentStartOutput",
    "SubagentStopOutput",
    "UserPromptSubmitHookSpecificOutput",
    "UserPromptSubmitOutput",
    "__version__",
    "allow",
    "available_schemas",
    "codex_review_hooks",
    "deny",
    "dump_json",
    "download_schema_snapshot",
    "load_schema",
    "request_review",
    "ReviewMarker",
    "run_review",
    "schema_path",
    "secret_guard_hook",
    "validate",
]
