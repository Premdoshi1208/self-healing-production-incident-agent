from fastapi import APIRouter

from backend.services.patch_apply_service import apply_unified_diff_to_workspace
from backend.services.patch_artifact_service import list_patch_artifacts, read_patch_artifact
from backend.storage.run_store import get_workflow_run, update_workflow_run


router = APIRouter()


@router.get("/patches")
def get_patches():
    artifacts = list_patch_artifacts()

    return {
        "total_patches": len(artifacts),
        "patches": artifacts,
    }


@router.post("/patches/apply/{run_id}")
def apply_patch_from_run(run_id: str):
    run = get_workflow_run(run_id)

    if not run:
        return {
            "status": "not_found",
            "message": f"No workflow run found for run_id={run_id}.",
        }

    existing_result = run.get("patch_apply_result") or {}
    if existing_result.get("applied"):
        return {
            "status": "already_applied",
            "patch_apply_result": existing_result,
        }

    real_patch = run.get("real_patch") or {}
    unified_diff = real_patch.get("unified_diff") or run.get("unified_diff") or run.get("code_patch")
    result = apply_unified_diff_to_workspace(unified_diff, run_id=run_id)
    updated_run = update_workflow_run(run_id, {"patch_apply_result": result})

    return {
        "status": "applied" if result.get("applied") else "failed",
        "patch_apply_result": result,
        "run": updated_run,
    }


@router.get("/patches/{filename}")
def get_patch(filename: str):
    artifact = read_patch_artifact(filename)

    if not artifact:
        return {
            "error": "Patch artifact not found",
            "filename": filename,
        }

    return artifact
