import json
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path


TEST_RUNS_FILE = Path(__file__).resolve().parent / "test_runs.json"


def _backup_corrupt_file(path):
    if not path.exists():
        return

    backup_path = path.with_suffix(
        path.suffix + f".corrupt-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    )
    path.replace(backup_path)


def load_test_runs():
    if not TEST_RUNS_FILE.exists():
        return []

    try:
        with open(TEST_RUNS_FILE, "r") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (JSONDecodeError, OSError):
        _backup_corrupt_file(TEST_RUNS_FILE)
        return []


def save_test_run(test_run):
    runs = load_test_runs()
    runs.append(test_run)

    TEST_RUNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TEST_RUNS_FILE, "w") as file:
        json.dump(runs, file, indent=4)

    return test_run


def get_latest_test_run():
    runs = load_test_runs()

    if not runs:
        return None

    return runs[-1]
