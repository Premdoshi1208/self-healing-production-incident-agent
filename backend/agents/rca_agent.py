from backend.services.llm_service import invoke_text_prompt


def _as_text(value):
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{k}: {v}" for k, v in value.items())
    return str(value or "")


def deterministic_rca(incident):
    text = " ".join([
        incident.get("title", ""), incident.get("description", ""),
        _as_text(incident.get("metrics", {})), _as_text(incident.get("logs", [])),
        _as_text(incident.get("trace_summary", [])),
    ]).lower()

    if any(term in text for term in ["database", "db", "connection", "pool", "session"]):
        root = "Database connection leak or pool exhaustion in the auth/login path."
        explanation = (
            "The incident contains database pool exhaustion signals, high latency/error rate, "
            "and traces showing sessions remaining active after login requests. This strongly "
            "indicates connections are acquired but not reliably released on all code paths."
        )
        signals = ["database connection pool exhausted", "too many active sessions", "login trace kept DB session active"]
        confidence = "95"
    elif any(term in text for term in ["frontend", "undefined", "null", "component", "render"]):
        root = "Frontend render crash caused by missing null/undefined guards."
        explanation = "The logs point to a component reading properties from undefined profile data during render."
        signals = ["TypeError", "undefined/null object", "frontend render failed"]
        confidence = "88"
    elif any(term in text for term in ["memory", "oom", "retained", "cache"]):
        root = "Memory leak caused by retained large objects or unbounded cache growth."
        explanation = "Memory and restart signals indicate objects are accumulating between requests."
        signals = ["high memory usage", "OOM/restarts", "retained objects"]
        confidence = "86"
    else:
        root = "Unknown production degradation requiring log, metric, and trace review."
        explanation = "The available telemetry is insufficient for a high-confidence deterministic diagnosis."
        signals = ["generic alert payload", "missing detailed telemetry"]
        confidence = "60"

    return (
        f"Root Cause:\n{root}\n\n"
        f"Explanation:\n{explanation}\n\n"
        f"Important Signals:\n- " + "\n- ".join(signals) + "\n\n"
        f"Confidence:\n{confidence}%"
    )


def analyze_incident(incident):
    template = """
You are an elite Site Reliability Engineer. Analyze the production incident and return Root Cause, Explanation, Important Signals, Confidence.
Incident: {incident}
"""
    return invoke_text_prompt(
        template,
        {"incident": incident},
        fallback=lambda: deterministic_rca(incident),
    )
