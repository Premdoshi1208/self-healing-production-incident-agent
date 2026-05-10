import json
import uuid
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path


APPROVALS_FILE = Path(__file__).resolve().parent / "approvals.json"


def _backup_corrupt_file(path):
    if not path.exists():
        return

    backup_path = path.with_suffix(
        path.suffix + f".corrupt-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    )
    path.replace(backup_path)


def load_approvals():
    if not APPROVALS_FILE.exists():
        return []

    try:
        with open(APPROVALS_FILE, "r") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (JSONDecodeError, OSError):
        _backup_corrupt_file(APPROVALS_FILE)
        return []


def save_approvals(approvals):
    APPROVALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(APPROVALS_FILE, "w") as file:
        json.dump(approvals, file, indent=4)


def get_approval_for_run(run_id):
    approvals = load_approvals()

    for approval in reversed(approvals):
        if approval.get("run_id") == run_id:
            return approval

    return None


def get_pending_approvals():
    return [
        approval
        for approval in load_approvals()
        if approval.get("status") == "pending"
    ]


def create_pending_approval(run_id, reviewer="human-reviewer", comment=""):
    existing = get_approval_for_run(run_id)

    if existing:
        return existing

    approval = {
        "approval_id": str(uuid.uuid4()),
        "run_id": run_id,
        "created_at": str(datetime.utcnow()),
        "updated_at": str(datetime.utcnow()),
        "status": "pending",
        "reviewer": reviewer,
        "comment": comment
    }

    approvals = load_approvals()
    approvals.append(approval)
    save_approvals(approvals)

    return approval


def set_approval_status(run_id, status, reviewer="human-reviewer", comment=""):
    approvals = load_approvals()
    existing_index = None

    for index, approval in enumerate(approvals):
        if approval.get("run_id") == run_id:
            existing_index = index

    if existing_index is None:
        approval = {
            "approval_id": str(uuid.uuid4()),
            "run_id": run_id,
            "created_at": str(datetime.utcnow())
        }
        approvals.append(approval)
        existing_index = len(approvals) - 1

    approvals[existing_index].update({
        "updated_at": str(datetime.utcnow()),
        "status": status,
        "reviewer": reviewer,
        "comment": comment
    })

    save_approvals(approvals)

    return approvals[existing_index]
