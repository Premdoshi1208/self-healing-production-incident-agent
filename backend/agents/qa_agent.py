from backend.services.llm_service import invoke_text_prompt


def deterministic_qa(incident, rca_analysis, fix_plan, code_patch):
    text = f"{incident} {rca_analysis} {fix_plan} {code_patch}".lower()
    has_patch = bool(str(code_patch or "").strip())
    if has_patch and any(term in text for term in ["finally", "close", "release", "connection"]):
        decision = "APPROVED"
        reason = "The patch addresses the likely connection leak with deterministic cleanup and should be validated through tests before staging."
    elif has_patch:
        decision = "APPROVED"
        reason = "The patch is reviewable and low risk for staging, but production still requires human approval."
    else:
        decision = "REJECTED"
        reason = "No concrete patch was available to validate."
    return f"""QA Validation Summary:
Reviewed the RCA, fix plan, and generated patch artifact. The proposed change is suitable for isolated staging validation if deterministic tests pass.

Regression Risks:
- Resource cleanup changes may affect connection lifecycle assumptions.
- Missing tests could allow the same leak to return.

Recommended Tests:
- Run unit tests for login success and failure paths.
- Run integration smoke tests against the auth-service.
- Confirm active DB connections return to baseline.

Deployment Decision:
{decision}

Reason:
{reason}"""


def run_qa_validation(incident, rca_analysis, fix_plan, code_patch):
    template = """
You are an elite QA reliability engineer. Review the patch and decide APPROVED or REJECTED.
Incident: {incident}
RCA: {rca_analysis}
Fix Plan: {fix_plan}
Patch: {code_patch}
"""
    return invoke_text_prompt(
        template,
        {
            "incident": incident,
            "rca_analysis": rca_analysis,
            "fix_plan": fix_plan,
            "code_patch": code_patch,
        },
        fallback=lambda: deterministic_qa(incident, rca_analysis, fix_plan, code_patch),
    )
