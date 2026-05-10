import os

from backend.storage.run_store import get_workflow_run


def prepare_pr_from_run(run_id):
    enabled = os.getenv("ENABLE_GITHUB_PR", "false").lower() == "true"
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    default_branch = os.getenv("GITHUB_DEFAULT_BRANCH", "main")
    run = get_workflow_run(run_id)

    if not run:
        return {
            "enabled": False,
            "status": "not_found",
            "message": f"No workflow run found for run_id={run_id}."
        }

    if not enabled:
        return {
            "enabled": False,
            "status": "disabled",
            "message": "GitHub PR disabled. Set ENABLE_GITHUB_PR=true to enable PR preparation.",
            "run_id": run_id,
            "patch_file_path": run.get("patch_file_path"),
        }

    if not token or not repo:
        return {
            "enabled": False,
            "status": "disabled",
            "message": "GitHub PR disabled. Set GITHUB_TOKEN and GITHUB_REPO to enable PR preparation.",
            "run_id": run_id,
            "patch_file_path": run.get("patch_file_path")
        }

    branch_name = f"ai-sre/{run_id[:8]}"
    incident_title = run.get("incident_title") or "incident remediation"
    service = run.get("service") or "unknown-service"
    severity = run.get("severity") or "unknown"
    deploy_gate = run.get("deploy_gate") or {}

    return {
        "enabled": True,
        "status": "ready_to_create_pr",
        "message": "GitHub credentials detected. PR metadata is prepared, but this demo does not push branches automatically.",
        "repo": repo,
        "default_branch": default_branch,
        "branch_name": branch_name,
        "pr_title": f"[AI SRE] Remediate {incident_title}",
        "pr_body": (
            f"## Incident\n\n"
            f"- Service: {service}\n"
            f"- Severity: {severity}\n"
            f"- Run ID: {run_id}\n\n"
            f"## Deploy Gate\n\n"
            f"- Staging allowed: {deploy_gate.get('staging_allowed', False)}\n"
            f"- Production allowed: {deploy_gate.get('production_allowed', False)}\n"
            f"- Human approval required: {deploy_gate.get('production_requires_human', True)}\n\n"
            f"Patch artifact: `{run.get('patch_file_path')}`\n"
        ),
        "run_id": run_id,
        "patch_file_path": run.get("patch_file_path"),
        "next_steps": [
            "Create a branch from the default branch after human review.",
            "Apply the generated patch artifact to the branch.",
            "Open a pull request with the prepared title and body."
        ]
    }
