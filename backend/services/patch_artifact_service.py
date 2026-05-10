import json
import re
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PATCH_DIR = PROJECT_ROOT / "generated_patches"


def _slugify(value):
    value = str(value or "incident").lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:80] or "incident"


def _format_block(title, content):
    if content is None or content == "":
        content = "Not available."

    if not isinstance(content, str):
        content = json.dumps(content, indent=2)

    return f"## {title}\n\n{content}\n"


def save_patch_artifact(workflow_result):
    PATCH_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    run_id = workflow_result.get("run_id") or workflow_result.get("incident_id") or "run"
    slug = _slugify(workflow_result.get("incident_title"))
    filename = f"{timestamp}-{run_id}-{slug}.md"
    path = PATCH_DIR / filename

    metadata = {
        "run_id": workflow_result.get("run_id"),
        "incident_id": workflow_result.get("incident_id"),
        "incident_title": workflow_result.get("incident_title"),
        "service": workflow_result.get("service"),
        "severity": workflow_result.get("severity"),
        "status": workflow_result.get("status"),
        "created_at": workflow_result.get("created_at"),
        "timestamp": timestamp,
    }

    real_patch = workflow_result.get("real_patch") or {}

    parts = [
        "# Generated Incident Remediation Artifact",
        "",
        "## Metadata",
        "",
        "```json",
        json.dumps(metadata, indent=2),
        "```",
        "",
        _format_block("Incident Title", workflow_result.get("incident_title")),
        _format_block("Service", workflow_result.get("service")),
        _format_block("Severity", workflow_result.get("severity")),
        _format_block("RCA", workflow_result.get("rca_analysis")),
        _format_block("Fix Plan", workflow_result.get("fix_plan")),
        _format_block("Codebase Search Result", workflow_result.get("codebase_search")),
        _format_block("Code Context", workflow_result.get("code_context")),
        _format_block("Real Patch Summary", real_patch.get("patch_summary")),
        _format_block("Generated Unified Diff", real_patch.get("unified_diff") or workflow_result.get("code_patch")),
        _format_block("Patch Apply Result", workflow_result.get("patch_apply_result")),
        _format_block("Test Result", workflow_result.get("test_result")),
        _format_block("QA Validation", workflow_result.get("qa_validation")),
        _format_block("Evaluation", workflow_result.get("evaluation")),
        _format_block("Deploy Gate Result", workflow_result.get("deploy_gate")),
        _format_block("Workflow Error", workflow_result.get("error")),
    ]

    path.write_text("\n".join(parts), encoding="utf-8")

    return str(path.relative_to(PROJECT_ROOT))


def list_patch_artifacts():
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = []

    for path in sorted(PATCH_DIR.glob("*.md"), key=lambda item: item.stat().st_mtime, reverse=True):
        stat = path.stat()
        artifacts.append(
            {
                "filename": path.name,
                "path": str(path.relative_to(PROJECT_ROOT)),
                "size_bytes": stat.st_size,
                "modified_at": datetime.utcfromtimestamp(stat.st_mtime).isoformat(),
            }
        )

    return artifacts


def read_patch_artifact(filename):
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(filename).name
    path = PATCH_DIR / safe_name

    if not path.exists() or not path.is_file():
        return None

    return {
        "filename": safe_name,
        "path": str(path.relative_to(PROJECT_ROOT)),
        "content": path.read_text(encoding="utf-8", errors="ignore"),
    }
