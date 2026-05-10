import json
import time
import uuid
from datetime import datetime

from backend.agents.codebase_search_agent import search_codebase_for_incident
from backend.agents.rca_agent import analyze_incident
from backend.agents.fix_planner_agent import generate_fix_plan
from backend.agents.real_patch_agent import generate_real_patch
from backend.agents.qa_agent import run_qa_validation

from backend.services.code_context_service import build_code_context
from backend.services.patch_apply_service import apply_unified_diff_to_workspace
from backend.services.patch_artifact_service import save_patch_artifact
from backend.services.test_runner_service import run_tests_for_workspace

from backend.memory.reflexion_memory import create_reflexion_memory
from backend.memory.retrieve_memory import retrieve_similar_memories

from backend.evaluation.incident_evaluator import evaluate_incident_response

from backend.storage.run_store import save_workflow_run
from backend.storage.approval_store import create_pending_approval
from backend.storage.test_run_store import get_latest_test_run

from backend.core.deploy_gate import evaluate_deploy_gate

from backend.observability.metrics import (
    record_workflow_run,
    record_memory_save,
    record_deploy_gate_decision,
    WORKFLOW_DURATION_SECONDS
)


def get_agent_visible_incident(incident):
    return {
        "id": incident.get("id", int(time.time())),
        "title": incident.get("title", "Untitled production incident"),
        "severity": incident.get("severity", "unknown"),
        "service": incident.get("service", "unknown-service"),
        "description": incident.get("description", "No description provided."),
        "metrics": incident.get("metrics", {}),
        "logs": incident.get("logs", []),
        "trace_summary": incident.get("trace_summary", [])
    }


def build_failed_evaluation(error):
    return {
        "evaluated": False,
        "overall_score": 0.0,
        "verdict": "FAIL",
        "reason": "Workflow failed before a successful evaluation could be completed.",
        "error": error
    }


def build_failed_deploy_gate(error, test_result=None):
    return {
        "staging_allowed": False,
        "production_allowed": False,
        "production_requires_human": True,
        "policy_engine": "deterministic_deploy_gate",
        "blocking_reasons": [
            f"Workflow failed: {error.get('message', 'unknown error')}"
        ],
        "test_result_considered": bool(test_result),
        "decision_summary": (
            "Patch is blocked because the workflow failed. "
            "Production deployment still requires explicit human approval."
        )
    }


