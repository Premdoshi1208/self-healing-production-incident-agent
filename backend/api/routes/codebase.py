import os
from pathlib import Path

from fastapi import APIRouter, Body

from backend.agents.codebase_search_agent import (
    IGNORED_DIRS,
    get_codebase_configuration,
    search_codebase_for_incident,
)


router = APIRouter()


def _estimate_file_count(root_path, max_count=10000):
    root = Path(root_path)

    if not root.exists() or not root.is_dir():
        return 0

    count = 0

    for _, dirs, files in os.walk(str(root)):
        dirs[:] = [directory for directory in dirs if directory not in IGNORED_DIRS]
        count += len(files)

        if count >= max_count:
            return count

    return count


@router.get("/codebase/status")
def get_codebase_status():
    config = get_codebase_configuration()
    file_count = 0

    if config.get("mode") == "local" and config.get("local_path_exists"):
        file_count = _estimate_file_count(config.get("local_path"))

    return {
        "mode": config.get("mode"),
        "local_path": config.get("local_path"),
        "local_path_exists": config.get("local_path_exists", False),
        "github_repo": config.get("github_repo"),
        "github_default_branch": config.get("github_default_branch"),
        "github_token_configured": config.get("github_token_configured", False),
        "file_count_estimate": file_count,
        "enabled": config.get("mode") in ["local", "github"],
    }


@router.post("/codebase/search")
def search_codebase(payload: dict = Body(default={})):
    incident = payload.get("incident") or {
        "title": payload.get("title"),
        "service": payload.get("service"),
        "description": payload.get("description"),
        "logs": payload.get("logs"),
        "trace_summary": payload.get("trace_summary"),
        "metrics": payload.get("metrics"),
    }
    rca_analysis = payload.get("rca_analysis") or payload.get("rca") or ""

    return search_codebase_for_incident(incident, rca_analysis)
