import json
import uuid
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path

RUN_HISTORY_FILE = Path(__file__).resolve().parent / "workflow_runs.json"


def _backup_corrupt_file(path):
    if not path.exists():
        return

    backup_path = path.with_suffix(
        path.suffix + f".corrupt-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    )
    path.replace(backup_path)


def load_workflow_runs():
    if not RUN_HISTORY_FILE.exists():
        return []

    try:
        with open(RUN_HISTORY_FILE, "r") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (JSONDecodeError, OSError):
        _backup_corrupt_file(RUN_HISTORY_FILE)
        return []


def save_workflow_run(workflow_result):
    runs = load_workflow_runs()
    run_id = workflow_result.get("run_id") or str(uuid.uuid4())

    stored_run = {
        "run_id": run_id,
        "created_at": workflow_result.get("created_at") or str(datetime.utcnow()),

        "incident_id": workflow_result.get("incident_id"),
        "incident_title": workflow_result.get("incident_title"),
        "service": workflow_result.get("service"),
        "severity": workflow_result.get("severity"),
        "status": workflow_result.get("status"),

        "retrieved_memories": workflow_result.get("retrieved_memories", []),

        "rca_analysis": workflow_result.get("rca_analysis"),
        "fix_plan": workflow_result.get("fix_plan"),
        "code_patch": workflow_result.get("code_patch"),
        "codebase_search": workflow_result.get("codebase_search"),
        "code_context": workflow_result.get("code_context"),
        "real_patch": workflow_result.get("real_patch"),
        "patch_apply_result": workflow_result.get("patch_apply_result"),
        "patch_applied": workflow_result.get("patch_applied", False),
        "test_result": workflow_result.get("test_result"),
        "qa_validation": workflow_result.get("qa_validation"),
        "playwright_test_result": workflow_result.get("playwright_test_result"),

        "evaluation": workflow_result.get("evaluation"),
        "deploy_gate": workflow_result.get("deploy_gate"),
        "observability": workflow_result.get("observability"),

        "memory_saved": workflow_result.get("memory_saved", False),
        "memory_entry": workflow_result.get("memory_entry"),
        "patch_file_path": workflow_result.get("patch_file_path"),
        "error": workflow_result.get("error")
    }

    runs.append(stored_run)

    RUN_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RUN_HISTORY_FILE, "w") as file:
        json.dump(runs, file, indent=4)

    return stored_run


def get_recent_workflow_runs(limit=5):
    runs = load_workflow_runs()
    return runs[-limit:]


def get_all_workflow_runs():
    return load_workflow_runs()


def get_workflow_run(run_id):
    for run in load_workflow_runs():
        if run.get("run_id") == run_id:
            return run

    return None


def update_workflow_run(run_id, updates):
    runs = load_workflow_runs()
    updated_run = None

    for index, run in enumerate(runs):
        if run.get("run_id") == run_id:
            updated_run = dict(run)
            updated_run.update(updates)
            runs[index] = updated_run
            break

    if updated_run is None:
        return None

    RUN_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RUN_HISTORY_FILE, "w") as file:
        json.dump(runs, file, indent=4)

    return updated_run