def run_incident_workflow(incident):
    start_time = time.time()
    run_id = str(uuid.uuid4())
    created_at = str(datetime.utcnow())

    safe_incident = get_agent_visible_incident(incident)

    workflow_result = {
        "run_id": run_id,
        "created_at": created_at,
        "incident_id": safe_incident["id"],
        "incident_title": safe_incident["title"],
        "service": safe_incident["service"],
        "severity": safe_incident["severity"],
        "status": "investigating"
    }

    print("\n")
    print("=" * 80)
    print("STARTING INCIDENT WORKFLOW")
    print("=" * 80)

    print("\n")
    print("=" * 80)
    print("[STEP 0] RETRIEVING SIMILAR MEMORIES")
    print("=" * 80)

    try:
        retrieved_memories = retrieve_similar_memories(safe_incident)
        workflow_result["retrieved_memories"] = retrieved_memories

        if retrieved_memories:
            print("\nRetrieved Similar Memories:\n")
            for memory in retrieved_memories:
                print(f"- {memory['incident_title']} ({memory['service']})")
        else:
            print("\nNo similar memories found.")

        print("\n")
        print("=" * 80)
        print("[STEP 1] RUNNING RCA AGENT")
        print("=" * 80)

        rca_result = analyze_incident(safe_incident)
        workflow_result["rca_analysis"] = rca_result

        print("\n")
        print(rca_result)

        print("\n")
        print("=" * 80)
        print("[STEP 2] RUNNING FIX PLANNER AGENT")
        print("=" * 80)

        fix_plan_result = generate_fix_plan(
            safe_incident,
            rca_result
        )

        workflow_result["fix_plan"] = fix_plan_result

        print("\n")
        print(fix_plan_result)

        print("\n")
        print("=" * 80)
        print("[STEP 3] RUNNING CODEBASE SEARCH AGENT")
        print("=" * 80)

        try:
            codebase_search_result = search_codebase_for_incident(
                safe_incident,
                rca_result
            )
        except Exception as search_error:
            codebase_search_result = {
                "status": "skipped",
                "mode": "error",
                "skipped_reason": (
                    "codebase analysis skipped: "
                    f"{type(search_error).__name__}: {search_error}"
                ),
                "suspected_files": []
            }

        workflow_result["codebase_search"] = codebase_search_result

        print("\n")
        print(codebase_search_result)

        print("\n")
        print("=" * 80)
        print("[STEP 4] BUILDING COMPACT CODE CONTEXT")
        print("=" * 80)

        try:
            code_context_result = build_code_context(codebase_search_result)
        except Exception as context_error:
            code_context_result = {
                "status": "skipped",
                "skipped_reason": (
                    "code context skipped: "
                    f"{type(context_error).__name__}: {context_error}"
                ),
                "files": []
            }

        workflow_result["code_context"] = code_context_result

        print("\n")
        print(code_context_result)

        print("\n")
        print("=" * 80)
        print("[STEP 5] GENERATING REAL PATCH DIFF")
        print("=" * 80)

        real_patch_result = generate_real_patch(
            safe_incident,
            rca_result,
            fix_plan_result,
            codebase_search_result,
            code_context_result
        )

        workflow_result["real_patch"] = real_patch_result

        code_patch_result = (
            real_patch_result.get("unified_diff")
            or "Patch recommendation only:\n"
            + json.dumps(real_patch_result, indent=2)
        )
        workflow_result["code_patch"] = code_patch_result

        print("\n")
        print(code_patch_result)

        print("\n")
        print("=" * 80)
        print("[STEP 6] APPLYING PATCH IN SAFE WORKSPACE")
        print("=" * 80)

        try:
            patch_apply_result = apply_unified_diff_to_workspace(
                real_patch_result.get("unified_diff"),
                run_id=run_id
            )
        except Exception as patch_apply_error:
            patch_apply_result = {
                "applied": False,
                "workspace_path": None,
                "changed_files": real_patch_result.get("affected_files", []),
                "error": f"{type(patch_apply_error).__name__}: {patch_apply_error}"
            }

        workflow_result["patch_apply_result"] = patch_apply_result
        workflow_result["patch_applied"] = bool(patch_apply_result.get("applied"))

        print("\n")
        print(patch_apply_result)

        print("\n")
        print("=" * 80)
        print("[STEP 7] RUNNING DETERMINISTIC TESTS")
        print("=" * 80)

        try:
            test_result = run_tests_for_workspace(
                patch_apply_result.get("workspace_path") if patch_apply_result.get("applied") else None,
                run_id=run_id
            )
        except Exception as test_error:
            test_result = {
                "run_id": run_id,
                "tests_run": False,
                "passed": False,
                "status": "failed",
                "command": "",
                "stdout": "",
                "stderr": f"{type(test_error).__name__}: {test_error}",
                "duration_seconds": 0.0,
                "summary": "Test runner failed before executing tests."
            }

        workflow_result["test_result"] = test_result
        workflow_result["playwright_test_result"] = get_latest_test_run()

        print("\n")
        print(test_result)

        print("\n")
        print("=" * 80)
        print("[STEP 8] RUNNING QA VALIDATION AGENT")
        print("=" * 80)

        qa_result = run_qa_validation(
            safe_incident,
            rca_result,
            fix_plan_result,
            code_patch_result
        )

        workflow_result["qa_validation"] = qa_result

        print("\n")
        print(qa_result)

        print("\n")
        print("=" * 80)
        print("[STEP 9] EVALUATING AGENT PERFORMANCE")
        print("=" * 80)

        evaluation_result = evaluate_incident_response(
            incident,
            rca_result,
            fix_plan_result,
            qa_result
        )

        workflow_result["evaluation"] = evaluation_result

        print("\n")
        print(evaluation_result)

        print("\n")
        print("=" * 80)
        print("[STEP 10] RUNNING DETERMINISTIC DEPLOY GATE")
        print("=" * 80)

        deploy_gate_result = evaluate_deploy_gate(
            safe_incident,
            qa_result,
            evaluation_result,
            test_result=test_result,
            patch_apply_result=patch_apply_result,
            real_patch=real_patch_result
        )

        workflow_result["deploy_gate"] = deploy_gate_result

        print("\n")
        print(deploy_gate_result)

        print("\n")
        print("=" * 80)
        print("[STEP 11] SAVING REFLEXION MEMORY")
        print("=" * 80)

        memory_result = create_reflexion_memory(
            safe_incident,
            rca_result,
            fix_plan_result,
            qa_result
        )

        workflow_result["memory_saved"] = True
        workflow_result["memory_entry"] = memory_result

        print("\nMemory successfully saved.")
        workflow_result["status"] = "completed"
    except Exception as error:
        error_details = {
            "type": type(error).__name__,
            "message": str(error)
        }

        workflow_result["status"] = "failed"
        workflow_result["error"] = error_details
        workflow_result["evaluation"] = workflow_result.get("evaluation") or build_failed_evaluation(error_details)
        workflow_result["test_result"] = workflow_result.get("test_result") or get_latest_test_run()
        workflow_result["playwright_test_result"] = workflow_result.get("playwright_test_result") or get_latest_test_run()
        workflow_result["deploy_gate"] = workflow_result.get("deploy_gate") or build_failed_deploy_gate(
            error_details,
            workflow_result.get("test_result") or workflow_result.get("playwright_test_result")
        )

    print("\n")
    print("=" * 80)
    print("[STEP 12] RECORDING PROMETHEUS METRICS")
    print("=" * 80)

    evaluation_result = workflow_result.get("evaluation") or {}
    deploy_gate_result = workflow_result.get("deploy_gate") or {}
    verdict = evaluation_result.get("verdict", "NOT_EVALUATED")
    duration_seconds = round(time.time() - start_time, 2)

    try:
        record_workflow_run(
            service=safe_incident["service"],
            severity=safe_incident["severity"],
            verdict=verdict
        )

        if workflow_result.get("memory_saved"):
            record_memory_save(
                service=safe_incident["service"]
            )

        record_deploy_gate_decision(
            service=safe_incident["service"],
            severity=safe_incident["severity"],
            deploy_gate_result=deploy_gate_result
        )

        WORKFLOW_DURATION_SECONDS.labels(
            service=safe_incident["service"],
            severity=safe_incident["severity"]
        ).observe(duration_seconds)

        workflow_result["observability"] = {
            "metrics_recorded": True,
            "duration_seconds": duration_seconds,
            "verdict": verdict,
            "deploy_gate_metrics_recorded": True
        }

        print("\nPrometheus metrics recorded.")
    except Exception as metrics_error:
        workflow_result["observability"] = {
            "metrics_recorded": False,
            "duration_seconds": duration_seconds,
            "verdict": verdict,
            "error": f"{type(metrics_error).__name__}: {metrics_error}"
        }

    print(f"Duration: {duration_seconds}s")
    print(f"Verdict: {verdict}")

    print("\n")
    print("=" * 80)
    print("[STEP 13] SAVING PATCH ARTIFACT AND WORKFLOW RUN HISTORY")
    print("=" * 80)

    try:
        workflow_result["patch_file_path"] = save_patch_artifact(workflow_result)
    except Exception as patch_error:
        workflow_result["patch_file_error"] = f"{type(patch_error).__name__}: {patch_error}"

    stored_run = save_workflow_run(workflow_result)

    workflow_result["stored_run"] = {
        "run_id": stored_run["run_id"],
        "created_at": stored_run["created_at"]
    }

    workflow_result["approval"] = create_pending_approval(
        stored_run["run_id"],
        comment="Production deployment requires human approval."
    )

    print("\nWorkflow run saved successfully.")
    print(f"Run ID: {stored_run['run_id']}")

    print("\n")
    print("=" * 80)
    print("WORKFLOW COMPLETED")
    print("=" * 80)

    return workflow_result
