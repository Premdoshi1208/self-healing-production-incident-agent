import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from backend.storage.test_run_store import save_test_run


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def _parse_playwright_output(stdout):
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        start_index = stdout.find("{")

        if start_index == -1:
            return None

        try:
            return json.loads(stdout[start_index:])
        except json.JSONDecodeError:
            return None


def run_playwright_tests(timeout_seconds=120):
    started_at = datetime.utcnow()

    result = {
        "test_run_id": str(uuid.uuid4()),
        "started_at": str(started_at),
        "finished_at": None,
        "status": "failed",
        "command": "npm run test:e2e -- --reporter=json",
        "summary": "",
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "parsed_report": None
    }

    try:
        completed = subprocess.run(
            ["npm", "run", "test:e2e", "--", "--reporter=json"],
            cwd=str(FRONTEND_DIR),
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )

        result["exit_code"] = completed.returncode
        result["stdout"] = completed.stdout[-12000:]
        result["stderr"] = completed.stderr[-12000:]
        result["parsed_report"] = _parse_playwright_output(completed.stdout)
        result["status"] = "passed" if completed.returncode == 0 else "failed"
        result["summary"] = (
            "Playwright tests passed."
            if completed.returncode == 0
            else "Playwright tests failed. See stdout/stderr for details."
        )
    except subprocess.TimeoutExpired as error:
        result["status"] = "failed"
        result["summary"] = f"Playwright tests timed out after {timeout_seconds}s."
        result["stdout"] = (error.stdout or "")[-12000:]
        result["stderr"] = (error.stderr or "")[-12000:]
    except FileNotFoundError as error:
        result["status"] = "failed"
        result["summary"] = f"Unable to run Playwright tests: {error}"
    except Exception as error:
        result["status"] = "failed"
        result["summary"] = f"Unexpected Playwright runner error: {type(error).__name__}: {error}"
    finally:
        result["finished_at"] = str(datetime.utcnow())

    return save_test_run(result)
