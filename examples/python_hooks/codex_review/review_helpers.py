"""Codex review hook helpers."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

ACTIVE_ENV = "CODEX_HOOKKIT_REVIEW_ACTIVE"
DEFAULT_STATE_DIR = ".codex-hookkit"
DEFAULT_MARKER = "pending-review.json"

CODE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".json",
    ".kt",
    ".mjs",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class ReviewMarker:
    """A pending Codex review request."""

    cwd: str
    files: list[str]
    session_id: str
    turn_id: str
    tool_name: str


@dataclass(frozen=True)
class Check:
    """A local verification command to run before review."""

    name: str
    command: list[str]
    timeout: int = 120


@dataclass(frozen=True)
class CheckResult:
    """Result from a local verification command."""

    name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def is_review_active() -> bool:
    return os.environ.get(ACTIVE_ENV) == "1"


def marker_path(cwd: str | Path, state_dir: str | Path = DEFAULT_STATE_DIR) -> Path:
    return Path(cwd) / state_dir / DEFAULT_MARKER


def changed_files(cwd: str | Path) -> list[str]:
    """Return tracked and untracked changed files relative to cwd."""

    root = Path(cwd)
    tracked = git_lines(root, ["diff", "--name-only", "--diff-filter=ACMRTUXB"])
    untracked = git_lines(root, ["ls-files", "--others", "--exclude-standard"])
    seen: set[str] = set()
    files: list[str] = []
    for path in [*tracked, *untracked]:
        if path not in seen:
            seen.add(path)
            files.append(path)
    return files


def code_files(paths: list[str], state_dir: str | Path = DEFAULT_STATE_DIR) -> list[str]:
    ignored_prefix = f"{Path(state_dir).as_posix().rstrip('/')}/"
    return [
        path
        for path in paths
        if not path.startswith(ignored_prefix) and Path(path).suffix.lower() in CODE_EXTENSIONS
    ]


def git_lines(cwd: Path, args: list[str]) -> list[str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line]


def tool_succeeded(payload: object) -> bool:
    response = _field(payload, "tool_response")
    if isinstance(response, dict):
        exit_code = response.get("exit_code")
        if isinstance(exit_code, int):
            return exit_code == 0
    return True


def request_review(
    payload: object, state_dir: str | Path = DEFAULT_STATE_DIR
) -> ReviewMarker | None:
    """Persist a review request when a PostToolUse event leaves code changes."""

    if (
        is_review_active()
        or _field(payload, "hook_event_name") != "PostToolUse"
        or not tool_succeeded(payload)
    ):
        return None

    cwd = str(_field(payload, "cwd", ""))
    files = code_files(changed_files(cwd), state_dir)
    if not files:
        return None

    marker = ReviewMarker(
        cwd=cwd,
        files=files,
        session_id=str(_field(payload, "session_id", "")),
        turn_id=str(_field(payload, "turn_id", "")),
        tool_name=str(_field(payload, "tool_name", "")),
    )
    path = marker_path(cwd, state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(marker.__dict__, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return marker


def load_marker(cwd: str | Path, state_dir: str | Path = DEFAULT_STATE_DIR) -> ReviewMarker | None:
    path = marker_path(cwd, state_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    files = data.get("files")
    if not isinstance(files, list):
        return None
    return ReviewMarker(
        cwd=str(data.get("cwd", cwd)),
        files=[str(path) for path in files],
        session_id=str(data.get("session_id", "")),
        turn_id=str(data.get("turn_id", "")),
        tool_name=str(data.get("tool_name", "")),
    )


def clear_marker(cwd: str | Path, state_dir: str | Path = DEFAULT_STATE_DIR) -> None:
    try:
        marker_path(cwd, state_dir).unlink()
    except FileNotFoundError:
        return


def discover_checks(cwd: str | Path, files: list[str]) -> list[Check]:
    """Infer cheap, non-mutating verification commands for changed files."""

    root = Path(cwd)
    suffixes = {Path(path).suffix.lower() for path in files}
    checks: list[Check] = []

    if suffixes & {".py"} and (root / "pyproject.toml").exists():
        checks.extend(
            [
                Check("fmt", ["uv", "run", "ruff", "format", "--check", "."]),
                Check("lint", ["uv", "run", "ruff", "check", "."]),
            ]
        )
        if (root / "tests").exists():
            checks.append(Check("test", ["uv", "run", "pytest", "-q"], timeout=180))

    if suffixes & {".js", ".jsx", ".mjs", ".ts", ".tsx"} and (root / "package.json").exists():
        scripts = package_scripts(root / "package.json")
        if "format:check" in scripts:
            checks.append(Check("fmt", ["npm", "run", "format:check"]))
        elif "prettier:check" in scripts:
            checks.append(Check("fmt", ["npm", "run", "prettier:check"]))
        if "lint" in scripts:
            checks.append(Check("lint", ["npm", "run", "lint"]))
        if "test" in scripts:
            checks.append(Check("test", ["npm", "test", "--", "--runInBand"], timeout=180))

    return dedupe_checks(checks)


def package_scripts(path: Path) -> set[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return set()
    return {str(name) for name in scripts}


def dedupe_checks(checks: list[Check]) -> list[Check]:
    seen: set[tuple[str, tuple[str, ...]]] = set()
    result: list[Check] = []
    for check in checks:
        key = (check.name, tuple(check.command))
        if key in seen:
            continue
        seen.add(key)
        result.append(check)
    return result


def run_checks(cwd: str | Path, checks: list[Check]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for check in checks:
        try:
            result = subprocess.run(
                check.command,
                cwd=cwd,
                text=True,
                capture_output=True,
                timeout=check.timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            results.append(
                CheckResult(
                    name=check.name,
                    command=check.command,
                    returncode=124,
                    stdout="",
                    stderr=str(exc),
                )
            )
            continue
        results.append(
            CheckResult(
                name=check.name,
                command=check.command,
                returncode=result.returncode,
                stdout=result.stdout[-4000:],
                stderr=result.stderr[-4000:],
            )
        )
    return results


def check_results_text(results: list[CheckResult]) -> str:
    if not results:
        return "No local verification checks were selected."

    lines = ["Local verification checks:"]
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        lines.append(f"- {result.name}: {status} ({shell_join(result.command)})")
        output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
        if output:
            lines.append(indent(output[-2000:], "  "))
    return "\n".join(lines)


def checks_plan_text(checks: list[Check]) -> str:
    if not checks:
        return "No local verification checks would be selected."
    lines = ["Local verification checks to run:"]
    lines.extend(f"- {check.name}: {shell_join(check.command)}" for check in checks)
    return "\n".join(lines)


def shell_join(command: list[str]) -> str:
    return subprocess.list2cmdline(command)


def indent(text: str, prefix: str) -> str:
    return "\n".join(f"{prefix}{line}" for line in text.splitlines())


def review_prompt(files: list[str], check_text: str = "") -> str:
    file_list = "\n".join(f"- {path}" for path in files)
    check_section = f"\n\n{check_text}\n" if check_text else ""
    return (
        "Review the current uncommitted code changes in this repository.\n"
        "Focus on concrete bugs, security risks, behavior regressions, broken contracts, "
        "and missing tests.\n"
        "Use the local verification results below as evidence. Do not modify files. "
        "Return findings first with file and line references when possible. "
        "If there are no issues, say that clearly.\n\n"
        "Changed code files:\n"
        f"{file_list}\n"
        f"{check_section}"
    )


def run_review(
    payload: object,
    *,
    state_dir: str | Path = DEFAULT_STATE_DIR,
    codex_bin: str = "codex",
    dry_run: bool = False,
    run_local_checks: bool = True,
    timeout: int = 240,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run a nested Codex review once for a pending Stop hook marker."""

    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr

    if (
        is_review_active()
        or _field(payload, "hook_event_name") != "Stop"
        or _field(payload, "stop_hook_active")
    ):
        return 0

    cwd = str(_field(payload, "cwd", ""))
    marker = load_marker(cwd, state_dir)
    if marker is None:
        return 0

    files = code_files(changed_files(cwd), state_dir)
    if not files:
        clear_marker(cwd, state_dir)
        return 0

    checks = discover_checks(cwd, files)
    if dry_run:
        check_text = checks_plan_text(checks)
    elif run_local_checks:
        check_text = check_results_text(run_checks(cwd, checks))
    else:
        check_text = "Local verification checks were disabled."

    prompt = review_prompt(files, check_text=check_text)
    if dry_run:
        print(prompt, file=stdout)
        return 0

    clear_marker(cwd, state_dir)
    env = {**os.environ, ACTIVE_ENV: "1"}
    command = [codex_bin, "exec", "--disable", "unified_exec", "--cd", cwd, prompt]
    try:
        result = subprocess.run(
            command,
            input="",
            text=True,
            capture_output=True,
            env=env,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Codex review hook skipped: {exc}", file=stderr)
        return 0

    if result.stdout:
        print(result.stdout, file=stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, file=stderr, end="" if result.stderr.endswith("\n") else "\n")
    return 0


def _field(payload: object, name: str, default: Any = None) -> Any:
    return getattr(payload, name, default)
