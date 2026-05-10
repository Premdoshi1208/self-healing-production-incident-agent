from backend.services.llm_service import invoke_text_prompt


def deterministic_fix_plan(incident, rca_analysis):
    combined = f"{incident} {rca_analysis}".lower()
    if any(term in combined for term in ["database", "db", "connection", "session", "pool"]):
        return """Fix Plan:
Stop the database connection leak in the login/auth path and validate that every connection is released.

Engineering Changes:
- Wrap DB usage in try/finally or a context manager.
- Close/release the connection in all success, invalid-user, invalid-password, timeout, and exception paths.
- Add connection lifecycle logging and active pool metrics.

Deployment Risks:
- Incorrect cleanup could close connections too early.
- Pool configuration changes could hide the real leak if used as the only fix.

Rollback Strategy:
- Revert the login/db cleanup patch.
- Keep temporary rate limiting or pool-size mitigation if needed.

Required Tests:
- Successful login closes the connection.
- Unknown user closes the connection.
- Bad password closes the connection.
- Forced DB error path closes the connection.
- Load test confirms active connections return to baseline."""
    if "frontend" in combined or "undefined" in combined:
        return """Fix Plan:
Add defensive null guards and fallback UI around profile/dashboard rendering.

Engineering Changes:
- Validate API response shape before rendering.
- Use optional chaining/default values for missing profile fields.
- Add an error boundary for the dashboard component.

Deployment Risks:
- Fallback UI may hide upstream API bugs if not logged.

Rollback Strategy:
- Revert component guard changes.

Required Tests:
- Render with complete profile.
- Render with missing profile.
- Render with null nested fields."""
    return """Fix Plan:
Apply the smallest safe remediation, add regression tests, and deploy only through staging.

Engineering Changes:
- Patch the suspected failure path.
- Add observability around the suspected component.

Deployment Risks:
- Unknown regression risk due to limited telemetry.

Rollback Strategy:
- Revert patch and restore previous configuration.

Required Tests:
- Unit, integration, and smoke tests for the impacted service."""


def generate_fix_plan(incident, rca_analysis):
    template = """
You are an elite production reliability engineer. Create a safe remediation plan.
Incident: {incident}
RCA: {rca_analysis}
"""
    return invoke_text_prompt(
        template,
        {"incident": incident, "rca_analysis": rca_analysis},
        fallback=lambda: deterministic_fix_plan(incident, rca_analysis),
    )
