import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from backend.agents.codebase_search_agent import get_codebase_configuration


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_DIR = PROJECT_ROOT / "patch_workspaces"
IGNORE_PATTERNS = shutil.ignore_patterns(
    ".git",
    ".next",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "*.pyc",
)


def _workspace_name(run_id=None):
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_run = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(run_id or "run"))[:80]
    return f"{timestamp}-{safe_run}"


def _changed_files_from_diff(unified_diff):
    changed_files = []

    for line in unified_diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                changed_files.append(parts[3].replace("b/", "", 1))

    return changed_files


def _run_apply_command(command, cwd):
    return subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=30,
    )


def apply_unified_diff_to_workspace(unified_diff, run_id=None):
    if not unified_diff or not unified_diff.strip():
        return {
            "applied": False,
            "workspace_path": None,
            "changed_files": [],
            "error": "No unified diff was provided.",
            "skipped": True,
        }

    config = get_codebase_configuration()

    if config.get("mode") != "local":
        return {
            "applied": False,
            "workspace_path": None,
            "changed_files": _changed_files_from_diff(unified_diff),
            "error": "Patch apply skipped: CODEBASE_LOCAL_PATH is not configured for local mode.",
            "skipped": True,
        }

    source_path = Path(config.get("local_path", ""))

    if not source_path.exists() or not source_path.is_dir():
        return {
            "applied": False,
            "workspace_path": None,
            "changed_files": _changed_files_from_diff(unified_diff),
            "error": f"Patch apply skipped: local codebase path does not exist: {source_path}",
            "skipped": True,
        }

    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    workspace_path = WORKSPACE_DIR / _workspace_name(run_id)

    try:
        shutil.copytree(str(source_path), str(workspace_path), ignore=IGNORE_PATTERNS)
    except Exception as error:
        return {
            "applied": False,
            "workspace_path": str(workspace_path),
            "changed_files": _changed_files_from_diff(unified_diff),
            "error": f"Unable to copy codebase to patch workspace: {type(error).__name__}: {error}",
        }

    patch_file = workspace_path / "generated.patch"
    patch_file.write_text(unified_diff, encoding="utf-8")

    changed_files = _changed_files_from_diff(unified_diff)
    attempts = []

    commands = [
        ["git", "apply", "--whitespace=nowarn", "generated.patch"],
        ["patch", "-p1", "-i", "generated.patch"],
    ]

    for command in commands:
        try:
            completed = _run_apply_command(command, workspace_path)
        except FileNotFoundError as error:
            attempts.append(
                {
                    "command": " ".join(command),
                    "exit_code": None,
                    "stderr": str(error),
                }
            )
            continue
        except subprocess.TimeoutExpired as error:
            attempts.append(
                {
                    "command": " ".join(command),
                    "exit_code": None,
                    "stderr": f"Timed out: {error}",
                }
            )
            continue

        attempts.append(
            {
                "command": " ".join(command),
                "exit_code": completed.returncode,
                "stdout": completed.stdout[-4000:],
                "stderr": completed.stderr[-4000:],
            }
        )

        if completed.returncode == 0:
            return {
                "applied": True,
                "workspace_path": str(workspace_path.relative_to(PROJECT_ROOT)),
                "changed_files": changed_files,
                "apply_command": " ".join(command),
                "attempts": attempts,
            }

    return {
        "applied": False,
        "workspace_path": str(workspace_path.relative_to(PROJECT_ROOT)),
        "changed_files": changed_files,
        "error": "Unable to apply unified diff in isolated workspace.",
        "attempts": attempts,
    }
