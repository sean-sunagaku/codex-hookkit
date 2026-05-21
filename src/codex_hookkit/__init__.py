"""Small helpers for building Codex hook guards."""

from .decisions import Decision, allow, deny, dump_json
from .payload import HookPayload
from .policy import SecretPolicy
from .scaffold import secret_guard_hook
from .schemas import SchemaName, available_schemas, load_schema, schema_path, validate
from .upstream import SchemaSnapshot, download_schema_snapshot

__version__ = "0.0.3"

__all__ = [
    "Decision",
    "HookPayload",
    "SchemaName",
    "SecretPolicy",
    "SchemaSnapshot",
    "__version__",
    "allow",
    "available_schemas",
    "deny",
    "dump_json",
    "download_schema_snapshot",
    "load_schema",
    "schema_path",
    "secret_guard_hook",
    "validate",
]
