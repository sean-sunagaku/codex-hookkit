"""Load and validate vendored Codex hook schemas."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any, Iterable, Literal

from jsonschema import Draft7Validator

SchemaName = Literal[
    "permission-request",
    "post-compact",
    "post-tool-use",
    "pre-compact",
    "pre-tool-use",
    "session-start",
    "stop",
    "subagent-start",
    "subagent-stop",
    "user-prompt-submit",
]

_VENDOR_ROOT = "vendor/openai-codex-hook-schemas/generated"
_THIRD_PARTY_ROOT = (
    Path(__file__).resolve().parents[2] / "third_party" / "openai-codex-hook-schemas" / "generated"
)


def _schema_filename(schema: str, direction: str) -> str:
    normalized = schema.removesuffix(".command.input").removesuffix(".command.output")
    normalized = normalized.removesuffix(".input").removesuffix(".output")
    if direction not in {"input", "output"}:
        raise ValueError("direction must be 'input' or 'output'")
    return f"{normalized}.command.{direction}.schema.json"


def schema_path(schema: str, direction: str = "input") -> Path:
    """Return the installed path for a vendored schema file."""

    filename = _schema_filename(schema, direction)
    resource = resources.files("codex_hookkit").joinpath(_VENDOR_ROOT, filename)
    with resources.as_file(resource) as path:
        if not path.exists():
            third_party_path = _THIRD_PARTY_ROOT / filename
            if third_party_path.exists():
                return third_party_path
            raise FileNotFoundError(f"unknown Codex hook schema: {schema!r} ({direction})")
        return Path(path)


def load_schema(schema: str, direction: str = "input") -> dict[str, Any]:
    """Load a vendored Codex hook schema."""

    path = schema_path(schema, direction)
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise TypeError(f"schema is not a JSON object: {path}")
    return data


def available_schemas() -> list[str]:
    """List hook schema base names available in the installed package."""

    resource_root = resources.files("codex_hookkit").joinpath(_VENDOR_ROOT)
    with resources.as_file(resource_root) as resource_path:
        root = resource_path if resource_path.exists() else _THIRD_PARTY_ROOT
    names: set[str] = set()
    for path in root.iterdir():
        name = path.name
        if name.endswith(".command.input.schema.json"):
            names.add(name.removesuffix(".command.input.schema.json"))
    return sorted(names)


def iter_validation_errors(payload: Any, schema: str, direction: str = "input") -> Iterable[str]:
    """Yield human-readable validation errors for a payload."""

    validator = Draft7Validator(load_schema(schema, direction))
    for error in sorted(validator.iter_errors(payload), key=lambda item: item.path):
        path = ".".join(str(part) for part in error.path) or "$"
        yield f"{path}: {error.message}"


def validate(payload: Any, schema: str, direction: str = "input") -> None:
    """Raise ``ValueError`` if a payload does not match a Codex hook schema."""

    errors = list(iter_validation_errors(payload, schema, direction))
    if errors:
        raise ValueError("; ".join(errors))
