import json
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path

MEMORY_FILE = Path(__file__).resolve().parent / "reflexion_store.json"


def _backup_corrupt_file(path):
    if not path.exists():
        return

    backup_path = path.with_suffix(
        path.suffix + f".corrupt-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    )
    path.replace(backup_path)


def load_memories():
    if not MEMORY_FILE.exists():
        return []

    try:
        with open(MEMORY_FILE, "r") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (JSONDecodeError, OSError):
        _backup_corrupt_file(MEMORY_FILE)
        return []


def save_memory(memory_entry):
    memories = load_memories()
    memories.append(memory_entry)

    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, "w") as file:
        json.dump(memories, file, indent=4)


def create_reflexion_memory(
    incident,
    rca_analysis,
    fix_plan,
    qa_validation
):
    memory_entry = {
        "timestamp": str(datetime.utcnow()),
        "incident_title": incident["title"],
        "service": incident["service"],
        "severity": incident["severity"],

        "learning_summary": (
            f"Resolved incident involving "
            f"{incident['title']} using structured "
            f"RCA, remediation planning, "
            f"and QA validation."
        ),

        "important_signals": {
            "logs": incident["logs"],
            "metrics": incident["metrics"],
            "trace_summary": incident["trace_summary"]
        },

        "rca_analysis": rca_analysis,
        "fix_plan": fix_plan,
        "qa_validation": qa_validation
    }

    save_memory(memory_entry)

    return memory_entry
