from fastapi import APIRouter

from backend.services.playwright_qa_service import run_playwright_tests
from backend.storage.test_run_store import get_latest_test_run, load_test_runs


router = APIRouter()


@router.post("/qa/run-playwright")
def run_playwright_qa():
    result = run_playwright_tests()

    return {
        "message": result.get("summary"),
        "test_result": result
    }


@router.get("/qa/test-runs/latest")
def get_latest_playwright_qa():
    result = get_latest_test_run()

    return {
        "test_result": result
    }


@router.get("/qa/test-runs")
def get_playwright_runs():
    runs = load_test_runs()

    return {
        "total_runs": len(runs),
        "test_runs": runs
    }
