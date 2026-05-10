from fastapi import APIRouter

from backend.services.github_pr_service import prepare_pr_from_run


router = APIRouter()


@router.post("/github/pr/from-run/{run_id}")
def create_pr_from_run(run_id: str):
    return prepare_pr_from_run(run_id)
