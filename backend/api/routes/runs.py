from fastapi import APIRouter

from backend.storage.run_store import (
    get_all_workflow_runs,
    get_recent_workflow_runs,
    get_workflow_run
)
from backend.storage.approval_store import get_approval_for_run

router = APIRouter()


def attach_approvals(runs):
    enriched_runs = []

    for run in runs:
        enriched_run = dict(run)
        enriched_run["approval"] = get_approval_for_run(run.get("run_id"))
        enriched_runs.append(enriched_run)

    return enriched_runs


@router.get("/runs")
def get_all_runs():
    runs = get_all_workflow_runs()

    return {
        "total_runs": len(runs),
        "runs": attach_approvals(runs)
    }


@router.get("/runs/recent")
def get_recent_runs():
    runs = get_recent_workflow_runs(limit=5)

    return {
        "total_returned": len(runs),
        "runs": attach_approvals(runs)
    }


@router.get("/runs/summary")
def get_runs_summary():
    runs = get_all_workflow_runs()

    total_runs = len(runs)

    if total_runs == 0:
        return {
            "total_runs": 0,
            "pass_count": 0,
            "partial_count": 0,
            "fail_count": 0,
            "average_score": 0.0,
            "deploy_gate_decisions": 0,
            "patch_applied_count": 0,
            "tests_passed_count": 0
        }

    pass_count = 0
    partial_count = 0
    fail_count = 0
    deploy_gate_decisions = 0
    patch_applied_count = 0
    tests_passed_count = 0
    total_score = 0.0
    scored_runs = 0

    for run in runs:
        evaluation = run.get("evaluation") or {}
        deploy_gate = run.get("deploy_gate") or {}
        patch_apply_result = run.get("patch_apply_result") or {}
        test_result = run.get("test_result") or {}

        verdict = evaluation.get("verdict")
        score = evaluation.get("overall_score")

        if verdict == "PASS":
            pass_count += 1
        elif verdict == "PARTIAL":
            partial_count += 1
        elif verdict == "FAIL":
            fail_count += 1

        if score is not None:
            total_score += score
            scored_runs += 1

        if deploy_gate:
            deploy_gate_decisions += 1

        if patch_apply_result.get("applied"):
            patch_applied_count += 1

        if test_result.get("passed") or test_result.get("status") == "passed":
            tests_passed_count += 1

    average_score = 0.0

    if scored_runs > 0:
        average_score = round(total_score / scored_runs, 2)

    return {
        "total_runs": total_runs,
        "pass_count": pass_count,
        "partial_count": partial_count,
        "fail_count": fail_count,
        "average_score": average_score,
        "deploy_gate_decisions": deploy_gate_decisions,
        "patch_applied_count": patch_applied_count,
        "tests_passed_count": tests_passed_count
    }

@router.get("/runs/{run_id}")
def get_run(run_id: str):
    run = get_workflow_run(run_id)

    if not run:
        return {
            "error": "Run not found"
        }

    enriched_run = dict(run)
    enriched_run["approval"] = get_approval_for_run(run_id)

    return {
        "run": enriched_run
    }
