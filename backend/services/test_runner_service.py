import json
import importlib.util
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

from backend.storage.test_run_store import save_test_run


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_workspace(workspace_path):
    if not workspace_path:
        return None

    path = Path(workspace_path)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path


def _select_test_command(workspace):
    if not workspace or not workspace.exists():
        return None, "No patch workspace exists."

    if (workspace / "pytest.ini").exists() or (workspace / "pyproject.toml").exists() or (workspace / "tests").exists():
        if importlib.util.find_spec("pytest") is None:
            simple_runner = PROJECT_ROOT / "backend" / "services" / "simple_pytest_runner.py"
            return [sys.executable, str(simple_runner)], "simple pytest-compatible runner"

        return [sys.executable, "-m", "pytest", "-q"], "pytest"

    package_json = workspace / "package.json"
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            scripts = data.get("scripts", {})
            if "test" in scripts:
                return ["npm", "test", "--", "--watch=false"], "npm test"
            if "test:e2e" in scripts or (workspace / "playwright.config.js").exists():
                return ["npm", "run", "test:e2e"], "playwright"
        except (json.JSONDecodeError, OSError):
            return ["npm", "test", "--", "--watch=false"], "npm test"

    python_files = list(workspace.rglob("*.py"))
    if python_files:
        return [sys.executable, "-m", "compileall", "-q", "."], "python syntax check"

    return None, "No supported deterministic test command found."


def run_tests_for_workspace(workspace_path, run_id=None, timeout_seconds=120):
    started_at = datetime.utcnow()
    start_time = time.time()
    workspace = _resolve_workspace(workspace_path)
    command, runner = _select_test_command(workspace)

    result = {
        "test_run_id": str(uuid.uuid4()),
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "finished_at": None,
        "tests_run": False,
        "runner": runner,
        "command": " ".join(command) if command else "",
        "passed": False,
        "status": "skipped",
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "duration_seconds": 0.0,
        "workspace_path": str(workspace_path) if workspace_path else None,
    }

    if not command:
        result["summary"] = runner
        result["finished_at"] = datetime.utcnow().isoformat()
        result["duration_seconds"] = round(time.time() - start_time, 2)
        return save_test_run(result)

    try:
        completed = subprocess.run(
            command,
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )

        result["tests_run"] = True
        result["exit_code"] = completed.returncode
        result["stdout"] = completed.stdout[-12000:]
        result["stderr"] = completed.stderr[-12000:]
        result["passed"] = completed.returncode == 0
        result["status"] = "passed" if result["passed"] else "failed"
        result["summary"] = "Deterministic tests passed." if result["passed"] else "Deterministic tests failed."
    except subprocess.TimeoutExpired as error:
        result["tests_run"] = True
        result["status"] = "failed"
        result["summary"] = f"Tests timed out after {timeout_seconds}s."
        result["stdout"] = (error.stdout or "")[-12000:]
        result["stderr"] = (error.stderr or "")[-12000:]
    except FileNotFoundError as error:
        result["status"] = "failed"
        result["summary"] = f"Unable to run tests: {error}"
        result["stderr"] = str(error)
    except Exception as error:
        result["status"] = "failed"
        result["summary"] = f"Unexpected test runner error: {type(error).__name__}: {error}"
        result["stderr"] = str(error)
    finally:
        result["finished_at"] = datetime.utcnow().isoformat()
        result["duration_seconds"] = round(time.time() - start_time, 2)

    return save_test_run(result)
